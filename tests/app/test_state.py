"""The app state drives the document from keypad and physical keys (FR-DEV-004, FR-DEV-006)."""

from cassim.devices.nspire import keymap as nspire
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.state import AppState, Mode, System


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


def test_keypad_ctrl_escape_still_undoes() -> None:
    state = AppState()
    state.press_keypad("1")
    state.press_keypad("ctrl")
    state.press_keypad("esc")
    assert typed(state) == ""


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


def test_computer_column_order_and_widths_are_system_settings() -> None:
    system = System(
        computer_column_order=["keypad", "sidebar", "workspace"],
        computer_sidebar_width=310,
        computer_keypad_width=390,
    )
    saved = System.loads(system.dumps())
    assert saved.computer_column_order == ["keypad", "sidebar", "workspace"]
    assert saved.computer_sidebar_width == 310
    assert saved.computer_keypad_width == 390


def test_older_narrow_sidebar_is_clamped_and_column_controls_persist() -> None:
    old = System.loads('{"start_mode":"computer","math_size":20,"computer_sidebar_width":230}')
    assert old.computer_sidebar_width == 300
    assert not old.computer_column_controls
    old.computer_column_controls = True
    assert System.loads(old.dumps()).computer_column_controls


def test_invalid_computer_column_settings_use_safe_defaults() -> None:
    system = System.loads(
        '{"start_mode":"computer","math_size":20,'
        '"computer_column_order":["sidebar","sidebar","keypad"],'
        '"computer_sidebar_width":9999,"computer_keypad_width":true}'
    )
    assert system.computer_column_order == ["sidebar", "workspace", "keypad"]
    assert system.computer_sidebar_width == 300
    assert system.computer_keypad_width == 320


def test_the_letter_layout_is_a_system_setting() -> None:
    """ABC (as on the CX II) or QWERTY letters; an unknown name falls back to the default."""
    state = AppState()
    assert state.keypad is nspire.KEYPAD
    state.system.letters = "QWERTY"
    assert state.keypad is nspire.KEYPAD_QWERTY
    assert System.loads(state.system.dumps()).letters == "QWERTY"
    state.system.letters = "Dvorak"
    assert state.keypad is nspire.KEYPAD
    assert System.loads('{"start_mode": "computer", "math_size": 20, "letters": 3}').letters == ""


# ---- caps lock: the Caps Lock key and the keypad's ctrl then shift (decision 0024) ----------


def typed(state: AppState) -> str:
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    return calculator.editor.linear()


def test_the_caps_lock_key_turns_typed_letters_into_capitals() -> None:
    state = AppState()
    state.key_event("A")  # no Shift, no lock: a small letter
    state.key_event("Caps Lock")
    assert state.caps
    assert "CAPS" in state.screen().status
    state.key_event("A")  # the browser reports the key, not the case
    state.key_event("n")
    assert typed(state) == "aAN"
    state.key_event("A", shift=True)  # Shift with the lock on gives a small letter
    assert typed(state) == "aANa"
    state.key_event("Caps Lock")
    assert not state.caps
    assert "CAPS" not in state.screen().status


def test_caps_lock_leaves_digits_symbols_and_shortcuts_alone() -> None:
    state = AppState()
    state.key_event("Caps Lock")
    state.key_event("2")
    state.key_event("6", shift=True)  # ^
    state.key_event("3")
    state.key_event("A", ctrl=True)  # select all, not a typed letter
    assert typed(state) == "2^(3)"
    state.key_event("Enter")
    assert state.screen().lines[1].text == "8"


def test_keypad_ctrl_then_shift_is_caps_lock() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("a")
    state.press_keypad("ctrl")
    state.press_keypad("shift")
    assert state.caps
    assert state.pending == ""  # the pair is used up, not left waiting
    state.press_keypad("b")
    state.press_keypad("shift")  # a lone shift is still a modifier for the next key
    assert state.pending == "shift"
    state.press_keypad("c")  # shift then a letter with the lock on: small, as on a PC
    assert typed(state) == "aBc"
    state.press_keypad("ctrl")
    state.press_keypad("shift")
    assert not state.caps


def test_the_physical_and_keypad_locks_are_one_lock() -> None:
    state = AppState()
    state.key_event("Caps Lock")
    state.press_keypad("ctrl")
    state.press_keypad("shift")
    assert not state.caps
