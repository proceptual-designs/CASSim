"""The engine's side of the Lists & Spreadsheet pages (slice 3a, decision 0031).

`EngineCore` keeps one `ProblemSheets` per Problem that has a sheet. It runs the `sheet` ops and,
after every op of any kind, brings every sheet of the Problem up to date with its variables
(`settle`), so a reply is always consistent: a Calculator store reaches the cells, and a cell
reaches the lists and the other sheets, before the engine answers.

This module loads SymPy through `cassim.sheet`, so only the engine imports it, lazily (decision
0027: the UI worker never loads SymPy).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from cassim.sheet import actions
from cassim.sheet.refs import COLUMNS, Ref, Span
from cassim.sheet.sheet import (
    ColumnInfo,
    ConflictError,
    Content,
    Entry,
    Formula,
    Key,
    Notice,
    Sheet,
    SheetError,
)

if TYPE_CHECKING:
    from cassim.core.session import Session
    from cassim.device.engine import (
        ColumnPayload,
        NoticePayload,
        SheetErrorPayload,
        SheetOp,
        SheetReply,
    )

# How many rounds of one sheet's writes reaching another settle may take; a loop of sheets
# feeding each other stops here.
_MAX_ROUNDS = 10


def _span(value: object) -> Span:
    left, top, right, bottom = cast("list[int]", value)
    return Span(Ref(left, top), Ref(right, bottom))


class ProblemSheets:
    """The sheets of one Problem, by page id."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.pages: dict[int, Sheet] = {}
        self._reported: dict[int, int] = {}  # each page's revision in the last reply
        # Each page's contents and columns as last reported, so a reply carries only the edits:
        # the UI keeps the sheet's definitions (it saves the document without the engine).
        self._known: dict[int, tuple[dict[Key, Content], list[ColumnPayload]]] = {}
        self._viewed_at: dict[int, int] = {}  # each page's revision when its view was taken

    def run(self, op: SheetOp, replies: dict[int, SheetReply]) -> None:
        """Apply one sheet op; what it shows goes into `replies` for its page."""
        page = op["page"]
        if op["action"] == "drop":
            self.pages.pop(page, None)
            self._relock()
            return
        sheet = self.pages.get(page)
        if sheet is None:
            sheet = self.pages[page] = Sheet(self.session)
        reply = _reply(replies, page)
        try:
            reply["notices"].extend([_notice(n) for n in self._act(sheet, op)])
        except SheetError as error:
            names = list(error.names) if isinstance(error, ConflictError) else []
            failed: SheetErrorPayload = {
                "title": error.title,
                "message": error.message,
                "names": names,
            }
            reply["error"] = failed
        if op["action"] == "view":
            self._view(sheet, _span(op["args"]["span"]), reply)
            self._viewed_at[page] = sheet.revision
        self._relock()

    def _act(self, sheet: Sheet, op: SheetOp) -> list[Notice]:  # noqa: PLR0911 (one per action)
        args = op["args"]
        column = cast("int", args.get("column", 0))
        row = cast("int", args.get("row", 0))
        choose = cast("dict[str, str]", args.get("choose", {}))
        match op["action"]:
            case "cell":
                text = cast("str", args["text"])
                confirm = bool(args["confirm"])
                return sheet.set_cell(column, row, text, choose=choose, confirm=confirm)
            case "formula":
                return sheet.set_column_formula(column, cast("str", args["text"]), choose=choose)
            case "name":
                return sheet.set_name(column, cast("str", args["text"]))
            case "fill":
                return actions.fill(sheet, _span(args["source"]), _span(args["target"]))
            case "sort":
                return actions.sort(
                    sheet,
                    _span(args["span"]),
                    cast("int", args["by"]),
                    descending=bool(args["descending"]),
                    confirm=bool(args["confirm"]),
                )
            case "insert" | "delete":
                return _structure(sheet, op["action"], cast("str", args["what"]), column, row)
            case "generate":
                return actions.generate_sequence(
                    sheet,
                    column,
                    cast("str", args["formula"]),
                    initial=cast("str", args["initial"]),
                    first=cast("int", args["first"]),
                    last=cast("int", args["last"]),
                    step=cast("int", args["step"]),
                    ceiling=cast("str", args["ceiling"]),
                    confirm=bool(args["confirm"]),
                )
            case "recalculate":
                return sheet.recalculate()
            case "restore":
                return _restore(sheet, args)
            case "move":
                return actions.move_column(sheet, column, cast("int", args["to"]))
            case "put":
                return sheet.put(_contents(args["cells"]), confirm=bool(args["confirm"]))
            case _:  # "view" changes nothing
                return []

    def _view(self, sheet: Sheet, span: Span, reply: SheetReply) -> None:
        """The cells of `span` as drawn. Only the cells asked for are formatted (decision 0031,
        spike B)."""
        reply["span"] = [span.start.column, span.start.row, span.end.column, span.end.row]
        reply["cells"] = [
            (column, row, shown.text, shown.right, sheet.text(column, row))
            for column, row in span.cells()
            if (shown := sheet.shown(column, row)).text
        ]

    def _edits(self, page: int, sheet: Sheet, reply: SheetReply) -> None:
        """What changed in the page's definitions since the last reply: cells as
        [column, row, kind, text] ("" kind for a cleared cell), and the columns when they
        changed. Contents are compared as objects, so only changed cells are formatted."""
        contents = sheet.contents()
        columns: list[ColumnPayload] = [
            (info.name, info.shown_name, info.formula)
            for info in (sheet.column(c) for c in range(COLUMNS))
        ]
        before, old_columns = self._known.get(page, ({}, []))
        # A reply may already hold edits from an earlier op of the same batch: the latest wins.
        edits = {
            (column, row): (column, row, kind, text) for column, row, kind, text in reply["edits"]
        }
        for key, content in contents.items():
            old = before.get(key)
            if old is not content and old != content:
                edits[key] = (*key, *sheet.saved(key))
        for key in before.keys() - contents.keys():
            edits[key] = (*key, "", "")
        reply["edits"] = [edits[key] for key in sorted(edits)]
        if columns != old_columns:
            reply["columns"] = columns
        self._known[page] = (contents, columns)

    def settle(self, replies: dict[int, SheetReply], *, recalculate: bool = False) -> None:
        """Bring every sheet up to date with the Problem's variables, round by round until no
        sheet writes anything more. `recalculate` does every formula again first (a settings
        change: Approximate mode shows `5.`)."""
        if recalculate:
            for page, sheet in self.pages.items():
                _reply(replies, page)["notices"].extend([_notice(n) for n in sheet.recalculate()])
        scope = self.session.scope
        for _ in range(_MAX_ROUNDS):
            before = scope.revision
            for page, sheet in self.pages.items():
                notices = sheet.sync()
                if notices:
                    _reply(replies, page)["notices"].extend([_notice(n) for n in notices])
            if scope.revision == before:
                break
        for page, sheet in self.pages.items():
            # A sheet is in the reply when it was acted on or has changed since it was last
            # reported, whatever changed it (a Calculator store, another sheet).
            if page in replies or sheet.revision != self._reported.get(page):
                reply = _reply(replies, page)
                reply["revision"] = sheet.revision
                self._reported[page] = sheet.revision
                if reply["span"] and self._viewed_at.get(page) != sheet.revision:
                    reply["span"], reply["cells"] = [], []  # the sheet moved on since the view
                self._edits(page, sheet, reply)
        self._relock()

    def _relock(self) -> None:
        """The Problem's locked names are those of all its sheets together, so one sheet
        unlinking a list does not free it while another still holds it."""
        scope = self.session.scope
        scope.lists = set().union(*(sheet.locks[0] for sheet in self.pages.values()))
        scope.read_only = set().union(*(sheet.locks[1] for sheet in self.pages.values()))


def _reply(replies: dict[int, SheetReply], page: int) -> SheetReply:
    if page not in replies:
        replies[page] = {
            "page": page,
            "revision": 0,
            "notices": [],
            "error": None,
            "cells": [],
            "span": [],
            "edits": [],
            "columns": [],
        }
    return replies[page]


def _contents(raw: object) -> dict[Key, Content | None]:
    """Cells as sent, [column, row, kind, text]: `=` text is a formula, "" clears the cell."""
    return {
        (column, row): None if not text else Formula(text) if kind == "formula" else Entry(text)
        for column, row, kind, text in cast("list[list]", raw)
    }


def _notice(notice: Notice) -> NoticePayload:
    return {"title": notice.title, "message": notice.message}


def _structure(sheet: Sheet, action: str, what: str, column: int, row: int) -> list[Notice]:
    if action == "insert":
        if what == "row":
            return actions.insert_row(sheet, row)
        if what == "column":
            return actions.insert_column(sheet, column)
        return actions.insert_cell(sheet, column, row)
    if what == "row":
        return actions.delete_row(sheet, row)
    if what == "column":
        return actions.delete_column(sheet, column)
    return actions.delete_cell(sheet, column, row)


def _restore(sheet: Sheet, args: dict[str, object]) -> list[Notice]:
    """A saved sheet: its cells as typed and its columns' names and formulas."""
    contents = {key: content for key, content in _contents(args["cells"]).items() if content}
    columns = [
        ColumnInfo(name, shown, formula)
        for name, shown, formula in cast("list[list]", args["columns"])
    ]
    columns += [ColumnInfo() for _ in range(COLUMNS - len(columns))]
    return sheet.restore(contents, columns[:COLUMNS])
