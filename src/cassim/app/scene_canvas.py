"""A `Scene` drawn as Flet canvas shapes (FR-GRAPH-006): the only Flet code that knows the scene.

Every device's pages draw through this, so it lives in the shell. One `Polyline` is one `Points`
shape (decision 0004); `Segments` is one `Points` shape in lines mode; a `Fill` is one `Path`.
"""

from __future__ import annotations

from collections.abc import Mapping

import flet as ft
import flet.canvas as cv

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

# Colour names a scene uses, for the dark theme. A theme may override any of them.
COLOURS: Mapping[str, str] = {
    "ink": "#e8e8e8",
    "axis": "#9a9a9a",
    "grid": "#3a3a3a",
    "cursor": "#6aa9ff",
    "selection": "#2d5fa8",
    "curve1": "#4f9dff",
    "curve2": "#ff6b6b",
    "curve3": "#5fd068",
    "curve4": "#ffb84d",
    "curve5": "#c77dff",
    "curve6": "#4dd0e1",
}

_ALIGN = {
    Align.LEFT: (ft.Alignment.TOP_LEFT, ft.TextAlign.LEFT),
    Align.CENTRE: (ft.Alignment.TOP_CENTER, ft.TextAlign.CENTER),
    Align.RIGHT: (ft.Alignment.TOP_RIGHT, ft.TextAlign.RIGHT),
}


def _colour(name: str, colours: Mapping[str, str]) -> str:
    return colours.get(name) or COLOURS.get(name) or name


def _paint(stroke: Stroke, colours: Mapping[str, str]) -> ft.Paint:
    return ft.Paint(
        color=_colour(stroke.colour, colours),
        stroke_width=stroke.width,
        style=ft.PaintingStyle.STROKE,
        stroke_dash_pattern=[4, 4] if stroke.dashed else None,
    )


def shape(item: Shape, colours: Mapping[str, str] = COLOURS) -> cv.Shape:
    """One scene shape as one canvas shape."""
    match item:
        case Polyline(points, stroke):
            return cv.Points(list(points), cv.PointMode.POLYGON, _paint(stroke, colours))
        case Segments(points, stroke):
            return cv.Points(list(points), cv.PointMode.LINES, _paint(stroke, colours))
        case Dots(points, colour, size, marker):
            paint = ft.Paint(
                color=_colour(colour, colours),
                stroke_width=size,
                stroke_cap=ft.StrokeCap.SQUARE if marker is Marker.SQUARE else ft.StrokeCap.ROUND,
            )
            return cv.Points(list(points), cv.PointMode.POINTS, paint)
        case Fill(points, colour, opacity):
            elements: list[cv.Path.PathElement] = [cv.Path.MoveTo(*points[0])]
            elements += [cv.Path.LineTo(*point) for point in points[1:]]
            elements.append(cv.Path.Close())
            paint = ft.Paint(
                color=ft.Colors.with_opacity(opacity, _colour(colour, colours)),
                style=ft.PaintingStyle.FILL,
            )
            return cv.Path(elements, paint)
        case Box(x, y, width, height, stroke):
            return cv.Rect(x, y, width, height, paint=_paint(stroke, colours))
        case Label(x, y, text, size, colour, align, line_height, width):
            alignment, text_align = _ALIGN[align]
            style = ft.TextStyle(
                size=size,
                color=_colour(colour, colours),
                height=None if line_height is None else line_height / size,
            )
            return cv.Text(
                x,
                y,
                text,
                style,
                alignment=alignment,
                text_align=text_align,
                max_width=float("inf") if width is None else width,
            )
    msg = f"not a scene shape: {item!r}"
    raise TypeError(msg)


def layer_shapes(layer: Layer, colours: Mapping[str, str] = COLOURS) -> list[cv.Shape]:
    return [shape(item, colours) for item in layer.shapes if _drawable(item)]


def _drawable(item: Shape) -> bool:
    """A curve or fill of one point or none draws nothing; leave it out."""
    if isinstance(item, Polyline | Fill):
        return len(item.points) > 1
    return True


def canvas(scene: Scene, colours: Mapping[str, str] = COLOURS) -> ft.Stack:
    """The scene as a stack of canvases, one per layer, so a layer is redrawn on its own."""
    layers: list[ft.Control] = [
        cv.Canvas(layer_shapes(layer, colours), width=scene.width, height=scene.height)
        for layer in scene.layers
    ]
    return ft.Stack(layers, width=scene.width, height=scene.height)
