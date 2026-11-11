"""Documents, Problems and Pages (FR-DOC-001, FR-DOC-002, FR-DOC-005).

A document holds Problems; a Problem holds Pages and one variable namespace (a `Session`), so a new
Page keeps the variables and a new Problem starts clean. The document settings apply to every
Problem. Page types other than Calculator have no model yet and are placeholders.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from cassim.core.settings import Settings
from cassim.device.calculator import Calculator
from cassim.device.clipboard import Clipboard
from cassim.device.engine import RemoteSession, local_session

if TYPE_CHECKING:
    from cassim.core.session import Session

MAX_PAGES = 50  # per Problem, as on the emulator (docs/testing/emulator-editor-capture.md)


class PageKind(StrEnum):
    CALCULATOR = "calculator"
    GRAPHS = "graphs"
    SPREADSHEET = "spreadsheet"
    STATISTICS = "statistics"
    NOTES = "notes"
    PROGRAM = "program"
    PYTHON = "python"
    PSEUDOCODE = "pseudocode"


@dataclass
class Page:
    kind: PageKind
    calculator: Calculator | None = None  # the model of a Calculator page


@dataclass
class Problem:
    session: Session | RemoteSession
    clipboard: Clipboard
    pages: list[Page] = field(default_factory=list)

    def new_page(self, kind: PageKind) -> Page:
        calculator = (
            Calculator(self.session, self.clipboard) if kind is PageKind.CALCULATOR else None
        )
        return Page(kind, calculator)


@dataclass(frozen=True)
class _Layout:
    """Which pages sit in which Problems, and where we are (for document undo)."""

    problems: tuple[tuple[Problem, tuple[Page, ...]], ...]
    problem: int
    page: int


class Document:
    """The pages in order, grouped by Problem, and which page is showing."""

    def __init__(
        self,
        name: str = "Untitled",
        settings: Settings | None = None,
        sessions: Callable[[Settings], Session | RemoteSession] = local_session,
    ) -> None:
        self.name = name
        self.sessions = sessions  # makes each Problem's session (a RemoteSession in the browser)
        self.settings = settings if settings is not None else Settings()
        self.clipboard = Clipboard()  # shared by every page, so copy works across them
        self.problems: list[Problem] = []
        self.problem = 0  # the current Problem
        self.page = 0  # the current Page within it
        self._new_problem(PageKind.CALCULATOR)
        self._undo: list[_Layout] = []  # structure only; page contents have their own undo
        self._redo: list[_Layout] = []

    # ---- looking ---------------------------------------------------------------------------

    @property
    def current(self) -> Page:
        return self.problems[self.problem].pages[self.page]

    def sorter(self) -> list[tuple[int, int, PageKind]]:
        """Every page as (problem, page, kind), numbered from 0, for the page sorter."""
        return [
            (p, q, page.kind)
            for p, problem in enumerate(self.problems)
            for q, page in enumerate(problem.pages)
        ]

    def can_add_page(self) -> bool:
        return len(self.problems[self.problem].pages) < MAX_PAGES

    # ---- adding and removing ---------------------------------------------------------------

    def add_problem(self, kind: PageKind = PageKind.CALCULATOR) -> Page:
        """Insert a Problem after the current one, with one page, and go to it."""
        self._remember()
        return self._new_problem(kind)

    def _new_problem(self, kind: PageKind) -> Page:
        problem = Problem(self.sessions(self.settings), self.clipboard)
        index = self.problem + 1 if self.problems else 0
        self.problems.insert(index, problem)
        page = problem.new_page(kind)
        problem.pages.append(page)
        self.problem, self.page = index, 0
        return page

    def add_page(self, kind: PageKind = PageKind.CALCULATOR) -> Page:
        """Insert a page after the current one in the same Problem, and go to it."""
        if not self.can_add_page():
            msg = f"a Problem holds at most {MAX_PAGES} pages"
            raise ValueError(msg)
        self._remember()
        problem = self.problems[self.problem]
        page = problem.new_page(kind)
        self.page += 1
        problem.pages.insert(self.page, page)
        return page

    def delete_page(self) -> None:
        """Remove the current page. Removing the last page of a Problem removes the Problem,
        and a document is never left empty: its last page is replaced by a blank Calculator."""
        self._remember()
        problem = self.problems[self.problem]
        del problem.pages[self.page]
        if problem.pages:
            self.page = min(self.page, len(problem.pages) - 1)
            return
        del self.problems[self.problem]
        if not self.problems:
            self.problem = 0
            self._new_problem(PageKind.CALCULATOR)
            return
        self.problem = min(self.problem, len(self.problems) - 1)
        self.page = min(self.page, len(self.problems[self.problem].pages) - 1)

    def delete_problem(self) -> None:
        self._remember()
        del self.problems[self.problem]
        if not self.problems:
            self._new_problem(PageKind.CALCULATOR)
            return
        self.problem = min(self.problem, len(self.problems) - 1)
        self.page = 0

    # ---- moving ----------------------------------------------------------------------------

    def go(self, problem: int, page: int) -> None:
        if not (
            0 <= problem < len(self.problems) and 0 <= page < len(self.problems[problem].pages)
        ):
            msg = f"no page {problem}.{page}"
            raise IndexError(msg)
        self.problem, self.page = problem, page

    def next_page(self, step: int = 1) -> None:
        """Go forward (or back with a negative step) one page, across Problem boundaries."""
        flat = [(p, q) for p, q, _ in self.sorter()]
        at = flat.index((self.problem, self.page)) + step
        self.problem, self.page = flat[max(0, min(at, len(flat) - 1))]

    def move_page(self, to: int) -> None:
        """Reorder: put the current page at position `to` of its Problem."""
        self._remember()
        pages = self.problems[self.problem].pages
        to = max(0, min(to, len(pages) - 1))
        pages.insert(to, pages.pop(self.page))
        self.page = to

    def move_problem(self, to: int) -> None:
        self._remember()
        to = max(0, min(to, len(self.problems) - 1))
        self.problems.insert(to, self.problems.pop(self.problem))
        self.problem = to

    # ---- undo ------------------------------------------------------------------------------

    def _layout(self) -> _Layout:
        return _Layout(
            tuple((problem, tuple(problem.pages)) for problem in self.problems),
            self.problem,
            self.page,
        )

    def _remember(self) -> None:
        self._undo.append(self._layout())
        self._redo.clear()

    def _restore(self, layout: _Layout) -> None:
        for problem, pages in layout.problems:
            problem.pages[:] = pages
        self.problems[:] = [problem for problem, _ in layout.problems]
        self.problem, self.page = layout.problem, layout.page

    def forget_history(self) -> None:
        """Drop the page-change undo history (after loading a document)."""
        self._undo.clear()
        self._redo.clear()

    def undo(self) -> bool:
        """Undo the last add, delete or move of a page or Problem. False when there is none."""
        return self._step(self._undo, self._redo)

    def redo(self) -> bool:
        return self._step(self._redo, self._undo)

    def _step(self, source: list[_Layout], target: list[_Layout]) -> bool:
        if not source:
            return False
        target.append(self._layout())
        self._restore(source.pop())
        return True

    # ---- settings --------------------------------------------------------------------------

    def use(self, settings: Settings) -> None:
        """Make `settings` the Document Settings of every Problem (the settings dialog)."""
        for problem in self.problems:
            problem.session.settings = settings
        self.settings = settings

    def set(self, **changes: str) -> None:
        """Change Document Settings (angle, display digits, calculation mode...) everywhere."""
        for problem in self.problems:
            problem.session.set(**changes)
        self.settings = self.problems[0].session.settings
