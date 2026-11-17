# Requirements traced here: FR-DEV-004
"""Full screen (or the installed app) in Handheld: the screen takes the spare height, the status
line is drawn over it instead of taking a row, and the published page covers a camera cutout."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import flet as ft
import pytest
from tests.app.test_splitter_drag import handheld_app
from tools import publish

from cassim.device.keys import keypad_units
from cassim.devices.nspire import keymap as nspire
from cassim.devices.nspire.ui.app import App
from cassim.devices.nspire.ui.layout import (
    FULL_RESERVE,
    PHONE_MARGIN,
    SCREEN_H,
    Sizing,
    full_screen_height,
    handheld_plan,
    keypad_size,
)
from cassim.devices.nspire.ui.state import Mode

UNITS = keypad_units(nspire.KEYPAD)


def padding(app: App) -> ft.Padding:
    value = app.outer.padding
    assert isinstance(value, ft.Padding)
    return value


def test_portrait_the_screen_takes_what_the_keypad_leaves() -> None:
    """The keys are sized with the reserve still taken, then the screen gets the reserve too."""
    sizing = Sizing(None, 1.0, FULL_RESERVE, PHONE_MARGIN, splitter=False)
    plan = handheld_plan(400, 900, *UNITS, sizing)
    assert not plan.side_by_side
    sizing = Sizing(None, 1.0, 0, PHONE_MARGIN, splitter=False)
    height = full_screen_height(plan, 900, UNITS[1], sizing)
    pad = keypad_size(*UNITS)[1] * plan.pad_scale
    assert height >= SCREEN_H * plan.scale + FULL_RESERVE - 1e-6
    assert abs(height + pad + sizing.between - (900 - 2 * PHONE_MARGIN)) < 1e-6


def test_landscape_the_screen_is_the_window_height() -> None:
    sizing = Sizing(None, 1.0, 0, PHONE_MARGIN, splitter=False)
    plan = handheld_plan(900, 400, *UNITS, sizing)
    assert plan.side_by_side
    assert full_screen_height(plan, 400, UNITS[1], sizing) == 400 - 2 * PHONE_MARGIN


def test_never_shorter_than_the_natural_screen() -> None:
    plan = handheld_plan(None, None, *UNITS)
    assert full_screen_height(plan, None, UNITS[1], Sizing()) == SCREEN_H * plan.scale


def offers(*, standalone: bool) -> SimpleNamespace:
    return SimpleNamespace(
        installable=False,
        can_fullscreen=True,
        standalone=standalone,
        in_fullscreen=standalone,
        installed=False,
        touch=False,
        safe_area=(0, 0, 0, 0),
        offline_state="ready",
        offline_message="Ready for offline use.",
        offline_retry=False,
        update_ready=False,
    )


def test_the_app_grows_the_screen_and_moves_the_status_in_full_screen() -> None:
    app, _ = handheld_app(400, 900)
    normal = app.view.control.height
    assert normal is not None
    shell: Any = app.shell
    shell.bridge = offers(standalone=True)
    app.arrange()
    assert app.full
    assert (app.view.control.height or 0) > normal
    assert not app.toolbar.visible
    app.say("Calculating... press Esc to cancel")
    assert app.view.doc_name.value == "Calculating... press Esc to cancel"  # in the title bar
    app.say("")
    assert app.view.doc_name.value == "Untitled"
    shell.bridge = offers(standalone=False)
    app.arrange()
    app.place_status()
    assert not app.full
    assert app.view.control.height == normal
    assert app.toolbar.visible
    assert app.status in app.toolbar.controls


def test_the_published_page_covers_the_cutout() -> None:
    assert "viewport-fit=cover" in publish.HEAD_TAGS
    assert "viewport-fit=cover" in publish.BODY_TAGS


@pytest.mark.parametrize("size", [(400, 900), (900, 400)])
def test_installed_phone_cutout_toggle_uses_all_safe_area_edges(size: tuple[int, int]) -> None:
    app, page = handheld_app(*size)
    shell: Any = app.shell
    shell.bridge = offers(standalone=True)
    shell.bridge.installed = True
    shell.bridge.in_fullscreen = False
    shell.bridge.safe_area = (30, 25, 10, 20)
    app.arrange()
    initial_height = app.view.control.height
    assert app.use_cutout
    assert padding(app).top == 0
    assert app.cassim_menu().items[1].label == "Avoid cutout"

    with patch.object(app, "refresh"):
        app.go_fullscreen()
        assert not app.use_cutout
        assert app.cassim_menu().items[1].label == "Use cutout"
        assert padding(app).top == 30
        assert padding(app).right == 25 + PHONE_MARGIN
        assert padding(app).bottom == 10 + PHONE_MARGIN
        assert padding(app).left == 20 + PHONE_MARGIN
        assert app.view.control.height is not None
        assert initial_height is not None
        assert app.view.control.height < initial_height
        assert not app.toolbar.visible
        app.go_fullscreen()
    assert app.use_cutout
    assert app.view.control.height == initial_height
    assert padding(app).top == 0
    assert page.width == size[0]


def test_cutout_choice_survives_resize_and_only_affects_installed_phones() -> None:
    app, page = handheld_app(400, 900)
    shell: Any = app.shell
    shell.bridge = offers(standalone=True)
    shell.bridge.installed = True
    shell.bridge.in_fullscreen = False
    shell.bridge.safe_area = (30, 25, 10, 20)
    with patch.object(app, "refresh"):
        app.go_fullscreen()
        page.width, page.height = 900, 400
        app.arrange()
        assert padding(app).left == 20 + PHONE_MARGIN
        page.width, page.height = 1200, 700
        app.arrange()
        assert padding(app).left != 20 + PHONE_MARGIN
        page.width, page.height = 400, 900
        shell.bridge.installed = False
        app.arrange()
        assert padding(app).top == 0
        shell.bridge.installed = True
        shell.bridge.safe_area = (0, 0, 0, 0)
        app.arrange()
        assert padding(app).top == 0
        assert not app.use_cutout


def test_noninstalled_phone_keeps_browser_fullscreen_action() -> None:
    app, _ = handheld_app(400, 900)
    shell: Any = app.shell
    shell.bridge = offers(standalone=False)
    with patch.object(app.shell, "toggle_fullscreen") as toggle:
        app.go_fullscreen()
        toggle.assert_called_once()
    assert app.use_cutout


def test_cassim_key_opens_menu_and_ctrl_installs() -> None:
    """FR-PWA-001: the new key works even when no install offer is present."""
    app, _ = handheld_app(400, 900)
    shell: Any = app.shell
    shell.bridge = offers(standalone=False)
    with patch.object(app, "refresh"), patch.object(app, "install") as install:
        app.press_cassim()
        assert app.state.menu is not None
        assert app.state.menu.root.label == "CASSim"
        shell.bridge.installable = True
        app.state.press_keypad("ctrl")
        app.press_cassim()
        install.assert_called_once()
        assert app.state.pending == ""


def test_cassim_key_red_dot_tracks_browser_attention() -> None:
    """FR-PWA-002/004: offline failures and waiting updates are visible without an overlay."""
    app, _ = handheld_app(400, 900)
    shell: Any = app.shell
    shell.bridge = offers(standalone=False)
    app.arrange()
    app.keypad.refresh()
    row = app.keypad.control.controls[0]
    assert isinstance(row, ft.Row)
    key = row.controls[-1]
    assert isinstance(key, ft.Container)
    assert key.tooltip == "CASSim menu"
    shell.bridge.update_ready = True
    app.arrange()
    app.keypad.refresh()
    row = app.keypad.control.controls[0]
    assert isinstance(row, ft.Row)
    key = row.controls[-1]
    assert isinstance(key, ft.Container)
    assert key.tooltip == "CASSim menu: attention required"
    column = key.content
    assert isinstance(column, ft.Column)
    labels = column.controls[-1]
    assert isinstance(labels, ft.Row)
    assert any(
        isinstance(control, ft.Icon) and control.color == "#e53935" for control in labels.controls
    )
    shell.bridge.update_ready = False
    shell.bridge.offline_state = "unavailable"
    app.state.mode = Mode.COMPUTER
    toolbar_button = next(
        control
        for row in app.toolbar_controls()
        if isinstance(row, ft.Row)
        for control in row.controls
        if control.tooltip == "CASSim menu: attention required"
    )
    assert isinstance(toolbar_button, ft.Container)
    toolbar_labels = toolbar_button.content
    assert isinstance(toolbar_labels, ft.Row)
    assert any(
        isinstance(control, ft.Icon) and control.color == "#e53935"
        for control in toolbar_labels.controls
    )


def test_reload_update_asks_before_reloading_unsaved_document() -> None:
    """FR-PWA-004: a waiting update never reloads automatically or discards unsaved work."""
    app, page = handheld_app()
    app.state.document.name = "Changed"
    dialogs: list[tuple[str, str, str, Any]] = []
    with (
        patch.object(app.shell, "confirm", side_effect=lambda *args: dialogs.append(args)),
        patch.object(app.shell, "reload_update") as reload_update,
    ):
        app.reload_update()
        reload_update.assert_not_called()
        assert dialogs
        assert dialogs[0][0] == "Reload CASSim?"
        page.run_task(dialogs[0][3])
        page.run_queued()
        reload_update.assert_called_once()
