"""Spike A painter: a `Layout` as Flet canvas shapes. The only module here that imports Flet.

`cv.Text` puts the *top of its line box* at (x, y) with the default TOP_LEFT alignment. The line
box's ascent is the font's hhea ascender (`BASELINE` below, checked by screenshot in
`run_math_render_a.py`), so a glyph run whose baseline is at `b` is drawn at y = b - ascent * size.
"""

from __future__ import annotations

import flet as ft
import flet.canvas as cv

import mathlayout as ml

_FAMILY = {
    "Main-Regular": ("KaTeX_Main", False, False),
    "Main-Bold": ("KaTeX_Main", True, False),
    "Main-Italic": ("KaTeX_Main", False, True),
    "Math-Italic": ("KaTeX_Math", False, True),
    "Math-BoldItalic": ("KaTeX_Math", True, True),
    "AMS-Regular": ("KaTeX_AMS", False, False),
    "Size1-Regular": ("KaTeX_Size1", False, False),
    "Size2-Regular": ("KaTeX_Size2", False, False),
    "Size3-Regular": ("KaTeX_Size3", False, False),
    "Size4-Regular": ("KaTeX_Size4", False, False),
    "Typewriter-Regular": ("KaTeX_Typewriter", False, False),
}

# Where the baseline sits below the top of cv.Text's line box, in ems, per font: the hhea
# ascender plus half the hhea lineGap (half-leading above the ascent). The first calibration run
# with the ascender alone put every glyph 0.045 em (= lineGap / 2 in all KaTeX fonts) too low.
BASELINE = {
    font: ml.font_vertical(font)["hhea"][0] + ml.font_vertical(font)["hhea"][2] / 2 for font in _FAMILY
}


def text_style(font: str, size: float, colour: str) -> ft.TextStyle:
    family, bold, italic = _FAMILY[font]
    return ft.TextStyle(
        size=size,
        color=colour,
        font_family=f"packages/flutter_math_fork/{family}",
        weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
        italic=italic,
    )


def glyph_shape(font: str, text: str, x: float, baseline: float, size: float, colour: str) -> cv.Text:
    """`text` with its baseline starting at (x, baseline) in pixels."""
    return cv.Text(x, baseline - BASELINE[font] * size, text, text_style(font, size, colour))


def shapes(lay: ml.Layout, px: float, ox: float, oy: float, colour: str) -> list[cv.Shape]:
    """The layout's items in pixels: em size `px`, root baseline starting at (ox, oy)."""
    fill = ft.Paint(color=colour, style=ft.PaintingStyle.FILL)
    out: list[cv.Shape] = []
    for it in lay.items:
        match it:
            case ml.Glyphs():
                out.append(glyph_shape(it.font, it.text, ox + it.x * px, oy + it.y * px, it.scale * px, colour))
            case ml.Rule():
                out.append(cv.Rect(ox + it.x * px, oy + it.y * px, it.w * px, it.h * px, paint=fill))
            case ml.Poly():
                pts = [(ox + x * px, oy + y * px) for x, y in it.points]
                elements: list[cv.Path.PathElement] = [cv.Path.MoveTo(*pts[0])]
                elements += [cv.Path.LineTo(*p) for p in pts[1:]]
                elements.append(cv.Path.Close())
                out.append(cv.Path(elements, paint=fill))
    return out


def overlay(lay: ml.Layout, px: float, ox: float, oy: float, path, pos: int,
            span: tuple[int, int] | None, colour: str = "#4da3ff", sel: str = "#7fb2e8") -> list[cv.Shape]:
    """The cursor bar and selection boxes: drawn on their own canvas, so moving them never
    touches the content."""
    out: list[cv.Shape] = []
    if span is not None and span[1] > span[0]:
        for x, y, w, h in lay.selection_rects(path, *span):
            out.append(cv.Rect(ox + x * px, oy + y * px, w * px, h * px,
                               paint=ft.Paint(color=ft.Colors.with_opacity(0.45, sel))))
    x, top, bottom = lay.caret(path, pos)
    w = max(1.5, 0.06 * px * lay.rows[tuple(path)].scale)
    out.append(cv.Rect(ox + x * px - w / 2, oy + top * px, w, (bottom - top) * px,
                       paint=ft.Paint(color=colour)))
    return out
