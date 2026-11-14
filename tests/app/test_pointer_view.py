# Requirements traced here: FR-DEV-005
"""The keypad's centre key steers a pointer on the screen: the arrow shows while it moves, hides
after a second, and a tap with it showing clicks where it is: a menu row, a history line, the entry
line or a sheet cell, as a tap there would (emulator check 6, part P4)."""

import asyncio
from types import SimpleNamespace
from typing import Any, cast

import flet as ft
import pytest
from tests.app.test_splitter_drag import handheld_app

from cassim.device import pointer as pointer_module
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.sheet_scene import FORMULA, HEAD, ROW, ROW_LABELS
from cassim.devices.nspire.ui import app as app_module
from cassim.devices.nspire.ui.layout import key_span
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import (
    HEADER_H,
    LIST_ROW_H,
    MENU_STEP_Y,
    STICK_KEY,
    Keypad,
    selected_index,
)


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


def click(app: Any, x: float, y: float) -> None:
    """Show the pointer, put its tip at (`x`, `y`) handheld pixels of the body, and tap."""
    app.on_stick("start", 0, 0)
    app.page.tasks.clear()
    app.pointer.x, app.pointer.y = app.state.px(x), app.state.px(y)
    app.on_stick("tap", 0, 0)


def menu_row_y(row: int, depth: int = 0) -> float:
    """The middle of list row `row` of the panel at `depth`, with no ▲ above the rows."""
    return 4 + depth * MENU_STEP_Y + 4 + HEADER_H + (row + 0.5) * LIST_ROW_H


def test_a_click_on_a_menu_row_picks_it():
    app, _ = handheld_app()
    app.act("open_menu", "menu")
    click(app, 60, menu_row_y(2))  # 3: Algebra
    menu = app.state.screen().menu
    assert menu is not None
    assert len(menu.panels) == 2  # its submenu opened, as a tap on the row does
    assert selected_index(menu.panels[0]) == 2
    assert STICK_KEY == "click"


def test_a_click_on_a_submenu_header_goes_back_and_outside_closes():
    app, _ = handheld_app()
    app.act("open_menu", "menu")
    click(app, 60, menu_row_y(2))
    click(app, 60, 4 + MENU_STEP_Y + 4 + HEADER_H / 2)  # the submenu's ◀ header
    assert panels(app) == 1
    click(app, 300, 200)  # right of the panel
    assert panels(app) == 0


def test_a_click_on_a_grid_menu_picks_the_cell():
    app, _ = handheld_app()
    app.act("open_menu", "templates")
    view = app.view
    box = view._boxes[-1]
    assert box.columns
    x = (box.left + box.pad + 2.5 * box.cell) / app.state.px(1)  # the third cell
    y = (box.top + box.pad + box.header + box.line / 2) / app.state.px(1)
    assert view.menu_click(app.state.px(x), app.state.px(y)) == ("menu_pick", "0:2")


def report_sizes(app: Any, row_height: float = 30.0, entry_width: float = 40.0) -> None:
    """Stand in for Flet's size reports: every history child, and each history line."""
    for control in app.view.history.controls:
        handler = control.on_size_change
        assert handler is not None  # the pointer is in use, so sizes are asked for
        height = control.height if control.height is not None else row_height
        handler(SimpleNamespace(width=300.0, height=height))
        body = getattr(control, "content", None)
        for line in getattr(body, "controls", []):
            if line.on_size_change is not None:
                line.on_size_change(SimpleNamespace(width=entry_width, height=row_height / 2))


def test_a_click_on_a_history_line_picks_it_and_on_the_entry_places_the_cursor():
    app, page = handheld_app()
    for keys in (("1", "plus", "1"), ("2", "times", "3")):
        for key in (*keys, "enter"):
            app.press(key)
    app.press("4")
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    report_sizes(app)
    px = app.state.px(1)
    spacing = app.view.history.spacing
    second_row = 6 * px + spacing + 30 + spacing  # under the spacer and the first row
    app.pointer.x, app.pointer.y = 10.0, second_row + 5
    app.on_stick("tap", 0, 0)
    calculator = calculator_of(app.state.document.current)
    assert calculator is not None
    assert calculator.recall == (1, "entry")
    report_sizes(app)  # the click redrew the history, which reports its sizes again
    first_row = 6 * px + spacing + 5
    app.pointer.x, app.pointer.y = 200.0, first_row  # right of the entry: its result
    app.on_stick("tap", 0, 0)
    assert calculator.recall == (0, "result")
    entry_line = second_row + 30 + spacing + 5
    app.pointer.x, app.pointer.y = 10.0, entry_line
    app.press("esc")  # back to the entry line
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    calculator.editor.home()
    report_sizes(app)
    app.on_stick("tap", 0, 0)
    assert calculator.editor.pos == len(calculator.editor.root)  # at the end of `4`


def size_handlers(app: Any) -> list[object]:
    return [getattr(control, "on_size_change", None) for control in app.view.history.controls]


def test_history_sizes_are_asked_for_only_while_the_pointer_is_in_use():
    app, page = handheld_app()
    app.press("1")
    app.press("enter")
    assert all(handler is None for handler in size_handlers(app))
    assert app.view.history.on_scroll is not None  # the scroll offset is always followed
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    assert all(handler is not None for handler in size_handlers(app))
    app.pointer.hide()
    asyncio.run(app.steer())  # the loop ends at once and turns the reports off
    app.refresh()
    assert all(handler is None for handler in size_handlers(app))


def test_before_the_sizes_arrive_a_tap_still_selects():
    app, page = handheld_app()
    app.press("1")
    app.press("enter")
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    assert not app.view.history_click(10, 10)


def test_a_clicked_line_is_picked_where_it_is_but_a_line_picked_by_keys_is_followed():
    """Picking a line scrolls the history to it, except when a click picked it: the line is under
    the pointer or the finger, and scrolling would move it away (found in the browser)."""
    app, _ = handheld_app()
    for key in ("1", "enter", "2", "enter"):
        app.press(key)
    app.view._click_line("0:entry")
    assert app.view._follow is False
    app.refresh()  # a pointer click redraws twice: the second must not follow either
    assert app.view._follow is False
    app.press("down")  # the keys pick another line: the view follows it
    assert app.view._follow is True


def test_the_entry_lines_size_is_kept_across_redraws():
    """The entry line is one control for the page's life, and Flet reports a size only when it
    changes, so its last report must survive a redraw."""
    app, page = handheld_app()
    app.press("1")
    app.press("enter")
    app.on_stick("start", 0, 0)
    page.tasks.clear()
    report_sizes(app)
    app.refresh()  # a redraw: the rows are new controls, the entry line is not
    for control in app.view.history.controls:
        handler = getattr(control, "on_size_change", None)
        if control is not app.view.entry and handler is not None:
            height = getattr(control, "height", None) or 30.0
            handler(SimpleNamespace(width=300.0, height=height))
    assert app.view.history_click(10, 2) is not False


def test_a_redraw_at_the_end_forgets_an_old_scroll_report():
    """A user scroll is reported, but the jump back to the end on the next redraw may not be: so
    a redraw with no line picked drops the old offset and the end is assumed (found in the
    browser: a click after a wheel scroll picked the line above)."""
    app, _ = handheld_app()
    app.press("1")
    app.press("enter")
    app.view._scrolled(cast("ft.OnScrollEvent", SimpleNamespace(pixels=40.0)))
    assert app.view._scroll == 40.0
    app.press("2")  # any redraw with no line picked
    assert app.view._scroll is None


def test_a_click_keeps_the_view_where_it_was_until_another_line_is_picked():
    """Picking a line makes the history stop keeping itself at its end, and Flet then resets the
    scroll position, so after a click the view is put back where the click was made."""
    app, _ = handheld_app()
    for key in ("1", "enter", "2", "enter"):
        app.press(key)
    view = app.view
    view._scrolled(cast("ft.OnScrollEvent", SimpleNamespace(pixels=12.0)))
    view._click_line("0:entry")
    assert (view._held, view._keep) == (0, 12.0)
    app.refresh()
    assert (view._held, view._keep) == (0, 12.0)  # still the clicked line: still kept
    app.press("esc")  # nothing picked: let go
    assert (view._held, view._keep) == (None, None)
