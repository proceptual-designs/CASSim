# Requirements traced here: FR-DEV-005
"""The letter block's corner: an L-shaped return key and a wider space key share it equally; the
accent key sits where the handheld has its flag key; x, y and z are bold."""

from typing import Any

import flet as ft
import pytest

from cassim.devices.nspire import keymap
from cassim.devices.nspire.ui.layout import KEY_GAP, key_span
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import Keypad, key_corners, key_weight


def keys_named(keypad: Keypad, name: str) -> list[Any]:
    """The drawn controls of every key piece called `name`, in order."""
    found = []
    for drawn_row, row in zip(keypad.control.controls, keypad.state.keypad, strict=True):
        for control, key in zip(drawn_row.controls, row, strict=True):  # ty: ignore[unresolved-attribute]
            if key.name == name:
                found.append((key, control))
    return found


def test_every_row_of_the_letter_block_is_the_same_width():
    for layout in keymap.KEYPADS.values():
        widths = {round(sum(key.width for key in row), 9) for row in layout[-4:]}
        assert len(widths) == 1


def test_space_and_the_return_foot_share_the_corner_equally():
    last = keymap.KEYPAD[-1]
    space, foot = last[-2], last[-1]
    assert (space.name, foot.name, foot.join) == ("space", "return", "up")
    assert space.width == foot.width == pytest.approx(keymap._ALPHA * 1.5)
    top = keymap.KEYPAD[-2][-1]
    assert (top.name, top.join) == ("return", "down")
    # the pieces line up at the right edge: both rows end there
    assert sum(k.width for k in keymap.KEYPAD[-2]) == pytest.approx(sum(k.width for k in last))


def test_the_return_pieces_are_drawn_as_one_l():
    state = AppState()
    keypad = Keypad(state, lambda _: None)
    (top_key, top), (foot_key, foot) = keys_named(keypad, "return")
    assert isinstance(top, ft.Stack)  # the piece and the seam that fills the gap below it
    piece, seam = top.controls
    assert seam.top == piece.height - 1  # overlaps by a pixel, so no hairline shows
    assert seam.height == pytest.approx(state.kpx(KEY_GAP) + 2)
    assert seam.bgcolor == piece.bgcolor
    assert key_corners(top_key, 7) == ft.BorderRadius(7, 7, 0, 0)
    assert key_corners(foot_key, 7) == ft.BorderRadius(7, 0, 7, 7)  # square where they meet
    assert foot.width == pytest.approx(state.kpx(key_span(foot_key.width)))


def test_both_pieces_press_return():
    pressed: list[str] = []
    keypad = Keypad(AppState(), pressed.append)
    (_, top), (_, foot) = keys_named(keypad, "return")
    top.controls[0].on_click(None)
    foot.on_click(None)
    assert pressed == ["return", "return"]


def test_x_y_and_z_are_bold_and_the_accent_key_is_drawn():
    keypad = Keypad(AppState(), lambda _: None)
    for name in "xyz":
        ((key, _),) = keys_named(keypad, name)
        assert key.bold
    assert key_weight(key) == ft.FontWeight.BOLD
    ((key, _),) = keys_named(keypad, "a")
    assert not key.bold
    assert key_weight(key) == ft.FontWeight.W_400  # the rest of the letters are regular
    ((key, _),) = keys_named(keypad, "accent")
    assert key.label == keymap.ACCENT_LABEL
    assert keymap.HANDHELD["accent"].action == "accent"
