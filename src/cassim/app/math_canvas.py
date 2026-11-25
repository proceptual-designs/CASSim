"""Maths drawn on a Flet canvas from our own layout (decision 0038).

`device/math_layout.py` says where every glyph, rule and row is; this module only paints that:
the maths on one canvas, the selection on a canvas under it and the cursor on one over it, so
neither is part of the maths and neither can move it. One gesture detector covers the lot and a
click is turned into a place in the tree by the layout (`Layout.hit`), exactly, at any depth.

A line of plain characters is one shape, and a large result a few dozen: the entry line this
replaced (decision 0019) made about ten controls a character.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import flet as ft
import flet.canvas as cv

from cassim.app.theme import Theme
from cassim.device import math_layout as ml
from cassim.device.editor import Editor

type Click = Callable[[Sequence[tuple[int, int]], int], None]  # a row's path, a position in it

CURSOR_WIDTH = 2.0
PAD = 2.0  # pixels round the maths: room for a cursor at either end
HIT = "#01ffffff"  # all but invisible, but a coloured box takes clicks where nothing is drawn
_FONTS = "packages/flutter_math_fork/KaTeX_"  # the fonts the history's LaTeX is drawn with
_FAMILY: dict[str, tuple[str, bool, bool]] = {  # family, bold, italic
    "Main-Regular": ("Main", False, False),
    "Main-Bold": ("Main", True, False),
    "Main-Italic": ("Main", False, True),
    "Math-Italic": ("Math", False, True),
    "Math-BoldItalic": ("Math", True, True),
    "AMS-Regular": ("AMS", False, False),
    "Size1-Regular": ("Size1", False, False),
    "Size2-Regular": ("Size2", False, False),
    "Size3-Regular": ("Size3", False, False),
    "Size4-Regular": ("Size4", False, False),
    "Typewriter-Regular": ("Typewriter", False, False),
}
_FALLBACK_ASCENT = 0.93  # the app's own font, for a character no KaTeX font has


@dataclass(frozen=True)
class MathStyle:
    """What a device may choose about how its maths lines look; the defaults are the Nspire's."""

    selection: str = "#7fb2e8"
    cursor_in_selection: str = "#0b3d78"


DEFAULT_STYLE = MathStyle()


def faint(colour: str) -> str:
    """`colour` (#rrggbb) at four tenths: a bracket Enter will add."""
    return "#66" + colour[-6:]


def _glyphs(run: ml.Glyphs, size: float, origin: tuple[float, float], colour: str) -> cv.Text:
    """A run of characters, its baseline where the layout put it. A canvas places text by the
    top of its line, which is the font's ascent above the baseline."""
    pixels = run.scale * size
    family, bold, italic = _FAMILY.get(run.font, ("", False, False))
    ascent = ml.ascent(run.font) if family else _FALLBACK_ASCENT
    style = ft.TextStyle(
        size=pixels,
        color=faint(colour) if run.faint else colour,
        font_family=_FONTS + family if family else None,
        weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
        italic=italic,
        letter_spacing=0,
    )
    x, y = origin
    return cv.Text(x + run.x * size, y + run.y * size - ascent * pixels, run.text, style)


def content_shapes(
    layout: ml.Layout, size: float, origin: tuple[float, float], colour: str
) -> list[cv.Shape]:
    """The maths itself: `size` pixels to the em, the root's baseline starting at `origin`."""
    x, y = origin
    fill = ft.Paint(color=colour, style=ft.PaintingStyle.FILL)
    shapes: list[cv.Shape] = []
    for item in layout.items:
        if isinstance(item, ml.Glyphs):
            shapes.append(_glyphs(item, size, origin, colour))
        elif isinstance(item, ml.Rule):
            shapes.append(
                cv.Rect(
                    x + item.x * size,
                    y + item.y * size,
                    item.width * size,
                    max(item.height * size, 1.0),  # a hairline is still a whole pixel
                    paint=fill,
                )
            )
        else:
            points = [(x + px * size, y + py * size) for px, py in item.points]
            outline: list[cv.Path.PathElement] = [cv.Path.MoveTo(*points[0])]
            outline += [cv.Path.LineTo(*point) for point in points[1:]]
            outline.append(cv.Path.Close())
            shapes.append(cv.Path(outline, paint=fill))
    return shapes


class MathLine:
    """Draws one editor's maths with its cursor and selection; `click` is told where the user
    clicked. After `build` it also says how wide the drawing is and where its cursor is, so a
    long line can be scrolled to keep the cursor in view."""

    def __init__(
        self,
        theme: Theme,
        size: float,
        click: Click,
        is_defined: Callable[[str], bool] = lambda _: False,
        hold: Click | None = None,
    ) -> None:
        self.theme = theme
        self.style = DEFAULT_STYLE
        self.size = size
        self.click = click
        self.is_defined = is_defined
        # A long press is the touch screen's shift+click: it extends the selection (0019)
        self.hold = hold or click
        # Selected text dragged onto a place moves there (run 5, H3 k); None: no dragging
        self.drop: Click | None = None
        self.layout = ml.layout([])
        self.width = self.height = self.cursor_x = 0.0
        self._origin = (PAD, PAD)
        self._chosen: list[ml.Rect] = []
        self._dragging = False

    # ---- geometry ---------------------------------------------------------------------------

    def _pixels(self, rect: ml.Rect) -> ml.Rect:
        x, y, width, height = rect
        size = self.size
        return (self._origin[0] + x * size, self._origin[1] + y * size, width * size, height * size)

    def place_at(self, x: float, y: float) -> tuple[ml.Path, int]:
        """The place in the tree that a click at (x, y) pixels in the drawing means."""
        return self.layout.hit((x - self._origin[0]) / self.size, (y - self._origin[1]) / self.size)

    def point_at(self, path: Sequence[tuple[int, int]], pos: int) -> tuple[float, float]:
        """The middle of the cursor at a place, in pixels in the drawing (the reverse of
        `place_at`; the tests click here)."""
        x, top, bottom = self.layout.caret(path, pos)
        return self._origin[0] + x * self.size, self._origin[1] + (top + bottom) / 2 * self.size

    # ---- drawing ----------------------------------------------------------------------------

    def build(self, editor: Editor, *, active: bool = True) -> ft.Control:
        """The whole line; with `active` false it is drawn with no cursor or selection."""
        size = self.size
        closers = editor.missing_closers() if active else ""
        self.layout = layout = ml.layout(editor.root, self.is_defined, closers=closers)
        up = max(layout.height, ml.LINE_ASCENT)
        down = max(layout.depth, ml.LINE_DESCENT)
        self._origin = (PAD, PAD + up * size)
        self.width = layout.width * size + 2 * PAD
        self.height = (up + down) * size + 2 * PAD
        colour = self.theme.screen_text
        layers: list[ft.Control] = []
        self._chosen = self._selection(editor) if active else []
        if self._chosen:
            shade = ft.Paint(color=self.style.selection, style=ft.PaintingStyle.FILL)
            layers.append(
                cv.Canvas(
                    [cv.Rect(*rect, paint=shade) for rect in self._chosen],
                    width=self.width,
                    height=self.height,
                )
            )
        layers.append(
            cv.Canvas(
                content_shapes(layout, size, self._origin, colour),
                width=self.width,
                height=self.height,
            )
        )
        if active:
            layers.append(cv.Canvas([self._cursor(editor)], width=self.width, height=self.height))
        dragged = self.drop is not None and bool(self._chosen)
        return ft.GestureDetector(
            ft.Container(ft.Stack(layers, width=self.width, height=self.height), bgcolor=HIT),
            on_tap_up=self._tapped,
            on_long_press_start=self._held,
            on_pan_start=self._drag_start if dragged else None,
            on_pan_end=self._drag_end if dragged else None,
        )

    def _selection(self, editor: Editor) -> list[ml.Rect]:
        """What is highlighted, in pixels: the selected run of the cursor's row, or the whole
        cells of a matrix's selected rows or columns."""
        if editor.cell_sel is not None and editor.path:
            *above, (index, _slot) = editor.path
            cells = [self.layout.cell((*above, (index, cell))) for cell in editor.selected_cells()]
            return [self._pixels(cell) for cell in cells]
        low, high = editor.span
        chosen = self.layout.selection(editor.path, low, high) if high > low else None
        return [self._pixels(chosen)] if chosen is not None else []

    def _cursor(self, editor: Editor) -> cv.Shape:
        x, top, bottom = self.layout.caret(editor.path, editor.pos)
        left, top_px, _width, height = self._pixels((x, top, 0.0, bottom - top))
        self.cursor_x = left
        low, high = editor.span
        colour = self.style.cursor_in_selection if high > low else self.theme.accent
        return cv.Rect(
            left - CURSOR_WIDTH / 2,
            top_px,
            CURSOR_WIDTH,
            height,
            paint=ft.Paint(color=colour, style=ft.PaintingStyle.FILL),
        )

    # ---- the pointer ------------------------------------------------------------------------

    def _tapped(self, event: ft.TapEvent) -> None:
        position = event.local_position
        if position is not None:
            self.click(*self.place_at(position.x, position.y))

    def _held(self, event: ft.LongPressStartEvent) -> None:
        position = event.local_position
        if position is not None:
            self.hold(*self.place_at(position.x, position.y))

    def in_selection(self, x: float, y: float) -> bool:
        return any(
            left <= x <= left + width and top <= y <= top + height
            for left, top, width, height in self._chosen
        )

    def _drag_start(self, event: ft.DragStartEvent) -> None:
        position = event.local_position
        self._dragging = self.in_selection(position.x, position.y)

    def _drag_end(self, event: ft.DragEndEvent) -> None:
        """Selected text dragged to a place moves there."""
        if self._dragging and self.drop is not None:
            position = event.local_position
            self.drop(*self.place_at(position.x, position.y))
        self._dragging = False


def draw(row: ml.Row, theme: Theme, size: float) -> ft.Control:
    """`row` as a drawing with no cursor: a history row, a label."""
    layout = ml.layout(row)
    up, down = max(layout.height, ml.LINE_ASCENT), max(layout.depth, ml.LINE_DESCENT)
    return cv.Canvas(
        content_shapes(layout, size, (PAD, PAD + up * size), theme.screen_text),
        width=layout.width * size + 2 * PAD,
        height=(up + down) * size + 2 * PAD,
    )
