"""FR-GRAPH-004: breaks and ends in Graphs page scenes, against the emulator (graphs D12, D13).

The device draws no line across an asymptote or a jump (`1/x`, `tan(x)`, `1/(x-1)^2`,
`abs(x)/x`, `floor(x)`) and no open or closed circle at the end of a curve (`ln(x)`, `sqrt(x)`,
`sqrt(4-x^2)`, `x^2|x>0`), in the Standard window (graphs3 D12 and D13, graphs5 D12).
"""

import math

import pytest

from cassim.core.session import Session
from cassim.devices.nspire.pages.graphs import Graphs, graph_definition
from cassim.graph.scene import Polyline, Scene

WIDTH, HEIGHT = 318.0, 212.0  # the handheld's plot


def curves(expression: str) -> tuple[Scene, list[Polyline]]:
    graphs = Graphs(Session())
    graphs.submit(0, expression)
    assert graphs.functions[0].error == ""
    scene = graphs.scene(WIDTH, HEIGHT)
    layer = scene.layer("curves")
    assert layer is not None
    assert all(isinstance(shape, Polyline) for shape in layer.shapes)  # no end markers
    shapes = [shape for shape in layer.shapes if isinstance(shape, Polyline)]
    assert shapes
    return scene, shapes


def to_x(screen_x: float) -> float:
    return -10 + screen_x * 20 / WIDTH


def crossings(lines: list[Polyline], breaks: list[float]) -> list[float]:
    """Breaks that a drawn segment joins across."""
    found = []
    for line in lines:
        for (x0, _), (x1, _) in zip(line.points, line.points[1:], strict=False):
            low, high = sorted((to_x(x0), to_x(x1)))
            found.extend(point for point in breaks if low < point < high)
    return found


@pytest.mark.parametrize(
    ("expression", "breaks", "branches"),
    [
        ("1/x", [0.0], 2),
        ("1/(x-1)^2", [1.0], 2),
        ("abs(x)/x", [0.0], 2),
        ("tan(x)", [math.pi / 2 + k * math.pi for k in range(-4, 3)], 7),
        ("floor(x)", [float(k) for k in range(-9, 10)], 20),
    ],
)
def test_no_line_joins_across_a_break(expression: str, breaks: list[float], branches: int) -> None:
    _, lines = curves(expression)
    assert crossings(lines, breaks) == []
    assert len(lines) == branches


def test_floor_steps_are_flat_with_no_vertical_joins() -> None:
    _, lines = curves("floor(x)")
    for line in lines:
        assert len({round(y, 6) for _, y in line.points}) == 1


@pytest.mark.parametrize(
    ("expression", "start", "end"),
    [
        ("ln(x)", 0.0, 10.0),
        ("sqrt(x)", 0.0, 10.0),
        ("sqrt(4-x^2)", -2.0, 2.0),
        ("x^2|x>0", 0.0, math.sqrt(20 / 3)),
    ],
)
def test_a_curve_runs_to_its_domain_end_with_no_marker(
    expression: str, start: float, end: float
) -> None:
    pixel = 20 / WIDTH
    _, lines = curves(expression)
    assert len(lines) == 1
    xs = [to_x(x) for x, _ in lines[0].points]
    assert min(xs) == pytest.approx(start, abs=pixel)
    assert max(xs) >= end - pixel


def test_ln_runs_off_the_bottom_near_the_y_axis() -> None:
    _, lines = curves("ln(x)")
    assert max(y for _, y in lines[0].points) > HEIGHT


@pytest.mark.parametrize(
    ("expression", "definition"),
    [
        ("x^2|x>0", "when(x>0,x^2)"),
        ("x^2|-1<x<2", "when(-1<x<2,x^2)"),
        ("x^2|x=2", "x^2|x=2"),
        ("abs(x|x>0)", "abs(x|x>0)"),
        ("x^2", "x^2"),
        ("|x>0", "|x>0"),
    ],
)
def test_a_restriction_is_stored_as_a_one_piece_piecewise(expression: str, definition: str) -> None:
    """graphs4 D13: `x^2|x>0` is kept as `{x², x>0`, so it is undefined for x ≤ 0."""
    assert graph_definition(expression) == definition


def test_a_restricted_function_is_undefined_outside_on_the_calculator_too() -> None:
    session = Session()
    graphs = Graphs(session)
    graphs.submit(0, "x^2|-1<x<2")
    assert session.eval("f1(1)").text == "1"
    assert session.eval("f1(3)").text == "undef"
    _, lines = curves("x^2|-1<x<2")
    xs = [to_x(x) for x, _ in lines[0].points]
    assert min(xs) == pytest.approx(-1, abs=20 / WIDTH)
    assert max(xs) == pytest.approx(2, abs=20 / WIDTH)
