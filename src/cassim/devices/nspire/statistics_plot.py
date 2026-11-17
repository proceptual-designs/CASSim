"""A p-value plot for the spreadsheet's 1-Prop z Test dialog."""

import math
from dataclasses import dataclass

from cassim.graph.scene import Align, Fill, Label, Layer, Polyline, Scene, Segments, Stroke

_X_MIN, _X_MAX = -4.0, 4.0
_Y_MAX = 0.45


@dataclass(frozen=True, slots=True)
class PValuePlot:
    statistic: float
    p_value: float
    alternative: int


def p_value_scene(plot: PValuePlot, width: float, height: float) -> Scene:
    left, right, top, bottom = 16.0, width - 8.0, 42.0, height - 18.0
    plot_width, plot_height = max(right - left, 1.0), max(bottom - top, 1.0)

    def point(x: float, density: float) -> tuple[float, float]:
        px = left + (x - _X_MIN) / (_X_MAX - _X_MIN) * plot_width
        py = bottom - density / _Y_MAX * plot_height
        return px, py

    def density(x: float) -> float:
        return math.exp(-(x * x) / 2) / math.sqrt(2 * math.pi)

    def curve(start: float, end: float) -> list[tuple[float, float]]:
        count = max(2, round((end - start) * 32))
        return [
            point(
                start + (end - start) * index / count,
                density(start + (end - start) * index / count),
            )
            for index in range(count + 1)
        ]

    def shaded(start: float, end: float) -> Fill | None:
        if start >= end:
            return None
        line = curve(start, end)
        return Fill((point(start, 0), *line, point(end, 0)), "curve2", 0.36)

    threshold = abs(plot.statistic)
    if plot.alternative == 0:
        tails = (shaded(_X_MIN, min(-threshold, _X_MAX)), shaded(max(threshold, _X_MIN), _X_MAX))
    elif plot.alternative == 1:
        tails = (shaded(_X_MIN, max(_X_MIN, min(plot.statistic, _X_MAX))),)
    else:
        tails = (shaded(max(_X_MIN, min(plot.statistic, _X_MAX)), _X_MAX),)
    shapes = [
        *(fill for fill in tails if fill is not None),
        Segments(
            (point(_X_MIN, 0), point(_X_MAX, 0), point(0, 0), point(0, _Y_MAX)),
            Stroke("axis"),
        ),
        Polyline(tuple(curve(_X_MIN, _X_MAX)), Stroke("curve1", 1.5)),
        Label(
            width / 2,
            4,
            f"z = {plot.statistic:.4f}    PVal = {plot.p_value:.4f}",
            11,
            align=Align.CENTRE,
        ),
        Label(left, top - 12, "Density", 9, colour="axis"),
        Label(right, bottom + 2, "z", 10, colour="axis", align=Align.RIGHT),
    ]
    return Scene(width, height, (Layer("plot", tuple(shapes)),))
