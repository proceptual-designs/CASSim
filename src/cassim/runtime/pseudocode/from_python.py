"""Translate the supported Python AST subset into a pseudocode program tree."""

import ast
import re

from cassim.runtime.pseudocode.printer import print_program
from cassim.runtime.pseudocode.syntax import DEFAULT, Syntax
from cassim.runtime.pseudocode.translation_error import TranslationError
from cassim.runtime.pseudocode.tree import (
    Append,
    Assign,
    Binary,
    Break,
    Call,
    Compare,
    Define,
    Expr,
    ExprStmt,
    For,
    If,
    Index,
    Input,
    ListLit,
    Name,
    Num,
    Param,
    Print,
    Program,
    RepeatTimes,
    RepeatUntil,
    Return,
    Stmt,
    Str,
    Unary,
    While,
)

_MARKER = "# CASSim pseudocode translation"
_RENAME = re.compile(
    r"^# CASSim: renamed pseudocode identifier '(?P<old>[^']+)' as '(?P<new>[^']+)'\.$"
)


class _Translator:
    def __init__(self, renames: dict[str, str]) -> None:
        self.renames = renames

    def fail(self, node: ast.AST | None, construct: str, detail: str = "") -> TranslationError:
        line = getattr(node, "lineno", 0) or 1
        return TranslationError(line, construct, detail)

    def name(self, value: str) -> str:
        return self.renames.get(value, value)

    def literal(self, value: object, node: ast.Constant) -> Expr:
        if isinstance(value, bool):
            return Name("true" if value else "false", node.lineno)
        if isinstance(value, int):
            return Num(str(value), node.lineno)
        if isinstance(value, float):
            return Num(repr(value), node.lineno)
        if isinstance(value, str):
            return Str(value, node.lineno)
        raise self.fail(
            node, type(value).__name__, "only numbers, strings and booleans are supported"
        )

    def expression(self, node: ast.expr) -> Expr:  # noqa: PLR0911, PLR0912
        if isinstance(node, ast.Constant):
            return self.literal(node.value, node)
        if isinstance(node, ast.Name):
            return Name(self.name(node.id), node.lineno)
        if isinstance(node, ast.BinOp):
            supported = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
            if isinstance(node.op, supported):
                left = self.expression(node.left)
                right = self.expression(node.right)
                return Binary(_binary_op(node.op, self, node), left, right, node.lineno)
            raise self.fail(node, type(node.op).__name__)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And | ast.Or):
                values = [self.expression(value) for value in node.values]
                result = values[0]
                op = "and" if isinstance(node.op, ast.And) else "or"
                for value in values[1:]:
                    result = Binary(op, result, value, node.lineno)
                return result
            raise self.fail(node, type(node.op).__name__)
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return Unary("not", self.expression(node.operand), node.lineno)
            if isinstance(node.op, ast.USub):
                return Unary("-", self.expression(node.operand), node.lineno)
            if isinstance(node.op, ast.UAdd):
                return self.expression(node.operand)
            raise self.fail(node, type(node.op).__name__)
        if isinstance(node, ast.Compare):
            first = self.expression(node.left)
            ops = tuple(_comparison_op(op, self, node) for op in node.ops)
            return Compare(
                first,
                ops,
                tuple(self.expression(value) for value in node.comparators),
                node.lineno,
            )
        if isinstance(node, ast.Call):
            return self.call(node)
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Slice):
                raise self.fail(node, "slice")
            return Index(
                self.expression(node.value),
                self.python_index(node.slice),
                node.lineno,
            )
        if isinstance(node, ast.List):
            return ListLit(tuple(self.expression(item) for item in node.elts), node.lineno)
        if isinstance(node, ast.IfExp):
            raise self.fail(node, "conditional expression")
        if isinstance(node, ast.Tuple):
            raise self.fail(node, "tuple")
        if isinstance(node, ast.Dict):
            raise self.fail(node, "dict")
        if isinstance(node, ast.Set):
            raise self.fail(node, "set")
        raise self.fail(node, type(node).__name__)

    def python_index(self, node: ast.expr) -> Expr:
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Sub)
            and isinstance(node.right, ast.Constant)
            and node.right.value == 1
        ):
            return self.expression(node.left)
        return Binary("+", self.expression(node), Num("1", node.lineno), node.lineno)

    def call(self, node: ast.Call) -> Expr:
        if node.keywords:
            raise self.fail(node, "call with keyword arguments")
        if isinstance(node.func, ast.Name) and node.func.id == "Fraction" and len(node.args) == 1:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return Num(arg.value, node.lineno)
            return self.expression(arg)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"radians", "degrees"}
            and len(node.args) == 1
        ):
            inner = node.args[0]
            if (
                node.func.id == "degrees"
                and isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Name)
                and inner.func.id in {"asin", "acos", "atan"}
                and len(inner.args) == 1
            ):
                return Call(inner.func.id, (self.expression(inner.args[0]),), node.lineno)
            if node.func.id == "radians":
                return self.expression(inner)
        if not isinstance(node.func, ast.Name):
            raise self.fail(node, "non-name call")
        return Call(
            self.name(node.func.id),
            tuple(self.expression(a) for a in node.args),
            node.lineno,
        )

    def assignment_target(self, node: ast.expr) -> Name | Index:
        if isinstance(node, ast.Name):
            return Name(self.name(node.id), node.lineno)
        if isinstance(node, ast.Subscript) and not isinstance(node.slice, ast.Slice):
            return Index(self.expression(node.value), self.python_index(node.slice), node.lineno)
        if isinstance(node, ast.Subscript):
            raise self.fail(node, "slice assignment")
        raise self.fail(node, f"assignment to {type(node).__name__}")

    def statements(self, body: list[ast.stmt]) -> list[Stmt]:
        return [stmt for node in body for stmt in self.statement(node)]

    def statement(self, node: ast.stmt) -> list[Stmt]:  # noqa: PLR0911, PLR0912
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                raise self.fail(node, "chained assignment")
            value = node.value
            if _is_input(value):
                return [Input(self.assignment_target(node.targets[0]), node.lineno)]
            return [
                Assign(
                    self.assignment_target(node.targets[0]),
                    self.expression(value),
                    node.lineno,
                )
            ]
        if isinstance(node, ast.AnnAssign):
            raise self.fail(node, "annotated assignment")
        if isinstance(node, ast.AugAssign):
            raise self.fail(node, "augmented assignment")
        if isinstance(node, ast.Expr):
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "append"
                and not node.value.keywords
                and len(node.value.args) == 1
            ):
                return [
                    Append(
                        self.expression(node.value.args[0]),
                        self.expression(node.value.func.value),
                        node.lineno,
                    )
                ]
            expression = self.expression(node.value)
            if not isinstance(expression, Call):
                raise self.fail(node.value, "expression statement", "only a call is supported")
            if expression.name == "print":
                return self.print_statement(node.value)
            return [ExprStmt(expression, node.lineno)]
        if isinstance(node, ast.If):
            return [self.if_statement(node)]
        if isinstance(node, ast.While):
            repeated = self.repeat_until(node)
            return (
                [repeated]
                if repeated is not None
                else [While(self.expression(node.test), self.statements(node.body), node.lineno)]
            )
        if isinstance(node, ast.For):
            return [self.for_statement(node)]
        if isinstance(node, ast.FunctionDef):
            return [self.function(node)]
        if isinstance(node, ast.Return):
            value = None if node.value is None else self.expression(node.value)
            return [Return(value, node.lineno)]
        if isinstance(node, ast.Break):
            return [Break(node.lineno)]
        if isinstance(node, ast.Pass):
            raise self.fail(node, "pass")
        if isinstance(node, ast.ClassDef):
            raise self.fail(node, "class definition")
        if isinstance(node, ast.Import | ast.ImportFrom):
            raise self.fail(node, "import")
        if isinstance(node, ast.Try):
            raise self.fail(node, "try")
        raise self.fail(node, type(node).__name__)

    def print_statement(self, node: ast.expr) -> list[Stmt]:
        if not isinstance(node, ast.Call):
            raise self.fail(node, "print expression")
        if node.keywords:
            raise self.fail(node, "print keyword argument")
        return [Print([self.expression(a) for a in node.args], node.lineno)]

    def if_statement(self, node: ast.If) -> If:
        branches: list[tuple[Expr, list[Stmt], int]] = [
            (self.expression(node.test), self.statements(node.body), node.lineno)
        ]
        orelse: list[Stmt] | None = None
        rest = node.orelse
        while len(rest) == 1 and isinstance(rest[0], ast.If):
            nested = rest[0]
            branches.append(
                (self.expression(nested.test), self.statements(nested.body), nested.lineno)
            )
            rest = nested.orelse
        if rest:
            orelse = self.statements(rest)
        return If(branches, orelse, node.lineno)

    def repeat_until(self, node: ast.While) -> RepeatUntil | None:
        if not (isinstance(node.test, ast.Constant) and node.test.value is True):
            return None
        if node.orelse:
            raise self.fail(node, "while/else")
        last = node.body[-1]
        if (
            not isinstance(last, ast.If)
            or last.orelse
            or len(last.body) != 1
            or not isinstance(last.body[0], ast.Break)
        ):
            raise self.fail(last, "while True", "the final statement must be 'if condition: break'")
        return RepeatUntil(
            self.statements(node.body[:-1]),
            self.expression(last.test),
            node.lineno,
            last.lineno,
        )

    def for_statement(self, node: ast.For) -> For | RepeatTimes:  # noqa: PLR0912
        if node.orelse:
            raise self.fail(node, "for/else")
        if not isinstance(node.target, ast.Name):
            raise self.fail(node.target, "for target")
        if (
            not isinstance(node.iter, ast.Call)
            or not isinstance(node.iter.func, ast.Name)
            or node.iter.func.id not in {"range", "_inclusive_range"}
            or node.iter.keywords
        ):
            raise self.fail(node.iter, "for iterable", "only for ... in range(...) is supported")
        args = node.iter.args
        inclusive = node.iter.func.id == "_inclusive_range"
        if inclusive:
            if len(args) not in {2, 3}:
                raise self.fail(node.iter, "inclusive range arguments")
            return For(
                self.name(node.target.id),
                self.expression(args[0]),
                self.expression(args[1]),
                self.expression(args[2]) if len(args) == 3 else None,  # noqa: PLR2004
                self.statements(node.body),
                node.lineno,
            )
        if len(args) == 1:
            start: Expr = Num("0", node.lineno)
            if node.target.id == "_":
                return RepeatTimes(
                    self.expression(args[0]), self.statements(node.body), node.lineno
                )
            stop = self.minus_one(args[0], 1)
            step: Expr | None = None
        elif len(args) in {2, 3}:
            start = self.expression(args[0])
            if len(args) == 3:  # noqa: PLR2004
                step = self.expression(args[2])
                if _generated_dynamic_stop(args[1], args[2]):
                    assert isinstance(args[1], ast.BinOp)
                    stop = self.expression(args[1].left)
                else:
                    sign = _constant_sign(args[2])
                    if sign == 0:
                        raise self.fail(args[2], "range step", "zero is not supported")
                    if sign is None:
                        raise self.fail(
                            args[2], "range step", "step must have a known constant sign"
                        )
                    stop = self.exclusive_stop(args[1], sign)
            else:
                step = None
                stop = self.exclusive_stop(args[1], 1)
        else:
            raise self.fail(node.iter, "range arguments", "expected one to three arguments")
        return For(
            self.name(node.target.id),
            start,
            stop,
            step,
            self.statements(node.body),
            node.lineno,
        )

    def exclusive_stop(self, node: ast.expr, sign: int) -> Expr:
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Add)
            and isinstance(node.right, ast.Constant)
            and node.right.value in {1, -1}
            and node.right.value == sign
        ):
            return self.expression(node.left)
        return self.minus_one(node, sign)

    def minus_one(self, node: ast.expr, sign: int) -> Expr:
        return Binary("-", self.expression(node), Num(str(sign), node.lineno), node.lineno)

    def function(self, node: ast.FunctionDef) -> Define:
        if node.decorator_list:
            raise self.fail(node, "decorated function")
        if node.returns is not None:
            raise self.fail(node.returns, "function return annotation")
        if node.args.posonlyargs or node.args.kwonlyargs or node.args.vararg or node.args.kwarg:
            raise self.fail(node, "function signature", "only positional parameters are supported")
        args = node.args.args
        default_offset = len(args) - len(node.args.defaults)
        params: list[Param] = []
        for index, arg in enumerate(args):
            if arg.annotation is not None:
                raise self.fail(arg.annotation, "parameter annotation")
            default = (
                self.expression(node.args.defaults[index - default_offset])
                if index >= default_offset
                else None
            )
            params.append(Param(self.name(arg.arg), default=default))
        return Define(self.name(node.name), tuple(params), self.statements(node.body), node.lineno)


def _constant_sign(node: ast.expr) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float) and node.value != 0:
        return 1 if node.value > 0 else -1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _constant_sign(node.operand)
        return None if value is None else -value
    return None


def _binary_op(op: ast.operator, translator: _Translator, node: ast.expr) -> str:
    names = (
        (ast.Add, "+"),
        (ast.Sub, "-"),
        (ast.Mult, "*"),
        (ast.Div, "/"),
        (ast.FloorDiv, "div"),
        (ast.Mod, "mod"),
        (ast.Pow, "^"),
    )
    for kind, name in names:
        if isinstance(op, kind):
            return name
    raise translator.fail(node, type(op).__name__)


def _comparison_op(op: ast.cmpop, translator: _Translator, node: ast.expr) -> str:
    names = (
        (ast.Eq, "="),
        (ast.NotEq, "≠"),
        (ast.Lt, "<"),
        (ast.LtE, "≤"),
        (ast.Gt, ">"),
        (ast.GtE, "≥"),
    )
    for kind, name in names:
        if isinstance(op, kind):
            return name
    raise translator.fail(node, type(op).__name__)


def _generated_dynamic_stop(stop: ast.expr, step: ast.expr) -> bool:
    if not (
        isinstance(stop, ast.BinOp)
        and isinstance(stop.op, ast.Add)
        and isinstance(stop.right, ast.IfExp)
    ):
        return False
    test = stop.right.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, type(step))
        and ast.dump(test.left) == ast.dump(step)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Gt)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == 0
    )


def _is_input(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call) or node.keywords:
        return False
    if isinstance(node.func, ast.Name):
        if node.func.id == "read_value":
            return not node.args
        if node.func.id in {"input", "int", "float"} and len(node.args) <= 1:
            if node.func.id == "input":
                return not node.args
            return bool(node.args) and _is_input(node.args[0])
    return False


def python_to_program(source: str) -> Program:
    """Parse supported Python and build the shared pseudocode tree."""
    lines = source.splitlines()
    renames: dict[str, str] = {}
    original_lines = lines
    for line in lines:
        match = _RENAME.fullmatch(line.strip())
        if match:
            renames[match.group("new")] = match.group("old")
    if _MARKER in lines:
        marker_line = lines.index(_MARKER)
        lines = lines[marker_line + 1 :]
        source = "\n".join(lines) + "\n"
    else:
        source = "\n".join(original_lines) + "\n"
    try:
        module = ast.parse(source)
    except SyntaxError as error:
        line = error.lineno or 1
        raise TranslationError(line, "syntax", error.msg) from error
    translator = _Translator(renames)
    body = translator.statements(module.body)
    return Program(body, source.splitlines())


def python_to_pseudocode(source: str, syntax: Syntax = DEFAULT) -> str:
    """Translate Python to pseudocode using the selected syntax's emit style."""
    return print_program(python_to_program(source), syntax)


translate_to_pseudocode = python_to_pseudocode
