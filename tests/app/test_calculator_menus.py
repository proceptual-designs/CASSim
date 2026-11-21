# Requirements traced here: FR-CALC-005, FR-DEV-008
"""The Calculator's context menus, from emulator check 6, run 5 (emulator-calc6-results.md)."""

from cassim.device.menu import MenuView
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of
from cassim.devices.nspire.ui.state import AppState


def _menu(state: AppState) -> MenuView:
    view = state.screen().menu
    assert view is not None
    return view


def _calculator(state: AppState) -> Calculator:
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    return calculator


def _enter(state: AppState, text: str) -> None:
    for char in text:
        state.key_event(char)
    state.key_event("Enter")


def _items(view: MenuView) -> list[tuple[str, str, bool]]:
    return [(row.key, row.label, row.enabled) for row in view.rows]


def test_the_entry_lines_context_menu() -> None:
    """H3 j: eight items; with nothing selected Cut, Copy and Delete are greyed."""
    state = AppState()
    state.key_event("ContextMenu")
    assert _items(_menu(state)) == [
        ("1", "Clear History", True),
        ("2", "Cut", False),
        ("3", "Copy", False),
        ("4", "Paste", True),
        ("5", "Delete", False),
        ("6", "Select Variable", True),
        ("7", "Symbols…", True),
        ("8", "Math Templates…", True),
    ]
    assert _menu(state).rows[5].submenu


def test_entry_menu_items_act_on_the_selection() -> None:
    state = AppState()
    for char in "12+34":
        state.key_event(char)
    state.key_event("Arrow Left", shift=True)
    state.key_event("Arrow Left", shift=True)
    state.key_event("ContextMenu")
    assert all(enabled for _, _, enabled in _items(_menu(state)))
    state.key_event("2")  # Cut
    assert _calculator(state).editor.linear() == "12+"
    state.key_event("ContextMenu")
    state.key_event("4")  # Paste
    assert _calculator(state).editor.linear() == "12+34"


def test_entry_menu_opens_symbols_templates_and_variables() -> None:
    state = AppState()
    _enter(state, "a:=5")
    state.key_event("ContextMenu")
    state.key_event("7")
    assert _menu(state).title == "Symbols"
    state.key_event("Escape")
    state.key_event("ContextMenu")
    state.key_event("8")
    assert _menu(state).title == "Templates"
    state.key_event("Escape")
    state.key_event("ContextMenu")
    state.key_event("6")
    assert [row.label for row in _menu(state).rows] == ["a"]
    state.key_event("Enter")
    assert _calculator(state).editor.linear() == "a"


def test_the_history_lines_context_menu_and_clear_history() -> None:
    """H3 j, H5 h: Show Warning Info greyed on a line with no triangle; Clear History clears at
    once and keeps the variables."""
    state = AppState()
    _enter(state, "a:=5")
    _enter(state, "2+3")
    state.key_event("ArrowUp")
    state.key_event("ContextMenu")
    assert _items(_menu(state)) == [
        ("1", "Show Warning Info…", False),
        ("2", "Clear History", True),
        ("3", "Copy", True),
        ("4", "Delete", True),
    ]
    state.key_event("4")  # Delete: the pair goes
    calculator = _calculator(state)
    assert [entry.text for entry in calculator.history] == ["a:=5"]
    state.key_event("ContextMenu")
    state.key_event("2")  # Clear History
    assert not calculator.history
    assert state.menu is None
    _enter(state, "a")
    assert calculator.history[-1].result.text == "5"


def test_show_warning_info_from_the_context_menu() -> None:
    state = AppState()
    calculator = _calculator(state)
    calculator.editor.insert_linear("real(3+4*√(-1))")
    state.key_event("Enter")
    state.key_event("ArrowUp")
    state.key_event("ArrowUp")  # the input, beside its triangle
    state.key_event("ContextMenu")
    assert _menu(state).rows[0].enabled
    state.key_event("1")
    screen = state.screen()
    assert screen.error_title == "Warning"
    assert screen.error == calculator.history[-1].result.warnings[0]


def test_actions_clear_history() -> None:
    """Menu, Actions, 5 Clear History works (it was a placeholder)."""
    state = AppState()
    _enter(state, "2+3")
    state.key_event("F2")
    state.key_event("1")
    state.key_event("5")
    assert not _calculator(state).history
