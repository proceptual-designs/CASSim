"""Documents, Problems and Pages (FR-DOC-001, FR-DOC-002, FR-DOC-005).

A document holds Problems; a Problem holds Pages and one variable namespace (a `Session`), so a new
Page keeps the variables and a new Problem starts clean. The document settings apply to every
Problem. Page types other than Calculator have no model yet and are placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from cassim.core.session import Session
from cassim.core.settings import Settings
from cassim.device.calculator import Calculator

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
    session: Session
    pages: list[Page] = field(default_factory=list)

    def new_page(self, kind: PageKind) -> Page:
        calculator = Calculator(self.session) if kind is PageKind.CALCULATOR else None
        return Page(kind, calculator)


class Document:
    """The pages in order, grouped by Problem, and which page is showing."""

    def __init__(self, name: str = "Untitled", settings: Settings | None = None) -> None:
        self.name = name
        self.settings = settings if settings is not None else Settings()
        self.problems: list[Problem] = []
        self.problem = 0  # the current Problem
        self.page = 0  # the current Page within it
        self.add_problem()

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
        problem = Problem(Session(self.settings))
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
        problem = self.problems[self.problem]
        page = problem.new_page(kind)
        self.page += 1
        problem.pages.insert(self.page, page)
        return page

    def delete_page(self) -> None:
        """Remove the current page. Removing the last page of a Problem removes the Problem,
        and a document is never left empty: its last page is replaced by a blank Calculator."""
        problem = self.problems[self.problem]
        del problem.pages[self.page]
        if problem.pages:
            self.page = min(self.page, len(problem.pages) - 1)
            return
        del self.problems[self.problem]
        if not self.problems:
            self.problem = 0
            self.add_problem()
            return
        self.problem = min(self.problem, len(self.problems) - 1)
        self.page = min(self.page, len(self.problems[self.problem].pages) - 1)

    def delete_problem(self) -> None:
        del self.problems[self.problem]
        if not self.problems:
            self.add_problem()
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
        pages = self.problems[self.problem].pages
        to = max(0, min(to, len(pages) - 1))
        pages.insert(to, pages.pop(self.page))
        self.page = to

    def move_problem(self, to: int) -> None:
        to = max(0, min(to, len(self.problems) - 1))
        self.problems.insert(to, self.problems.pop(self.problem))
        self.problem = to

    # ---- settings --------------------------------------------------------------------------

    def set(self, **changes: str) -> None:
        """Change Document Settings (angle, display digits, calculation mode...) everywhere."""
        for problem in self.problems:
            problem.session.set(**changes)
        self.settings = self.problems[0].session.settings
