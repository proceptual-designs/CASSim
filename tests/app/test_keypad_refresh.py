# Requirements traced here: FR-DEV-005
"""The keypad is rebuilt only when its look changes: a rebuild of ~40 controls on every key press
made a phone feel slow (about 70 ms of building and 200 ms of diffing, measured at 4x throttle)."""

from cassim.app.state import AppState
from cassim.app.ui import Keypad


def test_keypad_is_not_rebuilt_for_an_unchanged_look() -> None:
    state = AppState()
    keypad = Keypad(state, lambda _: None)
    first = keypad.control.controls
    keypad.refresh()
    assert keypad.control.controls is first  # same objects, so Flet has nothing to diff


def test_keypad_is_rebuilt_when_the_modifier_or_scale_changes() -> None:
    state = AppState()
    keypad = Keypad(state, lambda _: None)
    first = keypad.control.controls
    state.press_keypad("shift")
    keypad.refresh()
    second = keypad.control.controls
    assert second is not first  # the shift layer's labels are drawn
    state.pad_scale *= 0.5
    keypad.refresh()
    assert keypad.control.controls is not second
