"""Browser key events become key names (FR-DEV-001)."""

import asyncio
from collections.abc import Callable
from typing import cast

import flet as ft
import pytest
from tests.app.test_splitter_drag import handheld_app

from cassim.app.keyboard import key_name, repeat_interval
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.ui import app as app_module

# (key, modifiers as letters: s shift, c ctrl, a alt, m meta, expected name)
CASES = [
    ("A", "", "a"),
    ("A", "s", "A"),
    ("6", "s", "^"),
    ("9", "s", "("),
    ("Slash", "", "/"),
    ("Slash", "c", "ctrl+/"),
    ("Z", "c", "ctrl+z"),
    ("Z", "m", "ctrl+z"),
    ("Enter", "c", "ctrl+Enter"),
    ("Enter", "a", "alt+Enter"),
    ("Tab", "s", "shift+Tab"),
    ("Arrow Left", "", "ArrowLeft"),
    ("Space", "c", "ctrl+ "),
    ("Shift Left", "", None),
    ("Escape", "", "Escape"),
    ("F1", "", "F1"),
    ("H", "sa", "alt+shift+h"),
    ("F5", "", None),
]


@pytest.mark.parametrize(("key", "mods", "name"), CASES)
def test_key_name(key: str, mods: str, name: str | None) -> None:
    got = key_name(key, shift="s" in mods, ctrl="c" in mods, alt="a" in mods, meta="m" in mods)
    assert got == name


def test_arrow_repeat_accelerates_after_a_sustained_hold() -> None:
    assert repeat_interval(1.49) == 0.15
    assert repeat_interval(1.5) == 0.05


def test_arrow_repeat_stops_on_release(monkeypatch: pytest.MonkeyPatch) -> None:
    app, page = handheld_app()
    monkeypatch.setattr(app, "refresh", lambda: None)
    monkeypatch.setattr(app_module, "REPEAT_DELAY", 0.01)
    monkeypatch.setattr(app_module, "repeat_interval", lambda _: 0.01)
    calculator = calculator_on(app.state.document.current)
    calculator.editor.insert_text("123456789")
    key = ft.KeyboardEvent(
        "keyboard_event", cast("ft.Page", page), "Arrow Left", False, False, False, False
    )

    async def hold_and_release() -> None:
        await app.on_key(key)
        assert calculator.editor.pos == 8
        task = asyncio.create_task(page.tasks.pop())
        await asyncio.sleep(0.035)
        app.keyboard_up("Arrow Left")
        released_at = calculator.editor.pos
        await task
        assert calculator.editor.pos == released_at
        assert released_at < 8

    asyncio.run(hold_and_release())


def test_keypad_arrow_hold_repeats_until_release(monkeypatch: pytest.MonkeyPatch) -> None:
    app, page = handheld_app()
    monkeypatch.setattr(app, "refresh", lambda: None)
    monkeypatch.setattr(app_module, "REPEAT_DELAY", 0.01)
    monkeypatch.setattr(app_module, "repeat_interval", lambda _: 0.01)
    calculator = calculator_on(app.state.document.current)
    calculator.editor.insert_text("123456789")

    async def hold_and_release() -> None:
        app.hold_keypad_arrow("left", True)
        assert calculator.editor.pos == 8
        task = asyncio.create_task(page.tasks.pop())
        await asyncio.sleep(0.035)
        app.hold_keypad_arrow("left", False)
        released_at = calculator.editor.pos
        await task
        assert calculator.editor.pos == released_at
        assert released_at < 8

    asyncio.run(hold_and_release())


def test_keypad_arrow_tap_is_not_duplicated_and_cancel_stops_hold() -> None:
    app, _ = handheld_app()
    events: list[tuple[str, bool]] = []
    taps: list[str] = []
    app.keypad.on_arrow_hold = lambda name, down: events.append((name, down))
    app.keypad.on_key = taps.append
    key = next(key for row in app.state.keypad for key in row if key.name == "left")
    control = app.keypad._key(key)
    assert isinstance(control, ft.GestureDetector)
    assert control.on_tap_down is not None
    assert control.on_tap_up is not None
    assert control.on_tap is not None
    assert control.on_tap_cancel is not None
    event = cast("ft.TapEvent", None)
    down = cast("Callable[[ft.TapEvent], None]", control.on_tap_down)
    up = cast("Callable[[ft.TapEvent], None]", control.on_tap_up)
    tap = cast("Callable[[ft.TapEvent], None]", control.on_tap)
    cancel = cast("Callable[[ft.TapCancelEvent], None]", control.on_tap_cancel)
    down(event)
    up(event)
    tap(event)
    assert events == [("left", True), ("left", False)]
    assert taps == []
    tap(event)
    assert taps == ["left"]
    down(event)
    cancel(cast("ft.TapCancelEvent", None))
    assert events[-2:] == [("left", True), ("left", False)]
