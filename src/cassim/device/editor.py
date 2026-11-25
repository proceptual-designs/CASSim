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
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from cassim.core.builtin_names import is_builtin, spelling
from cassim.core.parser import COMMANDS
from cassim.device.accents import next_accent
from cassim.device.templates import GRIDS, SPECS, WALKED, Kind

__all__ = [
    "EMPTY_SLOT",
    "GRIDS",
    "MARK",
    "WALKED",
    "Editor",
    "Kind",
    "Node",
    "Row",
    "Template",
    "row_latex",
]

MARK = "▮"  # in text for `insert_linear`: where to leave the cursor

type Row = list[Node]
type Node = str | Template


_TERM_CHARS = frozenset("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZπⅇⅈ_")
# What the fraction template takes as its numerator: terms and products, not sums (0017).
_NUMERATOR_CHARS = _TERM_CHARS | {"*"}
# An operator typed first on an empty line is applied to the last answer, as on the handheld.
_ANS_OPERATORS = frozenset("+-*/^")


@dataclass
class Template:
    kind: Kind
    slots: list[Row] = field(default_factory=list)
    cols: int = 0  # a grid's columns (matrix, piecewise, system); its rows are len(slots) // cols

    @classmethod
    def empty(cls, kind: Kind, shape: tuple[int, int] = (1, 1)) -> Template:
        """Empty slots. `shape` is (rows, columns) for a grid; piecewise and system templates
        have fixed columns, so only the rows count."""
        if kind in GRIDS:
            rows, cols = shape
            cols = GRIDS[kind] or cols
            return cls(kind, [[] for _ in range(rows * cols)], cols)
        return cls(kind, [[] for _ in range(SPECS[kind].slots)])


class Editor:
    """One entry line being edited."""

    def __init__(self, text: str = "") -> None:
        self.root: Row = []
        self.path: list[tuple[int, int]] = []
        self.pos = 0
        self.selected = False  # the template just before the cursor is highlighted
        self.anchor: int | None = None  # the far end of a shift-arrow selection in this row
        # Whole rows or columns of the matrix the cursor is in: (axis, anchor, free) with axis
        # "row" or "col" and the two ends as indices of that axis.
        self.cell_sel: tuple[str, int, int] | None = None
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
        self.cell_sel = None

    def row(self) -> Row:
        """The row the cursor is in."""
        row = self.root
        for index, slot in self.path:
            row = _template(row[index]).slots[slot]
        return row

    @property
    def in_grid(self) -> bool:
        """Whether the cursor is in a matrix-like template."""
        return bool(self.path and self._parent().kind in GRIDS)

    @property
    def in_string(self) -> bool:
        """Whether the cursor is inside quoted text."""
        row = self.root
        prefix = ""
        for index, slot in self.path:
            prefix += linear_text(row[:index])
            row = _template(row[index]).slots[slot]
        prefix += linear_text(row[: self.pos])
        return prefix.count('"') % 2 == 1

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
        """Type `text` key by key: a `^` opens an exponent that the rest is typed into."""
        for char in text:
            self.insert(char)

    def insert_linear(self, text: str, mark: str = "") -> None:
        """Paste linear text as the parser reads it: `^` takes only its operand (a bracketed group
        or a run of term characters) and `√(…)` is a root, so `x^2+1` is x² + 1, not x^(2+1).
        `mark`, if given, is a character in `text` where the cursor is left."""
        self._unselect(replace=True)
        spot = self._paste_linear(text, mark)
        if spot is not None:
            self.path, self.pos = spot

    def _paste_linear(self, text: str, mark: str) -> tuple[list[tuple[int, int]], int] | None:
        spot: tuple[list[tuple[int, int]], int] | None = None
        index = 0
        quoted = self.in_string
        while index < len(text):
            char = text[index]
            if mark and char == mark:
                spot = (list(self.path), self.pos)
                index += 1
            elif char in "^√" and not quoted:
                operand, index = _operand(text, index + 1, root=char == "√")
                self.insert_template(Kind.POWER if char == "^" else Kind.ROOT)
                spot = self._paste_linear(operand, mark) or spot
                self.right()  # out of the template
            else:
                self.row().insert(self.pos, char)
                self.pos += 1
                index += 1
                if char == '"':
                    quoted = not quoted
        return spot

    def insert(self, char: str) -> None:
        """Type one character. `^` and `√` build templates; `/` stays linear, as on the handheld.

        The fraction is stacked only after Return or from the palette (`insert_template`).
        """
        self._unselect(replace=True)
        quoted = self.in_string
        if char == "," and not quoted and self.path and self._parent().kind is Kind.LIST:
            self._split_list_cell()
            return
        if char in _ANS_OPERATORS and not self.root:
            self.root.extend("Ans")
            self.pos = 3
        if char == "^" and not quoted:
            self.insert_template(Kind.POWER)
        elif char == "√" and not quoted:
            self.insert_template(Kind.ROOT)
        else:
            self.row().insert(self.pos, char)
            self.pos += 1

    def cycle_accent(self) -> None:
        """The accent key: the letter just before the cursor becomes its next accented form
        (`e`, `è`, `é`, ...). Anything else before the cursor, or a selection, is left alone."""
        row = self.row()
        if self.anchor is not None or self.pos == 0:
            return
        before = row[self.pos - 1]
        changed = next_accent(before) if isinstance(before, str) else None
        if changed is not None:
            row[self.pos - 1] = changed

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

    def _split_list_cell(self) -> None:
        """A comma in a list element ends it: what follows the cursor starts the next element."""
        index, slot = self.path[-1]
        template = self._parent()
        row = self.row()
        tail = row[self.pos :]
        del row[self.pos :]
        template.slots.insert(slot + 1, tail)
        template.cols += 1
        self.path[-1] = (index, slot + 1)
        self.pos = 0

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
        if self.cell_sel is not None:
            if replace:
                self._clear_cells()
            self.cell_sel = None
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
        self.cell_sel = None
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
        self.cell_sel = None
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

    # ---- selecting rows and columns of a matrix ----------------------------------------------

    def select_cells(self, axis: str, step: int = 0) -> None:
        """Shift+Up/Down (`axis` "row") or Alt+Shift+Left/Right ("col") in a matrix. The first
        press selects the row or column the cursor is in; each press after it moves the free end
        by `step`, so the selection grows (or shrinks back) a line at a time."""
        grid = self._grid()
        if grid is None:
            return
        self.anchor = None
        self.selected = False
        slot = self.path[-1][1]
        here = slot // grid.cols if axis == "row" else slot % grid.cols
        if self.cell_sel is None or self.cell_sel[0] != axis:
            self.cell_sel = (axis, here, here)
            return
        count = len(grid.slots) // grid.cols if axis == "row" else grid.cols
        _, anchor, free = self.cell_sel
        self.cell_sel = (axis, anchor, max(0, min(count - 1, free + step)))

    def selected_cells(self) -> list[int]:
        """Slot numbers of the selected rows or columns, in reading order (empty if none)."""
        grid = self._grid()
        if self.cell_sel is None or grid is None:
            return []
        axis, anchor, free = self.cell_sel
        low, high = min(anchor, free), max(anchor, free)
        return [
            i
            for i in range(len(grid.slots))
            if low <= (i // grid.cols if axis == "row" else i % grid.cols) <= high
        ]

    def _grid(self) -> Template | None:
        """The matrix whose cell the cursor is in, if it is in one."""
        if not self.path:
            return None
        parent = self._parent()
        return parent if parent.kind is Kind.MATRIX else None

    def _clear_cells(self) -> None:
        """Empty the selected cells and put the cursor in the first of them."""
        grid = self._grid()
        cells = self.selected_cells()
        if grid is None or not cells:
            return
        for i in cells:
            grid.slots[i] = []
        self.path[-1] = (self.path[-1][0], cells[0])
        self.pos = 0

    def _remove_cells(self) -> None:
        """Backspace or Delete on selected rows or columns takes them out of the matrix. If that
        would leave nothing, the cells are only emptied."""
        grid = self._grid()
        assert grid is not None
        assert self.cell_sel is not None
        by_row = self.cell_sel[0] == "row"
        cells = self.selected_cells()
        rows = len(grid.slots) // grid.cols
        lines = sorted({i // grid.cols if by_row else i % grid.cols for i in cells})
        self.cell_sel = None
        if len(lines) >= (rows if by_row else grid.cols):
            for i in cells:
                grid.slots[i] = []
            self.path[-1] = (self.path[-1][0], cells[0])
            self.pos = 0
            return
        here_row, here_col = divmod(self.path[-1][1], grid.cols)
        gone = set(cells)
        grid.slots = [slot for i, slot in enumerate(grid.slots) if i not in gone]
        if by_row:
            here_row = min(lines[0], len(grid.slots) // grid.cols - 1)
        else:
            grid.cols -= len(lines)
            here_col = min(lines[0], grid.cols - 1)
        self.path[-1] = (self.path[-1][0], here_row * grid.cols + here_col)
        self.pos = 0

    # ---- clipboard --------------------------------------------------------------------------

    def selection(self) -> Row:
        """A copy of the selected nodes (templates intact), or the highlighted template."""
        part = self._cells_as_matrix()
        if part is not None:
            return [part]
        if self.anchor is not None:
            low, high = self.span
            return copy.deepcopy(self.row()[low:high])
        if self.selected:
            return copy.deepcopy([self.row()[self.pos - 1]])
        return []

    def _cells_as_matrix(self) -> Template | None:
        """The selected rows or columns as a matrix of their own (a copy)."""
        grid = self._grid()
        if self.cell_sel is None or grid is None:
            return None
        cells = self.selected_cells()
        rows = len(grid.slots) // grid.cols
        width = grid.cols if self.cell_sel[0] == "row" else len(cells) // rows
        return copy.deepcopy(Template(Kind.MATRIX, [grid.slots[i] for i in cells], width))

    def cut(self) -> Row:
        nodes = self.selection()
        self._unselect(replace=True)
        return nodes

    def paste(self, nodes: Row) -> None:
        """Insert copies of `nodes` at the cursor, replacing any selection. A matrix of the shape
        of the selected rows or columns fills those cells instead of nesting."""
        grid = self._grid()
        shape = self._cells_as_matrix()
        if grid is not None and shape is not None and len(nodes) == 1:
            part = nodes[0]
            if (
                isinstance(part, Template)
                and part.kind is Kind.MATRIX
                and (part.cols, len(part.slots)) == (shape.cols, len(shape.slots))
            ):
                cells = self.selected_cells()
                for i, slot in zip(cells, copy.deepcopy(part.slots), strict=True):
                    grid.slots[i] = slot
                self.cell_sel = None
                self.path[-1] = (self.path[-1][0], cells[0])
                self.pos = 0
                return
        self._unselect(replace=True)
        row = self.row()
        row[self.pos : self.pos] = copy.deepcopy(nodes)
        self.pos += len(nodes)

    def select_all(self) -> None:
        """Ctrl+A: the whole entry line."""
        self.selected = False
        self.cell_sel = None
        self.path = []
        self.anchor = 0 if self.root else None
        self.pos = len(self.root)

    # ---- deleting ---------------------------------------------------------------------------

    def backspace(self) -> None:
        """Just after a template the first press highlights it and the second deletes it (0017)."""
        row = self.row()
        if self.cell_sel is not None and self._grid() is not None:
            self._remove_cells()
        elif self.anchor is not None or self.selected:
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
        """Forward delete. In front of a template the first press highlights it; a second leaves
        only what was in its first slot, selected (emulator run S8 a: `3/4` becomes `3`)."""
        if self.cell_sel is not None and self._grid() is not None:
            self._remove_cells()
            return
        row = self.row()
        if self.selected and self.anchor is None:
            index = self.pos - 1
            kept = _template(row[index]).slots[0]
            row[index : index + 1] = kept
            self.selected = False
            self.anchor = index if kept else None
            self.pos = index + len(kept)
            return
        if self.anchor is not None:
            self._unselect(replace=True)
            return
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
        if template.kind is Kind.LIST and self.path[-1][1] > 0:  # undo the comma
            index, slot = self.path[-1]
            previous = template.slots[slot - 1]
            joint = len(previous)
            previous.extend(template.slots.pop(slot))
            template.cols -= 1
            self.path[-1] = (index, slot - 1)
            self.pos = joint
            return
        if template.kind in GRIDS and self.path[-1][1] > 0:  # cells do not merge: step back
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
        if self.anchor is not None or self.cell_sel is not None:  # collapses to its left edge
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
            index, slot = self.path[-1]
            if slot and self._parent().kind in WALKED:
                self.path[-1] = (index, slot - 1)
                self.pos = len(self.row())
                return
            self.path.pop()  # Left from the start of any other slot leaves on the left
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
        """Right leaves the slot it is in, even the numerator of a fraction (0017). In an
        integral, sum, product, limit or derivative it walks the slots in Tab order instead
        (`WALKED`), then leaves."""
        if self.cell_sel is not None:
            self.cell_sel = None
            return
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
            index, slot = self.path[-1]
            parent = self._parent()
            if parent.kind in WALKED and slot + 1 < len(parent.slots):
                self.path[-1] = (index, slot + 1)
                self.pos = 0
                return
            self.path.pop()
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
        elif parent.kind in GRIDS and 0 <= slot + step * parent.cols < len(parent.slots):
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

    # ---- placing the cursor by target (a click) ---------------------------------------------

    def select_token(self, path: Sequence[tuple[int, int]], pos: int) -> None:
        """A double-click: select the token at `pos` (the node after it, else the one before) in
        the row at `path`: a run of letters and digits, a run of operator signs (`:=`), or one
        template or other sign (run 5, H3 b)."""
        self.place(path, pos)
        row = self.row()
        if not row:
            return
        at = min(self.pos, len(row) - 1)
        if self.pos == len(row) or (
            at > 0 and _token_class(row[at]) == "space" and _token_class(row[at - 1]) != "space"
        ):
            at = max(self.pos - 1, 0)
        kind = _token_class(row[at])
        low = high = at
        if kind in ("word", "sign"):
            while low > 0 and _token_class(row[low - 1]) == kind:
                low -= 1
            while high + 1 < len(row) and _token_class(row[high + 1]) == kind:
                high += 1
        self.anchor, self.pos = low, high + 1

    def move_selection(self, path: Sequence[tuple[int, int]], pos: int) -> None:
        """Drag and drop: the selected nodes move to `pos` in the row at `path` and stay
        selected (run 5, H3 k). A drop inside the selection, or in another row, changes nothing."""
        if self.anchor is None or list(path) != self.path:
            return
        low, high = self.span
        if low <= pos <= high:
            return
        row = self.row()
        moved = row[low:high]
        del row[low:high]
        at = pos - len(moved) if pos > high else pos
        row[at:at] = moved
        self.anchor, self.pos = at, at + len(moved)

    def place(self, path: Sequence[tuple[int, int]], pos: int, *, extend: bool = False) -> None:
        """Put the cursor at `pos` in the row reached by `path`, as a click does.

        A path that leaves the tree is cut where it stops being valid and `pos` is clamped to the
        row, so a stale click never raises. With `extend` (shift+click) the selection grows from
        where the cursor or selection started; when the two ends are in different rows it takes
        the whole templates that hold them, in their nearest common row.
        """
        target_path = self._valid_path(path)
        target_pos = max(0, min(pos, len(self._row_at(target_path))))
        self.cell_sel = None
        if not extend:
            self.selected = False
            self.anchor = None
            self.path = target_path
            self.pos = target_pos
            return
        self.selected = False
        start_path = list(self.path)
        start_pos = self.pos if self.anchor is None else self.anchor
        shared = 0
        while (
            shared < min(len(start_path), len(target_path))
            and start_path[shared] == target_path[shared]
        ):
            shared += 1
        if shared == len(start_path) == len(target_path):
            self.path = target_path
            self.pos = target_pos
            self.anchor = start_pos if start_pos != target_pos else None
            return
        # Different rows: work in the nearest common row, a template counting as one unit.
        first = _unit(start_path, start_pos, shared)
        second = _unit(target_path, target_pos, shared)
        low, high = min(first[0], second[0]), max(first[1], second[1])
        self.path = start_path[:shared]
        forward = second[0] >= first[0]
        self.anchor, self.pos = (low, high) if forward else (high, low)
        if low == high:
            self.anchor = None

    def _valid_path(self, path: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
        row = self.root
        valid: list[tuple[int, int]] = []
        for index, slot in path:
            if not 0 <= index < len(row) or not isinstance(row[index], Template):
                break
            template = _template(row[index])
            if not 0 <= slot < len(template.slots):
                break
            valid.append((index, slot))
            row = template.slots[slot]
        return valid

    def _row_at(self, path: Sequence[tuple[int, int]]) -> Row:
        row = self.root
        for index, slot in path:
            row = _template(row[index]).slots[slot]
        return row

    # ---- output -----------------------------------------------------------------------------

    def linear(self) -> str:
        """The TI text for the parser."""
        return _linear(self.root)

    def missing_closers(self) -> str:
        """The brackets Enter would add at the end of the line."""
        return missing_closers(self.root)

    def complete_brackets(self) -> None:
        """Close the brackets left open at the end of the line (what Enter does)."""
        self.root.extend(self.missing_closers())

    def latex(
        self, *, cursor: bool = True, is_defined: Callable[[str], bool] = lambda _: False
    ) -> str:
        """LaTeX for the entry, with the cursor drawn as a bar and empty slots as boxes. Catalog
        names are upright and names `is_defined` accepts are bold (`name_styles`)."""
        place = (self.path, self.pos, self.span) if cursor else None
        return _latex(self.root, place, [], is_defined)


def row_latex(row: Row, is_defined: Callable[[str], bool] = lambda _: False) -> str:
    """LaTeX for a row with no cursor; an empty slot is `EMPTY_SLOT`."""
    return _latex(row, None, [], is_defined)


_CLOSERS = {"(": ")", "[": "]", "{": "}"}


def missing_closers(row: Row) -> str:
    """The closing brackets the line lacks at its end, innermost first (`sin(2*(3+4` needs `))`).
    Brackets inside a text string do not count."""
    wanted: list[str] = []
    in_text = False
    for node in row:
        if not isinstance(node, str):
            continue
        if node == '"':
            in_text = not in_text
        elif in_text:
            continue
        elif node in _CLOSERS:
            wanted.append(_CLOSERS[node])
        elif wanted and node == wanted[-1]:
            wanted.pop()
    return "".join(reversed(wanted))


def _is_name_char(node: Node | str) -> bool:
    return isinstance(node, str) and (node.isalnum() or node in "_.@")


def _closing(row: Row, start: int) -> int | None:
    """The index of the `)` that closes the `(` at `start`, among the characters of `row`."""
    depth = 0
    for index in range(start, len(row)):
        if row[index] == "(":
            depth += 1
        elif row[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def modernised(row: Row) -> Row:
    """The line as a student would write it on paper: `pi` is π, `infinity` is ∞, `sqrt(x)` is a
    root template, `exp(x)` is ⅇ with a power, and a Catalog name typed in the wrong case is
    spelled as the Catalog spells it (`SOLVE` is `solve`, `define` is `Define`). Used on a line
    once it has been entered; the typing is untouched until then, as on the device."""
    out: Row = []
    index = 0
    while index < len(row):
        node = row[index]
        if isinstance(node, Template):
            out.append(Template(node.kind, [modernised(slot) for slot in node.slots], node.cols))
            index += 1
            continue
        if not (node.isascii() and node.isalpha()) or (out and _is_name_char(out[-1])):
            out.append(node)
            index += 1
            continue
        end = index
        while end < len(row) and _is_name_char(row[end]) and row[end] != ".":
            end += 1
        word = "".join(str(n) for n in row[index:end]).casefold()
        close = _closing(row, end) if end < len(row) and row[end] == "(" else None
        if word in ("pi", "infinity"):
            out.append("π" if word == "pi" else "∞")
        elif word == "sqrt" and close is not None:
            out.append(Template(Kind.ROOT, [modernised(row[end + 1 : close])]))
            end = close + 1
        elif word == "exp" and close is not None:
            out.extend(["ⅇ", Template(Kind.POWER, [modernised(row[end + 1 : close])])])
            end = close + 1
        elif (name := catalog_spelling(word)) is not None:
            out.extend(name)
        else:
            out.extend(row[index:end])
        index = end
    return out


def catalog_spelling(word: str) -> str | None:
    """How the Catalog spells `word` (any case), or None for a name it does not own."""
    if word in _WORDS:
        return word
    if word == "define":
        return "Define"
    return COMMANDS.get(word) or spelling(word)


def substitute_ans(row: Row, value: str) -> Row:
    """The line with each `ans` replaced by `value`, as the Teacher Software shows an entry in the
    history (emulator check 3, H1 g and H6 a). A value that is not a plain number is bracketed."""
    plain = re.fullmatch(r"[\d.]+(ᴇ-?\d+)?|[A-Za-zπⅇⅈ_][\w]*", value) is not None
    inserted: Row = list(value if plain else f"({value})")
    out: Row = []
    index = 0
    while index < len(row):
        node = row[index]
        if isinstance(node, Template):
            out.append(
                Template(node.kind, [substitute_ans(slot, value) for slot in node.slots], node.cols)
            )
            index += 1
            continue
        word = "".join(str(n) for n in row[index : index + 3]).casefold()
        before = bool(out) and _is_name_char(out[-1])
        after = index + 3 < len(row) and _is_name_char(row[index + 3])
        if word == "ans" and not before and not after:
            out.extend(inserted)
            index += 3
        else:
            out.append(node)
            index += 1
    return out


_SIGNS = frozenset(":=<>≤≥≠+-*/^|→!")


def _token_class(node: Node) -> str:
    """What a double-click groups a node with: `word` (names and numbers), `sign` (operators),
    `space`, or `one` (a template or bracket, on its own)."""
    if isinstance(node, Template):
        return "one"
    if node.isalnum() or node in "._πⅇⅈ":
        return "word"
    if node in _SIGNS:
        return "sign"
    return "space" if node.isspace() else "one"


def position_near(row: Row, em: float) -> int:
    """The gap in `row` nearest a click `em` ems from the left of its drawing. The history is
    drawn on the Flutter canvas, which gives Python no layout, so the widths are estimates
    (`estimated_width`): the cursor lands near the click, at the top level of the row."""
    left = 0.0
    for index, node in enumerate(row):
        width = _node_width(node)
        if em < left + width / 2:
            return index
        left += width
    return len(row)


def estimated_width(row: Row) -> float:
    """A row's width in ems as KaTeX sets it inline (`$...$`): fraction parts and exponents are
    at 70 per cent, binary operators and relations carry their spacing."""
    return sum(_node_width(node) for node in row)


_WIDE = {**dict.fromkeys("+-−", 1.22), **dict.fromkeys("=<>≤≥≠", 1.33), "*": 0.72, " ": 0.25}
_NARROW = {**dict.fromkeys(".,:;'!|", 0.28), **dict.fromkeys("()[]{}", 0.39)}
_SCRIPT = 0.7  # a fraction's parts and an exponent, set at script size


def _node_width(node: Node) -> float:
    if isinstance(node, str):
        return _WIDE.get(node) or _NARROW.get(node) or (0.72 if node.isupper() else 0.5)
    slots = [estimated_width(slot) or 0.6 for slot in node.slots]  # an empty slot is a box
    if node.kind is Kind.FRACTION:
        return _SCRIPT * max(slots) + 0.24
    if node.kind is Kind.POWER:
        return _SCRIPT * slots[0]
    if node.kind is Kind.ROOT:
        return 0.83 + slots[0]
    if node.kind is Kind.MATRIX and node.cols:
        columns = [max(slots[c :: node.cols]) for c in range(node.cols)]
        return sum(columns) + node.cols + 0.5
    return sum(slots) + 1.0


def linear_text(nodes: Row) -> str:
    """The TI text of some nodes, as for the system clipboard."""
    return _linear(nodes)


def format_target(path: Sequence[tuple[int, int]], pos: int) -> str:
    """A cursor target as GUI event text, `INDEX.SLOT/INDEX.SLOT:POS` (the path may be empty)."""
    return "/".join(f"{i}.{s}" for i, s in path) + f":{pos}"


def parse_target(text: str) -> tuple[list[tuple[int, int]], int]:
    """The inverse of `format_target`; a malformed text raises `ValueError`."""
    steps, _, pos = text.rpartition(":")
    path: list[tuple[int, int]] = []
    for step in filter(None, steps.split("/")):
        index, _, slot = step.partition(".")
        path.append((int(index), int(slot)))
    return path, int(pos)


def _unit(path: list[tuple[int, int]], pos: int, shared: int) -> tuple[int, int]:
    """The nodes of the common row that a cursor stands for: the template holding it, or the gap."""
    if len(path) > shared:
        return (path[shared][0], path[shared][0] + 1)
    return (pos, pos)


def _operand(text: str, start: int, *, root: bool) -> tuple[str, int]:
    """The operand of a `^` or `√` at `start`, and the index after it. A bracketed group loses its
    brackets; otherwise a sign and a run of term characters (a root without brackets takes the
    same run)."""
    if start < len(text) and text[start] == "(":
        depth = 0
        for end in range(start, len(text)):
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            if depth == 0:
                return text[start + 1 : end], end + 1
        return text[start + 1 :], len(text)  # unbalanced: the rest
    end = start + (not root and start < len(text) and text[start] == "-")
    while end < len(text) and text[end] in _TERM_CHARS:
        end += 1
    return text[start:end], end


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


# After one of these a function-like template needs an explicit `*`: `x` then |□| would
# otherwise read as `xabs(`, and `2` then a system as `2{`.
_JOINS = _TERM_CHARS | {")", "]", "}"}


def _linear(row: Row) -> str:
    out: list[str] = []
    for node in row:
        if isinstance(node, str):
            out.append(node)
            continue
        spec = SPECS[node.kind]
        text = spec.linear([_linear(slot) for slot in node.slots], node.cols)
        out.append(("*" if spec.joins and out and out[-1][-1:] in _JOINS else "") + text)
    return "".join(out)


# Digit height with a little depth: a taller bar pushes a denominator down.
_CURSOR = r"{\color{#4da3ff}\rule[-0.15em]{0.06em}{0.8em}}"
_CURSOR_IN_SELECTION = r"{\color{#0b3d78}\rule[-0.15em]{0.06em}{0.8em}}"  # darker on the highlight
_EMPTY_SLOT = r"\square"
EMPTY_SLOT = _EMPTY_SLOT  # public: how `row_latex` draws an empty slot
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
    "ⅇ": r"\mathbf{e}",  # bold upright, so the constants stand out from the variables e and i
    "ⅈ": r"\boldsymbol{i}",  # bold italic, as the device draws it
    " ": r"\ ",  # TeX drops a plain space, which would run `and` into its equations
    "%": r"\%",
    '"': r'\mathtt{"}',  # straight, as the device draws it: KaTeX_Main's quote is curly
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


class Style(StrEnum):
    """How a name's letters are drawn. A name with neither style stays italic, as a variable."""

    ROMAN = "roman"  # upright: a Catalog name (function, command, `Define`) or a word operator
    BOLD = "bold"  # a name the Problem defines: a variable, an expression, a function...
    BOLD_ITALIC = "bold italic"  # the imaginary unit ⅈ


# Names that are never a plain variable: `ans`, the words that join conditions, and the values
# `true`, `false` and `undef` (upright on the device, emulator calc2 results)
_WORDS = frozenset({"ans", "and", "or", "xor", "not", "true", "false", "undef"})
# The calculator's own result variables (`tvm.pmt`, `stat.sx`) are one name each, bold once set.
_SYSTEM_PREFIXES = ("tvm.", "stat.")


def is_catalog_name(name: str) -> bool:
    """Whether `name` is in the Catalog: a function, a command such as `DelVar`, or `Define`."""
    word = name.casefold()
    return word in _WORDS or word in COMMANDS or word == "define" or is_builtin(word)


def name_styles(row: Row, is_defined: Callable[[str], bool]) -> dict[int, Style]:
    """The style of each letter that belongs to a name which is not a plain variable: Catalog
    names (`Define`, `solve`, `sin`, `ans`, `and`) upright, and names the Problem defines (any
    value or function, and `tvm.pmt` style system variables once something has set them) bold.
    Any other name is italic. The device draws bold only on the entry line: a history row is
    drawn with `is_defined` false for every name (emulator check 4, A4). Letters inside a string
    (between quotes) are text, so they are upright too."""
    styles: dict[int, Style] = {}
    run: list[int] = []
    in_text = False
    for index, node in enumerate([*row, ""]):
        if node == '"':
            in_text = not in_text
        elif in_text:
            if isinstance(node, str) and node.isalpha():
                styles[index] = Style.ROMAN
            continue
        if isinstance(node, str) and node.isascii() and (node.isalpha() or node == "_"):
            run.append(index)
            continue
        if run and isinstance(node, str) and node == "." and _dotted(row, run, index):
            run.append(index)  # `tvm.` goes on into `tvm.pmt`
            continue
        if run:
            name = "".join(str(row[i]) for i in run)
            style = (
                Style.BOLD if is_defined(name) else Style.ROMAN if is_catalog_name(name) else None
            )
            if style is not None:
                styles.update(dict.fromkeys(run, style))
        run = []
    return styles


def _dotted(row: Row, run: list[int], index: int) -> bool:
    """Whether the `.` at `index` continues the name in `run` as a system name (`tvm.`)."""
    word = "".join(str(row[i]) for i in run).casefold()
    return f"{word}.".startswith(_SYSTEM_PREFIXES) and word in ("tvm", "stat")


def at_constants(row: Row) -> dict[int, str]:
    """TI's `@` names: the index of the `@` (shown as nothing) and of each character after it, as
    shown. `@e` and `@i` are the constants the palette's ⅇ and ⅈ give; `@n1` and `@c1` are the
    arbitrary integers and constants `solve` names (shown `n1`, `c1`; emulator calc4 results)."""
    shown: dict[int, str] = {}
    for index in range(len(row) - 1):
        if row[index] != "@" or not isinstance(letter := row[index + 1], str):
            continue
        end = index + 2
        if letter in ("n", "c"):
            while end < len(row) and isinstance(row[end], str) and str(row[end]).isdigit():
                end += 1
            if end == index + 2:
                continue  # `@n` alone is not one of them
        elif letter not in ("e", "i"):
            continue
        after = row[end] if end < len(row) else ""
        if not (isinstance(after, str) and after.isalnum()):
            shown[index] = ""
            shown.update({i: str(row[i]) for i in range(index + 1, end)})
    return shown


_FONTS = {Style.ROMAN: "mathrm", Style.BOLD: "mathbf", Style.BOLD_ITALIC: "boldsymbol"}


def constant_style(letter: str) -> Style:
    """ⅇ is drawn bold upright, ⅈ and the `solve` constants (`n1`) bold italic (emulator check 4,
    A13; calc4 results)."""
    return Style.BOLD if letter == "e" else Style.BOLD_ITALIC


type Place = tuple[list[tuple[int, int]], int, tuple[int, int]]


def _stretch_brackets(row: Row, pieces: list[str], span: tuple[int, int]) -> None:
    """Round brackets around something taller than a line (a fraction, a root, a matrix) grow
    with it, as `\\left( \\right)`. A pair split by the selection's edge stays plain, since the
    highlight box cannot hold one half of a `\\left \\right` pair."""
    low, high = span
    opened: list[int] = []
    in_text = False
    for index, node in enumerate(row):
        if node == '"':
            in_text = not in_text
        elif in_text:
            continue
        elif node == "(":
            opened.append(index)
        elif node == ")" and opened:
            start = opened.pop()
            tall = any(
                isinstance(n, Template) and n.kind is not Kind.POWER for n in row[start + 1 : index]
            )
            whole = (low <= start and index < high) or index < low or start >= high
            if tall and whole:
                pieces[start], pieces[index] = r"\left(", r"\right)"


def _latex(
    row: Row, place: Place | None, here: list[tuple[int, int]], is_defined: Callable[[str], bool]
) -> str:
    """The row as LaTeX. `place` is the cursor's path, its position and the selected span."""
    here_cursor = place is not None and place[0] == here
    at = place[1] if place is not None else -1
    low, high = place[2] if here_cursor and place is not None else (0, 0)
    styles = name_styles(row, is_defined)
    constants = at_constants(row)
    if not row:
        return _CURSOR if here_cursor else _EMPTY_SLOT
    pieces: list[str] = []
    for i, node in enumerate(row):
        if i in constants:
            letter = constants[i]
            pieces.append(rf"\{_FONTS[constant_style(letter)]}{{{letter}}}" if letter else "")
            continue
        if isinstance(node, str):
            style = styles.get(i)
            pieces.append(rf"\{_FONTS[style]}{{{node}}}" if style else _SYMBOLS.get(node, node))
            continue
        slots = [
            _latex(slot, place, [*here, (i, s)], is_defined) for s, slot in enumerate(node.slots)
        ]
        pieces.append(SPECS[node.kind].latex(slots, node.cols))
    _stretch_brackets(row, pieces, (low, high))
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
