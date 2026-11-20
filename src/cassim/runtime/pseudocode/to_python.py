"""Translate the supported pseudocode program tree to readable Python."""

import ast
import builtins
import keyword
from dataclasses import dataclass, field

from cassim.runtime.pseudocode.parser import parse
from cassim.runtime.pseudocode.settings import Settings
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
    FuncAssign,
    If,
    Index,
    Input,
    ListLit,
    Name,
    Num,
    Paren,
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

TRANSLATION_MARKER = "# CASSim pseudocode translation"
_RESERVED = frozenset(
    set(keyword.kwlist) | set(dir(builtins)) | {"Fraction", "read_value", "radians", "degrees"}
)
_CMP = {
    "=": ast.Eq,
    "≠": ast.NotEq,
    "<": ast.Lt,
    ">": ast.Gt,
    "≤": ast.LtE,
    "≥": ast.GtE,
}
_BIN = {"+": ast.Add, "-": ast.Sub, "*": ast.Mult, "mod": ast.Mod, "div": ast.FloorDiv}


@dataclass(slots=True)
class _Translator:
    settings: Settings
    names: dict[str, str]
    needs_fraction: bool = False
    needs_input: bool = False
    needs_inclusive_range: bool = False
    math_names: set[str] = field(default_factory=set)

    def rename(self, name: str) -> str:
        return self.names.get(name, name)

    def fail(self, line: int, construct: str, detail: str = "") -> TranslationError:
        return TranslationError(line, construct, detail, language="pseudocode")

    def number(self, expr: Num) -> ast.expr:
        text = expr.text.replace("ᴇ", "E")
        if self.settings.number == "exact" and any(c in text for c in (".", "E", "e")):
            self.needs_fraction = True
            return ast.Call(ast.Name("Fraction"), [ast.Constant(text)], [])
        try:
            return ast.Constant(int(text))
        except ValueError:
            try:
                return ast.Constant(float(text))
            except ValueError as error:
                raise self.fail(expr.line, "number literal", repr(text)) from error

    def call(self, expr: Call) -> ast.expr:
        name = self.rename(expr.name)
        args = [self.expression(a) for a in expr.args]
        math_names = {
            "acos",
            "asin",
            "atan",
            "ceil",
            "cos",
            "exp",
            "floor",
            "log",
            "log10",
            "sin",
            "sqrt",
            "tan",
        }
        if name in math_names:
            self.math_names.add(name)
        if self.settings.angle == "degree" and name in {"sin", "cos", "tan"} and len(args) == 1:
            self.math_names.update({"radians"})
            args = [ast.Call(ast.Name("radians"), args, [])]
        result: ast.expr = ast.Call(ast.Name(name), args, [])
        if self.settings.angle == "degree" and name in {"asin", "acos", "atan"} and len(args) == 1:
            self.math_names.update({"degrees"})
            result = ast.Call(ast.Name("degrees"), [result], [])
        return result

    def expression(self, expr: Expr) -> ast.expr:  # noqa: PLR0911, PLR0912
        match expr:
            case Num():
                return self.number(expr)
            case Str(value=value):
                return ast.Constant(value)
            case Name(name=name):
                if name.lower() == "true":
                    return ast.Constant(True)
                if name.lower() == "false":
                    return ast.Constant(False)
                return ast.Name(self.rename(name), ast.Load())
            case Paren(inner=inner):
                return self.expression(inner)
            case Unary(op=op, operand=operand):
                value = self.expression(operand)
                node = {"-": ast.USub, "+": ast.UAdd}.get(op)
                if node is not None:
                    return ast.UnaryOp(node(), value)
                if op == "not":
                    return ast.UnaryOp(ast.Not(), value)
                if op == "abs":
                    return ast.Call(ast.Name("abs"), [value], [])
                if op == "sqrt":
                    return ast.BinOp(value, ast.Pow(), ast.Constant(0.5))
                raise self.fail(expr.line, f"unary {op!r}")
            case Binary(op=op, left=left, right=right):
                lhs, rhs = self.expression(left), self.expression(right)
                if op in {"and", "or"}:
                    return ast.BoolOp(ast.And() if op == "and" else ast.Or(), [lhs, rhs])
                if op == "^":
                    return ast.BinOp(lhs, ast.Pow(), rhs)
                if op in {"/", "÷"} and self.settings.number in {"auto", "exact"}:
                    self.needs_fraction = True
                    lhs = ast.Call(ast.Name("Fraction"), [lhs], [])
                    rhs = ast.Call(ast.Name("Fraction"), [rhs], [])
                    return ast.BinOp(lhs, ast.Div(), rhs)
                if op in {"/", "÷"}:
                    return ast.BinOp(lhs, ast.Div(), rhs)
                node = _BIN.get(op)
                if node is None:
                    raise self.fail(expr.line, f"operator {op!r}")
                return ast.BinOp(lhs, node(), rhs)
            case Compare():
                return ast.Compare(
                    self.expression(expr.first),
                    [
                        _CMP[op]()
                        if op in _CMP
                        else self._raise(self.fail(expr.line, f"comparison {op!r}"))
                        for op in expr.ops
                    ],
                    [self.expression(value) for value in expr.rest],
                )
            case Call():
                return self.call(expr)
            case Index():
                index = ast.BinOp(self.expression(expr.index), ast.Sub(), ast.Constant(1))
                return ast.Subscript(self.expression(expr.target), index, ast.Load())
            case ListLit():
                return ast.List([self.expression(item) for item in expr.items], ast.Load())
        raise self.fail(expr.line, type(expr).__name__)

    @staticmethod
    def _raise(error: TranslationError) -> ast.cmpop:
        raise error

    def target(self, target: Name | Index) -> ast.expr:
        if isinstance(target, Name):
            return ast.Name(self.rename(target.name), ast.Store())
        index = ast.BinOp(self.expression(target.index), ast.Sub(), ast.Constant(1))
        return ast.Subscript(self.expression(target.target), index, ast.Store())

    def block(self, body: list[Stmt]) -> list[ast.stmt]:
        return [statement for stmt in body for statement in self.statement(stmt)]

    def statement(self, stmt: Stmt) -> list[ast.stmt]:  # noqa: PLR0911, PLR0912
        match stmt:
            case Assign():
                return [
                    ast.Assign(
                        [self.target(stmt.target)],
                        self.expression(stmt.value),
                        type_comment=None,
                    )
                ]
            case FuncAssign():
                args = _arguments([ast.arg(p) for p in stmt.params])
                body = [ast.Return(self.expression(stmt.body))]
                return [
                    ast.FunctionDef(
                        self.rename(stmt.name),
                        args,
                        body,
                        [],
                        returns=None,
                        type_comment=None,
                        type_params=[],
                    )
                ]
            case Input():
                self.needs_input = True
                return [
                    ast.Assign(
                        [self.target(stmt.target)],
                        ast.Call(ast.Name("read_value"), [], []),
                        type_comment=None,
                    )
                ]
            case Print():
                call = ast.Call(ast.Name("print"), [self.expression(i) for i in stmt.items], [])
                return [ast.Expr(call)]
            case Append():
                return [
                    ast.Expr(
                        ast.Call(
                            ast.Attribute(self.expression(stmt.target), "append", ast.Load()),
                            [self.expression(stmt.value)],
                            [],
                        )
                    )
                ]
            case ExprStmt():
                return [ast.Expr(self.expression(stmt.expr))]
            case Return():
                return [ast.Return(None if stmt.value is None else self.expression(stmt.value))]
            case Break():
                return [ast.Break()]
            case If():
                return [self.if_statement(stmt)]
            case While():
                return [ast.While(self.expression(stmt.cond), self.block(stmt.body), [])]
            case For():
                return [self.for_statement(stmt)]
            case ForEach():
                return [
                    ast.For(
                        ast.Name(self.rename(stmt.var), ast.Store()),
                        self.expression(stmt.iterable),
                        self.block(stmt.body),
                        [],
                        type_comment=None,
                    )
                ]
            case RepeatTimes():
                return [
                    ast.For(
                        ast.Name("_", ast.Store()),
                        ast.Call(ast.Name("range"), [self.expression(stmt.count)], []),
                        self.block(stmt.body),
                        [],
                        type_comment=None,
                    )
                ]
            case RepeatUntil():
                body = self.block(stmt.body)
                body.append(ast.If(self.expression(stmt.cond), [ast.Break()], []))
                return [ast.While(ast.Constant(True), body, [])]
            case Define():
                return [self.define(stmt)]
        raise self.fail(stmt.line, type(stmt).__name__)

    def if_statement(self, stmt: If) -> ast.If:
        if not stmt.branches:
            raise self.fail(stmt.line, "if", "it has no branch")
        condition, body, _ = stmt.branches[0]
        result = ast.If(self.expression(condition), self.block(body), [])
        current = result
        for condition, body, _ in stmt.branches[1:]:
            branch = ast.If(self.expression(condition), self.block(body), [])
            current.orelse = [branch]
            current = branch
        if stmt.orelse is not None:
            current.orelse = self.block(stmt.orelse)
        return result

    def for_statement(self, stmt: For) -> ast.For:
        start = self.expression(stmt.start)
        stop = self.expression(stmt.stop)
        if stmt.step is None:
            safe_for_range = _integer_expression(stmt.start) and _integer_expression(stmt.stop)
        else:
            safe_for_range = (
                _integer_expression(stmt.start)
                and _integer_expression(stmt.stop)
                and _integer_step(stmt.step)
            )
        if not safe_for_range:
            self.needs_inclusive_range = True
            self.math_names.add("floor")
            args = [start, stop]
            if stmt.step is not None:
                args.append(self.expression(stmt.step))
            return ast.For(
                ast.Name(self.rename(stmt.var), ast.Store()),
                ast.Call(ast.Name("_inclusive_range"), args, []),
                self.block(stmt.body),
                [],
                type_comment=None,
            )
        if stmt.step is None:
            range_args = [start, ast.BinOp(stop, ast.Add(), ast.Constant(1))]
        else:
            step = self.expression(stmt.step)
            signed = _signed_one(stmt.step)
            if signed is None:
                adjustment: ast.expr = ast.IfExp(
                    ast.Compare(step, [ast.Gt()], [ast.Constant(0)]),
                    ast.Constant(1),
                    ast.Constant(-1),
                )
            else:
                adjustment = ast.Constant(1 if signed > 0 else -1)
            range_args = [start, ast.BinOp(stop, ast.Add(), adjustment), step]
        return ast.For(
            ast.Name(self.rename(stmt.var), ast.Store()),
            ast.Call(ast.Name("range"), range_args, []),
            self.block(stmt.body),
            [],
            type_comment=None,
        )

    def define(self, stmt: Define) -> ast.FunctionDef:
        if any(param.sig is not None for param in stmt.params):
            raise self.fail(stmt.line, "function-valued parameter")
        args = [ast.arg(self.rename(param.name)) for param in stmt.params]
        first_default = next(
            (index for index, param in enumerate(stmt.params) if param.default is not None),
            len(stmt.params),
        )
        if any(param.default is None for param in stmt.params[first_default:]):
            raise self.fail(stmt.line, "function default parameter", "defaults must be trailing")
        defaults = [
            self.expression(param.default)
            for param in stmt.params[first_default:]
            if param.default is not None
        ]
        return ast.FunctionDef(
            self.rename(stmt.name),
            _arguments(args, defaults),
            self.block(stmt.body),
            [],
            returns=None,
            type_comment=None,
            type_params=[],
        )


def _signed_one(expr: Expr) -> int | None:
    if isinstance(expr, Num):
        try:
            number = float(expr.text.replace("ᴇ", "E"))
        except ValueError:
            return None
        return 1 if number > 0 else -1 if number < 0 else 0
    if isinstance(expr, Unary) and expr.op == "-":
        return -1
    return None


def _integer_expression(expr: Expr) -> bool:
    if isinstance(expr, Name):
        return True
    if isinstance(expr, Num):
        try:
            int(expr.text.replace("ᴇ", "E"))
            return True
        except ValueError:
            return False
    if isinstance(expr, Unary) and expr.op in {"-", "+"}:
        return _integer_expression(expr.operand)
    if isinstance(expr, Binary):
        return _integer_expression(expr.left) and _integer_expression(expr.right)
    return False


def _integer_step(expr: Expr) -> bool:
    if isinstance(expr, Name):
        return False
    return _integer_expression(expr)


def _arguments(args: list[ast.arg], defaults: list[ast.expr] | None = None) -> ast.arguments:
    return ast.arguments(
        posonlyargs=[],
        args=args,
        vararg=None,
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=None,
        defaults=[] if defaults is None else defaults,
    )


def _bound_names(body: list[Stmt]) -> set[str]:
    found: set[str] = set()
    for stmt in body:
        match stmt:
            case Assign(target=Name(name=name)):
                found.add(name)
            case Input(target=Name(name=name)):
                found.add(name)
            case FuncAssign(name=name, params=params):
                found.add(name)
                found.update(params)
            case For(var=var) | ForEach(var=var):
                found.add(var)
                nested = stmt.body
                found.update(_bound_names(nested))
            case Define(name=name, params=params, body=nested):
                found.add(name)
                found.update(p.name for p in params)
                found.update(_bound_names(nested))
            case If(branches=branches, orelse=orelse):
                for _, nested, _ in branches:
                    found.update(_bound_names(nested))
                if orelse is not None:
                    found.update(_bound_names(orelse))
            case While(body=nested) | RepeatTimes(body=nested) | RepeatUntil(body=nested):
                found.update(_bound_names(nested))
    return found


def _renames(program: Program) -> dict[str, str]:
    bound = sorted(_bound_names(program.body))
    names: dict[str, str] = {}
    taken = set(bound)
    for name in bound:
        if name not in _RESERVED:
            continue
        candidate = f"{name}_"
        while candidate in taken or candidate in _RESERVED:
            candidate += "_"
        names[name] = candidate
        taken.add(candidate)
    return names


def pseudocode_to_python(
    source: str | Program,
    settings: Settings | None = None,
    syntax: Syntax = DEFAULT,
) -> str:
    """Translate pseudocode (or its program tree) to a safe, readable Python subset."""
    program = parse(source, syntax) if isinstance(source, str) else source
    translator = _Translator(settings or Settings(), _renames(program))
    module = ast.Module(body=translator.block(program.body), type_ignores=[])
    ast.fix_missing_locations(module)
    translated = ast.unparse(module)
    header: list[str] = []
    if translator.needs_fraction:
        header.append("from fractions import Fraction")
    if translator.math_names:
        header.append(f"from math import {', '.join(sorted(translator.math_names))}")
    if translator.needs_inclusive_range:
        header.extend(
            [
                "",
                "def _inclusive_range(start, stop, step=1):",
                "    quotient = (stop - start) / step",
                "    if isinstance(quotient, float):",
                "        quotient += 1e-9 * max(1.0, abs(quotient))",
                "    count = max(0, floor(quotient) + 1)",
                "    for offset in range(count):",
                "        yield start + offset * step",
            ]
        )
    if translator.needs_input:
        if not translator.needs_fraction:
            header.append("from fractions import Fraction")
        if (settings or Settings()).number == "exact":
            converter = "return Fraction(value)"
        elif (settings or Settings()).number == "auto":
            converter = "return float(value) if any(c in value for c in '.eE') else Fraction(value)"
        else:
            converter = "return float(Fraction(value))"
        header.extend(
            [
                "",
                "def read_value():",
                "    value = input().strip()",
                "    try:",
                f"        {converter}",
                "    except (ValueError, ZeroDivisionError):",
                "        return value",
            ]
        )
    for original, renamed in translator.names.items():
        header.append(f"# CASSim: renamed pseudocode identifier {original!r} as {renamed!r}.")
    header.append(TRANSLATION_MARKER)
    code = "\n".join(header) + "\n" + translated
    return code.rstrip() + "\n"


translate_to_python = pseudocode_to_python
