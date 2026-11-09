# Requirements traced here: FR-CALC-001, FR-CALC-002, FR-CALC-006
"""The Calculator page driven by key names (FR-DEV-001, FR-CALC-004, FR-DEV-007)."""

from pathlib import Path

import pytest

from cassim import device
from cassim.device.calculator import Calculator
from cassim.device.document import Document
from cassim.device.keys import Binding, Keyboard
from cassim.profiles import nspire


def computer(*keys: str) -> Calculator:
    """Press computer keys; a multi-character key name is written in full, text is typed."""
    page = Calculator()
    keyboard = Keyboard(nspire.COMPUTER)
    for key in keys:
        press(page, keyboard, key)
    return page


def handheld(*keys: str) -> Calculator:
    page = Calculator()
    keyboard = Keyboard(nspire.HANDHELD, nspire.MODIFIERS)
    for key in keys:
        press(page, keyboard, key)
    return page


def press(page: Calculator, keyboard: Keyboard, key: str) -> None:
    binding = keyboard.press(key)
    if binding is not None:
        page.perform(binding)


def type_text(page: Calculator, keyboard: Keyboard, text: str) -> None:
    for char in text:
        press(page, keyboard, char)


def test_keyboard_types_a_printable_character_with_no_binding():
    assert Keyboard(nspire.COMPUTER).press("x") == Binding("insert", "x")
    assert Keyboard(nspire.COMPUTER).press("ctrl+q") is None


def test_keypad_modifier_applies_to_the_next_key_only():
    keyboard = Keyboard(nspire.HANDHELD, nspire.MODIFIERS)
    assert keyboard.press("ctrl") is None
    assert keyboard.press("div") == Binding("template", "fraction")
    assert keyboard.press("div") == Binding("insert", "/")  # the modifier has gone
    keyboard.press("ctrl")
    keyboard.press("ctrl")  # pressed twice: cancelled
    assert keyboard.press("div") == Binding("insert", "/")


def test_return_evaluates_and_moves_the_entry_to_the_history():
    page = computer("1", "+", "2", "Enter")
    assert page.editor.is_empty
    assert [(e.text, e.result.text) for e in page.history] == [("1+2", "3")]


def test_a_typed_slash_stays_linear_and_evaluates():
    page = computer("1", "/", "3", "x", "Enter")
    assert page.history[0].text == "1/3x"
    assert page.history[0].result.text == "x/3"


@pytest.mark.parametrize("fraction", ["ctrl+/"])
def test_ctrl_slash_makes_the_fraction_template_on_a_computer(fraction):
    page = computer("1", "2", ".", "5", fraction, "3")
    assert page.editor.linear() == "((12.5)/(3))"
    assert page.editor.path == [(0, 1)]  # the cursor is in the denominator


def test_ctrl_div_makes_the_fraction_template_on_the_keypad():
    page = handheld("1", "ctrl", "div", "3")
    assert page.editor.linear() == "((1)/(3))"


def test_square_key_opens_an_exponent_holding_2():
    page = handheld("x", "square", "right", "plus", "1")
    assert page.editor.linear() == "x^(2)+1"


def test_ctrl_enter_and_keypad_ctrl_enter_give_the_decimal_result():
    for page in (computer("1", "/", "3", "ctrl+Enter"), handheld("1", "div", "3", "ctrl", "enter")):
        assert page.history[0].result.text == "0.33333333"
        assert page.history[0].approximate


def test_an_error_dialog_takes_the_next_key_and_keeps_the_entry():
    page = computer("2", "+", "/", "3", "Enter")
    assert page.error is not None
    assert not page.history
    page.perform(Binding("enter"))  # dismisses the dialog and does nothing else
    assert page.error is None
    assert page.editor.linear() == "2+/3"


def test_up_on_an_empty_line_walks_the_history_and_return_copies():
    page = computer("2", "+", "2", "Enter", "3", "*", "3", "Enter")
    page.perform(Binding("up"))
    assert page.recall == (1, "result")
    page.perform(Binding("up"))
    assert page.recall == (1, "entry")
    page.perform(Binding("up"))
    assert page.recall == (0, "result")
    page.perform(Binding("down"))
    assert page.recall == (1, "entry")
    page.perform(Binding("enter"))  # copies the entry, does not evaluate it
    assert page.editor.linear() == "3*3"
    assert len(page.history) == 2
    page.perform(Binding("enter"))
    assert len(page.history) == 3


def test_down_past_the_last_row_leaves_recall():
    page = computer("1", "Enter", "ArrowUp", "ArrowDown")
    assert page.recall is None


def test_up_does_not_recall_while_there_is_something_in_the_entry():
    page = computer("1", "Enter", "x", "ArrowUp")
    assert page.recall is None


def test_a_selected_result_is_copied_into_the_entry():
    page = computer("2", "+", "2", "Enter", "ArrowUp", "Enter")
    assert page.editor.linear() == "4"


def test_undo_and_redo_step_through_operator_groups():
    """`ab+c` is three steps: `c`, `+`, `ab` (emulator, shortcuts S7 d)."""
    page = computer("a", "b", "+", "c")
    undo = Binding("undo")
    states = []
    for _ in range(3):
        page.perform(undo)
        states.append(page.editor.linear())
    assert states == ["ab+", "ab", ""]
    redo = Binding("redo")
    states = []
    for _ in range(3):
        page.perform(redo)
        states.append(page.editor.linear())
    assert states == ["ab", "ab+", "ab+c"]


def test_typing_after_undo_drops_the_redo_steps():
    page = computer("a", "b", "+", "c")
    page.perform(Binding("undo"))
    page.perform(Binding("insert", "d"))
    page.perform(Binding("redo"))
    assert page.editor.linear() == "ab+d"


def test_undo_with_nothing_to_undo_does_nothing():
    page = computer("ctrl+z")
    assert page.editor.is_empty


def test_undo_restores_a_template():
    page = computer("1", "ctrl+/", "2", "ctrl+z", "ctrl+z")
    assert page.editor.linear() == "1"


def test_unknown_action_is_an_error():
    with pytest.raises(ValueError, match="unknown action"):
        Calculator().perform(Binding("fly"))


def test_framework_does_not_import_a_profile():
    """FR-DEV-007: profiles depend on the device package, never the reverse."""
    for module in Path(device.__file__).parent.glob("*.py"):
        assert "cassim.profiles" not in module.read_text(encoding="utf-8"), module.name


def test_user_and_builtin_functions_are_bold_once_defined() -> None:
    """A function is bold when something defines it: a built-in, or `f(x):=...` in the Problem."""
    page = computer(*"f(x):=x^2", "Enter")
    typed = Keyboard(nspire.COMPUTER)
    for key in "f(2)":
        press(page, typed, key)
    assert r"\mathbf{f}" in page.editor.latex(is_function=page.session.is_function)
    page.editor.clear()
    for key in "g(2)":
        press(page, typed, key)
    assert r"\mathbf" not in page.editor.latex(is_function=page.session.is_function)
    page.editor.clear()
    for key in "solve(":
        press(page, typed, key)
    assert r"\mathbf{s}" in page.editor.latex(is_function=page.session.is_function)


def test_shift_arrows_select_and_typing_replaces() -> None:
    """Computer shift+arrows, ctrl+A; the keypad's shift then an arrow does the same (S5)."""
    page = computer(*"abc", "shift+ArrowLeft", "shift+ArrowLeft", "9")
    assert page.editor.linear() == "a9"
    page = computer(*"a+b", "ctrl+a", "7")
    assert page.editor.linear() == "7"
    page = handheld(*"abc", "shift", "left", "shift", "left", "del")
    assert page.editor.linear() == "a"


def test_undo_restores_a_replaced_selection() -> None:
    page = computer(*"abc", "ctrl+a", "9", "ctrl+z")
    assert page.editor.linear() == "abc"


def test_ctrl_shift_arrows_select_words() -> None:
    page = computer(*"ab cd", "ctrl+shift+ArrowLeft", "ctrl+shift+ArrowLeft")
    assert page.editor.span == (0, 5)
    page = computer(*"ab cd", "ctrl+shift+ArrowLeft", "x")
    assert page.editor.linear() == "ab x"


def test_copy_cut_and_paste_across_pages_and_into_a_template() -> None:
    """S7: a pasted fraction stays stacked; the clipboard is shared by the pages of a document."""
    document = Document()
    first = document.current.calculator
    assert first is not None
    keyboard = Keyboard(nspire.COMPUTER)
    for key in ("1", "ctrl+/", "2", "ArrowRight", "shift+ArrowLeft", "ctrl+c"):
        press(first, keyboard, key)
    document.add_page()
    second = document.current.calculator
    assert second is not None
    for key in ("ctrl+v", "+", "ctrl+v"):
        press(second, keyboard, key)
    assert second.editor.linear() == "((1)/(2))+((1)/(2))"
    assert second.editor.latex(cursor=False).count(r"\frac") == 2


def test_cut_is_undoable_and_paste_of_other_text_is_typed() -> None:
    page = computer(*"abc", "shift+ArrowLeft", "ctrl+x")
    assert page.editor.linear() == "ab"
    assert page.clipboard.text == "c"
    press(page, Keyboard(nspire.COMPUTER), "ctrl+z")
    assert page.editor.linear() == "abc"
    page.perform(Binding("paste", "x\ny"))  # text from outside the calculator
    assert page.editor.linear() == "abx y"  # undo brought back the selection, which paste replaces


def test_recalling_an_entry_keeps_its_templates() -> None:
    """Up then Enter puts a fraction back as a fraction, not as `(1)/(2)` text (FR-CALC-004)."""
    calc = Calculator()
    calc.perform(Binding("template", "fraction"))
    calc.perform(Binding("insert", "1"))
    calc.perform(Binding("tab"))
    calc.perform(Binding("insert", "2"))
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))  # the entry row
    calc.perform(Binding("enter"))
    assert calc.editor.root
    assert not isinstance(calc.editor.root[0], str)  # a template, not characters


def test_clicking_a_history_row_picks_it_and_a_second_click_recalls_it() -> None:
    calc = Calculator()
    for char in "1+2":
        calc.perform(Binding("insert", char))
    calc.perform(Binding("enter"))
    calc.perform(Binding("recall_at", "0:entry"))
    assert calc.recall == (0, "entry")
    assert calc.editor.linear() == ""
    calc.perform(Binding("recall_at", "0:entry"))
    assert calc.editor.linear() == "1+2"
    calc.perform(Binding("recall_at", "9:entry"))  # no such row: ignored


def _type(calc: Calculator, text: str) -> None:
    for char in text:
        calc.perform(Binding("insert", char))


def test_a_picked_row_has_a_cursor_that_selects_parts() -> None:
    """Up picks a row; Left and Shift+Left move and select inside it; Enter brings only the
    selected part down to the entry line (FR-CALC-004)."""
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))  # the entry row `12+34`
    assert calc.recall_editor is not None
    calc.perform(Binding("select_left"))
    calc.perform(Binding("select_left"))  # "34"
    calc.perform(Binding("enter"))
    assert calc.recall is None
    assert calc.editor.linear() == "34"


def test_enter_on_a_picked_row_without_a_selection_brings_the_whole_row() -> None:
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))
    calc.perform(Binding("left"))  # moves inside the row, which stays picked
    assert calc.recall is not None
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "12+34"


def test_clicking_inside_a_picked_row_places_the_cursor() -> None:
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))
    calc.perform(Binding("recall_place", "0"))
    calc.perform(Binding("recall_extend", "2"))  # selects "12"
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "12"


def test_enter_repeats_an_entry_that_uses_ans() -> None:
    """Newton-style: an entry with `ans`, then Enter again and again, each with the new Ans."""
    calc = Calculator()
    _type(calc, "1")
    calc.perform(Binding("enter"))
    _type(calc, "ans+1")
    calc.perform(Binding("enter"))
    calc.perform(Binding("enter"))  # empty entry: the same expression with the new Ans
    calc.perform(Binding("enter"))
    assert [entry.result.text for entry in calc.history] == ["1", "2", "3", "4"]


def test_enter_on_an_empty_line_does_nothing_without_ans() -> None:
    calc = Calculator()
    _type(calc, "2+2")
    calc.perform(Binding("enter"))
    calc.perform(Binding("enter"))
    assert len(calc.history) == 1
