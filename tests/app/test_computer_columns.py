# Requirements traced here: FR-DEV-002, FR-DOC-001, FR-DEV-006
"""Computer mode's resizable, movable columns and compact controls."""

import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import flet as ft
import pytest

from cassim.app.shell import Shell
from cassim.devices.nspire import DEVICE
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.app import App
from cassim.devices.nspire.ui.state import AppState, Mode


class FakePage(SimpleNamespace):
    def __init__(self, width: float = 1280, height: float = 800) -> None:
        super().__init__(width=width, height=height, url="", services=[], updates=0, tasks=[])

    def update(self) -> None:
        self.updates += 1

    def run_task(self, handler: object, *args: object) -> None:
        self.tasks.append((handler, args))


def computer_app(width: float = 1280) -> tuple[App, FakePage]:
    page = FakePage(width)
    app = App(Shell(cast("ft.Page", page), DEVICE), AppState())
    app.arrange()
    return app, page


def descendants(control: ft.Control) -> list[ft.Control]:
    found = [control]
    children = getattr(control, "controls", None)
    if children is not None:
        for child in children:
            found.extend(descendants(child))
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        found.extend(descendants(content))
    return found


def text_chip(controls: list[ft.Control], label: str) -> ft.Container:
    return next(
        control
        for root in controls
        for control in descendants(root)
        if isinstance(control, ft.Container)
        and isinstance(control.content, ft.Text)
        and control.content.value == label
    )


def test_computer_layout_defaults_to_sidebar_workspace_and_optional_keypad() -> None:
    app, _ = computer_app()
    assert app.frame.controls == [app.layout]
    row = app.layout.content
    assert isinstance(row, ft.Row)
    targets = [control for control in row.controls if isinstance(control, ft.DragTarget)]
    assert len(targets) == 2
    assert list(app.computer_panels) == ["sidebar", "workspace"]
    sidebar_content = app.computer_panels["sidebar"].content
    assert isinstance(sidebar_content, ft.Column)
    content = sidebar_content.controls[1]
    assert isinstance(content, ft.Column)
    assert content.controls[0] is app.toolbar

    app.toggle_keypad()
    row = app.layout.content
    assert isinstance(row, ft.Row)
    assert list(app.computer_panels) == ["sidebar", "workspace", "keypad"]
    assert app.keypad.control in descendants(app.computer_panels["keypad"])


def test_computer_columns_can_be_resized_and_swapped() -> None:
    app, _ = computer_app()
    app.toggle_keypad()
    app._resize_boundary("sidebar", "workspace", 40)
    assert app.state.system.computer_sidebar_width == 270
    assert app.computer_panels["sidebar"].width == 270

    app._move_column("keypad", -1)
    assert app.state.system.computer_column_order == ["sidebar", "keypad", "workspace"]
    assert list(app.computer_panels) == ["sidebar", "keypad", "workspace"]


def test_computer_toolbar_removes_page_arrows_and_keeps_undo_redo() -> None:
    app, _ = computer_app()
    controls = app.toolbar_controls()
    tips = {
        control.tooltip
        for root in controls
        for control in descendants(root)
        if isinstance(control, ft.Container | ft.IconButton) and control.tooltip
    }
    assert "Undo (Ctrl+Z)" in tips
    assert "Redo (Ctrl+Y)" in tips
    labels = {
        control.content.value
        for root in controls
        for control in descendants(root)
        if isinstance(control, ft.Container)
        and isinstance(control.content, ft.Text)
        and control.content.value
    }
    assert "◀ page" not in labels
    assert "page ▶" not in labels


def test_computer_mode_and_keypad_controls_have_toggle_states() -> None:
    app, _ = computer_app()
    controls = app.toolbar_controls()
    mode_toggle = next(control for control in controls if isinstance(control, ft.SegmentedButton))
    assert [segment.value for segment in mode_toggle.segments] == ["handheld", "computer"]
    assert mode_toggle.selected == ["computer"]
    assert not mode_toggle.show_selected_icon
    assert not mode_toggle.allow_empty_selection
    assert not mode_toggle.allow_multiple_selection
    assert text_chip(controls, "Keypad").bgcolor == app.theme.key
    app.state.system.computer_keypad = True
    assert text_chip(app.toolbar_controls(), "Keypad").bgcolor == app.theme.accent


def test_selecting_handheld_on_mode_toggle_switches_view() -> None:
    app, _ = computer_app()
    toggle = next(
        control for control in app.toolbar_controls() if isinstance(control, ft.SegmentedButton)
    )
    toggle.selected = ["handheld"]
    assert toggle.on_change is not None
    handler = cast("Callable[[ft.Event[ft.SegmentedButton]], object]", toggle.on_change)
    handler(ft.Event("change", toggle))
    assert app.state.mode is Mode.HANDHELD


def test_handheld_still_uses_the_same_keypad_control() -> None:
    app, _ = computer_app()
    keypad = app.keypad.control
    app.set_mode(Mode.HANDHELD)
    assert keypad in descendants(app.layout)
    app.state.system.computer_keypad = True
    app.set_mode(Mode.COMPUTER)
    assert keypad in descendants(app.layout)


def test_variable_delete_can_be_undone_and_redone(monkeypatch: pytest.MonkeyPatch) -> None:
    app, _ = computer_app()

    def no_refresh() -> None:
        pass

    def no_flash(text: str) -> None:
        pass

    monkeypatch.setattr(app, "refresh", no_refresh)
    monkeypatch.setattr(app, "flash", no_flash)
    session = app.state.document.problems[0].session
    session.eval("a:=5")
    session.eval("f(x):=x^2")
    rows = tuple(session.variables())
    calculator = calculator_of(app.state.document.current)
    assert calculator is not None

    asyncio.run(
        app._delete_variables(
            calculator,
            tuple(row.name for row in rows),
            tuple(row.source for row in rows),
        )
    )
    assert not session.is_defined("a")
    assert not session.is_defined("f")

    asyncio.run(app._apply_variable_history("undo"))
    assert session.eval("a").text == "5"
    assert session.eval("f(3)").text == "9"
    asyncio.run(app._apply_variable_history("redo"))
    assert not session.is_defined("a")
    assert not session.is_defined("f")
