"""Translate the supported pseudocode program tree to readable Python."""

import ast
import builtins
import keyword
import re
from dataclasses import dataclass, field, fields, is_dataclass

from cassim.runtime.pseudocode import comments
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
# Comment lines, then the blank line unparse puts before a `def`.
_COMMENT_BEFORE_DEF = re.compile(r"(?m)^((?:[ \t]*#.*\n)+)\n(?=[ \t]*def )")
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
    # Loop variables translated 0-based: the pseudocode's `i` is the Python `i + 1`.
    shifted: set[str] = field(default_factory=set)
    # The program's or the current function's body, to see where else a name is used.
    scopes: list[list[Stmt]] = field(default_factory=list)
    # Comments to write before a statement: its line -> placeholder numbers.
    comments_before: dict[int, list[int]] = field(default_factory=dict)

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
                if name in self.shifted:
                    return ast.BinOp(
                        ast.Name(self.rename(name), ast.Load()), ast.Add(), ast.Constant(1)
                    )
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
                index = _simplify(
                    ast.BinOp(self.expression(expr.index), ast.Sub(), ast.Constant(1))
                )
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
        index = _simplify(ast.BinOp(self.expression(target.index), ast.Sub(), ast.Constant(1)))
        return ast.Subscript(self.expression(target.target), index, ast.Store())

    def block(self, body: list[Stmt]) -> list[ast.stmt]:
        out: list[ast.stmt] = []
        for stmt in body:
            out.extend(
                ast.Expr(ast.Name(comments.PLACEHOLDER.format(number), ast.Load()))
                for number in self.comments_before.pop(stmt.line, [])
            )
            out.extend(self.statement(stmt))
        return out

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

    def scoped_block(self, body: list[Stmt]) -> list[ast.stmt]:
        self.scopes.append(body)
        try:
            return self.block(body)
        finally:
            self.scopes.pop()

    def can_shift(self, stmt: For) -> bool:
        """A counting loop whose variable indexes a list, is not set inside the loop and is
        not used anywhere else in its function (after the loop Python's `i` is one less)."""
        return (
            stmt.step is None
            and stmt.var not in self.shifted
            and _indexes_with(stmt.body, stmt.var)
            and stmt.var not in _bound_names(stmt.body)
            and stmt.var not in _names_in(self.scopes[-1] if self.scopes else [], skip=stmt)
        )

    def shifted_for(self, stmt: For) -> ast.For:
        """`for i from 1 to n` indexing lists as `L[i]` becomes `for i in range(n)` with `L[i]`:
        the Python `i` is one less, so its other uses read `i + 1`, folded where they can be
        (`n - i + 1` becomes `n - i`)."""
        start = _simplify(ast.BinOp(self.expression(stmt.start), ast.Sub(), ast.Constant(1)))
        stop = self.expression(stmt.stop)
        zero = isinstance(start, ast.Constant) and start.value == 0
        self.shifted.add(stmt.var)
        try:
            body = [_SumSimplifier().visit(line) for line in self.block(stmt.body)]
        finally:
            self.shifted.discard(stmt.var)
        return ast.For(
            ast.Name(self.rename(stmt.var), ast.Store()),
            ast.Call(ast.Name("range"), [stop] if zero else [start, stop], []),
            body,
            [],
            type_comment=None,
        )

    def for_statement(self, stmt: For) -> ast.For:
        if self.can_shift(stmt):
            return self.shifted_for(stmt)
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
            range_args = [start, _past(stmt.stop, stop, 1)]
        else:
            step = self.expression(stmt.step)
            signed = _signed_one(stmt.step)
            if signed is None:
                adjustment: ast.expr = ast.IfExp(
                    ast.Compare(step, [ast.Gt()], [ast.Constant(0)]),
                    ast.Constant(1),
                    ast.Constant(-1),
                )
                range_args = [start, ast.BinOp(stop, ast.Add(), adjustment), step]
            else:
                range_args = [start, _past(stmt.stop, stop, 1 if signed > 0 else -1), step]
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
            self.scoped_block(stmt.body),
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


def _whole_number_literal(text: str) -> bool:
    try:
        int(text.replace("ᴇ", "E"))
    except ValueError:
        return False
    return True


def _integer_expression(expr: Expr) -> bool:
    """Whether a loop bound is a whole number, so the loop can use range(): names, whole
    literals, `len(...)`, and + - * div mod of those."""
    match expr:
        case Name():
            return True
        case Num():
            return _whole_number_literal(expr.text)
        case Unary(op="-" | "+"):
            return _integer_expression(expr.operand)
        case Binary() if expr.op in _WHOLE_NUMBER_OPS:
            return _integer_expression(expr.left) and _integer_expression(expr.right)
        case Call(name="len"):
            return True
    return False


# Operators that keep whole numbers whole (not `/` or `÷`, which can give a decimal).
_WHOLE_NUMBER_OPS = {"+", "-", "*", "div", "mod"}


def _past(stop: Expr, python: ast.expr, adjustment: int) -> ast.expr:
    """The exclusive `range` end for an inclusive `stop`: `8` gives 9 and `n - 1` gives `n`,
    rather than `8 + 1` and `n - 1 + 1`."""
    if isinstance(stop, Num):
        try:
            return ast.Constant(int(stop.text) + adjustment)
        except ValueError:
            pass
    if (
        adjustment == 1
        and isinstance(stop, Binary)
        and stop.op == "-"
        and isinstance(stop.right, Num)
        and stop.right.text == "1"
        and isinstance(python, ast.BinOp)
    ):
        return python.left
    return ast.BinOp(python, ast.Add(), ast.Constant(adjustment))


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


def _children(node: object) -> list[object]:
    if isinstance(node, (list, tuple)):
        return list(node)
    if is_dataclass(node) and not isinstance(node, type):
        return [getattr(node, f.name) for f in fields(node)]
    return []


def _names_in(node: object, *, skip: object = None) -> set[str]:
    """Every name used in a statement or expression tree, leaving out the subtree `skip`."""
    if node is skip:
        return set()
    found = {node.name} if isinstance(node, Name) else set()
    for child in _children(node):
        found |= _names_in(child, skip=skip)
    return found


def _indexes_with(node: object, var: str) -> bool:
    """Whether `L[var]` (the bare loop variable as an index) appears in the tree."""
    if isinstance(node, Index) and isinstance(node.index, Name) and node.index.name == var:
        return True
    return any(_indexes_with(child, var) for child in _children(node))


def _simplify(node: ast.expr) -> ast.expr:
    """Fold the whole-number constants of a sum: `(i + 1) - 1` is `i`, `n - (i + 1) + 1` is
    `n - i`. Other terms keep their order; anything that is not a sum is left alone."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub))):
        return node
    terms: list[tuple[int, ast.expr]] = []
    constant = 0

    def walk(part: ast.expr, sign: int) -> None:
        nonlocal constant
        if isinstance(part, ast.BinOp) and isinstance(part.op, (ast.Add, ast.Sub)):
            walk(part.left, sign)
            walk(part.right, sign if isinstance(part.op, ast.Add) else -sign)
        elif isinstance(part, ast.Constant) and type(part.value) is int:
            constant += sign * part.value
        else:
            terms.append((sign, part))

    walk(node, 1)
    if not terms:
        return ast.Constant(constant)
    first_sign, first = terms[0]
    result: ast.expr = first if first_sign > 0 else ast.UnaryOp(ast.USub(), first)
    for sign, term in terms[1:]:
        result = ast.BinOp(result, ast.Add() if sign > 0 else ast.Sub(), term)
    if constant:
        result = ast.BinOp(
            result, ast.Add() if constant > 0 else ast.Sub(), ast.Constant(abs(constant))
        )
    return result


class _SumSimplifier(ast.NodeTransformer):
    """Fold the constants of every sum in a shifted loop's body (see `_simplify`)."""

    def visit_BinOp(self, node: ast.BinOp) -> ast.expr:
        self.generic_visit(node)
        return _simplify(node)


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
    found = comments.pseudocode_comments(program.lines, syntax.comments)
    translator.comments_before, texts, trailing = comments.anchor(
        found, comments.statement_lines(program.body)
    )
    module = ast.Module(body=translator.scoped_block(program.body), type_ignores=[])
    ast.fix_missing_locations(module)
    translated = comments.restore(ast.unparse(module), texts, trailing, "#")
    # unparse puts a blank line before each `def`: keep a comment with its function.
    translated = _COMMENT_BEFORE_DEF.sub(r"\n\1", translated)
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
