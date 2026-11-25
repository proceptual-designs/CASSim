"""Backend-neutral scenes for numeric and categorical statistics plots.

Requirements: FR-STAT-001 and FR-STAT-005.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, replace
from enum import StrEnum

from cassim.graph.scene import (
    Align,
    Box,
    Dots,
    Fill,
    Label,
    Layer,
    Marker,
    Polyline,
    Scene,
    Segments,
    Shape,
    Stroke,
)
from cassim.stats.data import DataValue

type Point = tuple[float, float]
type NumericPoint = tuple[float, float]
MIN_NORMAL_SAMPLE = 2


@dataclass(frozen=True, slots=True)
class _CategoryData:
    categories: tuple[str, ...]
    groups: tuple[str, ...]
    counts: tuple[float, ...]
    group_name: str
    color_order: tuple[str, ...]


class PlotType(StrEnum):
    DOT = "Dot Plot"
    BOX = "Box Plot"
    HISTOGRAM = "Histogram"
    NORMAL_PROBABILITY = "Normal Probability Plot"
    SCATTER = "Scatter Plot"
    XY_LINE = "XY Line Plot"
    DOT_CHART = "Dot Chart"
    BAR = "Bar Chart"
    PIE = "Pie Chart"


@dataclass(frozen=True, slots=True)
class PlotData:
    plot_type: PlotType = PlotType.DOT
    x_name: str = ""
    x: tuple[DataValue, ...] = ()
    y_name: str = ""
    y: tuple[DataValue, ...] = ()
    summary: tuple[float | None, ...] = ()
    summary_name: str = ""
    split_name: str = ""
    split: tuple[DataValue, ...] = ()
    force_categorical_x: bool = False
    category_order: str = "Alpha Order"
    connect_points: bool = False
    show_all_labels: bool = False
    extend_whiskers: bool = False
    histogram_width: float = 1.0
    histogram_scale: str = "Frequency"
    regression: tuple[NumericPoint, ...] = ()
    regression_label: str = ""
    residuals: tuple[NumericPoint, ...] = ()
    residual_plot: bool = False
    residual_squares: float | None = None
    normal_pdf: tuple[NumericPoint, ...] = ()
    function: tuple[NumericPoint, ...] = ()
    function_label: str = ""
    plot_value: float | None = None
    window: tuple[float, float, float, float] | None = None
    selected: frozenset[int] = frozenset()  # list rows drawn selected (shared across plots)


@dataclass(frozen=True, slots=True)
class PlottedPoint:
    index: int
    x: float
    y: float
    screen_x: float
    screen_y: float


@dataclass(frozen=True, slots=True)
class _Area:
    left: float
    top: float
    right: float
    bottom: float
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def point(self, x: float, y: float) -> Point:
        return (
            self.left + (x - self.xmin) / (self.xmax - self.xmin) * (self.right - self.left),
            self.bottom - (y - self.ymin) / (self.ymax - self.ymin) * (self.bottom - self.top),
        )


_COLOURS = ("curve1", "curve4", "curve3", "curve2", "curve5", "curve6")


def _finite(values: tuple[DataValue, ...]) -> tuple[float, ...]:
    return tuple(value for value in values if isinstance(value, float) and math.isfinite(value))


def _shown(value: float) -> str:
    if value == 0:
        return "0"
    return f"{value:.4g}"


def _bounds(values: tuple[float, ...], *, include_zero: bool = False) -> tuple[float, float]:
    if not values:
        return (0.0, 1.0)
    low, high = min(values), max(values)
    if include_zero:
        low, high = min(low, 0), max(high, 0)
    if low == high:
        pad = max(abs(low) * 0.05, 0.5)
        return low - pad, high + pad
    pad = (high - low) * 0.05
    return low - pad, high + pad


def _area(
    size: tuple[float, float],
    xvalues: tuple[float, ...],
    yvalues: tuple[float, ...],
    window: tuple[float, float, float, float] | None,
    *,
    residual_plot: bool = False,
) -> _Area:
    width, height = size
    left, right, top, bottom = 48.0, max(width - 14.0, 64.0), 16.0, max(height - 34.0, 48.0)
    if residual_plot:
        bottom = top + (bottom - top) * 0.64
    xmin, xmax = _bounds(xvalues)
    ymin, ymax = _bounds(yvalues, include_zero=True)
    if window is not None:
        xmin, xmax, ymin, ymax = window
    if xmax <= xmin:
        xmax = xmin + 1
    if ymax <= ymin:
        ymax = ymin + 1
    return _Area(left, top, right, bottom, xmin, xmax, ymin, ymax)


def _axes(area: _Area, xname: str, yname: str, *, y_ticks: bool = True) -> Layer:
    grid: list[Point] = []
    labels: list[Label] = []
    for step in range(5):
        x = area.left + (area.right - area.left) * step / 4
        y = area.top + (area.bottom - area.top) * step / 4
        grid.extend(((x, area.top), (x, area.bottom), (area.left, y), (area.right, y)))
        labels.append(
            Label(
                x,
                area.bottom + 3,
                _shown(area.xmin + (area.xmax - area.xmin) * step / 4),
                10,
                "axis",
                Align.CENTRE,
            )
        )
        if y_ticks:
            labels.append(
                Label(
                    area.left - 5,
                    y - 6,
                    _shown(area.ymax - (area.ymax - area.ymin) * step / 4),
                    10,
                    "axis",
                    Align.RIGHT,
                )
            )
    labels.extend(
        (
            Label((area.left + area.right) / 2, area.bottom + 17, xname, 12, "ink", Align.CENTRE),
            *((Label(area.left + 2, area.top + 2, yname, 11, "axis"),) if yname else ()),
        )
    )
    return Layer("axes", (Segments(tuple(grid), Stroke("grid")), *labels))


def _map_points(points: tuple[NumericPoint, ...], area: _Area) -> tuple[Point, ...]:
    return tuple(area.point(x, y) for x, y in points)


def _scatter_rows(data: PlotData) -> tuple[tuple[int, float, float], ...]:
    return tuple(
        (index, x, y)
        for index, (x, y) in enumerate(zip(data.x, data.y, strict=False))
        if isinstance(x, float) and math.isfinite(x) and isinstance(y, float) and math.isfinite(y)
    )


def _scatter_area(
    data: PlotData, width: float, height: float
) -> tuple[tuple[tuple[int, float, float], ...], _Area]:
    rows = _scatter_rows(data)
    area = _area(
        (width, height),
        tuple(x for _, x, _ in rows),
        tuple(y for _, _, y in rows),
        data.window,
        residual_plot=data.residual_plot,
    )
    return rows, area


def scatter_points(data: PlotData, width: float, height: float) -> tuple[PlottedPoint, ...]:
    """Return scatter points in scene pixels, retaining their source-list row indices."""
    rows, area = _scatter_area(data, width, height)
    return tuple(PlottedPoint(index, x, y, *area.point(x, y)) for index, x, y in rows)


def scatter_data_at(
    data: PlotData, width: float, height: float, screen_x: float, screen_y: float
) -> NumericPoint | None:
    """Convert a point inside the scatter plot's data area back to data coordinates."""
    rows, area = _scatter_area(data, width, height)
    if not rows or not (
        area.left <= screen_x <= area.right and area.top <= screen_y <= area.bottom
    ):
        return None
    x = area.xmin + (screen_x - area.left) / (area.right - area.left) * (area.xmax - area.xmin)
    y = area.ymax - (screen_y - area.top) / (area.bottom - area.top) * (area.ymax - area.ymin)
    return x, y


def _dot_layout(
    data: PlotData, width: float, height: float
) -> tuple[tuple[PlottedPoint, ...], _Area]:
    rows = tuple(
        sorted(
            (
                (index, value)
                for index, value in enumerate(data.x)
                if isinstance(value, float) and math.isfinite(value)
            ),
            key=lambda row: row[1],
        )
    )
    values = tuple(value for _, value in rows)
    xmin, xmax = data.window[:2] if data.window is not None else _bounds(values)
    area = _Area(
        48, 16, max(width - 14, 64), max(height - 34, 48), xmin, xmax, 0, max(len(rows), 1)
    )
    counts: dict[float, int] = {}
    points = []
    for index, value in rows:
        counts[value] = counts.get(value, 0) + 1
        y = counts[value] - 0.5
        points.append(PlottedPoint(index, value, y, *area.point(value, y)))
    return tuple(points), area


def dot_points(data: PlotData, width: float, height: float) -> tuple[PlottedPoint, ...]:
    """Return one-variable dot-plot points in scene pixels with their source-list rows."""
    points, _ = _dot_layout(data, width, height)
    return points


def dot_data_at(
    data: PlotData, width: float, height: float, screen_x: float, screen_y: float
) -> float | None:
    """Convert a point inside a one-variable dot plot back to its X value."""
    points, area = _dot_layout(data, width, height)
    if not points or not (
        area.left <= screen_x <= area.right and area.top <= screen_y <= area.bottom
    ):
        return None
    return area.xmin + (screen_x - area.left) / (area.right - area.left) * (area.xmax - area.xmin)


def _drawn_area(data: PlotData, width: float, height: float) -> tuple[_Area, bool] | None:
    """The plot's area as `plot_scene` draws it, and whether its y axis zooms too; None for a
    plot with category axes, a normal probability plot or no data."""
    width, height = max(width, 120), max(height, 100)
    categorical = data.force_categorical_x or any(isinstance(value, str) for value in data.x)
    if categorical or data.plot_type in (
        PlotType.DOT_CHART,
        PlotType.BAR,
        PlotType.PIE,
        PlotType.NORMAL_PROBABILITY,
    ):
        return None
    values = _finite(data.x)
    if not values:
        return None
    if data.plot_type is PlotType.HISTOGRAM:
        bins = _histogram_bins(_distribution_data(data))
        return (_histogram_area(bins, width, height, data), True) if bins else None
    if data.plot_type is PlotType.BOX:
        xmin, xmax = data.window[:2] if data.window is not None else _bounds(values)
        return _Area(48, 16, max(width - 14, 64), max(height - 34, 48), xmin, xmax, 0, 1), False
    if data.y:
        rows, area = _scatter_area(data, width, height)
        return (area, True) if rows else None
    _, area = _dot_layout(data, width, height)
    return area, False


def zoomed_window(
    data: PlotData, size: tuple[float, float], factor: float, at: tuple[float, float]
) -> tuple[float, float, float, float] | None:
    """The window after zooming by `factor` (below 1 zooms in) about the screen point `at`:
    the mouse wheel and a pinch on a Data & Statistics plot (Simon, 2026-11-25; the device does
    not zoom, run 6 S1). One-variable plots zoom along x only. None if the plot does not zoom."""
    drawn = _drawn_area(data, *size)
    if drawn is None or not (math.isfinite(factor) and factor > 0):
        return None
    area, both = drawn
    x, y = at
    across = (x - area.left) / (area.right - area.left)
    down = (y - area.top) / (area.bottom - area.top)
    x_anchor = area.xmin + across * (area.xmax - area.xmin)
    x_span = (area.xmax - area.xmin) * factor
    xmin = x_anchor - across * x_span
    ymin, ymax = area.ymin, area.ymax
    if both:
        y_anchor = area.ymax - down * (area.ymax - area.ymin)
        y_span = (area.ymax - area.ymin) * factor
        ymax = y_anchor + down * y_span
        ymin = ymax - y_span
    return xmin, xmin + x_span, ymin, ymax


def _empty(width: float, height: float, xname: str, yname: str) -> Scene:
    return Scene(
        width,
        height,
        (
            Layer(
                "labels",
                (
                    Label(
                        width / 2,
                        height / 2 - 12,
                        "Choose a list to plot",
                        14,
                        "axis",
                        Align.CENTRE,
                    ),
                    Label(
                        width / 2,
                        height / 2 + 8,
                        f"X: {xname or 'Click to add variable'}",
                        12,
                        "axis",
                        Align.CENTRE,
                    ),
                    Label(
                        width / 2,
                        height / 2 + 28,
                        f"Y: {yname or 'Click to add variable'}",
                        12,
                        "axis",
                        Align.CENTRE,
                    ),
                ),
            ),
        ),
    )


def plot_scene(data: PlotData, width: float, height: float, *, axis_labels: bool = True) -> Scene:
    """Build a plot in screen coordinates; input data stays owned by the Problem's variables."""
    width, height = max(width, 120), max(height, 100)
    if not axis_labels:
        data = replace(data, x_name="", y_name="")
    if (
        data.y
        and data.plot_type in (PlotType.DOT, PlotType.BOX)
        and (data.force_categorical_x or any(isinstance(value, str) for value in data.x))
    ):
        scene = _grouped_numeric(data, width, height)
    elif (
        data.plot_type in (PlotType.DOT_CHART, PlotType.BAR, PlotType.PIE)
        or data.force_categorical_x
    ):
        scene = _categorical(data, width, height)
    elif not data.x:
        scene = _empty(width, height, data.x_name, data.y_name)
    elif data.plot_type is PlotType.HISTOGRAM:
        scene = _histogram(_distribution_data(data), width, height)
    elif data.plot_type is PlotType.BOX:
        scene = _box_plot(data, width, height)
    elif data.plot_type is PlotType.NORMAL_PROBABILITY:
        scene = _normal_probability(_distribution_data(data), width, height)
    elif data.y:
        scene = _scatter(data, width, height)
    else:
        scene = _dot_plot(data, width, height)
    if not axis_labels:
        scene = Scene(
            scene.width,
            scene.height,
            tuple(
                Layer(
                    layer.name,
                    tuple(
                        shape
                        for shape in layer.shapes
                        if not (isinstance(shape, Label) and shape.text.startswith(("X: ", "Y: ")))
                    ),
                )
                for layer in scene.layers
            ),
        )
    return scene


def _distribution_data(data: PlotData) -> PlotData:
    if data.y and any(isinstance(value, str) for value in data.x):
        return replace(data, x_name=data.y_name, x=data.y, y_name="", y=())
    return data


def _selected_dots(points: tuple[PlottedPoint, ...], selected: frozenset[int]) -> tuple[Dots, ...]:
    """Selected points drawn again, lighter and larger (R5-G1)."""
    chosen = tuple((p.screen_x, p.screen_y) for p in points if p.index in selected)
    return (Dots(chosen, "selection", size=9),) if chosen else ()


def _dot_plot(data: PlotData, width: float, height: float) -> Scene:
    points, area = _dot_layout(data, width, height)
    if not points:
        return _empty(width, height, data.x_name, data.y_name)
    axis = _axes(area, data.x_name, "", y_ticks=False)
    shapes: list[Polyline | Dots] = [
        Dots(tuple((point.screen_x, point.screen_y) for point in points), size=7),
        *_selected_dots(points, data.selected),
    ]
    if data.plot_value is not None:
        x, _ = area.point(data.plot_value, 0)
        shapes.append(Polyline(((x, area.top), (x, area.bottom)), Stroke("curve2", 2)))
    return Scene(width, height, (axis, Layer("data", tuple(shapes))))


def _histogram_bins(data: PlotData) -> tuple[tuple[float, float, float], ...]:
    """The histogram's bins as (left, right, height); with a Summary List, each X value counts
    as its summary value (R5-Q2)."""
    weighted = [
        (float(value), 1.0 if not data.summary else (data.summary[index] or 0.0))
        for index, value in enumerate(data.x)
        if isinstance(value, float)
        and math.isfinite(value)
        and (not data.summary or index < len(data.summary))
    ]
    values = tuple(value for value, _ in weighted)
    if not values:
        return ()
    bin_width = data.histogram_width if data.histogram_width > 0 else 1.0
    start = min(values)
    counts: dict[int, float] = {}
    for value, weight in weighted:
        index = math.floor((value - start) / bin_width)
        counts[index] = counts.get(index, 0) + weight
    count = sum(weight for _, weight in weighted) or 1.0
    bins = tuple(
        (
            start + index * bin_width,
            start + (index + 1) * bin_width,
            (
                amount / count * 100
                if data.histogram_scale == "Percent"
                else amount / (count * bin_width)
                if data.histogram_scale == "Density"
                else amount
            ),
        )
        for index, amount in sorted(counts.items())
    )
    return bins


def _histogram_area(
    bins: tuple[tuple[float, float, float], ...], width: float, height: float, data: PlotData
) -> _Area:
    return _area(
        (width, height),
        (bins[0][0], max(right for _, right, _ in bins)),
        tuple(amount for _, _, amount in bins),
        data.window,
    )


def _histogram(data: PlotData, width: float, height: float) -> Scene:
    """A histogram; with a Summary List, each X value counts as its summary value (R5-Q2)."""
    bins = _histogram_bins(data)
    if not bins:
        return _empty(width, height, data.x_name, "Frequency")
    area = _histogram_area(bins, width, height, data)
    shapes: list[Shape] = []
    for left, right, amount in bins:
        x0, y0 = area.point(left, 0)
        x1, y1 = area.point(right, amount)
        shapes.append(Fill(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), "curve1", 0.65))
        shapes.append(Box(x0, y1, x1 - x0, y0 - y1, Stroke("axis", 0.8)))
    title = data.summary_name or data.histogram_scale
    if data.normal_pdf:
        shapes.append(Polyline(_map_points(data.normal_pdf, area), Stroke("curve4", 2)))
    if data.function:
        shapes.append(Polyline(_map_points(data.function, area), Stroke("curve3", 2)))
    if data.plot_value is not None:
        x, _ = area.point(data.plot_value, area.ymin)
        shapes.append(Polyline(((x, area.top), (x, area.bottom)), Stroke("curve2", 2)))
    labels = (
        (Label(area.left + 4, area.top + 4, data.function_label, 11, "curve3"),)
        if data.function_label
        else ()
    )
    return Scene(
        width,
        height,
        (_axes(area, data.x_name, title), Layer("data", tuple(shapes)), Layer("labels", labels)),
    )


def _quartiles(values: tuple[float, ...]) -> tuple[float, float, float, float, float]:
    ordered = sorted(values)
    middle = len(ordered) // 2
    lower = ordered[:middle]
    upper = ordered[middle + len(ordered) % 2 :]
    median = statistics.median(ordered)
    return (
        ordered[0],
        float(statistics.median(lower)) if lower else ordered[0],
        float(median),
        float(statistics.median(upper)) if upper else ordered[-1],
        ordered[-1],
    )


def _box_plot(data: PlotData, width: float, height: float) -> Scene:
    values = _finite(data.x or data.y)
    if not values:
        return _empty(width, height, data.x_name or data.y_name, "")
    low, q1, median, q3, high = _quartiles(values)
    iqr = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    lower = (
        low if data.extend_whiskers else min((v for v in values if v >= lower_fence), default=low)
    )
    upper = (
        high if data.extend_whiskers else max((v for v in values if v <= upper_fence), default=high)
    )
    xmin, xmax = data.window[:2] if data.window is not None else _bounds(values)
    area = _Area(48, 16, max(width - 14, 64), max(height - 34, 48), xmin, xmax, 0, 1)
    y = (area.top + area.bottom) / 2
    box_left, _ = area.point(q1, 0.5)
    box_right, _ = area.point(q3, 0.5)
    low_x, _ = area.point(lower, 0.5)
    high_x, _ = area.point(upper, 0.5)
    median_x, _ = area.point(median, 0.5)
    shapes: list[Fill | Box | Segments | Dots] = [
        Segments(((low_x, y), (box_left, y), (box_right, y), (high_x, y))),
        Segments(((low_x, y - 8), (low_x, y + 8), (high_x, y - 8), (high_x, y + 8))),
        Fill(
            ((box_left, y - 15), (box_right, y - 15), (box_right, y + 15), (box_left, y + 15)),
            "curve1",
            0.3,
        ),
        Box(box_left, y - 15, box_right - box_left, 30, Stroke("curve1", 1.5)),
        Segments(((median_x, y - 15), (median_x, y + 15)), Stroke("curve1", 2)),
    ]
    outliers = tuple(area.point(value, 0.5) for value in values if value < lower or value > upper)
    if outliers:
        shapes.append(Dots(outliers, "curve2", 6))
    if data.plot_value is not None:
        value_x, _ = area.point(data.plot_value, 0)
        shapes.append(Segments(((value_x, area.top), (value_x, area.bottom)), Stroke("curve2", 2)))
    axis = _axes(area, data.x_name or data.y_name, "", y_ticks=False)
    labels = Layer(
        "labels",
        (
            Label(box_left, y - 32, f"Q₁: {_shown(q1)}", 10, "axis"),
            Label(median_x, y + 18, f"Median: {_shown(median)}", 10, "axis", Align.CENTRE),
            Label(box_right, y - 32, f"Q₃: {_shown(q3)}", 10, "axis", Align.RIGHT),
        ),
    )
    return Scene(width, height, (axis, Layer("data", tuple(shapes)), labels))


def _grouped_numeric(data: PlotData, width: float, height: float) -> Scene:
    categories = _ordered_categories(data.x, data.category_order)
    if not categories:
        return _empty(width, height, data.x_name, data.y_name)
    grouped = {
        category: tuple(
            float(y)
            for x, y in zip(data.x, data.y, strict=False)
            if _category_label(x) == category and isinstance(y, float)
        )
        for category in categories
    }
    values = tuple(value for group in grouped.values() for value in group)
    if not values:
        return _empty(width, height, data.x_name, data.y_name)
    ymin, ymax = _bounds(values, include_zero=False)
    area = _Area(
        48, 18, max(width - 14, 64), max(height - 42, 54), -0.5, len(categories) - 0.5, ymin, ymax
    )
    grid: list[Point] = []
    labels: list[Label] = []
    for step in range(5):
        y = area.bottom - (area.bottom - area.top) * step / 4
        value = ymax - (ymax - ymin) * step / 4
        grid.extend(((area.left, y), (area.right, y)))
        labels.append(Label(area.left - 5, y - 6, _shown(value), 10, "axis", Align.RIGHT))
    for index, category in enumerate(categories):
        x = area.left + (area.right - area.left) * (index + 0.5) / len(categories)
        labels.append(Label(x, area.bottom + 4, category, 10, "ink", Align.CENTRE))
    labels.append(
        Label((area.left + area.right) / 2, height - 19, data.x_name, 12, "ink", Align.CENTRE)
    )
    labels.append(Label(area.left + 3, area.top + 2, data.y_name, 11, "axis"))
    shapes: list[Shape] = []
    band = (area.right - area.left) / len(categories)
    for index, category in enumerate(categories):
        group = grouped[category]
        centre = area.left + band * (index + 0.5)
        if data.plot_type is PlotType.DOT:
            dots = tuple(
                (centre + ((rank % 5) - 2) * 2.5, area.point(0, value)[1])
                for rank, value in enumerate(group)
            )
            shapes.append(Dots(dots, _COLOURS[index % len(_COLOURS)], 6))
        elif group:
            low, q1, median, q3, high = _quartiles(group)
            iqr = q3 - q1
            lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            lower = (
                low
                if data.extend_whiskers
                else min((v for v in group if v >= lower_fence), default=low)
            )
            upper = (
                high
                if data.extend_whiskers
                else max((v for v in group if v <= upper_fence), default=high)
            )
            low_y, _ = area.point(0, lower)
            high_y, _ = area.point(0, upper)
            q1_y, _ = area.point(0, q1)
            q3_y, _ = area.point(0, q3)
            median_y, _ = area.point(0, median)
            box_width = band * 0.48
            shapes.extend(
                (
                    Segments(((centre, low_y), (centre, q1_y), (centre, q3_y), (centre, high_y))),
                    Segments(
                        (
                            (centre - box_width / 3, low_y),
                            (centre + box_width / 3, low_y),
                            (centre - box_width / 3, high_y),
                            (centre + box_width / 3, high_y),
                        )
                    ),
                    Fill(
                        (
                            (centre - box_width / 2, q1_y),
                            (centre + box_width / 2, q1_y),
                            (centre + box_width / 2, q3_y),
                            (centre - box_width / 2, q3_y),
                        ),
                        _COLOURS[index % len(_COLOURS)],
                        0.3,
                    ),
                    Box(
                        centre - box_width / 2,
                        q3_y,
                        box_width,
                        q1_y - q3_y,
                        Stroke(_COLOURS[index % len(_COLOURS)], 1.5),
                    ),
                    Segments(
                        ((centre - box_width / 2, median_y), (centre + box_width / 2, median_y)),
                        Stroke(_COLOURS[index % len(_COLOURS)], 2),
                    ),
                )
            )
            outliers = tuple(
                (centre, area.point(0, value)[1])
                for value in group
                if value < lower or value > upper
            )
            if outliers:
                shapes.append(Dots(outliers, "curve2", 6))
    return Scene(
        width,
        height,
        (
            Layer("axes", (Segments(tuple(grid), Stroke("grid")), *labels)),
            Layer("data", tuple(shapes)),
        ),
    )


def _normal_probability(data: PlotData, width: float, height: float) -> Scene:
    values = tuple(sorted(_finite(data.x)))
    if len(values) < MIN_NORMAL_SAMPLE:
        return _empty(width, height, data.x_name, "Expected z")
    points = tuple(
        (value, statistics.NormalDist().inv_cdf((index + 0.5) / len(values)))
        for index, value in enumerate(values)
    )
    mean = statistics.mean(values)
    deviation = statistics.stdev(values)
    low, high = min(values), max(values)
    line = ((low, (low - mean) / deviation), (high, (high - mean) / deviation)) if deviation else ()
    area = _area(
        (width, height),
        values,
        tuple(y for _, y in points),
        data.window,
    )
    return Scene(
        width,
        height,
        (
            _axes(area, data.x_name, "Expected z"),
            Layer(
                "data",
                (
                    Dots(_map_points(points, area), size=6),
                    *((Polyline(_map_points(line, area), Stroke("curve2", 1.5)),) if line else ()),
                ),
            ),
            Layer(
                "labels",
                (
                    Label(
                        area.left + 4,
                        area.top + 4,
                        f"y = (x-{_shown(mean)})/{_shown(deviation)}"
                        if deviation
                        else "Constant data",
                        11,
                    ),
                ),
            ),
        ),
    )


def _scatter(data: PlotData, width: float, height: float) -> Scene:
    pairs = tuple(
        (x, y)
        for x, y in zip(data.x, data.y, strict=False)
        if isinstance(x, float) and isinstance(y, float)
    )
    if not pairs:
        return _empty(width, height, data.x_name, data.y_name)
    xs, ys = tuple(x for x, _ in pairs), tuple(y for _, y in pairs)
    area = _area((width, height), xs, ys, data.window, residual_plot=data.residual_plot)
    dots = Dots(_map_points(pairs, area), size=7)
    shapes: list[Polyline | Dots] = []
    if data.connect_points or data.plot_type is PlotType.XY_LINE:
        shapes.append(Polyline(_map_points(pairs, area), Stroke("curve1", 2.5)))
    shapes.append(dots)
    shapes.extend(_selected_dots(scatter_points(data, width, height), data.selected))
    if data.regression:
        shapes.append(Polyline(_map_points(data.regression, area), Stroke("curve2", 2)))
    if data.function:
        shapes.append(Polyline(_map_points(data.function, area), Stroke("curve3", 2)))
    if data.normal_pdf:
        shapes.append(Polyline(_map_points(data.normal_pdf, area), Stroke("curve4", 2)))
    labels = []
    if data.regression_label:
        labels.append(Label(area.left + 4, area.top + 4, data.regression_label, 11, "curve2"))
    if data.residual_squares is not None:
        labels.append(
            Label(
                area.left + 4,
                area.top + 31,
                f"Σres² = {_shown(data.residual_squares)}",
                11,
                "curve2",
            )
        )
    if data.function_label:
        labels.append(Label(area.left + 4, area.top + 18, data.function_label, 11, "curve3"))
    if data.plot_value is not None:
        x, _ = area.point(data.plot_value, area.ymin)
        shapes.append(Polyline(((x, area.top), (x, area.bottom)), Stroke("curve4", 2)))
    layers: list[Layer] = [_axes(area, data.x_name, data.y_name), Layer("data", tuple(shapes))]
    if labels:
        layers.append(Layer("labels", tuple(labels)))
    if data.residual_plot and data.residuals:
        residual_area = _Area(
            area.left,
            area.bottom + 28,
            area.right,
            max(height - 24, area.bottom + 48),
            min(xs),
            max(xs) if min(xs) != max(xs) else min(xs) + 1,
            min((r for _, r in data.residuals), default=-1),
            max((r for _, r in data.residuals), default=1),
        )
        if residual_area.ymax <= residual_area.ymin:
            residual_area = _Area(
                residual_area.left,
                residual_area.top,
                residual_area.right,
                residual_area.bottom,
                residual_area.xmin,
                residual_area.xmax,
                residual_area.ymin - 1,
                residual_area.ymax + 1,
            )
        y0 = residual_area.point(residual_area.xmin, 0)[1]
        layers.append(
            Layer(
                "residuals",
                (
                    Segments(
                        ((residual_area.left, y0), (residual_area.right, y0)),
                        Stroke("axis", 1, True),
                    ),
                    Dots(_map_points(data.residuals, residual_area), "curve5", 6),
                    Label(residual_area.left, residual_area.top, "Residual", 11, "axis"),
                ),
            )
        )
    return Scene(width, height, tuple(layers))


def _categorical(data: PlotData, width: float, height: float) -> Scene:
    values = data.x
    summary = data.summary
    if not values:
        return _empty(width, height, data.x_name, data.y_name)
    if summary:
        pairs = [
            (_category_label(value), max(summary[index] or 0.0, 0.0))
            for index, value in enumerate(values)
            if value is not None and value != "" and index < len(summary)
        ]
        category_data = _CategoryData(
            tuple(category for category, _ in pairs),
            ("",),
            tuple(count for _, count in pairs),
            "",
            tuple(category for category, _ in pairs),
        )
    else:
        color_order = _ordered_categories(values, "Alpha Order")
        groups = tuple(
            sorted(
                {
                    _category_label(value)
                    for value in data.split
                    if value is not None and value != ""
                }
            )
            or [""]
        )
        categories = tuple(_ordered_categories(values, data.category_order))
        xs = tuple(_category_label(value) if value is not None else "" for value in values)
        split = tuple(_category_label(value) if value is not None else "" for value in data.split)
        counts = tuple(
            float(
                sum(
                    1
                    for index, value in enumerate(xs)
                    if value == category
                    and (
                        not split
                        or (index < len(split) and split[index] == group)
                        or (index >= len(split) and group == "")
                    )
                )
            )
            for category in categories
            for group in groups
        )
        category_data = _CategoryData(categories, groups, counts, data.split_name, color_order)
    if not category_data.categories:
        return _empty(width, height, data.x_name, data.y_name)
    if data.plot_type is PlotType.PIE:
        return _pie(data, (width, height), category_data)
    return _bar_or_dots(data, (width, height), category_data)


def _category_label(value: DataValue) -> str:
    return _shown(value) if isinstance(value, float) else str(value)


def _ordered_categories(values: tuple[DataValue, ...], order: str) -> tuple[str, ...]:
    present = [value for value in values if value is not None and value != ""]
    if not present:
        labels: tuple[str, ...] = ()
    elif all(isinstance(value, float) for value in present):
        labels = tuple(_category_label(value) for value in present)
        if order == "List Order":
            labels = tuple(dict.fromkeys(labels))
        else:
            counts = {label: labels.count(label) for label in set(labels)}
            if order == "Value Order":
                labels = tuple(sorted(counts, key=lambda label: (-counts[label], float(label))))
            else:
                labels = tuple(sorted(counts, key=float))
    else:
        labels = tuple(_category_label(value) for value in present)
        if order == "List Order":
            labels = tuple(dict.fromkeys(labels))
        elif order == "Value Order":
            counts = {label: labels.count(label) for label in set(labels)}
            labels = tuple(sorted(counts, key=lambda label: (-counts[label], label)))
        else:
            labels = tuple(sorted(set(labels)))
    return labels


def _bar_or_dots(data: PlotData, size: tuple[float, float], categories: _CategoryData) -> Scene:
    width, height = size
    category_names, groups = categories.categories, categories.groups
    counts, group_name = categories.counts, categories.group_name
    left, right, top, bottom = 48.0, max(width - 14.0, 64.0), 20.0, max(height - 42.0, 54.0)
    ymax = max(counts, default=1.0)
    ymax = max(ymax * 1.15, 1.0)
    area = _Area(left, top, right, bottom, -0.5, len(category_names) - 0.5, 0.0, ymax)
    shapes: list[Shape] = []
    group_count = max(len(groups), 1)
    band = (right - left) / len(category_names)
    cluster = band * 0.78
    bar_width = cluster / group_count
    for category_index in range(len(category_names)):
        for group_index in range(len(groups)):
            count = counts[category_index * group_count + group_index]
            centre = (
                left + band * (category_index + 0.5) - cluster / 2 + bar_width * (group_index + 0.5)
            )
            colour = (
                _COLOURS[group_index % len(_COLOURS)]
                if group_name
                else _COLOURS[
                    categories.color_order.index(category_names[category_index]) % len(_COLOURS)
                ]
            )
            if data.plot_type is PlotType.DOT_CHART:
                marker = Marker.SQUARE if group_name and group_index % 2 else Marker.DOT
                dots = tuple((centre, area.point(0, i + 0.5)[1]) for i in range(math.ceil(count)))
                shapes.append(Dots(dots, colour, 6, marker))
            else:
                y = area.point(0, count)[1]
                shapes.append(
                    Fill(
                        (
                            (centre - bar_width / 2, bottom),
                            (centre + bar_width / 2, bottom),
                            (centre + bar_width / 2, y),
                            (centre - bar_width / 2, y),
                        ),
                        colour,
                        0.7,
                    )
                )
                shapes.append(
                    Box(centre - bar_width / 2, y, bar_width, bottom - y, Stroke("axis", 0.7))
                )
                if count == 0:
                    shapes.append(
                        Segments(
                            ((centre - bar_width / 2, bottom), (centre + bar_width / 2, bottom)),
                            Stroke(colour, 2),
                        )
                    )
                if data.show_all_labels:
                    total = sum(
                        counts[category_index * group_count : (category_index + 1) * group_count]
                    )
                    pct = count / total * 100 if total else 0
                    shapes.append(
                        Label(
                            centre, y - 14, f"{_shown(count)} ({pct:.1f}%)", 9, "ink", Align.CENTRE
                        )
                    )
    grid: list[Point] = []
    labels: list[Label] = []
    for step in range(5):
        y = bottom - (bottom - top) * step / 4
        value = ymax * step / 4
        grid.extend(((left, y), (right, y)))
        labels.append(Label(left - 5, y - 6, _shown(value), 10, "axis", Align.RIGHT))
    for index, category in enumerate(category_names):
        x = left + band * (index + 0.5)
        labels.append(Label(x, bottom + 4, category, 10, "ink", Align.CENTRE, width=band))
    labels.append(
        Label(
            (left + right) / 2,
            height - 19,
            f"{data.x_name}{' / ' + group_name if group_name else ''}",
            12,
            "ink",
            Align.CENTRE,
        )
    )
    labels.append(Label(left + 3, top + 2, data.y_name or "Frequency", 11, "axis"))
    if group_name:
        for index, group in enumerate(groups):
            y = top + 3 + index * 14
            labels.append(Label(right - 80, y, f"■ {group}", 10, _COLOURS[index % len(_COLOURS)]))
    return Scene(
        width,
        height,
        (
            Layer("axes", (Segments(tuple(grid), Stroke("grid")), *labels)),
            Layer("data", tuple(shapes)),
        ),
    )


def _pie(data: PlotData, size: tuple[float, float], categories: _CategoryData) -> Scene:
    width, height = size
    category_names, counts = categories.categories, categories.counts
    if categories.group_name:
        return _bar_or_dots(data, size, categories)
    total = sum(counts)
    if total <= 0:
        return _empty(width, height, data.x_name, data.y_name)
    radius = min(width * 0.25, height * 0.32, 90)
    cx, cy = width / 2, height / 2 - 6
    shapes: list[Shape] = []
    angle = 0.0
    for index, (category, count) in enumerate(zip(category_names, counts, strict=True)):
        end = angle + count / total * math.tau
        points = [(cx, cy)]
        steps = max(3, int((end - angle) * 24))
        points.extend(
            (
                cx + radius * math.cos(angle + (end - angle) * step / steps),
                cy + radius * math.sin(angle + (end - angle) * step / steps),
            )
            for step in range(steps + 1)
        )
        colour = _COLOURS[index % len(_COLOURS)]
        shapes.append(Fill(tuple(points), colour, 0.75))
        shapes.append(Polyline(tuple(points[1:]), Stroke("axis", 1)))
        middle = (angle + end) / 2
        lx, ly = cx + (radius + 18) * math.cos(middle), cy + (radius + 18) * math.sin(middle)
        shapes.append(Label(lx, ly, category, 10, "ink", Align.CENTRE))
        angle = end
    labels = Layer("labels", (Label(cx, height - 18, data.x_name, 12, "ink", Align.CENTRE),))
    return Scene(width, height, (Layer("data", tuple(shapes)), labels))
