# Requirements traced here: FR-CALC-004, FR-DEV-001
"""Behaviour found in the emulator shortcut follow-up (docs/testing/emulator-shortcuts-results.md:
S7 e to g, S5 b2, S8 a follow-up)."""

from cassim.device.editor import Editor, Kind, Template
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.state import AppState, Mode


def typed(state: AppState, keys: str) -> None:
    for char in keys:
        state.key_event(char)


def line(state: AppState) -> str:
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    return calculator.editor.linear()


def test_undo_steps_through_a_template_and_its_slots() -> None:
    """S7 e: `1 ctrl+/ 2 Right + 3`; the template and each slot entry are separate steps."""
    state = AppState()
    typed(state, "1")
    state.key_event("/", ctrl=True)
    typed(state, "2")
    state.key_event("Arrow Right")
    typed(state, "+3")
    calculator = calculator_of(state.document.current)
    assert calculator is not None

    def denominator() -> list[object]:
        fraction = calculator.editor.root[0]
        assert isinstance(fraction, Template)
        assert fraction.kind is Kind.FRACTION
        return list(fraction.slots[1])

    state.key_event("z", ctrl=True)  # the 3 goes
    assert len(calculator.editor.root) == 2
    state.key_event("z", ctrl=True)  # the + goes
    assert len(calculator.editor.root) == 1
    assert denominator() == ["2"]
    state.key_event("z", ctrl=True)  # the 2 goes: 1 over an empty denominator
    assert denominator() == []
    state.key_event("z", ctrl=True)  # the template goes
    assert calculator.editor.root == ["1"]
    state.key_event("y", ctrl=True)
    assert denominator() == []
    state.key_event("y", ctrl=True)
    assert denominator() == ["2"]


def test_undo_with_nothing_typed_undoes_the_page_insert() -> None:
    """S7 f: on a fresh page ctrl+Z takes the page away and ctrl+Y brings it back."""
    state = AppState()
    state.key_event("i", ctrl=True)
    state.key_event("1")  # Add Calculator
    assert state.screen().title == "1.2"
    state.key_event("z", ctrl=True)
    assert len(state.document.sorter()) == 1
    state.key_event("y", ctrl=True)
    assert state.screen().title == "1.2"


def test_undo_goes_through_the_typing_before_the_page() -> None:
    state = AppState()
    state.key_event("i", ctrl=True)
    state.key_event("1")  # Add Calculator
    typed(state, "5")
    state.key_event("z", ctrl=True)
    assert line(state) == ""
    assert len(state.document.sorter()) == 2  # that press undid the typing
    state.key_event("z", ctrl=True)
    assert len(state.document.sorter()) == 1


def test_undo_steps_back_over_the_evaluation_before_the_page_insert() -> None:
    """H1 a, b: the first ctrl+Z takes the result away, the typing and then the page follow."""
    state = AppState()
    state.key_event("i", ctrl=True)
    state.key_event("1")  # Add Calculator
    typed(state, "2+3")
    state.key_event("Enter")
    state.key_event("z", ctrl=True)
    assert line(state) == "2+3"
    assert len(state.document.sorter()) == 2
    for _ in range(3):  # 3, +, 2
        state.key_event("z", ctrl=True)
    assert line(state) == ""
    state.key_event("z", ctrl=True)
    assert len(state.document.sorter()) == 1


def test_the_keypad_has_ctrl_z_and_ctrl_y_and_shift_esc_redoes() -> None:
    """Redo is ctrl+Y, and the keypad's shift then esc (run 5, H8 b); the computer's
    shift+Escape does not redo (S7 g)."""
    state = AppState(mode=Mode.HANDHELD)
    for key in ("a", "plus", "b"):
        state.press_keypad(key)
    for key in ("ctrl", "z"):
        state.press_keypad(key)
    assert line(state) == "a+"
    state.key_event("Escape", shift=True)
    assert line(state) == "a+"
    for key in ("shift", "esc"):
        state.press_keypad(key)
    assert line(state) == "a+b"
    for key in ("ctrl", "z", "ctrl", "y"):
        state.press_keypad(key)
    assert line(state) == "a+b"


def test_ctrl_7_picks_the_first_row_and_ctrl_1_returns_to_the_entry_line() -> None:
    """S5 b2, on the keypad."""
    state = AppState(mode=Mode.HANDHELD)
    for entry in ("1", "2", "3"):
        state.press_keypad(entry)
        state.press_keypad("enter")
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    for key in ("ctrl", "7"):
        state.press_keypad(key)
    assert calculator.recall == (0, "entry")
    for key in ("ctrl", "1"):
        state.press_keypad(key)
    assert calculator.recall is None
    state.press_keypad("4")
    assert line(state) == "4"


def test_ctrl_7_on_an_empty_history_does_nothing() -> None:
    state = AppState(mode=Mode.HANDHELD)
    for key in ("ctrl", "7"):
        state.press_keypad(key)
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    assert calculator.recall is None


def three_quarters() -> Editor:
    """3/4 as a stacked fraction, cursor in front of it."""
    editor = Editor("3")
    editor.insert_template(Kind.FRACTION)
    editor.insert_text("4")
    editor.path, editor.pos = [], 0
    return editor


def test_second_delete_keeps_the_first_slot_selected() -> None:
    """S8 a follow-up: in front of 3/4, Delete selects the fraction; Delete again leaves `3`,
    selected."""
    editor = three_quarters()
    editor.delete()
    assert editor.selected
    assert len(editor.root) == 1
    editor.delete()
    assert editor.root == ["3"]
    assert editor.selection() == ["3"]
    editor.insert("x")  # typing replaces what is selected
    assert editor.root == ["x"]


def test_second_delete_on_a_template_with_an_empty_first_slot_removes_it() -> None:
    editor = Editor()
    editor.insert_template(Kind.ROOT)
    editor.path, editor.pos = [], 0
    editor.delete()
    editor.delete()
    assert editor.is_empty
    assert editor.anchor is None


def test_backspace_on_a_highlighted_template_still_deletes_it() -> None:
    """Decision 0017: Backspace after a template highlights it, then deletes all of it."""
    editor = three_quarters()
    editor.pos = 1
    editor.backspace()
    assert editor.selected
    editor.backspace()
    assert editor.is_empty
