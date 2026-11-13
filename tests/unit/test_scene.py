# Requirements traced here: FR-GRAPH-006
"""The backend-neutral scene and its canvas drawing (decision 0031, spikes A and C)."""

import flet.canvas as cv
import pytest

from cassim.app import scene_canvas
from cassim.graph.scene import (
    Align,
    Box,
    Dots,
    Fill,
    Label,
    Layer,
    Polyline,
    Scene,
    Segments,
    Stroke,
    column_label,
)


def test_one_canvas_shape_per_curve() -> None:
    """Decision 0004: a curve is one `Points` shape, however many points it has."""
    curve = Polyline(tuple((x, x * x) for x in range(2000)), Stroke("curve1", 2))
    drawn = scene_canvas.shape(curve)
    assert isinstance(drawn, cv.Points)
    assert drawn.point_mode is cv.PointMode.POLYGON
    assert len(drawn.points or []) == 2000


def test_each_kind_of_shape_is_drawn() -> None:
    shapes = [
        Segments(((0, 0), (1, 1), (2, 2), (3, 3))),
        Dots(((1, 1),)),
        Fill(((0, 0), (10, 0), (10, 10))),
        Box(0, 0, 10, 10),
        Label(0, 0, "x", align=Align.RIGHT),
    ]
    kinds = [type(scene_canvas.shape(item)) for item in shapes]
    assert kinds == [cv.Points, cv.Points, cv.Path, cv.Rect, cv.Text]


def test_segments_need_pairs() -> None:
    with pytest.raises(ValueError, match="even"):
        Segments(((0, 0), (1, 1), (2, 2)))


def test_a_column_of_cells_is_one_label_with_rows_a_cell_apart() -> None:
    """Spike A: one multi-line text per column drew the grid fastest."""
    label = column_label((5, 0), ["1", "2.5", "a\nb"], 22)
    assert label.text == "1\n2.5\na b"
    drawn = scene_canvas.shape(label)
    assert isinstance(drawn, cv.Text)
    assert drawn.style is not None
    assert drawn.style.height == pytest.approx(22 / 13)


def test_layers_are_replaced_by_name_so_a_cursor_move_sends_no_text() -> None:
    grid = Layer("cells", (column_label((0, 0), ["1"], 22),))
    cursor = Layer("cursor", (Box(0, 0, 50, 22),))
    scene = Scene(100, 100, (grid, cursor))
    moved = scene.replace(Layer("cursor", (Box(0, 22, 50, 22),)))
    assert moved.layer("cells") is grid
    cursor_layer = moved.layer("cursor")
    assert cursor_layer is not None
    assert cursor_layer.shapes == (Box(0, 22, 50, 22),)
    assert len(scene.replace(Layer("marks")).layers) == 3
    assert scene.layer("none") is None


def test_the_canvas_has_one_layer_per_canvas_and_skips_empty_curves() -> None:
    scene = Scene(
        100,
        50,
        (Layer("a", (Polyline(((0, 0),)), Polyline(((0, 0), (1, 1))))), Layer("b")),
    )
    stack = scene_canvas.canvas(scene)
    assert len(stack.controls) == 2
    first = stack.controls[0]
    assert isinstance(first, cv.Canvas)
    assert len(first.shapes) == 1


def test_theme_colours_override_the_defaults_and_unknown_names_pass_through() -> None:
    drawn = scene_canvas.shape(Polyline(((0, 0), (1, 1)), Stroke("curve1")), {"curve1": "#123456"})
    assert isinstance(drawn, cv.Points)
    assert drawn.paint.color == "#123456"
    other = scene_canvas.shape(Polyline(((0, 0), (1, 1)), Stroke("#abcdef")))
    assert isinstance(other, cv.Points)
    assert other.paint.color == "#abcdef"
