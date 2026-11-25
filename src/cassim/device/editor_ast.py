"""Engine text as an editor tree (FR-CALC-004): the bridge from the core parser's AST to a `Row`.

A result brought down from the history must keep its structure: `(x-1)^2-1` has an exponent of
`2`, not `2-1`, and the `√` in `-√(3)*sin(π/9)` holds only `3`. Typing the text key by key cannot
know where a template ends, so the text is parsed with the real parser and the AST is turned into
templates and characters: `/` is a fraction, `^` a power, a matrix a matrix, and a call is the
template written as it (`Spec.call` in `templates.py`: `√`, `root`, `log`, `abs`, `derivative`,
`∫`, `Σ`, `Π`).

The tree's linear text parses back to the same AST (`row_from_text` checks it and falls back to a
plain paste if it ever does not), so a recalled value is never changed by the trip.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
from typing import Any

from cassim.core import ast
from cassim.core.ast import RIGHT_ASSOCIATIVE, UNARY_OPERAND_PREC, Prec
from cassim.core.errors import TIError
from cassim.core.parser import parse_expression
from cassim.device.editor import Editor, Row, Template, estimated_width, linear_text
from cassim.device.templates import SPECS, Kind

# Binary operators written with a space either side, as `ast.Binary` prints them
_SPACED = frozenset({"and", "or", "xor", "nor", "nand", "|"})


def row_from_text(text: str) -> Row:
    """The editor tree for engine text. Text the parser cannot read, or whose tree would not
    read back the same, is pasted as linear text instead."""
    parsed = _parsed(text)
    if parsed is not None:
        return parsed[1]
    editor = Editor()
    editor.insert_linear(text)
    return editor.root


@lru_cache(maxsize=1024)
def text_ems(text: str) -> float:
    """About how wide engine text is when drawn as maths, in ems (`editor.estimated_width` of
    its tree): fractions, powers and roots at their drawn sizes, not a count of characters."""
    return estimated_width(row_from_text(text))


def pasted_row(text: str) -> Row | None:
    """The tree for pasted text that has a `^` or a `√`, or None to paste it character by
    character. The text is kept as it was spelled (a `/` stays linear, `2x` stays `2x`, as
    decision 0035 stage 2 settled) with only the exponents and roots made templates; the parser
    then checks that the tree still means what the text meant. If it does not, the parser's own
    tree is used: the value comes before the spelling. Text the parser cannot read (part of an
    expression, a statement such as `Define`) gives None. A leading `=` (a spreadsheet formula)
    is kept and the rest checked."""
    if text.startswith("="):
        rest = pasted_row(text[1:])
        return None if rest is None else ["=", *rest]
    try:
        wanted = normal_form(parse_expression(text))
    except TIError, RecursionError:
        return None
    editor = Editor()
    editor._paste_linear(text, "")  # the scan alone, without this check
    try:
        if normal_form(parse_expression(linear_text(editor.root))) == wanted:
            return editor.root
    except TIError, RecursionError:
        pass
    parsed = _parsed(text)
    return None if parsed is None else parsed[1]


# Results SymPy's LaTeX draws closer to the device: `when` and `piecewise` as a brace (emulator
# calc2 results), and the message `Done`
_SYMPY_CALLS = frozenset({"when", "piecewise"})
_MESSAGES = frozenset({"Done"})


@lru_cache(maxsize=512)
def result_latex(text: str) -> str | None:
    """A result drawn from its text through the editor tree (decision 0035 stage 3), so a picked
    row looks the same before and after the cursor moves into it, products show their `·` as on
    the device, and `and`/`or` are upright. None for text the tree should not draw (it does not
    parse, or SymPy draws it closer to the device): the caller keeps SymPy's LaTeX."""
    row = result_row(text)
    if row is None:
        return None
    editor = Editor()
    editor.root = list(row)
    return editor.latex(cursor=False)


@lru_cache(maxsize=1024)
def result_row(text: str) -> tuple[str | Template, ...] | None:
    """The tree a result is drawn from (`result_latex`'s rule), or None. It is shared by every
    caller, so it is a tuple: copy it before editing."""
    parsed = _parsed(text)
    if parsed is None:
        return None
    node, row = parsed
    if (isinstance(node, ast.Name) and node.text in _MESSAGES) or _calls(node, _SYMPY_CALLS):
        return None
    return tuple(row)


def _parsed(text: str) -> tuple[ast.Expr, Row] | None:
    """The text's AST and its tree, if it parses and the tree reads back as the same value."""
    try:
        node = parse_expression(text)
        row = row_from_ast(node)
        if normal_form(parse_expression(linear_text(row))) == normal_form(node):
            return node, row
    except TIError, RecursionError:
        pass
    return None


def normal_form(value: Any) -> Any:  # noqa: ANN401 (any AST field)
    """The AST with the rewrite the tree makes undone in a single form: `(-a)/b`, drawn as −a over
    b with the minus outside the fraction, is `-(a/b)`."""
    if isinstance(value, tuple):
        return tuple(normal_form(item) for item in value)
    if not is_dataclass(value) or isinstance(value, type):
        return value
    node = replace(value, **{f.name: normal_form(getattr(value, f.name)) for f in fields(value)})
    match node:
        case ast.Binary(op="/", left=ast.Unary(op="-", operand=top), right=bottom):
            return ast.Unary("-", ast.Binary("/", top, bottom))
    return node


def _calls(node: Any, names: frozenset[str]) -> bool:  # noqa: ANN401 (any AST field)
    """Whether the AST calls any of `names`."""
    if isinstance(node, tuple):
        return any(_calls(item, names) for item in node)
    if not is_dataclass(node) or isinstance(node, type):
        return False
    if isinstance(node, ast.Call) and node.func in names:
        return True
    return any(_calls(getattr(node, f.name), names) for f in fields(node))


def row_from_ast(node: ast.Expr) -> Row:
    """The editor tree for an expression."""
    return _wrapped(node, 0)


def _wrapped(node: ast.Expr, outer: int) -> Row:
    """`node` as a row, bracketed if it binds more loosely than its context needs. A stacked
    fraction is its own bracket, except as the base of a power, where TI writes `(a/b)²`."""
    row = _row(node)
    stacked = isinstance(node, ast.Binary) and node.op == "/"
    if node.prec < outer and not (stacked and outer <= Prec.POWER):
        return ["(", *row, ")"]
    return row


def _row(node: ast.Expr) -> Row:  # noqa: PLR0911 (one case a node type)
    match node:
        case ast.Binary():
            return _binary(node)
        case ast.Unary(op="#", operand=operand):
            return ["#", *_wrapped(operand, Prec.ATOM)]
        case ast.Unary(op=op, operand=operand):
            body = _wrapped(operand, UNARY_OPERAND_PREC[op])
            return [*"not ", *body] if op == "not" else [op, *body]
        case ast.Postfix(op=op, operand=operand):
            return [*_wrapped(operand, Prec.POST), op]
        case ast.Call():
            return _call(node)
        case ast.Compare(first=first, rest=rest):
            out = _wrapped(first, Prec.COMPARE + 1)
            for op, term in rest:
                out += [op, *_wrapped(term, Prec.COMPARE + 1)]
            return out
        case ast.Matrix(rows=rows) if rows and len({len(r) for r in rows}) == 1:
            cells = [row_from_ast(cell) for r in rows for cell in r]
            return [Template(Kind.MATRIX, cells, len(rows[0]))]
        case ast.ListLit(items=items):
            return ["{", *_joined(items), "}"]
        case ast.Convert(value=value, target=target):
            return [*_wrapped(value, Prec.CONVERT), "▶", *str(target)]
        case _:  # numbers, names, strings, indexing: their own text reads back the same
            return list(str(node))


def _binary(node: ast.Binary) -> Row:
    if node.op == "/":
        top = node.left
        if isinstance(top, ast.Unary) and top.op == "-":  # −½, not (−1)/2: the minus goes in front
            return [
                "-",
                Template(Kind.FRACTION, [row_from_ast(top.operand), row_from_ast(node.right)]),
            ]
        return [Template(Kind.FRACTION, [row_from_ast(top), row_from_ast(node.right)])]
    if node.op == "^":
        return [
            *_wrapped(node.left, Prec.POWER + 1),
            Template(Kind.POWER, [row_from_ast(node.right)]),
        ]
    prec = node.prec
    if node.op in RIGHT_ASSOCIATIVE:  # `.^`, written linear as `ast.Binary` writes it
        left = _wrapped(node.left, prec + 1)
        negated = isinstance(node.right, ast.Unary) and node.right.op == "-"
        right = row_from_ast(node.right) if negated else _wrapped(node.right, prec)
    else:
        left, right = _wrapped(node.left, prec), _wrapped(node.right, prec + 1)
    joint = f" {node.op} " if node.op in _SPACED else node.op
    if node.op[0] == "." and isinstance(left[-1], str) and left[-1].isdigit():
        joint = " " + joint  # `1.+x` would read as the number `1.` plus x
    return [*left, *joint, *right]


def _call(node: ast.Call) -> Row:
    """A call a template is written as becomes that template (the first that fits, in the order
    `SPECS` lists them); any other call stays a name and its bracketed arguments."""
    for kind, spec in SPECS.items():
        call = spec.call
        if call is None or call.name != node.func or len(call.arguments) != len(node.args):
            continue
        pairs = list(zip(call.arguments, node.args, strict=True))
        if any(isinstance(want, str) and str(arg) != want for want, arg in pairs):
            continue  # a fixed argument (`2` for d²/dx²) that differs
        slots: list[Row] = [[] for _ in range(spec.slots)]
        for want, arg in pairs:
            if isinstance(want, int):
                slots[want] = row_from_ast(arg)
        return [Template(kind, slots)]
    return [*node.func, "(", *_joined(node.args), ")"]


def _joined(items: tuple[ast.Expr, ...]) -> Row:
    out: Row = []
    for index, item in enumerate(items):
        out += ([","] if index else []) + row_from_ast(item)
    return out
