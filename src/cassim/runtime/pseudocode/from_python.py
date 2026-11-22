"""Translate the supported Python AST subset into a pseudocode program tree."""

import ast
import re

from cassim.runtime.pseudocode import comments
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
    ForEach,
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
        # Comments to write before a statement: its line -> placeholder numbers.
        self.comments_before: dict[int, list[int]] = {}
        # Loop variables read 1-based: the Python `i` is the pseudocode's `i - 1`.
        self.unshifted: set[str] = set()
        # The module's or the current function's body, to see where else a name is used.
        self.scopes: list[list[ast.stmt]] = []

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
            if node.id in self.unshifted:
                return Binary("-", Name(self.name(node.id), node.lineno), Num("1"), node.lineno)
            return Name(self.name(node.id), node.lineno)
        if isinstance(node, ast.BinOp):
            supported = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
            if isinstance(node.op, supported):
                left = self.expression(node.left)
                right = self.expression(node.right)
                made = Binary(_binary_op(node.op, self, node), left, right, node.lineno)
                return _fold(made) if self.unshifted else made
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
        return _fold(Binary("+", self.expression(node), Num("1", node.lineno), node.lineno))

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
        out: list[Stmt] = []
        for node in body:
            out.extend(
                ExprStmt(Name(comments.PLACEHOLDER.format(number), node.lineno), node.lineno)
                for number in self.comments_before.pop(node.lineno, [])
            )
            out.extend(self.statement(node))
        return out

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

    def scoped(self, body: list[ast.stmt]) -> list[Stmt]:
        self.scopes.append(body)
        try:
            return self.statements(body)
        finally:
            self.scopes.pop()

    def can_unshift(self, node: ast.For, var: str) -> bool:
        """A plain `range` loop whose variable indexes a list, is not set inside the loop and is
        not used anywhere else in its function: it reads as a 1-based pseudocode loop."""
        call = node.iter
        assert isinstance(call, ast.Call)
        outside = _python_names(self.scopes[-1] if self.scopes else [], skip=node)
        return (
            len(call.args) in {1, 2}
            and var not in self.unshifted
            and _python_indexes_with(node.body, var)
            and not _python_sets(node.body, var)
            and var not in outside
        )

    def unshifted_for(self, node: ast.For, var: str) -> For:
        """`for i in range(n)` indexing lists as `L[i]` becomes `for i from 1 to n` with `L[i]`;
        the pseudocode `i` is one more, so other uses read `i - 1`, folded where they can be."""
        call = node.iter
        assert isinstance(call, ast.Call)
        args = call.args
        start: Expr = (
            Num("1", node.lineno)
            if len(args) == 1
            else _fold(Binary("+", self.expression(args[0]), Num("1"), node.lineno))
        )
        stop = self.expression(args[-1])
        self.unshifted.add(var)
        try:
            body = self.statements(node.body)
        finally:
            self.unshifted.discard(var)
        return For(self.name(var), start, stop, None, body, node.lineno)

    def for_statement(self, node: ast.For) -> For | ForEach | RepeatTimes:  # noqa: PLR0912
        if node.orelse:
            raise self.fail(node, "for/else")
        if not isinstance(node.target, ast.Name):
            raise self.fail(node.target, "for target")
        if not (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id in {"range", "_inclusive_range"}
        ):  # `for coeff in coeffs`: a loop over the items
            return ForEach(
                self.name(node.target.id),
                self.expression(node.iter),
                self.statements(node.body),
                node.lineno,
            )
        if node.iter.keywords:
            raise self.fail(node.iter, "for iterable", "range() takes no keywords here")
        if node.iter.func.id == "range" and self.can_unshift(node, node.target.id):
            return self.unshifted_for(node, node.target.id)
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
        # Folded: `range(1, 9)` ends at 8, not `9 - 1`.
        return _fold(Binary("-", self.expression(node), Num(str(sign), node.lineno), node.lineno))

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
        return Define(self.name(node.name), tuple(params), self.scoped(node.body), node.lineno)


def _python_names(body: list[ast.stmt], *, skip: ast.AST) -> set[str]:
    """Every name used in `body`, leaving out the subtree `skip`."""
    found: set[str] = set()
    stack: list[ast.AST] = list(body)
    while stack:
        node = stack.pop()
        if node is skip:
            continue
        if isinstance(node, ast.Name):
            found.add(node.id)
        stack.extend(ast.iter_child_nodes(node))
    return found


def _python_indexes_with(body: list[ast.stmt], var: str) -> bool:
    """Whether `L[var]` (the bare loop variable as an index) appears in `body`."""
    return any(
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Name)
        and node.slice.id == var
        for stmt in body
        for node in ast.walk(stmt)
    )


def _python_sets(body: list[ast.stmt], var: str) -> bool:
    """Whether `body` assigns to `var` (so the loop cannot be renumbered)."""
    return any(
        isinstance(node, ast.Name) and node.id == var and isinstance(node.ctx, ast.Store)
        for stmt in body
        for node in ast.walk(stmt)
    )


def _whole(expr: Expr) -> int | None:
    """A whole-number literal's value, including one written with a sign (`-1` for a step)."""
    if isinstance(expr, Num) and expr.text.removeprefix("-").isdigit():
        return int(expr.text)
    if isinstance(expr, Unary) and expr.op == "-" and (value := _whole(expr.operand)) is not None:
        return -value
    return None


def _fold(expr: Expr) -> Expr:
    """Fold the whole-number constants of a pseudocode sum: `(i - 1) + 1` is `i` and
    `n - (i - 1)` is `n - i + 1`. Other terms keep their order."""
    if not (isinstance(expr, Binary) and expr.op in {"+", "-"}):
        return expr
    terms: list[tuple[int, Expr]] = []
    constant = 0

    def walk(part: Expr, sign: int) -> None:
        nonlocal constant
        if isinstance(part, Binary) and part.op in {"+", "-"} and not part.implicit:
            walk(part.left, sign)
            walk(part.right, sign if part.op == "+" else -sign)
        elif (number := _whole(part)) is not None:
            constant += sign * number
        else:
            terms.append((sign, part))

    walk(expr, 1)
    line = expr.line
    if not terms:
        return Num(str(constant), line) if constant >= 0 else Unary("-", Num(str(-constant)), line)
    first_sign, first = terms[0]
    result: Expr = first if first_sign > 0 else Unary("-", first, line)
    for sign, term in terms[1:]:
        result = Binary("+" if sign > 0 else "-", result, term, line)
    if constant:
        result = Binary("+" if constant > 0 else "-", result, Num(str(abs(constant))), line)
    return result


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
    return _python_program(source)[0]


def _python_program(
    source: str, *, keep_comments: bool = False
) -> tuple[Program, list[str | None], list[int]]:
    """The tree, and with `keep_comments` the comment placeholders written into it (see
    `comments`): never when the tree is run, only when it is printed as text."""
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
    texts: list[str | None] = []
    trailing: list[int] = []
    if keep_comments:
        lines = [node.lineno for node in ast.walk(module) if isinstance(node, ast.stmt)]
        translator.comments_before, texts, trailing = comments.anchor(
            comments.python_comments(source), lines
        )
    body = translator.scoped(module.body)
    return Program(body, source.splitlines()), texts, trailing


def python_to_pseudocode(source: str, syntax: Syntax = DEFAULT) -> str:
    """Translate Python to pseudocode using the selected syntax's emit style."""
    program, texts, trailing = _python_program(source, keep_comments=True)
    marker = "#" if syntax.comments.get("#", "no") != "no" else "//"
    return comments.restore(print_program(program, syntax), texts, trailing, marker)


translate_to_pseudocode = python_to_pseudocode
