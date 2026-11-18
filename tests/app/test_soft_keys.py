# Requirements traced here: FR-DEV-004
"""Computer view on a phone or tablet: a tap where typing goes opens the on-screen keyboard (a
hidden text box takes the focus), and what is typed there reaches the calculator."""

from types import SimpleNamespace
from typing import Any

from tests.app.test_splitter_drag import handheld_app

from cassim.device.keys import Binding
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.ui.soft_keys import SENTINEL, keys_for
from cassim.devices.nspire.ui.state import Mode


def test_typed_text_becomes_keys() -> None:
    assert keys_for(SENTINEL + "2x") == [Binding("insert", "2"), Binding("insert", "x")]
    assert keys_for("") == [Binding("backspace")]  # the sentinel was deleted
    assert keys_for("a" + SENTINEL) == [Binding("insert", "a")]  # typed before it
    assert keys_for(SENTINEL) == []


def touch_app(*, touch: bool) -> Any:
    app, page = handheld_app(1000, 700)
    shell: Any = app.shell
    shell.bridge = SimpleNamespace(
        installable=False,
        can_fullscreen=True,
        standalone=False,
        in_fullscreen=False,
        installed=False,
        touch=touch,
        safe_area=(0, 0, 0, 0),
        offline_state="ready",
        offline_message="Ready for offline use.",
        offline_retry=False,
        update_ready=False,
    )
    app.state.mode = Mode.COMPUTER
    app.arrange()
    page.tasks.clear()
    return app, page


def test_a_tap_in_the_entry_line_opens_the_keyboard_on_a_touch_screen() -> None:
    app, page = touch_app(touch=True)
    app.act("place", ":0")
    assert len(page.tasks) >= 1
    assert any("focus" in task.__qualname__ for task in page.tasks)
    for task in page.tasks:
        task.close()


def test_no_keyboard_with_a_mouse_or_in_handheld() -> None:
    app, page = touch_app(touch=False)
    app.offer_keyboard("place")
    assert not page.tasks
    app, page = touch_app(touch=True)
    app.state.mode = Mode.HANDHELD
    app.offer_keyboard("place")
    assert not page.tasks
    app.state.mode = Mode.COMPUTER
    app.offer_keyboard("enter")  # not a tap where typing goes
    assert not page.tasks


def test_what_is_typed_reaches_the_entry_line() -> None:
    app, page = touch_app(touch=True)
    app.sink.value = SENTINEL + "1+2"
    app.on_sink()
    assert app.sink.value == SENTINEL
    calculator = calculator_on(app.state.document.current)
    assert calculator.editor.linear() == "1+2"
    app.sink.value = ""  # Backspace
    app.on_sink()
    assert calculator.editor.linear() == "1+"
    app.sink.value = SENTINEL + "3"
    app.on_sink_submit()
    assert calculator.history[-1].result.text == "4"
    for task in page.tasks:
        task.close()


def test_hardware_keys_are_not_typed_twice_while_the_box_has_focus() -> None:
    app, _ = touch_app(touch=True)
    app.sink_focused = True
    event = SimpleNamespace(key="7", shift=False, ctrl=False, alt=False, meta=False)
    import asyncio  # noqa: PLC0415

    asyncio.run(app.on_key(event))
    assert calculator_on(app.state.document.current).editor.linear() == ""


def test_physical_escape_cancels_pending_keypad_modifiers() -> None:
    """FR-DEV-001: physical Escape cancels keypad Ctrl or Shift and closes the open menu."""
    app, page = touch_app(touch=True)
    import asyncio  # noqa: PLC0415

    for modifier in ("ctrl", "shift"):
        app.state.key_event("F2")
        app.state.press_keypad(modifier)
        assert app.state.pending == modifier
        asyncio.run(
            app.on_key(
                SimpleNamespace(key="Escape", shift=False, ctrl=False, alt=False, meta=False)
            )
        )
        assert app.state.pending == ""
        assert app.state.screen().menu is None
    for task in page.tasks:
        task.close()


def test_physical_escape_cancels_pending_keypad_modifier_while_busy() -> None:
    app, page = touch_app(touch=True)
    app.starting = True
    app.state.press_keypad("shift")
    import asyncio  # noqa: PLC0415

    asyncio.run(
        app.on_key(SimpleNamespace(key="Escape", shift=False, ctrl=False, alt=False, meta=False))
    )
    assert app.state.pending == ""
    for task in page.tasks:
        task.close()
