"""Spike 6: a template (2D) math editor model, as on the handheld: fractions, powers, roots.

A document is a `Row` (list of nodes). A node is a one-character string or a template whose slots
are Rows. The cursor is a path of (node index, slot index) steps from the root row, plus a position
in the row it ends in. `linear()` writes the TI text the parser already reads; `latex()` draws the
tree with the cursor as a glyph, so any LaTeX renderer can show the editing state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

type Row = list[Node]


@dataclass
class Template:
    kind: str  # "frac" (num, den), "pow" (exp), "sqrt" (body)
    slots: list[Row] = field(default_factory=list)


type Node = str | Template
_SLOTS = {"frac": 2, "pow": 1, "sqrt": 1}
_TERM = set("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZπ")


def _new(kind: str) -> Template:
    return Template(kind, [[] for _ in range(_SLOTS[kind])])


class Editor:
    def __init__(self) -> None:
        self.root: Row = []
        self.path: list[tuple[int, int]] = []
        self.pos = 0

    # -- navigation helpers ---------------------------------------------------------------
    def row(self) -> Row:
        row = self.root
        for index, slot in self.path:
            node = row[index]
            assert isinstance(node, Template)
            row = node.slots[slot]
        return row

    def _enter(self, index: int, slot: int, *, at_end: bool = False) -> None:
        self.path.append((index, slot))
        self.pos = len(self.row()) if at_end else 0

    def _leave(self, *, after: bool) -> None:
        index, _ = self.path.pop()
        self.pos = index + (1 if after else 0)

    def _parent_node(self) -> Template:
        row = self.root
        for index, slot in self.path[:-1]:
            node = row[index]
            assert isinstance(node, Template)
            row = node.slots[slot]
        node = row[self.path[-1][0]]
        assert isinstance(node, Template)
        return node

    # -- editing ---------------------------------------------------------------------------
    def insert(self, char: str) -> None:
        if char == "/":
            self._fraction()
        elif char == "^":
            self._template("pow")
        elif char == "√":
            self._template("sqrt")
        else:
            self.row().insert(self.pos, char)
            self.pos += 1

    def _template(self, kind: str) -> None:
        self.row().insert(self.pos, _new(kind))
        self._enter(self.pos, 0)

    def _fraction(self) -> None:
        """The term before the cursor becomes the numerator, as on the handheld."""
        row = self.row()
        start = self.pos
        if start and row[start - 1] == ")":
            depth = 0
            while start:
                start -= 1
                if row[start] == ")":
                    depth += 1
                elif row[start] == "(":
                    depth -= 1
                    if depth == 0:
                        break
        else:
            while start and _is_term(row[start - 1]):
                start -= 1
        node = _new("frac")
        node.slots[0] = row[start : self.pos]
        row[start : self.pos] = [node]
        self.pos = start
        self._enter(start, 1)

    def backspace(self) -> None:
        row = self.row()
        if self.pos:
            prev = row[self.pos - 1]
            if isinstance(prev, Template):  # step into it first, so nothing is lost by accident
                self._enter(self.pos - 1, len(prev.slots) - 1, at_end=True)
            else:
                del row[self.pos - 1]
                self.pos -= 1
        elif self.path:
            self._dissolve()

    def _dissolve(self) -> None:
        """Backspace at the start of a slot: remove the template and keep its contents."""
        node = self._parent_node()
        index, slot = self.path.pop()
        row = self.row()
        before = sum(len(s) for s in node.slots[:slot])
        row[index : index + 1] = [item for s in node.slots for item in s]
        self.pos = index + before

    def left(self) -> None:
        row = self.row()
        if self.pos:
            prev = row[self.pos - 1]
            if isinstance(prev, Template):
                self._enter(self.pos - 1, len(prev.slots) - 1, at_end=True)
            else:
                self.pos -= 1
        elif self.path:
            index, slot = self.path[-1]
            if slot:
                self.path[-1] = (index, slot - 1)
                self.pos = len(self.row())
            else:
                self._leave(after=False)

    def right(self) -> None:
        row = self.row()
        if self.pos < len(row):
            node = row[self.pos]
            if isinstance(node, Template):
                self._enter(self.pos, 0)
            else:
                self.pos += 1
        elif self.path:
            index, slot = self.path[-1]
            if slot + 1 < len(self._parent_node().slots):
                self.path[-1] = (index, slot + 1)
                self.pos = 0
            else:
                self._leave(after=True)

    def vertical(self, *, up: bool) -> None:
        """Up and Down move between numerator and denominator."""
        if not self.path:
            return
        index, slot = self.path[-1]
        if self._parent_node().kind == "frac" and slot == (1 if up else 0):
            self.path[-1] = (index, slot - 1 if up else slot + 1)
            self.pos = min(self.pos, len(self.row()))

    # -- output ----------------------------------------------------------------------------
    def linear(self) -> str:
        """The TI text that the parser reads."""
        return _linear(self.root)

    def latex(self, *, cursor: bool = True) -> str:
        return _latex(self.root, (self.path, self.pos) if cursor else None, [])


def _is_term(node: Node) -> bool:
    return node in _TERM if isinstance(node, str) else node.kind == "pow"


def _linear(row: Row) -> str:
    out = []
    for node in row:
        if isinstance(node, str):
            out.append(node)
        elif node.kind == "frac":
            out.append(f"(({_linear(node.slots[0])})/({_linear(node.slots[1])}))")
        elif node.kind == "pow":
            out.append(f"^({_linear(node.slots[0])})")
        else:
            out.append(f"√({_linear(node.slots[0])})")
    return "".join(out)


_CURSOR = r"{\color{#4da3ff}\rule{0.06em}{1.0em}}"
_EMPTY = r"\square"
_ESC = {"*": r"\cdot ", "<": r"\lt ", ">": r"\gt ", "≤": r"\le ", "≥": r"\ge ", "{": r"\{", "}": r"\}"}


def _latex(
    row: Row, cursor: tuple[list[tuple[int, int]], int] | None, here: list[tuple[int, int]]
) -> str:
    here_cursor = cursor is not None and cursor[0] == here
    at = cursor[1] if cursor is not None else -1
    out = []
    if not row:
        out.append(_CURSOR if here_cursor else _EMPTY)
    for i, node in enumerate(row):
        if here_cursor and at == i:
            out.append(_CURSOR)
        if isinstance(node, str):
            out.append(_ESC.get(node, node))
            continue
        slots = [_latex(slot, cursor, [*here, (i, s)]) for s, slot in enumerate(node.slots)]
        if node.kind == "frac":
            out.append(rf"\frac{{{slots[0]}}}{{{slots[1]}}}")
        elif node.kind == "pow":
            out.append(rf"^{{{slots[0]}}}")
        else:
            out.append(rf"\sqrt{{{slots[0]}}}")
    if row and here_cursor and at == len(row):
        out.append(_CURSOR)
    return "".join(out)
