"""The screen buffer (FR-DEV-001): what a Calculator page shows, as data a GUI can draw.

It holds LaTeX and plain text only; the GUI decides fonts, sizes and layout.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from cassim.device.document import Document, Page
from cassim.device.menu import MenuView


@dataclass(frozen=True)
class Line:
    kind: Literal["entry", "result"]
    latex: str
    text: str
    selected: bool = False  # Up has picked this row for recall
    part: bool = False  # the LaTeX draws its own cursor and selection (the row was moved into)


@dataclass(frozen=True)
class Screen:
    title: str  # "1.1" (problem.page)
    status: str
    lines: tuple[Line, ...]
    entry: str  # LaTeX of the entry line, cursor drawn
    error: str | None
    menu: MenuView | None = None  # drawn over the page while a menu is open
    # The page type's name when the page has no model yet (Graphs, Notes...): the GUI shows a
    # notice instead of an entry line. None on a page that works.
    stub: str | None = None


def page_name(page: Page, names: Mapping[str, str] | None = None) -> str:
    """What the device calls this page's type (`names` comes from the profile)."""
    return (names or {}).get(page.kind.value, page.kind.value)


def thumbnail(page: Page, rows: int = 3, names: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """The last few lines of a page as plain text, for the page sorter."""
    if page.calculator is None:
        return (page_name(page, names), "(not built yet)")
    lines = [
        text
        for entry in page.calculator.history[-rows:]
        for text in (entry.text, entry.result.text)
    ]
    return tuple(lines[-rows:])


def render(
    document: Document,
    status: str = "",
    menu: MenuView | None = None,
    names: Mapping[str, str] | None = None,
) -> Screen:
    """Describe the current page. A page without a model is a stub: only its type's name."""
    title = f"{document.problem + 1}.{document.page + 1}"
    page = document.current.calculator
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
            lines.append(Line(kind, latex or rf"\text{{{text}}}", text, picked, bool(part)))
    return Screen(
        title,
        status,
        tuple(lines),
        page.editor.latex(is_defined=page.session.is_defined),
        page.error,
        menu,
    )
