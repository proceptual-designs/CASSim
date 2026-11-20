"""Engine text as an editor tree (FR-CALC-004): the bridge from the core parser's AST to a `Row`.

A result brought down from the history must keep its structure: `(x-1)^2-1` has an exponent of
`2`, not `2-1`, and the `√` in `-√(3)*sin(π/9)` holds only `3`. Typing the text key by key cannot
know where a template ends, so the text is parsed with the real parser and the AST is turned into
templates (fraction, power, root, nth root, log, absolute value, matrix) and characters.

The tree's linear text parses back to the same AST (`row_from_text` checks it and falls back to a
plain paste if it ever does not), so a recalled value is never changed by the trip.
"""

from __future__ import annotations

from cassim.core import ast
from cassim.core.ast import RIGHT_ASSOCIATIVE, UNARY_OPERAND_PREC, Prec
from cassim.core.errors import TIError
from cassim.core.parser import parse_expression
from cassim.device.editor import Editor, Kind, Row, Template, linear_text

# Binary operators written with a space either side, as `ast.Binary` prints them
_SPACED = frozenset({"and", "or", "xor", "nor", "nand", "|"})
# Calls drawn as templates: the function name and the template's slots from the call's arguments
_CALL_TEMPLATES: dict[tuple[str, int], tuple[Kind, tuple[int, ...]]] = {
    ("√", 1): (Kind.ROOT, (0,)),
    ("root", 2): (Kind.NTH_ROOT, (1, 0)),  # root(x, n): index n, radicand x
    ("log", 2): (Kind.LOG, (1, 0)),  # log(x, b): base b, argument x
    ("abs", 1): (Kind.ABS, (0,)),
}


def row_from_text(text: str) -> Row:
    """The editor tree for engine text. Text the parser cannot read, or whose tree would not
    read back the same, is pasted as linear text instead."""
    try:
        expected = parse_expression(text)
        row = row_from_ast(expected)
        if parse_expression(linear_text(row)) == expected:
            return row
    except TIError, RecursionError:
        pass
    editor = Editor()
    editor.insert_linear(text)
    return editor.root


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
        return [Template(Kind.FRACTION, [row_from_ast(node.left), row_from_ast(node.right)])]
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
    template = _CALL_TEMPLATES.get((node.func, len(node.args)))
    if template is not None:
        kind, order = template
        return [Template(kind, [row_from_ast(node.args[i]) for i in order])]
    return [*node.func, "(", *_joined(node.args), ")"]


def _joined(items: tuple[ast.Expr, ...]) -> Row:
    out: Row = []
    for index, item in enumerate(items):
        out += ([","] if index else []) + row_from_ast(item)
    return out
