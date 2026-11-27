"""FR-GRAPH-003: Analyze Graph on the Graphs page: prompts, kept results that recompute when
the function changes (graphs D14, graphs5 R5-D32 and R5-D33)."""

import math

import pytest

from cassim.device.keys import Binding
from cassim.devices.nspire.document import loads
from cassim.devices.nspire.pages import graph_analyze
from cassim.devices.nspire.pages.graph_analyze import AnalysisObject
from cassim.devices.nspire.pages.graph_tools import Tool
from cassim.devices.nspire.pages.graphs import Graphs, graphs_of
from cassim.devices.nspire.ui.state import AppState
from cassim.doc.serialize import dumps
from cassim.graph.scene import Dots, Fill, Label, Segments

WIDTH, HEIGHT = 318.0, 212.0


def page(*expressions: str) -> tuple[AppState, Graphs]:
    state = AppState()
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    for index, expression in enumerate(expressions):
        graphs.submit(index, expression)
    graphs.scene(WIDTH, HEIGHT)
    return state, graphs


def pick(state: AppState, *keys: str) -> None:
    state.key_event("F2")
    for key in keys:
        state.key_event(key)


def labels(graphs: Graphs, layer: str) -> list[str]:
    found = graphs.scene(WIDTH, HEIGHT).layer(layer)
    assert found is not None
    return [shape.text for shape in found.shapes if isinstance(shape, Label)]


def screen_x(x: float) -> float:
    return (x + 10) * WIDTH / 20


def bound(state: AppState, x: float) -> None:
    state.run_action("graphs", f"tap:{screen_x(x)},100")


def test_analyze_graph_menu_is_numbered_as_on_the_device() -> None:
    state, _ = page("x^2")
    pick(state, "6")
    assert state.menu is not None
    rows = state.menu.view().rows
    assert [(row.key, row.label, row.enabled) for row in rows] == [
        ("1", "Zero", True),
        ("2", "Minimum", True),
        ("3", "Maximum", True),
        ("4", "Intersection", True),
        ("5", "Inflection", True),
        ("6", "dy/dx", True),
        ("7", "Integral", True),
        ("8", "Bounded Area", True),
        ("9", "Analyze conics", False),
    ]


def test_zero_asks_for_bounds_and_marks_the_point() -> None:
    """D14: `lower bound?`, `upper bound?`, then the point (-1.73,0) of x^3-3x."""
    state, graphs = page("x^3-3x")
    pick(state, "6", "1")
    assert graphs.tools.tool is Tool.ANALYZE
    assert labels(graphs, "tool") == ["lower bound?"]
    tool = graphs.scene(WIDTH, HEIGHT).layer("tool")
    assert tool is not None
    assert any(isinstance(shape, Segments) and shape.stroke.dashed for shape in tool.shapes)
    bound(state, -2.5)
    assert labels(graphs, "tool") == ["upper bound?"]
    bound(state, -1)
    assert labels(graphs, "analysis") == ["(-1.73,0)"]
    assert labels(graphs, "tool") == ["lower bound?"]  # the tool stays on for another
    state.key_event("Escape")
    assert graphs.tools.tool is None
    assert labels(graphs, "analysis") == ["(-1.73,0)"]


def test_a_zero_that_touches_the_axis_is_found() -> None:
    """graphs2 D14: Zero on x^2 gave (0,0)."""
    state, graphs = page("x^2")
    pick(state, "6", "1")
    bound(state, -3)
    bound(state, 4)
    assert labels(graphs, "analysis") == ["(0,0)"]


def test_no_zero_in_the_bounds_says_so() -> None:
    """graphs2 D14: "No zero found within the specified bounds"."""
    state, graphs = page("x^2+1")
    pick(state, "6", "1")
    bound(state, -3)
    bound(state, 3)
    # an Error dialog over the graph (R6-A8); other keys wait, Enter closes it
    assert labels(graphs, "tool") == ["Error", "No zero found within the specified bounds", "OK"]
    assert graphs.objects == []
    state.key_event("ArrowLeft")
    assert "OK" in labels(graphs, "tool")
    state.key_event("Enter")
    assert labels(graphs, "tool") == ["lower bound?"]


def test_kept_points_follow_the_function_when_it_changes() -> None:
    """R5-D32: zero and maximum of f2 = sin(x) move when f2 is redefined as 2sin(x)."""
    state, graphs = page("x^2", "sin(x)")
    pick(state, "6", "3")
    assert labels(graphs, "tool") == ["graph? f1"]
    state.key_event("ArrowDown")
    assert labels(graphs, "tool") == ["graph? f2"]
    state.key_event("Enter")
    assert labels(graphs, "tool") == ["lower bound?"]
    state.key_event("0")
    state.key_event("Enter")
    state.key_event("3")
    state.key_event("Enter")
    assert labels(graphs, "analysis") == ["(1.57,1)"]
    state.key_event("Escape")
    graphs.submit(1, "2sin(x)")
    assert labels(graphs, "analysis") == ["(1.57,2)"]
    graphs.submit(1, "x+5")  # the greatest value is now at the upper bound (R6-A8)
    assert labels(graphs, "analysis") == ["(3,8)"]


def test_a_tap_picks_the_nearest_graph() -> None:
    state, graphs = page("x^2", "x-5")
    pick(state, "6", "2")
    state.run_action("graphs", f"tap:{screen_x(2)},{(20 / 3 + 3) * HEIGHT / (40 / 3)}")
    assert graphs.tools.picked == ["f2"]


def test_integral_shades_and_stays_live() -> None:
    """R5-D33: typed bounds 0 and 2 on cos(x) give 0.909; 2sin(x) then gives 2.83."""
    state, graphs = page("cos(x)")
    pick(state, "6", "7")
    for key in ("0", "Enter", "2", "Enter"):
        state.key_event(key)
    analysis = graphs.scene(WIDTH, HEIGHT).layer("analysis")
    assert analysis is not None
    assert any(isinstance(shape, Fill) for shape in analysis.shapes)
    assert sum(len(shape.points) for shape in analysis.shapes if isinstance(shape, Dots)) == 2
    assert labels(graphs, "analysis") == ["0.909"]
    graphs.submit(0, "2sin(x)")
    assert labels(graphs, "analysis") == ["2.83"]


def test_intersection_and_bounded_area_use_both_graphs() -> None:
    """graphs2 D14: with two graphs, no `graph?` prompt; (1.3,2.3) for 4-x^2 and x+1."""
    state, graphs = page("4-x^2", "x+1")
    pick(state, "6", "4")
    assert labels(graphs, "tool") == ["lower bound?"]
    bound(state, 0)
    bound(state, 2)
    assert labels(graphs, "analysis") == ["(1.3,2.3)"]
    state.key_event("Escape")
    pick(state, "6", "8")
    bound(state, -1.5)
    bound(state, 0)
    assert labels(graphs, "analysis")[-1] == "4.5"  # the integral of 3-x-x^2 over -1.5..0


def test_minimum_inflection_and_dydx() -> None:
    state, graphs = page("x^3-3x")
    pick(state, "6", "2")
    bound(state, 0)
    bound(state, 2)
    state.key_event("Escape")
    pick(state, "6", "5")
    bound(state, -1)
    bound(state, 1)
    state.key_event("Escape")
    pick(state, "6", "6")
    assert labels(graphs, "tool") == ["position?"]
    bound(state, 2)
    assert labels(graphs, "analysis") == ["(1,-2)", "(0,0)", "dy/dx=9"]


def test_kept_results_survive_save_and_load() -> None:
    state, _ = page("cos(x)")
    pick(state, "6", "7")
    for key in ("0", "Enter", "2", "Enter", "Escape"):
        state.key_event(key)
    restored = graphs_of(loads(dumps(state.document)).current)
    assert restored is not None
    assert restored.objects == [AnalysisObject("integral", ("f1",), (0.0, 2.0))]
    restored.scene(WIDTH, HEIGHT)
    assert labels(restored, "analysis") == ["0.909"]


@pytest.mark.parametrize(
    "data",
    [
        "x",
        {"kind": "spin", "names": ["f1"], "bounds": [0, 1]},
        {"kind": "zero", "names": "f1", "bounds": [0, 1]},
        {"kind": "zero", "names": ["f1", "f2"], "bounds": [0, 1]},
        {"kind": "zero", "names": ["f1"], "bounds": [0]},
        {"kind": "zero", "names": ["f1"], "bounds": [0, math.inf]},
        {"kind": "zero", "names": ["f1"], "bounds": [0, True]},
    ],
)
def test_bad_saved_results_are_dropped(data: object) -> None:
    assert AnalysisObject.load(data) is None


def test_analysis_needs_enough_graphs_and_a_known_item() -> None:
    state, graphs = page("x^2")
    pick(state, "6", "4")  # Intersection needs two graphs
    assert graphs.tools.tool is None
    with pytest.raises(ValueError, match="unknown Analyze Graph item"):
        graph_analyze.start(graphs, "spin")
    assert graph_analyze.key(graphs, Binding("left")) is False
    assert graph_analyze.perform(graphs, "zoom:fit") is False


def test_typing_and_pointer_keys_while_analysing() -> None:
    state, graphs = page("x^2")
    pick(state, "6", "1")
    state.key_event("5")
    assert labels(graphs, "tool") == ["lower bound? 5"]
    state.key_event("Backspace")
    state.run_action("insert", "x")  # not part of a number
    assert labels(graphs, "tool") == ["lower bound?"]
    state.key_event("5")
    state.key_event("Escape")  # drops the typing only
    assert graphs.tools.tool is Tool.ANALYZE
    before = graphs.tools.pointer
    state.key_event("ArrowLeft")
    assert graphs.tools.pointer != before
    state.key_event("Enter")
    assert len(graphs.tools.bounds) == 1
    state.key_event("1")
    state.key_event(".")
    state.key_event(".")
    state.key_event("Enter")  # `1..` is not a number: ignored
    assert len(graphs.tools.bounds) == 1


def test_a_minimum_at_a_bound_is_the_bound_point() -> None:
    """R6-A8: Minimum on x^2 from 1 to 3 marks the lower bound, (1,1)."""
    state, graphs = page("x^2")
    pick(state, "6", "2")
    bound(state, 1)
    bound(state, 3)
    assert labels(graphs, "analysis") == ["(1,1)"]
