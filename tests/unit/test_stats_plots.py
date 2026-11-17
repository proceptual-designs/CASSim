# Requirements traced here: FR-STAT-001, FR-STAT-005
"""Backend-neutral Data & Statistics plots for numeric and categorical data."""

import math

from cassim.graph.scene import Dots, Fill, Label, Polyline
from cassim.stats.data import parse_items
from cassim.stats.plots import PlotData, PlotType, plot_scene


def _shapes(data: PlotData):
    return tuple(shape for layer in plot_scene(data, 320, 220).layers for shape in layer.shapes)


def test_list_items_parse_numeric_values_categories_and_voids() -> None:
    assert parse_items(("1", '"dog"', "_", "1/2", "2ᴇ3", "ⅇ", "e")) == (
        1.0,
        "dog",
        None,
        0.5,
        2000.0,
        math.e,
        None,
    )


def test_numeric_histogram_draws_bars_and_normal_pdf_overlay() -> None:
    shapes = _shapes(
        PlotData(
            plot_type=PlotType.HISTOGRAM,
            x_name="scores",
            x=(1.0, 2.0, 3.0),
            histogram_width=1,
            histogram_scale="Density",
            normal_pdf=((1.0, 0.1), (3.0, 0.1)),
        )
    )
    assert sum(isinstance(shape, Fill) for shape in shapes) == 3
    assert any(isinstance(shape, Polyline) for shape in shapes)


def test_constant_data_normal_probability_plot_does_not_divide_by_zero() -> None:
    shapes = _shapes(
        PlotData(
            plot_type=PlotType.NORMAL_PROBABILITY,
            x_name="scores",
            x=(2.0, 2.0, 2.0),
        )
    )
    assert any(isinstance(shape, Dots) for shape in shapes)
    assert any(isinstance(shape, Label) and shape.text == "Constant data" for shape in shapes)


def test_grouped_numeric_plot_ignores_unpaired_tail_values() -> None:
    shapes = _shapes(
        PlotData(
            plot_type=PlotType.DOT,
            x_name="group",
            x=("B", "A", "A"),
            y_name="score",
            y=(10.0, 20.0),
        )
    )
    assert any(isinstance(shape, Dots) for shape in shapes)


def test_categorical_chart_uses_alphabetical_category_order_by_default() -> None:
    scene = plot_scene(
        PlotData(
            plot_type=PlotType.BAR,
            x_name="responses",
            x=("C", "A", "B", "A"),
        ),
        320,
        220,
    )
    labels = [
        shape.text
        for layer in scene.layers
        for shape in layer.shapes
        if isinstance(shape, Label) and shape.text in {"A", "B", "C"}
    ]
    assert labels == ["A", "B", "C"]


def test_summary_chart_keeps_list_order_and_split_chart_uses_clustered_marks() -> None:
    summary = plot_scene(
        PlotData(
            plot_type=PlotType.BAR,
            x_name="kind",
            x=("dog", "cat", "bird"),
            summary=(5.0, 3.0, 1.0),
        ),
        320,
        220,
    )
    summary_labels = [
        shape.text
        for layer in summary.layers
        for shape in layer.shapes
        if isinstance(shape, Label) and shape.text in {"dog", "cat", "bird"}
    ]
    assert summary_labels == ["dog", "cat", "bird"]

    split_shapes = _shapes(
        PlotData(
            plot_type=PlotType.DOT_CHART,
            x=("dog", "dog", "cat", "cat", "cat"),
            split_name="sex",
            split=("f", "m", "f", "m", "m"),
        )
    )
    assert sum(isinstance(shape, Dots) for shape in split_shapes) == 4
