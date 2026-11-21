# Requirements traced here: FR-CALC-001, FR-CALC-002, FR-CALC-006
"""The Calculator page driven by key names (FR-DEV-001, FR-CALC-004, FR-DEV-007)."""

from pathlib import Path
from typing import cast

import pytest

from cassim import device
from cassim.device.editor import Editor
from cassim.device.keys import Action, Binding, Keyboard
from cassim.devices.nspire import keymap as nspire
from cassim.devices.nspire.document import Document
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of
from cassim.devices.nspire.screen import render
from cassim.devices.nspire.ui.state import AppState


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


def test_an_error_dialog_takes_the_next_key_and_the_entry_stays_in_the_history():
    """H1 j: after the dialog the history keeps the entry, its result the message in quotes."""
    page = computer("2", "+", "/", "3", "Enter")
    assert page.error is not None
    page.perform(Binding("enter"))  # dismisses the dialog and does nothing else
    assert page.error is None
    assert page.editor.is_empty
    assert page.history[-1].text == "2+/3"
    assert page.history[-1].result.text.startswith('"')
    assert page.history[-1].result.error is not None


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
        Calculator().perform(Binding(cast("Action", "fly")))


def test_framework_does_not_import_a_profile():
    """FR-DEV-007: devices depend on the device framework, never the reverse."""
    for module in Path(device.__file__).parent.glob("*.py"):
        assert "cassim.devices" not in module.read_text(encoding="utf-8"), module.name


def test_defined_names_are_bold_and_catalog_names_upright() -> None:
    """FR-CALC-003: a name turns bold once the Problem defines it (a function or any value);
    a Catalog function is upright, and an undefined name stays italic."""
    page = computer(*"f(x):=x^2", "Enter", *"a:=3", "Enter")
    typed = Keyboard(nspire.COMPUTER)

    def shown(text: str) -> str:
        page.editor.clear()
        for key in text:
            press(page, typed, key)
        return page.editor.latex(is_defined=page.session.is_defined)

    assert r"\mathbf{f}" in shown("f(2)")
    assert r"\mathbf{a}" in shown("a+1")
    assert r"\mathbf" not in shown("g(2)")
    assert r"\mathrm{s}" in shown("solve(")
    assert r"\mathbf" not in shown("solve(")


def test_the_history_draws_defined_names_italic_again() -> None:
    """FR-CALC-003, emulator check 4 A4 and A6: bold is only for the entry line. Once Return is
    pressed the history row draws every name of the user's italic, defined or not, while a
    Catalog name stays upright."""
    page = computer(*"a:=3", "Enter", *"solve(a*x=1,x)")
    assert r"\mathbf{a}" in page.editor.latex(is_defined=page.session.is_defined)
    press(page, Keyboard(nspire.COMPUTER), "Enter")
    latex = page.history[-1].latex
    assert r"\mathbf" not in latex
    assert r"\mathrm{s}" in latex


def test_catalog_names_take_the_catalogs_case_on_return() -> None:
    """Emulator check 4 A3: `SOLVE(`, `Sin(` and `define` stay as typed on the entry line and are
    spelled as the Catalog spells them in the history; a user's own name is left alone."""
    page = computer(*"SOLVE(x=1,x)")
    assert page.editor.linear() == "SOLVE(x=1,x)"
    press(page, Keyboard(nspire.COMPUTER), "Enter")
    assert page.history[-1].text == "solve(x=1,x)"
    page = computer(*"define k(x)=x", "Enter", *"Sin(x)+K(2)+BINOMCDF(5,0.5,2)", "Enter")
    assert page.history[0].text == "Define k(x)=x"
    assert page.history[1].text == "sin(x)+K(2)+binomCdf(5,0.5,2)"


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
    first = calculator_of(document.current)
    assert first is not None
    keyboard = Keyboard(nspire.COMPUTER)
    for key in ("1", "ctrl+/", "2", "ArrowRight", "shift+ArrowLeft", "ctrl+c"):
        press(first, keyboard, key)
    document.add_page()
    second = calculator_of(document.current)
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


def test_clicking_a_history_row_puts_a_cursor_in_it_and_return_recalls_it() -> None:
    """Run 5, H3 a, c: a click places a cursor (no highlight); a click inside the picked row
    moves that cursor and brings nothing down; Return does."""
    calc = Calculator()
    for char in "1+2":
        calc.perform(Binding("insert", char))
    calc.perform(Binding("enter"))
    calc.perform(Binding("recall_at", "0:entry"))
    assert calc.recall == (0, "entry")
    assert calc.recall_touched  # drawn with its own cursor, not highlighted whole
    assert calc.editor.linear() == ""
    calc.perform(Binding("recall_place", ":1"))
    assert calc.editor.linear() == ""
    calc.perform(Binding("enter"))
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
    calc.perform(Binding("end"))  # the cursor starts at the left of a picked row
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


def test_enter_on_an_empty_line_repeats_the_last_entry_with_or_without_ans() -> None:
    """H6 d: the entry is run again whether or not it uses Ans."""
    calc = Calculator()
    _type(calc, "2+2")
    calc.perform(Binding("enter"))
    calc.perform(Binding("enter"))
    assert [entry.result.text for entry in calc.history] == ["4", "4"]
    empty = Calculator()
    empty.perform(Binding("enter"))  # nothing to repeat
    assert not empty.history


def test_delete_on_a_picked_row_removes_that_entry_from_the_display() -> None:
    """Del or Backspace with a history row picked deletes the entry and its result. The input of
    the pair that takes its place is picked: Delete the next pair's, Backspace the previous pair's
    (run 5, H5 a, b, f, j)."""
    for key, picked in (("delete", (1, "entry")), ("backspace", (0, "entry"))):
        calc = Calculator()
        for line in ("1+1", "2+2", "3+3"):
            _type(calc, line)
            calc.perform(Binding("enter"))
        calc.perform(Binding("up"))
        calc.perform(Binding("up"))  # the entry `3+3`
        calc.perform(Binding("up"))
        calc.perform(Binding("up"))  # the entry `2+2`
        calc.perform(Binding(key))
        assert [entry.text for entry in calc.history] == ["1+1", "3+3"]
        assert calc.recall == picked


def test_del_again_deletes_the_lines_above_in_turn() -> None:
    """Deleting the last pair picks the input of the one before it (H5 a, e, g), so pressing Del
    again clears upwards until the history is empty."""
    calc = Calculator()
    for line in ("1+1", "2+2", "3+3"):
        _type(calc, line)
        calc.perform(Binding("enter"))
    calc.perform(Binding("up"))  # the result of `3+3`
    calc.perform(Binding("delete"))
    assert [entry.text for entry in calc.history] == ["1+1", "2+2"]
    assert calc.recall == (1, "entry")
    calc.perform(Binding("delete"))
    calc.perform(Binding("delete"))
    assert not calc.history
    assert calc.recall is None
    calc.perform(Binding("undo"))
    assert [entry.text for entry in calc.history] == ["1+1"]


def test_deleting_the_first_line_picks_the_next() -> None:
    for key in ("delete", "backspace"):
        calc = Calculator()
        for line in ("1+1", "2+2"):
            _type(calc, line)
            calc.perform(Binding("enter"))
        calc.perform(Binding("first_line"))
        calc.perform(Binding(key))
        assert [entry.text for entry in calc.history] == ["2+2"]
        assert calc.recall == (0, "entry")


def test_a_picked_row_draws_its_own_selection_once_moved_into() -> None:
    document = Document()
    calc = calculator_of(document.current)
    assert calc is not None
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))
    plain = render(document).lines[0]
    assert plain.selected
    assert not plain.part  # the whole item is highlighted, in its usual LaTeX
    calc.perform(Binding("select_right"))  # from the left of the row, where the cursor starts
    moved = render(document).lines[0]
    assert moved.part
    assert r"\fcolorbox" in moved.latex  # the selected part is highlighted inside the line


def test_del_on_an_empty_line_does_nothing() -> None:
    """H5 c: Del, Backspace and the keypad's del leave the history alone on an empty entry line."""
    calc = Calculator()
    _type(calc, "1+1")
    calc.perform(Binding("enter"))
    for action in ("backspace", "delete"):
        calc.perform(Binding(action))
    assert [entry.text for entry in calc.history] == ["1+1"]
    assert calc.editor.is_empty


def test_del_on_an_empty_line_with_no_history_does_nothing() -> None:
    calc = Calculator()
    calc.perform(Binding("delete"))
    assert calc.editor.is_empty


def test_enter_closes_open_brackets() -> None:
    calc = Calculator()
    _type(calc, "2*(3+4")
    assert calc.editor.missing_closers() == ")"
    calc.perform(Binding("enter"))
    assert calc.history[-1].text == "2*(3+4)"
    assert calc.history[-1].result.text == "14"


def test_brackets_in_text_and_already_closed_ones_are_left_alone() -> None:
    assert Editor("sin(2*(3+4").missing_closers() == "))"
    assert Editor("{1,[2").missing_closers() == "]}"
    assert Editor("(1+2)").missing_closers() == ""
    assert Editor('"a(b"').missing_closers() == ""


def test_entered_lines_use_proper_symbols() -> None:
    """After Enter, pi, sqrt( and exp( show as π, a root and ⅇ to a power; the value is the same."""
    calc = Calculator()
    _type(calc, "sqrt(2)*pi+exp(1)")
    calc.perform(Binding("enter"))
    entry = calc.history[-1]
    assert entry.text == "√(2)*π+ⅇ^(1)"
    assert r"\sqrt{2}" in entry.latex
    assert r"\pi" in entry.latex
    assert "pi" not in entry.latex.replace(r"\pi", "")
    assert [type(node).__name__ for node in entry.nodes].count("Template") == 2


def test_names_that_only_contain_pi_or_sqrt_are_left_alone() -> None:
    calc = Calculator()
    _type(calc, "spin+pie+sqrtx")
    calc.perform(Binding("enter"))
    assert calc.history[-1].text == "spin+pie+sqrtx"


def test_copy_from_a_picked_history_row_pastes_into_the_entry_line() -> None:
    """Ctrl+C on a picked row copies its selected part; Ctrl+V pastes it into the current input."""
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))
    calc.perform(Binding("end"))  # the cursor starts at the left of a picked row
    calc.perform(Binding("select_left"))
    calc.perform(Binding("select_left"))  # "34"
    calc.perform(Binding("copy"))
    assert calc.recall is not None  # copying leaves the row picked
    calc.perform(Binding("paste", ""))
    assert calc.recall is None
    assert calc.editor.linear() == "34"
    assert [entry.text for entry in calc.history] == ["12+34"]


def test_cut_on_a_picked_row_only_copies() -> None:
    calc = Calculator()
    _type(calc, "7+8")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))
    calc.perform(Binding("cut"))
    assert len(calc.history) == 1
    calc.perform(Binding("paste", ""))
    assert calc.editor.linear() == "7+8"


def test_the_keypad_has_ctrl_c_x_v() -> None:
    state = AppState()
    state.press_keypad("ctrl")
    state.press_keypad("c")
    pasted: list[str] = []
    state.request_paste = lambda: pasted.append("asked")
    state.press_keypad("ctrl")
    state.press_keypad("v")
    assert pasted == ["asked"]


def test_up_and_down_enter_a_row_at_its_left() -> None:
    """Simon, 2026-11-20: picking a row by Up or Down puts its cursor at the row's left."""
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    picked = calc.recall_editor
    assert picked is not None
    assert picked.pos == 0
    calc.perform(Binding("up"))
    calc.perform(Binding("down"))
    assert calc.recall_editor is not None
    assert calc.recall_editor.pos == 0


def test_clicking_a_row_puts_the_cursor_near_the_click() -> None:
    """Simon, 2026-11-20: a click on a row's maths picks it with the cursor near the click."""
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("recall_at", "0:entry@2.0"))  # past `12` (2 x 0.5 em) and `+` (1.22 em)
    picked = calc.recall_editor
    assert picked is not None
    assert calc.recall_touched  # the cursor shows at once
    assert picked.pos == 3
    calc.perform(Binding("recall_at", "0:entry@0.1"))  # a second click brings the row down
    assert calc.editor.linear() == "12+34"


def test_a_click_beyond_a_row_puts_the_cursor_at_its_end() -> None:
    calc = Calculator()
    _type(calc, "12+34")
    calc.perform(Binding("enter"))
    calc.perform(Binding("recall_at", "0:entry@40"))
    assert calc.recall_editor is not None
    assert calc.recall_editor.pos == 5
