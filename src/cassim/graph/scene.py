"""The backend-neutral scene (FR-GRAPH-006): what Graphs, Data & Statistics and the sheet grid draw.

A page's model builds a `Scene` in screen pixels; the shell turns it into canvas shapes
(`cassim.app.scene_canvas`). Nothing here imports Flet, so scenes are built and tested headless and
kept as a page's cached scene between page switches (decision 0031, spike A).

The shapes follow spikes A and C: a curve is one `Polyline` (one canvas `Points` shape, decision
0004), separate segments such as an implicit curve's are one `Segments`, a filled region is one
`Fill` with fewer points than the curve, and a column of sheet cells is one multi-line `Label`.
Colours are names from the theme (`ink`, `axis`, `curve1`...), not values, so a theme change does
not rebuild a scene.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

type Point = tuple[float, float]


class Align(StrEnum):
    LEFT = "left"
    CENTRE = "centre"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class Stroke:
    colour: str = "ink"
    width: float = 1.0
    dashed: bool = False


@dataclass(frozen=True, slots=True)
class Polyline:
    """Joined points: one curve, or one branch of a curve between breaks."""

    points: tuple[Point, ...]
    stroke: Stroke = Stroke()


@dataclass(frozen=True, slots=True)
class Segments:
    """Separate line segments, two points each: an implicit curve, axis ticks, grid lines."""

    points: tuple[Point, ...]  # an even number: (start, end) pairs
    stroke: Stroke = Stroke()

    def __post_init__(self) -> None:
        if len(self.points) % 2:
            msg = "segments need an even number of points"
            raise ValueError(msg)


class Marker(StrEnum):
    DOT = "dot"
    SQUARE = "square"
    CROSS = "cross"


@dataclass(frozen=True, slots=True)
class Dots:
    """Plotted points: a scatter plot or a dot plot."""

    points: tuple[Point, ...]
    colour: str = "curve1"
    size: float = 4.0
    marker: Marker = Marker.DOT


@dataclass(frozen=True, slots=True)
class Fill:
    """A closed region: an integral, an inequality, a bar or a pie slice."""

    points: tuple[Point, ...]
    colour: str = "curve1"
    opacity: float = 0.3


@dataclass(frozen=True, slots=True)
class Box:
    """A rectangle's outline: the sheet cursor, a selection, a box plot's box."""

    x: float
    y: float
    width: float
    height: float
    stroke: Stroke = Stroke()


@dataclass(frozen=True, slots=True)
class Label:
    """Text at (x, y), its top-left (or top-right, top-centre) corner. Lines separated by `\\n` are
    `line_height` apart, which draws a whole column of cells as one shape (spike A)."""

    x: float
    y: float
    text: str
    size: float = 13.0
    colour: str = "ink"
    align: Align = Align.LEFT
    line_height: float | None = None  # pixels between lines; None is the font's own
    width: float | None = None  # wrap or clip at this width; None is unbounded


type Shape = Polyline | Segments | Dots | Fill | Box | Label


@dataclass(frozen=True, slots=True)
class Layer:
    """Shapes drawn together. A page keeps parts that change at different rates (the grid's text
    and its cursor) on separate layers, so a cursor move sends no text (spike A)."""

    name: str
    shapes: tuple[Shape, ...] = ()


@dataclass(frozen=True, slots=True)
class Scene:
    width: float
    height: float
    layers: tuple[Layer, ...] = field(default=())

    def layer(self, name: str) -> Layer | None:
        return next((layer for layer in self.layers if layer.name == name), None)

    def replace(self, layer: Layer) -> Scene:
        """This scene with the layer of the same name replaced (or added at the top)."""
        names = [existing.name for existing in self.layers]
        if layer.name not in names:
            return Scene(self.width, self.height, (*self.layers, layer))
        layers = tuple(
            layer if existing.name == layer.name else existing for existing in self.layers
        )
        return Scene(self.width, self.height, layers)


def column_label(
    at: Point, cells: list[str], row_height: float, *, align: Align = Align.LEFT
) -> Label:
    """One column of cells as one multi-line label from `at`: a row per line, `row_height` apart.
    A cell's own line breaks become spaces, so the rows stay in step."""
    text = "\n".join(cell.replace("\n", " ") for cell in cells)
    return Label(at[0], at[1], text, align=align, line_height=row_height)
