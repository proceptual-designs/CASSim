# Requirements traced here: FR-DEV-004
"""Dragging the Handheld splitter: drag steps are coalesced into one redraw, and a redraw rebuilds
only the part whose scale changed. A redraw of the screen and all the keys for every step made the
drag lag behind the pointer (PLAN.md, M2 note of 2026-11-08)."""

import asyncio
from collections.abc import Callable, Coroutine
from types import SimpleNamespace
from typing import Any, cast

import flet as ft

from cassim.app.shell import Shell
from cassim.devices.nspire import DEVICE
from cassim.devices.nspire.ui.app import App
from cassim.devices.nspire.ui.state import AppState, Mode


class FakePage(SimpleNamespace):
    """Just enough of a Flet page for `App` to arrange itself."""

    def __init__(self, width: float, height: float) -> None:
        super().__init__(width=width, height=height, url="", services=[], updates=0)
        self.tasks: list[Coroutine[Any, Any, None]] = []

    def run_task(self, handler: Callable[..., Coroutine[Any, Any, None]], *args: object) -> None:
        self.tasks.append(handler(*args))

    def update(self) -> None:
        self.updates += 1

    def run_queued(self) -> None:
        tasks, self.tasks = self.tasks, []
        for task in tasks:
            asyncio.run(task)


def handheld_app(width: float = 1200, height: float = 700) -> tuple[App, FakePage]:
    page = FakePage(width, height)
    app = App(Shell(cast("ft.Page", page), DEVICE), AppState(mode=Mode.HANDHELD))
    app.arrange()
    page.tasks.clear()
    return app, page


def test_many_drag_steps_make_one_redraw() -> None:
    app, page = handheld_app()
    redraws: list[float] = []
    redraw = app.resize_now
    app.resize_now = lambda: (redraws.append(app.state.system.keypad_share), redraw())[1]  # ty: ignore[invalid-assignment]
    for share in (0.30, 0.32, 0.34, 0.36, 0.38):
        app.state.system.keypad_share = share
        app.resize_soon()
    assert len(page.tasks) == 1  # the later steps only moved the share
    page.run_queued()
    assert redraws == [0.38]  # one redraw, at the share the pointer reached
    app.resize_soon()  # and the next step is not locked out
    assert len(page.tasks) == 1
    page.run_queued()


def test_a_redraw_rebuilds_only_the_part_whose_scale_changed() -> None:
    """Here (Tablet view: the keypad beside the screen) the screen is limited by the height of
    the window, so the splitter changes only the keys' scale: the history is not drawn again."""
    app, page = handheld_app(1200, 700)
    app.state.mode = Mode.TABLET
    app.state.system.keypad_share = 0.2
    app.resize_now()
    screen_scale = app.state.scale
    view_refreshes: list[int] = []
    app.view.refresh = lambda: view_refreshes.append(1)  # ty: ignore[invalid-assignment]
    keys = app.keypad.control.controls
    app.state.system.keypad_share = 0.22
    app.resize_now()
    assert app.state.scale == screen_scale
    assert view_refreshes == []
    assert app.keypad.control.controls is not keys  # the keys were drawn at their new scale
    assert page.updates >= 2
