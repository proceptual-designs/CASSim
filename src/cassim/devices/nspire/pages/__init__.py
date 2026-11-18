"""The Nspire's page types (FR-PROF-006).

The Calculator and Lists & Spreadsheet pages have models. The others are registered with their
names, so the menus can add them and a file can hold them, and they show as not built yet.

A saved Calculator page holds the entries as typed (the editor's nodes, so templates survive), not
their results: loading replays them in order through the engine.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from cassim.device.editor import Node
from cassim.device.keys import Binding
from cassim.devices.nspire.editor_storage import dump_nodes, load_nodes
from cassim.devices.nspire.pages import spreadsheet
from cassim.devices.nspire.pages.calculator import Calculator
from cassim.devices.nspire.pages.spreadsheet import Spreadsheet
from cassim.devices.nspire.pages.statistics import (
    Statistics,
    dump_statistics,
    load_statistics,
    new_statistics,
)
from cassim.doc.document import PageType, PageTypes

if TYPE_CHECKING:
    from collections.abc import Generator

    from cassim.doc.document import Problem

DEVICE = "nspire"


class PageKind(StrEnum):
    CALCULATOR = "calculator"
    GRAPHS = "graphs"
    SPREADSHEET = "spreadsheet"
    STATISTICS = "statistics"
    NOTES = "notes"
    PROGRAM = "program"
    PYTHON = "python"
    PSEUDOCODE = "pseudocode"


# ---- the Calculator page ------------------------------------------------------------------------


def _new_calculator(problem: Problem) -> Calculator:
    return Calculator(problem.session, problem.clipboard)


def _dump_entry(nodes: tuple[Node, ...], *, approximate: bool) -> str | list[Any] | dict[str, Any]:
    """An entry as typed: its row alone, or `{"nodes": row, "approximate": true}` for one
    entered with ctrl+enter."""
    row = dump_nodes(nodes)
    return {"nodes": row, "approximate": True} if approximate else row


def _dump_calculator(calculator: Calculator) -> dict[str, Any]:
    return {
        "entries": [
            _dump_entry(entry.source or entry.nodes, approximate=entry.approximate)
            for entry in calculator.history
        ],
        "entry": dump_nodes(calculator.editor.root),
    }


def _load_calculator(
    page_type: PageType, problem: Problem, data: dict[str, Any]
) -> Generator[Calculator, None, Calculator]:
    calculator = _new_calculator(problem)
    for saved in data.get("entries", []):
        # schema 2: an exact entry is only its row
        entry = saved if isinstance(saved, dict) else {"nodes": saved}
        calculator.editor.clear()
        calculator.editor.root = load_nodes(entry["nodes"])
        calculator.editor.pos = len(calculator.editor.root)
        calculator.perform(Binding("approximate" if entry.get("approximate") else "enter"))
        if calculator.pending is not None:
            yield calculator
        calculator.error = None  # an entry that fails now was kept as typed; drop its dialog
    calculator.editor.clear()
    calculator.editor.root = load_nodes(data.get("entry", []))
    calculator.editor.pos = len(calculator.editor.root)
    calculator.forget_undo()  # loading is not something to undo
    return calculator


# ---- the Lists & Spreadsheet page ---------------------------------------------------------------


def _new_sheet(problem: Problem) -> Spreadsheet:
    sheet = Spreadsheet(problem.session, problem.clipboard)
    sheet.link.alive(sheet.id)
    return sheet


def _load_sheet(
    page_type: PageType, problem: Problem, data: dict[str, Any]
) -> Generator[Spreadsheet, None, Spreadsheet]:
    yield from ()
    return spreadsheet.load(Spreadsheet(problem.session, problem.clipboard), data)


def _after_sheet(sheet: Spreadsheet) -> None:
    sheet.loaded()


def _load_statistics(
    page_type: PageType, problem: Problem, data: dict[str, Any]
) -> Generator[Statistics, None, Statistics]:
    yield from ()
    return load_statistics(new_statistics(problem), data)


PAGES = PageTypes(
    DEVICE,
    (
        PageType(
            PageKind.CALCULATOR, "Calculator", _new_calculator, _dump_calculator, _load_calculator
        ),
        PageType(PageKind.GRAPHS, "Graphs"),
        PageType(
            PageKind.SPREADSHEET,
            "Lists & Spreadsheet",
            _new_sheet,
            spreadsheet.dump,
            _load_sheet,
            _after_sheet,
        ),
        PageType(
            PageKind.STATISTICS,
            "Data & Statistics",
            new_statistics,
            dump_statistics,
            _load_statistics,
        ),
        PageType(PageKind.NOTES, "Notes"),
        PageType(PageKind.PROGRAM, "Program Editor"),
        PageType(PageKind.PYTHON, "Python"),
        PageType(PageKind.PSEUDOCODE, "Pseudocode"),
    ),
)
