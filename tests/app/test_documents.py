"""Document actions from keys, the variable list and the settings model (FR-DOC-001, FR-DOC-002)."""

from dataclasses import replace

from cassim.app.state import MATH_SIZES, AppState, Mode, System
from cassim.core.settings import Angle
from cassim.device.screen import thumbnail


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


def test_page_move_and_undo_redo() -> None:
    """Pages reorder within a Problem, and every structural change can be undone (FR-DOC-001)."""
    state = AppState()
    enter(state, "a:=1")
    state.run_action("add_page")
    enter(state, "2")
    state.run_action("add_page")
    enter(state, "3")
    document = state.document
    texts = lambda: [  # noqa: E731
        page.calculator.history[0].text for page in document.problems[0].pages if page.calculator
    ]
    assert texts() == ["a:=1", "2", "3"]
    state.run_action("move_page", "-2")
    assert texts() == ["3", "a:=1", "2"]
    assert document.page == 0
    state.run_action("undo_pages")
    assert texts() == ["a:=1", "2", "3"]
    assert document.page == 2
    state.run_action("redo_pages")
    assert texts() == ["3", "a:=1", "2"]
    state.run_action("delete_page")
    assert len(document.problems[0].pages) == 2
    state.run_action("undo_pages")
    assert texts() == ["3", "a:=1", "2"]  # the deleted page is back with its content


def test_undo_restores_a_deleted_problem_and_is_empty_at_start() -> None:
    state = AppState()
    assert not state.document.undo()
    state.run_action("add_problem")
    state.run_action("delete_page")  # removes the new Problem
    assert len(state.document.problems) == 1
    state.run_action("undo_pages")
    assert len(state.document.problems) == 2
    state.run_action("move_problem", "-1")
    assert state.document.problem == 0


def test_page_thumbnail_shows_the_last_lines() -> None:
    state = AppState()
    for text in ("1+1", "2+2"):
        enter(state, text)
    assert thumbnail(state.document.current)[-1] == "4"
    state.run_action("add_page")
    assert thumbnail(state.document.current) == ()


def test_system_settings_start_in_the_state_mode() -> None:
    state = AppState(mode=Mode.HANDHELD)
    assert state.system.start_mode is Mode.HANDHELD
    assert state.system.math_size == MATH_SIZES["Normal"]


def test_new_document_and_replace_document() -> None:
    state = AppState()
    enter(state, "a:=5")
    state.run_action("new_document")
    assert state.document.current.calculator is not None
    assert state.document.current.calculator.history == []
    assert state.screen().menu is None


def test_file_menu_new_by_keys() -> None:
    state = AppState()
    enter(state, "1+1")
    for key in ("F4", "1", "1"):  # Doc > File > New
        state.key_event(key)
    assert state.document.current.calculator is not None
    assert state.document.current.calculator.history == []


def test_file_menu_asks_for_the_file_dialogs() -> None:
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "1", "2", "F4", "1", "4"):  # File > 2 Open, File > 4 Save
        state.key_event(key)
    assert asked == ["open_file", "save_file"]


def test_system_settings_round_trip_and_fall_back() -> None:
    """FR-DOC-002: System Settings survive a reload; a bad saved value gives the defaults."""
    system = System(Mode.HANDHELD, MATH_SIZES["Large"])
    assert System.loads(system.dumps()) == system
    for bad in ("", "[]", '{"start_mode": "x", "math_size": 20}', '{"start_mode": "computer"}'):
        assert System.loads(bad) == System()
    assert System.loads('{"start_mode": "handheld", "math_size": 99}').math_size == 20
