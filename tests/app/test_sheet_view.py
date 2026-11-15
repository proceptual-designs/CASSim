# Requirements traced here: FR-SHEET-001, NFR-PERF-006, FR-DEV-004
"""The Lists & Spreadsheet page in the Flet view (slice 3b): it draws in the screen's place of
the history, keeps the canvases of layers that did not change, and turns taps, long presses,
drags and the wheel into sheet actions (decision 0031 item 7)."""

from types import SimpleNamespace
from typing import Any, cast

import flet as ft
from tests.app.test_splitter_drag import FakePage

from cassim.app.shell import Shell
from cassim.device.keys import Action, Binding
from cassim.devices.nspire import DEVICE
from cassim.devices.nspire.pages.spreadsheet import NAME_ROW
from cassim.devices.nspire.sheet_scene import FORMULA, HEAD, ROW, ROW_LABELS
from cassim.devices.nspire.ui.app import App
from cassim.devices.nspire.ui.sheet_view import SheetView, sheet_colours
from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.views import CalculatorView


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


def view_for(state: AppState) -> tuple[CalculatorView, Recorder]:
    recorder = Recorder(state)
    view = CalculatorView(state, on_action=recorder)
    view.body_size = lambda: (320.0, 220.0)
    return view, recorder


def test_the_sheet_draws_in_place_of_the_history():
    state = sheet_state()
    view, _ = view_for(state)
    state.run(Binding("insert", "7"))
    state.run(Binding("enter"))
    state.prepare()
    view.refresh()
    assert view.body.controls == [view.sheet_view.control]
    assert texts(view.sheet_view.bar) == ["A2", ""]
    state.run_action("prev_page")
    view.refresh()
    assert view.body.controls == [view.history]


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
