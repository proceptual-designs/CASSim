"""Shaded density panes from a Lists & Spreadsheet page (FR-STAT-004, FR-DOC-009).

Two kinds, each a pane of a split sheet page (decision 0034 item 2):

- `PValuePlot`: Draw: Shade P Value in a z or t test dialog (stats4 I2): the statistic's density
  with the tail (or tails) of the alternative shaded, and `z = …` or `t = …` and `PVal = …` at
  the top.
- `AreaPlot`: Draw: Shade area in the Normal Cdf dialog (split2 H14): `normPdf(x,μ,σ)` with the
  area between the bounds shaded and labelled.

Alternatives use the engine's numbering: 0 is ≠, 1 is <, 2 is >.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

from cassim.graph.scene import Align, Fill, Label, Layer, Polyline, Scene, Segments, Stroke

_Z_RANGE = 4.0
_T_RANGE = 5.0
_SAMPLES = 256  # points along the whole curve


@dataclass(frozen=True, slots=True)
class PValuePlot:
    statistic: float
    p_value: float
    alternative: int
    variable: str = "z"  # "z" (normal) or "t"
    df: float | None = None  # the t distribution's degrees of freedom


@dataclass(frozen=True, slots=True)
class AreaPlot:
    lower: float  # -inf or inf for an open bound
    upper: float
    mu: float = 0.0
    sigma: float = 1.0

    @property
    def area(self) -> float:
        def below(x: float) -> float:
            return 0.5 * (1 + math.erf((x - self.mu) / (self.sigma * math.sqrt(2))))

        return below(self.upper) - below(self.lower)


def normal_density(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    return math.exp(-(((x - mu) / sigma) ** 2) / 2) / (sigma * math.sqrt(2 * math.pi))


def t_density(x: float, df: float) -> float:
    log_scale = math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
    return math.exp(log_scale - (df + 1) / 2 * math.log1p(x * x / df))


@dataclass(frozen=True, slots=True)
class _Frame:
    """Data to pixels for one density pane."""

    left: float
    right: float
    top: float
    bottom: float
    x_min: float
    x_max: float
    y_max: float

    def point(self, x: float, y: float) -> tuple[float, float]:
        px = self.left + (x - self.x_min) / (self.x_max - self.x_min) * (self.right - self.left)
        py = self.bottom - y / self.y_max * (self.bottom - self.top)
        return px, py


@dataclass(frozen=True, slots=True)
class _Density:
    function: Callable[[float], float]
    x_min: float
    x_max: float
    x_label: str


def _density_scene(
    width: float,
    height: float,
    density: _Density,
    shaded: tuple[tuple[float, float], ...],
    title: tuple[str, ...],
) -> Scene:
    function, x_min, x_max = density.function, density.x_min, density.x_max
    peak = max(function(x_min + (x_max - x_min) * i / _SAMPLES) for i in range(_SAMPLES + 1))
    frame = _Frame(16.0, width - 8.0, 42.0, height - 18.0, x_min, x_max, peak * 1.12 or 1.0)

    def curve(start: float, end: float) -> list[tuple[float, float]]:
        count = max(2, round((end - start) / (x_max - x_min) * _SAMPLES))
        return [
            frame.point(
                start + (end - start) * index / count,
                function(start + (end - start) * index / count),
            )
            for index in range(count + 1)
        ]

    fills = []
    for start, end in shaded:
        low, high = max(start, x_min), min(end, x_max)
        if low < high:
            line = curve(low, high)
            fills.append(Fill((frame.point(low, 0), *line, frame.point(high, 0)), "curve2", 0.36))
    centre = min(max(0.0, x_min), x_max)
    shapes = [
        *fills,
        Segments(
            (
                frame.point(x_min, 0),
                frame.point(x_max, 0),
                frame.point(centre, 0),
                frame.point(centre, frame.y_max),
            ),
            Stroke("axis"),
        ),
        Polyline(tuple(curve(x_min, x_max)), Stroke("curve1", 1.5)),
        *(
            Label(width / 2, 4 + 13 * row, text, 11, align=Align.CENTRE)
            for row, text in enumerate(title)
        ),
        Label(frame.left, frame.top - 12, "Density", 9, colour="axis"),
        Label(frame.right, frame.bottom + 2, density.x_label, 10, colour="axis", align=Align.RIGHT),
    ]
    return Scene(width, height, (Layer("plot", tuple(shapes)),))


def p_value_scene(plot: PValuePlot, width: float, height: float) -> Scene:
    df = plot.df if plot.df is not None and plot.df > 0 else None
    if plot.variable == "t" and df is not None:
        density = _Density(lambda x: t_density(x, df), -_T_RANGE, _T_RANGE, "t")
    else:
        density = _Density(normal_density, -_Z_RANGE, _Z_RANGE, plot.variable)
    low, high = density.x_min, density.x_max
    threshold = abs(plot.statistic)
    shaded: tuple[tuple[float, float], ...]
    if plot.alternative == 0:
        shaded = ((low, -threshold), (threshold, high))
    elif plot.alternative == 1:
        shaded = ((low, plot.statistic),)
    else:
        shaded = ((plot.statistic, high),)
    title = (f"{plot.variable} = {plot.statistic:.4f}    PVal = {plot.p_value:.4f}",)
    return _density_scene(width, height, density, shaded, title)


def area_scene(plot: AreaPlot, width: float, height: float) -> Scene:
    sigma = plot.sigma if plot.sigma > 0 else 1.0
    mu = plot.mu
    density = _Density(
        lambda x: normal_density(x, mu, sigma),
        mu - _Z_RANGE * sigma,
        mu + _Z_RANGE * sigma,
        "x",
    )
    title = (f"normPdf(x,{mu:g},{sigma:g})", f"Area: {plot.area:.6g}")
    return _density_scene(width, height, density, ((plot.lower, plot.upper),), title)
