# Requirements traced here: NFR-PORT-002
"""The clickable entry line (FR-CALC-004, decision 0019): every click region maps to a target.

The controls are built without a page, then each tap handler is called the way Flet would call it.
"""

from collections.abc import Callable, Iterator, Sequence

import flet as ft

from cassim.app.entry import EntryLine
from cassim.app.state import AppState
from cassim.app.theme import DARK
from cassim.device.calculator import calculator_of, calculator_on
from cassim.device.editor import Editor, Kind

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


def targets(editor: Editor) -> list[Target]:
    """Every target a tap on the entry line can produce, in drawing order."""
    clicked: list[Target] = []

    def click(path: Sequence[tuple[int, int]], pos: int) -> None:
        clicked.append((tuple(path), pos))

    view = EntryLine(DARK, 20, click).build(editor)
    for control in walk(view):
        if isinstance(control, ft.GestureDetector) and control.on_tap is not None:
            tap: Callable[..., object] = control.on_tap
            tap(None)
    return clicked


def test_a_plain_row_has_a_half_for_each_side_of_each_character() -> None:
    clicked = targets(Editor("abc"))
    for pos in range(4):
        assert ((), pos) in clicked
    assert ((), 3) in clicked  # also the click past the end of the row


def test_an_empty_entry_still_takes_a_click() -> None:
    assert ((), 0) in targets(Editor())


def test_fraction_slots_and_the_fraction_itself_are_targets() -> None:
    editor = Editor("1+")
    editor.insert("2")
    editor.insert_template(Kind.FRACTION)
    editor.insert("3")
    clicked = targets(editor)
    assert (((2, 0),), 0) in clicked
    assert (((2, 0),), 1) in clicked
    assert (((2, 1),), 0) in clicked
    assert (((2, 1),), 1) in clicked
    assert ((), 2) in clicked
    assert ((), 3) in clicked


def test_an_empty_slot_takes_a_click_at_its_start() -> None:
    editor = Editor()
    editor.insert_template(Kind.FRACTION)
    assert (((0, 0),), 0) in targets(editor)
    assert (((0, 1),), 0) in targets(editor)


def test_nested_templates_and_matrix_cells_are_targets() -> None:
    editor = Editor("x")
    editor.insert("^")
    editor.insert("1")
    editor.insert_template(Kind.FRACTION)
    editor.insert("2")
    clicked = targets(editor)
    assert (((1, 0), (0, 0)), 0) in clicked  # numerator of the fraction in the exponent
    assert (((1, 0), (0, 1)), 1) in clicked
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (3, 3))
    clicked = targets(editor)
    for cell in range(9):
        assert (((0, cell),), 0) in clicked


def test_root_radicand_is_a_target() -> None:
    editor = Editor()
    editor.insert("√")
    editor.insert_text("49")
    clicked = targets(editor)
    assert (((0, 0),), 1) in clicked
    assert ((), 0) in clicked
    assert ((), 1) in clicked


def test_a_click_reaches_the_editor_through_the_view() -> None:
    state = AppState()
    for key in "abc":
        state.key_event(key)
    state.run_action("place", ":1")
    assert calculator_of(state.document.current) is not None
    assert calculator_on(state.document.current).editor.pos == 1
    state.run_action("extend", ":3")
    assert calculator_on(state.document.current).editor.span == (1, 3)
