# Requirements traced here: FR-CALC-004, NFR-PORT-002
"""Maths lines painted on a canvas (decision 0038): the entry line, a picked history row, a graph
entry and a sheet cell. A click anywhere is turned into a place by the layout; the cursor and the
selection are layers of their own. The controls are built without a page and each handler is
called the way Flet would call it."""

from collections.abc import Callable, Iterator, Sequence
from types import SimpleNamespace
from typing import cast

import flet as ft
import flet.canvas as cv
import pytest

from cassim.app.math_canvas import DEFAULT_STYLE, MathLine, draw
from cassim.app.theme import DARK
from cassim.device.editor import Editor, Kind
from cassim.device.editor_ast import row_from_text
from cassim.device.keys import Action
from cassim.devices.nspire.pages.calculator import calculator_of, calculator_on
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import CalculatorView

type Target = tuple[tuple[tuple[int, int], ...], int]


def walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        yield from walk(content)
    for child in getattr(control, "controls", None) or []:
        yield from walk(child)


def canvases(control: ft.Control) -> list[cv.Canvas]:
    return [c for c in walk(control) if isinstance(c, cv.Canvas)]


def event(x: float, y: float) -> ft.TapEvent:
    return cast("ft.TapEvent", SimpleNamespace(local_position=SimpleNamespace(x=x, y=y)))


class Line:
    """A built line and what its clicks and long presses reported."""

    def __init__(self, editor: Editor, *, active: bool = True) -> None:
        self.clicked: list[Target] = []
        self.held: list[Target] = []
        self.dropped: list[Target] = []
        self.line = MathLine(DARK, 20, self._into(self.clicked), hold=self._into(self.held))
        self.line.drop = self._into(self.dropped)
        self.view = cast("ft.GestureDetector", self.line.build(editor, active=active))

    @staticmethod
    def _into(seen: list[Target]) -> Callable[[Sequence[tuple[int, int]], int], None]:
        return lambda path, pos: seen.append((tuple(path), pos))

    def tap(self, path: Sequence[tuple[int, int]], pos: int, nudge: float = 0.0) -> Target:
        """Tap where the cursor is drawn for a place, `nudge` pixels to the right."""
        x, y = self.line.point_at(path, pos)
        cast("Callable[[ft.TapEvent], None]", self.view.on_tap_up)(event(x + nudge, y))
        return self.clicked[-1]


def test_a_tap_beside_a_character_puts_the_cursor_on_that_side() -> None:
    line = Line(Editor("abc"))
    for pos in range(4):
        assert line.tap([], pos) == ((), pos)
    assert line.tap([], 3, nudge=40) == ((), 3)  # past the end of the row: its end


def test_an_empty_entry_still_takes_a_click() -> None:
    line = Line(Editor())
    assert line.tap([], 0) == ((), 0)
    assert line.line.width > 0
    assert line.line.height > 20  # a line of text tall, with nothing typed


def test_a_fractions_slots_and_the_fraction_itself_take_taps() -> None:
    editor = Editor("1+")
    editor.insert("2")
    editor.insert_template(Kind.FRACTION)
    editor.insert("3")
    line = Line(editor)
    assert line.tap([(2, 0)], 0, nudge=1) == (((2, 0),), 0)  # inside the digit, its left half
    assert line.tap([(2, 0)], 1, nudge=-1) == (((2, 0),), 1)
    assert line.tap([(2, 1)], 0, nudge=1) == (((2, 1),), 0)
    assert line.tap([(2, 1)], 1, nudge=-1) == (((2, 1),), 1)
    assert line.tap([], 2, nudge=-1) == ((), 2)
    assert line.tap([], 3, nudge=1) == ((), 3)


def test_an_empty_slot_takes_a_tap() -> None:
    editor = Editor()
    editor.insert_template(Kind.FRACTION)
    line = Line(editor)
    assert line.tap([(0, 0)], 0) == (((0, 0),), 0)
    assert line.tap([(0, 1)], 0) == (((0, 1),), 0)


def test_nested_templates_and_matrix_cells_take_taps() -> None:
    editor = Editor("x")
    editor.insert("^")
    editor.insert("1")
    editor.insert_template(Kind.FRACTION)
    editor.insert("2")
    line = Line(editor)
    assert line.tap([(1, 0), (0, 0)], 0, nudge=-0.5) == (((1, 0), (0, 0)), 0)
    assert line.tap([(1, 0), (0, 1)], 1, nudge=0.5) == (((1, 0), (0, 1)), 1)
    matrix = Editor()
    matrix.insert_template(Kind.MATRIX, (3, 3))
    line = Line(matrix)
    for cell in range(9):
        assert line.tap([(0, cell)], 0) == (((0, cell),), 0)


def test_a_radicand_takes_taps_and_so_does_the_place_before_its_root() -> None:
    editor = Editor()
    editor.insert("√")
    editor.insert_text("49")
    line = Line(editor)
    assert line.tap([(0, 0)], 1) == (((0, 0),), 1)
    assert line.tap([], 0) == ((), 0)


def test_a_long_press_is_taken_wherever_a_tap_is() -> None:
    editor = Editor("1+")
    editor.insert_template(Kind.FRACTION)
    line = Line(editor)
    press = cast("Callable[[ft.TapEvent], None]", line.view.on_long_press_start)
    for path, pos in ([], 0), ([(2, 0)], 0), ([(2, 1)], 0):
        press(event(*line.line.point_at(path, pos)))
        assert line.held[-1] == (tuple(path), pos)
    assert line.clicked == []


@pytest.mark.parametrize("kind", list(Kind))
def test_every_kind_is_painted(kind: Kind) -> None:
    editor = Editor()
    editor.insert_template(kind)
    assert canvases(Line(editor).view)


def test_the_maths_is_few_shapes_and_the_cursor_is_not_among_them() -> None:
    """A plain line is one text shape, however long; the cursor is a canvas of its own above."""
    line = Line(Editor("12345+67890"))
    content, cursor = canvases(line.view)
    assert len(content.shapes) <= 3  # the digits either side of the spaced `+`
    assert [type(shape) for shape in cursor.shapes] == [cv.Rect]
    assert not canvases(Line(Editor("12"), active=False).view)[1:]  # inactive: no cursor layer


def test_moving_the_cursor_changes_nothing_in_the_maths() -> None:
    """The jiggle this replaces: a cursor drawn as part of the maths moved what was beside it."""
    editor = Editor()
    editor.root = row_from_text("x=-((1+√(2))^(1/3))/2+1/(2*(1+√(2))^(1/3))")
    editor.home()

    def drawn() -> tuple[list[tuple[object, ...]], float, float]:
        shapes: list[tuple[object, ...]]
        line = Line(editor)
        content = canvases(line.view)[-2]
        shapes = [
            (type(s).__name__, getattr(s, "x", None), getattr(s, "y", None), getattr(s, "value", 0))
            for s in content.shapes
        ]
        return shapes, line.line.width, line.line.height

    first = drawn()
    for _ in range(30):
        editor.right()
        assert drawn() == first
    editor.select_left()
    editor.select_left()
    assert drawn() == first


def test_a_selection_is_a_layer_under_the_maths() -> None:
    editor = Editor("1234")
    editor.place([], 1)
    editor.place([], 3, extend=True)
    under, _content, cursor = canvases(Line(editor).view)
    (box,) = under.shapes
    assert isinstance(box, cv.Rect)
    assert box.paint is not None
    assert box.paint.color == DEFAULT_STYLE.selection
    assert box.width == pytest.approx(20.0)  # two digits, half an em each
    (bar,) = cursor.shapes
    assert isinstance(bar, cv.Rect)
    assert bar.paint is not None
    assert bar.paint.color == DEFAULT_STYLE.cursor_in_selection


def test_selected_matrix_rows_and_columns_are_highlighted_cell_by_cell() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 3))
    assert len(canvases(Line(editor).view)) == 2  # no selection layer
    editor.select_cells("row", 1)
    assert len(canvases(Line(editor).view)[0].shapes) == 3
    editor.cell_sel = None
    editor.select_cells("col", 1)
    assert len(canvases(Line(editor).view)[0].shapes) == 2


def test_a_selection_dragged_to_a_place_is_dropped_there() -> None:
    """H3 k: selected text dragged onto a place moves there; a drag from elsewhere does not."""
    editor = Editor("1234")
    editor.place([], 1)
    editor.place([], 3, extend=True)
    line = Line(editor)
    start = cast("Callable[[ft.TapEvent], None]", line.view.on_pan_start)
    end = cast("Callable[[ft.TapEvent], None]", line.view.on_pan_end)
    inside = line.line.point_at([], 2)
    start(event(*inside))
    end(event(*line.line.point_at([], 4)))
    assert line.dropped == [((), 4)]
    start(event(*line.line.point_at([], 0)))  # not on the selection
    end(event(*line.line.point_at([], 4)))
    assert line.dropped == [((), 4)]
    plain = Line(Editor("1234"))
    assert plain.view.on_pan_start is None  # nothing selected: nothing to drag


def test_the_line_says_how_wide_it_is_and_where_its_cursor_is() -> None:
    """A long line is scrolled to keep its cursor in view from these, not from an estimate."""
    editor = Editor("1234")
    line = Line(editor).line
    assert line.width == pytest.approx(4 * 10 + 4)  # four digits at half an em, and the padding
    assert line.cursor_x == pytest.approx(42)
    editor.home()
    assert Line(editor).line.cursor_x == pytest.approx(2)


def test_a_row_is_drawn_without_a_cursor() -> None:
    canvas = draw(row_from_text("1/2"), DARK, 20)
    assert isinstance(canvas, cv.Canvas)
    assert canvas.width == pytest.approx((0.35 + 0.24) * 20 + 4)
    assert not any(isinstance(shape, cv.Rect) and shape.width == 2 for shape in canvas.shapes)


# ---- through the Calculator view ----------------------------------------------------------------


def test_a_click_reaches_the_editor_through_the_view() -> None:
    state = AppState()
    for key in "abc":
        state.key_event(key)
    state.run_action("place", ":1")
    assert calculator_of(state.document.current) is not None
    assert calculator_on(state.document.current).editor.pos == 1
    state.run_action("extend", ":3")
    assert calculator_on(state.document.current).editor.span == (1, 3)


def test_a_long_press_extends_the_selection_from_the_cursor() -> None:
    state = AppState()
    for key in "abcd":
        state.key_event(key)
    actions: list[tuple[Action, str]] = []
    view = CalculatorView(state, on_action=lambda action, arg: actions.append((action, arg)))
    view.refresh()
    view._hold([], 1)
    assert actions == [("extend", ":1")]
    state.run_action(*actions[0])
    editor = calculator_on(state.document.current).editor
    assert editor.span == (1, 4)


def test_the_keypad_shift_turns_the_next_tap_into_an_extend() -> None:
    state = AppState()
    for key in "abc":
        state.key_event(key)
    actions: list[tuple[str, str]] = []
    view = CalculatorView(state, on_action=lambda action, arg: actions.append((action, arg)))
    view._click([], 1)
    assert actions == [("place", ":1")]
    state.press_keypad("shift")
    assert state.pending == "shift"
    view._click([], 0)
    assert actions[-1] == ("extend", ":0")
    assert state.pending == ""  # used up, as for any other key
    view._click([], 2)
    assert actions[-1] == ("place", ":2")


def test_the_calculators_entry_line_is_a_canvas() -> None:
    state = AppState()
    for key in "1+2":
        state.key_event(key)
    view = CalculatorView(state, on_action=state.run_action)
    view.refresh()
    assert canvases(view.entry)
