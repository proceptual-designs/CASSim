"""The screen buffer (FR-DEV-001): what a Calculator page shows, as data a GUI can draw.

It holds LaTeX and plain text only; the GUI decides fonts, sizes and layout.
"""

from __future__ import annotations

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


@dataclass(frozen=True)
class Screen:
    title: str  # "1.1" (problem.page)
    status: str
    lines: tuple[Line, ...]
    entry: str  # LaTeX of the entry line, cursor drawn
    error: str | None
    menu: MenuView | None = None  # drawn over the page while a menu is open


def thumbnail(page: Page, rows: int = 3) -> tuple[str, ...]:
    """The last few lines of a page as plain text, for the page sorter."""
    if page.calculator is None:
        return (page.kind.value,)
    lines = [
        text
        for entry in page.calculator.history[-rows:]
        for text in (entry.text, entry.result.text)
    ]
    return tuple(lines[-rows:])


def render(document: Document, status: str = "", menu: MenuView | None = None) -> Screen:
    """Describe the current page. A page without a model shows an empty screen."""
    title = f"{document.problem + 1}.{document.page + 1}"
    page = document.current.calculator
    if page is None:
        return Screen(title, status, (), "", None, menu)
    lines: list[Line] = []
    for index, entry in enumerate(page.history):
        lines.append(Line("entry", entry.latex, entry.text, page.recall == (index, "entry")))
        result = entry.result.latex or f"\text{{{entry.result.text}}}"
        lines.append(Line("result", result, entry.result.text, page.recall == (index, "result")))
    return Screen(
        title,
        status,
        tuple(lines),
        page.editor.latex(is_function=page.session.is_function),
        page.error,
        menu,
    )
