# Requirements traced here: FR-CALC-004, FR-CALC-005
"""The mouse on the Calculator page, from emulator check 6, run 5 (H3)."""

import asyncio
from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import cast

import flet as ft
import flet.canvas as cv
import pytest

from cassim.app.theme import DARK
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.ui import views as views_module
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import CalculatorView


def walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        yield from walk(content)
    for child in getattr(control, "controls", None) or []:
        yield from walk(child)


def _recorded() -> tuple[CalculatorView, list[tuple[str, str]], AppState]:
    state = AppState()
    actions: list[tuple[str, str]] = []
    view = CalculatorView(state, on_action=lambda action, arg: actions.append((action, arg)))
    return view, actions, state


def test_one_two_and_three_clicks_place_select_a_token_and_select_all() -> None:
    """H3 b: a double-click selects a token, a triple-click the whole line."""
    view, actions, _ = _recorded()
    for _ in range(3):
        view._click([], 2)
    assert actions == [("place", ":2"), ("select_token", ":2"), ("select_all", "")]


def test_clicks_far_apart_in_time_or_place_are_single(monkeypatch: pytest.MonkeyPatch) -> None:
    view, actions, _ = _recorded()
    view._click([], 1)
    view._click([], 2)  # somewhere else
    monkeypatch.setattr(views_module, "MULTI_CLICK", -1.0)
    view._click([], 2)  # too late
    assert [action for action, _ in actions] == ["place", "place", "place"]


def test_a_history_line_click_then_clicks_inside_it_count_on() -> None:
    """The first click picks the line (a cursor in it); the clicks after land in its editor."""
    view, actions, _ = _recorded()
    view._click_line("0:entry")
    view._recall_click([], 1)
    view._recall_click([], 1)
    assert actions == [
        ("recall_at", "0:entry"),
        ("recall_token", ":1"),
        ("select_all", ""),
    ]


def test_shift_click_in_a_history_line_extends() -> None:
    state = AppState()
    actions: list[tuple[str, str]] = []
    view = CalculatorView(
        state, on_action=lambda action, arg: actions.append((action, arg)), shift=lambda: True
    )
    view._recall_click([], 2)
    assert actions == [("recall_extend", ":2")]


def _shapes(control: ft.Control) -> list[list[tuple[object, ...]]]:
    """What each canvas in `control` draws: the kind and place of every shape."""
    return [
        [(type(s).__name__, getattr(s, "x", 0), getattr(s, "y", 0)) for s in canvas.shapes]
        for canvas in walk(control)
        if isinstance(canvas, cv.Canvas)
    ]


def test_a_clicked_history_line_shows_a_cursor_in_the_same_drawing() -> None:
    """H3 a: no highlight over the item; a cursor in it. The row is the same canvas drawing it
    was before, with a cursor on a layer above, so nothing in it changes size or place
    (decision 0038)."""
    state = AppState()
    for char in "2+3":
        state.key_event(char)
    state.key_event("Enter")
    view = CalculatorView(state, on_action=state.run_action)
    view.refresh()
    plain = _shapes(view.history)
    assert not [c for c in walk(view.history) if isinstance(c, ft.Markdown)]  # no LaTeX rows
    state.run_action("recall_at", "0:entry")
    view.refresh()
    calculator = calculator_on(state.document.current)
    assert calculator.recall == (0, "entry")
    drawn = _shapes(view.history)
    assert len(drawn) == len(plain) + 1  # the cursor's layer
    assert all(shapes in drawn for shapes in plain)  # the maths is untouched

    def cursors(canvases: list[list[tuple[object, ...]]]) -> int:
        return sum([kind for kind, _x, _y in shapes] == ["Rect"] for shapes in canvases)

    assert cursors(drawn) == cursors(plain) + 1  # the entry line's, and now the row's
    highlighted = [
        c for c in walk(view.history) if isinstance(c, ft.Container) and c.bgcolor == DARK.selection
    ]
    assert not highlighted


def test_a_tap_in_a_row_with_a_cursor_moves_the_cursor_to_it() -> None:
    """H3 a, b: the row takes its own taps, and a tap lands where it was made."""
    state = AppState()
    for char in "2+3":
        state.key_event(char)
    state.key_event("Enter")
    state.run_action("recall_at", "0:entry")
    actions: list[tuple[str, str]] = []
    view = CalculatorView(state, on_action=lambda action, arg: actions.append((action, arg)))
    view.refresh()
    row = next(  # the picked row is above the entry line
        c
        for c in walk(view.history)
        if isinstance(c, ft.GestureDetector) and c.on_tap_up is not None
    )
    size = state.math_size
    event = cast("ft.TapEvent", SimpleNamespace(local_position=SimpleNamespace(x=0.6 * size, y=9)))
    cast("Callable[[ft.TapEvent], None]", row.on_tap_up)(event)
    assert actions == [("recall_place", ":1")]  # just right of the `2`, half an em wide


# ---- E5: the history layout (H9) --------------------------------------------------------------


def _texts(control: ft.Control) -> list[str]:
    return [str(c.value) for c in walk(control) if isinstance(c, ft.Text)]


def _marks(control: ft.Control) -> list[str]:
    """The ◂ and ▸ that show: each keeps its room beside a cut line, unseen when not needed."""
    return [
        str(c.value)
        for c in walk(control)
        if isinstance(c, ft.Text) and c.value in ("◂", "▸") and c.opacity != 0
    ]


def _laid_out(*entries: str, width: float = 320.0) -> CalculatorView:
    state = AppState()
    calculator = calculator_on(state.document.current)
    for entry in entries:
        calculator.editor.insert_linear(entry)
        state.key_event("Enter")
    view = CalculatorView(state, on_action=state.run_action)
    view.body_size = lambda: (width, 200.0)
    view.refresh()
    return view


def test_pairs_alternate_a_band_and_the_plain_screen() -> None:
    """H9 e: the first pair banded, the next plain, no rule between them."""
    view = _laid_out("1", "2", "3")
    pairs = [c for c in view.history.controls[1:4] if isinstance(c, ft.Container)]
    band = views_module.history_band(DARK)
    assert [pair.bgcolor for pair in pairs] == [band, None, band]
    assert all(pair.border is None for pair in pairs)


def test_a_long_input_is_cut_with_a_mark_and_its_result_has_its_own_line() -> None:
    """H9 b: the 45-character sum is not wrapped; ▸ ends it, and the result moves under it."""
    view = _laid_out("1234567+2345678+3456789+4567891+5678912+67891")
    pair = view.history.controls[1]
    assert isinstance(pair, ft.Container)
    assert isinstance(pair.content, ft.Column)  # input and result on lines of their own
    assert _marks(pair) == ["▸"]
    result = pair.content.controls[1]
    assert isinstance(result, ft.GestureDetector)
    assert isinstance(result.content, ft.Container)
    assert result.content.alignment == ft.Alignment.CENTER_LEFT  # from the left edge (H9 d)


def test_a_long_result_is_cut_on_its_own_line() -> None:
    """H9 d: `seq(n,n,1,25)` gives a list longer than the screen."""
    view = _laid_out("seq(n,n,1,25)")
    pair = view.history.controls[1]
    assert isinstance(pair, ft.Container)
    assert isinstance(pair.content, ft.Column)
    assert _marks(pair.content.controls[1]) == ["▸"]


def test_a_long_entry_line_scrolls_sideways_with_marks() -> None:
    """H3 f: ◂ at the left while the cursor is at the end, ▸ at the right when it is at the
    start, and both with the cursor in the middle of the line."""
    state = AppState()
    calculator = calculator_on(state.document.current)
    calculator.editor.insert_linear("1111111+2222222+3333333+4444444+5555555+6666666+7777777+")
    view = CalculatorView(state, on_action=state.run_action)
    view.refresh()
    assert _marks(view.entry) == ["◂"]
    calculator.editor.home()
    view.refresh()
    assert _marks(view.entry) == ["▸"]
    for _ in range(28):
        calculator.editor.right()
    view.refresh()
    assert _marks(view.entry) == ["◂", "▸"]
    calculator.editor.clear()
    view.refresh()
    assert _marks(view.entry) == []


def test_a_long_line_scrolls_only_when_the_cursor_nears_an_edge() -> None:
    """The line stays put while the cursor moves in the middle of the window, and follows it
    within `margin` of either edge, never past the line's own ends."""
    offset = views_module.scroll_offset
    assert offset(100, 300, 1000, 400, 60) == 100  # in the middle: no move
    assert offset(100, 480, 1000, 400, 60) == 140  # near the right edge: the line moves left
    assert offset(100, 130, 1000, 400, 60) == 70  # near the left edge: it moves right
    assert offset(100, 10, 1000, 400, 60) == 0  # not past the start
    assert offset(500, 990, 1000, 400, 60) == 600  # nor past the end


def test_the_entry_line_is_scrolled_to_its_cursor_after_the_redraw() -> None:
    state = AppState()
    calculator = calculator_on(state.document.current)
    calculator.editor.insert_linear("1111111+2222222+3333333+4444444+5555555+6666666+7777777+")
    view = CalculatorView(state, on_action=state.run_action)
    view.refresh()
    strip = view._strips["entry"]
    assert strip.due
    assert strip.offset == views_module.TO_END  # the cursor is at the end
    calculator.editor.home()
    view.refresh()
    assert view._strips["entry"] is strip  # the same row: it keeps its place between redraws
    assert strip.offset == 0


def test_a_wide_screen_keeps_an_entry_and_its_result_on_one_line() -> None:
    """The Computer view's pane is wider than the Handheld's screen: what needs two lines at
    320 pixels shares one at 900, the entry at the left and the result at the right."""
    entry = "1234567+2345678+3456789+4567891"
    narrow = _laid_out(entry).history.controls[1]
    wide = _laid_out(entry, width=900.0).history.controls[1]
    assert isinstance(narrow, ft.Container)
    assert isinstance(wide, ft.Container)
    assert isinstance(narrow.content, ft.Column)
    assert isinstance(wide.content, ft.Row)
    assert _marks(wide) == []


def test_a_fraction_is_measured_as_it_is_drawn_not_by_its_characters() -> None:
    """`(x+1)/(x+2)` is 11 characters of text but a stacked fraction about three wide."""
    from cassim.device.editor_ast import text_ems  # noqa: PLC0415

    assert text_ems("(x+1)/(x+2)") < text_ems("x+1+x+2")


def test_stepping_back_from_the_end_of_a_long_line_does_not_move_it() -> None:
    """The line is at its end; one Left keeps it there (the cursor is still well inside)."""
    state = AppState()
    calculator = calculator_on(state.document.current)
    calculator.editor.insert_linear("1111111+2222222+3333333+4444444+5555555+6666666+7777777+")
    view = CalculatorView(state, on_action=state.run_action)
    view.refresh()
    calculator.editor.left()
    view.refresh()
    strip = view._strips["entry"]
    assert strip.offset > 0
    assert _marks(view.entry) == ["◂"]  # nothing more to the right: it is still at its end
    before = strip.offset
    calculator.editor.left()
    view.refresh()
    assert strip.offset == before


def test_a_sideways_scroll_that_the_window_does_not_answer_is_dropped() -> None:
    """A busy window can time out on `scroll_to` (Flet raises RuntimeError); the next redraw
    scrolls again, so the failure must not surface."""

    class Row:
        async def scroll_to(self, **_: object) -> None:
            raise RuntimeError("TimeoutException after 0:00:10: ... Row(1).scroll_to")

    strip = views_module.Strip()
    strip.row, strip.offset = cast("ft.Row", Row()), 10.0
    asyncio.run(views_module._scroll_strip(strip))


def test_a_sideways_scroll_is_made_twice_to_where_the_line_should_be_by_then() -> None:
    """The first scroll can run before the longer line is laid out, so it is made again a
    moment later; if a later key has moved the cursor meanwhile, the second goes there."""
    strip = views_module.Strip()
    asked: list[float] = []

    class Row:
        async def scroll_to(self, *, offset: float, duration: int) -> None:
            asked.append(offset)
            strip.offset = 42.0  # another key came while this one settled

    strip.row, strip.offset = cast("ft.Row", Row()), views_module.TO_END
    asyncio.run(views_module._scroll_strip(strip))
    assert asked == [views_module.TO_END, 42.0]
