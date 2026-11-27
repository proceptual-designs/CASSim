# Requirements traced here: FR-DEV-008
"""Menus walked from keys: the Doc and Menu trees come from the profile (FR-DEV-001, FR-DEV-007)."""

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest

from cassim.app import about
from cassim.app.shell import BrowserOffers, Shell, update_message
from cassim.core.catalog import registry
from cassim.device.keys import Binding
from cassim.device.menu import MenuItem, MenuState, MenuView, item_keys
from cassim.devices.nspire import keymap as nspire
from cassim.devices.nspire import syntax as nspire_syntax
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of, calculator_on
from cassim.devices.nspire.pages.spreadsheet import SHEET_ACTIONS, Spreadsheet
from cassim.devices.nspire.ui.app import cassim_items, nspire_menu
from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.template_icons import HEIGHT, ICONS, WIDTH, Slot, Stroke
from cassim.devices.nspire.ui.views import (
    CalculatorView,
    DragSteps,
    icon_canvas,
    scroll_line,
    window_start,
)


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
        ("5", "Page layout"),
        ("6", "Refresh libraries"),
        ("7", "Settings & status"),
        ("8", "Login"),
        ("9", "Press-to-Test"),
    ]
    assert view.rows[0].selected
    assert view.rows[0].submenu


def test_doc_insert_problem_by_keys() -> None:
    """Doc > 4 Insert > 1 Problem, the route used on the simulator."""
    state = AppState()
    for key in ("F4", "4", "1", "1"):  # then 1 Add Calculator
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
    state.key_event("Enter")  # Add Calculator, the first application
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
    assert calculator_of(state.document.current) is not None
    assert calculator_on(state.document.current).editor.linear() == ""


def test_menu_item_types_a_command() -> None:
    state = AppState()
    for key in ("F2", "3", "1"):  # Menu > 3 Algebra > 1 Solve, as on the handheld
        state.key_event(key)
    assert calculator_of(state.document.current) is not None
    assert calculator_on(state.document.current).editor.linear() == "solve("


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
        MenuItem(
            "m",
            items=(MenuItem("a", "insert"), MenuItem("b", "enter", key="1"), MenuItem("c", "up")),
        )
    )
    assert menu.keys() == ["2", "1", "3"]
    menu.press("up")
    assert menu.level.index == 2
    assert menu.press("enter") is not None
    assert not menu.open


def test_page_sorter_opens_on_the_screen_and_the_doc_menu_still_works() -> None:
    """Doc > View > Page Sorter opens the sorter on the screen, not a dialog; the Doc menu still
    opens over it (Handheld Setup asks for its dialog)."""
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "3", "3", "F4", "7", "3"):  # View > Page Sorter, Handheld Setup
        state.key_event(key)
    assert state.sorting
    assert asked == ["system_settings"]


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


@pytest.mark.parametrize(
    ("page", "menu_name"),
    [("calculator", "menu"), ("spreadsheet", "menu_sheet")],
)
def test_menu_and_doc_switch_directly_even_in_a_submenu(page: str, menu_name: str) -> None:
    """FR-DEV-007: the other menu replaces the open one, for buttons and keys alike."""
    state = AppState()
    if page != "calculator":
        state.run_action("add_page", page)
    state.run_action("open_menu", "menu")
    assert state.menu is not None
    expected = state.profile.menus[menu_name]
    assert state.menu.root.label == expected.label
    assert [item.label for item in state.menu.root.items] == [item.label for item in expected.items]
    state.run_action("menu_pick", "0:0")
    assert len(state.menu.levels) == 2
    state.key_event("F4")
    assert _menu(state).title == "Doc"
    state.run_action("menu_pick", "0:0")
    assert len(state.menu.levels) == 2
    state.run_action("open_menu", "menu")
    assert state.menu is not None
    assert state.menu.root.label == expected.label
    assert [item.label for item in state.menu.root.items] == [item.label for item in expected.items]
    assert len(state.menu.levels) == 1


MENU_OPENERS = {
    "menu": "Menu",
    "doc": "Doc",
    "cassim": "CASSim",
    "variables": "Variables",
    "catalog": "Catalog",
    "trig": "Trig",
    "templates": "Templates",
    "symbols": "Symbols",
    "relations": "Relations",
    "punctuation": "Punctuation",
}


@pytest.mark.parametrize("source", MENU_OPENERS)
@pytest.mark.parametrize("target", MENU_OPENERS)
def test_menu_openers_switch_or_close(source: str, target: str) -> None:
    """FR-DEV-007: every opener switches menus or closes its own."""
    state = AppState()
    state.cassim_menu = lambda: MenuItem("CASSim")
    state.run_action("open_menu", source)
    assert state.menu is not None
    state.run_action("open_menu", target)
    if source == target:
        assert state.menu is None
    else:
        assert state.menu is not None
        assert state.menu.root.label == MENU_OPENERS[target]


def test_menu_switch_preserves_sorter_restrictions() -> None:
    state = AppState()
    state.sorting = True
    state.run_action("open_menu", "doc")
    doc = state.menu
    state.run_action("open_menu", "menu")
    assert state.menu is doc
    assert state.sorting


def test_context_menu_and_page_picker_switch_and_toggle() -> None:
    state = AppState()
    state.run_action("add_page", "spreadsheet")
    state.run_action("context_menu")
    assert _menu(state).title == "Cell"
    state.run_action("open_menu", "doc")
    assert _menu(state).title == "Doc"
    state.run_action("context_menu")
    assert _menu(state).title == "Cell"
    state.run_action("context_menu")
    assert state.menu is None
    state.run_action("add_page")
    assert _menu(state).title == "Add a page"
    state.run_action("add_problem")
    assert _menu(state).title == "Add a Problem"
    state.run_action("add_problem")
    assert state.menu is None


def test_unavailable_menu_does_not_close_the_current_menu() -> None:
    state = AppState()
    state.run_action("open_menu", "doc")
    original = state.menu
    state.run_action("open_menu", "not-a-menu")
    assert state.menu is original


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
        ("4", "3"): "∫(,)",  # the definite-integral template (empty limits: indefinite)
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


def _enabled_leaves(item: MenuItem) -> list[MenuItem]:
    if not item.enabled:
        return []
    if not item.items:
        return [item]
    return [leaf for child in item.items for leaf in _enabled_leaves(child)]


def _assert_action_dispatches(
    binding: Binding, *, sheet_page: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Follow AppState's real routing, checking the actual page handler tables on arrival."""
    state = AppState()
    if sheet_page:
        state.run_action("add_page", "spreadsheet")
    calculator = calculator_of(state.document.current)
    sheet = state.sheet
    handled: list[str] = []
    shell_action = state._shell_action
    document_action = state._document_action

    def shell(candidate: Binding) -> bool:
        result = shell_action(candidate)
        if result:
            handled.append("shell")
        return result

    def document(candidate: Binding) -> bool:
        result = document_action(candidate)
        if result:
            handled.append("document")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(state, "_shell_action", shell)
        patch.setattr(state, "_document_action", document)
        if calculator is not None:

            def calculator_action(candidate: Binding) -> None:
                assert calculator.handles(candidate.action), candidate
                handled.append("calculator")

            patch.setattr(calculator, "perform", calculator_action)
        if sheet is not None:

            def sheet_action(candidate: Binding) -> None:
                assert candidate.action in sheet._keys(), candidate
                handled.append("sheet")

            patch.setattr(sheet, "perform", sheet_action)
        state.run(binding)
        if sheet is not None and binding.action == "context_menu":
            assert state.menu is not None
            handled.append("sheet context menu")
    assert handled, binding


@pytest.mark.parametrize("name", sorted(nspire.PROFILE.menus))
def test_enabled_menu_actions_reach_handlers(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-DEV-007: every enabled leaf has an action handled on its applicable page."""
    actions: dict[str, Binding] = {}
    for leaf in _enabled_leaves(nspire.PROFILE.menus[name]):
        assert leaf.action, (name, leaf.label)
        actions.setdefault(leaf.action, Binding(leaf.action, leaf.arg))
    for binding in actions.values():
        _assert_action_dispatches(
            binding,
            sheet_page=name == "menu_sheet" or name.startswith("sheet_"),
            monkeypatch=monkeypatch,
        )


@pytest.mark.parametrize("keymap", [nspire.PROFILE.handheld, nspire.PROFILE.computer])
def test_profile_actions_reach_handlers(
    keymap: Mapping[str, Binding], monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-DEV-007: sheet-only shortcuts are checked on a sheet, other keys on a calculator."""
    actions = {binding.action: binding for binding in keymap.values()}
    for binding in actions.values():
        _assert_action_dispatches(
            binding, sheet_page=binding.action in SHEET_ACTIONS, monkeypatch=monkeypatch
        )


def test_missing_page_handler_fails_dispatch_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Calculator, "handles", lambda self, action: False)
    with pytest.raises(AssertionError):
        _assert_action_dispatches(Binding("insert", "x"), sheet_page=False, monkeypatch=monkeypatch)


def test_missing_sheet_handler_fails_dispatch_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Spreadsheet, "_keys", lambda self: {})
    with pytest.raises(AssertionError):
        _assert_action_dispatches(Binding("goto"), sheet_page=True, monkeypatch=monkeypatch)


def test_enabled_leaf_without_action_is_an_error() -> None:
    menu = MenuState(MenuItem("m", items=(MenuItem("missing"),)))
    with pytest.raises(ValueError, match="has no action"):
        menu.press("enter")


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


@pytest.mark.parametrize(
    ("key", "title"), [("pi", "Symbols"), ("trig", "Trig"), ("templates", "Templates")]
)
def test_palette_key_toggles_and_arrows_select(key: str, title: str) -> None:
    """FR-DEV-007: palette buttons toggle; arrows still navigate the grid."""
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad(key)
    view = _menu(state)
    assert view.title == title
    state.press_keypad(key)
    assert state.menu is None
    state.press_keypad(key)
    state.press_keypad("right")
    assert _menu(state).rows[1].selected
    state.press_keypad("enter")
    assert state.menu is None
    assert _calculator(state).editor.linear()


@pytest.mark.parametrize("source", ["pi", "trig", "templates"])
@pytest.mark.parametrize("target", ["pi", "trig", "templates"])
def test_palette_keys_switch_or_close(source: str, target: str) -> None:
    state = AppState()
    state.press_keypad(source)
    state.press_keypad(target)
    if source == target:
        assert state.menu is None
    else:
        view = _menu(state)
        assert view.title == {"pi": "Symbols", "trig": "Trig", "templates": "Templates"}[target]
        assert view.rows[0].selected
    assert _calculator(state).editor.linear() == ""


@pytest.mark.parametrize("tab", ["4", "5"])
@pytest.mark.parametrize("key", ["pi", "trig", "templates"])
def test_palette_keys_replace_catalog_symbol_and_template_grids(tab: str, key: str) -> None:
    state = AppState()
    state.press_keypad("catalog")
    state.key_event(tab)
    assert len(_menu(state).panels) == 2
    state.press_keypad(key)
    view = _menu(state)
    assert view.title == {"pi": "Symbols", "trig": "Trig", "templates": "Templates"}[key]
    assert view.rows[0].selected
    assert len(view.panels) == 1


def test_ctrl_catalog_toggles_symbols_and_switches_from_catalog() -> None:
    state = AppState()
    for _ in range(2):
        state.press_keypad("ctrl")
        state.press_keypad("catalog")
    assert state.menu is None
    state.press_keypad("ctrl")
    state.press_keypad("catalog")
    assert _menu(state).title == "Symbols"
    state.press_keypad("right")
    assert _menu(state).rows[1].selected
    state.press_keypad("enter")
    assert _calculator(state).editor.linear() == "ⅈ"
    state.press_keypad("catalog")
    state.press_keypad("trig")
    assert _menu(state).title == "Trig"


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
    calculator = calculator_of(state.document.current)
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
    assert (rows[4].label, rows[4].enabled) == ("Complete the square", True)
    assert rows[5].label == "Numerical solve"
    assert rows[5].enabled


def test_complete_square_menu_inserts_the_command() -> None:
    state = AppState()
    for key in ("F2", "3", "5"):  # Algebra > 5 Complete the Square
        state.key_event(key)
    assert _calculator(state).editor.linear() == "completeSquare("


def test_unimplemented_convert_submenu_stays_greyed() -> None:
    state = AppState()
    state.key_event("F2")
    state.key_event("3")
    state.key_event("A")  # Convert Expression: it opens to show the device's items, greyed
    view = _menu(state)
    assert view.title == "Menu > Algebra > Convert expression"
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


def test_cassim_menu_opens_and_dispatches_browser_items() -> None:
    """App actions belong to CASSim, not Doc (FR-DEV-001)."""
    state = AppState()
    state.cassim_menu = lambda: MenuItem(
        "CASSim",
        items=(
            MenuItem("Fullscreen", "dialog", "fullscreen"),
            MenuItem("Install CASSim", "dialog", "install"),
        ),
    )
    asked: list[str] = []
    state.show_dialog = asked.append
    state.run_action("open_menu", "cassim")
    view = state.screen().menu
    assert view is not None
    assert [row.label for row in view.rows][-2:] == ["Fullscreen", "Install CASSim"]
    state.key_event("Enter")
    assert asked == ["fullscreen"]


def nspire_rows(**facts: Any) -> list[tuple[str, str, str, bool, bool]]:
    """(key, label, mark, rule, enabled) of each row of the Nspire's CASSim menu."""
    offers = facts.pop("offers", BrowserOffers())
    items = cassim_items(offers, nspire_menu(**facts))
    root = MenuItem("CASSim", items=items)
    return [
        (key, item.label, item.mark, item.rule, item.enabled)
        for key, item in zip(item_keys(root), items, strict=True)
    ]


def test_the_nspire_numbers_the_shared_sections_and_rules_them_off() -> None:
    """SDD-15 section 4: the shared sections as a numbered panel; each section after the
    first starts with a rule, and ● marks the current view."""
    assert nspire_rows(handheld=False, keypad=True) == [
        ("1", "Computer view", "●", False, True),
        ("2", "Handheld view", "", False, True),
        ("3", "Keypad", "✓", False, True),
        ("4", "Fullscreen", "", False, False),
        ("5", "Settings…", "", True, True),
        ("6", "Appearance…", "", False, True),
        ("7", "Install CASSim…", "", True, False),
        ("8", "Check for updates", "", False, True),
        ("9", "Offline: unknown", "", False, True),
        ("A", "Help (wiki)…", "", True, True),
        ("B", "About CASSim…", "", False, True),
    ]


def test_handheld_view_greys_the_keypad_which_it_always_shows() -> None:
    rows = nspire_rows(handheld=True)
    assert rows[0][1:3] == ("Computer view", "")
    assert rows[1][1:3] == ("Handheld view", "●")
    assert rows[2][1:] == ("Keypad", "✓", False, False)


def test_home_comes_first_and_never_moves_the_other_numbers_within_a_build() -> None:
    """Home is fixed for a bundle; the retry item that used to appear and shift the numbers is
    folded into the offline status."""
    failed = BrowserOffers(offline_state="unavailable", offline_retry=True)
    plain = [row[1] for row in nspire_rows(handheld=True, home=True)]
    with_failure = [row[1] for row in nspire_rows(handheld=True, home=True, offers=failed)]
    assert plain[0] == "Home"
    assert len(plain) == len(with_failure)
    assert "Offline: unavailable" in with_failure


def test_the_hints_are_shortcuts() -> None:
    items = cassim_items(BrowserOffers(), nspire_menu(handheld=True))
    hints = {item.label: item.hint for item in items}
    assert hints["Computer view"] == "Alt+Shift+C"
    assert hints["Handheld view"] == "Alt+Shift+H"
    assert hints["Help (wiki)…"] == "F1"
    assert all(hint != "CASSim" for hint in hints.values())


def test_template_cells_are_drawn_as_pictures() -> None:
    """FR-CALC-005: every cell of the templates palette has a picture of its template, drawn
    inside the cell, and the menu rows carry it to the view."""
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("templates")
    rows = _menu(state).rows
    assert [row.icon for row in rows] == list(ICONS)  # one each, in the palette's order
    for name, icon in ICONS.items():
        for shape in icon:
            if isinstance(shape, Stroke):
                xs, ys = zip(*shape.points, strict=True)
            elif isinstance(shape, Slot):
                xs, ys = (shape.x, shape.x + shape.side), (shape.y, shape.y + shape.side)
            else:
                xs, ys = (shape.x,), (shape.y,)
            assert 0 <= min(xs) <= max(xs) <= WIDTH, name
            assert 0 <= min(ys) <= max(ys) <= HEIGHT, name
        assert len(icon_canvas(icon, 2.0, "#ffffff").shapes) == len(icon)


def test_other_grid_cells_keep_their_labels() -> None:
    state = AppState(mode=Mode.HANDHELD)
    state.press_keypad("trig")
    assert not any(row.icon for row in _menu(state).rows)


def test_a_drag_turns_into_whole_row_steps() -> None:
    """Touch-scrollable menus (a CASSim feature): a finger moving up a row's height steps one
    row down the list, as the list follows the finger; part rows carry over."""
    drag = DragSteps()
    assert drag.feed(-10, 19.5) == []
    assert drag.feed(-10, 19.5) == [1]  # 20 px up in all: one row
    assert drag.feed(-40, 19.5) == [1, 1]
    assert drag.feed(60, 19.5) == [-1, -1, -1]
    drag.reset()
    assert drag.travel == 0
    assert drag.feed(5, 0) == []  # a zero row height never loops


def test_a_drag_on_an_open_menu_moves_its_highlight() -> None:
    state = AppState(mode=Mode.HANDHELD)
    view = CalculatorView(state, on_action=state.run_action)
    state.key_event("F2")
    state.key_event("3")  # Algebra, longer than the handheld screen
    view.refresh()
    assert state.menu is not None
    before = state.menu.level.index
    here = ft.Offset(0, 0)
    event = ft.DragUpdateEvent(
        name="update",
        control=view.control,
        local_position=here,
        global_position=here,
        primary_delta=-60,
    )
    view._drag_menu(event)
    assert state.menu.level.index > before


def test_each_scroll_step_moves_the_window_one_line() -> None:
    """A drag or wheel step scrolls the list itself: from the top of a 20-line list showing 7,
    the window moves a line at once, and it stops at the ends."""
    shown, lines = 7, 20
    line = 0
    starts = []
    for _ in range(4):
        line = scroll_line(line, lines, shown, 1)
        starts.append(window_start(line, lines, shown))
    assert starts == [1, 2, 3, 4]
    line = scroll_line(line, lines, shown, -1)
    assert window_start(line, lines, shown) == 3
    assert scroll_line(19, lines, shown, 1) == 19
    assert scroll_line(0, lines, shown, -1) == 0


def test_ctrl_i_ctrl_doc_and_insert_problem_offer_the_applications():
    """The emulator's list for a new page or Problem (graphs2 D, graphs3, sharing G, split H)."""
    state = AppState()
    state.key_event("i", ctrl=True)
    view = _menu(state)
    assert [(row.key, row.label) for row in view.rows] == [
        ("1", "Add Calculator"),
        ("2", "Add Graphs"),
        ("3", "Add Geometry"),
        ("4", "Add Lists & Spreadsheet"),
        ("5", "Add Data & Statistics"),
        ("6", "Add Notes"),
        ("7", "Add Vernier DataQuest™"),
        ("8", "Add widget"),
        ("9", "Add Program Editor"),
        ("A", "Add Python"),
    ]
    assert not view.rows[2].enabled  # Geometry is not in CASSim
    assert next(row for row in view.rows if row.label == "Add Graphs").hint == ""
    assert next(row for row in view.rows if row.label == "Add Data & Statistics").hint == ""
    assert next(row for row in view.rows if row.label == "Add Notes").hint
    state.key_event("Escape")
    assert state.screen().title == "1.1"  # nothing added
    state.press_keypad("ctrl")
    state.press_keypad("doc")
    state.key_event("4")
    assert (state.screen().title, state.document.current.kind) == ("1.2", "spreadsheet")
    for key in ("F4", "4", "1", "4"):  # Doc > Insert > Problem > Add Lists & Spreadsheet
        state.key_event(key)
    assert (state.screen().title, state.document.current.kind) == ("2.1", "spreadsheet")
    state.run_action("add_page")  # the toolbar's + page
    assert _menu(state).title == "Add a page"


def test_check_for_updates_asks_the_page_and_shows_its_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CASSim > Check for Updates sends the request to the page and shows what it found; without a
    page (the desktop) it says it cannot check."""
    shown: list[str] = []
    sent: list[str] = []
    bridge = SimpleNamespace(on_update=None, check_update=lambda: sent.append("check_update"))
    shell = SimpleNamespace(bridge=bridge, notice=lambda _title, text: shown.append(text))
    Shell.check_for_updates(shell)  # ty: ignore[invalid-argument-type]
    assert sent == ["check_update"]
    monkeypatch.setattr(about.bundle, "SOURCE", "CASSim-calc")
    bridge.on_update("current")
    bridge.on_update("ready")
    bridge.on_update("something new")
    assert shown == [
        update_message("current"),
        update_message("ready"),
        update_message("offline"),
    ]
    assert f"CASSimᵝ {dict(about.versions())['CASSim']} from CASSim-calc is up to date." == shown[0]
    shown.clear()
    shell.bridge = None
    Shell.check_for_updates(shell)  # ty: ignore[invalid-argument-type]
    assert shown == ["This copy of CASSimᵝ cannot check for updates."]
