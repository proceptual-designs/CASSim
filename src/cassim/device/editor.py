"""The 2D input editor (FR-CALC-004): template editing as on the handheld.

A document is a `Row`, a list of nodes. A node is a one-character string or a `Template` whose
slots are Rows (a fraction has two, a power or a root has one). The cursor is a path of
(node index, slot index) steps from the root row, plus a position in the row where the path ends.

The editor has no Flet or Nspire knowledge. `linear()` writes the text the TI parser reads, so the
engine is unchanged, and `latex()` draws the tree with the cursor as a glyph for any LaTeX
renderer (decision 0015).
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

type Row = list[Node]
type Node = str | Template


class Kind(StrEnum):
    FRACTION = "fraction"  # numerator, denominator
    POWER = "power"  # exponent, attached to the term before it
    ROOT = "root"  # radicand
    MATRIX = "matrix"  # rows x columns of cells, row by row


_SLOTS = {Kind.FRACTION: 2, Kind.POWER: 1, Kind.ROOT: 1}
_TERM_CHARS = frozenset("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZπⅇⅈ_")
# What the fraction template takes as its numerator: terms and products, not sums (0017).
_NUMERATOR_CHARS = _TERM_CHARS | {"*"}
# An operator typed first on an empty line is applied to the last answer, as on the handheld.
_ANS_OPERATORS = frozenset("+-*/^")


@dataclass
class Template:
    kind: Kind
    slots: list[Row] = field(default_factory=list)
    cols: int = 0  # a matrix's columns; its rows are len(slots) // cols

    @classmethod
    def empty(cls, kind: Kind, shape: tuple[int, int] = (1, 1)) -> Template:
        if kind is Kind.MATRIX:
            rows, cols = shape
            return cls(kind, [[] for _ in range(rows * cols)], cols)
        return cls(kind, [[] for _ in range(_SLOTS[kind])])


class Editor:
    """One entry line being edited."""

    def __init__(self, text: str = "") -> None:
        self.root: Row = []
        self.path: list[tuple[int, int]] = []
        self.pos = 0
        self.selected = False  # the template just before the cursor is highlighted
        self.anchor: int | None = None  # the far end of a shift-arrow selection in this row
        self.insert_text(text)

    # ---- state ------------------------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        return not self.root

    def clear(self) -> None:
        self.root = []
        self.path = []
        self.pos = 0
        self.selected = False
        self.anchor = None

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
        """Type one character. `^` and `√` build templates; `/` stays linear, as on the handheld.

        The fraction is stacked only after Return or from the palette (`insert_template`).
        """
        self._unselect(replace=True)
        if char in _ANS_OPERATORS and not self.root:
            self.root.extend("Ans")
            self.pos = 3
        if char == "^":
            self.insert_template(Kind.POWER)
        elif char == "√":
            self.insert_template(Kind.ROOT)
        else:
            self.row().insert(self.pos, char)
            self.pos += 1

    def insert_template(self, kind: Kind, shape: tuple[int, int] = (2, 2)) -> None:
        """A template from the palette: empty slots, cursor in the first.

        A fraction takes the term before the cursor as its numerator and starts in the denominator,
        or takes the selection (S1 h).
        """
        if kind is Kind.FRACTION and self.anchor is not None:
            self._fraction(self.span)
            return
        self._unselect(replace=True)
        if kind is Kind.FRACTION:
            self._fraction()
        else:
            self.row().insert(self.pos, Template.empty(kind, shape))
            self._enter(self.pos, 0)

    def _fraction(self, selection: tuple[int, int] | None = None) -> None:
        row = self.row()
        if selection is not None:
            start, end = selection
            self.anchor = None
        else:
            start = end = self.pos
            while start and (row[start - 1] == ")" or _takes_numerator(row[start - 1])):
                start = _matching_open(row, start - 1) if row[start - 1] == ")" else start - 1
        numerator = row[start:end]
        if selection is None and _is_bracketed(numerator):
            numerator = numerator[1:-1]  # a plain bracketed sum loses its brackets
        fraction = Template.empty(Kind.FRACTION)
        fraction.slots[0] = numerator
        row[start:end] = [fraction]
        self.pos = start
        self._enter(start, 1 if numerator else 0)  # an empty numerator is filled first

    def _unselect(self, *, replace: bool = False) -> None:
        """Drop the highlight; typing over it deletes the highlighted template or selection."""
        if self.anchor is not None:
            low, high = self.span
            if replace:
                del self.row()[low:high]
            self.pos = low
            self.anchor = None
        if self.selected and replace:
            del self.row()[self.pos - 1]
            self.pos -= 1
        self.selected = False

    # ---- selecting --------------------------------------------------------------------------

    @property
    def span(self) -> tuple[int, int]:
        """The selected nodes of the current row, as `[low, high)`; empty when nothing is."""
        if self.anchor is None:
            return (self.pos, self.pos)
        return (min(self.anchor, self.pos), max(self.anchor, self.pos))

    def select_left(self) -> None:
        """Shift+Left: extend the selection by one node. A template counts as one unit (S5)."""
        self._extend(-1)

    def select_right(self) -> None:
        self._extend(1)

    def select_word_left(self) -> None:
        """Ctrl+Shift+Left: extend to the start of the word, or past one template."""
        self._extend_to(self._word_edge(-1))

    def select_word_right(self) -> None:
        self._extend_to(self._word_edge(1))

    def select_to_start(self) -> None:
        """Shift+Home: extend to the start of the row the cursor is in."""
        self._extend_to(0)

    def select_to_end(self) -> None:
        self._extend_to(len(self.row()))

    def _extend(self, step: int) -> None:
        self._extend_to(self.pos + step)

    def _extend_to(self, pos: int) -> None:
        """Move the free end of the selection. Running off the end of a slot selects the whole
        template in the row outside it, and the selection carries on from there."""
        self.selected = False
        if self.anchor is None:
            self.anchor = self.pos
        if (pos < 0 or pos > len(self.row())) and self.path:
            index, _ = self.path.pop()
            self.anchor, self.pos = (index + 1, index) if pos < 0 else (index, index + 1)
            return
        self.pos = max(0, min(pos, len(self.row())))
        if self.pos == self.anchor:
            self.anchor = None

    def word_left(self) -> None:
        """Ctrl+Left: collapse any selection, then move to the start of the word."""
        self._unselect()
        self.pos = self._word_edge(-1)

    def word_right(self) -> None:
        if self.anchor is not None:
            self.pos = self.span[1]
            self.anchor = None
        self._unselect()
        self.pos = self._word_edge(1)

    def _word_edge(self, step: int) -> int:
        """Where a word move from the cursor lands: over a run of letters and digits, a run of
        other characters, or one template; trailing spaces are skipped going right."""
        row = self.row()

        def kind(index: int) -> str:
            node = row[index]
            if isinstance(node, Template):
                return "template"
            if node == " ":
                return "space"
            return "word" if node in _TERM_CHARS else "other"

        pos = self.pos
        if step > 0:
            if pos >= len(row):
                return pos
            first = kind(pos)
            pos += 1
            while first not in ("template", "space") and pos < len(row) and kind(pos) == first:
                pos += 1
            while pos < len(row) and kind(pos) == "space":
                pos += 1
            return pos
        while pos and kind(pos - 1) == "space":
            pos -= 1
        if not pos:
            return 0
        first = kind(pos - 1)
        pos -= 1
        while first != "template" and pos and kind(pos - 1) == first:
            pos -= 1
        return pos

    # ---- clipboard --------------------------------------------------------------------------

    def selection(self) -> Row:
        """A copy of the selected nodes (templates intact), or the highlighted template."""
        if self.anchor is not None:
            low, high = self.span
            return copy.deepcopy(self.row()[low:high])
        if self.selected:
            return copy.deepcopy([self.row()[self.pos - 1]])
        return []

    def cut(self) -> Row:
        nodes = self.selection()
        self._unselect(replace=True)
        return nodes

    def paste(self, nodes: Row) -> None:
        """Insert copies of `nodes` at the cursor, replacing any selection."""
        self._unselect(replace=True)
        row = self.row()
        row[self.pos : self.pos] = copy.deepcopy(nodes)
        self.pos += len(nodes)

    def select_all(self) -> None:
        """Ctrl+A: the whole entry line."""
        self.selected = False
        self.path = []
        self.anchor = 0 if self.root else None
        self.pos = len(self.root)

    # ---- deleting ---------------------------------------------------------------------------

    def backspace(self) -> None:
        """Just after a template the first press highlights it and the second deletes it (0017)."""
        row = self.row()
        if self.anchor is not None or self.selected:
            self._unselect(replace=True)
        elif self.pos:
            previous = row[self.pos - 1]
            if isinstance(previous, Template):
                self.selected = True
            else:
                del row[self.pos - 1]
                self.pos -= 1
        elif self.path:
            self._dissolve()

    def delete(self) -> None:
        if self.anchor is not None or self.selected:
            self._unselect(replace=True)
            return
        row = self.row()
        if self.pos < len(row):
            node = row[self.pos]
            if isinstance(node, Template):
                self.pos += 1  # forward delete highlights the template first
                self.selected = True
            else:
                del row[self.pos]

    def _dissolve(self) -> None:
        """Backspace at the start of a slot removes the template and keeps what was in it.

        At the start of a template's first slot it highlights the whole template instead, or deletes
        it when it is empty.
        """
        template = self._parent()
        if template.kind is Kind.MATRIX and self.path[-1][1] > 0:  # cells do not merge: step back
            index, slot = self.path[-1]
            self.path[-1] = (index, slot - 1)
            self.pos = len(self.row())
            return
        index, slot = self.path.pop()
        if slot == 0:
            if any(template.slots):
                self.pos = index + 1
                self.selected = True
            else:
                del self.row()[index]
                self.pos = index
            return
        before = sum(len(s) for s in template.slots[:slot])
        self.row()[index : index + 1] = [item for s in template.slots for item in s]
        self.pos = index + before

    # ---- moving -----------------------------------------------------------------------------

    def left(self) -> None:
        if self.anchor is not None:  # a selection collapses to its left edge
            self._unselect()
            return
        self._unselect()
        row = self.row()
        if self.pos:
            previous = row[self.pos - 1]
            if isinstance(previous, Template):
                self._enter(self.pos - 1, len(previous.slots) - 1, at_end=True)
            else:
                self.pos -= 1
        elif self.path:
            index, _ = self.path.pop()  # Left from the start of any slot leaves on the left
            self.pos = index

    def shift_tab(self) -> None:
        """The reverse of Tab: the previous slot, then out to the left of the template."""
        self._unselect()
        if not self.path:
            self.left()
            return
        index, slot = self.path[-1]
        if slot:
            self.path[-1] = (index, slot - 1)
            self.pos = len(self.row())
        else:
            self.path.pop()
            self.pos = index

    def right(self) -> None:
        """Right leaves the slot it is in, even the numerator of a fraction (0017)."""
        if self.anchor is not None:  # a selection collapses to its right edge
            self.pos = self.span[1]
            self.anchor = None
            return
        self._unselect()
        row = self.row()
        if self.pos < len(row):
            node = row[self.pos]
            if isinstance(node, Template):
                self._enter(self.pos, 0)
            else:
                self.pos += 1
        elif self.path:
            index, _ = self.path.pop()
            self.pos = index + 1

    def tab(self) -> None:
        """Tab visits the slots in order, then leaves the template."""
        self._unselect()
        if not self.path:
            return
        index, slot = self.path[-1]
        if slot + 1 < len(self._parent().slots):
            self.path[-1] = (index, slot + 1)
            self.pos = 0
        else:
            self.path.pop()
            self.pos = index + 1

    def up(self) -> None:
        self._between_rows(from_slot=1, step=-1)

    def down(self) -> None:
        self._between_rows(from_slot=0, step=1)

    def _between_rows(self, *, from_slot: int, step: int) -> None:
        """Up and Down: between the two slots of a fraction, or between a matrix's rows."""
        self._unselect()
        if not self.path:
            return
        index, slot = self.path[-1]
        parent = self._parent()
        target = slot
        if parent.kind is Kind.FRACTION and slot == from_slot:
            target = 1 - from_slot
        elif parent.kind is Kind.MATRIX and 0 <= slot + step * parent.cols < len(parent.slots):
            target = slot + step * parent.cols
        if target != slot:
            self.path[-1] = (index, target)
            self.pos = min(self.pos, len(self.row()))

    def home(self) -> None:
        self._unselect()
        self.path = []
        self.pos = 0

    def end(self) -> None:
        self._unselect()
        self.path = []
        self.pos = len(self.root)

    # ---- output -----------------------------------------------------------------------------

    def linear(self) -> str:
        """The TI text for the parser."""
        return _linear(self.root)

    def latex(
        self, *, cursor: bool = True, is_function: Callable[[str], bool] = lambda _: False
    ) -> str:
        """LaTeX for the entry, with the cursor drawn as a bar and empty slots as boxes. Names
        that `is_function` accepts are bold."""
        place = (self.path, self.pos, self.span) if cursor else None
        return _latex(self.root, place, [], is_function)


def linear_text(nodes: Row) -> str:
    """The TI text of some nodes, as for the system clipboard."""
    return _linear(nodes)


def _template(node: Node) -> Template:
    assert isinstance(node, Template)
    return node


def _takes_numerator(node: Node) -> bool:
    return node in _NUMERATOR_CHARS if isinstance(node, str) else True  # any template is a term


def _is_bracketed(run: Row) -> bool:
    if not run or run[0] != "(" or run[-1] != ")":
        return False
    return _matching_open(run, len(run) - 1) == 0 and len(run) > len("()")


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
        elif node.kind is Kind.MATRIX:
            cells = [_linear(slot) for slot in node.slots]
            rows = [",".join(cells[i : i + node.cols]) for i in range(0, len(cells), node.cols)]
            out.append("[" + ";".join(rows) + "]")
        else:
            out.append(f"√({_linear(node.slots[0])})")
    return "".join(out)


# Digit height with a little depth: a taller bar pushes a denominator down.
_CURSOR = r"{\color{#4da3ff}\rule[-0.15em]{0.06em}{0.8em}}"
_CURSOR_IN_SELECTION = r"{\color{#0b3d78}\rule[-0.15em]{0.06em}{0.8em}}"  # darker on the highlight
_EMPTY_SLOT = r"\square"
_SELECTION = "#7fb2e8"
_SYMBOLS = {
    "*": r"\cdot ",
    "\\": r"\backslash ",
    "~": r"\sim ",
    "|": r"\vert ",
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


def _function_names(row: Row, is_function: Callable[[str], bool]) -> set[int]:
    """Indices of letters that spell a defined function followed by `(`, such as `sin` in
    `sin(x)` or a user's `f` in `f(x)`. A name nothing defines stays plain."""
    marked: set[int] = set()
    run: list[int] = []
    for index, node in enumerate([*row, ""]):
        if isinstance(node, str) and node.isascii() and (node.isalpha() or node == "_"):
            run.append(index)
            continue
        if run and node == "(":
            name = "".join(str(row[i]) for i in run)
            if is_function(name):
                marked.update(run)
        run = []
    return marked


type Place = tuple[list[tuple[int, int]], int, tuple[int, int]]


def _latex(
    row: Row, place: Place | None, here: list[tuple[int, int]], is_function: Callable[[str], bool]
) -> str:
    """The row as LaTeX. `place` is the cursor's path, its position and the selected span."""
    here_cursor = place is not None and place[0] == here
    at = place[1] if place is not None else -1
    low, high = place[2] if here_cursor and place is not None else (0, 0)
    names = _function_names(row, is_function)
    if not row:
        return _CURSOR if here_cursor else _EMPTY_SLOT
    pieces: list[str] = []
    for i, node in enumerate(row):
        if isinstance(node, str):
            pieces.append(rf"\mathbf{{{node}}}" if i in names else _SYMBOLS.get(node, node))
            continue
        slots = [
            _latex(slot, place, [*here, (i, s)], is_function) for s, slot in enumerate(node.slots)
        ]
        if node.kind is Kind.FRACTION:
            pieces.append(rf"\frac{{{slots[0]}}}{{{slots[1]}}}")
        elif node.kind is Kind.MATRIX:
            rows = [slots[i : i + node.cols] for i in range(0, len(slots), node.cols)]
            body = r" \\ ".join(" & ".join(row) for row in rows)
            pieces.append(rf"\left[\begin{{matrix}}{body}\end{{matrix}}\right]")
        elif node.kind is Kind.POWER:
            pieces.append(rf"{{}}^{{{slots[0]}}}")  # `{}` keeps a power at the start of a row valid
        else:
            pieces.append(rf"\sqrt{{{slots[0]}}}")
    cursor = _CURSOR if here_cursor else ""
    if high > low:
        chosen = "".join(pieces[low:high])
        if here_cursor:  # the cursor sits inside the highlight at its edge, so no gap opens
            bar = _CURSOR_IN_SELECTION
            chosen = bar + chosen if at == low else chosen + bar
        # \colorbox draws no fill; \fcolorbox pads by 0.34em, so pull the contents back to its edges
        box = (
            rf"\fcolorbox{{{_SELECTION}}}{{{_SELECTION}}}"
            rf"{{$\kern-0.34em {chosen}\kern-0.34em$}}"
        )
        return "".join(pieces[:low]) + box + "".join(pieces[high:])
    if not here_cursor:
        return "".join(pieces)
    return "".join(pieces[:at]) + cursor + "".join(pieces[at:])
