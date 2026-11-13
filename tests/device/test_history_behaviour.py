# Requirements traced here: FR-CALC-004
"""Behaviour from emulator check 3 (docs/testing/emulator-history-results.md, run 2026-11-10)."""

from cassim.app.state import AppState
from cassim.core.session import Session
from cassim.device.calculator import Calculator, calculator_of
from cassim.device.keys import Binding
from cassim.devices.nspire.document import loads
from cassim.doc.serialize import dumps


def make() -> Calculator:
    return Calculator(Session())


def enter(calc: Calculator, text: str) -> None:
    if "^" in text:  # a power opens an exponent; paste it as the parser reads it
        calc.perform(Binding("insert_linear", text))
    else:
        for char in text:
            calc.perform(Binding("insert", char))
    calc.perform(Binding("enter"))


def texts(calc: Calculator) -> list[str]:
    return [entry.result.text for entry in calc.history]


def test_undo_takes_back_an_evaluation_and_redo_returns_it() -> None:
    """H1 a, c: the pair goes, the input returns with the cursor at its end; redo restores it."""
    calc = make()
    enter(calc, "2+3")
    calc.perform(Binding("undo"))
    assert not calc.history
    assert calc.editor.linear() == "2+3"
    assert calc.editor.pos == 3
    calc.perform(Binding("redo"))
    assert texts(calc) == ["5"]
    assert calc.editor.is_empty


def test_after_undoing_an_evaluation_undo_goes_on_through_the_typing() -> None:
    """H1 d: the first press takes the last result, later ones undo that entry's typing."""
    calc = make()
    enter(calc, "1")
    enter(calc, "2+3")
    calc.perform(Binding("undo"))
    assert texts(calc) == ["1"]
    assert calc.editor.linear() == "2+3"
    calc.perform(Binding("undo"))
    assert calc.editor.linear() == "2+"


def test_undo_does_not_undo_a_store() -> None:
    """H1 f: the variable keeps its value after the evaluation that set it is undone."""
    calc = make()
    enter(calc, "5→a")
    calc.perform(Binding("undo"))
    enter(calc, "a")
    assert texts(calc) == ["5"]


def test_deleting_a_pair_can_be_undone() -> None:
    """H1 h, H5 i."""
    calc = make()
    enter(calc, "1+1")
    enter(calc, "2+2")
    calc.perform(Binding("up"))
    calc.perform(Binding("up"))  # the second entry
    calc.perform(Binding("backspace"))
    assert texts(calc) == ["2"]
    calc.perform(Binding("undo"))
    assert texts(calc) == ["2", "4"]


def test_ans_is_shown_as_the_value_it_had_and_undo_brings_back_the_entry_as_typed() -> None:
    """H1 g."""
    calc = make()
    enter(calc, "2+3")
    enter(calc, "ans*2")
    assert calc.history[-1].text == "5*2"
    assert texts(calc) == ["5", "10"]
    calc.perform(Binding("undo"))
    assert calc.editor.linear() == "ans*2"


def test_a_value_that_is_not_a_plain_number_is_bracketed() -> None:
    calc = make()
    enter(calc, "1/3")
    enter(calc, "ans^2")
    assert "(" in calc.history[-1].text


def test_ans_shows_fourteen_digits() -> None:
    """H6 a: the history line has the full-precision previous value, not the 8 digits shown."""
    calc = make()
    enter(calc, "1/3.")
    enter(calc, "ans*2")
    shown = calc.history[-1].text
    assert shown.endswith("*2")
    assert len(shown.split("*")[0].replace(".", "")) >= 12


def test_empty_enter_runs_newtons_method_again() -> None:
    """H6 a: the entry is repeated as typed, so each press uses the new Ans."""
    calc = make()
    enter(calc, "f(x):=x^2-2")
    enter(calc, "df(x):=derivative(f(x),x)")
    enter(calc, "1.0")
    enter(calc, "ans-f(ans)/df(ans)")
    for _ in range(4):
        calc.perform(Binding("enter"))
    assert texts(calc)[-5:] == ["1.5", "1.4166667", "1.4142157", "1.4142136", "1.4142136"]


def test_ans_follows_the_history_after_undo() -> None:
    """H5 g."""
    calc = make()
    enter(calc, "5")
    enter(calc, "7")
    calc.perform(Binding("undo"))
    calc.editor.clear()
    enter(calc, "ans")
    assert texts(calc)[-1] == "5"


def test_a_saved_document_keeps_ans_in_the_entry_and_has_no_undo() -> None:
    state = AppState()
    calc = calculator_of(state.document.current)
    assert calc is not None
    enter(calc, "2+3")
    enter(calc, "ans*2")
    loaded = loads(dumps(state.document))
    again = calculator_of(loaded.current)
    assert again is not None
    assert [e.text for e in again.history] == ["2+3", "5*2"]
    assert not again.can_undo  # loading is not something to undo
    again.perform(Binding("enter"))  # the saved entry still has `ans`: 10 times 2
    assert texts(again)[-1] == "20"


def test_home_with_a_history_line_picked_goes_to_the_first_line() -> None:
    """H2 c."""
    state = AppState()
    calc = calculator_of(state.document.current)
    assert calc is not None
    enter(calc, "1")
    enter(calc, "2")
    state.key_event("ArrowUp")
    state.key_event("Home")
    assert calc.recall == (0, "entry")
