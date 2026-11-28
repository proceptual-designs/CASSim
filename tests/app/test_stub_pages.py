# Requirements traced here: FR-DOC-001, FR-DEV-007
"""Graph and Notes page behavior (FR-DOC-001, FR-DEV-007)."""

import pytest

from cassim.app.shell import BrowserOffers
from cassim.device.menu import MenuItem
from cassim.devices.nspire.document import PageKind, loads
from cassim.devices.nspire.screen import thumbnail
from cassim.devices.nspire.ui.app import cassim_items, nspire_menu
from cassim.devices.nspire.ui.sidebar import Sidebar
from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.views import STUB_NOTICE, CalculatorView
from cassim.doc.serialize import dumps

STUBS = [
    ("8", PageKind.NOTES, "Notes"),
]


def insert(state: AppState, key: str) -> None:
    """Doc > Insert > the item numbered `key`, as on the handheld."""
    state.key_event("F4")
    state.key_event("4")
    state.key_event(key)


def texts(control: object) -> list[str]:
    """Every text value under a Flet control."""
    found: list[str] = []
    value = getattr(control, "value", None)
    if isinstance(value, str):
        found.append(value)
    for name in ("content", "controls"):
        inner = getattr(control, name, None)
        for child in inner if isinstance(inner, list) else [inner]:
            if child is not None:
                found.extend(texts(child))
    return found


@pytest.mark.parametrize(("key", "kind", "name"), STUBS)
def test_doc_insert_adds_the_page_with_the_device_name(key: str, kind: PageKind, name: str) -> None:
    state = AppState()
    insert(state, key)
    assert state.document.current.kind is kind
    screen = state.screen()
    assert screen.title == "1.2"
    assert screen.stub == name
    assert screen.lines == ()


def test_a_calculator_page_is_not_a_stub() -> None:
    assert AppState().screen().stub is None


def test_a_graphs_page_has_an_active_model_not_a_stub() -> None:
    state = AppState()
    insert(state, "4")
    screen = state.screen()
    assert screen.graphs
    assert screen.stub is None


@pytest.mark.parametrize(("key", "kind", "name"), STUBS)
def test_the_view_says_the_page_is_still_to_be_built(key: str, kind: PageKind, name: str) -> None:
    state = AppState()
    insert(state, key)
    assert state.document.current.kind is kind
    view = CalculatorView(state)
    view.refresh()
    shown = texts(view.history)
    assert name in shown
    assert STUB_NOTICE in shown
    state.run_action("prev_page")  # and the Calculator page is drawn as before
    view.refresh()
    assert STUB_NOTICE not in texts(view.history)


def test_typing_on_a_stub_page_does_nothing_and_it_has_no_menu() -> None:
    state = AppState()
    insert(state, "8")
    for char in "2+3":
        state.key_event(char)
    state.key_event("Enter")
    state.key_event("F2")  # the Calculator's menu does not belong to this page
    assert state.menu is None
    state.key_event("F4")  # Doc still opens, so the page can be deleted or another added
    assert state.menu is not None


@pytest.mark.parametrize(("index", "dialog"), [(-1, "about"), (-2, "help")])
@pytest.mark.parametrize("page", ["calculator", "4", "6", "7", "8"])
def test_about_and_help_are_in_cassim_on_every_page(page: str, index: int, dialog: str) -> None:
    """NFR-LEG-002: About and Help are available on every page type."""
    state = AppState()
    state.cassim_menu = lambda: MenuItem(
        "CASSim", items=cassim_items(BrowserOffers(), nspire_menu(view=Mode.HANDHELD))
    )
    asked: list[str] = []
    state.show_dialog = asked.append
    if page != "calculator":
        insert(state, page)
    state.run_action("open_menu", "cassim")
    assert state.menu is not None
    state.key_event(state.menu.keys()[index])
    assert asked == [dialog]


def test_the_sidebar_and_sorter_use_the_device_name() -> None:
    state = AppState()
    insert(state, "6")
    sidebar = Sidebar(state, lambda: None)
    sidebar.refresh()
    assert "1.2  Lists & Spreadsheet" in texts(sidebar.control)
    lines = thumbnail(state.document.current, names=state.profile.pages)
    assert lines[0] == "Lists & Spreadsheet"


def test_graph_and_stub_pages_survive_save_and_load() -> None:
    """FR-DOC-003: a saved document keeps its page types, in order."""
    state = AppState()
    for char in "2+3":
        state.key_event(char)
    state.key_event("Enter")
    insert(state, "4")
    insert(state, "8")
    kinds = [kind for _, _, kind in loads(dumps(state.document)).sorter()]
    assert kinds == [PageKind.CALCULATOR, PageKind.GRAPHS, PageKind.NOTES]


def test_undo_on_a_stub_page_takes_it_away_and_redo_brings_it_back() -> None:
    state = AppState()
    insert(state, "7")
    state.key_event("z", ctrl=True)
    assert [kind for _, _, kind in state.document.sorter()] == [PageKind.CALCULATOR]
    state.key_event("y", ctrl=True)
    assert state.document.current.kind is PageKind.STATISTICS
