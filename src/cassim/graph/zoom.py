"""Window / Zoom windows for a function graph (FR-GRAPH-002), headless.

The numbers come from the emulator captures (`docs/testing/emulator-graphs-results.md` D7 and D8,
`-graphs2-` D8, `-graphs4-` D8, `-graphs5-` D29): Standard is x -10..10 by y +-20/3; Quadrant 1
is x -4..20 by y -8/3..40/3; Trig is x +-2pi by y +-4pi/3; Decimal is x +-32 by y +-21.3; In and
Out halve or double the window about the chosen point; Box takes the two corners; Square keeps x
and sets y so a unit is as tall as it is wide; Fit keeps x and pads the sampled y range by 10% each
side; Data pads the data's range by 10% each side.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Callable, Iterable, Sequence

from cassim.graph.sampling import Window

STANDARD = Window()
QUADRANT_1 = Window(-4.0, 20.0, -8 / 3, 40 / 3)
TRIG = Window(-2 * math.pi, 2 * math.pi, -4 * math.pi / 3, 4 * math.pi / 3)
DECIMAL = Window(-32.0, 32.0, -21.3, 21.3)
PADDING = 0.1  # Zoom - Fit and Zoom - Data add a tenth of the range at each side
_NO_DATA_MARGIN = 1.0
_PI_MULTIPLE_LIMIT = 1000
_PI_TOLERANCE = 1e-12


def zoom_about(window: Window, x: float, y: float, factor: float) -> Window:
    """Zoom - In (factor 1/2) or Zoom - Out (factor 2): the window scaled and centred on (x, y)."""
    half_width = (window.x_max - window.x_min) * factor / 2
    half_height = (window.y_max - window.y_min) * factor / 2
    return Window(x - half_width, x + half_width, y - half_height, y + half_height)


def zoom_box(first: tuple[float, float], second: tuple[float, float]) -> Window:
    """Zoom - Box: the window between two corners. A box with no width or height is refused."""
    (x0, y0), (x1, y1) = first, second
    return Window(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1))


def zoom_square(window: Window, width: float, height: float) -> Window:
    """Zoom - Square: x is kept and y is scaled so units are square on screen. The x axis stays
    where it is on the screen (graphs2 D8: y -6.9004..27.9044 became -1.3217..5.3449); with the
    axis off the screen, y is scaled about its centre."""
    scale = (window.x_max - window.x_min) * height / width / (window.y_max - window.y_min)
    anchor = 0.0 if window.y_min <= 0 <= window.y_max else (window.y_min + window.y_max) / 2
    return Window(
        window.x_min,
        window.x_max,
        anchor + (window.y_min - anchor) * scale,
        anchor + (window.y_max - anchor) * scale,
    )


def _padded(low: float, high: float) -> tuple[float, float]:
    span = high - low
    if span == 0:
        span = abs(low) if low else _NO_DATA_MARGIN
        return low - span * PADDING * 5, high + span * PADDING * 5
    return low - span * PADDING, high + span * PADDING


def zoom_fit(
    window: Window, functions: Iterable[Callable[[float], float]], columns: int = 320
) -> Window:
    """Zoom - Fit: x is kept; y covers every value sampled across the window, padded by 10%.
    (D8: x^2 on -10..10 gives about -10.0012 to 110.0198.) A window with no values is kept.

    TODO(run 6, R6-D3): with a scatter plot on the page, Fit changes x as well (D29: -0.54 to
    9.54); not built until the case is captured."""
    columns = max(columns, 1)
    xs = [
        window.x_min + index * (window.x_max - window.x_min) / columns
        for index in range(columns + 1)
    ]
    values: list[float] = []
    for function in functions:
        for x in xs:
            try:
                value = float(function(x))
            except ArithmeticError, TypeError, ValueError:
                continue
            if math.isfinite(value):
                values.append(value)
    if not values:
        return window
    low, high = _padded(min(values), max(values))
    return Window(window.x_min, window.x_max, low, high)


def zoom_data(window: Window, points: Sequence[tuple[float, float]]) -> Window:
    """Zoom - Data: the data's x and y ranges, each padded by 10% (D29: x 1..8 gives 0.3..8.7).
    With no data on the page the window grows by one unit at each side (graphs2 D8)."""
    if not points:
        return Window(
            window.x_min - _NO_DATA_MARGIN,
            window.x_max + _NO_DATA_MARGIN,
            window.y_min - _NO_DATA_MARGIN,
            window.y_max + _NO_DATA_MARGIN,
        )
    x_low, x_high = _padded(min(x for x, _ in points), max(x for x, _ in points))
    y_low, y_high = _padded(min(y for _, y in points), max(y for _, y in points))
    return Window(x_low, x_high, y_low, y_high)


def window_text(value: float) -> str:
    """A window value as Window Settings shows it: full digits, and a multiple of pi as `2·π`."""
    if value and math.isfinite(value):
        multiple = value / math.pi
        whole = round(multiple)
        if 0 < abs(whole) <= _PI_MULTIPLE_LIMIT and abs(multiple - whole) <= _PI_TOLERANCE * abs(
            multiple
        ):
            sign = "-" if whole < 0 else ""
            return f"{sign}π" if abs(whole) == 1 else f"{sign}{abs(whole)}·π"
    text = format(value, ".14g")
    return text.replace("e", "ᴇ").replace("ᴇ+", "ᴇ")


def _binary(op: ast.operator, left: float, right: float) -> float | None:
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.Div) and right != 0:
        return left / right
    return None


def parse_window_value(text: str) -> float:
    """Read a typed window value: a number, `π`, products and quotients of them (`-2·π`,
    `pi/2`, `3.1ᴇ2`). Raises ValueError for anything else."""
    source = (
        text.strip()
        .replace("·", "*")
        .replace("×", "*")
        .replace("−", "-")
        .replace("π", "pi")
        .replace("ᴇ", "e")
    )
    if not source:
        msg = "a window value is empty"
        raise ValueError(msg)
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as error:
        msg = f"not a number: {text!r}"
        raise ValueError(msg) from error

    def value(node: ast.expr) -> float:
        constant = node.value if isinstance(node, ast.Constant) else None
        if isinstance(constant, int | float) and not isinstance(constant, bool):
            return float(constant)
        if isinstance(node, ast.Name) and node.id == "pi":
            return math.pi
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
            inner = value(node.operand)
            return -inner if isinstance(node.op, ast.USub) else inner
        if isinstance(node, ast.BinOp):
            result = _binary(node.op, value(node.left), value(node.right))
            if result is not None:
                return result
        msg = f"not a number: {text!r}"
        raise ValueError(msg)

    result = value(tree.body)
    if not math.isfinite(result):
        msg = f"not a finite number: {text!r}"
        raise ValueError(msg)
    return result
