"""Menus walked from keys: the Doc and Menu trees come from the profile (FR-DEV-001, FR-DEV-007)."""

import pytest

from cassim.app.state import AppState, Mode
from cassim.core.catalog import registry
from cassim.device.calculator import Calculator
from cassim.device.menu import MenuItem, MenuState, MenuView, item_keys
from cassim.profiles import nspire, nspire_syntax


def test_doc_menu_opens_and_lists_rows() -> None:
    state = AppState()
    state.key_event("F4")
    view = state.screen().menu
    assert view is not None
    assert view.title == "Doc"
    assert [(row.key, row.label) for row in view.rows] == [
        ("1", "File"),
        ("2", "Edit"),
        ("3", "View"),
        ("4", "Insert"),
        ("5", "Page Layout"),
        ("6", "Refresh Libraries"),
        ("7", "Settings & Status"),
        ("8", "Login…"),
        ("9", "Press-to-Test"),
    ]
    assert view.rows[0].selected
    assert view.rows[0].submenu


def test_doc_insert_problem_by_keys() -> None:
    """Doc > 4 Insert > 1 Problem, the route used on the simulator."""
    state = AppState()
    for key in ("F4", "4", "1"):
        state.key_event(key)
    assert state.screen().menu is None
    assert state.screen().title == "2.1"


def test_doc_insert_calculator_adds_a_page_in_the_problem() -> None:
    state = AppState()
    for key in ("F4", "4", "3"):
        state.key_event(key)
    assert state.screen().title == "1.2"


def test_arrows_and_enter_choose() -> None:
    state = AppState()
    state.key_event("F4")
    state.key_event("Arrow Down")  # Edit
    state.key_event("Arrow Down")  # View
    state.key_event("Arrow Down")  # Insert
    state.key_event("Enter")  # open it
    view = state.screen().menu
    assert view is not None
    assert view.title == "Doc > Insert"
    state.key_event("Enter")  # Problem
    assert state.screen().title == "2.1"


def test_escape_and_left_go_back() -> None:
    state = AppState()
    state.key_event("F4")
    state.key_event("4")
    assert state.screen().menu is not None
    state.key_event("Arrow Left")
    view = state.screen().menu
    assert view is not None
    assert view.title == "Doc"
    state.key_event("Escape")
    assert state.screen().menu is None


def test_menu_swallows_typing() -> None:
    state = AppState()
    state.key_event("F2")
    state.key_event("z")  # no such item
    state.key_event("Escape")
    assert state.document.current.calculator is not None
    assert state.document.current.calculator.editor.linear() == ""


def test_menu_item_types_a_command() -> None:
    state = AppState()
    for key in ("F2", "3", "1"):  # Menu > 3 Algebra > 1 Solve, as on the handheld
        state.key_event(key)
    assert state.document.current.calculator is not None
    assert state.document.current.calculator.editor.linear() == "solve("


def test_settings_item_asks_for_the_dialog() -> None:
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "7", "2"):
        state.key_event(key)
    assert asked == ["document_settings"]


def test_keypad_doc_and_esc_keys() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("doc")
    assert state.screen().menu is not None
    state.press_keypad("esc")
    assert state.screen().menu is None


def test_selection_wraps_and_explicit_keys_are_reserved() -> None:
    menu = MenuState(
        MenuItem("m", items=(MenuItem("a", "x"), MenuItem("b", "y", key="1"), MenuItem("c", "z")))
    )
    assert menu.keys() == ["2", "1", "3"]
    menu.press("up")
    assert menu.level.index == 2
    assert menu.press("enter") is not None
    assert not menu.open


def test_page_sorter_and_system_settings_ask_for_dialogs() -> None:
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "3", "3", "F4", "7", "3"):  # View > Page Sorter, Handheld Setup
        state.key_event(key)
    assert asked == ["page_sorter", "system_settings"]


# ---- touch and mouse, hints, the profile's trees (FR-DEV-001, FR-CALC-005, FR-CAT-004) ----------


def _menu(state: AppState) -> MenuView:
    view = state.screen().menu
    assert view is not None
    return view


def test_a_click_opens_a_submenu_and_runs_a_leaf() -> None:
    state = AppState()
    state.run_action("open_menu", "menu")
    state.run_action("menu_pick", "0:2")  # Algebra
    view = _menu(state)
    assert [panel.title for panel in view.panels] == ["Menu", "Algebra"]
    assert view.panels[0].rows[2].selected
    state.run_action("menu_pick", "1:0")  # Solve
    assert state.screen().menu is None
    assert _calculator(state).editor.linear() == "solve("


def test_clicking_a_parent_row_switches_submenu() -> None:
    state = AppState()
    state.run_action("open_menu", "menu")
    state.run_action("menu_pick", "0:2")  # Algebra
    state.run_action("menu_pick", "0:3")  # Calculus instead
    assert [panel.title for panel in _menu(state).panels] == ["Menu", "Calculus"]
    state.run_action("menu_pick", "0:3")  # clicking the open one closes it
    assert [panel.title for panel in _menu(state).panels] == ["Menu"]


def test_menu_back_and_clicks_without_a_menu_do_nothing() -> None:
    state = AppState()
    state.run_action("menu_pick", "0:0")
    state.run_action("select")
    assert state.screen().menu is None
    state.run_action("open_menu", "menu")
    state.run_action("menu_pick", "0:1")
    state.run_action("menu_back")
    assert _menu(state).title == "Menu"


def test_the_highlighted_row_shows_its_syntax() -> None:
    state = AppState()
    for key in ("F2", "3"):  # Algebra, Solve highlighted
        state.key_event(key)
    view = _menu(state)
    assert view.hint == "solve(Equation,Var)"
    assert view.rows[0].hint == "solve(Equation,Var)"


def test_menu_keys_follow_the_handheld() -> None:
    """Spot checks of real menu numbers (decision 0022)."""
    routes = {
        ("4", "3"): "∫(,,,)",  # the definite-integral template
        ("4", "4"): "limit(,,)",  # the limit template
        ("2", "8", "1"): "round(",
        ("6", "3", "3"): "mean(",
        ("8", "2", "5"): "tvmFV(",
        ("7", "3"): "det(",
    }
    for route, typed in routes.items():
        state = AppState()
        for key in ("F2", *route):
            state.key_event(key)
        assert _calculator(state).editor.linear() == typed, route


def _leaves(item: MenuItem) -> list[MenuItem]:
    if not item.items:
        return [item]
    return [leaf for child in item.items for leaf in _leaves(child)]


@pytest.mark.parametrize("name", sorted(nspire.PROFILE.menus))
def test_every_menu_leaf_is_something_the_app_can_do(name: str) -> None:
    """Commands are known to the engine, dialogs exist, and keys are unique per level."""
    root = nspire.PROFILE.menus[name]
    for leaf in _leaves(root):
        if leaf.action == "wizard":
            assert leaf.arg in nspire.PROFILE.wizards, leaf.label
            assert leaf.label.endswith("…") or name in {"templates", "catalog"}, leaf.label
        if leaf.action == "insert" and len(leaf.arg) > 1 and leaf.arg.endswith("("):
            assert registry.is_builtin(leaf.arg[:-1]), leaf.arg
            assert leaf.hint, leaf.label

    def check(item: MenuItem) -> None:
        keys = item_keys(item)
        keyless = item.columns or item.jump  # grids and jump lists have no keys
        assert keyless or len(keys) == len(set(keys)), item.label
        for child in item.items:
            check(child)

    check(root)


def test_hinted_commands_are_known_to_the_engine() -> None:
    for name in nspire_syntax.FUNCTIONS:
        assert registry.is_builtin(name), name
    for name in nspire_syntax.COMMANDS:
        statement = name in {"Define", "DelVar", "ClearAZ"}  # parser statements, not commands
        assert registry.lookup_command(name) is not None or statement, name


def test_every_menu_command_runs() -> None:
    """A spot check that what the menus type parses and evaluates (no crash, no syntax error)."""
    state = AppState()
    calculator = _calculator(state)
    lines = (
        "solve(x^2=4,x)",
        "∫(x,x,0,1)",
        "Σ(k,k,1,3)",
        "2▶Decimal",
        "[1,2;3,4]ᵀ",
        "Define f(x)=x^2",
        "DelVar f",
        "ClearAZ",
    )
    for line in lines:
        calculator.editor.clear()
        calculator.editor.insert_linear(line)
        state.run_action("enter")
        assert calculator.error is None, line
        assert "Error" not in calculator.history[-1].result.text, line


def test_catalog_opens_on_its_list_and_letters_jump() -> None:
    """Six tabs, opening on the A to Z list; a letter jumps, a digit changes tab (results M2)."""
    state = AppState()
    state.run_action("open_menu", "catalog")
    view = _menu(state)
    assert view.title == "Catalog > Catalog"
    assert [row.key for row in view.panels[0].rows] == list("123456")
    assert view.rows[0].label == "abs("
    assert view.rows[0].key == ""  # the list shows no keys
    state.key_event("s")
    view = _menu(state)
    chosen = next(row for row in view.rows if row.selected)
    assert chosen.label.startswith("s")
    state.key_event("4")  # the Symbols tab, a grid 11 wide
    view = _menu(state)
    assert view.title == "Catalog > Symbols"
    assert view.panels[-1].columns == 11
    state.key_event("Arrow Down")  # down a row of the grid
    assert next(n for n, row in enumerate(_menu(state).rows) if row.selected) == 11


def test_grid_menus_move_in_two_dimensions() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("trig")
    view = _menu(state)
    assert [row.label for row in view.rows] == [
        "sin",
        "cos",
        "tan",
        "csc",
        "sec",
        "cot",
        "sin⁻¹",
        "cos⁻¹",
        "tan⁻¹",
        "csc⁻¹",
        "sec⁻¹",
        "cot⁻¹",
    ]
    for key in ("right", "down"):  # to cos⁻¹
        state.press_keypad(key)
    state.press_keypad("enter")
    assert _calculator(state).editor.linear() == "cos⁻¹("


def test_variables_menu_lists_the_problem() -> None:
    state = AppState()
    calculator = _calculator(state)
    calculator.editor.insert_text("5→a")
    state.run_action("enter")
    state.press_keypad("var")
    view = _menu(state)
    assert [row.label for row in view.rows] == ["a"]
    assert view.hint == "a = 5"
    state.press_keypad("enter")
    assert calculator.editor.linear() == "a"


def test_keypad_trig_and_ctrl_layers() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("trig")
    assert _menu(state).title == "Trig"
    state.press_keypad("click")  # sin
    state.press_keypad("ctrl")
    state.press_keypad("var")  # sto→
    state.press_keypad("shift")
    state.press_keypad("a")  # a capital
    assert _calculator(state).editor.linear() == "sin(→A"
    state.press_keypad("ctrl")
    state.press_keypad("del")  # clear
    assert _calculator(state).editor.linear() == ""


def _calculator(state: AppState) -> Calculator:
    calculator = state.document.current.calculator
    assert calculator is not None
    return calculator


def test_placeholders_keep_the_handheld_numbering() -> None:
    """Items CASSim lacks are greyed but keep their numbers (decision 0022)."""
    state = AppState()
    state.key_event("F2")
    assert [row.key for row in _menu(state).rows] == list("123456789")
    state.key_event("9")  # Functions & Programs: it opens, every command greyed
    assert not any(row.enabled for row in _menu(state).rows if not row.submenu)
    state.key_event("Arrow Left")
    state.key_event("3")  # Algebra
    rows = _menu(state).rows
    assert [row.key for row in rows] == list("123456789ABCD")
    assert (rows[4].label, rows[4].enabled) == ("Complete the Square", False)
    assert rows[5].label == "Numerical Solve"
    assert rows[5].enabled


def test_a_placeholder_does_nothing_when_chosen() -> None:
    state = AppState()
    for key in ("F2", "3", "5"):  # Algebra > 5 Complete the Square (not yet)
        state.key_event(key)
    view = _menu(state)
    assert view.title == "Menu > Algebra"  # still open, the placeholder highlighted
    assert view.rows[4].selected
    assert view.hint == "Not in CASSim yet"
    state.key_event("Enter")
    state.run_action("menu_pick", "1:4")
    state.key_event("A")  # Convert Expression: it opens to show the device's items, greyed
    view = _menu(state)
    assert view.title == "Menu > Algebra > Convert Expression"
    assert [row.label for row in view.rows][:2] == ["Convert to ln", "Convert to logbase"]
    assert not any(row.enabled for row in view.rows)
    state.key_event("Escape")
    assert _calculator(state).editor.linear() == ""


@pytest.mark.parametrize(
    ("route", "typed"),
    [
        (("4", "F", "1"), "nDerivative("),  # no dialog on the device
        (("4", "F", "3"), "nInt("),
        (("6", "3", "9"), "stDevPop("),  # List Math is flat
        (("6", "4", "5"), "seq("),
        (("6", "4", "9"), "mat▶list("),
        (("7", "C", "6"), "▶Cylind"),
        (("7", "B", "4"), "eigVl("),
        (("7", "8", "1"), "dim("),
    ],
)
def test_routes_checked_on_the_simulator(route: tuple[str, ...], typed: str) -> None:
    """Menu numbers from the Teacher Software run of 2026-11-08 (emulator-menus-results.md)."""
    state = AppState()
    for key in ("F2", *route):
        state.key_event(key)
    assert _calculator(state).editor.linear() == typed


@pytest.mark.parametrize(
    ("letter", "dialog"),
    [
        ("A", "binomPdf"),
        ("B", "binomCdf"),
        ("C", "invBinom"),
        ("E", "FPdf"),
        ("H", "geomPdf"),
        ("K", "poissCdf"),
    ],
)
def test_distribution_letters_follow_the_device(letter: str, dialog: str) -> None:
    state = AppState()
    shown: list[object] = []
    state.show_wizard = shown.append
    for key in ("F2", "6", "5", letter):  # Statistics > Distributions, same list as Probability
        state.key_event(key)
    assert shown == [nspire.PROFILE.wizards[dialog]]


def test_keypad_pairs_and_the_return_key() -> None:
    """ctrl+( and ctrl+) give a bracket pair, ctrl+× a pair of quotes, each with the cursor
    inside; ⏎ does nothing on a Calculator page (results M3)."""
    state = AppState(mode=Mode.HANDHELD)
    calculator = _calculator(state)
    for name in ("ctrl", "(", "1"):
        state.press_keypad(name)
    assert calculator.editor.linear() == "[1]"
    calculator.editor.clear()
    for name in ("ctrl", "times", "h"):
        state.press_keypad(name)
    assert calculator.editor.linear() == '"h"'
    state.press_keypad("return")
    assert calculator.history == []


def test_mode_and_insert_follow_the_second_device_run() -> None:
    state = AppState()
    for key in ("F2", "9", "8", "1"):  # Functions & Programs > Mode > Display Digits
        state.key_event(key)
    rows = _menu(state).rows
    assert (rows[0].label, rows[12].key, rows[12].label) == ("Float", "D", "Float12")
    assert (rows[13].key, rows[25].key, rows[25].label) == ("E", "Q", "Fix12")
    state.key_event("Escape")
    for key in ("F4", "4"):
        state.key_event(key)
    labels = {row.key: row.label for row in _menu(state).rows}
    assert (labels["B"], labels["C"]) == ("Program Editor", "Add Python")
