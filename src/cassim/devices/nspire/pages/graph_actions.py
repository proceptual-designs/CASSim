"""The Graphs page's Actions menu (FR-GRAPH-007), without Flet: Attributes, Text, Coordinates and
Equations, Calculate, and dragging a curve to move it (emulator check 6, run 7: R7-B2, R7-B8 and
R7-B10).

Attributes keep, for each function, the rows the device's attribute panel shows: line weight,
line style, label style, continuous or discrete, and for a discrete graph its step and number of
points. CASSim asks for them in a dialog rather than the device's panel of icons. Text,
coordinate labels and Calculate results are text objects at a point in graph units, so they stay
where they were put when the window moves. A curve dragged by the pointer is translated:
`2·sin(x)` becomes `2·sin(x-0.91)-0.044`.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cassim.device.wizard import Field, Wizard
from cassim.graph.sampling import Viewport

if TYPE_CHECKING:
    from collections.abc import Mapping

    from cassim.devices.nspire.pages.graphs import FunctionEntry, Graphs

WEIGHTS = ("Thin", "Medium", "Thick")
WEIGHT_PIXELS = (2.0, 3.0, 4.5)  # CASSim's thin is the width it always drew
STYLES = ("Continuous", "Dotted", "Dashed")
LABEL_STYLES = 5  # f1; f1(x); f1(x)=x+1; y=f1(x); y=x+1
DEFAULT_LABEL_STYLE = 3  # the device starts on 3/5
DEFAULT_POINTS = 25
NEAR_PIXELS = 8.0  # how close a tap must be to a curve or an object to take it


@dataclass
class Attributes:
    """One function's attributes, as the device's panel lists them."""

    weight: int = 0  # index into WEIGHTS
    style: int = 0  # index into STYLES
    label: int = DEFAULT_LABEL_STYLE  # 1 to 5
    discrete: bool = False
    points: int = DEFAULT_POINTS
    step: float | None = None  # None: the window's width over (points + 1)

    def dump(self) -> dict[str, Any]:
        return {
            "weight": self.weight,
            "style": self.style,
            "label": self.label,
            "discrete": self.discrete,
            "points": self.points,
            "step": self.step,
        }

    @classmethod
    def load(cls, data: object) -> Attributes:
        found = cls()
        if not isinstance(data, dict):
            return found
        found.weight = _index(data.get("weight"), len(WEIGHTS))
        found.style = _index(data.get("style"), len(STYLES))
        label = data.get("label")
        if isinstance(label, int) and not isinstance(label, bool) and 1 <= label <= LABEL_STYLES:
            found.label = label
        found.discrete = data.get("discrete") is True
        points = data.get("points")
        if isinstance(points, int) and not isinstance(points, bool) and 1 <= points <= 1000:  # noqa: PLR2004
            found.points = points
        step = data.get("step")
        if isinstance(step, int | float) and not isinstance(step, bool) and step > 0:
            found.step = float(step)
        return found


def _index(value: object, count: int) -> int:
    ok = isinstance(value, int) and not isinstance(value, bool) and 0 <= value < count
    return int(value) if ok else 0


@dataclass
class TextObject:
    """Text on the page at (x, y) in graph units: typed with Text, a point's coordinates from
    Coordinates and Equations, or a value from Calculate."""

    x: float
    y: float
    text: str

    def dump(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y, "text": self.text}

    @classmethod
    def load(cls, data: object) -> TextObject | None:
        if not isinstance(data, dict):
            return None
        x, y, text = data.get("x"), data.get("y"), data.get("text")
        numbers = all(
            isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v)
            for v in (x, y)
        )
        if not numbers or not isinstance(text, str):
            return None
        return cls(float(x), float(y), text)  # ty: ignore[invalid-argument-type]


# ---- labels ---------------------------------------------------------------------------------


def label_text(entry: FunctionEntry, style: int) -> str:
    """A graph's label in each of the five label styles (R7-B8)."""
    name, expression = entry.name, entry.expression
    return {
        1: name,
        2: f"{name}(x)",
        3: f"{name}(x)={expression}",
        4: f"y={name}(x)",
        5: f"y={expression}",
    }.get(style, f"{name}(x)={expression}")


# ---- hit testing ----------------------------------------------------------------------------


def _viewport(graphs: Graphs) -> Viewport:
    width, height = graphs.viewport_size
    return Viewport(graphs.window, width, height)


def curve_at(graphs: Graphs, x: float, y: float) -> int | None:
    """The plotted function whose curve passes within a few pixels of screen point (x, y)."""
    viewport = _viewport(graphs)
    window = viewport.window
    gx = window.x_min + x * (window.x_max - window.x_min) / viewport.width
    best: tuple[float, int] | None = None
    for index, entry in enumerate(graphs.functions):
        if not entry.visible or entry.compiled is None:
            continue
        try:
            value = float(entry.compiled(gx))
        except ArithmeticError, TypeError, ValueError:
            continue
        if not math.isfinite(value):
            continue
        _, sy = viewport.window.to_screen(gx, value, viewport.width, viewport.height)
        distance = abs(sy - y)
        if distance <= NEAR_PIXELS and (best is None or distance < best[0]):
            best = (distance, index)
    return best[1] if best is not None else None


def text_at(graphs: Graphs, x: float, y: float) -> int | None:
    """The text object whose start is within a few pixels of screen point (x, y)."""
    viewport = _viewport(graphs)
    for index, item in enumerate(graphs.texts):
        sx, sy = viewport.window.to_screen(item.x, item.y, viewport.width, viewport.height)
        if abs(sx - x) <= NEAR_PIXELS * 4 and abs(sy - y) <= NEAR_PIXELS * 2:
            return index
    return None


# ---- dragging a curve -----------------------------------------------------------------------

# x as a variable: not part of a name (max, x1), but after a digit (2x is 2·x)
_X = re.compile(r"(?<![A-Za-z_.])x(?![A-Za-z0-9_(])")


def _short(value: float) -> str:
    """Two significant figures, as the device writes a dragged shift (x-0.91, -0.044)."""
    text = f"{value:.2g}"
    if "e" in text:
        text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text


def translated(expression: str, dx: float, dy: float) -> str:
    """`expression` moved right by dx and up by dy: x becomes (x-dx) and dy is added
    (R7-B2: a drag turned `2·sin(x)` into `2·sin(x-0.91)-0.044`)."""
    text = expression
    if abs(dx) > 0:
        shift = _short(abs(dx))
        replacement = f"x-{shift}" if dx > 0 else f"x+{shift}"
        bare = _X.fullmatch(text.strip()) is not None
        text = _X.sub(replacement if bare else f"({replacement})", text)
        text = re.sub(r"\((x[-+][0-9.]+)\)(?=\))", r"\1", text)  # sin((x-1)) is sin(x-1)
    if abs(dy) > 0:
        shift = _short(abs(dy))
        text = f"{text}+{shift}" if dy > 0 else f"{text}-{shift}"
    return text


def drag_curve(graphs: Graphs, index: int, dx_pixels: float, dy_pixels: float) -> None:
    """Move function `index` by a drag of (dx, dy) screen pixels, and redefine it."""
    if not 0 <= index < len(graphs.functions):
        return
    entry = graphs.functions[index]
    if not entry.expression:
        return
    width, height = graphs.viewport_size
    window = graphs.window
    dx = dx_pixels * (window.x_max - window.x_min) / width
    dy = -dy_pixels * (window.y_max - window.y_min) / height
    if abs(dx_pixels) < 1 and abs(dy_pixels) < 1:
        return
    graphs.submit(index, translated(entry.expression, dx, dy))


# ---- the tools ------------------------------------------------------------------------------


def attributes_wizard(entry: FunctionEntry, found: Attributes) -> Wizard:
    """Attributes for one graph, row for row as the device's panel has them (R7-B8)."""

    def choices(labels: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
        return tuple((str(index), label) for index, label in enumerate(labels))

    labels = tuple(f"{n}: {label_text(entry, n)}" for n in range(1, LABEL_STYLES + 1))
    return Wizard(
        f"Attributes: graph {entry.name}",
        (
            Field("weight", "Line weight", str(found.weight), choices=choices(WEIGHTS)),
            Field("style", "Line style", str(found.style), choices=choices(STYLES)),
            Field(
                "label",
                "Label style",
                str(found.label),
                choices=tuple((str(n), labels[n - 1]) for n in range(1, LABEL_STYLES + 1)),
            ),
            Field(
                "discrete",
                "Continuous or discrete",
                "1" if found.discrete else "0",
                choices=(("0", "Graph is continuous"), ("1", "Graph is discrete")),
            ),
            Field("points", "Number of points (discrete)", str(found.points)),
        ),
    )


def attributes_problems(values: Mapping[str, str]) -> list[str]:
    """What is wrong with the Attributes dialog's fields, shown before it closes."""
    try:
        points = int(values.get("points", str(DEFAULT_POINTS)))
    except ValueError:
        return ["Number of points must be a whole number."]
    if not 1 <= points <= 1000:  # noqa: PLR2004
        return ["Number of points must be from 1 to 1000."]
    return []


def apply_attributes(graphs: Graphs, name: str, values: Mapping[str, str]) -> list[str]:
    """Keep the attributes a dialog gave (and a discrete step loaded with the document); the
    problems instead, if a field will not do."""
    problems = attributes_problems(values)
    if problems:
        return problems
    found = graphs.attributes.get(name, Attributes())
    graphs.attributes[name] = Attributes(
        weight=_index(_int(values.get("weight")), len(WEIGHTS)),
        style=_index(_int(values.get("style")), len(STYLES)),
        label=min(max(_int(values.get("label")) or DEFAULT_LABEL_STYLE, 1), LABEL_STYLES),
        discrete=values.get("discrete") == "1",
        points=int(values.get("points", str(found.points))),
        step=found.step,
    )
    return []


def _int(text: str | None) -> int:
    try:
        return int(text or "")
    except ValueError:
        return 0


def coordinates_text(graphs: Graphs, x: float, y: float) -> str | None:
    """What Coordinates and Equations labels at screen point (x, y): a kept or analysed point's
    coordinates, or a curve's equation (R7-B10); None if nothing is there."""
    from cassim.devices.nspire.pages.graph_tools import coordinate_text  # noqa: PLC0415

    viewport = _viewport(graphs)
    for point in marked_points(graphs):
        sx, sy = viewport.window.to_screen(*point, viewport.width, viewport.height)
        if math.hypot(sx - x, sy - y) <= NEAR_PIXELS:
            return f"({coordinate_text(point[0])}, {coordinate_text(point[1])})"
    index = curve_at(graphs, x, y)
    if index is None:
        return None
    entry = graphs.functions[index]
    return label_text(entry, DEFAULT_LABEL_STYLE)


def marked_points(graphs: Graphs) -> list[tuple[float, float]]:
    """The points on the page that Coordinates and Equations can label."""
    from cassim.devices.nspire.pages import graph_analyze  # noqa: PLC0415

    return graph_analyze.marked_points(graphs)


def calculate(graphs: Graphs, index: int) -> None:
    """Calculate on a text object: its text worked out in the Problem (R7-B10: `12` gives 12),
    shown beside it. In the browser the engine works it out, and the answer is placed when its
    reply comes back (`Graphs.update`)."""
    from cassim.device.engine import RemoteSession, graph_calc, graph_calc_op  # noqa: PLC0415

    if not 0 <= index < len(graphs.texts):
        return
    session = graphs.session
    line = graphs.texts[index].text
    if isinstance(session, RemoteSession):
        session.outbox.append(graph_calc_op(index, line))
        return
    place_calculation(graphs, index, graph_calc(session, index, line)["text"])


def place_calculation(graphs: Graphs, index: int, value: str | None) -> None:
    """Show Calculate's answer for text object `index` just after it (nothing if it did not
    work out)."""
    if value is None or not 0 <= index < len(graphs.texts):
        return
    item = graphs.texts[index]
    width = graphs.window.x_max - graphs.window.x_min
    graphs.texts.append(TextObject(item.x + width * 0.06 * len(item.text), item.y, value))
