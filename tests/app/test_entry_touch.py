# Requirements traced here: NFR-PORT-002
"""Touch selection, list and matrix drawing, and the stretching radical (M2d, FR-CALC-004)."""

from collections.abc import Callable, Iterator, Sequence

import flet as ft

from cassim.app.theme import DARK
from cassim.device.editor import Editor, Kind
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.ui.entry import SELECTION, EntryLine, row_height
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import CalculatorView

type Target = tuple[tuple[tuple[int, int], ...], int]


def walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    children: list[ft.Control] = []
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        children.append(content)
    controls = getattr(control, "controls", None)
    if controls:
        children.extend(controls)
    for child in children:
        yield from walk(child)


def long_presses(editor: Editor) -> list[Target]:
    """Every target a long press on the entry line can produce, in drawing order."""
    held: list[Target] = []

    def hold(path: Sequence[tuple[int, int]], pos: int) -> None:
        held.append((tuple(path), pos))

    view = EntryLine(DARK, 20, lambda path, pos: None, hold=hold).build(editor)
    for control in walk(view):
        if isinstance(control, ft.GestureDetector) and control.on_long_press_start is not None:
            press: Callable[..., object] = control.on_long_press_start
            press(None)
    return held


def test_a_long_press_is_offered_wherever_a_tap_is() -> None:
    editor = Editor("1+")
    editor.insert_template(Kind.FRACTION)
    held = long_presses(editor)
    assert ((), 0) in held
    assert (((2, 0),), 0) in held
    assert (((2, 1),), 0) in held


def test_a_long_press_extends_the_selection_from_the_cursor() -> None:
    state = AppState()
    for key in "abcd":
        state.key_event(key)
    actions: list[tuple[str, str]] = []
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


def fills(control: ft.Control) -> list[str]:
    return [
        str(c.bgcolor)
        for c in walk(control)
        if isinstance(c, ft.Container) and c.bgcolor == SELECTION
    ]


def test_selected_matrix_rows_are_highlighted() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 3))
    assert fills(EntryLine(DARK, 20, lambda path, pos: None).build(editor)) == []
    editor.select_cells("row", 1)
    assert len(fills(EntryLine(DARK, 20, lambda path, pos: None).build(editor))) == 3
    editor.cell_sel = None
    editor.select_cells("col", 1)
    assert len(fills(EntryLine(DARK, 20, lambda path, pos: None).build(editor))) == 2


def test_a_list_is_drawn_with_braces_and_its_elements_are_targets() -> None:
    editor = Editor()
    editor.insert_template(Kind.LIST, (1, 3))
    view = EntryLine(DARK, 20, lambda path, pos: None).build(editor)
    texts = [c.value for c in walk(view) if isinstance(c, ft.Text)]
    assert "{" in texts
    assert "}" in texts
    assert texts.count(", ") == 2


class TestRowHeight:
    def test_plain_text_is_one_line(self):
        assert row_height(Editor("x+1").root) == 1

    def test_a_fraction_is_about_two_and_a_bit(self):
        editor = Editor()
        editor.insert_template(Kind.FRACTION)
        assert 2 < row_height(editor.root) < 2.6

    def test_it_adds_up_through_nesting(self):
        flat = Editor()
        flat.insert_template(Kind.FRACTION)
        tall = Editor()
        tall.insert_template(Kind.FRACTION)
        tall.insert_template(Kind.FRACTION)  # a fraction in the numerator
        assert row_height(tall.root) > row_height(flat.root) + 1

    def test_a_matrix_is_its_rows(self):
        editor = Editor()
        editor.insert_template(Kind.MATRIX, (3, 2))
        assert 3 <= row_height(editor.root) < 3.5

    def test_a_power_lifts_the_line(self):
        editor = Editor("x^2")
        assert 1.3 < row_height(editor.root) < 1.7


def test_the_radical_grows_with_its_radicand() -> None:
    def sign_size(editor: Editor) -> float:
        view = EntryLine(DARK, 20, lambda path, pos: None).build(editor)
        return max(c.size or 0 for c in walk(view) if isinstance(c, ft.Text) and c.value == "√")

    plain = Editor()
    plain.insert("√")
    plain.insert_text("49")
    tall = Editor()
    tall.insert("√")
    tall.insert_template(Kind.FRACTION)
    assert sign_size(tall) > 1.8 * sign_size(plain)
    assert sign_size(plain) == 20 * 1.15
