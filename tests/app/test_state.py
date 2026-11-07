"""The app state drives the document from keypad and physical keys (FR-DEV-004, FR-DEV-006)."""

from cassim.app.state import AppState, Mode, System


def entry_latex(state: AppState) -> str:
    return state.screen().entry


def test_physical_and_keypad_keys_reach_the_same_page() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.key_event("1")
    state.press_keypad("plus")
    state.press_keypad("2")
    state.key_event("Enter")
    assert [line.text for line in state.screen().lines] == ["1+2", "3"]


def test_keypad_ctrl_is_sticky_for_one_key() -> None:
    state = AppState()
    state.press_keypad("1")
    state.press_keypad("ctrl")
    assert state.pending == "ctrl"
    state.press_keypad("div")
    assert state.pending == ""
    state.press_keypad("3")
    state.press_keypad("enter")
    assert state.screen().lines[0].text == "((1)/(3))"


def test_computer_shortcuts() -> None:
    state = AppState()
    for key in ("1", "Slash", "2"):
        state.key_event(key)
    assert state.screen().entry.count("\frac") == 0  # typed / stays linear
    state.key_event("Enter")
    state.key_event("2")
    state.key_event("Slash", ctrl=True)
    state.key_event("3")
    assert "frac" in entry_latex(state)


def test_shifted_symbols_and_unknown_keys() -> None:
    state = AppState()
    state.key_event("2")
    state.key_event("6", shift=True)  # ^
    state.key_event("3")
    state.key_event("Enter")
    assert state.screen().lines[1].text == "8"
    assert state.key_event("F5") is False
    assert state.key_event("Shift Left") is False


def test_the_computer_keypad_choice_is_kept() -> None:
    system = System(computer_keypad=True)
    assert System.loads(system.dumps()).computer_keypad
    assert not System.loads('{"start_mode": "computer", "math_size": 20}').computer_keypad
