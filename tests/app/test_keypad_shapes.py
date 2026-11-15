# Requirements traced here: FR-DEV-005
"""The keypad's key shapes, legends and outlines (FR-DEV-005)."""

from dataclasses import replace
from typing import Any

import flet as ft
import pytest

from cassim.app.theme import DARK
from cassim.devices.nspire import keymap
from cassim.devices.nspire.ui.keypad import Keypad, key_corners
from cassim.devices.nspire.ui.layout import KEY_GAP, KEY_H, key_span
from cassim.devices.nspire.ui.state import AppState


def keys_named(keypad: Keypad, name: str) -> list[Any]:
    """The drawn controls of every key piece called `name`, in order."""
    found = []
    for drawn_row, row in zip(keypad.control.controls, keypad.state.keypad, strict=True):
        for control, key in zip(drawn_row.controls, row, strict=True):  # ty: ignore[unresolved-attribute]
            if key.name == name:
                found.append((key, control))
    return found


def texts_of(control: Any) -> list[str]:
    """Every text drawn in `control`, spans joined."""
    found = []
    stack = [control]
    while stack:
        item = stack.pop()
        if isinstance(item, ft.Text):
            found.append(item.value or "".join(span.text or "" for span in item.spans or []))
        for name in ("content", "controls"):
            inner = getattr(item, name, None)
            stack.extend(inner if isinstance(inner, list) else [inner] if inner else [])
    return found


def test_every_row_of_the_letter_block_is_the_same_width():
    for layout in keymap.KEYPADS.values():
        widths = {round(sum(key.width for key in row), 9) for row in layout[-4:]}
        assert len(widths) == 1


def test_space_and_a_symmetric_l_shaped_return_fill_the_corner():
    last = keymap.KEYPAD[-1]
    space, foot = last[-2], last[-1]
    assert (space.name, foot.name, foot.join) == ("space", "return", "up")
    assert space.width + foot.width == pytest.approx(keymap._ALPHA * 3)
    top = keymap.KEYPAD[-2][-1]
    assert (top.name, top.join) == ("return", "down")
    # Simon, 2026-11-14: a symmetric L, the foot as long as the upright is tall (within a pixel)
    upright = key_span(foot.height, KEY_H) + KEY_GAP + key_span(top.height, KEY_H)
    assert key_span(foot.width) == pytest.approx(upright, abs=1)
    assert foot.width > top.width  # still an L: the foot reaches left of the upright
    # the pieces line up at the right edge: both rows end there
    assert sum(k.width for k in keymap.KEYPAD[-2]) == pytest.approx(sum(k.width for k in last))


def test_the_return_pieces_are_drawn_as_one_l_with_the_symbol_in_the_foot():
    state = AppState()
    keypad = Keypad(state, lambda _: None)
    (top_key, top), (foot_key, foot) = keys_named(keypad, "return")
    # the short tab sits at the foot of its row, in a box as tall as the row
    row_height = state.kpx(key_span(keymap._LETTER_H, KEY_H))
    assert top.height == pytest.approx(row_height)
    assert top.alignment == ft.Alignment.BOTTOM_CENTER
    stack = top.content
    assert isinstance(stack, ft.Stack)  # the piece and the seam that fills the gap below it
    piece, seam = stack.controls
    assert piece.height == pytest.approx(state.kpx(key_span(keymap._RETURN_TAB, KEY_H)))
    assert piece.height < row_height / 2  # Simon, 2026-11-14: a small key, not enter
    assert seam.top == piece.height - 1  # overlaps by a pixel, so no hairline shows
    assert seam.height == pytest.approx(state.kpx(KEY_GAP) + 2)
    assert seam.bgcolor == piece.bgcolor
    assert key_corners(top_key, 7) == ft.BorderRadius(7, 7, 0, 0)
    assert key_corners(foot_key, 7) == ft.BorderRadius(7, 0, 7, 7)  # square where they meet
    assert foot.width == pytest.approx(state.kpx(key_span(foot_key.width)))
    assert texts_of(top) == [""]
    assert texts_of(foot) == ["⏎"]  # Simon, 2026-11-14: in the foot, where the arrow points


def test_both_pieces_press_return():
    pressed: list[str] = []
    keypad = Keypad(AppState(), pressed.append)
    (_, top), (_, foot) = keys_named(keypad, "return")
    top.content.controls[0].on_click(None)
    foot.on_click(None)
    assert pressed == ["return", "return"]


def test_the_accent_key_shows_a_flag():
    keypad = Keypad(AppState(), lambda _: None)
    ((key, control),) = keys_named(keypad, "accent")
    (icon,) = control.content.controls
    assert icon.icon == ft.Icons.FLAG  # for now: PLAN.md section 12, row A9
    assert key.label == keymap.ACCENT_LABEL
    assert keymap.HANDHELD["accent"].action == "accent"


def test_menu_key_shows_context_menu_legend_and_pending_layer():
    state = AppState()
    keypad = Keypad(state, lambda _: None)
    ((key, control),) = keys_named(keypad, "menu")
    labels, main = control.content.controls
    icon = labels.controls[0]
    assert key.ctrl == "context menu"
    assert control.tooltip == "ctrl: context menu"
    assert main.value == "menu"
    assert len(icon.shapes) == 4
    assert all(shape.paint.color == DARK.ctrl_label_light for shape in icon.shapes)
    assert keymap.HANDHELD["ctrl+menu"].action == "context_menu"

    state.press_keypad("ctrl")
    keypad.refresh()
    ((_, control),) = keys_named(keypad, "menu")
    labels, main = control.content.controls
    assert len(main.shapes) == 4
    assert all(shape.paint.color == DARK.key_colours(key.style)[1] for shape in main.shapes)


def test_shift_has_an_orange_ring_and_x_y_z_and_enter_have_a_green_ring():
    keypad = Keypad(AppState(), lambda _: None)
    ((_, shift),) = keys_named(keypad, "shift")
    assert shift.border == ft.Border.all(keypad.state.kpx(2), DARK.shift_outline)
    for name in ("x", "y", "z", "enter"):
        ((key, control),) = keys_named(keypad, name)
        assert key.outline
        assert control.border == ft.Border.all(keypad.state.kpx(2), DARK.key_outline)
    for name in "aw":
        ((key, control),) = keys_named(keypad, name)
        assert not key.outline
        assert control.border is None
    for name in "axz":
        ((_, control),) = keys_named(keypad, name)
        (label,) = control.content.controls
        assert label.weight == ft.FontWeight.W_600


def test_key_outlines_follow_theme_colours():
    theme = replace(DARK, shift_outline="#aa5500", key_outline="#116633")
    keypad = Keypad(AppState(), lambda _: None, theme)
    for name, colour in (("shift", theme.shift_outline), ("x", theme.key_outline)):
        ((_, control),) = keys_named(keypad, name)
        assert control.border == ft.Border.all(keypad.state.kpx(2), colour)


@pytest.mark.parametrize(
    ("modifier", "expected"),
    [
        ("plain", "a"),
        ("shift", "A"),
        ("caps", "A"),
        ("shift+caps", "a"),
    ],
)
def test_letter_key_shows_its_effective_case(modifier: str, expected: str) -> None:
    state = AppState()
    if "shift" in modifier:
        state.press_keypad("shift")
    if "caps" in modifier:
        state.caps = True
    keypad = Keypad(state, lambda _: None)
    ((_, control),) = keys_named(keypad, "a")
    assert texts_of(control) == [expected]
