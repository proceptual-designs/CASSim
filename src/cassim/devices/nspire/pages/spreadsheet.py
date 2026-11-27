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

import copy
import json
import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, cast

from cassim.device.editor import MARK, Editor, Kind, Row, Template, linear_text, parse_target
from cassim.device.engine import RemoteSession
from cassim.device.entry_session import EntryRules, EntrySession
from cassim.device.keys import Action, Binding
from cassim.device.menu import MenuItem
from cassim.device.sheet_link import SheetLink, link_for
from cassim.device.wizard import Field, Wizard
from cassim.devices.nspire import sheet_inference
from cassim.devices.nspire.editor_storage import dump_nodes, load_nodes
from cassim.devices.nspire.pages.statistics import Statistics, dump_statistics, load_statistics
from cassim.devices.nspire.statistics_plot import AreaPlot, PValuePlot
from cassim.sheet import refs
from cassim.sheet.fileio import FileCell
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

# Statistics > Stat Calculations on a sheet, after One-Variable (check 4 E15; run 4, S4):
# (label, command, menu key)
STAT_CALCULATIONS = (
    ("Two-Variable Statistics", "TwoVar", "2"),
    ("Linear Regression (mx+b)", "LinRegMx", "3"),
    ("Linear Regression (a+bx)", "LinRegBx", "4"),
    ("Median-Median Line", "MedMed", "5"),
    ("Quadratic Regression", "QuadReg", "6"),
    ("Cubic Regression", "CubicReg", "7"),
    ("Quartic Regression", "QuartReg", "8"),
    ("Power Regression", "PowerReg", "9"),
    ("Exponential Regression", "ExpReg", "A"),
    ("Logarithmic Regression", "LnReg", "B"),
    ("Sinusoidal Regression", "SinReg", "C"),
    ("Logistic Regression (d=0)", "Logistic", "D"),
    ("Logistic Regression (d≠0)", "LogisticD", "E"),
)
INVALID_INPUT = "Cannot accept change: Invalid input."
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
        "sheet_bar",
        "sheet_op",
        "sheet_goto",
        "sheet_choose",
        "sheet_tap",
        "sheet_ref_mode",
        "sheet_ref_fixed",
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
    entries: tuple[tuple[int, int, Row], ...] = ()


@dataclass
class ReferenceSelection:
    anchor: Key
    focus: Key
    start: int
    end: int


@dataclass
class ShadePane:
    """Draw: Shade P Value (stats4 I2): the test's statistic and p-value, read from the engine's
    `stat.` results once the test has run and then kept, so a later test leaves this pane as it
    was (the 2×2 page in R5-I2 shows a z and a t pane side by side)."""

    variable: str  # "z" or "t"
    alternative: int  # 0 ≠, 1 <, 2 >
    plot: PValuePlot | None = None


@dataclass(frozen=True)
class AreaPane:
    """Draw: Shade area in the Normal Cdf dialog (split2 H14)."""

    plot: AreaPlot


type Pane = Statistics | ShadePane | AreaPane
MAX_PANES = 4  # the sheet and up to three more (decision 0034 item 2); Custom Split stays grey


# The sheet Menu's items that depend on what is selected (sheet5, R5-Q1 and R5-S): what each is
# enabled for. Keys are a `sheet` item's action or a submenu's label.
_NOT_BLOCK = frozenset({"cell", "column", "name", "row"})
_DATA = frozenset({"cell", "column", "name"})
MENU_ENABLED_FOR: dict[str, frozenset[str]] = {
    "Insert": _NOT_BLOCK,
    "Statistics": _NOT_BLOCK,
    "move_column": _NOT_BLOCK,
    "Resize": _NOT_BLOCK,
    "Select": _NOT_BLOCK,
    "generate": _DATA,
    "Data capture": _DATA,
    "Random": _DATA,
    "List math": _DATA,
    "List operations": _DATA,
    "fill": frozenset({"cell", "block"}),
    "clear": frozenset({"column", "name", "row"}),
}


def pane_boxes(count: int, width: float, height: float) -> list[tuple[float, float, float, float]]:
    """Where each of a page's panes goes, as (left, top, width, height): one fills the page; two
    are left and right halves; three put the first on the left and the others one above the other
    on the right (R5-I2, t Test); four are 2×2 in reading order (R5-I2, 1-Prop z Test)."""
    half_w, half_h = width / 2, height / 2
    if count <= 1:
        return [(0, 0, width, height)]
    if count == 2:  # noqa: PLR2004 (the layouts are by count)
        return [(0, 0, half_w, height), (half_w, 0, half_w, height)]
    if count == 3:  # noqa: PLR2004
        return [
            (0, 0, half_w, height),
            (half_w, 0, half_w, half_h),
            (half_w, half_h, half_w, half_h),
        ]
    return [
        (0, 0, half_w, half_h),
        (half_w, 0, half_w, half_h),
        (0, half_h, half_w, half_h),
        (half_w, half_h, half_w, half_h),
    ]


@dataclass(frozen=True)
class Snapshot:
    cells: dict[Key, tuple[str, str]]
    columns: tuple[ColumnPayload, ...]
    panes: tuple[Pane, ...] | None = None  # set for a step that changed the page's panes


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
    reference: tuple[int, int, int, int] | None = None
    edit_selection: tuple[int, int] | None = None


def letter(column: int) -> str:
    return refs.column_letter(column)


def _definition_text(kind: str, text: str) -> str:
    return f"={text}" if kind == "formula" and text else text


def _sheet_text(row: Row, *, clone: bool = True) -> str:
    """Keep the spreadsheet's existing spelling for simple digit powers."""
    if not any(isinstance(node, Template) for node in row):
        return linear_text(row)
    nodes = copy.deepcopy(row) if clone else row

    def compact(items: Row) -> None:
        index = 0
        while index < len(items):
            node = items[index]
            if isinstance(node, Template):
                for slot in node.slots:
                    compact(slot)
                if node.kind is Kind.POWER:
                    slot = node.slots[0]
                    digits = [item for item in slot if item != MARK]
                    following = next((item for item in items[index + 1 :] if item != MARK), None)
                    delimited = following is None or (
                        isinstance(following, str) and following in "+-*/=<>),:;]}"
                    )
                    if (
                        delimited
                        and len(digits) == 1
                        and isinstance(digits[0], str)
                        and digits[0].isdigit()
                    ):
                        items[index : index + 1] = ["^", *slot]
                        index += len(slot)
            index += 1

    compact(nodes)
    return linear_text(nodes)


def _shift_entry_nodes(nodes: Row, columns: int, rows: int) -> Row | None:
    """Shift references in a copied entry without losing its structured templates."""
    original = _sheet_text(nodes)
    shifted = refs.shifted(original, columns, rows)
    if shifted is None:
        return None
    result = copy.deepcopy(nodes)
    runs: list[tuple[int, int, Row, int]] = []

    def collect(row: Row, path: list[tuple[int, int]]) -> None:
        index = 0
        while index < len(row):
            node = row[index]
            if isinstance(node, Template):
                for slot, children in enumerate(node.slots):
                    collect(children, [*path, (index, slot)])
                index += 1
                continue
            start = index
            while index < len(row) and isinstance(row[index], str):
                index += 1
            marked = copy.deepcopy(result)
            target = marked
            for parent, slot in path:
                template = target[parent]
                assert isinstance(template, Template)
                target = template.slots[slot]
            target.insert(start, MARK)
            offset = _sheet_text(marked, clone=False).index(MARK)
            runs.append((offset, index - start, row, start))

    collect(result, [])
    for found in reversed(refs.scan(original)):
        run = next(
            (item for item in runs if item[0] <= found.start and found.end <= item[0] + item[1]),
            None,
        )
        if run is None:
            raise ValueError("spreadsheet reference crosses structured entry nodes")
        offset, _, row, start = run
        replacement = refs.shifted(original[found.start : found.end], columns, rows)
        assert replacement is not None
        row[start + found.start - offset : start + found.end - offset] = list(replacement)
    if _sheet_text(result) != shifted:
        raise ValueError("shifted spreadsheet entry does not match its formula")
    return result


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
        # The page's other panes, after the sheet (decision 0034 item 2).
        self.panes: list[Pane] = []
        self._pending_shade: ShadePane | None = None  # waits for its test's results
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
        # The cell being edited: `editor` is the entry session's editor while a cell is open.
        # The sheet keeps no undo inside a cell, and an operator typed first gets no `Ans`.
        self._entry = EntrySession(clipboard, EntryRules(cells_paste=True, undo=False))
        self.editor: Editor | None = None
        self.entry_nodes: dict[tuple[Key, str], Row] = {}
        self.selected = False  # the whole of `editing` is selected: a key typed replaces it
        self.reference: ReferenceSelection | None = None
        self.reference_mode: bool | None = None  # None chooses from the formula at the caret
        self.mode: Literal["fill", "move", "resize"] | None = None
        self._fill_from: tuple[int, int, int, int] | None = None
        self._move_to = 0
        # Dialogs and the last action, which a Data Loss OK or a Conflict choice sends again.
        self.dialogs: list[Dialog] = []
        self.wizard: Wizard | None = None  # a dialog for the app to open
        self.last: SheetOp | None = None
        self._pending_import: list[list[object]] | None = None
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []

    @property
    def editing(self) -> str | None:
        return _sheet_text(self.editor.root) if self.editor is not None else None

    def _marked(self, pos: int | None = None) -> str:
        assert self.editor is not None
        editor = copy.deepcopy(self.editor)
        if pos is not None:
            editor.pos = pos
        editor.row().insert(editor.pos, MARK)
        return _sheet_text(editor.root, clone=False)

    @property
    def caret(self) -> int:
        return self._marked().index(MARK) if self.editor is not None else 0

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

    def _snapshot(self, *, panes: bool = False) -> Snapshot:
        return Snapshot(dict(self.cells), tuple(self.columns), tuple(self.panes) if panes else None)

    @property
    def split_statistics(self) -> list[Statistics]:
        """The Data & Statistics panes, in page order."""
        return [pane for pane in self.panes if isinstance(pane, Statistics)]

    def add_pane(self, pane: Pane, *, undoable: bool = True) -> None:
        """Put another app on the page: a second pane on the right, a third under it, a fourth
        making a 2×2 page whose new pane is bottom left (R5-I2). A full page replaces its newest
        pane. `undoable`: one ctrl+Z removes it again (R5-Q1: Quick Graph); a shaded pane stays
        when its cell is undone (R5-H14), so it is not."""
        if undoable:
            self._undo.append(self._snapshot(panes=True))
            del self._undo[:-UNDO_DEPTH]
            self._redo.clear()
        if len(self.panes) >= MAX_PANES - 1:
            self.panes[1] = pane
        else:
            self.panes.insert(min(len(self.panes), 1), pane)

    def loaded(self) -> None:
        """After a document's pages are loaded: rebuild the sheet in the engine. This runs after
        the Problem's other pages, so the sheet's saved values win over older Calculator entries."""
        self.link.alive(self.id)
        self.link.send(self.restore_op())
        self.update()

    def take_replies(self) -> None:
        """Take the engine's replies for this sheet. They wait in the session while another page
        is on screen, so a sheet left before its reply came back takes it here."""
        for reply in self.link.take(self.id):
            self._accept(reply)

    def update(self) -> None:
        """Take the engine's replies, then ask for the cells on show if they are out of date."""
        self.take_replies()
        for statistics in self.split_statistics:
            statistics.update()
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
        error = reply["error"]
        if error is not None and error["title"] != DATA_LOSS and not error["names"]:
            self._pending_shade = None  # refused; a Data Loss or a Conflict asks first
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
        if reply["error"] is None:
            self._refresh_shading()

    def _refresh_shading(self) -> None:
        """A shaded pane whose test has run takes its statistic and p-value; a new one joins the
        page then."""
        waiting = [pane for pane in self.panes if isinstance(pane, ShadePane) and not pane.plot]
        pending = self._pending_shade
        if pending is None and not waiting:
            return
        values = {row.name.casefold(): row.text for row in self.session.variables()}

        def number(name: str) -> float | None:
            text = values.get(name)
            try:
                return float(text.replace("ᴇ", "e")) if text is not None else None
            except ValueError:
                return None

        for pane in [*waiting, *([pending] if pending is not None else [])]:
            statistic, p_value = number(f"stat.{pane.variable}"), number("stat.pval")
            if statistic is None or p_value is None:
                continue
            df = number("stat.df") if pane.variable == "t" else None
            pane.plot = PValuePlot(statistic, p_value, pane.alternative, pane.variable, df)
            if pane is pending:
                self._pending_shade = None
                self.add_pane(pane, undoable=False)

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
            columns = {shown.casefold() for _, shown, _ in self.columns if shown}
            self.wizard = _conflict_wizard(error, last, columns)
            return
        self.dialogs.append(Dialog(error["title"], error["message"]))
        if last is not None and last["action"] in ("cell", "formula", "name"):
            args = last["args"]
            rows = {"cell": args.get("row"), "formula": FORMULA_ROW, "name": NAME_ROW}
            self.cursor = (cast("int", args["column"]), cast("int", rows[last["action"]]))
            self.begin_edit(str(args["text"]))
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
            left, right = sorted((self.anchor[0], column)) if self.anchor else (column, column)
            return left, 1, right, ROWS
        if self.whole == "row":
            first, last = sorted((self.anchor[1], row)) if self.anchor else (row, row)
            return 0, first, COLUMNS - 1, last
        if self.anchor is None or self.anchor == self.cursor:
            return None
        left, right = sorted((self.anchor[0], column))
        top, bottom = sorted((max(self.anchor[1], 1), max(row, 1)))
        return left, top, right, bottom

    def whole_columns(self) -> tuple[int, int] | None:
        """The first and last of the whole columns selected: one, or more taken with shift+Left
        or shift+Right from a column or its name cell (R5-Q1)."""
        if self.whole != "column":
            return None
        column = self.cursor[0]
        other = self.anchor[0] if self.anchor is not None else column
        return min(column, other), max(column, other)

    def selection_kind(self) -> Literal["cell", "block", "column", "name", "row"]:
        """What is selected, which greys Menu items (sheet5, R5-S: a cell, a block, a column, or
        the name cell)."""
        if self.whole == "column":
            return "column"
        if self.cursor[1] == NAME_ROW:
            return "name"
        if self.whole == "row":
            return "row"
        return "block" if self.selection() is not None else "cell"

    def quick_graph_lists(self) -> tuple[str, ...]:
        """The lists Quick Graph plots: one or two selected columns, each linked to a list
        (R5-Q1). Empty when Quick Graph is grey."""
        if self.selection_kind() not in ("column", "name"):
            return ()
        left, right = self.whole_columns() or (self.cursor[0], self.cursor[0])
        if right - left > 1:
            return ()
        lists = {
            row.name.casefold(): row.name
            for row in self.session.variables()
            if row.items is not None and row.text.startswith("{")
        }
        found = tuple(
            lists.get((self.columns[c][0] or "").casefold(), "") for c in range(left, right + 1)
        )
        return found if all(found) else ()

    def adjust_menu(self, root: MenuItem) -> MenuItem:
        """The sheet's Menu or a context menu with items greyed by what is selected: Quick Graph
        everywhere, and the Menu's items as sheet5 recorded them."""
        graph = bool(self.quick_graph_lists())
        kind = self.selection_kind()
        menu = root.label == "Menu"
        in_results = self.cursor[0] in self.results_columns()

        def visit(item: MenuItem) -> MenuItem:
            items = tuple(visit(child) for child in item.items)
            enabled = item.enabled
            key = item.arg.partition(":")[0] if item.action == "sheet" else item.label
            if item.action == "sheet" and item.arg == "quick_graph":
                enabled = graph
            elif item.action == "sheet" and item.arg == "insert_cell" and in_results:
                enabled = False  # grey in a results column (run 6, R6-C8)
            elif menu and key in MENU_ENABLED_FOR and item is not root:
                enabled = enabled and kind in MENU_ENABLED_FOR[key]
            if items == item.items and enabled == item.enabled:
                return item
            return replace(item, items=items, enabled=enabled)

        return visit(root)

    def results_columns(self) -> set[int]:
        """The label and value columns of a Stat Calculations, interval or test result: `Title`
        in row 1 beside a column formula."""
        found: set[int] = set()
        for column in range(COLUMNS - 1):
            cell = self.cells.get((column, 1))
            if cell is not None and cell[1].strip('"') == "Title" and self.columns[column + 1][2]:
                found |= {column, column + 1}
        return found

    def _span(self) -> tuple[int, int, int, int]:
        """The selection, or the cursor's cell."""
        column, row = self.cursor
        if self.whole == "column":
            left, right = sorted((self.anchor[0], column)) if self.anchor else (column, column)
            bottom = max((self.last_row(c) for c in range(left, right + 1)), default=0)
            return left, 1, right, max(bottom, 1)
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
            editing = self._marked()
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
            self._reference_span(),
            self._text_selection(),
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
        if self.whole == "column":
            left, right = sorted((self.anchor[0], column)) if self.anchor else (column, column)
            first = letter(left).upper()
            return first if left == right else f"{first}:{letter(right).upper()}"
        if row == NAME_ROW:
            return letter(column).upper()
        if self.whole == "row":
            first, last = sorted((self.anchor[1], row)) if self.anchor else (row, row)
            return str(first) if first == last else f"{first}:{last}"
        block = self.selection()
        if block is not None:
            a, b, c, d = block
            return f"{letter(a).upper()}{b}:{letter(c).upper()}{d}"
        if row == FORMULA_ROW:
            return f"{letter(column).upper()}="
        return f"{letter(column).upper()}{row}"

    def context_menu(self) -> str:
        """The context menu for where the cursor is (check 6, E2, E12; run 2, E2; run 4, S12:
        the name cell's differs from a selected column's)."""
        if self.whole == "column":
            return "sheet_column"
        if self.cursor[1] == NAME_ROW:
            return "sheet_name"
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
        elif self.editing is not None:
            handler = self._edit_keys().get(action)
            if handler is not None:
                handler(arg)
            elif action in ("sheet_tap", "sheet_drag"):
                self._keys()[action](arg)
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
            if self._pending_import is not None:
                self._pending_import = None
            if dialog.title == DATA_LOSS:
                self._pending_shade = None
            self.dialogs.pop(0)

    def _keys(self) -> dict[Action, Callable[[str], None]]:
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
            "enter": lambda _: self.begin_edit(self.entry_text(self.cursor), selected=True),
            "select": lambda _: self.begin_edit(self.entry_text(self.cursor), selected=True),
            "insert": self.type_text,
            "insert_linear": self.type_text,
            "template": self._start_template,
            "power": self._start_power,
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
            "sheet_bar": lambda _: self.edit_bar(),
        }

    def _edit_keys(self) -> dict[Action, Callable[[str], None]]:
        return {
            "insert": self._insert,
            "insert_linear": lambda text: self._insert(text, linear=True),
            "template": self._template,
            "power": self._power,
            "accent": lambda _: self._accent(),
            "left": lambda _: self._edit_arrow(-1, 0),
            "right": lambda _: self._edit_arrow(1, 0),
            "home": lambda _: self._move_editor("home"),
            "home_key": lambda _: self._move_editor("home"),
            "end": lambda _: self._move_editor("end"),
            "backspace": lambda _: self._erase(before=True),
            "delete": lambda _: self._erase(before=False),
            "clear": lambda _: self._clear_text(),
            "escape": lambda _: self.cancel_edit(),
            "enter": lambda _: self.commit(then=(0, 1)),
            "select": lambda _: self.commit(then=(0, 1)),
            "up": lambda _: self._edit_arrow(0, -1),
            "down": lambda _: self._edit_arrow(0, 1),
            "select_left": lambda _: self._edit_arrow(-1, 0, extend=True),
            "select_right": lambda _: self._edit_arrow(1, 0, extend=True),
            "select_cells": self._edit_select_cells,
            "select_to_start": lambda _: self._move_editor("select_to_start"),
            "select_to_end": lambda _: self._move_editor("select_to_end"),
            "word_left": lambda _: self._move_editor("word_left"),
            "word_right": lambda _: self._move_editor("word_right"),
            "select_word_left": lambda _: self._move_editor("select_word_left"),
            "select_word_right": lambda _: self._move_editor("select_word_right"),
            "tab": lambda _: self._tab(back=False),
            "shift_tab": lambda _: self._tab(back=True),
            "select_all": lambda _: self._select_editing(),
            "copy": lambda _: self._copy_editing(),
            "cut": lambda _: self._copy_editing(cut=True),
            "paste": self._paste_editing,
            "place": lambda target: self._place(target, extend=False),
            "extend": lambda target: self._place(target, extend=True),
            "sheet_ref_mode": lambda _: self.toggle_reference_mode(),
            "sheet_ref_fixed": lambda _: self.toggle_reference_fixed(),
            "sheet_bar": lambda _: self.edit_bar(),
        }

    # ---- moving and selecting -----------------------------------------------------------------

    def move(self, columns: int, rows: int, *, extend: bool = False) -> None:
        column, row = self.cursor
        if extend and not rows and row == NAME_ROW and self.whole != "column":
            self.select_whole("column")  # shift+Left or Right from a name cell (R5-Q1)
        if extend and self.whole == "row":
            if rows:
                self.cursor = (column, min(max(row + rows, 1), ROWS))
            self._follow()
            return
        if extend and self.whole == "column":
            if columns:
                self.cursor = (min(max(column + columns, 0), COLUMNS - 1), row)
                self._follow()
            return
        if extend:
            if self.anchor is None:
                self.anchor = self.cursor
        else:
            self.anchor = None
            self.whole = None
        if extend and row >= 1 and columns < 0 and column == 0:
            self.anchor = (0, row)
            self.whole = "row"
            self._follow()
            return
        if extend and row == 1 and rows < 0:
            self.anchor = (column, NAME_ROW)
            self.whole = "column"
            self._follow()
            return
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

    def _follow(self, key: Key | None = None) -> None:
        """Scroll as little as keeps the cursor on show (run 2, G39: Go To h40 shows rows 36 to
        40 with H at the right)."""
        column, row = key if key is not None else self.cursor
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
        """A grid tap selects a cell, or points to a reference while editing a formula.
        `column,row,extend` extends the selection (shift+click, a drag)."""
        parts = arg.split(",")
        key = (int(parts[0]), int(parts[1]))
        extend = bool(parts[2:])
        if key[1] >= 1 and self._can_point():
            self._point(key, extend=extend)
            return
        if self.editing is not None:
            if key == self.cursor:
                return
            self.commit(then=(0, 0))
            if self.editing is not None or self.dialogs:
                return
        if extend and key[1] >= 1:
            if self.anchor is None:
                self.anchor = self.cursor
            self.whole = None
            self.cursor = key
            self._follow()
            return
        self.go(key)
        if key[1] == NAME_ROW:
            self.select_whole("column")

    def drag(self, arg: str) -> None:
        """A drag across the grid scrolls it by `columns,rows` (touch: a one-finger drag)."""
        columns, rows = (int(part) for part in arg.split(","))
        self.top = min(max(self.top + rows, 1), ROWS - self.rows_shown + 1)
        self.left = min(max(self.left + columns, 0), COLUMNS - self.columns_shown)

    def _formula_editing(self) -> bool:
        return self.editing is not None and self.editing.startswith("=") and not self.selected

    def _select_editing(self) -> None:
        assert self.editor is not None
        self.reference = None
        self.reference_mode = False
        self.editor.select_all()
        self.selected = bool(self.editor.root)

    def _text_selection(self) -> tuple[int, int] | None:
        if self.editor is None or self.editor.anchor is None:
            return None
        start, end = self.editor.span
        return self._marked(start).index(MARK), self._marked(end).index(MARK)

    def _can_point(self) -> bool:
        if not self._formula_editing() or self.editor is None or self.editor.selection():
            return False
        if self.editor.in_string:
            return False
        if self.reference is not None:
            return True
        if self.reference_mode is not None:
            return self.reference_mode
        prefix = linear_text(self.editor.row()[: self.editor.pos]).rstrip()
        if not prefix and self.editor.path:
            return True
        return prefix.endswith(
            ("=", "+", "-", "*", "/", "^", "(", ",", ":", "<", ">", "≤", "≥", "≠", "|")
        )

    def _reference_span(self) -> tuple[int, int, int, int] | None:
        if self.reference is None:
            return None
        a, b = self.reference.anchor, self.reference.focus
        return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])

    def _point(self, key: Key, *, extend: bool = False) -> None:
        assert self.editor is not None
        editor = self.editor
        selected = self.reference
        previous: refs.Ref | refs.Span | None = None
        if selected is None:
            self._delete_selection()
            anchor = (self.cursor[0], max(self.cursor[1], 1)) if extend else key
            selected = ReferenceSelection(anchor, key, editor.pos, editor.pos)
            self.reference = selected
        else:
            found = refs.scan(linear_text(editor.row()[selected.start : selected.end]))
            if found and isinstance(found[0].reference, refs.Ref | refs.Span):
                previous = found[0].reference
            if not extend:
                selected.anchor = key
            selected.focus = key
        old_start = previous.start if isinstance(previous, refs.Span) else previous
        old_end = previous.end if isinstance(previous, refs.Span) else previous
        start = refs.Ref(
            *selected.anchor,
            fixed_column=old_start.fixed_column if old_start else False,
            fixed_row=old_start.fixed_row if old_start else False,
        )
        end = refs.Ref(
            *selected.focus,
            fixed_column=old_end.fixed_column if old_end else False,
            fixed_row=old_end.fixed_row if old_end else False,
        )
        text = str(start) if start == end else str(refs.Span(start, end))
        editor.row()[selected.start : selected.end] = list(text)
        selected.end = selected.start + len(text)
        editor.pos = selected.end
        self.reference_mode = True
        self._follow(key)

    def _edit_arrow(self, columns: int, rows: int, *, extend: bool = False) -> None:
        assert self.editor is not None
        if rows and self.editor.path and self.reference is None and self.reference_mode is not True:
            self._move_editor("up" if rows < 0 else "down")
            return
        if self._can_point():
            current = self.reference.focus if self.reference is not None else self.cursor
            key = (
                min(max(current[0] + columns, 0), COLUMNS - 1),
                min(max(current[1] + rows, 1), ROWS),
            )
            self._point(key, extend=extend)
        elif extend:
            if columns:
                self._move_editor("select_left" if columns < 0 else "select_right")
        elif columns:
            self._move_editor("left" if columns < 0 else "right")
        elif self._formula_editing() and self.reference_mode is False:
            return
        else:
            self.commit(then=(0, rows))

    def _edit_select_cells(self, arg: str) -> None:
        axis, _, step = arg.partition(":")
        amount = int(step or 1)
        if self.editor is not None and self.editor.in_grid:
            self.reference = None
            self.reference_mode = False
            self.selected = False
            self.editor.select_cells(axis, amount)
            return
        self._edit_arrow(
            amount if axis == "col" else 0, amount if axis == "row" else 0, extend=True
        )

    def toggle_reference_mode(self) -> None:
        self.selected = False
        assert self.editor is not None
        self.editor.anchor = None
        if not self._formula_editing() or self.editor.in_string:
            return
        if self._can_point():
            self.reference = None
            self.reference_mode = False
            return
        self.reference_mode = True
        for start_pos, end_pos, ref in self._row_references():
            if start_pos <= self.editor.pos <= end_pos and isinstance(ref, refs.Ref | refs.Span):
                start = ref.start if isinstance(ref, refs.Span) else ref
                end = ref.end if isinstance(ref, refs.Span) else ref
                self.reference = ReferenceSelection(start.key(), end.key(), start_pos, end_pos)
                self._follow(end.key())
                break

    def toggle_reference_fixed(self) -> None:
        self.selected = False
        assert self.editor is not None
        self.editor.anchor = None
        if not self._formula_editing():
            return
        for start, end, ref in self._row_references():
            if not (start <= self.editor.pos <= end):
                continue
            if not isinstance(ref, refs.Ref | refs.Span):
                return

            def cycle(cell: refs.Ref) -> refs.Ref:
                states = ((False, False), (True, True), (False, True), (True, False))
                index = states.index((cell.fixed_column, cell.fixed_row))
                fixed_column, fixed_row = states[(index + 1) % len(states)]
                return refs.Ref(cell.column, cell.row, fixed_column, fixed_row)

            changed = (
                refs.Span(cycle(ref.start), cycle(ref.end))
                if isinstance(ref, refs.Span)
                else cycle(ref)
            )
            text = str(changed)
            self.editor.row()[start:end] = list(text)
            self.editor.pos = start + len(text)
            if self.reference is not None:
                self.reference.end = self.editor.pos
            return

    def _row_references(self) -> list[tuple[int, int, refs.Reference]]:
        assert self.editor is not None
        row = self.editor.row()
        offsets = {len(linear_text(row[:i])): i for i in range(len(row) + 1)}
        return [
            (offsets[found.start], offsets[found.end], found.reference)
            for found in refs.scan(linear_text(row))
            if found.start in offsets and found.end in offsets
        ]

    def edit_bar(self) -> None:
        if self.editing is None:
            self.begin_edit(self.entry_text(self.cursor))
        else:
            self._move_editor("end")

    def select_whole(self, what: Literal["row", "column"]) -> None:
        self.whole = what
        if what == "row":
            self.cursor = (self.cursor[0], max(self.cursor[1], 1))
            self.anchor = (0, self.cursor[1])
        else:
            self.anchor = (self.cursor[0], NAME_ROW)

    # ---- typing -------------------------------------------------------------------------------

    def begin_edit(self, text: str, *, selected: bool = False) -> None:
        """Edit the cursor's cell. `selected`: its content starts selected, so the first key
        typed replaces it (run 4, S16: Return on a filled cell)."""
        self.editor = self._entry.reset()
        saved = self.entry_nodes.get((self.cursor, text))
        if saved is not None:
            self.editor.root = copy.deepcopy(saved)
            self.editor.pos = len(self.editor.root)
        else:
            self.editor.insert_linear(text)
        if selected:
            self.editor.select_all()
        self.selected = selected and bool(text)
        self.reference = None
        self.reference_mode = None
        self.anchor = None
        self.whole = None

    def type_text(self, text: str) -> None:
        """A key that types starts editing the cell, replacing what it held (check 6, E5)."""
        self.begin_edit("")
        self._insert(text)

    def _typing(self) -> EntrySession:
        """The open cell's entry session, after typing ends any reference pointing and the
        whole-content selection."""
        assert self.editor is not None
        self.reference = None
        self.reference_mode = None
        self.selected = False
        return self._entry

    def _insert(self, text: str, *, linear: bool = False) -> None:
        entry = self._typing()
        if linear or MARK in text:
            entry.insert_linear(text)
        else:
            entry.insert(text)

    def _start_template(self, spec: str) -> None:
        self.begin_edit("")
        self._template(spec)

    def _start_power(self, exponent: str) -> None:
        self.begin_edit("")
        self._power(exponent)

    def _template(self, spec: str) -> None:
        self._typing().template(spec)

    def _power(self, exponent: str) -> None:
        self._typing().power(exponent)

    def _accent(self) -> None:
        """The accent key on the letter before the caret (see `device.accents`)."""
        assert self.editor is not None
        self._entry.accent()

    def _clear_text(self) -> None:
        self._typing().clear()

    def _moving(self) -> EntrySession:
        """The open cell's entry session, after a move ends any reference pointing (and does
        not choose it again from the formula at the caret)."""
        assert self.editor is not None
        self.selected = False
        self.reference = None
        self.reference_mode = False
        return self._entry

    def _move_editor(self, action: str) -> None:
        self._moving().move(action)

    def _place(self, target: str, *, extend: bool) -> None:
        parse_target(target)  # a target that does not parse is an error here
        self._moving().place(target, extend=extend)

    def _tab(self, *, back: bool) -> None:
        assert self.editor is not None
        if self.editor.path:
            self.reference = None
            self.reference_mode = False
            self._entry.move("shift_tab" if back else "tab")
        else:
            self.commit(then=(-1 if back else 1, 0))

    def _erase(self, *, before: bool) -> None:
        assert self.editor is not None
        if self.reference is not None:
            self.editor.anchor = self.reference.start
            self.editor.pos = self.reference.end
        entry = self._typing()
        if before:
            entry.backspace()
        else:
            entry.delete()

    def _delete_selection(self) -> bool:
        assert self.editor is not None
        if not self.editor.selection():
            return False
        self.editor.cut()
        self.selected = False
        return True

    def _copy_editing(self, *, cut: bool = False) -> None:
        assert self.editor is not None
        if self.reference is not None:
            self.editor.anchor = self.reference.start
            self.editor.pos = self.reference.end
            self.reference = None
            self.reference_mode = False
        if self._entry.cut() if cut else self._entry.copy():
            self.selected = False

    def _paste_editing(self, text: str) -> None:
        self._typing().paste(text)

    def cancel_edit(self) -> None:
        self.editor = None
        self.selected = False
        self.reference = None
        self.reference_mode = None

    def commit(self, then: tuple[int, int] = (0, 0)) -> None:
        """Enter what was typed, then move (Enter moves down: run 2, E4). An unchanged cell is
        not sent again."""
        text = (self.editing or "").strip()
        if self.editor is not None and any(isinstance(node, Template) for node in self.editor.root):
            nodes = copy.deepcopy(self.editor.root)
            while nodes and isinstance(nodes[0], str) and nodes[0].isspace():
                nodes.pop(0)
            while nodes and isinstance(nodes[-1], str) and nodes[-1].isspace():
                nodes.pop()
            text = _sheet_text(nodes)
            if self.cursor[1] == FORMULA_ROW and text and not text.startswith("="):
                nodes.insert(0, "=")
                self.entry_nodes[(self.cursor, f"={text}")] = nodes
            else:
                self.entry_nodes[(self.cursor, text)] = nodes
        self.editor = None
        self.selected = False
        self.reference = None
        self.reference_mode = None
        column, row = self.cursor
        if text != self.entry_text(self.cursor).strip():
            if row == NAME_ROW:
                self._send("name", column=column, text=text)
            elif row == FORMULA_ROW:
                formula = text if not text or text.startswith("=") else f"={text}"
                self._send("formula", column=column, text=formula, choose={})
            else:
                self.waiting[self.cursor] = text
                self._send("cell", column=column, row=row, text=text, choose={}, confirm=False)
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
            self._send("put", cells=cleared, confirm=False)

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
        entries = tuple(
            (c - left, r - top, copy.deepcopy(nodes))
            for ((c, r), entry), nodes in self.entry_nodes.items()
            if left <= c <= right
            and top <= r <= bottom
            and (c, r) in self.cells
            and self.entry_text((c, r)) == entry
        )
        copied = Copied(
            (left, top),
            right - left + 1,
            bottom - top + 1,
            cells,
            rows=self.whole == "row",
            entries=entries,
        )
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
        entries = {(dc, dr): nodes for dc, dr, nodes in copied.entries}
        for dc, dr, kind, text_ in copied.cells:
            target = (left + dc, top + dr)
            nodes = entries.get((dc, dr)) if target[0] < COLUMNS and target[1] <= ROWS else None
            if kind == "formula":
                shift_columns = target[0] - copied.origin[0] - dc
                shift_rows = target[1] - copied.origin[1] - dr
                moved = refs.shifted(text_, shift_columns, shift_rows)
                cells[target] = [*target, "formula", moved or ""]
                if nodes is not None and moved is not None:
                    shifted_nodes = _shift_entry_nodes(nodes, shift_columns, shift_rows)
                    if shifted_nodes is not None:
                        self.entry_nodes[(target, f"={moved}")] = shifted_nodes
            else:
                cells[target] = [*target, kind, text_]
                if nodes is not None:
                    self.entry_nodes[(target, text_)] = copy.deepcopy(nodes)
        valid = [cell for key, cell in cells.items() if 0 <= key[0] < COLUMNS and key[1] <= ROWS]
        if valid:
            self._send("put", cells=valid, confirm=False)
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
            self._send("put", cells=cells, confirm=False)

    def undo(self) -> None:
        if not self._undo:
            return
        snapshot = self._undo.pop()
        self._redo.append(self._snapshot(panes=snapshot.panes is not None))
        self._sendback(snapshot)

    def redo(self) -> None:
        if not self._redo:
            return
        snapshot = self._redo.pop()
        self._undo.append(self._snapshot(panes=snapshot.panes is not None))
        self._sendback(snapshot)

    def _sendback(self, snapshot: Snapshot) -> None:
        if snapshot.panes is not None:
            self.panes = list(snapshot.panes)
            if snapshot.cells == self.cells and snapshot.columns == tuple(self.columns):
                return
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
        if self._edit_structure_action(name, column, row):
            return
        if name == "generate":
            self.wizard = _generate_wizard(column)
        elif name == "summary_plot":
            self.wizard = self._summary_plot_wizard()
        elif name == "quick_graph":
            self._quick_graph()
        elif name == "split_summary":
            self._show_summary(cast("dict[str, str]", json.loads(rest)))
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
        elif name == "distribution":
            self.wizard = self._normal_cdf_wizard()
        elif name == "shade_area":
            self._shade_area(cast("dict[str, str]", json.loads(rest)))
        elif name in ("onevar", "stat", "inference", "edit", "dialog"):
            self._statistics_action(name, rest)
        elif name == "paste_ok":
            self.paste(confirm=True)
        elif name == "import_ok":
            self._import_pending()
        elif name in ("copy", "cut", "paste"):
            {"copy": self.copy, "cut": self.cut, "paste": self.paste}[name]()

    def _edit_structure_action(self, name: str, column: int, row: int) -> bool:
        if name not in (
            "insert_row",
            "delete_row",
            "insert_column",
            "delete_column",
            "insert_cell",
            "delete_cell",
            "delete_cells",
            "clear",
            "fill",
            "sort",
        ):
            return False
        if name in ("insert_row", "delete_row", "insert_column", "delete_column"):
            verb, what = name.split("_")
            self._send(verb, what=what, column=column, row=max(row, 1))
        elif name == "insert_cell" and (
            column in self.results_columns() or self.selection() is not None
        ):
            pass  # grey in a results column and with a range selected (run 6, R6-C8)
        elif name in ("insert_cell", "delete_cell"):
            self._send(name.split("_", maxsplit=1)[0], what="cell", column=column, row=max(row, 1))
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
        return True

    def _quick_graph(self) -> None:
        """A dot plot of one selected list, or a scatter plot of two (the first column on x),
        beside the sheet; one undo step (R5-Q1). Grey unless columns of lists are selected."""
        lists = self.quick_graph_lists()
        if not lists:
            return
        statistics = Statistics(self.session)
        statistics.perform(f"x:{lists[0]}")
        if len(lists) > 1:
            statistics.perform(f"y:{lists[1]}")
        self.add_pane(statistics)

    def _summary_plot_wizard(self) -> Wizard | None:
        """Summary Plot (R5-Q2): X List is a category or a numeric list, Summary List a numeric
        list, each taken from the selected columns first; Display On is Split Page first."""
        statistics = Statistics(self.session)
        lists, summaries = statistics.lists, statistics.numeric_lists
        if not lists or not summaries:
            self.dialogs.append(Dialog("Summary Plot", "Enter a list and a numeric list first."))
            return None
        left, _, right, _ = self._span()
        known = {name.casefold(): name for name in lists}
        names = [
            known.get((self.columns[c][0] or "").casefold(), "") for c in range(left, right + 1)
        ]
        names = [name for name in names if name]
        x_default = names[0] if names else lists[0]
        summary_default = next(
            (name for name in names[1:] if name in summaries),
            next((name for name in summaries if name != x_default), summaries[0]),
        )
        categories = lists
        fields = (
            Field(
                "x",
                "X List",
                x_default,
                choices=tuple((name, name) for name in categories),
            ),
            Field(
                "summary",
                "Summary List",
                summary_default,
                choices=tuple((name, name) for name in summaries),
            ),
            Field(
                "display",
                "Display On",
                "split",
                choices=(("split", "Split Page"), ("new", "New Page")),
            ),
        )

        def steps(values: Mapping[str, str]) -> list[Binding]:
            if values["display"] == "new":
                return [
                    Binding("add_page", "statistics"),
                    Binding("statistics", f"x:{values['x']}"),
                    Binding("statistics", f"summary:{values['summary']}"),
                ]
            return [
                Binding(
                    "sheet",
                    "split_summary:" + json.dumps({"x": values["x"], "summary": values["summary"]}),
                )
            ]

        return Wizard("Summary Plot", fields, steps=steps)

    def _show_summary(self, values: Mapping[str, str]) -> None:
        statistics = Statistics(self.session)
        statistics.perform(f"x:{values['x']}")
        statistics.perform(f"summary:{values['summary']}")
        self.add_pane(statistics)

    def import_rows(self, rows: list[list[FileCell]]) -> None:
        if not rows:
            raise ValueError("The file contains no data")
        column, row = self.cursor[0], max(self.cursor[1], 1)
        if column + max(map(len, rows)) > COLUMNS or row + len(rows) - 1 > ROWS:
            raise ValueError(f"The imported data does not fit in the {COLUMNS}-column sheet")
        targets = {
            (column + offset, row + row_offset)
            for row_offset, values in enumerate(rows)
            for offset, _ in enumerate(values)
        }
        cells: list[list[object]] = [
            [
                column + offset,
                row + row_offset,
                "formula" if cell.formula else "entry",
                cell.text,
            ]
            for row_offset, values in enumerate(rows)
            for offset, cell in enumerate(values)
        ]
        if cells:
            variable_lengths = {
                row.name.casefold(): len(row.items)
                for row in self.session.variables()
                if row.items is not None
            }
            if any(
                key in self.cells
                or self.columns[key[0]][2] is not None
                or key[1] <= variable_lengths.get((self.columns[key[0]][0] or "").casefold(), 0)
                or bool((view := self.view.get(key)) and view.text)
                for key in targets
            ):
                self._pending_import = cells
                self.dialogs.append(
                    Dialog(
                        DATA_LOSS,
                        DATA_LOSS_MESSAGE,
                        cancel=True,
                        then=Binding("sheet", "import_ok"),
                    )
                )
                return
            self._send("put", cells=cells, confirm=False)
            self.anchor = (column, row)
            self.cursor = (column + max(map(len, rows)) - 1, row + len(rows) - 1)

    def _import_pending(self) -> None:
        cells, self._pending_import = self._pending_import, None
        if cells:
            self._send("put", cells=cells, confirm=True)
            self.anchor = (cast("int", cells[0][0]), cast("int", cells[0][1]))
            self.cursor = (
                max(cast("int", cell[0]) for cell in cells),
                max(cast("int", cell[1]) for cell in cells),
            )

    def request_export_view(self) -> None:
        self.link.send(self.op("view", span=[0, 1, self._last_column(), self._last_row()]))

    def export_rows(self, *, formulas: bool = False) -> list[list[FileCell]]:
        column, row = self._last_column(), self._last_row()
        headers = [self.columns[index][1] or "" for index in range(column + 1)]
        rows = [[FileCell(value) for value in headers]] if any(headers) else []
        for r in range(1, row + 1):
            line: list[FileCell] = []
            for c in range(column + 1):
                kind, text = self.cells.get((c, r), ("", ""))
                if formulas and kind == "formula":
                    line.append(FileCell(text, True))
                else:
                    cell = self.view.get((c, r))
                    line.append(FileCell(cell.text if cell is not None else ""))
            rows.append(line)
        return rows

    def _last_row(self) -> int:
        lengths = {
            row.name.casefold(): len(row.items)
            for row in self.session.variables()
            if row.items is not None
        }
        return max(
            max((self.last_row(column) for column in range(COLUMNS)), default=1),
            max(
                (lengths.get((info[0] or "").casefold(), 0) for info in self.columns),
                default=1,
            ),
            1,
        )

    def _statistics_action(self, name: str, rest: str) -> None:
        """The Statistics menu's items, and what their dialogs send back."""
        if name == "onevar":  # One-Variable asks how many lists first (run 4, S1, S5)
            self.wizard = Wizard(
                "One-Variable Statistics",
                (Field("count", "Num of Lists:", "1", whole=(1, 20)),),
                steps=lambda values: [Binding("sheet", f"stat:OneVar:{values['count']}")],
            )
        elif name == "stat":
            command, _, count = rest.partition(":")
            self.wizard = self._stat_wizard(command, int(count or 1))
        elif name == "inference":
            self.wizard = self._inference_wizard(rest)
        elif name == "edit":  # a Distributions dialog: its formula, in the cell (run 4, S10)
            self.go((self.cursor[0], max(self.cursor[1], 1)))
            self.begin_edit(rest)
        else:  # "dialog": a dialog from a dialog's own check
            title, _, message = rest.partition(":")
            self.dialogs.append(Dialog(title, message))

    def _normal_cdf_wizard(self) -> Wizard:
        """Normal Cdf from a sheet (split2 H14): the Calculator's fields and Draw: Shade area.
        Unticked, the formula waits in the cell's entry line (run 4, S10); ticked, it goes into
        the selected cell and a shaded normal curve joins the page."""
        fields = (
            Field("lower", "Lower Bound", "-∞"),
            Field("upper", "Upper Bound"),
            Field("mu", "μ", "0"),
            Field("sigma", "σ", "1"),
            Field("shade", "Draw: Shade area", "0", toggle=True),
        )

        def steps(values: Mapping[str, str]) -> list[Binding]:
            parts = [values[name].strip() for name in ("lower", "upper", "mu", "sigma")]
            if not parts[1]:
                return [Binding("sheet", "dialog:Input Error:Required field is empty!")]
            if values.get("shade") == "1":
                return [Binding("sheet", "shade_area:" + json.dumps(dict(values)))]
            return [Binding("sheet", "edit:=normCdf(" + ",".join(parts) + ")")]

        return Wizard("Normal Cdf", fields, steps=steps)

    def _shade_area(self, values: Mapping[str, str]) -> None:
        """Put `=normCdf(…)` in the selected cell and add the shaded curve. The pane is not part
        of the cell's undo step: ctrl+Z restores the cell and the plot stays (R5-H14)."""
        parts = [values[name].strip() for name in ("lower", "upper", "mu", "sigma")]
        numbers = [_bound(part) for part in parts]
        if all(number is not None for number in numbers):
            lower, upper, mu, sigma = cast("list[float]", numbers)
            if math.isfinite(mu) and math.isfinite(sigma) and sigma > 0:
                self.add_pane(AreaPane(AreaPlot(lower, upper, mu, sigma)), undoable=False)
        column, row = self.cursor[0], max(self.cursor[1], 1)
        self.go((column, row))
        text = "=normCdf(" + ",".join(parts) + ")"
        self.waiting[(column, row)] = text
        self._send("cell", column=column, row=row, text=text, choose={}, confirm=False)

    def free_column(self) -> int:
        """The first column after the cursor's that holds nothing: where results go unless the
        dialog says otherwise (run 4, S1, S4)."""
        used = {c for c, _ in self.cells} | {c for c, info in enumerate(self.columns) if any(info)}
        used |= {c for c, _ in self.view}
        return next((c for c in range(self.cursor[0] + 1, COLUMNS) if c not in used), COLUMNS - 1)

    def free_function(self) -> str:
        """The first of f1, f2, ... that is not defined: Save RegEqn to's default (run 4, S4)."""
        return next(f"f{n}" for n in range(1, 100) if not self.session.is_defined(f"f{n}"))

    def _stat_wizard(self, command: str, count: int) -> Wizard:
        """A Stat Calculations dialog, with the emulator's fields and defaults (check 5, E15;
        run 4, S1 to S5). OK sends the `stat` action."""
        here = f"{letter(self.cursor[0])}[]"
        results = f"{letter(self.free_column())}[]"
        lists: tuple[Field, ...]
        if command == "OneVar":
            lists = tuple(
                Field(f"x{n}", f"X{n} List", here if n == 1 else "") for n in range(1, count + 1)
            )
        else:
            lists = (Field("x1", "X List", here), Field("x2", "Y List"))
        regression = command not in ("OneVar", "TwoVar")
        saving = (Field("save", "Save RegEqn to", self.free_function()),) if regression else ()
        extra = (
            (
                Field("freq", "Frequency List", "1"),
                Field("category", "Category List"),
                Field("include", "Include Categories"),
            )
            if count == 1
            else ()
        )
        titles = {"OneVar": "One-Variable Statistics", "TwoVar": "Two-Variable Statistics"}
        title = titles.get(
            command,
            next((label for label, name, _ in STAT_CALCULATIONS if name == command), command),
        )
        names = [field.name for field in lists]

        def steps(values: Mapping[str, str]) -> list[Binding]:
            target = refs.address(values["results"].strip().removesuffix("[]") + "1")
            if target is None or len(values["results"].strip().removesuffix("[]")) != 1:
                return [Binding("sheet", "dialog:Syntax Error:" + INVALID_INPUT)]
            if any(not values.get(name, "").strip() for name in names):
                return [Binding("sheet", "dialog:Input Error:Required field is empty!")]
            args = {
                "command": command,
                "lists": [values[name].strip() for name in names],
                "freq": values.get("freq", "1"),
                "category": values.get("category", ""),
                "include": values.get("include", ""),
                "save": values.get("save", "").strip(),
                "column": target.column,
                "choose": {},
                "confirm": False,
            }
            return [Binding("sheet_op", json.dumps({"action": "stat", "args": args}))]

        fields = (*lists, *saving, *extra, Field("results", "1st Result Column", results))
        return Wizard(title, fields, steps=steps)

    def _inference_wizard(self, arg: str) -> Wizard:
        """A Confidence Interval or Stat Test dialog writing a live result column (stats4, R5-I2):
        first the Data Input Method where the device asks it, then the form."""
        command, _, method = arg.partition(":")
        found = sheet_inference.inference(command)
        if found is None:
            raise ValueError(f"Unknown statistical command: {command}")
        if found.method and not method:
            methods = (("data", "Data"), *((("stats", "Stats"),) if found.stats else ()))
            return Wizard(
                found.title,
                (Field("method", "Data Input Method", "data", choices=methods),),
                steps=lambda values: [Binding("sheet", f"inference:{command}:{values['method']}")],
            )
        form = found.stats if method == "stats" and found.stats is not None else found.data
        here = f"{letter(self.cursor[0])}[]"
        fields: list[Field] = [
            replace(field, default=here) if field.default == sheet_inference.LIST else field
            for field in form.fields
        ]
        if found.save:
            fields.insert(2, Field("save", "Save RegEqn to", self.free_function()))
        following = f"{letter(min(self.cursor[0] + 1, COLUMNS - 1))}[]"
        fields.append(Field("results", "1st Result Column", following))
        if found.shade:
            fields.append(Field("shade", "Draw: Shade P Value", "0", toggle=True))

        def steps(values: Mapping[str, str]) -> list[Binding]:
            if any(not values.get(field.name, "").strip() for field in form.fields):
                return [Binding("sheet", "dialog:Input Error:Required field is empty!")]
            column_name = values["results"].strip().removesuffix("[]")
            target = refs.address(f"{column_name}1")
            if target is None or len(column_name) != 1:
                return [Binding("sheet", "dialog:Syntax Error:" + INVALID_INPUT)]
            formula = form.command(found.command, values)
            if found.save and values.get("save", "").strip():
                formula += f": CopyVar stat.RegEqn,{values['save'].strip()}"
            self._pending_shade = (
                ShadePane(found.shade, int(values.get("alternative", "0")))
                if found.shade and values.get("shade") == "1"
                else None
            )
            args = {"formula": formula, "column": target.column, "choose": {}, "confirm": False}
            return [Binding("sheet_op", json.dumps({"action": "inference", "args": args}))]

        back = (Binding("sheet", f"inference:{command}"),) if found.method else ()
        return Wizard(found.title, tuple(fields), steps=steps, back=back)

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
        if self.selection() is None:
            return
        block = self._span()
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


def _conflict_wizard(error: SheetErrorPayload, last: SheetOp, columns: set[str]) -> Wizard:
    """Conflict Detected (run 2, E7; run 4, S11): for each name, Cell Reference or Variable
    Reference (a name that is also a cell, `d1`), or Column Reference or Variable Reference (a
    linked column's name, `u`); then the formula goes in again with the choices."""
    cells = (("cell", "Cell Reference"), ("variable", "Variable Reference"))
    lists = (("cell", "Column Reference"), ("variable", "Variable Reference"))

    def field(name: str) -> Field:
        if name.casefold() in columns:
            return Field(name, f"{name} :  Column or Variable?", "cell", choices=lists)
        return Field(name, f"{name} :  Cell or Variable?", "cell", choices=cells)

    def steps(values: Mapping[str, str]) -> list[Binding]:
        choose = {name: values.get(name, "cell") for name in error["names"]}
        again = {"action": last["action"], "args": {**last["args"], "choose": choose}}
        return [Binding("sheet_choose", json.dumps(again))]

    return Wizard(
        "Conflict Detected",
        tuple(field(name) for name in error["names"]),
        steps=steps,
    )


def _bound(text: str) -> float | None:
    """A typed bound or parameter: `-∞` and `∞` as well as numbers."""
    plain = text.replace("−", "-").replace("ᴇ", "e").replace(" ", "")
    if plain in ("∞", "+∞", "-∞"):
        return -math.inf if plain.startswith("-") else math.inf
    try:
        return float(plain)
    except ValueError:
        return None


def _inside(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> bool:
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


# ---- saving -------------------------------------------------------------------------------------


def dump(sheet: Spreadsheet) -> dict[str, Any]:
    """A sheet page in a document file: its definitions and view state, not its values. The
    cursor and selection are not kept: a reopened sheet starts at A1 (R5-Q3).

    What was typed is kept even when the page was left before the engine answered: the sheet
    first takes the replies waiting for it, and a typed cell still unanswered is saved as typed
    (a bug lost the data, the column names and the plots that used them)."""
    sheet.take_replies()
    cells = dict(sheet.cells)
    for key, text in sheet.waiting.items():
        cells[key] = ("formula", text[1:]) if text.startswith("=") else ("entry", text)
    columns = {letter(c): list(info) for c, info in enumerate(sheet.columns) if any(info)}
    data: dict[str, Any] = {
        "cells": [[c, r, kind, text] for (c, r), (kind, text) in sorted(cells.items())],
        "columns": columns,
        "widths": {letter(c): w for c, w in sorted(sheet.widths.items())},
    }
    if sheet.panes:
        data["panes"] = [_dump_pane(pane) for pane in sheet.panes]
    entries = [
        [column, row, dump_nodes(nodes)]
        for ((column, row), text), nodes in sheet.entry_nodes.items()
        if (row <= FORMULA_ROW or (column, row) in sheet.cells)
        and sheet.entry_text((column, row)) == text
    ]
    if entries:
        data["entry_nodes"] = entries
    return data


def _dump_pane(pane: Pane) -> dict[str, Any]:
    if isinstance(pane, Statistics):
        return {"kind": "statistics", **dump_statistics(pane)}
    if isinstance(pane, ShadePane):
        plot = pane.plot
        return {
            "kind": "shade",
            "variable": pane.variable,
            "alternative": pane.alternative,
            "statistic": plot.statistic if plot is not None else None,
            "p_value": plot.p_value if plot is not None else None,
            "df": plot.df if plot is not None else None,
        }
    area = pane.plot
    return {
        "kind": "area",
        "lower": area.lower if math.isfinite(area.lower) else None,
        "upper": area.upper if math.isfinite(area.upper) else None,
        "mu": area.mu,
        "sigma": area.sigma,
    }


def _saved_number(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def _load_pane(sheet: Spreadsheet, saved: dict[str, Any]) -> Pane:
    kind = saved.get("kind")
    if kind == "statistics":
        return load_statistics(Statistics(sheet.session), saved)
    if kind == "shade":
        variable = saved.get("variable") if saved.get("variable") in ("z", "t") else "z"
        alternative = saved.get("alternative")
        if alternative not in (0, 1, 2) or isinstance(alternative, bool):
            alternative = 0
        pane = ShadePane(str(variable), int(alternative))
        statistic, p_value = (
            _saved_number(saved.get("statistic")),
            _saved_number(saved.get("p_value")),
        )
        if statistic is not None and p_value is not None:
            df = _saved_number(saved.get("df"))
            pane.plot = PValuePlot(statistic, p_value, pane.alternative, pane.variable, df)
        return pane
    if kind == "area":
        lower, upper = _saved_number(saved.get("lower")), _saved_number(saved.get("upper"))
        mu, sigma = _saved_number(saved.get("mu")), _saved_number(saved.get("sigma"))
        return AreaPane(
            AreaPlot(
                -math.inf if lower is None else lower,
                math.inf if upper is None else upper,
                0.0 if mu is None else mu,
                sigma if sigma is not None and sigma > 0 else 1.0,
            )
        )
    raise ValueError(f"unknown pane {kind!r}")


def load(sheet: Spreadsheet, data: dict[str, Any]) -> Spreadsheet:
    """Fill a new page from a file. The engine gets the sheet in `Spreadsheet.loaded`."""
    for column, row, kind, text in data.get("cells", []):
        if kind in ("entry", "formula") and 0 <= int(column) < COLUMNS and 1 <= int(row) <= ROWS:
            sheet.cells[(int(column), int(row))] = (str(kind), str(text))
    columns = list(sheet.columns)
    for name, info in data.get("columns", {}).items():
        columns[refs.column_index(name)] = (info[0], info[1], info[2])
    sheet.columns = columns
    for column, row, nodes in data.get("entry_nodes", []):
        key = (int(column), int(row))
        if not (0 <= key[0] < COLUMNS and NAME_ROW <= key[1] <= ROWS):
            raise ValueError("invalid spreadsheet entry location")
        restored = load_nodes(nodes)
        text = _sheet_text(restored)
        if sheet.entry_text(key) != text:
            raise ValueError("spreadsheet entry nodes do not match the definition")
        sheet.entry_nodes[(key, text)] = restored
    sheet.widths = {
        refs.column_index(name): min(max(int(w), MIN_WIDTH), MAX_WIDTH)
        for name, w in data.get("widths", {}).items()
    }
    panes = data.get("panes", [])
    if not isinstance(panes, list) or not all(isinstance(saved, dict) for saved in panes):
        raise ValueError("invalid panes")
    sheet.panes = [_load_pane(sheet, saved) for saved in panes[: MAX_PANES - 1]]
    return sheet


def spreadsheet_of(page: object) -> Spreadsheet | None:
    model = getattr(page, "model", None)
    return model if isinstance(model, Spreadsheet) else None
