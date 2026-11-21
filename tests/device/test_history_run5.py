# Requirements traced here: FR-CALC-001, FR-CALC-004, FR-CALC-005, FR-CALC-006
"""Calculator behaviour from emulator check 6, run 5 (docs/testing/emulator-calc6-results.md)."""

from cassim.core.session import Session
from cassim.device.keys import Binding, Keyboard
from cassim.devices.nspire import keymap as nspire
from cassim.devices.nspire.pages.calculator import Calculator


def make() -> Calculator:
    return Calculator(Session())


def enter(calc: Calculator, text: str) -> None:
    for char in text:
        calc.perform(Binding("insert", char))
    calc.perform(Binding("enter"))


def pairs(calc: Calculator) -> list[tuple[str, str]]:
    return [(entry.text, entry.result.text) for entry in calc.history]


def keys(calc: Calculator, keyboard: Keyboard, *names: str) -> None:
    for name in names:
        binding = keyboard.press(name)
        if binding is not None:
            calc.perform(binding)


# ---- E1: an entry that starts with an operator works on Ans (H6 g, todo A5) -------------------


def test_an_entry_that_starts_with_plus_adds_to_ans() -> None:
    """H6 g: after `10`, `+1` is shown as `10+1` and gives 11; an empty Return then repeats it
    with the new answer, `11+1` = 12."""
    calc = make()
    enter(calc, "10")
    enter(calc, "+1")
    assert pairs(calc)[-1] == ("10+1", "11")
    calc.perform(Binding("enter"))
    assert pairs(calc)[-1] == ("11+1", "12")


def test_a_typed_minus_first_is_subtraction_from_ans() -> None:
    """The computer keyboard's `-` is the subtraction key: first on a line it takes Ans
    (editor check T1 i: `Ans−3/4`)."""
    calc = make()
    keyboard = Keyboard(nspire.COMPUTER)
    keys(calc, keyboard, "1", "0", "Enter", "-", "3", "Enter")
    assert pairs(calc)[-1] == ("10-3", "7")


def test_the_keypad_negative_key_first_is_a_negative_number() -> None:
    """The keypad's (−) key negates: `(−)3` is -3 even with an Ans to hand."""
    calc = make()
    keyboard = Keyboard(nspire.HANDHELD, nspire.MODIFIERS)
    keys(calc, keyboard, "1", "0", "enter", "neg", "3")
    assert calc.editor.linear() == "-3"
    keys(calc, keyboard, "enter")
    assert pairs(calc)[-1] == ("-3", "-3")
    keys(calc, keyboard, "minus", "2", "enter")  # the keypad's subtraction key takes Ans
    assert pairs(calc)[-1] == ("(-3)-2", "-5")


# ---- E4: Up then Return on a result brings down its stored value (H6 c, h) --------------------


def test_up_then_return_on_a_result_brings_down_the_stored_value() -> None:
    """H6 c, h: `3.4142135623731` comes down (not the 8 digits shown) and nothing is run."""
    calc = make()
    calc.perform(Binding("insert_linear", "√(2)+2."))
    calc.perform(Binding("enter"))
    assert calc.history[-1].result.text == "3.4142136"
    calc.perform(Binding("up"))
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "3.4142135623731"
    assert len(calc.history) == 1


# ---- E3: Clear History (H5 h) -----------------------------------------------------------------


def test_clear_history_empties_it_at_once_and_ans_is_then_undefined() -> None:
    """H5 h: no question asked; afterwards `ans` is an error, in CASSim's words, and the entry
    stays on the entry line with no pair added. Variables stay."""
    calc = make()
    enter(calc, "a:=5")
    enter(calc, "2+3")
    calc.perform(Binding("clear", "history"))
    assert not calc.history
    assert calc.recall is None
    enter(calc, "ans")
    assert calc.error is not None
    assert "Ans" in calc.error
    assert not calc.history
    calc.perform(Binding("escape"))
    assert calc.editor.linear() == "ans"
    calc.perform(Binding("clear"))
    enter(calc, "a")
    assert pairs(calc) == [("a", "5")]


def test_an_operator_first_on_a_fresh_page_is_an_undefined_ans() -> None:
    """Editor check T1 i: `-3/4` first on a fresh page asks for an Ans there is not."""
    calc = make()
    enter(calc, "-3")
    assert calc.error is not None
    assert not calc.history


def test_undo_brings_back_a_cleared_history() -> None:
    """The device greys Undo after Clear History (H5 h); CASSim keeps it."""
    calc = make()
    enter(calc, "2+3")
    enter(calc, "4+1")
    calc.perform(Binding("clear", "history"))
    calc.perform(Binding("undo"))
    assert pairs(calc) == [("2+3", "5"), ("4+1", "5")]
    enter(calc, "ans+1")
    assert pairs(calc)[-1] == ("5+1", "6")


def test_clear_history_with_nothing_to_clear_does_nothing() -> None:
    calc = make()
    calc.perform(Binding("clear", "history"))
    assert not calc.can_undo


# ---- E7: an empty template is a syntax error that stays on the entry line (E4) -----------------


def test_an_empty_derivative_template_is_a_syntax_error_and_stays() -> None:
    calc = make()
    calc.perform(Binding("template", "derivative"))
    calc.perform(Binding("enter"))
    assert calc.error is not None
    assert calc.error.startswith("Syntax")
    assert not calc.history
    calc.perform(Binding("escape"))  # OK: the template is still there
    assert calc.editor.linear() == "derivative(,)"


def test_show_warning_info_shows_the_picked_lines_warning() -> None:
    """H9 h, H3 j: the warning triangle's message, in a dialog titled Warning."""
    calc = make()
    calc.perform(Binding("insert_linear", "real(3+4*√(-1))"))
    calc.perform(Binding("enter"))
    assert calc.history[-1].result.warnings
    calc.show_warning_info()  # nothing picked: nothing to show
    assert calc.error is None
    calc.perform(Binding("up"))
    calc.show_warning_info()
    assert calc.error == calc.history[-1].result.warnings[0]
    assert calc.error_title == "Warning"
    calc.perform(Binding("escape"))
    assert calc.error is None
    assert calc.error_title == "Error"


# ---- E6: the mouse (H3) and the keypad's del on a template (F3) -------------------------------


def test_a_double_click_selects_a_token_in_the_entry_line() -> None:
    """H3 b: `:=` as one token; a name or a number as one."""
    calc = make()
    calc.perform(Binding("insert_linear", "a:=2+abc"))
    calc.perform(Binding("select_token", ":2"))  # between : and =
    assert calc.editor.selection() == [":", "="]
    calc.perform(Binding("select_token", ":6"))  # inside abc
    assert calc.editor.selection() == ["a", "b", "c"]
    calc.perform(Binding("select_token", ":8"))  # at the end: the token before it
    assert calc.editor.selection() == ["a", "b", "c"]
    calc.perform(Binding("select_token", "bad"))  # a malformed target is ignored


def test_a_double_click_in_a_picked_history_row_selects_a_token() -> None:
    calc = make()
    enter(calc, "a+1")
    calc.perform(Binding("recall_token", ":1"))  # nothing picked: nothing happens
    calc.perform(Binding("recall_at", "0:entry"))
    calc.perform(Binding("recall_token", ":1"))
    calc.perform(Binding("enter"))  # the selected part comes down
    assert calc.editor.linear() == "+"


def test_a_triple_click_in_a_history_row_selects_the_whole_input() -> None:
    calc = make()
    enter(calc, "a+1")
    calc.perform(Binding("recall_at", "0:entry"))
    calc.perform(Binding("select_all"))
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "a+1"


def test_dragging_a_selection_moves_it_within_the_entry_line() -> None:
    """H3 k: `123456789` with 4567 selected, dropped at the end: `123894567`, still selected."""
    calc = make()
    calc.perform(Binding("insert_linear", "123456789"))
    calc.perform(Binding("place", ":3"))
    calc.perform(Binding("extend", ":7"))
    calc.perform(Binding("drop", ":5"))  # inside the selection: nothing
    calc.perform(Binding("drop", ":9"))
    assert calc.editor.linear() == "123894567"
    assert calc.editor.selection() == list("4567")
    calc.perform(Binding("drop", ":0"))
    assert calc.editor.linear() == "456712389"
    calc.perform(Binding("undo"))
    assert calc.editor.linear() == "123894567"
    calc.perform(Binding("drop", "bad"))


def test_the_keypad_del_takes_a_fraction_template_in_one_press() -> None:
    """F3: 7 over 8, Right, del: the line is empty. A computer's Backspace highlights first."""
    for key, left in (("del", ""), ("Backspace", "((7)/(8))")):
        calc = make()
        keyboard = (
            Keyboard(nspire.HANDHELD, nspire.MODIFIERS)
            if key == "del"
            else Keyboard(nspire.COMPUTER)
        )
        calc.perform(Binding("template", "fraction"))
        calc.perform(Binding("insert", "7"))
        calc.perform(Binding("down"))
        calc.perform(Binding("insert", "8"))
        calc.perform(Binding("right"))
        keys(calc, keyboard, key)
        assert calc.editor.linear() == left
    calc = make()
    calc.perform(Binding("insert", "7"))
    keys(calc, Keyboard(nspire.HANDHELD, nspire.MODIFIERS), "del")
    assert calc.editor.is_empty
