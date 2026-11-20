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
