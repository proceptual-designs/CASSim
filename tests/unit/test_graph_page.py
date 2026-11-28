"""FR-GRAPH-001, FR-GRAPH-002, FR-GRAPH-004, FR-GRAPH-006: initial function Graphs page."""

import pytest

from cassim.core.session import Session
from cassim.device.editor import Kind, Template, format_target
from cassim.device.engine import EngineCore, EngineError, RemoteSession, graph_compile_op
from cassim.device.keys import Binding
from cassim.devices.nspire.document import Document, PageKind, loads
from cassim.devices.nspire.pages.graphs import (
    FUNCTION_COLOURS,
    GRAPH_ANS,
    Graphs,
    GridStyle,
    axis_drag_factor,
    axis_grabbed,
    function_colour,
    graphs_of,
)
from cassim.devices.nspire.ui.state import AppState
from cassim.doc.serialize import dumps
from cassim.graph.sampling import Window
from cassim.graph.scene import Dots, Label, Polyline, Segments


def test_function_entry_creates_a_shared_problem_function_and_curve() -> None:
    session = Session()
    graphs = Graphs(session)
    graphs.submit(0, "x^2-4")

    assert session.is_function("f1")
    assert session.eval("f1(3)").text == "5"
    scene = graphs.scene(400, 280)
    curves = scene.layer("curves")
    assert curves is not None
    assert len(curves.shapes) == 1
    assert isinstance(curves.shapes[0], Polyline)


def test_invalid_function_reports_an_error_without_drawing_a_curve() -> None:
    graphs = Graphs(Session())
    graphs.submit(0, "gamma(x)")

    assert graphs.functions[0].error
    assert graphs.functions[0].compiled is None
    curves = graphs.scene(400, 280).layer("curves")
    assert curves is not None
    assert curves.shapes == ()


def test_visibility_and_zoom_change_the_rendered_graph() -> None:
    graphs = Graphs(Session())
    graphs.submit(0, "x")
    default_scene = graphs.scene(400, 280)
    graphs.toggle("f1")
    hidden_scene = graphs.scene(400, 280)
    assert default_scene.layer("curves") != hidden_scene.layer("curves")
    hidden_curves = hidden_scene.layer("curves")
    assert hidden_curves is not None
    assert hidden_curves.shapes == ()

    graphs.toggle("f1")
    graphs.zoom(0.5)
    assert graphs.window.x_min == -5
    assert graphs.window.x_max == 5


def test_default_axes_use_ticks_and_end_values_without_a_grid() -> None:
    graphs = Graphs(Session())
    axes = graphs.scene(400, 280).layer("grid")
    assert axes is not None
    segments = [shape for shape in axes.shapes if isinstance(shape, Segments)]
    assert len(segments) == 1
    assert segments[0].stroke.colour == "axis"
    points = segments[0].points
    assert ((220, 137), (220, 143)) in list(zip(points[::2], points[1::2], strict=True))
    labels = [shape.text for shape in axes.shapes if isinstance(shape, Label)]
    assert labels == ["-10", "10", "x", "1", "6.67", "-6.67", "y", "1"]


def test_axes_outside_the_window_do_not_draw_false_grid_lines() -> None:
    graphs = Graphs(Session())
    graphs.set_window(Window(2, 6, 3, 7))
    axes = graphs.scene(400, 280).layer("grid")
    assert axes is not None
    assert axes.shapes == ()

    graphs.set_window(Window(2, 6, -2, 2))
    axes = graphs.scene(400, 280).layer("grid")
    assert axes is not None
    labels = [shape.text for shape in axes.shapes if isinstance(shape, Label)]
    assert "x" in labels
    assert "y" not in labels


def test_zoomed_axis_end_values_remain_distinguishable() -> None:
    graphs = Graphs(Session())
    graphs.set_window(Window(1000, 1001, -2, 2))
    axes = graphs.scene(400, 280).layer("grid")
    assert axes is not None
    labels = [shape.text for shape in axes.shapes if isinstance(shape, Label)]
    assert labels[:2] == ["1000", "1001"]


def test_graph_view_menu_controls_axes_end_values_and_grid() -> None:
    """FR-GRAPH-002: Graphs View follows the observed axes and grid options."""
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x^2")

    def pick(*keys: str) -> None:
        state.key_event("F2")
        for key in keys:
            state.key_event(key)

    pick("2", "8")
    axes = graphs.scene(400, 280).layer("grid")
    assert axes is not None
    assert [shape.text for shape in axes.shapes if isinstance(shape, Label)] == ["x", "1", "y", "1"]
    pick("2", "6", "2")
    pick("2", "5")
    scene = graphs.scene(400, 280)
    grid = scene.layer("grid")
    assert grid is not None
    assert len(grid.shapes) == 1
    assert isinstance(grid.shapes[0], Dots)
    assert len(grid.shapes[0].points) > 1
    curves = scene.layer("curves")
    assert curves is not None
    assert curves.shapes

    state.key_event("F2")
    state.key_event("2")
    assert state.menu is not None
    rows = {row.label: row for row in state.menu.view().rows}
    assert "Show axes" in rows
    assert not rows["Show axes end values"].enabled
    state.key_event("8")
    assert state.menu is not None
    state.key_event("5")
    assert graphs.show_axes
    assert not graphs.show_end_values

    pick("2", "6", "3")
    grid = graphs.scene(400, 280).layer("grid")
    assert grid is not None
    assert isinstance(grid.shapes[0], Segments)
    assert grid.shapes[0].stroke.colour == "grid"
    pick("2", "6", "1")
    assert graphs.grid_style is GridStyle.NONE
    pick("2", "8")
    assert graphs.show_end_values


def test_graph_view_settings_survive_save_load() -> None:
    """FR-DOC-003: preserve Graphs view settings in CASSim documents."""
    state = AppState()
    state.run_action("add_page", "graphs")
    state.run_action("graphs_view", "dot")
    state.run_action("graphs_view", "end-values")
    state.run_action("graphs_view", "axes")

    restored = loads(dumps(state.document))
    graphs = graphs_of(restored.current)
    assert graphs is not None
    assert graphs.grid_style is GridStyle.DOT
    assert not graphs.show_axes
    assert not graphs.show_end_values
    grid = graphs.scene(400, 280).layer("grid")
    assert grid is not None
    assert len(grid.shapes) == 1
    assert isinstance(grid.shapes[0], Dots)
    second = graphs_of(restored.add_page(PageKind.GRAPHS))
    assert second is not None
    assert second.grid_style is GridStyle.NONE
    assert second.show_axes
    assert second.show_end_values


def test_pan_and_zoom_gesture_keeps_the_focal_point_in_place() -> None:
    graphs = Graphs(Session())
    graphs.set_window(Window(-10, 10, -10, 10))
    graphs.scene(120, 100)

    graphs.gesture(12, 20, 0.5, 30, 25)

    assert graphs.window == Window(-9.5, 0.5, 1.5, 11.5)


def test_graph_gesture_action_updates_the_active_page() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.set_window(Window(-10, 10, -10, 10))
    graphs.scene(120, 100)

    state.run_action("graphs_gesture", "12,20,0.5,30,25")

    assert graphs.window == Window(-9.5, 0.5, 1.5, 11.5)


def test_graph_editor_uses_calculator_bindings_and_submits_a_template() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    for action, argument in (
        ("insert", "x"),
        ("template", "fraction"),
        ("insert", "2"),
        ("up", ""),
        ("right", ""),
        ("enter", ""),
    ):
        state.run_action(action, argument)

    entry = graphs.functions[0]
    assert isinstance(entry.editing.editor.root[0], Template)
    assert entry.editing.editor.root[0].kind is Kind.FRACTION
    assert entry.compiled is not None
    assert entry.compiled(6) == 3
    assert state.document.problems[0].session.is_function("f1")


def test_an_operator_typed_first_in_a_graph_entry_gets_no_ans() -> None:
    """FR-GRAPH-001: `-x` typed into a function entry is `-x`, not `Ans-x` (PLAN.md M4 notes, 1);
    the Calculator's `Ans` prefix stays on the Calculator's entry line."""
    state = AppState()
    state.run_action("insert", "5")
    state.run_action("enter", "")  # an answer exists on the Problem
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    state.run_action("insert", "-")
    state.run_action("insert", "x")
    state.run_action("enter", "")

    entry = graphs.functions[0]
    assert entry.expression == "-x"
    assert entry.compiled is not None
    assert entry.compiled(2) == -2

    graphs.functions[1].editing.perform(Binding("power", "2"))
    assert graphs.functions[1].editing.editor.linear() == "^(2)"


def test_graph_editor_accepts_keyboard_and_keypad_navigation() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    assert state.key_event("x")
    state.press_keypad("ctrl")
    state.press_keypad("div")
    assert state.key_event("2")
    editor = graphs.functions[0].editing.editor
    assert editor.path == [(0, 1)]
    state.press_keypad("up")
    assert editor.path == [(0, 0)]
    state.press_keypad("down")
    assert editor.path == [(0, 1)]
    state.press_keypad("enter")
    assert graphs.functions[0].compiled is not None
    assert graphs.functions[0].compiled(8) == 4


def test_graph_up_down_and_history_menu_select_one_function_slot() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x^2")

    state.key_event("ArrowDown")
    assert graphs.active_index == 1
    state.key_event("ArrowUp")
    assert graphs.active_index == 0

    state.run_action("open_menu", "graphs_history")
    assert state.menu is not None
    assert [row.label for row in state.menu.view().rows] == ["f1(x) = x^2", "f2(x) = …"]
    state.key_event("2")
    assert state.menu is None
    assert graphs.active_index == 1


def test_graph_goto_selects_the_first_empty_function_slot() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x^2")
    graphs.add_function()

    graphs.active_index = 0
    state.key_event("g", ctrl=True)

    assert graphs.active_index == 1


def test_graph_editor_can_insert_a_shared_problem_variable_from_the_menu() -> None:
    state = AppState()
    state.document.problems[0].session.eval("a:=2")
    state.run_action("add_page", "graphs")
    state.run_action("open_menu", "variables")
    assert state.menu is not None
    names = [item.label for item in state.menu.root.items]
    index = names.index("a")
    state.run_action("menu_pick", f"0:{index}")
    graphs = state.graphs
    assert graphs is not None
    assert graphs.functions[0].editing.editor.linear() == "a"


def test_graph_editor_selection_clipboard_undo_and_row_focus() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    state.run_action("insert", "x")
    state.run_action("power", "2")
    state.run_action("enter")
    state.run_action("place", f"1:{format_target([], 0)}")
    state.run_action("insert", "3")
    state.run_action("undo")
    assert graphs.functions[1].editing.editor.is_empty
    state.run_action("redo")
    assert graphs.functions[1].editing.editor.linear() == "3"

    state.run_action("place", f"0:{format_target([], 0)}")
    state.run_action("select_all")
    state.run_action("copy")
    state.run_action("place", f"1:{format_target([], 1)}")
    state.run_action("paste")
    editor = graphs.functions[1].editing.editor
    assert editor.linear() == "3x^(2)"
    assert isinstance(editor.root[-1], Template)
    assert graphs.active_index == 1


def test_graph_editor_templates_and_unsubmitted_drafts_survive_save_load() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    state.run_action("insert", "x")
    state.run_action("power", "2")
    state.run_action("enter")
    state.run_action("place", f"1:{format_target([], 0)}")
    state.run_action("template", "root")
    state.run_action("insert", "x")

    restored = loads(dumps(state.document))
    graphs = graphs_of(restored.current)
    assert graphs is not None
    assert graphs.functions[0].compiled is not None
    assert graphs.functions[0].compiled(3) == 9
    assert isinstance(graphs.functions[0].editing.editor.root[-1], Template)
    draft = graphs.functions[1].editing.editor
    assert isinstance(draft.root[0], Template)
    assert draft.root[0].kind is Kind.ROOT
    assert graphs.functions[1].expression == ""


def test_graph_save_restores_plotted_expression_and_a_separate_edited_draft() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    state.run_action("insert", "x")
    state.run_action("enter")
    state.run_action("insert", "+")
    state.run_action("insert", "3")

    restored = loads(dumps(state.document))
    graphs = graphs_of(restored.current)
    assert graphs is not None
    entry = graphs.functions[0]
    assert entry.compiled is not None
    assert entry.compiled(2) == 2
    assert entry.editing.editor.linear() == "x+3"
    graphs.submit_editor(0)
    assert entry.compiled is not None
    assert entry.compiled(2) == 5


def test_graph_save_restores_the_active_function_slot() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x")
    graphs.submit_editor(0)
    graphs.edit(Binding("insert", "+"))
    graphs.edit(Binding("insert", "1"))
    graphs.add_function()
    graphs.active_index = 1

    restored = loads(dumps(state.document))
    restored_graphs = graphs_of(restored.current)
    assert restored_graphs is not None
    assert restored_graphs.active_index == 1
    assert restored_graphs.functions[0].editing.editor.linear() == "x+1"


def test_graph_compile_op_runs_in_the_engine_and_preserves_ans() -> None:
    engine = EngineCore()
    initial = engine.apply(0, [{"op": "eval", "line": "7", "approximate": False}])
    assert initial["result"] is not None

    reply = engine.apply(0, [graph_compile_op("f1", "x^2+1")])
    assert reply["graph_compiles"] is not None
    compiled = reply["graph_compiles"][0]
    assert compiled["name"] == "f1"
    assert compiled["error"] is None
    assert compiled["source"] is not None

    answer = engine.apply(0, [{"op": "eval", "line": "Ans", "approximate": False}])
    assert answer["result"] is not None
    assert answer["result"]["text"] == "7"


def test_graph_compile_is_checked_and_returns_expression_errors() -> None:
    engine = EngineCore()
    reply = engine.apply(0, [graph_compile_op("f1", "x+z")])
    assert reply["graph_compiles"] is not None
    assert reply["graph_compiles"][0]["source"] is None
    assert "only use the variable" in (reply["graph_compiles"][0]["error"] or "")
    with pytest.raises(EngineError, match="invalid graph function name"):
        engine.apply(0, [{"op": "graph_compile", "name": "bad", "expression": "x"}])


def test_remote_graph_compile_reaches_the_model_and_save_load_replays() -> None:
    remote = RemoteSession(0)
    engine = EngineCore()
    graphs = Graphs(remote)
    graphs.submit(0, "x+2")
    sent = remote.take()
    reply = engine.apply(0, sent)
    remote.accept(sent, reply)
    graphs.update()
    assert graphs.functions[0].compiled is not None
    assert graphs.functions[0].compiled(3) == 5
    curves = graphs.scene(400, 280).layer("curves")
    assert curves is not None
    assert isinstance(curves.shapes[0], Polyline)

    document = Document()
    page = document.add_page(PageKind.GRAPHS)
    graphs = graphs_of(page)
    assert graphs is not None
    graphs.submit(0, "x+2")
    text = dumps(document)
    restored = loads(text)
    restored_graphs = graphs_of(restored.current)
    assert restored_graphs is not None
    assert restored_graphs.functions[0].expression == "x+2"
    assert restored_graphs.functions[0].compiled is not None
    assert restored_graphs.functions[0].compiled(3) == 5


def test_local_graph_creation_uses_a_new_function_name_on_each_page() -> None:
    document = Document()
    first = graphs_of(document.add_page(PageKind.GRAPHS))
    assert first is not None
    first.submit(0, "x")
    second = graphs_of(document.add_page(PageKind.GRAPHS))
    assert second is not None
    assert second.functions[0].name == "f2"


def test_multiple_graph_pages_reload_without_creating_extra_function_rows() -> None:
    """FR-DOC-003: function slots on later Graphs pages survive document replay."""
    document = Document()
    for expression in ("x", "x+1", "x+2"):
        graphs = graphs_of(document.add_page(PageKind.GRAPHS))
        assert graphs is not None
        graphs.submit(0, expression)

    restored = loads(dumps(document))
    for index, page in enumerate(restored.problems[0].pages[1:], start=1):
        graphs = graphs_of(page)
        assert graphs is not None
        assert [entry.name for entry in graphs.functions] == [f"f{index}", f"f{index + 1}"]
        assert graphs.functions[0].compiled is not None
        assert graphs.functions[0].compiled(2) == index + 1


def test_f99_does_not_create_an_unusable_f100_entry() -> None:
    graphs = Graphs(Session(), tuple(f"f{number}" for number in range(1, 99)))
    assert graphs.functions[0].name == "f99"
    graphs.submit(0, "x")
    assert len(graphs.functions) == 1


def test_f99_reloads_when_earlier_function_slots_are_reserved() -> None:
    """FR-DOC-003: a high-numbered Graphs function keeps its name on reload."""
    state = AppState()
    state.run_action("insert", "f98(x):=x")
    state.run_action("enter")
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x+1")

    restored = loads(dumps(state.document))
    graphs = graphs_of(restored.current)
    assert graphs is not None
    assert [entry.name for entry in graphs.functions] == ["f99"]
    assert graphs.functions[0].compiled is not None
    assert graphs.functions[0].compiled(2) == 3


def test_function_colours_follow_the_function_number_in_ti_order() -> None:
    """FR-GRAPH-001: blue, red, black, magenta, green, orange, brown, then round again (R5-D36,
    G-D12h: f8 is blue and f9 red)."""
    names = [f"f{number}" for number in range(1, 10)]
    assert [function_colour(name) for name in names] == [
        "graph_blue",
        "graph_red",
        "ink",
        "graph_magenta",
        "graph_green",
        "graph_orange",
        "graph_brown",
        "graph_blue",
        "graph_red",
    ]
    assert tuple(function_colour(name) for name in names[:7]) == FUNCTION_COLOURS


def test_a_curve_keeps_its_colour_across_pages_of_a_problem() -> None:
    """FR-GRAPH-001: the colour follows fN, so f2 on a second page is red, not blue."""
    document = Document()
    first = graphs_of(document.add_page(PageKind.GRAPHS))
    assert first is not None
    first.submit(0, "x")
    second = graphs_of(document.add_page(PageKind.GRAPHS))
    assert second is not None
    second.submit(0, "x+1")
    curves = second.scene(400, 280).layer("curves")
    assert curves is not None
    assert {shape.stroke.colour for shape in curves.shapes if isinstance(shape, Polyline)} == {
        "graph_red"
    }
    first_curves = first.scene(400, 280).layer("curves")
    assert first_curves is not None
    assert {
        shape.stroke.colour for shape in first_curves.shapes if isinstance(shape, Polyline)
    } == {"graph_blue"}


def test_a_function_set_from_text_keeps_its_templates() -> None:
    """FR-CALC-004: text from a saved file or a menu is parsed into templates (decision 0035), so
    `(x-1)^2-1` keeps `2` as its exponent and a saved fraction comes back stacked."""
    graphs = Graphs(Session())
    graphs.submit(0, "(x-1)^2-1+((1)/(2))")
    editor = graphs.functions[0].editing.editor
    templates = [node for node in editor.root if isinstance(node, Template)]
    assert [t.kind for t in templates] == [Kind.POWER, Kind.FRACTION]
    assert templates[0].slots == [["2"]]
    assert editor.pos == len(editor.root)


def test_a_restriction_is_labelled_with_a_brace() -> None:
    """R6-A9: `x^2|x>0` is labelled `f1(x)={x², x>0`; a `|` substitution is not a brace."""
    graphs = Graphs(Session())
    graphs.submit(0, "x^2|x>0")
    assert graphs.functions[0].latex == r"\begin{cases}x{}^{2}, & x\gt 0\end{cases}"
    graphs.submit(0, "x^2|x=2")
    assert r"\begin{cases}" not in graphs.functions[0].latex


def test_an_empty_last_condition_of_a_piecewise_is_labelled_else() -> None:
    """R6-A9: the piecewise template with no last condition reads `Else`."""
    graphs = Graphs(Session())
    editor = graphs.functions[0].editing.editor
    editor.insert_template(Kind.PIECEWISE)
    template = editor.root[0]
    assert isinstance(template, Template)
    template.slots[0][:] = list("x+1")
    template.slots[1][:] = list("x<0")
    template.slots[2][:] = list("x")
    graphs.submit(0, editor.linear())
    assert graphs.functions[0].latex.endswith(r"x, & \mathrm{Else}\end{cases}")


def _curve_xs(graphs: Graphs) -> list[float]:
    curves = graphs.scene(400, 280).layer("curves")
    assert curves is not None
    window, xs = graphs.window, []
    for shape in curves.shapes:
        if isinstance(shape, Polyline):
            xs.extend(
                window.x_min + x * (window.x_max - window.x_min) / 400 for x, _ in shape.points
            )
    return xs


@pytest.mark.parametrize(
    ("expression", "low", "high"),
    [
        ("sqrt(x)", 0, 10),
        ("ln(x)", 0, 10),
        ("1/sqrt(4-x^2)", -2, 2),
        ("x^(1/3)", -10, 10),
    ],
)
def test_a_function_is_drawn_only_where_it_is_real(
    expression: str, low: float, high: float
) -> None:
    """R6-A10 and Simon's note 3: no error, no message, and only the real part is drawn;
    `x^(1/3)` is the real cube root, so it is drawn for x<0 too."""
    graphs = Graphs(Session())
    graphs.submit(0, expression)
    assert graphs.functions[0].error == ""
    xs = _curve_xs(graphs)
    assert xs
    step = (graphs.window.x_max - graphs.window.x_min) / 400
    assert min(xs) >= low - step
    assert max(xs) <= high + step
    if expression == "x^(1/3)":
        assert min(xs) < -9


def _graphs_state(*expressions: str) -> tuple[AppState, Graphs]:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    for index, expression in enumerate(expressions):
        graphs.submit(index, expression)
    return state, graphs


def test_an_operator_typed_first_in_a_graph_entry_takes_no_ans() -> None:
    """Simon's note 1 (2026-11-22): the Calculator's `Ans` prefix stays out of graph entries."""
    state, graphs = _graphs_state()
    state.key_event("-")
    state.key_event("x")
    assert graphs.functions[graphs.active_index].editing.editor.linear() == "-x"


def test_tab_opens_the_first_empty_function() -> None:
    """Simon's note 2: Tab on a Graphs page opens the entry line on the first empty fN, as
    ctrl+G does."""
    state, graphs = _graphs_state("x^2", "x+1")
    graphs.select_function(0)
    state.key_event("Tab")
    assert graphs.functions[graphs.active_index].name == "f3"


def test_a_drag_on_an_axis_rescales_both_axes_about_the_origin() -> None:
    """R6-A1 (Handheld view): a drag starting on either axis is a rescale about the origin,
    not a pan; away from the origin zooms in, toward it zooms out. Off the axes it pans."""
    origin = (159.0, 106.0)
    assert axis_grabbed(origin, (175.0, 108.0)) == "x"
    assert axis_grabbed(origin, (157.0, 80.0)) == "y"
    assert axis_grabbed(origin, (200.0, 150.0)) is None
    assert axis_grabbed(origin, (161.0, 107.0)) is None  # at the origin: a pan
    assert axis_drag_factor("x", origin, (175.0, 108.0), (195.0, 108.0)) == pytest.approx(16 / 36)
    assert axis_drag_factor("y", origin, (157.0, 80.0), (157.0, 93.0)) == pytest.approx(26 / 13)
    assert axis_drag_factor("x", origin, (175.0, 108.0), (140.0, 108.0)) == 1.0  # across: none
    graphs = Graphs(Session())
    graphs.scene(318, 212)  # the plot size the gesture works in
    before = graphs.window
    graphs.gesture(0, 0, 0.5, 159.0, 106.0)
    assert graphs.window.x_max == pytest.approx(before.x_max / 2)
    assert graphs.window.y_max == pytest.approx(before.y_max / 2)


def test_ans_is_refused_in_a_graph_and_var_types_a_function_with_its_brackets() -> None:
    """Emulator run 7, R7-B11: `Ans` in a graph's entry gives an error on Enter and stays to be
    edited; the var list types `f1()` with the cursor between the brackets."""
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x^2")
    graphs.submit(1, "Ans+1")
    assert graphs.functions[1].error == GRAPH_ANS
    assert graphs.functions[1].compiled is None
    assert graphs.functions[1].editing.editor.linear() == "Ans+1"
    graphs.submit(1, "")
    graphs.active_index = 1
    menu = state._variables_menu()
    assert menu is not None
    item = next(item for item in menu.items if item.arg.startswith("f1("))
    assert item.action == "insert_linear"
    state.run(Binding("insert_linear", item.arg))
    editor = graphs.functions[1].editing.editor
    assert editor.linear() == "f1()"
