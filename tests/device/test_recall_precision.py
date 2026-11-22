# Requirements traced here: FR-CALC-004
"""A picked result shows its digits while the cursor moves through it; what Enter brings down
(and copy takes) is the value at full precision (owner, 2026-11-20)."""

from cassim.core.session import Session
from cassim.core.settings import Calc, Settings
from cassim.device.keys import Action, Binding
from cassim.devices.nspire.document import Document
from cassim.devices.nspire.pages.calculator import Calculator, calculator_on
from cassim.devices.nspire.screen import render


def calc_float3() -> Calculator:
    return Calculator(Session(Settings(calc=Calc.APPROXIMATE, digits="float3")))


def evaluate(calc: Calculator, text: str) -> None:
    calc.perform(Binding("insert_linear", text))
    calc.perform(Binding("enter"))


def keys(calc: Calculator, *names: Action) -> None:
    for name in names:
        calc.perform(Binding(name))


def test_moving_through_a_result_shows_its_digits_not_the_full_value() -> None:
    document = Document()
    calc = calculator_on(document.current)
    calc.session.settings = Settings(calc=Calc.APPROXIMATE, digits="float3")
    evaluate(calc, "1/3.")
    keys(calc, "up", "left")
    picked = calc.recall_editor
    assert picked is not None
    assert picked.linear() == "0.333"
    shown = render(document).lines[1].latex
    cursor = calc.editor.latex()  # the empty entry line is only a cursor, the same glyph
    assert shown.replace(cursor, "") == "0.333"


def test_enter_brings_down_the_full_value_after_moving() -> None:
    calc = calc_float3()
    evaluate(calc, "1/3.")
    keys(calc, "up", "left", "left", "enter")
    assert calc.editor.linear() == "0.33333333333333"


def test_a_selected_number_comes_down_at_full_precision() -> None:
    calc = calc_float3()
    evaluate(calc, "{1/3.,2/3.}")
    assert calc.history[-1].result.text == "{0.333,0.667}"
    keys(calc, "up", "end", "left")  # before the closing brace
    keys(calc, *repeat("select_left", 5))  # 0.667
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "0.66666666666667"


def test_a_selection_edge_inside_a_number_takes_the_whole_number() -> None:
    calc = calc_float3()
    evaluate(calc, "{1/3.,2/3.}")
    keys(calc, "up", "end", "left", "select_left", "select_left")  # "67" of 0.667
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "0.66666666666667"


def test_a_selection_across_numbers_keeps_what_is_between() -> None:
    calc = calc_float3()
    evaluate(calc, "{1/3.,2/3.}")
    keys(calc, "up", "home", "right", "select_right", "select_right")  # "0." of 0.333
    keys(calc, *repeat("select_right", 6))  # on through ",0.66"
    calc.perform(Binding("enter"))
    assert calc.editor.linear() == "0.33333333333333,0.66666666666667"


def test_a_number_inside_a_template_comes_down_at_full_precision() -> None:
    calc = calc_float3()
    evaluate(calc, "[1/3.,1]")
    keys(calc, "up", "home", "right")  # into the first cell
    picked = calc.recall_editor
    assert picked is not None
    assert picked.path
    keys(calc, "select_to_end", "enter")
    assert calc.editor.linear() == "0.33333333333333"


def test_copy_takes_the_full_value() -> None:
    calc = calc_float3()
    evaluate(calc, "2/3.")
    keys(calc, "up", "copy")
    assert calc.clipboard.text == "0.66666666666667"


def test_an_exact_result_comes_down_as_it_is_shown() -> None:
    calc = Calculator(Session())
    evaluate(calc, "1/3")
    keys(calc, "up", "left", "enter")
    assert calc.editor.linear() == "((1)/(3))"


def repeat(name: Action, times: int) -> list[Action]:
    return [name] * times
