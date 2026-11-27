"""The Graphs page's Actions: Attributes, Text, Coordinates and Equations, Calculate, and dragging
a curve (emulator check 6, run 7: R7-B2, R7-B8, R7-B9 and R7-B10).

Requirements: FR-GRAPH-008.
"""

from __future__ import annotations

import json

import pytest

from cassim.core.session import Session
from cassim.devices.nspire.pages import graph_actions, graph_tools
from cassim.devices.nspire.pages.graphs import Graphs, dump_graphs
from cassim.devices.nspire.ui.state import AppState
from cassim.graph.sampling import Window
from cassim.graph.scene import Dots, Label, Polyline


def graphs_with(*expressions: str) -> Graphs:
    graphs = Graphs(Session())
    for index, expression in enumerate(expressions):
        graphs.submit(index, expression)
    graphs.window = Window(-10, 10, -10, 10)
    graphs.scene(400, 400)  # the page knows its size
    return graphs


@pytest.mark.parametrize(
    ("expression", "dx", "dy", "moved"),
    [
        ("2*sin(x)", 0.9123, -0.0441, "2*sin(x-0.91)-0.044"),  # R7-B2
        ("x^2", 1, 0, "(x-1)^2"),
        ("x", -0.5, 2, "x+0.5+2"),
        ("exp(x)+x", 2, 0, "exp(x-2)+(x-2)"),
        ("max(x,1)", 0, 3, "max(x,1)+3"),
    ],
)
def test_a_dragged_curve_is_translated(expression: str, dx: float, dy: float, moved: str) -> None:
    assert graph_actions.translated(expression, dx, dy) == moved


def test_a_drag_on_a_curve_redefines_it() -> None:
    graphs = graphs_with("x^2")
    assert graph_actions.curve_at(graphs, 200, 200) == 0  # (0, 0) is on x²
    assert graph_actions.curve_at(graphs, 200, 120) is None  # (0, 4) is not
    graph_tools.perform(graphs, "drag_curve:0,40,-40")  # 2 right and 2 up
    assert graphs.functions[0].expression == "(x-2)^2+2"


def test_attributes_change_how_a_graph_is_drawn_and_are_saved() -> None:
    """R7-B8: thick and dashed; discrete as 25 points; the label in style 5, y=x+1."""
    graphs = graphs_with("x+1")
    values = {"weight": "2", "style": "2", "label": "5", "discrete": "0", "points": "25"}
    graph_tools.perform(graphs, f"attributes:f1:{json.dumps(values)}")
    curves = graphs.scene(400, 400).layer("curves")
    assert curves is not None
    lines = [shape for shape in curves.shapes if isinstance(shape, Polyline)]
    assert lines
    assert (lines[0].stroke.width, lines[0].stroke.dashed) == (4.5, True)
    assert [s.text for s in curves.shapes if isinstance(s, Label)] == ["y=x+1"]
    values["discrete"] = "1"
    graph_tools.perform(graphs, f"attributes:f1:{json.dumps(values)}")
    curves = graphs.scene(400, 400).layer("curves")
    assert curves is not None
    (dots,) = [shape for shape in curves.shapes if isinstance(shape, Dots)]
    assert len(dots.points) == graph_actions.DEFAULT_POINTS
    saved = dump_graphs(graphs)
    assert saved["attributes"]["f1"]["discrete"] is True


def test_attributes_dialog_lists_the_devices_rows() -> None:
    graphs = graphs_with("x+1")
    wizard = graph_actions.attributes_wizard(graphs.functions[0], graph_actions.Attributes())
    assert [field.label for field in wizard.fields] == [
        "Line weight",
        "Line style",
        "Label style",
        "Continuous or discrete",
        "Number of points (discrete)",
    ]
    styles = [label for _, label in wizard.fields[2].choices]
    assert styles == ["1: f1", "2: f1(x)", "3: f1(x)=x+1", "4: y=f1(x)", "5: y=x+1"]


def test_text_coordinates_and_calculate_put_text_on_the_page() -> None:
    """R7-B10: Text places typed text; Coordinates and Equations labels a kept point with its
    coordinates and a curve with its equation; Calculate works an expression out beside it."""
    graphs = graphs_with("x^2")
    graph_tools.perform(graphs, "tool:text")
    graph_tools.perform(graphs, "tap:300,100")
    assert graphs.tools.request == ("text", "5.0,5.0")
    graph_tools.perform(graphs, "text:5.0,5.0:3+4")
    graph_tools.perform(graphs, "tool:calculate")
    graph_tools.perform(graphs, "tap:300,100")
    assert [item.text for item in graphs.texts] == ["3+4", "7"]
    graph_tools.perform(graphs, "tool:coordinates")
    graph_tools.perform(graphs, "tap:200,200")  # on x² at the origin
    assert graphs.texts[-1].text == "f1(x)=x^2"
    text = graphs.scene(400, 400).layer("text")
    assert text is not None
    assert [s.text for s in text.shapes if isinstance(s, Label)] == ["3+4", "7", "f1(x)=x^2"]


def test_the_graphs_menu_has_actions_and_graph_entry_numbered_as_on_the_device() -> None:
    state = AppState()
    state.run_action("add_page", "graphs")
    menu = state._graphs_menu()
    assert menu is not None
    actions, _, entry = menu.items[:3]
    assert [(item.key, item.label, item.enabled) for item in actions.items] == [
        ("1", "Pointer", True),
        ("2", "Select", True),
        ("3", "Hide/Show", False),
        ("4", "Attributes", True),
        ("5", "Set Conditions", False),
        ("6", "Delete all", False),
        ("7", "Text", True),
        ("8", "Coordinates and Equations", True),
        ("9", "Calculate", True),
        ("A", "Redefine", False),
    ]
    templates = entry.items[2]
    assert templates.label == "Equation Templates"
    assert [(item.label, len(item.items)) for item in templates.items] == [
        ("Line", 3),
        ("Parabola", 4),
        ("Circle", 2),
        ("Ellipse", 1),
        ("Hyperbola", 2),
        ("Conic", 1),
    ]
