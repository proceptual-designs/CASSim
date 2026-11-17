# Requirements traced here: FR-DOC-001, FR-DOC-008
"""The Computer sidebar's scrolling and list expansion."""

import asyncio
from collections.abc import Callable
from typing import cast

import flet as ft
import pytest

from cassim.device.engine import LocalEngine, Op, RemoteSession, check_reply, eval_op
from cassim.devices.nspire.menus import WIZARDS
from cassim.devices.nspire.pages import PageKind
from cassim.devices.nspire.runner import Runner
from cassim.devices.nspire.ui.sidebar import LIST_BATCH, Sidebar
from cassim.devices.nspire.ui.state import AppState


def setup_sidebar() -> tuple[AppState, Sidebar]:
    state = AppState()
    sidebar = Sidebar(state, lambda: None)
    sidebar.on_change = sidebar.refresh
    return state, sidebar


def click(control: ft.Control) -> None:
    assert isinstance(control, ft.Container | ft.IconButton)
    assert control.on_click is not None
    handler = cast("Callable[[ft.Event[ft.Control]], object]", control.on_click)
    handler(ft.Event("click", control))


def variable_button(sidebar: Sidebar, index: int = 0) -> ft.Container:
    row = sidebar.variable_list.controls[index]
    assert isinstance(row, ft.Row)
    button = row.controls[1]
    assert isinstance(button, ft.Container)
    return button


def named_button(controls: list[ft.Control], tooltip: str) -> ft.Control:
    for row in controls:
        if isinstance(row, ft.Row):
            for control in row.controls:
                if getattr(control, "tooltip", None) == tooltip:
                    return control
    raise AssertionError(f"button not found: {tooltip}")


def test_variables_heading_hides_and_shows_without_losing_list_state() -> None:
    state, sidebar = setup_sidebar()
    state.document.problems[0].session.eval("a:={1,2}")
    sidebar.refresh()
    assert sidebar.variable_list.scroll == ft.ScrollMode.AUTO
    assert sidebar.variable_list.expand
    click(variable_button(sidebar))
    assert len(sidebar.variable_list.controls) == 3
    heading = sidebar.control.controls[-2]
    assert isinstance(heading, ft.Container)
    click(heading)
    assert not sidebar.variable_list.visible
    heading = sidebar.control.controls[-2]
    assert isinstance(heading, ft.Container)
    click(heading)
    assert sidebar.variable_list.visible
    assert len(sidebar.variable_list.controls) == 3
    click(variable_button(sidebar))
    assert len(sidebar.variable_list.controls) == 1


def test_long_lists_expand_in_batches_and_show_individual_values() -> None:
    state, sidebar = setup_sidebar()
    session = state.document.problems[0].session
    session.eval(f"a:=seq(x,x,1,{LIST_BATCH + 2})")
    sidebar.refresh()
    first = sidebar.variable_list.controls[0]
    assert isinstance(first, ft.Row)
    assert isinstance(first.controls[0], ft.Text)
    assert first.controls[0].no_wrap
    assert first.controls[0].overflow == ft.TextOverflow.ELLIPSIS
    click(variable_button(sidebar))
    assert len(sidebar.variable_list.controls) == LIST_BATCH + 2
    first_item = sidebar.variable_list.controls[1]
    assert isinstance(first_item, ft.Container)
    assert isinstance(first_item.content, ft.Text)
    assert first_item.content.value == "1: 1"
    more = sidebar.variable_list.controls[-1]
    assert isinstance(more, ft.Container)
    click(more)
    assert len(sidebar.variable_list.controls) == LIST_BATCH + 3
    last = sidebar.variable_list.controls[-1]
    assert isinstance(last, ft.Container)
    assert isinstance(last.content, ft.Text)
    assert last.content.value == f"{LIST_BATCH + 2}: {LIST_BATCH + 2}"


def test_expansion_belongs_to_problem_and_survives_page_switches() -> None:
    state, sidebar = setup_sidebar()
    state.document.problems[0].session.eval("a:={1,2}")
    sidebar.refresh()
    click(variable_button(sidebar))
    state.run_action("add_page", "calculator")
    sidebar.refresh()
    assert len(sidebar.variable_list.controls) == 3
    state.run_action("add_problem", "calculator")
    state.document.problems[1].session.eval("a:={3,4}")
    sidebar.refresh()
    assert len(sidebar.variable_list.controls) == 1
    state.document.go(0, 0)
    sidebar.refresh()
    assert len(sidebar.variable_list.controls) == 3


def test_expanded_list_refreshes_when_its_value_changes() -> None:
    state, sidebar = setup_sidebar()
    session = state.document.problems[0].session
    session.eval("a:={1,2}")
    sidebar.refresh()
    click(variable_button(sidebar))
    session.eval("a:={4,5,6}")
    sidebar.refresh()
    assert len(sidebar.variable_list.controls) == 4
    first_item = sidebar.variable_list.controls[1]
    assert isinstance(first_item, ft.Container)
    assert isinstance(first_item.content, ft.Text)
    assert first_item.content.value == "1: 4"
    session.eval("a:=9")
    sidebar.refresh()
    assert len(sidebar.variable_list.controls) == 1
    assert isinstance(sidebar.variable_list.controls[0], ft.Row)
    assert len(sidebar.variable_list.controls[0].controls) == 1


def test_pages_heading_and_problem_buttons_collapse_independently() -> None:
    state, sidebar = setup_sidebar()
    state.run_action("add_page", "calculator")
    state.run_action("add_page", "calculator")
    state.run_action("add_problem", "calculator")
    state.run_action("add_page", "calculator")
    sidebar.refresh()
    assert len(sidebar.page_list.controls) == 5
    assert sidebar.page_list.height == 135
    assert sidebar.page_list.scroll == ft.ScrollMode.AUTO
    assert not any(
        isinstance(control, ft.Container)
        and control.tooltip in {"Move page earlier", "Move page later"}
        for control in sidebar.control.controls
    )

    click(named_button(sidebar.page_list.controls, "Collapse Problem 1"))
    assert len(sidebar.page_list.controls) == 3
    assert sidebar.page_list.height == 81
    click(named_button(sidebar.page_list.controls, "Collapse Problem 2"))
    assert len(sidebar.page_list.controls) == 2
    heading = sidebar.control.controls[0]
    assert isinstance(heading, ft.Container)
    click(heading)
    assert not sidebar.page_list.visible
    assert not sidebar.control.controls[1].visible
    heading = sidebar.control.controls[0]
    assert isinstance(heading, ft.Container)
    click(heading)
    assert sidebar.page_list.visible
    click(named_button(sidebar.page_list.controls, "Expand Problem 1"))
    assert len(sidebar.page_list.controls) == 4


def test_dotted_names_form_independently_collapsible_problem_groups() -> None:
    state, sidebar = setup_sidebar()
    session = state.document.problems[0].session
    session.eval("OneVar {1,2,3}")
    session.eval("tvm.n:=4")
    session.eval("other.a:=7")
    session.eval("other.b:=8")
    sidebar.refresh()
    click(named_button(sidebar.variable_list.controls, "Collapse stat variables"))
    click(named_button(sidebar.variable_list.controls, "Collapse other variables"))
    assert not any(
        isinstance(row, ft.Row)
        and isinstance(row.controls[0], ft.Text)
        and (row.controls[0].value or "").startswith("stat.")
        for row in sidebar.variable_list.controls
    )
    assert named_button(sidebar.variable_list.controls, "Collapse tvm variables")
    state.run_action("add_problem", "calculator")
    state.document.problems[1].session.eval("other.a:=9")
    sidebar.refresh()
    assert named_button(sidebar.variable_list.controls, "Collapse other variables")
    state.document.go(0, 0)
    sidebar.refresh()
    click(named_button(sidebar.variable_list.controls, "Expand stat variables"))
    assert named_button(sidebar.variable_list.controls, "Expand stat.values")


def test_matrix_expansion_displays_cells_and_rows() -> None:
    state, sidebar = setup_sidebar()
    session = state.document.problems[0].session
    session.eval("a:=[1;2;3]")
    session.eval("b:=[1,2;3,4]")
    sidebar.refresh()
    click(named_button(sidebar.variable_list.controls, "Expand a"))
    first_item = sidebar.variable_list.controls[1]
    assert isinstance(first_item, ft.Container)
    assert isinstance(first_item.content, ft.Text)
    assert first_item.content.value == "1: 1"
    click(named_button(sidebar.variable_list.controls, "Expand b"))
    last = sidebar.variable_list.controls[-1]
    assert isinstance(last, ft.Container)
    assert isinstance(last.content, ft.Text)
    assert last.content.value == "2: [3,4]"


def test_delete_controls_target_standalone_variables_and_group_headers_only() -> None:
    state = AppState()
    session = state.document.problems[0].session
    session.eval("a:=5")
    session.eval("OneVar {1,2,3}")
    deleted: list[tuple[str, ...]] = []
    sidebar = Sidebar(
        state,
        lambda: None,
        on_delete=lambda rows: deleted.append(tuple(row.name for row in rows)),
    )
    sidebar.refresh()

    click(named_button(sidebar.variable_list.controls, "Delete variable a"))
    assert deleted == [("a",)]
    click(named_button(sidebar.variable_list.controls, "Delete stat variables"))
    assert deleted[1]
    assert all(name.startswith("stat.") for name in deleted[1])
    assert not any(
        isinstance(control, ft.Container)
        and isinstance(control.tooltip, str)
        and control.tooltip.startswith("Delete variable stat.")
        for row in sidebar.variable_list.controls
        if isinstance(row, ft.Row)
        for control in row.controls
    )
    grouped = next(
        row
        for row in sidebar.variable_list.controls
        if isinstance(row, ft.Row)
        and any(
            isinstance(control, ft.Text) and control.value == "stat" for control in row.controls
        )
    )
    assert isinstance(grouped.controls[0], ft.IconButton)
    assert grouped.controls[0].tooltip == "Delete stat variables"


def test_folding_all_registered_page_types_across_problems() -> None:
    """FR-DOC-001: folding hides pages, not their types, contents or Problem identity."""
    state, sidebar = setup_sidebar()
    for kind in PageKind:
        if kind is not PageKind.CALCULATOR:
            state.run_action("add_page", kind)
    state.run_action("add_problem", "spreadsheet")
    state.run_action("add_page", "calculator")
    state.document.go(0, 0)
    sidebar.refresh()
    original = list(state.document.sorter())
    assert len(original) == len(PageKind) + 2
    for row, (_, _, kind) in zip(sidebar.page_list.controls, original, strict=True):
        assert isinstance(row, ft.Row)
        title = row.controls[0]
        assert isinstance(title, ft.Container)
        assert isinstance(title.content, ft.Text)
        assert state.page_name(kind) in (title.content.value or "")
        assert title.content.no_wrap
        assert title.content.overflow == ft.TextOverflow.ELLIPSIS

    click(named_button(sidebar.page_list.controls, "Collapse Problem 1"))
    assert len(sidebar.page_list.controls) == 3
    click(named_button(sidebar.page_list.controls, "Collapse Problem 2"))
    assert len(sidebar.page_list.controls) == 2
    assert state.document.sorter() == original
    state.document.go(1, 0)
    state.run_action("move_problem", "-1")
    sidebar.refresh()
    assert len(sidebar.page_list.controls) == 2  # the fold follows each Problem, not its number
    click(named_button(sidebar.page_list.controls, "Expand Problem 2"))
    assert len(sidebar.page_list.controls) == len(PageKind) + 1
    click(named_button(sidebar.page_list.controls, "Expand Problem 1"))
    assert len(sidebar.page_list.controls) == len(original)
    assert [kind for _, _, kind in state.document.sorter()] == [
        kind for _, _, kind in original[-2:] + original[:-2]
    ]
    last_row = sidebar.page_list.controls[-1]
    assert isinstance(last_row, ft.Row)
    title = last_row.controls[0]
    assert isinstance(title, ft.Container)
    click(title)
    assert (state.document.problem, state.document.page) == (1, len(PageKind) - 1)
    click(named_button(sidebar.page_list.controls, "Collapse Problem 2"))
    assert (state.document.problem, state.document.page) == (1, len(PageKind) - 1)
    click(named_button(sidebar.page_list.controls, "Expand Problem 2"))
    assert (state.document.problem, state.document.page) == (1, len(PageKind) - 1)


@pytest.mark.parametrize(
    ("key", "kind"),
    [
        ("1", PageKind.CALCULATOR),
        ("2", PageKind.GRAPHS),
        ("4", PageKind.SPREADSHEET),
        ("5", PageKind.STATISTICS),
        ("6", PageKind.NOTES),
        ("9", PageKind.PROGRAM),
        ("a", PageKind.PYTHON),
    ],
)
def test_picker_creates_each_offered_page_and_problem(key: str, kind: PageKind) -> None:
    """FR-DOC-001: both pickers create the selected type and the resulting Problems fold."""
    state, sidebar = setup_sidebar()
    state.key_event("i", ctrl=True)
    state.key_event(key)
    state.key_event("i", ctrl=True, alt=True)
    state.key_event(key)
    state.run_action("add_page", "calculator")
    sidebar.refresh()
    assert [entry[2] for entry in state.document.sorter()] == [
        PageKind.CALCULATOR,
        kind,
        kind,
        PageKind.CALCULATOR,
    ]
    for number in (1, 2):
        click(named_button(sidebar.page_list.controls, f"Collapse Problem {number}"))
    assert len(sidebar.page_list.controls) == 2
    for number in (1, 2):
        click(named_button(sidebar.page_list.controls, f"Expand Problem {number}"))
    assert len(sidebar.page_list.controls) == 4


def check_stats_in_another_problem(state: AppState, sidebar: Sidebar, runner: Runner) -> None:
    state.run_action("add_problem", "calculator")
    other = state.document.problems[1].session
    assert isinstance(other, RemoteSession)

    async def calculate() -> None:
        sent: list[Op] = [eval_op("TwoVar {1,2,3},{3,6,9}", approximate=False)]
        other.accept(sent, check_reply(await runner.engine.run(other.id, sent)))

    asyncio.run(calculate())
    sidebar.refresh()
    assert named_button(sidebar.variable_list.controls, "Collapse stat variables")
    assert named_button(sidebar.variable_list.controls, "Expand stat.values")


def test_remote_two_variable_statistics_and_finance_groups_fold() -> None:
    """FR-DOC-008: real stats and Finance Solver results fold without changing the engine."""
    runner = Runner(LocalEngine())
    state = AppState(sessions=runner.new_session)
    sidebar = Sidebar(state, lambda: None)
    sidebar.on_change = sidebar.refresh
    session = state.document.problems[0].session
    assert isinstance(session, RemoteSession)

    async def calculate() -> None:
        sent: list[Op] = [
            eval_op("xs:={1,2,3,4}", approximate=False),
            eval_op("ys:={2,4,6,8}", approximate=False),
            eval_op("TwoVar xs,ys", approximate=False),
        ]
        session.accept(sent, check_reply(await runner.engine.run(session.id, sent)))
        wizard = WIZARDS["finance"]
        values = {
            **wizard.defaults(),
            "n": "12",
            "i": "6",
            "pv": "10000",
            "ppy": "12",
            "cpy": "12",
        }
        assert wizard.calculate is not None
        state.store_wizard(wizard, wizard.calculate(values, "pmt"))
        await runner.sync(state.document)

    asyncio.run(calculate())
    original = {row.name: row for row in session.variables()}
    assert {"xs", "ys", "stat.values", "stat.results", "tvm.pmt", "tvm.pv"} <= original.keys()
    assert original["stat.values"].items is not None
    assert original["stat.values"].items[0] == '"Two-Variable Statistics"'
    assert original["stat.results"].items is not None
    assert original["tvm.pv"].text == "10000"
    assert original["tvm.pmt"].text.startswith("-")
    sidebar.refresh()
    click(named_button(sidebar.variable_list.controls, "Expand stat.values"))
    click(named_button(sidebar.variable_list.controls, "Expand stat.results"))
    shown = [
        control.content.value
        for control in sidebar.variable_list.controls
        if isinstance(control, ft.Container) and isinstance(control.content, ft.Text)
    ]
    assert '1: "Two-Variable Statistics"' in shown
    assert '1: ["Title","Two-Variable Statistics"]' in shown
    click(named_button(sidebar.variable_list.controls, "Collapse stat variables"))
    click(named_button(sidebar.variable_list.controls, "Collapse tvm variables"))
    assert {row.name: row for row in session.variables()} == original
    assert named_button(sidebar.variable_list.controls, "Expand stat variables")
    assert named_button(sidebar.variable_list.controls, "Expand tvm variables")
    click(named_button(sidebar.variable_list.controls, "Expand stat variables"))
    assert named_button(sidebar.variable_list.controls, "Collapse stat.values")
    assert named_button(sidebar.variable_list.controls, "Collapse stat.results")
    click(named_button(sidebar.variable_list.controls, "Expand tvm variables"))
    assert {row.name: row for row in session.variables()} == original
    click(named_button(sidebar.variable_list.controls, "Collapse stat variables"))
    check_stats_in_another_problem(state, sidebar, runner)
    state.document.go(0, 0)
    sidebar.refresh()
    click(named_button(sidebar.variable_list.controls, "Expand stat variables"))
    assert named_button(sidebar.variable_list.controls, "Collapse stat.values")
    assert named_button(sidebar.variable_list.controls, "Collapse stat.results")
    assert {row.name: row for row in session.variables()} == original
