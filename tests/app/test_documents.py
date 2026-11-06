"""Document actions from keys, the variable list and the settings model (FR-DOC-001, FR-DOC-002)."""

from dataclasses import replace

from cassim.app.state import AppState
from cassim.core.settings import Angle


def enter(state: AppState, text: str) -> None:
    for char in text:
        state.key_event(char)
    state.key_event("Enter")


def test_ctrl_i_adds_a_page_and_alt_arrows_move() -> None:
    state = AppState()
    state.key_event("i", ctrl=True)
    assert state.screen().title == "1.2"
    state.key_event("Arrow Left", alt=True)
    assert state.screen().title == "1.1"
    state.key_event("Arrow Right", alt=True)
    assert state.screen().title == "1.2"


def test_variable_list_shows_values_and_functions() -> None:
    state = AppState()
    enter(state, "a:=5")
    enter(state, "f(x):=x^2")
    session = state.document.problems[0].session
    rows = {row.name: row for row in session.variables()}
    assert rows["a"].text == "5"
    assert not rows["a"].is_function
    assert rows["f"].text == "f(x)"
    assert rows["f"].is_function


def test_variables_belong_to_the_problem() -> None:
    state = AppState()
    enter(state, "a:=5")
    state.run_action("add_problem")
    assert state.document.problems[1].session.variables() == []


def test_document_settings_dialog_applies_everywhere() -> None:
    state = AppState()
    state.run_action("add_problem")
    state.document.use(replace(state.document.settings, angle=Angle.DEGREE))
    assert all(p.session.settings.angle is Angle.DEGREE for p in state.document.problems)
    assert state.screen().status.startswith("DEG")


def test_delete_page_action() -> None:
    state = AppState()
    state.run_action("add_page")
    state.run_action("delete_page")
    assert len(state.document.sorter()) == 1
