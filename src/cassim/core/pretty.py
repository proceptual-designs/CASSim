"""Draw a result as text in two dimensions: fractions, roots, powers and matrices.

The input is the same AST that `format.to_text` prints, so the digits, `ⅇ`, `π` and `sin⁻¹` come
out as they do in the linear text. Like SymPy's `pprint`, each result is a block of lines with a
baseline, and blocks are joined side by side along their baselines.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from cassim.core import ast
from cassim.core.ast import Prec

_ROUND, _SQUARE, _CURLY = "round", "square", "curly"
_UNICODE_FENCES = {
    _ROUND: ("⎛⎜⎝", "⎞⎟⎠"),
    _SQUARE: ("⎡⎢⎣", "⎤⎥⎦"),
    _CURLY: ("⎧⎪⎩", "⎫⎪⎭"),
}
_ASCII_FENCES = {
    _ROUND: ("/|\\", "\\|/"),
    _SQUARE: ("/|\\", "\\|/"),
    _CURLY: ("/|\\", "\\|/"),
}
_SINGLE = {_ROUND: ("(", ")"), _SQUARE: ("[", "]"), _CURLY: ("{", "}")}
_TALL = 2  # a block this many lines high needs fences drawn in pieces


@dataclass(frozen=True, slots=True)
class Block:
    """Lines of equal width, and the index of the line that sits on the text baseline."""

    lines: tuple[str, ...]
    base: int = 0

    @property
    def width(self) -> int:
        return len(self.lines[0])

    @property
    def below(self) -> int:
        return len(self.lines) - self.base


def _text(text: str) -> Block:
    return Block((text,))


def _across(blocks: list[Block]) -> Block:
    """Put blocks side by side so that their baselines line up."""
    above = max(b.base for b in blocks)
    below = max(b.below for b in blocks)
    rows = []
    for row in range(above + below):
        parts = []
        for block in blocks:
            index = row - (above - block.base)
            parts.append(block.lines[index] if 0 <= index < len(block.lines) else " " * block.width)
        rows.append("".join(parts))
    return Block(tuple(rows), above)


def _padded(block: Block, width: int) -> Block:
    """Centre a block in `width` columns."""
    extra = width - block.width
    left = extra // 2
    return Block(
        tuple(" " * left + line + " " * (extra - left) for line in block.lines), block.base
    )


class Painter:
    """Lays out an AST. `unicode=False` keeps to the characters of a plain keyboard."""

    def __init__(self, *, unicode: bool) -> None:
        self._unicode = unicode
        self._drawers: dict[type, Callable[[Any], Block]] = {
            ast.Call: self._call,
            ast.Index: self._index,
            ast.ListLit: self._list,
            ast.Matrix: self._matrix,
            ast.Unary: self._unary,
            ast.Postfix: self._postfix,
            ast.Binary: self._binary,
            ast.Compare: self._compare,
            ast.Convert: self._convert,
        }

    def draw(self, node: ast.Expr) -> Block:
        if isinstance(node, ast.Call) and node.func == "√" and len(node.args) == 1:
            return self._root(self.draw(node.args[0]))
        if isinstance(node, ast.Number | ast.Name | ast.String | ast.Dms):
            return _text(str(node))
        return self._drawers[type(node)](node)

    def _postfix(self, node: ast.Postfix) -> Block:
        return _across([self._wrapped(node.operand, Prec.POST), _text(node.op)])

    def _convert(self, node: ast.Convert) -> Block:
        value = self._wrapped(node.value, Prec.CONVERT)
        return _across([value, _text("▶"), _text(str(node.target))])

    def _list(self, node: ast.ListLit) -> Block:
        return self._fenced(self._separated(node.items), _CURLY)

    def _separated(self, items: tuple[ast.Expr, ...]) -> Block:
        parts: list[Block] = []
        for index, item in enumerate(items):
            if index:
                parts.append(_text(", "))
            parts.append(self.draw(item))
        return _across(parts) if parts else _text("")

    def _fenced(self, block: Block, kind: str) -> Block:
        if len(block.lines) < _TALL:
            left, right = _SINGLE[kind]
            return _across([_text(left), block, _text(right)])
        left_set, right_set = (_UNICODE_FENCES if self._unicode else _ASCII_FENCES)[kind]
        height = len(block.lines)

        def side(glyphs: str) -> Block:
            top, middle, bottom = glyphs
            return Block((top, *[middle] * (height - 2), bottom), block.base)

        return _across([side(left_set), block, side(right_set)])

    def _wrapped(self, node: ast.Expr, minimum: int, *, fraction_ok: bool = False) -> Block:
        """Draw `node`, in parentheses if linear text would need them."""
        block = self.draw(node)
        grouped = fraction_ok and isinstance(node, ast.Binary) and node.op == "/"
        return self._fenced(block, _ROUND) if node.prec < minimum and not grouped else block

    def _call(self, node: ast.Call) -> Block:
        return _across([_text(node.func), self._fenced(self._separated(node.args), _ROUND)])

    def _index(self, node: ast.Index) -> Block:
        base = node.base
        head = (
            self._fenced(self.draw(base), _ROUND)
            if isinstance(base, ast.Number)
            else (self._wrapped(base, Prec.POST))
        )
        return _across([head, self._fenced(self._separated(node.subscripts), _SQUARE)])

    def _matrix(self, node: ast.Matrix) -> Block:
        grid = [[self.draw(cell) for cell in row] for row in node.rows]
        widths = [
            max(row[c].width for row in grid if c < len(row)) for c in range(max(map(len, grid)))
        ]
        rows = []
        for row in grid:
            parts: list[Block] = []
            for column, cell in enumerate(row):
                if column:
                    parts.append(_text("  "))
                parts.append(_padded(cell, widths[column]))
            rows.append(_across(parts))
        height = sum(len(r.lines) for r in rows)
        lines: list[str] = []
        width = max(r.width for r in rows)
        for row in rows:
            lines += [line.ljust(width) for line in row.lines]
        return self._fenced(Block(tuple(lines), (height - 1) // 2), _SQUARE)

    def _unary(self, node: ast.Unary) -> Block:
        if node.op == "#":
            return _across([_text("#"), self._wrapped(node.operand, Prec.ATOM)])
        operand = self._wrapped(node.operand, ast.UNARY_OPERAND_PREC[node.op], fraction_ok=True)
        return _across([_text("not " if node.op == "not" else node.op), operand])

    def _binary(self, node: ast.Binary) -> Block:
        op = node.op
        if op == "/":
            return self._fraction(node)
        if op == "^":
            return self._power(node)
        prec = node.prec
        left = self._wrapped(node.left, prec, fraction_ok=True)
        right = self._wrapped(node.right, prec + 1, fraction_ok=True)
        if op == "*":
            return _across([left, _text("·" if self._unicode else "*"), right])
        spaced = op in {"+", "-", "|", "⇔", "⇒"} or (op in ast.BINARY_PREC and op.isalpha())
        return _across([left, _text(f" {op} " if spaced else op), right])

    def _compare(self, node: ast.Compare) -> Block:
        parts = [self._wrapped(node.first, Prec.COMPARE + 1, fraction_ok=True)]
        for op, term in node.rest:
            parts += [_text(f" {op} "), self._wrapped(term, Prec.COMPARE + 1, fraction_ok=True)]
        return _across(parts)

    def _fraction(self, node: ast.Binary) -> Block:
        numerator, denominator = self.draw(node.left), self.draw(node.right)
        width = max(numerator.width, denominator.width) + 2
        bar = _text(("─" if self._unicode else "-") * width)
        top, bottom = _padded(numerator, width), _padded(denominator, width)
        return Block((*top.lines, *bar.lines, *bottom.lines), len(top.lines))

    def _power(self, node: ast.Binary) -> Block:
        base = self._wrapped(node.left, Prec.POWER + 1)
        exponent = self.draw(node.right)
        pad = " " * exponent.width
        # The exponent sits above the base, to its right.
        raised = [" " * base.width + line for line in exponent.lines]
        lines = (*raised, *(line + pad for line in base.lines))
        return Block(lines, len(raised) + base.base)

    def _root(self, inner: Block) -> Block:
        bar = ("▁" if self._unicode else "_") * inner.width
        radical = "√" if self._unicode else "\\/"
        pad = " " * len(radical)
        rows = [pad + " " + bar]
        for index, line in enumerate(inner.lines):
            prefix = radical if index == inner.base else pad
            rows.append(f"{prefix} {line}")
        return Block(tuple(rows), inner.base + 1)

    def block(self, node: ast.Expr) -> str:
        return "\n".join(line.rstrip() for line in self.draw(node).lines)


def draw(node: ast.Expr, *, unicode: bool = True) -> str:
    """The lines that show `node` in two dimensions."""
    return Painter(unicode=unicode).block(node)
