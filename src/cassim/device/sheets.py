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
    from cassim.device.engine import NoticePayload, SheetErrorPayload, SheetOp, SheetReply

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
        self._relock()

    def _act(self, sheet: Sheet, op: SheetOp) -> list[Notice]:  # noqa: PLR0911 (one per action)
        args = op["args"]
        column = cast("int", args.get("column", 0))
        row = cast("int", args.get("row", 0))
        choose = cast("dict[str, str]", args.get("choose", {}))
        match op["action"]:
            case "cell":
                return sheet.set_cell(column, row, cast("str", args["text"]), choose=choose)
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
            case _:  # "view" changes nothing
                return []

    def _view(self, sheet: Sheet, span: Span, reply: SheetReply) -> None:
        """The cells of `span` as drawn, and every column's name and formula. Only the cells
        asked for are formatted (decision 0031, spike B)."""
        reply["cells"] = [
            (column, row, shown.text, shown.right, sheet.text(column, row))
            for column, row in span.cells()
            if (shown := sheet.shown(column, row)).text
        ]
        reply["columns"] = [
            (info.shown_name, info.formula) for info in (sheet.column(c) for c in range(COLUMNS))
        ]

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
                _reply(replies, page)["revision"] = sheet.revision
                self._reported[page] = sheet.revision
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
            "columns": [],
        }
    return replies[page]


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
    contents: dict[Key, Content] = {}
    for column, row, kind, text in cast("list[list]", args["cells"]):
        contents[(column, row)] = Formula(text) if kind == "formula" else Entry(text)
    columns = [
        ColumnInfo(name, shown, formula)
        for name, shown, formula in cast("list[list]", args["columns"])
    ]
    columns += [ColumnInfo() for _ in range(COLUMNS - len(columns))]
    return sheet.restore(contents, columns[:COLUMNS])
