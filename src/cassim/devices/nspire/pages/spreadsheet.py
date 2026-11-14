"""The Lists & Spreadsheet page (slice 3b, FR-SHEET-001 to 002): what is shown and what keys do.

The cells live in the Problem's engine (`cassim.sheet`, through `cassim.device.sheet_link`). This
model keeps what the page needs without the engine:

- the sheet's definitions (cells as typed, column names and formulas), updated from each reply's
  edits, so the document saves without asking the engine (decision 0031);
- the cells on show, as the engine formatted them (a `view`), drawn at once on a page switch;
- the cursor, block selection, scroll position, column widths and a half-typed cell, which a page
  keeps while another is shown (check run 2, G39, G48);
- dialogs as data: notices to dismiss, Data Loss to confirm, and wizards (Go To, Sort, Generate
  Sequence, Conflict Detected) for the app to open.

Behaviour follows emulator check 6 part E (`docs/testing/emulator-sheet3-results.md`, the finish
rows in `emulator-finish-results.md`). Every function reached on the emulator by a key chord or a
right-click is also a Menu item or a context-menu item, so touch can reach it (decision 0031 item
7). Nothing here loads SymPy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from cassim.device.editor import MARK
from cassim.device.engine import RemoteSession
from cassim.device.keys import Binding
from cassim.device.sheet_link import SheetLink, link_for
from cassim.device.wizard import Field, Wizard
from cassim.sheet import refs
from cassim.sheet.refs import COLUMNS, ROWS

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from cassim.core.session import Session
    from cassim.device.clipboard import Clipboard
    from cassim.device.engine import (
        ColumnPayload,
        SheetAction,
        SheetErrorPayload,
        SheetOp,
        SheetReply,
    )

type Key = tuple[int, int]  # (column, row): row -1 is the name row, 0 the formula row

NAME_ROW = -1
FORMULA_ROW = 0
DEFAULT_WIDTH = 64  # a column's width in the handheld's pixels; four fit beside the row numbers
NARROW = 32  # Minimize Column Width
WIDE = 280  # Maximize Column Width: about the screen's width (check 6, E13)
WIDTH_STEP = 12  # Resize Column Width: one arrow press (check 6, E13: about 12 px a press)
MIN_WIDTH, MAX_WIDTH = 20, WIDE
UNDO_DEPTH = 50

GO_TO_INVALID = "Invalid reference. Please try again."
CANNOT_PASTE = (
    "Cannot Paste",
    "The contents cannot be pasted because the copy and paste areas have incompatible sizes.",
)
DATA_LOSS = "Data Loss"
DATA_LOSS_MESSAGE = (
    "This operation may overwrite data in the current column(s). Do you wish to proceed?"
)
# Actions only a sheet page has; another page ignores them.
SHEET_ACTIONS = frozenset(
    {
        "goto",
        "recalculate",
        "page_up",
        "page_down",
        "context_menu",
        "sheet",
        "sheet_op",
        "sheet_goto",
        "sheet_choose",
        "sheet_tap",
        "sheet_drag",
        "sheet_ok",
        "sheet_cancel",
    }
)


@dataclass(frozen=True)
class CellView:
    text: str  # as drawn
    right: bool  # a number sits on the right, text on the left
    entry: str  # the entry line's text for the cell


@dataclass(frozen=True)
class Dialog:
    """A dialog over the page. `then` runs on OK; with `cancel` there is also Cancel."""

    title: str
    message: str
    cancel: bool = False
    then: Binding | None = None


@dataclass(frozen=True)
class Copied:
    """Cells copied from a sheet: (column offset, row offset, kind, text) from `origin`. A name
    cell cannot be pasted into cells (check 6, E11)."""

    origin: Key
    width: int
    height: int
    cells: tuple[tuple[int, int, str, str], ...]
    rows: bool = False  # whole rows: a paste over data asks first (Data Loss)
    name: bool = False


@dataclass(frozen=True)
class Snapshot:
    cells: dict[Key, tuple[str, str]]
    columns: tuple[ColumnPayload, ...]


@dataclass(frozen=True)
class SheetScreen:
    """The page as data for the view: the visible columns and rows, what each cell shows, where
    the cursor and selection are, what is being typed, and the bar under the grid."""

    # The window's columns and rows, and one more of each, part hidden at the right and the
    # bottom, as a hint that the sheet goes on.
    columns: tuple[tuple[int, str, str, str, int], ...]  # index, letter, name, formula, width
    rows: tuple[int, ...]  # the data rows on show
    cells: dict[Key, tuple[str, bool]]  # (text, right) of the cells on show
    cursor: Key
    selection: tuple[int, int, int, int] | None  # left, top, right, bottom (a block or more)
    editing: str | None  # the text being typed in the cursor's cell, with the caret marked
    mode: str | None  # "fill", "move" or "resize" while one of those is going on
    marker: tuple[int, int, int, int] | None  # the Fill range, or the Move Column bar
    address: str  # "A1", "A1:C4", "A" or "1": the bar's left side
    entry: str  # the bar's text: what the cursor's cell holds
    dialog: Dialog | None
    sliver: int | None = None  # the column off to the left, a sliver of it shown (check 6, E13)


def letter(column: int) -> str:
    return refs.column_letter(column)


def _definition_text(kind: str, text: str) -> str:
    return f"={text}" if kind == "formula" and text else text


class Spreadsheet:
    def __init__(self, session: Session | RemoteSession, clipboard: Clipboard) -> None:
        self.session = session
        self.clipboard = clipboard
        self.link: SheetLink = link_for(session)
        self.id = self.link.new_id()
        # The definitions, as the engine last reported them.
        self.cells: dict[Key, tuple[str, str]] = {}
        self.columns: list[ColumnPayload] = [(None, None, None)] * COLUMNS
        self.widths: dict[int, int] = {}
        # The cells on show, from the engine's last view.
        self.view: dict[Key, CellView] = {}
        self.revision = -1  # the sheet's revision in the last reply
        self._viewed: tuple[int, tuple[int, int, int, int]] | None = None
        self._asked: tuple[int, tuple[int, int, int, int]] | None = None
        self.waiting: dict[Key, str] = {}  # typed and sent, not answered yet
        # Where we are.
        self.cursor: Key = (0, 1)
        self.anchor: Key | None = None  # the other corner of a block selection
        self.whole: Literal["row", "column"] | None = None
        self.top, self.left = 1, 0  # the first data row and column on show
        self.rows_shown, self.columns_shown = 5, 4  # set by the view from its size
        self.editing: str | None = None
        self.caret = 0
        self.mode: Literal["fill", "move", "resize"] | None = None
        self._fill_from: tuple[int, int, int, int] | None = None
        self._move_to = 0
        # Dialogs and the last action, which a Data Loss OK or a Conflict choice sends again.
        self.dialogs: list[Dialog] = []
        self.wizard: Wizard | None = None  # a dialog for the app to open
        self.last: SheetOp | None = None
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []

    # ---- the engine ---------------------------------------------------------------------------

    def op(self, action: str, **args: object) -> SheetOp:
        return {"op": "sheet", "page": self.id, "action": cast("SheetAction", action), "args": args}

    def _send(self, action: str, *, undoable: bool = True, **args: object) -> None:
        """Send an action that changes the sheet; it can be undone."""
        if undoable:
            self._undo.append(self._snapshot())
            del self._undo[:-UNDO_DEPTH]
            self._redo.clear()
        op = self.op(action, **args)
        self.last = op
        self.link.send(op)
        self.update()

    def restore_op(self) -> SheetOp:
        """The op that rebuilds this sheet in an engine from its definitions."""
        return self._restore_of(self._snapshot())

    def _restore_of(self, snapshot: Snapshot) -> SheetOp:
        cells = [[c, r, kind, text] for (c, r), (kind, text) in sorted(snapshot.cells.items())]
        columns = [list(info) for info in snapshot.columns]
        return self.op("restore", cells=cells, columns=columns)

    def _snapshot(self) -> Snapshot:
        return Snapshot(dict(self.cells), tuple(self.columns))

    def loaded(self) -> None:
        """After a document's pages are loaded: rebuild the sheet in the engine. This runs after
        the Problem's other pages, so the sheet's saved values win over older Calculator entries."""
        self.link.alive(self.id)
        self.link.send(self.restore_op())
        self.update()

    def update(self) -> None:
        """Take the engine's replies, then ask for the cells on show if they are out of date."""
        for reply in self.link.take(self.id):
            self._accept(reply)
        if isinstance(self.session, RemoteSession) and self.session.journal:
            self.session.compact(self.id, self.restore_op())
        span = self._wanted_span()
        wanted = (self.revision, span)
        covered = self._viewed is not None and self._viewed[0] == self.revision
        if covered and self._viewed is not None and _inside(self._window(), self._viewed[1]):
            return
        if self._asked == wanted:
            return  # asked already; the reply is on its way
        self._asked = wanted
        self.link.send(self.op("view", span=list(span)))
        if not self.link.deferred:
            for reply in self.link.take(self.id):
                self._accept(reply)

    def _accept(self, reply: SheetReply) -> None:
        for column, row, kind, text in reply["edits"]:
            if kind:
                self.cells[(column, row)] = (kind, text)
            else:
                self.cells.pop((column, row), None)
        if reply["columns"]:
            self.columns = [(info[0], info[1], info[2]) for info in reply["columns"]]
        if reply["span"]:
            left, top, right, bottom = reply["span"]
            self.view = {
                key: cell
                for key, cell in self.view.items()
                if not (left <= key[0] <= right and top <= key[1] <= bottom)
            }
            for column, row, text, right_aligned, entry in reply["cells"]:
                self.view[(column, row)] = CellView(text, right_aligned, entry)
            self._viewed = (reply["revision"], (left, top, right, bottom))
            self._asked = None
        self.revision = reply["revision"]
        self.waiting.clear()
        for notice in reply["notices"]:
            self.dialogs.append(Dialog(notice["title"], notice["message"]))
        if reply["error"] is not None:
            self._failed(reply["error"])

    def _failed(self, error: SheetErrorPayload) -> None:
        """A refused action: Data Loss asks first, Conflict Detected asks Cell or Variable for
        each name, and anything else is a dialog; a refused entry goes back into edit mode with
        its text (check 6, E7, E20)."""
        last = self.last
        if error["title"] == DATA_LOSS and last is not None:
            again = json.dumps(
                {"action": last["action"], "args": {**last["args"], "confirm": True}}
            )
            self.dialogs.append(
                Dialog(
                    error["title"], error["message"], cancel=True, then=Binding("sheet_op", again)
                )
            )
            return
        if error["names"] and last is not None:
            self.wizard = _conflict_wizard(error, last)
            return
        self.dialogs.append(Dialog(error["title"], error["message"]))
        if last is not None and last["action"] in ("cell", "formula", "name"):
            args = last["args"]
            rows = {"cell": args.get("row"), "formula": FORMULA_ROW, "name": NAME_ROW}
            self.cursor = (cast("int", args["column"]), cast("int", rows[last["action"]]))
            self.editing = str(args["text"])
            self.caret = len(self.editing)
        if self._undo:  # a refused change changed nothing
            self._undo.pop()

    # ---- what is shown ------------------------------------------------------------------------

    def _window(self) -> tuple[int, int, int, int]:
        right = min(self.left + self.columns_shown - 1, COLUMNS - 1)
        bottom = min(self.top + self.rows_shown - 1, ROWS)
        return self.left, self.top, right, bottom

    def _wanted_span(self) -> tuple[int, int, int, int]:
        """The window and some more below and to the right, so a few moves need no new view."""
        left, top, right, bottom = self._window()
        return left, top, min(right + 2, COLUMNS - 1), min(bottom + self.rows_shown * 2, ROWS)

    def width(self, column: int) -> int:
        return self.widths.get(column, DEFAULT_WIDTH)

    def set_window(self, rows: int, columns: int) -> None:
        """The view's size in data rows and columns."""
        self.rows_shown, self.columns_shown = max(rows, 1), max(columns, 1)
        self._follow()

    def selection(self) -> tuple[int, int, int, int] | None:
        """The selected block as (left, top, right, bottom), or None for a single cell."""
        column, row = self.cursor
        if self.whole == "column":
            return column, 1, column, max(self.last_row(column), 1)
        if self.whole == "row":
            return 0, row, COLUMNS - 1, row
        if self.anchor is None or self.anchor == self.cursor:
            return None
        left, right = sorted((self.anchor[0], column))
        top, bottom = sorted((max(self.anchor[1], 1), max(row, 1)))
        return left, top, right, bottom

    def _span(self) -> tuple[int, int, int, int]:
        """The selection, or the cursor's cell."""
        column, row = self.cursor
        return self.selection() or (column, max(row, 1), column, max(row, 1))

    def last_row(self, column: int) -> int:
        """The column's last row with a definition (a formula column's values are not known
        here: its formula stands for the whole column)."""
        return max((r for c, r in self.cells if c == column), default=0)

    def entry_text(self, key: Key) -> str:
        """What the entry line shows for a cell."""
        column, row = key
        if row == NAME_ROW:
            return self.columns[column][1] or ""
        if row == FORMULA_ROW:
            formula = self.columns[column][2]
            return f"={formula}" if formula else ""
        if key in self.cells:
            return _definition_text(*self.cells[key])
        cell = self.view.get(key)
        return cell.entry if cell is not None else ""

    def screen(self) -> SheetScreen:
        left, top, right, bottom = self._window()
        right, bottom = min(right + 1, COLUMNS - 1), min(bottom + 1, ROWS)  # the part-hidden ones
        columns = tuple(
            (
                c,
                letter(c).upper(),
                self.columns[c][1] or "",
                self.columns[c][2] or "",
                self.width(c),
            )
            for c in range(left, right + 1)
        )
        rows = tuple(range(top, bottom + 1))
        cells = {
            key: (cell.text, cell.right)
            for key, cell in self.view.items()
            if left <= key[0] <= right and top <= key[1] <= bottom
        }
        for key, text in self.waiting.items():
            cells[key] = (text, False)
        editing = None
        if self.editing is not None:
            editing = self.editing[: self.caret] + MARK + self.editing[self.caret :]
        return SheetScreen(
            columns,
            rows,
            cells,
            self.cursor,
            self.selection(),
            editing,
            self.mode,
            self._marker(),
            self.address(),
            self.editing if self.editing is not None else self.entry_text(self.cursor),
            self.dialogs[0] if self.dialogs else None,
            left - 1 if left > 0 else None,
        )

    def _marker(self) -> tuple[int, int, int, int] | None:
        if self.mode == "fill" and self._fill_from is not None:
            left, top, right, bottom = self._fill_from
            column, row = self.cursor
            return min(left, column), min(top, row), max(right, column), max(bottom, row, 1)
        if self.mode == "move":
            return self._move_to, 1, self._move_to, 1
        return None

    def address(self) -> str:
        """The bar's cell name: `A1`, a block `A1:C4`, a column `A` or a row `1`."""
        column, row = self.cursor
        if self.whole == "column" or row == NAME_ROW:
            return letter(column).upper()
        if self.whole == "row":
            return str(row)
        block = self.selection()
        if block is not None:
            a, b, c, d = block
            return f"{letter(a).upper()}{b}:{letter(c).upper()}{d}"
        if row == FORMULA_ROW:
            return f"{letter(column).upper()}="
        return f"{letter(column).upper()}{row}"

    def context_menu(self) -> str:
        """The context menu for where the cursor is (check 6, E2, E12; run 2, E2)."""
        if self.whole == "column" or self.cursor[1] == NAME_ROW:
            return "sheet_column"
        if self.whole == "row":
            return "sheet_row"
        if self.selection() is not None:
            return "sheet_block"
        return "sheet_cell"

    def column_named(self, name: str) -> int | None:
        folded = name.casefold()
        for index, (_, shown, _) in enumerate(self.columns):
            if shown is not None and shown.casefold() == folded:
                return index
        return None

    # ---- keys ---------------------------------------------------------------------------------

    def perform(self, binding: Binding) -> None:
        """Do what a key or a menu item says."""
        action, arg = binding.action, binding.arg
        if self.dialogs:
            self._dialog_key(action)
        elif self.mode is not None:
            self._mode_key(action)
        elif self.editing is not None and action in self._edit_keys():
            self._edit_keys()[action](arg)
        else:
            handler = self._keys().get(action)
            if handler is not None:
                handler(arg)
        self.update()

    def _dialog_key(self, action: str) -> None:
        dialog = self.dialogs[0]
        if action in ("enter", "select", "sheet_ok"):
            self.dialogs.pop(0)
            if dialog.then is not None:
                self.perform(dialog.then)
        elif action in ("escape", "sheet_cancel") or not dialog.cancel:
            self.dialogs.pop(0)

    def _keys(self) -> dict[str, Callable[[str], None]]:
        return {
            "left": lambda _: self.move(-1, 0),
            "right": lambda _: self.move(1, 0),
            "up": lambda _: self.move(0, -1),
            "down": lambda _: self.move(0, 1),
            "select_left": lambda _: self.move(-1, 0, extend=True),
            "select_right": lambda _: self.move(1, 0, extend=True),
            "select_cells": self._select_cells,
            "page_up": lambda _: self.move(0, -(self.rows_shown - 1)),
            "page_down": lambda _: self.move(0, self.rows_shown - 1),
            "first_line": lambda _: self.go((self.cursor[0], 1)),
            "last_line": lambda _: self.go((self.cursor[0], max(self.last_row(self.cursor[0]), 1))),
            "home_key": lambda _: self.go((0, self.cursor[1])),
            "home": lambda _: self.go((0, self.cursor[1])),
            "end": lambda _: self.go((self._last_column(), self.cursor[1])),
            "tab": lambda _: self.go((self.cursor[0], FORMULA_ROW)),
            "shift_tab": lambda _: self._select_all(),
            "select_all": lambda _: self._select_all(),
            "enter": lambda _: self.begin_edit(self.entry_text(self.cursor)),
            "select": lambda _: self.begin_edit(self.entry_text(self.cursor)),
            "insert": self.type_text,
            "insert_linear": self.type_text,
            "template": lambda _: None,
            "power": lambda arg: self.type_text(f"^{arg}"),
            "backspace": lambda _: self.clear(),
            "delete": lambda _: self.clear(),
            "clear": lambda _: self.clear(),
            "escape": lambda _: self._deselect(),
            "copy": lambda _: self.copy(),
            "cut": lambda _: self.cut(),
            "paste": self.paste,
            "undo": lambda _: self.undo(),
            "redo": lambda _: self.redo(),
            "goto": lambda _: self._go_to_dialog(),
            "recalculate": lambda _: self._send("recalculate", undoable=False),
            "sheet": self.menu_action,
            "sheet_op": self._resend,
            "sheet_goto": self.go_to,
            "sheet_choose": self._resend,
            "sheet_tap": self.tap,
            "sheet_drag": self.drag,
        }

    def _edit_keys(self) -> dict[str, Callable[[str], None]]:
        return {
            "insert": self._insert,
            "insert_linear": self._insert,
            "power": lambda arg: self._insert(f"^{arg}"),
            "left": lambda _: self._caret(self.caret - 1),
            "right": lambda _: self._caret(self.caret + 1),
            "home": lambda _: self._caret(0),
            "home_key": lambda _: self._caret(0),
            "end": lambda _: self._caret(len(self.editing or "")),
            "backspace": lambda _: self._erase(before=True),
            "delete": lambda _: self._erase(before=False),
            "clear": lambda _: self._set_text(""),
            "escape": lambda _: self.cancel_edit(),
            "enter": lambda _: self.commit(then=(0, 1)),
            "select": lambda _: self.commit(then=(0, 1)),
            "up": lambda _: self.commit(then=(0, -1)),
            "down": lambda _: self.commit(then=(0, 1)),
            "tab": lambda _: self.commit(then=(1, 0)),
            "paste": lambda text: self._insert(text) if text else None,
        }

    # ---- moving and selecting -----------------------------------------------------------------

    def move(self, columns: int, rows: int, *, extend: bool = False) -> None:
        column, row = self.cursor
        if extend:
            if self.anchor is None:
                self.anchor = self.cursor
        else:
            self.anchor = None
            self.whole = None
        lowest = 1 if extend else NAME_ROW
        self.cursor = (
            min(max(column + columns, 0), COLUMNS - 1),
            min(max(row + rows, lowest), ROWS),
        )
        self._follow()

    def go(self, key: Key) -> None:
        self.anchor = None
        self.whole = None
        self.cursor = (min(max(key[0], 0), COLUMNS - 1), min(max(key[1], NAME_ROW), ROWS))
        self._follow()

    def _follow(self) -> None:
        """Scroll as little as keeps the cursor on show (run 2, G39: Go To h40 shows rows 36 to
        40 with H at the right)."""
        column, row = self.cursor
        if row >= 1:
            if row < self.top:
                self.top = row
            elif row >= self.top + self.rows_shown:
                self.top = row - self.rows_shown + 1
        if column < self.left:
            self.left = column
        elif column >= self.left + self.columns_shown:
            self.left = column - self.columns_shown + 1

    def _select_cells(self, arg: str) -> None:
        """shift+arrows: `row:1`, `col:-1` and so on."""
        axis, _, step = arg.partition(":")
        amount = int(step or 1)
        self.move(amount if axis == "col" else 0, amount if axis == "row" else 0, extend=True)

    def _select_all(self) -> None:
        """The whole of what is filled in, as a block (run 2, E4: shift+Tab)."""
        filled = [key for key in self.cells if key[1] >= 1]
        right = max((c for c, _ in filled), default=0)
        bottom = max((r for _, r in filled), default=1)
        self.whole = None
        self.anchor = (0, 1)
        self.cursor = (right, bottom)

    def _deselect(self) -> None:
        self.anchor = None
        self.whole = None

    def _last_column(self) -> int:
        used = [c for c, _ in self.cells] + [c for c, info in enumerate(self.columns) if any(info)]
        return max(used, default=0)

    def tap(self, arg: str) -> None:
        """A tap or click on the grid: `column,row` (row -1 the name cell, 0 the formula cell).
        A tap on the cell being edited keeps editing; elsewhere it enters what was typed first.
        `column,row,extend` extends the selection (shift+click, a drag)."""
        parts = arg.split(",")
        key = (int(parts[0]), int(parts[1]))
        if self.editing is not None:
            if key == self.cursor:
                return
            self.commit(then=(0, 0))
        if len(parts) > 2 and key[1] >= 1:  # noqa: PLR2004
            if self.anchor is None:
                self.anchor = self.cursor
            self.whole = None
            self.cursor = key
            self._follow()
            return
        self.go(key)

    def drag(self, arg: str) -> None:
        """A drag across the grid scrolls it by `columns,rows` (touch: a one-finger drag)."""
        columns, rows = (int(part) for part in arg.split(","))
        self.top = min(max(self.top + rows, 1), ROWS - self.rows_shown + 1)
        self.left = min(max(self.left + columns, 0), COLUMNS - self.columns_shown)

    def select_whole(self, what: Literal["row", "column"]) -> None:
        self.anchor = None
        self.whole = what
        if what == "row":
            self.cursor = (self.cursor[0], max(self.cursor[1], 1))

    # ---- typing -------------------------------------------------------------------------------

    def begin_edit(self, text: str) -> None:
        self.editing = text
        self.caret = len(text)
        self.anchor = None
        self.whole = None

    def type_text(self, text: str) -> None:
        """A key that types starts editing the cell, replacing what it held (check 6, E5)."""
        self.begin_edit("")
        self._insert(text)

    def _insert(self, text: str) -> None:
        assert self.editing is not None
        place = text.find(MARK)
        plain = text.replace(MARK, "")
        self.editing = self.editing[: self.caret] + plain + self.editing[self.caret :]
        self.caret += place if place >= 0 else len(plain)

    def _set_text(self, text: str) -> None:
        self.editing, self.caret = text, len(text)

    def _caret(self, place: int) -> None:
        self.caret = min(max(place, 0), len(self.editing or ""))

    def _erase(self, *, before: bool) -> None:
        text = self.editing or ""
        if before and self.caret > 0:
            self.editing = text[: self.caret - 1] + text[self.caret :]
            self.caret -= 1
        elif not before and self.caret < len(text):
            self.editing = text[: self.caret] + text[self.caret + 1 :]

    def cancel_edit(self) -> None:
        self.editing = None

    def commit(self, then: tuple[int, int] = (0, 0)) -> None:
        """Enter what was typed, then move (Enter moves down: run 2, E4). An unchanged cell is
        not sent again."""
        text = (self.editing or "").strip()
        self.editing = None
        column, row = self.cursor
        if text != self.entry_text(self.cursor).strip():
            if row == NAME_ROW:
                self._send("name", column=column, text=text)
            elif row == FORMULA_ROW:
                formula = text if not text or text.startswith("=") else f"={text}"
                self._send("formula", column=column, text=formula, choose={})
            else:
                self.waiting[self.cursor] = text
                self._send("cell", column=column, row=row, text=text, choose={})
        if then != (0, 0) and not self.dialogs:
            self.move(*then)

    # ---- changing cells -----------------------------------------------------------------------

    def clear(self) -> None:
        """Del: empty the selected cells; on the name cell, unlink the column; on the formula
        cell, drop the column formula, keeping its values (run 2, E20)."""
        column, row = self.cursor
        if self.selection() is None and row == NAME_ROW:
            self._send("name", column=column, text="")
            return
        if self.selection() is None and row == FORMULA_ROW:
            self._send("formula", column=column, text="", choose={})
            return
        left, top, right, bottom = self._span()
        cleared = [
            [c, r, "entry", ""]
            for (c, r) in self.cells
            if left <= c <= right and top <= r <= bottom
        ]
        if cleared:
            self._send("put", cells=cleared)

    def copy(self) -> None:
        column, row = self.cursor
        if self.selection() is None and row == NAME_ROW:
            copied = Copied(self.cursor, 1, 1, (), name=True)
            self.clipboard.copy_cells(copied, self.columns[column][1] or "")
            return
        left, top, right, bottom = self._span()
        cells = tuple(
            (c - left, r - top, *self.cells[(c, r)])
            for (c, r) in sorted(self.cells)
            if left <= c <= right and top <= r <= bottom
        )
        text = "\n".join(
            "\t".join(self._shown_text((c, r)) for c in range(left, right + 1))
            for r in range(top, bottom + 1)
        )
        copied = Copied((left, top), right - left + 1, bottom - top + 1, cells, self.whole == "row")
        self.clipboard.copy_cells(copied, text)

    def _shown_text(self, key: Key) -> str:
        cell = self.view.get(key)
        if cell is not None:
            return cell.text
        kind, text = self.cells.get(key, ("entry", ""))
        return _definition_text(kind, text)

    def cut(self) -> None:
        self.copy()
        self.clear()

    def paste(self, text: str = "", *, confirm: bool = False) -> None:
        """Paste copied cells at the cursor, formulas moved with them (check 6, E11). Text from
        elsewhere goes in as typed entries, a tab between cells and a line between rows."""
        copied = self.clipboard.cells
        if text and text != self.clipboard.text:
            self._paste_text(text)
            return
        if not isinstance(copied, Copied):
            return
        if copied.name:
            self.dialogs.append(Dialog(*CANNOT_PASTE))
            return
        column, row = self.cursor
        left, top = (0 if copied.rows else column), max(row, 1)
        targets = [
            (c, r)
            for c in range(left, left + copied.width)
            for r in range(top, top + copied.height)
        ]
        if copied.rows and not confirm and any(key in self.cells for key in targets):
            self.dialogs.append(
                Dialog(DATA_LOSS, DATA_LOSS_MESSAGE, cancel=True, then=Binding("sheet", "paste_ok"))
            )
            return
        cells: dict[Key, list[object]] = {
            key: [*key, "entry", ""] for key in targets if key in self.cells
        }
        for dc, dr, kind, text_ in copied.cells:
            target = (left + dc, top + dr)
            if kind == "formula":
                moved = refs.shifted(
                    text_, target[0] - copied.origin[0] - dc, target[1] - copied.origin[1] - dr
                )
                cells[target] = [*target, "formula", moved or ""]
            else:
                cells[target] = [*target, kind, text_]
        valid = [cell for key, cell in cells.items() if 0 <= key[0] < COLUMNS and key[1] <= ROWS]
        if valid:
            self._send("put", cells=valid)
        self.anchor = (left, top)
        self.cursor = (min(left + copied.width - 1, COLUMNS - 1), top + copied.height - 1)

    def _paste_text(self, text: str) -> None:
        column, row = self.cursor
        rows = [line.split("\t") for line in text.replace("\r\n", "\n").strip("\n").split("\n")]
        cells = [
            [
                column + dc,
                max(row, 1) + dr,
                "formula" if value.startswith("=") else "entry",
                value.removeprefix("=").strip(),
            ]
            for dr, line in enumerate(rows)
            for dc, value in enumerate(line)
            if column + dc < COLUMNS
        ]
        if cells:
            self._send("put", cells=cells)

    def undo(self) -> None:
        if not self._undo:
            return
        self._redo.append(self._snapshot())
        self._sendback(self._undo.pop())

    def redo(self) -> None:
        if not self._redo:
            return
        self._undo.append(self._snapshot())
        self._sendback(self._redo.pop())

    def _sendback(self, snapshot: Snapshot) -> None:
        op = self._restore_of(snapshot)
        self.last = op
        self.link.send(op)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def _resend(self, arg: str) -> None:
        """Send an action built by a dialog (Sort, Generate Sequence, a Data Loss OK, a
        Conflict choice) as JSON: {"action": ..., "args": {...}}."""
        built = json.loads(arg)
        self._send(built["action"], **built["args"])

    # ---- the Menu ------------------------------------------------------------------------------

    def menu_action(self, arg: str) -> None:  # noqa: PLR0912 (one branch an item)
        """A Menu or context-menu item (`sheet` binding)."""
        column, row = self.cursor
        name, _, rest = arg.partition(":")
        if name in ("insert_row", "delete_row", "insert_column", "delete_column"):
            verb, what = name.split("_")
            self._send(verb, what=what, column=column, row=max(row, 1))
        elif name in ("insert_cell", "delete_cell"):
            self._send(name.split("_")[0], what="cell", column=column, row=max(row, 1))
        elif name == "delete_cells":
            left, top, right, bottom = self._span()
            for c in range(left, right + 1):
                for _ in range(top, bottom + 1):
                    self._send("delete", what="cell", column=c, row=top)
        elif name == "clear":
            self.clear()
        elif name == "fill":
            self.mode = "fill"
            self._fill_from = self._span()
            self.anchor = None
        elif name == "sort":
            self._sort_dialog()
        elif name == "generate":
            self.wizard = _generate_wizard(column)
        elif name == "goto":
            self._go_to_dialog()
        elif name == "recalculate":
            self._send("recalculate", undoable=False)
        elif name in ("select_row", "select_column"):
            self.select_whole("row" if name == "select_row" else "column")
        elif name == "move_column":
            self.mode = "move"
            self._move_to = column
        elif name == "resize":
            self.mode = "resize"
        elif name in ("maximize", "minimize"):
            self.widths[column] = WIDE if name == "maximize" else NARROW
        elif name == "formula":  # List Math and List Operations: `=mean(` in the formula row
            self.go((column, FORMULA_ROW))
            self.begin_edit(rest)
        elif name == "link":  # var > Link To
            self._send("name", column=column, text=rest)
        elif name == "unlink":
            self._send("name", column=column, text="")
        elif name == "store_var":  # var > Store Var: types `var` in the name cell, selected
            self.go((column, NAME_ROW))
            self.begin_edit("var")
        elif name == "paste_ok":
            self.paste(confirm=True)
        elif name in ("copy", "cut", "paste"):
            {"copy": self.copy, "cut": self.cut, "paste": self.paste}[name]()

    def _go_to_dialog(self) -> None:
        self.wizard = Wizard(
            "Go To",
            (Field("ref", ""),),
            steps=lambda values: [Binding("sheet_goto", values["ref"])],
        )

    def go_to(self, text: str) -> None:
        """Go To (ctrl+G): a cell such as `h40`, or a linked list's name, which selects its
        whole column (check 6, E10, E11; run 2, E24)."""
        ref = refs.address(text)
        if ref is not None:
            self.go((ref.column, ref.row))
            return
        column = self.column_named(text.strip())
        if column is None:
            self.dialogs.append(Dialog("Go To", GO_TO_INVALID))
            return
        self.go((column, 1))
        self.select_whole("column")

    def _sort_dialog(self) -> None:
        """Sort (check 6, E18): only with a block selected, as the menu item is grey otherwise."""
        block = self.selection()
        if block is None:
            return
        left, top, right, bottom = block
        letters = tuple((letter(c), letter(c)) for c in range(left, right + 1))
        span = [left, top, right, bottom]
        self.wizard = Wizard(
            "Sort",
            (
                Field(
                    "range",
                    "Range",
                    f"{letter(left)}{top}:{letter(right)}{bottom}",
                ),
                Field("by", "Sort By", letters[0][0], choices=letters),
                Field(
                    "order",
                    "Sort",
                    "ascending",
                    choices=(("ascending", "Ascending"), ("descending", "Descending")),
                ),
            ),
            steps=lambda values: [
                Binding(
                    "sheet_op",
                    json.dumps(
                        {
                            "action": "sort",
                            "args": {
                                "span": _range_span(values["range"]) or span,
                                "by": refs.column_index(values["by"]),
                                "descending": values["order"] == "descending",
                                "confirm": False,
                            },
                        }
                    ),
                )
            ],
        )

    # ---- modes: Fill, Move Column, Resize -----------------------------------------------------

    def _mode_key(self, action: str) -> None:
        moves = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
        if action in ("escape", "sheet_cancel"):
            self.mode = None
            return
        if self.mode == "fill":
            if action in moves:
                self.move(*moves[action])
                self.cursor = (self.cursor[0], max(self.cursor[1], 1))
            elif action in ("enter", "select"):
                self._finish_fill()
        elif self.mode == "move":
            if action in ("left", "right"):
                self._move_to = min(max(self._move_to + moves[action][0], 0), COLUMNS - 1)
            elif action in ("enter", "select"):
                self.mode = None
                if self._move_to != self.cursor[0]:
                    self._send("move", column=self.cursor[0], to=self._move_to)
                    self.go((self._move_to, self.cursor[1]))
        elif self.mode == "resize":
            column = self.cursor[0]
            if action in ("left", "right"):
                step = WIDTH_STEP * moves[action][0]
                self.widths[column] = min(max(self.width(column) + step, MIN_WIDTH), MAX_WIDTH)
            elif action in ("enter", "select"):
                self.mode = None

    def _finish_fill(self) -> None:
        """Fill (check 6, E6): from the cell or block chosen first to the range the arrows
        reached; a single cell then Fill, a range, then Enter."""
        source = self._fill_from
        marker = self._marker()
        self.mode = None
        if source is None or marker is None:
            return
        self._send("fill", source=list(source), target=list(marker))
        self.go((marker[0], marker[1]))


# ---- dialogs ------------------------------------------------------------------------------------


def _range_span(text: str) -> list[int] | None:
    first, _, second = text.partition(":")
    start, end = refs.address(first), refs.address(second or first)
    if start is None or end is None:
        return None
    return [start.column, start.row, end.column, end.row]


def _generate_wizard(column: int) -> Wizard:
    """Data > Generate Sequence (check 6, E14): the fields as on the emulator."""

    def steps(values: Mapping[str, str]) -> list[Binding]:
        args: dict[str, Any] = {
            "column": column,
            "formula": values["formula"],
            "initial": values["initial"],
            "first": int(values["first"] or 1),
            "last": int(values["last"] or 255),
            "step": int(values["step"] or 1),
            "ceiling": values["ceiling"],
            "confirm": False,
        }
        return [Binding("sheet_op", json.dumps({"action": "generate", "args": args}))]

    return Wizard(
        "Sequence",
        (
            Field("formula", "Formula: u(n)="),
            Field("initial", "Initial Terms"),
            Field("first", "n0", "1", whole=(-(10**6), 10**6)),
            Field("last", "nMax", "255", whole=(-(10**6), 10**6)),
            Field("step", "nStep", "1", whole=(1, 10**6)),
            Field("ceiling", "Ceiling Value"),
        ),
        steps=steps,
    )


def _conflict_wizard(error: SheetErrorPayload, last: SheetOp) -> Wizard:
    """Conflict Detected (run 2, E7): Cell Reference or Variable Reference for each name, then
    the formula goes in again with the choices."""
    choices = (("cell", "Cell Reference"), ("variable", "Variable Reference"))

    def steps(values: Mapping[str, str]) -> list[Binding]:
        choose = {name: values.get(name, "cell") for name in error["names"]}
        again = {"action": last["action"], "args": {**last["args"], "choose": choose}}
        return [Binding("sheet_choose", json.dumps(again))]

    return Wizard(
        "Conflict Detected",
        tuple(
            Field(name, f"{name} :  Cell or Variable?", "cell", choices=choices)
            for name in error["names"]
        ),
        steps=steps,
    )


def _inside(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> bool:
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


# ---- saving -------------------------------------------------------------------------------------


def dump(sheet: Spreadsheet) -> dict[str, Any]:
    """A sheet page in a document file: its definitions and view state, not its values."""
    columns = {letter(c): list(info) for c, info in enumerate(sheet.columns) if any(info)}
    return {
        "cells": [[c, r, kind, text] for (c, r), (kind, text) in sorted(sheet.cells.items())],
        "columns": columns,
        "widths": {letter(c): w for c, w in sorted(sheet.widths.items())},
        "cursor": list(sheet.cursor),
        "top": sheet.top,
        "left": sheet.left,
    }


def load(sheet: Spreadsheet, data: dict[str, Any]) -> Spreadsheet:
    """Fill a new page from a file. The engine gets the sheet in `Spreadsheet.loaded`."""
    for column, row, kind, text in data.get("cells", []):
        if kind in ("entry", "formula") and 0 <= int(column) < COLUMNS and 1 <= int(row) <= ROWS:
            sheet.cells[(int(column), int(row))] = (str(kind), str(text))
    columns = list(sheet.columns)
    for name, info in data.get("columns", {}).items():
        columns[refs.column_index(name)] = (info[0], info[1], info[2])
    sheet.columns = columns
    sheet.widths = {
        refs.column_index(name): min(max(int(w), MIN_WIDTH), MAX_WIDTH)
        for name, w in data.get("widths", {}).items()
    }
    column, row = data.get("cursor", [0, 1])
    sheet.go((int(column), int(row)))
    sheet.top = min(max(int(data.get("top", 1)), 1), ROWS)
    sheet.left = min(max(int(data.get("left", 0)), 0), COLUMNS - 1)
    return sheet


def spreadsheet_of(page: object) -> Spreadsheet | None:
    model = getattr(page, "model", None)
    return model if isinstance(model, Spreadsheet) else None
