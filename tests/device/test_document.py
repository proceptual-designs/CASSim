"""Documents, Problems and Pages (FR-DOC-001, FR-DOC-002)."""

import pytest

from cassim.device.document import MAX_PAGES, Document, PageKind
from cassim.device.keys import Binding


def type_into(document: Document, text: str) -> None:
    page = document.current.calculator
    assert page is not None
    for char in text:
        page.perform(Binding("insert", char))
    page.perform(Binding("enter"))


def result(document: Document) -> str:
    page = document.current.calculator
    assert page is not None
    return page.history[-1].result.text


def test_new_document_has_one_calculator_page() -> None:
    document = Document()
    assert document.sorter() == [(0, 0, PageKind.CALCULATOR)]


def test_a_new_page_keeps_variables_and_a_new_problem_does_not() -> None:
    """FR-DOC-001: variables belong to the Problem."""
    document = Document()
    type_into(document, "a:=5")
    document.add_page()
    type_into(document, "a+1")
    assert result(document) == "6"
    document.add_problem()
    type_into(document, "a+1")
    assert result(document) == "a+1"


def test_problems_and_pages_insert_after_the_current_one() -> None:
    document = Document()
    document.add_page(PageKind.NOTES)
    document.add_problem()
    document.go(0, 0)
    document.add_page(PageKind.GRAPHS)
    assert [kind for *_, kind in document.sorter()] == [
        PageKind.CALCULATOR,
        PageKind.GRAPHS,
        PageKind.NOTES,
        PageKind.CALCULATOR,
    ]
    assert (document.problem, document.page) == (0, 1)


def test_only_calculator_pages_have_a_model() -> None:
    document = Document()
    assert document.add_page(PageKind.NOTES).calculator is None


def test_page_limit_per_problem() -> None:
    document = Document()
    for _ in range(MAX_PAGES - 1):
        document.add_page()
    assert not document.can_add_page()
    with pytest.raises(ValueError, match="at most"):
        document.add_page()
    document.add_problem()
    assert document.can_add_page()


def test_delete_page_and_problem_never_leave_the_document_empty() -> None:
    document = Document()
    document.add_page(PageKind.NOTES)
    document.delete_page()
    assert document.sorter() == [(0, 0, PageKind.CALCULATOR)]
    document.delete_page()
    assert document.sorter() == [(0, 0, PageKind.CALCULATOR)]
    document.add_problem()
    document.delete_problem()
    assert len(document.problems) == 1


def test_deleting_the_last_page_of_a_problem_removes_the_problem() -> None:
    document = Document()
    document.add_problem()
    document.delete_page()
    assert len(document.problems) == 1
    assert (document.problem, document.page) == (0, 0)


def test_next_page_crosses_problems_and_stops_at_the_ends() -> None:
    document = Document()
    document.add_problem()
    document.next_page(-1)
    assert (document.problem, document.page) == (0, 0)
    document.next_page(-1)
    assert (document.problem, document.page) == (0, 0)
    document.next_page()
    document.next_page()
    assert (document.problem, document.page) == (1, 0)


def test_reorder() -> None:
    document = Document()
    document.add_page(PageKind.NOTES)
    document.add_page(PageKind.GRAPHS)
    document.move_page(0)
    assert next(kind for *_, kind in document.sorter()) is PageKind.GRAPHS
    document.add_problem(PageKind.PROGRAM)
    document.move_problem(0)
    assert document.sorter()[0][2] is PageKind.PROGRAM


def test_document_settings_reach_every_problem() -> None:
    """FR-DOC-002: Document Settings apply to the whole document, including new Problems."""
    document = Document()
    document.add_problem()
    document.set(angle="degree")
    assert all(p.session.settings.angle == "degree" for p in document.problems)
    document.add_problem()
    assert document.problems[-1].session.settings == document.settings


def test_go_rejects_a_missing_page() -> None:
    with pytest.raises(IndexError):
        Document().go(0, 3)
