"""Menus walked from keys: the Doc and Menu trees come from the profile (FR-DEV-001, FR-DEV-007)."""

from cassim.app.state import AppState, Mode
from cassim.device.menu import MenuItem, MenuState


def test_doc_menu_opens_and_lists_rows() -> None:
    state = AppState()
    state.key_event("F4")
    view = state.screen().menu
    assert view is not None
    assert view.title == "Doc"
    assert [(row.key, row.label) for row in view.rows] == [
        ("2", "Page"),
        ("4", "Insert"),
        ("7", "Settings & Status"),
    ]
    assert view.rows[0].selected
    assert view.rows[0].submenu


def test_doc_insert_problem_by_keys() -> None:
    """Doc > 4 Insert > 1 Problem, the route used on the simulator."""
    state = AppState()
    for key in ("F4", "4", "1"):
        state.key_event(key)
    assert state.screen().menu is None
    assert state.screen().title == "2.1"


def test_doc_insert_calculator_adds_a_page_in_the_problem() -> None:
    state = AppState()
    for key in ("F4", "4", "3"):
        state.key_event(key)
    assert state.screen().title == "1.2"


def test_arrows_and_enter_choose() -> None:
    state = AppState()
    state.key_event("F4")
    state.key_event("Arrow Down")  # Insert
    state.key_event("Enter")  # open it
    view = state.screen().menu
    assert view is not None
    assert view.title == "Doc > Insert"
    state.key_event("Enter")  # Problem
    assert state.screen().title == "2.1"


def test_escape_and_left_go_back() -> None:
    state = AppState()
    state.key_event("F4")
    state.key_event("4")
    assert state.screen().menu is not None
    state.key_event("Arrow Left")
    view = state.screen().menu
    assert view is not None
    assert view.title == "Doc"
    state.key_event("Escape")
    assert state.screen().menu is None


def test_menu_swallows_typing() -> None:
    state = AppState()
    state.key_event("F2")
    state.key_event("z")  # no such item
    state.key_event("Escape")
    assert state.document.current.calculator is not None
    assert state.document.current.calculator.editor.linear() == ""


def test_menu_item_types_a_command() -> None:
    state = AppState()
    for key in ("F2", "2", "1"):  # Menu > Algebra > solve
        state.key_event(key)
    assert state.document.current.calculator is not None
    assert state.document.current.calculator.editor.linear() == "solve("


def test_settings_item_asks_for_the_dialog() -> None:
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "7", "2"):
        state.key_event(key)
    assert asked == ["document_settings"]


def test_keypad_doc_and_esc_keys() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("doc")
    assert state.screen().menu is not None
    state.press_keypad("esc")
    assert state.screen().menu is None


def test_selection_wraps_and_explicit_keys_are_reserved() -> None:
    menu = MenuState(
        MenuItem("m", items=(MenuItem("a", "x"), MenuItem("b", "y", key="1"), MenuItem("c", "z")))
    )
    assert menu.keys() == ["2", "1", "3"]
    menu.press("up")
    assert menu.level.index == 2
    assert menu.press("enter") is not None
    assert not menu.open
