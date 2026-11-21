"""The screen buffer (FR-DEV-001): what a Calculator page shows, as data a GUI can draw.

It holds LaTeX and plain text only; the GUI decides fonts, sizes and layout.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from cassim.device.menu import MenuView
from cassim.devices.nspire.pages.calculator import calculator_of, calculator_on
from cassim.devices.nspire.pages.graphs import graphs_of
from cassim.devices.nspire.pages.spreadsheet import SheetScreen, spreadsheet_of
from cassim.doc.document import Document, Page


@dataclass(frozen=True)
class Line:
    kind: Literal["entry", "result"]
    latex: str
    text: str
    selected: bool = False  # Up has picked this row for recall
    part: bool = False  # the LaTeX draws its own cursor and selection (the row was moved into)
    warnings: tuple[str, ...] = ()  # an entry row's warning triangle (FR-CALC-007)
    error: bool = False  # error result text is drawn as ordinary text to keep ASCII quotes straight


@dataclass(frozen=True)
class Tile:
    """One page in the page sorter."""

    problem: int  # numbered from 0
    page: int
    lines: tuple[str, ...]  # its thumbnail
    current: bool  # the highlighted page: Enter opens it, Delete removes it


@dataclass(frozen=True)
class Screen:
    title: str  # "1.1" (problem.page)
    status: str
    lines: tuple[Line, ...]
    entry: str  # LaTeX of the entry line, cursor drawn
    error: str | None
    menu: MenuView | None = None  # drawn over the page while a menu is open
    # The page type's name when the page has no model yet (Notes...): the GUI shows a
    # notice instead of an entry line. None on a page that works.
    stub: str | None = None
    # The page sorter, drawn on the screen in place of the page: a row of tiles per Problem.
    sorter: tuple[tuple[Tile, ...], ...] | None = None
    sheet: SheetScreen | None = None  # a Lists & Spreadsheet page
    graphs: bool = False  # a Graphs page with its own view
    error_title: str = "Error"  # the dialog's title ("Warning" for Show Warning Info)


def page_name(page: Page, names: Mapping[str, str] | None = None) -> str:
    """What the device calls this page's type (`names` comes from the profile)."""
    return (names or {}).get(str(page.kind), str(page.kind))


def thumbnail(page: Page, rows: int = 3, names: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """The last few lines of a page as plain text, for the page sorter."""
    sheet = spreadsheet_of(page)
    if sheet is not None:
        return (page_name(page, names), f"{len(sheet.cells)} cells")
    graphs = graphs_of(page)
    if graphs is not None:
        functions = (
            f"{item.name}(x)={item.expression}" for item in graphs.functions if item.expression
        )
        return (page_name(page, names), *functions)
    if calculator_of(page) is None:
        return (page_name(page, names), "(not built yet)")
    lines = [
        text
        for entry in calculator_on(page).history[-rows:]
        for text in (entry.text, entry.result.text)
    ]
    return tuple(lines[-rows:])


def sorter_tiles(
    document: Document, names: Mapping[str, str] | None = None
) -> tuple[tuple[Tile, ...], ...]:
    """Every page as a tile, a row per Problem; the current page is highlighted."""
    here = (document.problem, document.page)
    return tuple(
        tuple(
            Tile(p, q, thumbnail(page, names=names), (p, q) == here)
            for q, page in enumerate(problem.pages)
        )
        for p, problem in enumerate(document.problems)
    )


def render(
    document: Document,
    status: str = "",
    menu: MenuView | None = None,
    names: Mapping[str, str] | None = None,
    *,
    sorter: bool = False,
) -> Screen:
    """Describe the current page, or the page sorter over it. A page without a model is a stub:
    only its type's name."""
    title = f"{document.problem + 1}.{document.page + 1}"
    if sorter:
        return Screen(title, status, (), "", None, menu, sorter=sorter_tiles(document, names))
    sheet = spreadsheet_of(document.current)
    if sheet is not None:
        return Screen(title, status, (), "", None, menu, sheet=sheet.screen())
    if graphs_of(document.current) is not None:
        return Screen(title, status, (), "", None, menu, graphs=True)
    page = calculator_of(document.current)
    if page is None:
        return Screen(title, status, (), "", None, menu, page_name(document.current, names))
    lines: list[Line] = []
    for index, entry in enumerate(page.history):
        for kind in ("entry", "result"):
            picked = page.recall == (index, kind)
            latex = entry.latex if kind == "entry" else entry.result.latex
            text = entry.text if kind == "entry" else entry.result.text
            editor = page.recall_editor
            part = picked and page.recall_touched and editor is not None
            if part and editor is not None:  # drawn from its editor: its cursor and selection show
                latex = editor.latex(is_defined=page.session.is_defined)
            warnings = entry.result.warnings if kind == "entry" else ()
            shown = latex or rf"\text{{{text}}}"
            lines.append(
                Line(
                    kind,
                    shown,
                    text,
                    picked,
                    bool(part),
                    warnings,
                    kind == "result" and entry.result.error is not None,
                )
            )
    return Screen(
        title,
        status,
        tuple(lines),
        page.editor.latex(is_defined=page.session.is_defined),
        page.error,
        menu,
        error_title=page.error_title,
    )
