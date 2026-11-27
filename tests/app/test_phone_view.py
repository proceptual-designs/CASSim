# Requirements traced here: FR-DEV-004
"""A phone has only Handheld view: Computer view leaves no room for the on-screen keyboard. The
view is picked before the first draw, so the page does not show Computer view and then swap."""

import asyncio
from types import SimpleNamespace
from typing import cast

import flet as ft
from tests.app.test_splitter_drag import handheld_app

from cassim.devices.nspire.ui.state import Mode, System


def test_a_phone_stays_in_handheld() -> None:
    app, _ = handheld_app(412, 915)
    app.set_mode(Mode.COMPUTER)
    assert app.state.mode is Mode.HANDHELD
    app.show_dialog("view:computer")
    assert app.state.mode is Mode.HANDHELD


def test_a_window_shrunk_to_phone_size_goes_to_handheld() -> None:
    app, page = handheld_app(1200, 800)
    app.set_mode(Mode.COMPUTER)
    assert app.state.mode is Mode.COMPUTER
    page.width, page.height = 412, 915
    app.on_resize(cast("ft.PageResizeEvent", SimpleNamespace(width=412, height=915)))
    assert app.state.mode is Mode.HANDHELD


def recovered_mode(width: float, height: float, saved: Mode | None) -> Mode:
    app, _ = handheld_app(width, height)
    app.state.mode = Mode.COMPUTER  # the default before anything is read

    async def read(key: str) -> str | None:
        return System(start_mode=saved).dumps() if saved and key == "system" else None

    async def nothing_shared(_key: str) -> str | None:
        return None  # no shared theme (SDD-15 section 7) saved either

    app.shell.read = read  # ty: ignore[invalid-assignment]
    app.shell.read_global = nothing_shared  # ty: ignore[invalid-assignment]
    asyncio.run(app.recover_system())
    return app.state.mode


def test_the_view_is_chosen_before_the_first_draw() -> None:
    assert recovered_mode(412, 915, Mode.COMPUTER) is Mode.HANDHELD  # a phone, whatever is saved
    assert recovered_mode(412, 915, None) is Mode.HANDHELD
    assert recovered_mode(1200, 800, Mode.HANDHELD) is Mode.HANDHELD
    assert recovered_mode(1200, 800, None) is Mode.COMPUTER
