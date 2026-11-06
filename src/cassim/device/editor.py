"""The 2D input editor (FR-CALC-004): template editing as on the handheld.

A document is a `Row`, a list of nodes. A node is a one-character string or a `Template` whose
slots are Rows (a fraction has two, a power or a root has one). The cursor is a path of
(node index, slot index) steps from the root row, plus a position in the row where the path ends.

The editor has no Flet or Nspire knowledge. `linear()` writes the text the TI parser reads, so the
engine is unchanged, and `latex()` draws the tree with the cursor as a glyph for any LaTeX
renderer (decision 0015).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

type Row = list[Node]
type Node = str | Template


class Kind(StrEnum):
    FRACTION = "fraction"  # numerator, denominator
    POWER = "power"  # exponent, attached to the term before it
    ROOT = "root"  # radicand


_SLOTS = {Kind.FRACTION: 2, Kind.POWER: 1, Kind.ROOT: 1}
_TERM_CHARS = frozenset("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZπⅇⅈ_")


@dataclass
class Template:
    kind: Kind
    slots: list[Row] = field(default_factory=list)

    @classmethod
    def empty(cls, kind: Kind) -> Template:
        return cls(kind, [[] for _ in range(_SLOTS[kind])])


class Editor:
    """One entry line being edited."""

    def __init__(self, text: str = "") -> None:
        self.root: Row = []
        self.path: list[tuple[int, int]] = []
        self.pos = 0
        self.insert_text(text)

    # ---- state ------------------------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        return not self.root

    def clear(self) -> None:
        self.root = []
        self.path = []
        self.pos = 0

    def row(self) -> Row:
        """The row the cursor is in."""
        row = self.root
        for index, slot in self.path:
            row = _template(row[index]).slots[slot]
        return row

    def _parent(self) -> Template:
        row = self.root
        for index, slot in self.path[:-1]:
            row = _template(row[index]).slots[slot]
        return _template(row[self.path[-1][0]])

    def _enter(self, index: int, slot: int, *, at_end: bool = False) -> None:
        self.path.append((index, slot))
        self.pos = len(self.row()) if at_end else 0

    # ---- typing -----------------------------------------------------------------------------

    def insert_text(self, text: str) -> None:
        for char in text:
            self.insert(char)

    def insert(self, char: str) -> None:
        """Type one character. `/`, `^` and `√` build templates as on the handheld."""
        if char == "/":
            self._fraction()
        elif char == "^":
            self.insert_template(Kind.POWER)
        elif char == "√":
            self.insert_template(Kind.ROOT)
        else:
            self.row().insert(self.pos, char)
            self.pos += 1

    def insert_template(self, kind: Kind) -> None:
        """A template from the palette: empty slots, cursor in the first."""
        self.row().insert(self.pos, Template.empty(kind))
        self._enter(self.pos, 0)

    def _fraction(self) -> None:
        """The term before the cursor becomes the numerator."""
        row = self.row()
        start = self.pos
        if start and row[start - 1] == ")":
            start = _matching_open(row, start - 1)
        else:
            while start and _is_term(row[start - 1]):
                start -= 1
        fraction = Template.empty(Kind.FRACTION)
        fraction.slots[0] = row[start : self.pos]
        row[start : self.pos] = [fraction]
        self.pos = start
        self._enter(start, 1)

    # ---- deleting ---------------------------------------------------------------------------

    def backspace(self) -> None:
        row = self.row()
        if self.pos:
            previous = row[self.pos - 1]
            if isinstance(previous, Template):
                # Step into the template first, so one key press never deletes a whole fraction.
                self._enter(self.pos - 1, len(previous.slots) - 1, at_end=True)
            else:
                del row[self.pos - 1]
                self.pos -= 1
        elif self.path:
            self._dissolve()

    def delete(self) -> None:
        row = self.row()
        if self.pos < len(row):
            node = row[self.pos]
            if isinstance(node, Template):
                self._enter(self.pos, 0)
            else:
                del row[self.pos]

    def _dissolve(self) -> None:
        """Backspace at the start of a slot removes the template and keeps what was in it."""
        template = self._parent()
        index, slot = self.path.pop()
        before = sum(len(s) for s in template.slots[:slot])
        self.row()[index : index + 1] = [item for s in template.slots for item in s]
        self.pos = index + before

    # ---- moving -----------------------------------------------------------------------------

    def left(self) -> None:
        row = self.row()
        if self.pos:
            previous = row[self.pos - 1]
            if isinstance(previous, Template):
                self._enter(self.pos - 1, len(previous.slots) - 1, at_end=True)
            else:
                self.pos -= 1
        elif self.path:
            index, slot = self.path[-1]
            if slot:
                self.path[-1] = (index, slot - 1)
                self.pos = len(self.row())
            else:
                self.path.pop()
                self.pos = index

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
            if slot + 1 < len(self._parent().slots):
                self.path[-1] = (index, slot + 1)
                self.pos = 0
            else:
                self.path.pop()
                self.pos = index + 1

    def up(self) -> None:
        self._between_fraction_rows(from_slot=1)

    def down(self) -> None:
        self._between_fraction_rows(from_slot=0)

    def _between_fraction_rows(self, *, from_slot: int) -> None:
        if not self.path:
            return
        index, slot = self.path[-1]
        if self._parent().kind is Kind.FRACTION and slot == from_slot:
            self.path[-1] = (index, 1 - from_slot)
            self.pos = min(self.pos, len(self.row()))

    def home(self) -> None:
        self.path = []
        self.pos = 0

    def end(self) -> None:
        self.path = []
        self.pos = len(self.root)

    # ---- output -----------------------------------------------------------------------------

    def linear(self) -> str:
        """The TI text for the parser."""
        return _linear(self.root)

    def latex(self, *, cursor: bool = True) -> str:
        """LaTeX for the entry, with the cursor drawn as a bar and empty slots as boxes."""
        return _latex(self.root, (self.path, self.pos) if cursor else None, [])


def _template(node: Node) -> Template:
    assert isinstance(node, Template)
    return node


def _is_term(node: Node) -> bool:
    return node in _TERM_CHARS if isinstance(node, str) else True  # any template is a term


def _matching_open(row: Row, close: int) -> int:
    """Index of the `(` that matches the `)` at `close`; 0 if the brackets are unbalanced."""
    depth = 0
    for index in range(close, -1, -1):
        if row[index] == ")":
            depth += 1
        elif row[index] == "(":
            depth -= 1
            if depth == 0:
                return index
    return 0


def _linear(row: Row) -> str:
    out: list[str] = []
    for node in row:
        if isinstance(node, str):
            out.append(node)
        elif node.kind is Kind.FRACTION:
            out.append(f"(({_linear(node.slots[0])})/({_linear(node.slots[1])}))")
        elif node.kind is Kind.POWER:
            out.append(f"^({_linear(node.slots[0])})")
        else:
            out.append(f"√({_linear(node.slots[0])})")
    return "".join(out)


_CURSOR = r"{\color{#4da3ff}\rule{0.06em}{1.0em}}"
_EMPTY_SLOT = r"\square"
_SYMBOLS = {
    "*": r"\cdot ",
    "<": r"\lt ",
    ">": r"\gt ",
    "≤": r"\le ",
    "≥": r"\ge ",
    "≠": r"\ne ",
    "{": r"\{",
    "}": r"\}",
    "π": r"\pi ",
    "∞": r"\infty ",
    "ⅇ": r"\mathrm{e}",
    "ⅈ": r"\mathrm{i}",
    "%": r"\%",
    "_": r"\_",
    "#": r"\#",
    "&": r"\&",
    "$": r"\$",
    "∠": r"\angle ",
    "°": r"^\circ ",
    "→": r"\to ",
    "▶": r"\triangleright ",
    "ᴇ": r"\mathrm{E}",
}


def _function_names(row: Row) -> set[int]:
    """Indices of letters that spell a name followed by `(`, such as the `sin` in `sin(x)`."""
    marked: set[int] = set()
    run: list[int] = []
    for index, node in enumerate([*row, ""]):
        if isinstance(node, str) and node.isascii() and node.isalpha():
            run.append(index)
            continue
        followed_by_bracket = isinstance(node, str) and node == "("
        if len(run) > 1 and followed_by_bracket:
            marked.update(run)
        run = []
    return marked


def _latex(
    row: Row, cursor: tuple[list[tuple[int, int]], int] | None, here: list[tuple[int, int]]
) -> str:
    here_cursor = cursor is not None and cursor[0] == here
    at = cursor[1] if cursor is not None else -1
    names = _function_names(row)
    out: list[str] = []
    if not row:
        out.append(_CURSOR if here_cursor else _EMPTY_SLOT)
    for i, node in enumerate(row):
        if here_cursor and at == i:
            out.append(_CURSOR)
        if isinstance(node, str):
            out.append(rf"\mathrm{{{node}}}" if i in names else _SYMBOLS.get(node, node))
            continue
        slots = [_latex(slot, cursor, [*here, (i, s)]) for s, slot in enumerate(node.slots)]
        if node.kind is Kind.FRACTION:
            out.append(rf"\frac{{{slots[0]}}}{{{slots[1]}}}")
        elif node.kind is Kind.POWER:
            out.append(rf"{{}}^{{{slots[0]}}}")  # `{}` keeps a power at the start of a row valid
        else:
            out.append(rf"\sqrt{{{slots[0]}}}")
    if row and here_cursor and at == len(row):
        out.append(_CURSOR)
    return "".join(out)
