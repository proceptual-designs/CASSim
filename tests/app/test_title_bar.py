"""The page number and document name sit together to leave the title-bar centre clear."""

import flet as ft

from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.views import CalculatorView


def test_page_number_and_document_name_are_grouped_before_the_clear_centre() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.doc_title = "*Week 1"
    view = CalculatorView(state)
    view.refresh()

    column = view.control.content
    assert isinstance(column, ft.Column)
    title_bar = column.controls[0]
    assert isinstance(title_bar, ft.Container)
    row = title_bar.content
    assert isinstance(row, ft.Row)
    page_number, doc_box, spacer, status = row.controls

    assert isinstance(page_number, ft.Container)
    assert page_number.content is view.title
    assert doc_box is view.doc_box
    assert view.doc_box.content is view.doc_name
    assert view.doc_name.value == "Week 1*"
    assert view.doc_name.overflow == ft.TextOverflow.ELLIPSIS
    assert spacer.expand is True
    assert status is view.status
    assert view.doc_box.width == state.px(105)


def test_unsaved_marker_is_appended_to_the_displayed_filename() -> None:
    state = AppState(mode=Mode.HANDHELD)
    view = CalculatorView(state)
    view.set_doc_title("Week 1")
    name = view.doc_name

    view.set_doc_title("*Week 1")

    assert view.doc_name is name
    assert view.doc_name.value == "Week 1*"

    view.set_doc_title("Week 1")
    assert view.doc_name.value == "Week 1"
