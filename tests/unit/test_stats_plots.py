# Requirements traced here: FR-STAT-001, FR-STAT-005
"""Backend-neutral Data & Statistics plots for numeric and categorical data."""

import math
from dataclasses import replace

import pytest

from cassim.graph.scene import Box, Dots, Fill, Label, Polyline
from cassim.stats.data import NumericExpression, as_categories, as_numbers, parse_item, parse_items
from cassim.stats.plots import (
    PlotData,
    PlotType,
    dot_data_at,
    dot_points,
    plot_scene,
    scatter_data_at,
    scatter_points,
)


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


def test_numeric_list_values_and_supported_expressions() -> None:
    expression = NumericExpression(names={"x": 3}, lists={"scores": (2, 4)})
    assert expression.evaluate("sqrt(x^2)+mean(scores)") == 6
    expression.validate("sin(pi/2)+mean(scores)")
    assert parse_items(None) == ()
    assert parse_item(' "a""b" ') == 'a"b'
    assert parse_item("1/0") is None
    assert parse_item("sqrt(-1)") is None
    assert as_numbers((1.0, "cat", None)) == (1.0, None, None)
    assert as_categories((1.0, "cat", None)) == ("1.0", "cat", None)


def test_numeric_expression_rejects_unsupported_syntax() -> None:
    expression = NumericExpression(names={"x": 3})
    with pytest.raises(ValueError, match="supported numeric expression"):
        expression.validate("x.real")


def test_dot_and_box_plots_show_markers_and_outliers() -> None:
    dot_shapes = _shapes(PlotData(x_name="score", x=(2.0, 2.0, None), plot_value=2.0))
    assert sum(isinstance(shape, Dots) for shape in dot_shapes) == 1
    assert any(isinstance(shape, Polyline) for shape in dot_shapes)

    box_data = PlotData(
        plot_type=PlotType.BOX,
        x_name="score",
        x=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 100.0),
    )
    box_shapes = _shapes(box_data)
    assert any(isinstance(shape, Box) for shape in box_shapes)
    assert any(isinstance(shape, Dots) for shape in box_shapes)
    assert any(isinstance(shape, Label) and shape.text == "Q₁: 2.5" for shape in box_shapes)
    extended = _shapes(replace(box_data, extend_whiskers=True))
    assert not any(isinstance(shape, Dots) for shape in extended)


def test_histogram_percent_scale_handles_bad_width_and_function_overlay() -> None:
    shapes = _shapes(
        PlotData(
            plot_type=PlotType.HISTOGRAM,
            x_name="score",
            x=(1.0, 3.0),
            histogram_width=0,
            histogram_scale="Percent",
            function=((1.0, 0.1), (3.0, 0.2)),
            function_label="f(x)",
            plot_value=2.0,
        )
    )
    assert sum(isinstance(shape, Fill) for shape in shapes) == 2
    assert sum(isinstance(shape, Polyline) for shape in shapes) == 2
    assert any(isinstance(shape, Label) and shape.text == "f(x)" for shape in shapes)


def test_normal_probability_plot_requires_a_nonconstant_sample() -> None:
    empty = _shapes(PlotData(plot_type=PlotType.NORMAL_PROBABILITY, x=(2.0,)))
    assert any(
        isinstance(shape, Label) and shape.text == "Choose a list to plot" for shape in empty
    )

    normal = _shapes(PlotData(plot_type=PlotType.NORMAL_PROBABILITY, x=(1.0, 2.0, 3.0)))
    assert any(isinstance(shape, Dots) for shape in normal)
    assert any(isinstance(shape, Polyline) for shape in normal)


def test_scatter_plot_supports_fit_function_and_residual_layers() -> None:
    shapes = _shapes(
        PlotData(
            plot_type=PlotType.XY_LINE,
            x_name="time",
            x=(1.0, 2.0, 3.0),
            y_name="distance",
            y=(2.0, 4.0, 6.0),
            regression=((1.0, 2.0), (3.0, 6.0)),
            regression_label="fit",
            function=((1.0, 2.0), (3.0, 5.0)),
            function_label="model",
            normal_pdf=((1.0, 0.1), (3.0, 0.1)),
            residuals=((1.0, 0.0), (2.0, 1.0), (3.0, 2.0)),
            residual_plot=True,
            residual_squares=5.0,
            plot_value=2.0,
        )
    )
    assert sum(isinstance(shape, Polyline) for shape in shapes) >= 5
    assert any(isinstance(shape, Label) and shape.text == "Σres² = 5" for shape in shapes)
    assert any(isinstance(shape, Label) and shape.text == "Residual" for shape in shapes)


def test_scatter_hit_testing_retains_original_rows_and_converts_coordinates() -> None:
    data = PlotData(
        plot_type=PlotType.SCATTER,
        x=(1.0, 2.0, 3.0),
        y=(10.0, None, 30.0),
    )
    points = scatter_points(data, 320, 220)

    assert [point.index for point in points] == [0, 2]
    assert scatter_data_at(data, 320, 220, points[1].screen_x, points[1].screen_y) == (
        3.0,
        30.0,
    )


def test_dot_hit_testing_retains_source_rows_and_converts_coordinates() -> None:
    data = PlotData(x_name="score", x=(2.0, 1.0, 2.0))
    points = dot_points(data, 320, 220)

    assert [point.index for point in points] == [1, 0, 2]
    assert dot_data_at(data, 320, 220, points[0].screen_x, points[0].screen_y) == 1.0


def test_interactive_scatter_uses_larger_marks_and_hides_canvas_axis_names() -> None:
    data = PlotData(
        plot_type=PlotType.SCATTER,
        x_name="time",
        x=(1.0, 2.0, 3.0),
        y_name="distance",
        y=(2.0, 4.0, 6.0),
        connect_points=True,
    )
    scene = plot_scene(data, 320, 220, axis_labels=False)
    shapes = tuple(shape for layer in scene.layers for shape in layer.shapes)

    assert any(isinstance(shape, Dots) and shape.size == 7 for shape in shapes)
    assert any(isinstance(shape, Polyline) and shape.stroke.width == 2.5 for shape in shapes)
    assert not any(
        isinstance(shape, Label) and shape.text in {"time", "distance"} for shape in shapes
    )


def test_interactive_empty_scene_uses_axis_controls_without_duplicate_prompts() -> None:
    scene = plot_scene(PlotData(), 320, 220, axis_labels=False)
    labels = tuple(
        shape.text for layer in scene.layers for shape in layer.shapes if isinstance(shape, Label)
    )

    assert "Choose a list to plot" in labels
    assert not any(label.startswith(("X: ", "Y: ")) for label in labels)


def test_categorical_charts_support_pies_split_bars_and_value_order() -> None:
    pie = _shapes(PlotData(plot_type=PlotType.PIE, x_name="fruit", x=("pear", "apple", "pear")))
    assert sum(isinstance(shape, Fill) for shape in pie) == 2
    assert any(isinstance(shape, Label) and shape.text == "apple" for shape in pie)

    split = _shapes(
        PlotData(
            plot_type=PlotType.PIE,
            x_name="fruit",
            x=("pear", "apple", "pear"),
            split_name="group",
            split=("A", "B", "A"),
            show_all_labels=True,
        )
    )
    assert any(isinstance(shape, Label) and "group" in shape.text for shape in split)
    assert any(isinstance(shape, Label) and "%" in shape.text for shape in split)

    ordered = _shapes(
        PlotData(
            plot_type=PlotType.BAR,
            x=("C", "A", "B", "C", "B", "C"),
            category_order="Value Order",
        )
    )
    category_labels = [
        shape.text
        for shape in ordered
        if isinstance(shape, Label) and shape.text in {"A", "B", "C"}
    ]
    assert category_labels == ["C", "B", "A"]


def test_grouped_box_plot_applies_whisker_setting() -> None:
    data = PlotData(
        plot_type=PlotType.BOX,
        x_name="class",
        x=("A",) * 8,
        y_name="score",
        y=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 100.0),
    )
    shapes = _shapes(data)
    assert any(isinstance(shape, Box) for shape in shapes)
    assert any(isinstance(shape, Dots) for shape in shapes)
    assert not any(
        isinstance(shape, Dots) for shape in _shapes(replace(data, extend_whiskers=True))
    )


def test_a_numeric_x_list_with_a_summary_list_is_a_weighted_histogram():
    """FR-STAT-003 (R5-Q2, Computer view): d1 summarised against xs gives bars of those heights,
    the y axis named after the summary list."""
    data = PlotData(
        plot_type=PlotType.HISTOGRAM,
        x_name="xs",
        x=(1.0, 2.0, 3.0),
        summary=(2.0, 4.0, 7.0),
        summary_name="d1",
    )
    scene = plot_scene(data, 240, 180)
    bars = [shape for shape in scene.layers[1].shapes if isinstance(shape, Fill)]
    heights = [round(max(y for _, y in bar.points) - min(y for _, y in bar.points)) for bar in bars]
    assert len(bars) == 3
    assert heights[0] * 2 == pytest.approx(heights[1], abs=2)
    assert any(
        isinstance(shape, Label) and shape.text == "d1"
        for layer in scene.layers
        for shape in layer.shapes
    )
