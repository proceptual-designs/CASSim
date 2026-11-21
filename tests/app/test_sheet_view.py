# Requirements traced here:
# FR-SHEET-001, FR-SHEET-003 to 007, FR-STAT-001, FR-STAT-004,
# FR-STAT-005, FR-DOC-009, NFR-PERF-006, FR-DEV-004
"""The Lists & Spreadsheet page in the Flet view (slice 3b): it draws in the screen's place of
the history, keeps the canvases of layers that did not change, and turns taps, long presses,
drags and the wheel into sheet actions (decision 0031 item 7)."""

import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import flet as ft
from tests.app.test_splitter_drag import FakePage

from cassim.app.shell import Shell
from cassim.device.keys import Action, Binding
from cassim.device.wizard import Field
from cassim.devices.nspire import DEVICE
from cassim.devices.nspire.pages.spreadsheet import NAME_ROW, AreaPane, ShadePane
from cassim.devices.nspire.sheet_scene import (
    FORMULA,
    HEAD,
    ROW,
    ROW_LABELS,
    cell_at,
    context_regions,
)
from cassim.devices.nspire.statistics_plot import AreaPlot, PValuePlot
from cassim.devices.nspire.ui.app import App
from cassim.devices.nspire.ui.sheet_view import BAR, SheetView, sheet_colours
from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.views import CalculatorView, field_box
from cassim.sheet.fileio import FileCell, read_csv


def sheet_state() -> AppState:
    state = AppState(mode=Mode.HANDHELD)
    state.run_action("add_page", "spreadsheet")
    return state


def at(x: float, y: float) -> Any:
    return event(local_position=ft.Offset(x, y), kind=ft.PointerDeviceType.TOUCH)


def event(**fields: object) -> Any:
    """A stand-in for a Flet gesture event."""
    return SimpleNamespace(**fields)


def texts(control: object) -> list[str]:
    found: list[str] = []
    for name in ("value", "content"):
        value = getattr(control, name, None)
        if isinstance(value, str):
            found.append(value)
    for name in ("content", "controls"):
        inner = getattr(control, name, None)
        for child in inner if isinstance(inner, list) else [inner]:
            if child is not None:
                found.extend(texts(child))
    return found


class Recorder:
    def __init__(self, state: AppState) -> None:
        self.state = state
        self.done: list[tuple[str, str]] = []

    def __call__(self, action: Action, arg: str) -> None:
        self.done.append((action, arg))
        self.state.run_action(action, arg)


def placed(view: CalculatorView) -> list[ft.Container]:
    """A sheet page's panes, each a positioned container."""
    return [cast(ft.Container, control) for control in view.sheet_panes.controls]


def view_for(
    state: AppState, *, shift: Callable[[], bool] = lambda: False
) -> tuple[CalculatorView, Recorder]:
    recorder = Recorder(state)
    view = CalculatorView(state, on_action=recorder, shift=shift)
    view.body_size = lambda: (320.0, 220.0)
    return view, recorder


def test_the_sheet_draws_in_place_of_the_history():
    state = sheet_state()
    view, _ = view_for(state)
    state.run(Binding("insert", "7"))
    state.run(Binding("enter"))
    state.prepare()
    view.refresh()
    assert view.body.controls == [view.sheet_panes]
    assert [pane.content for pane in placed(view)] == [view.sheet_view.control]
    assert texts(view.sheet_view.bar) == ["A2", ""]
    state.run_action("prev_page")
    view.refresh()
    assert view.body.controls == [view.history]


def test_sheet_entry_bar_uses_the_clickable_structured_editor():
    state = sheet_state()
    view, recorder = view_for(state)
    state.run(Binding("insert", "=1"))
    state.run(Binding("template", "fraction"))
    view.refresh()
    assert view.sheet_view.entry_box.content is not view.sheet_view.entry
    assert view.sheet_view.bar.height is not None
    assert view.sheet_view.bar.height > BAR * state.scale
    view.sheet_view.click([], 0)
    assert recorder.done[-1] == ("place", ":0")
    assert state.sheet is not None
    assert state.sheet.editor is not None
    assert state.sheet.editor.path == []
    assert state.sheet.editor.pos == 0


def test_sheet_entry_bar_grows_for_a_tall_template():
    state = sheet_state()
    view, _ = view_for(state)
    state.run(Binding("template", "matrix:4,2"))
    view.refresh()
    assert view.sheet_view.bar.height is not None
    assert view.sheet_view.bar.height > 52 * state.scale


def test_shade_p_value_draws_a_second_pane():
    state = sheet_state()
    view, _ = view_for(state)
    sheet = state.sheet
    assert sheet is not None
    sheet.add_pane(ShadePane("z", 0, PValuePlot(0.8944, 0.3711, 0)))
    view.refresh()
    assert view.body.controls == [view.sheet_panes]
    sheet_pane, shade_pane = placed(view)
    assert sheet_pane.content is view.sheet_view.control
    assert (shade_pane.left, shade_pane.width) == (160, 160)
    assert cast(ft.Container, shade_pane.content).content is not None


def test_four_panes_make_a_two_by_two_page_and_clicks_find_their_pane():
    """FR-DOC-009, decision 0034 item 2 (R5-I2): the sheet top left, then the panes in reading
    order; a pointer click on the sheet's quarter goes to the sheet."""
    state = sheet_state()
    view, _ = view_for(state)
    sheet = state.sheet
    assert sheet is not None
    assert sheet.session.eval("xs:={1,2,3}").error is None
    sheet.go((0, NAME_ROW))
    sheet.menu_action("link:xs")
    sheet.menu_action("quick_graph")
    sheet.add_pane(ShadePane("t", 2, PValuePlot(1.4661, 0.0930, 2, "t", 7)), undoable=False)
    sheet.add_pane(AreaPane(AreaPlot(float("-inf"), 1)), undoable=False)
    view.refresh()
    boxes = [(c.left, c.top, c.width, c.height) for c in placed(view)]
    assert boxes == [(0, 0, 160, 110), (160, 0, 160, 110), (0, 110, 160, 110), (160, 110, 160, 110)]
    assert isinstance(sheet.panes[1], AreaPane)
    view.click_at(40, 60)
    assert sheet.cursor[1] >= 1
    assert view.click_at(200, 160)


def test_sheet_plots_share_a_statistics_pane():
    state = sheet_state()
    view, _ = view_for(state)
    sheet = state.sheet
    assert sheet is not None
    assert sheet.session.eval("scores:={1,2,3}").error is None
    assert sheet.session.eval('labels:={"cat","dog"}').error is None
    assert sheet.session.eval("counts:={5,3}").error is None
    sheet.go((0, NAME_ROW))
    sheet.menu_action("link:scores")
    sheet.menu_action("quick_graph")
    sheet.menu_action('split_summary:{"x":"labels","summary":"counts"}')

    view.refresh()

    sheet_pane, quick, summary = placed(view)
    assert (sheet_pane.height, quick.left, quick.top, summary.top) == (220, 160, 0, 110)
    assert quick.content is view.split_statistics_views[0].control
    assert summary.content is view.split_statistics_views[1].control


def test_csv_menu_actions_import_calculate_and_export_values(monkeypatch):
    page = FakePage(1100, 700)
    state = sheet_state()
    app = App(Shell(cast("ft.Page", page), DEVICE), state)
    app.arrange()
    for task in page.tasks:
        task.close()
    page.tasks.clear()
    downloads: list[tuple[str, bytes, str]] = []

    async def pick_file_bytes(extensions, title):
        assert extensions == ("csv",)
        assert title == "Import CSV data"
        return b"1,=A1+2\r\n"

    async def save_bytes_file(name, data, title):
        downloads.append((name, data, title))

    monkeypatch.setattr(app.shell, "pick_file_bytes", pick_file_bytes)
    monkeypatch.setattr(app.shell, "save_bytes_file", save_bytes_file)

    try:
        asyncio.run(app._sheet_file_action("csv", importing=True))
        asyncio.run(app._sheet_file_action("csv", importing=False))

        assert downloads[0][0] == "spreadsheet.csv"
        assert downloads[0][2] == "Export CSV data"
        assert read_csv(downloads[0][1]) == [[FileCell("1"), FileCell("3")]]
    finally:
        for task in page.tasks:
            task.close()
        page.tasks.clear()


def test_shade_option_is_a_checkbox():
    box = field_box(
        Field("shade", "Shade P Value", "1", toggle=True),
        lambda _: None,
        lambda _: None,
        None,
    )
    assert isinstance(box, ft.Checkbox)
    assert box.value is True


def test_the_window_follows_the_size():
    state = sheet_state()
    view, _ = view_for(state)
    view.body_size = lambda: (320.0 * 2, (HEAD + FORMULA + 8 * ROW + 22) * 2.0)
    state.scale = 2.0
    view.refresh()
    sheet = state.sheet
    assert sheet is not None
    assert (sheet.rows_shown, sheet.columns_shown) == (8, 4)


def test_a_cursor_move_keeps_the_text_canvases():
    """Spike A: a move rebuilds the cursor layer only."""
    state = sheet_state()
    view, _ = view_for(state)
    for value in ("1", "2"):
        state.run(Binding("insert", value))
        state.run(Binding("enter"))
    state.prepare()
    view.refresh()
    before = list(view.sheet_view.grid.controls)
    state.run(Binding("up"))
    view.refresh()
    after = view.sheet_view.grid.controls
    assert after[:3] == before[:3]
    assert after[3] is not before[3]


def test_context_regions_match_pickable_grid_cells():
    state = sheet_state()
    view, _ = view_for(state)
    view.refresh()
    sheet = state.sheet
    assert sheet is not None
    width, height = view.body_size()
    height -= BAR
    for cell in ((0, 1), (25, 2500)):
        sheet.go(cell)
        view.refresh()
        screen = sheet.screen()
        regions = context_regions(screen, 1.0, width, height)
        for x in (0, 23.9, 24, 50, 87.9, 88, 250, 319):
            for y in (0, 15.9, 16, 30.9, 31, 47.9, 48, 150, 197):
                marked = any(
                    left <= x < left + w and top <= y < top + h for left, top, w, h in regions
                )
                assert marked == (cell_at(x, y, screen, 1.0) is not None), (cell, x, y)


def test_taps_long_presses_and_drags():
    state = sheet_state()
    view, recorder = view_for(state)
    view.refresh()
    sheet_view = view.sheet_view
    x = ROW_LABELS + 70  # column B
    sheet_view._tap(at(x, HEAD + FORMULA + ROW + 2))
    assert state.sheet is not None
    assert state.sheet.cursor == (1, 2)
    sheet_view._tap(at(x, 2))
    assert state.sheet.cursor == (1, NAME_ROW)
    sheet_view._tap(at(4, HEAD + FORMULA + 2))  # a row number
    assert state.sheet.whole == "row"
    sheet_view._long_press(at(x, HEAD + FORMULA + 2))
    assert state.menu is not None
    state.menu = None
    sheet_view._secondary_tap(at(x, HEAD + FORMULA + 2))
    assert state.menu is not None
    state.menu = None
    sheet_view._double_tap(at(x, HEAD + FORMULA + 2))
    assert state.sheet.editing == ""
    state.run(Binding("escape"))
    sheet_view._pan_start(at(x, HEAD + FORMULA + 2))
    sheet_view._pan(event(local_delta=ft.Offset(0, -ROW * 3), local_position=None))
    assert state.sheet.top == 4
    sheet_view._scroll(event(scroll_delta=ft.Offset(0, -ROW * 2)))
    assert state.sheet.top == 2
    sheet_view._tap(at(-50, -50))  # outside the grid: nothing
    assert ("sheet_tap", "-1,-1") not in recorder.done


def test_mouse_drag_selects_cells_and_shift_click_extends():
    """FR-SHEET-006: drag and Shift+click select the inclusive cell rectangle."""
    state = sheet_state()
    sheet = state.sheet
    assert sheet is not None
    view, _ = view_for(state)
    sheet_view = view.sheet_view
    sheet_view.refresh(sheet, 320, 220)
    a1 = at(ROW_LABELS + 20, HEAD + FORMULA + 8)
    b2 = at(ROW_LABELS + 70, HEAD + FORMULA + ROW + 8)
    sheet_view._pan_start(event(kind=ft.PointerDeviceType.MOUSE, local_position=b2.local_position))
    sheet_view._pan(event(kind=ft.PointerDeviceType.MOUSE, local_position=a1.local_position))
    assert sheet.selection() == (0, 1, 1, 2)

    sheet_view._tap(a1)
    shifted, _ = view_for(state, shift=lambda: True)
    shifted.body_size = lambda: (320.0, 220.0)
    shifted.refresh()
    shifted.sheet_view._tap(b2)
    assert sheet.selection() == (0, 1, 1, 2)


def test_column_heading_tap_selects_a_column_and_double_tap_edits_its_name():
    """FR-SHEET-007: headings select columns; double-tap opens the name cell."""
    state = sheet_state()
    sheet = state.sheet
    assert sheet is not None
    view, _ = view_for(state)
    view.sheet_view.refresh(sheet, 320, 220)
    view.sheet_view._tap(at(ROW_LABELS + 70, HEAD // 2))
    assert sheet.whole == "column"
    assert sheet.cursor == (1, NAME_ROW)
    view.sheet_view._double_tap(at(ROW_LABELS + 70, HEAD // 2))
    assert sheet.editing == ""


def test_clicking_the_entry_bar_starts_editing():
    state = sheet_state()
    view, recorder = view_for(state)
    state.run(Binding("insert", "42"))
    state.run(Binding("enter"))
    state.run(Binding("up"))
    view.refresh()
    row = view.sheet_view.bar.content
    assert isinstance(row, ft.Row)
    entry = row.controls[1]
    assert isinstance(entry, ft.Container)
    assert entry.on_click is not None
    view.sheet_view._edit_bar(event())
    assert ("sheet_bar", "") in recorder.done
    assert state.sheet is not None
    assert state.sheet.editing == "42"


def test_dragging_a_formula_range_keeps_the_edited_cell():
    state = sheet_state()
    view, _ = view_for(state)
    sheet = state.sheet
    assert sheet is not None
    sheet.go((2, 1))
    state.run(Binding("insert", "=sum("))
    view.refresh()
    start = event(
        local_position=ft.Offset(ROW_LABELS + 5, HEAD + FORMULA + 2),
        kind=ft.PointerDeviceType.MOUSE,
    )
    view.sheet_view._pan_start(start)
    view.sheet_view._pan(
        event(
            local_position=ft.Offset(ROW_LABELS + 5, HEAD + FORMULA + 2 * ROW + 2),
            local_delta=None,
        )
    )
    assert sheet.cursor == (2, 1)
    assert sheet.editing == "=sum(a1:a3"
    assert sheet.screen().reference == (0, 1, 0, 3)


def test_a_mouse_drag_selects():
    """Run 2, E4: a drag from C1 to D2 selects C1:D2."""
    state = sheet_state()
    view, _ = view_for(state)
    view.refresh()
    sheet_view = view.sheet_view
    start = event(
        local_position=ft.Offset(ROW_LABELS + 64 * 2 + 5, HEAD + FORMULA + 2),
        kind=ft.PointerDeviceType.MOUSE,
    )
    sheet_view._pan_start(start)
    sheet_view._pan(
        event(
            local_position=ft.Offset(ROW_LABELS + 64 * 3 + 5, HEAD + FORMULA + ROW + 2),
            local_delta=None,
        )
    )
    assert state.sheet is not None
    assert state.sheet.address() == "C1:D2"


def test_a_dialog_shows_with_its_buttons():
    state = sheet_state()
    view, recorder = view_for(state)
    state.run(Binding("insert", "={1,2}"))
    state.run(Binding("enter"))
    view.refresh()
    assert view.sheet_view.dialog.visible
    assert "Syntax Error in Cell: a1" in texts(view.sheet_view.dialog)
    recorder("sheet_ok", "")
    view.refresh()
    assert not view.sheet_view.dialog.visible
    sheet = state.sheet
    assert sheet is not None
    sheet.go((0, 1))
    state.run(Binding("sheet", "select_row"))
    state.run(Binding("copy"))
    sheet.go((0, 1))
    state.run(Binding("paste"))  # over data: Data Loss, with Cancel
    view.refresh()
    assert "Cancel" in texts(view.sheet_view.dialog)


def test_the_app_tells_the_view_its_size():
    page = FakePage(1200, 700)
    app = App(Shell(cast("ft.Page", page), DEVICE), AppState(mode=Mode.HANDHELD))
    app.arrange()
    handheld = app.body_size()
    app.state.mode = Mode.COMPUTER
    app.arrange()
    computer = app.body_size()
    app.state.system.computer_keypad = True
    app.arrange()
    with_keys = app.body_size()
    assert handheld[0] < computer[0]
    assert with_keys[0] < computer[0]


def test_a_sheet_view_on_its_own():
    actions: list[tuple[str, str]] = []
    view = SheetView(
        CalculatorView(AppState()).theme, lambda a, b: actions.append((a, b)), lambda: 1.0
    )
    view._tap(at(10, 10))  # no sheet drawn yet: nothing
    assert actions == []


def test_the_sheet_uses_the_screens_colours():
    """Cell text was drawn in the dark theme's light ink on the light screen, so it did not
    show (fixed after slice 3b)."""
    theme = CalculatorView(AppState()).theme
    colours = sheet_colours(theme)
    assert colours["ink"] == theme.screen_text
    assert colours["ink"] != theme.screen
