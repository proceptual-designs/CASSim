"""Compile and sample graph functions into the backend-neutral scene types."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from itertools import pairwise

from cassim.core.compat.sympy_adapter import compile_math
from cassim.core.values import Expr
from cassim.graph.scene import Layer, Polyline, Scene, Stroke

_DEFAULT_STROKE = Stroke()
_MAX_ADAPTIVE_DEPTH = 16


@dataclass(frozen=True, slots=True)
class Window:
    """A finite graphing window in mathematical coordinates."""

    x_min: float = -10.0
    x_max: float = 10.0
    y_min: float = -20 / 3
    y_max: float = 20 / 3

    def __post_init__(self) -> None:
        bounds = (self.x_min, self.x_max, self.y_min, self.y_max)
        if not all(math.isfinite(value) for value in bounds):
            msg = "window bounds must be finite"
            raise ValueError(msg)
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            msg = "window minimums must be below their maximums"
            raise ValueError(msg)

    def to_screen(self, x: float, y: float, width: float, height: float) -> tuple[float, float]:
        """Map a mathematical point into screen pixels, with y increasing upward."""
        return (
            (x - self.x_min) * width / (self.x_max - self.x_min),
            (self.y_max - y) * height / (self.y_max - self.y_min),
        )


@dataclass(frozen=True, slots=True)
class Viewport:
    """A graph window and its screen-space dimensions."""

    window: Window
    width: float
    height: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) and value > 0 for value in (self.width, self.height)):
            msg = "plot dimensions must be finite and positive"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class CompiledFunction:
    """An expression and its checked, worker-ready Python math source."""

    source: str
    _function: Callable[[float], float] = field(repr=False, compare=False)

    def __call__(self, x: float) -> float:
        return float(self._function(x))


class GraphCompileError(ValueError):
    """An expression is outside the graph worker's supported math subset."""


def compile_function(expression: Expr, variable: Expr) -> CompiledFunction:
    """Compile a symbolic expression using only the graph worker's approved math functions."""
    try:
        source, function = compile_math(expression.raw, variable.raw)
    except ValueError as error:
        raise GraphCompileError(str(error)) from error
    return CompiledFunction(source, function)


def automatic_tick_step(minimum: float, maximum: float) -> float:
    """Choose the observed power-of-ten tick spacing, about 10–20 ticks per window."""
    if not math.isfinite(minimum) or not math.isfinite(maximum) or minimum >= maximum:
        msg = "tick bounds must be finite and increasing"
        raise ValueError(msg)
    exponent = math.floor(math.log10((maximum - minimum) / 10))
    return 10.0**exponent


def tick_values(minimum: float, maximum: float) -> tuple[float, ...]:
    """Return tick positions for an automatically scaled axis."""
    step = automatic_tick_step(minimum, maximum)
    first = math.ceil(minimum / step)
    last = math.floor(maximum / step)
    return tuple(index * step for index in range(first, last + 1))


def sample_function(
    function: Callable[[float], float],
    viewport: Viewport,
    *,
    stroke: Stroke = _DEFAULT_STROKE,
    tolerance_pixels: float = 0.75,
    max_depth: int = 8,
) -> tuple[Polyline, ...]:
    """Adaptively sample a function, splitting undefined points and unresolved jumps.

    The base grid is one point per horizontal pixel. Midpoints are added where the curve is
    nonlinear at screen resolution; an interval that remains unresolved at `max_depth` is broken
    rather than drawn as a false connecting line.
    """
    if not math.isfinite(tolerance_pixels) or tolerance_pixels <= 0:
        msg = "sampling tolerance must be finite and positive"
        raise ValueError(msg)
    if not 1 <= max_depth <= _MAX_ADAPTIVE_DEPTH:
        msg = f"max_depth must be between 1 and {_MAX_ADAPTIVE_DEPTH}"
        raise ValueError(msg)

    window = viewport.window
    width = viewport.width
    height = viewport.height

    def evaluate(x: float) -> float | None:
        try:
            value = float(function(x))
        except ArithmeticError, ValueError:
            return None
        return value if math.isfinite(value) else None

    y_span = window.y_max - window.y_min

    def needs_refinement(y0: float, ym: float, y1: float) -> bool:
        chord_error = abs(ym - (y0 + y1) / 2) * height / y_span
        chord_height = abs(y1 - y0) * height / y_span
        return chord_error > tolerance_pixels or chord_height > height

    def refine(
        x0: float,
        y0: float | None,
        x1: float,
        y1: float | None,
        depth: int,
    ) -> list[tuple[float, float | None]]:
        midpoint = (x0 + x1) / 2
        ym = evaluate(midpoint)
        unresolved = y0 is None or ym is None or y1 is None or needs_refinement(y0, ym, y1)
        if not unresolved:
            return [(x0, y0), (x1, y1)]
        if depth == max_depth:
            return [(x0, y0), (midpoint, None), (x1, y1)]
        left = refine(x0, y0, midpoint, ym, depth + 1)
        right = refine(midpoint, ym, x1, y1, depth + 1)
        return [*left, *right[1:]]

    pixel_columns = max(1, math.ceil(width))
    x_values = [
        window.x_min + index * (window.x_max - window.x_min) / pixel_columns
        for index in range(pixel_columns + 1)
    ]
    samples: list[tuple[float, float | None]] = []
    for x0, x1 in pairwise(x_values):
        y0, y1 = evaluate(x0), evaluate(x1)
        interval = refine(x0, y0, x1, y1, 0)
        samples.extend(interval if not samples else interval[1:])

    branches: list[Polyline] = []
    points: list[tuple[float, float]] = []
    for x, y in samples:
        if y is None:
            if len(points) > 1:
                branches.append(Polyline(tuple(points), stroke))
            points = []
            continue
        points.append(window.to_screen(x, y, width, height))
    if len(points) > 1:
        branches.append(Polyline(tuple(points), stroke))
    return tuple(branches)


def function_scene(
    functions: Sequence[tuple[Callable[[float], float], Stroke]],
    viewport: Viewport,
) -> Scene:
    """Build the curve layer of a graph scene from functions in one window."""
    curves = tuple(
        curve
        for function, stroke in functions
        for curve in sample_function(function, viewport, stroke=stroke)
    )
    return Scene(viewport.width, viewport.height, (Layer("curves", curves),))
