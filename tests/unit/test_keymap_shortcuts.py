# Requirements traced here: FR-DEV-007, FR-DEV-001
"""Every ctrl shortcut with a letter or a digit works from both keyboards: the keypad (ctrl, then
the key) and a computer (one chord). Simon, 2026-11-14: ctrl, I on the keypad did nothing."""

import pytest

from cassim.device.menu import MenuItem
from cassim.devices.nspire.keymap import COMPUTER, HANDHELD
from cassim.devices.nspire.ui.state import AppState


def shortcuts(keymap):
    return {
        k: v for k, v in keymap.items() if k.startswith("ctrl+") and len(k) == 6 and k[-1].isalnum()
    }


def test_both_keyboards_have_the_same_letter_and_digit_shortcuts():
    assert shortcuts(HANDHELD) == shortcuts(COMPUTER)


@pytest.mark.parametrize("key", ["i", "g", "r", "z", "l"])
def test_keypad_ctrl_then_a_letter_works(key):
    assert HANDHELD[f"ctrl+{key}"] == COMPUTER[f"ctrl+{key}"]


def test_keypad_ctrl_i_opens_the_application_list():
    state = AppState()
    state.press_keypad("ctrl")
    state.press_keypad("i")
    assert state.menu is not None
    rows = state.menu.view().rows
    assert [(row.key, row.label) for row in rows][:4] == [
        ("1", "Add Calculator"),
        ("2", "Add Graphs"),
        ("3", "Add Geometry"),
        ("4", "Add Lists & Spreadsheet"),
    ]
    state.press_keypad("4")
    assert state.document.current.kind == "spreadsheet"


def test_keyboard_ctrl_7_reaches_the_first_history_row():
    assert COMPUTER["ctrl+7"].action == "first_line"


@pytest.mark.parametrize(
    ("key", "arg"),
    [("F1", "help"), ("alt+shift+c", "switch_view"), ("alt+shift+h", "switch_view")],
)
def test_app_shortcuts_are_available_while_a_menu_is_open(key: str, arg: str) -> None:
    state = AppState()
    state.cassim_menu = lambda: MenuItem("CASSim")
    shown = []
    state.show_dialog = shown.append
    state.run_action("open_menu", "cassim")
    state.run(COMPUTER[key])
    assert shown == [arg]
    assert state.menu is None
