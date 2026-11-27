"""FR-GRAPH-002: Graph Trace, Trace All and Trace Step on the Graphs page (graphs D11, D27)."""

import pytest

from cassim.device.wizard import Wizard
from cassim.devices.nspire.pages import graph_tools
from cassim.devices.nspire.pages.graph_tools import Tool, coordinate_text
from cassim.devices.nspire.pages.graphs import Graphs
from cassim.devices.nspire.ui.state import AppState
from cassim.graph.scene import Dots, Label, Segments
from cassim.graph.zoom import STANDARD


def traced(*expressions: str) -> tuple[AppState, Graphs, list[Wizard]]:
    state = AppState()
    shown: list[Wizard] = []
    state.show_wizard = shown.append
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    for index, expression in enumerate(expressions):
        graphs.submit(index, expression)
    graphs.scene(318, 212)
    return state, graphs, shown


def pick(state: AppState, *keys: str) -> None:
    state.key_event("F2")
    for key in keys:
        state.key_event(key)


def readout(graphs: Graphs) -> Label:
    layer = graphs.scene(318, 212).layer("tool")
    assert layer is not None
    labels = [shape for shape in layer.shapes if isinstance(shape, Label)]
    assert len(labels) == 1
    return labels[0]


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0.3 * 0.3 * 0.2955202066613396, "0.027"),
        (-4.3474797933386604, "-4.35"),
        (4.71238898038469, "4.71"),
        (-2.0, "-2"),
        (169.0, "169"),
        (0.8999999999999999, "0.9"),
        (1.302775637731995, "1.3"),
        (0.0, "0"),
        (None, "undef"),
        (12345.6, "1.23ᴇ4"),
        (0.0004, "4.ᴇ-4"),
    ],
)
def test_coordinates_are_shown_in_float_3(value: float | None, text: str) -> None:
    assert coordinate_text(value) == text


def test_trace_menu_is_numbered_as_on_the_device() -> None:
    state, _, _ = traced("x^2")
    pick(state, "5")
    assert state.menu is not None
    rows = state.menu.view().rows
    assert [(row.key, row.label, row.enabled) for row in rows] == [
        ("1", "Graph trace", True),
        ("2", "Trace all", True),
        ("3", "Trace step…", True),
        ("4", "Path plot", False),
        ("5", "Geometry trace", False),
        ("6", "Erase Geometry trace", False),
    ]


def test_graph_trace_starts_at_zero_and_steps_by_one_percent() -> None:
    """The automatic step is 1% of the window width, 0.2 on the Standard window (decision 0034,
    item 7; the device stepped about 0.26 to 0.3, D27 and R5-D11)."""
    state, graphs, _ = traced("x^2", "sin(x)")
    pick(state, "5", "1")
    assert graphs.tools.tool is Tool.TRACE
    label = readout(graphs)
    assert label.text == "f1: (0, 0)"
    assert label.colour == "graph_blue"
    for _ in range(3):
        state.key_event("ArrowRight")
    assert readout(graphs).text == "f1: (0.6, 0.36)"
    layer = graphs.scene(318, 212).layer("tool")
    assert layer is not None
    assert [shape.colour for shape in layer.shapes if isinstance(shape, Dots)] == ["graph_blue"]
    state.key_event("ArrowLeft")
    assert readout(graphs).text == "f1: (0.4, 0.16)"


def test_up_and_down_move_between_graphs_and_wrap() -> None:
    """G-D11d: Up from f1 went to f3 (the last); Down goes on to the next."""
    state, graphs, _ = traced("x^2", "sin(x)", "x+1")
    pick(state, "5", "1")
    state.key_event("ArrowUp")
    label = readout(graphs)
    assert label.text == "f3: (0, 1)"
    assert label.colour == "ink"
    state.key_event("ArrowDown")
    assert readout(graphs).text == "f1: (0, 0)"
    state.key_event("ArrowDown")
    assert readout(graphs).text == "f2: (0, 0)"


def test_typed_x_then_enter_moves_the_trace() -> None:
    """graphs4 D11: typing 2 then Return moves the trace point to x = 2."""
    state, graphs, _ = traced("x^3-3x^2+2x-5+sin(x)")
    pick(state, "5", "1")
    state.key_event("2")
    assert readout(graphs).text == "f1: x = 2"
    state.key_event("Backspace")
    state.run_action("insert", "-")
    state.run_action("insert", "1")
    state.run_action("insert", "x")  # not part of a number: ignored
    state.key_event("Enter")
    assert readout(graphs).text == "f1: (-1, -11.8)"
    state.key_event("2")
    state.key_event("Escape")  # the first Esc drops the typing only
    assert graphs.tools.tool is Tool.TRACE
    state.key_event("Escape")
    assert graphs.tools.tool is None
    layer = graphs.scene(318, 212).layer("tool")
    assert layer is not None
    assert layer.shapes == ()


def test_the_window_pans_at_either_edge_and_follows_y() -> None:
    """R5-D11: at the right edge the window moves with the point, and up when it leaves the
    top (f1 = x^2 at x = 13 showed y about 157 to 170.33)."""
    state, graphs, shown = traced("x^2")
    pick(state, "5", "3")
    state.finish_wizard(shown[0], {"mode": "value", "value": "1"})
    assert graphs.tools.trace_step == 1
    pick(state, "5", "1")
    for _ in range(13):
        state.key_event("ArrowRight")
    assert readout(graphs).text == "f1: (13, 169)"
    window = graphs.window
    assert (window.x_min, window.x_max) == pytest.approx((-7, 13))
    assert window.y_max == pytest.approx(169 + 4 / 3)
    assert window.y_max - window.y_min == pytest.approx(40 / 3)
    for _ in range(30):
        state.key_event("ArrowLeft")
    assert graphs.window.x_min == pytest.approx(-17)
    assert graphs.window.y_min == pytest.approx(289 - 40 / 3 + 4 / 3)


def test_a_new_trace_starts_where_the_last_left() -> None:
    """D27: a new trace starts at the x the previous one left."""
    state, graphs, _ = traced("x^2")
    pick(state, "5", "1")
    state.key_event("ArrowRight")
    state.key_event("Escape")
    pick(state, "5", "1")
    assert readout(graphs).text == "f1: (0.2, 0.04)"


def test_trace_all_marks_every_graph_on_one_vertical() -> None:
    """R5-D11: Trace All draws a vertical line and a point on each graph."""
    state, graphs, _ = traced("x^2", "2sin(x)")
    graphs.active_index = 1
    pick(state, "5", "2")
    assert graphs.tools.tool is Tool.TRACE_ALL
    layer = graphs.scene(318, 212).layer("tool")
    assert layer is not None
    assert any(isinstance(shape, Segments) for shape in layer.shapes)
    assert [shape.colour for shape in layer.shapes if isinstance(shape, Dots)] == [
        "graph_blue",
        "graph_red",
    ]
    assert readout(graphs).text == "f2: (0, 0)"


def test_a_tap_moves_the_trace_to_that_x() -> None:
    state, graphs, _ = traced("x^2")
    pick(state, "5", "1")
    state.run_action("graphs", "tap:238.5,10")
    assert readout(graphs).text == "f1: (5, 25)"


def test_trace_step_dialog_has_automatic_and_enter_value() -> None:
    state, graphs, shown = traced("x^2")
    pick(state, "5", "3")
    wizard = shown[0]
    assert wizard.title == "Trace step"
    assert wizard.fields[0].choices == (("auto", "Automatic"), ("value", "Enter Value…"))
    assert wizard.defaults()["mode"] == "auto"
    assert state.finish_wizard(wizard, {"mode": "value", "value": "0"}) == [
        "Value: the step must be more than 0"
    ]
    assert state.finish_wizard(wizard, {"mode": "value", "value": "a"}) == ["Value: enter a number"]
    assert state.finish_wizard(wizard, {"mode": "value", "value": "π/4"}) == []
    assert graphs.tools.trace_step == pytest.approx(0.7853981633974483)
    pick(state, "5", "3")
    assert shown[-1].defaults() == {"mode": "value", "value": "0.78539816339745"}
    assert state.finish_wizard(shown[-1], {"mode": "auto", "value": ""}) == []
    assert graphs.tools.trace_step is None
    assert graph_tools.trace_step(graphs) == pytest.approx(0.2)
    with pytest.raises(ValueError, match="positive"):
        graph_tools.set_trace_step(graphs, "-1")


def test_no_trace_without_a_plotted_graph() -> None:
    state, graphs, _ = traced()
    pick(state, "5", "1")
    assert graphs.tools.tool is None
    assert graphs.window == STANDARD


def test_trace_leaves_when_the_graphs_are_hidden() -> None:
    state, graphs, _ = traced("x^2")
    pick(state, "5", "1")
    graphs.toggle("f1")
    state.key_event("ArrowRight")
    assert graphs.tools.tool is None


def test_undefined_points_read_undef_and_draw_no_mark() -> None:
    state, graphs, _ = traced("ln(x)")
    pick(state, "5", "1")
    assert readout(graphs).text == "f1: (0, undef)"
    layer = graphs.scene(318, 212).layer("tool")
    assert layer is not None
    assert not any(isinstance(shape, Dots) for shape in layer.shapes)


def test_graph_page_modules_do_not_load_sympy() -> None:
    """Decision 0027: the UI worker has no SymPy, so the Graphs page and its tools must import
    without it (a SymPy import stopped the app starting in the browser)."""
    import subprocess  # noqa: PLC0415
    import sys  # noqa: PLC0415

    code = (
        "import sys\n"
        "import cassim.devices.nspire.pages.graphs\n"
        "import cassim.devices.nspire.pages.graph_analyze\n"
        "import cassim.graph.zoom\n"
        "print('sympy' in sys.modules)\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "False"


def test_enter_during_a_trace_leaves_a_point_that_stays_after_esc() -> None:
    """R6-A3: Enter at a traced point leaves a dot with its coordinates; Esc ends the trace and
    the point stays."""
    state, graphs, _ = traced("x^2")
    pick(state, "5", "1")
    for _ in range(3):
        state.key_event("ArrowRight")
    state.key_event("Enter")
    assert graphs.tools.tool is Tool.TRACE
    state.key_event("Escape")
    assert graphs.tools.tool is None
    layer = graphs.scene(318, 212).layer("analysis")
    assert layer is not None
    assert [shape.text for shape in layer.shapes if isinstance(shape, Label)] == ["(0.6,0.36)"]
    graphs.submit(0, "2x^2")  # the point follows the function
    layer = graphs.scene(318, 212).layer("analysis")
    assert layer is not None
    assert [shape.text for shape in layer.shapes if isinstance(shape, Label)] == ["(0.6,0.72)"]
