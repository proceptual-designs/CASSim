# Requirements traced here: FR-DEV-005
"""The keypad's centre key steers a pointer on the screen: the arrow shows while it moves, hides
after a second, and a tap with it showing clicks where it is (on the sheet so far)."""

import asyncio
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest
from tests.app.test_splitter_drag import handheld_app

from cassim.device import pointer as pointer_module
from cassim.devices.nspire.sheet_scene import FORMULA, HEAD, ROW, ROW_LABELS
from cassim.devices.nspire.ui import app as app_module
from cassim.devices.nspire.ui.layout import key_span
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import STICK_KEY, Keypad


def find_stick(keypad: Keypad) -> Any:
    """The centre key's gesture detector."""
    for row in keypad.control.controls:
        for key in row.controls:  # ty: ignore[unresolved-attribute]
            if isinstance(key, ft.GestureDetector):
                return key
    raise AssertionError("no joystick key")


def panels(app: Any) -> int:
    menu = app.state.screen().menu
    return 0 if menu is None else len(menu.panels)


def test_the_centre_key_reports_its_travel_in_key_widths():
    heard: list[tuple[str, float, float]] = []
    keypad = Keypad(AppState(), lambda _: None, on_stick=lambda *a: heard.append(a))
    stick = find_stick(keypad)
    width = keypad.state.kpx(key_span(1.0))
    stick.on_pan_down(SimpleNamespace(local_position=ft.Offset(10, 10)))
    stick.on_pan_start(None)
    stick.on_pan_update(SimpleNamespace(local_position=ft.Offset(10 + width / 2, 10)))
    stick.on_pan_end(None)
    stick.on_tap(None)
    assert [event for event, *_ in heard] == ["start", "move", "end", "tap"]
    assert heard[1][1] == pytest.approx(0.5)  # half a key width
    assert heard[1][2] == 0


def test_without_a_handler_the_centre_key_is_a_plain_button():
    pressed: list[str] = []
    keypad = Keypad(AppState(), pressed.append)
    with pytest.raises(AssertionError):
        find_stick(keypad)


def test_a_tap_with_the_pointer_hidden_is_the_usual_select():
    app, _ = handheld_app()
    app.act("open_menu", "menu")
    assert panels(app) == 1
    app.on_stick("tap", 0, 0)
    assert panels(app) == 2  # the highlighted row opened its submenu, as the key always did


def test_moving_shows_the_arrow_and_it_hides_after_it_stops(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app_module, "POINTER_TICK", 0.005)
    monkeypatch.setattr(pointer_module, "HIDE", 0.05)
    app, page = handheld_app()
    mark = app.view.pointer
    app.on_stick("start", 0, 0)
    assert mark.visible
    start = (mark.left, mark.top)
    app.on_stick("move", 1.0, 0)
    steer = page.tasks.pop()

    async def run() -> None:
        task = asyncio.ensure_future(steer)
        await asyncio.sleep(0.05)
        assert isinstance(mark.left, float)
        assert isinstance(start[0], float)
        assert mark.left > start[0]  # it moved right
        assert mark.top == start[1]
        app.on_stick("end", 0, 0)
        await asyncio.wait_for(task, 2)

    asyncio.run(run())
    assert not mark.visible
    assert not app.ticking


def test_a_key_press_hides_the_pointer():
    app, page = handheld_app()
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    assert app.view.pointer.visible
    app.press("5")
    assert not app.pointer.visible
    assert not app.view.pointer.visible


def test_a_tap_with_the_pointer_showing_clicks_the_sheet_cell_under_it():
    app, page = handheld_app()
    app.state.run_action("add_page", "spreadsheet")
    app.refresh()
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    scale = app.state.scale
    app.pointer.x = (ROW_LABELS + 70) * scale  # column B
    app.pointer.y = (HEAD + FORMULA + ROW + 2) * scale  # row 2
    app.on_stick("tap", 0, 0)
    sheet = app.state.sheet
    assert sheet is not None
    assert sheet.cursor == (1, 2)
    assert app.pointer.visible  # it stays a while after a click


def test_a_tap_with_the_pointer_showing_elsewhere_still_selects():
    """The Calculator page has no hit test yet, so the key keeps its usual meaning."""
    app, page = handheld_app()
    app.act("open_menu", "menu")
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    app.on_stick("tap", 0, 0)
    assert panels(app) == 2
    assert STICK_KEY == "click"
