"""Paint a `Layout` as absolutely positioned Flet controls (spike B).

One Stack of Text runs and thin Containers; no per-character controls. The caret and selection are
a second Stack on top that never takes part in layout.
"""

from __future__ import annotations

import flet as ft
from layout import FACES, Layout, baseline_offset, glyph

FAMILY = "packages/flutter_math_fork/KaTeX_"


def paint(
    layout: Layout, colour: str, *, per_char: bool = False
) -> list[ft.Control]:
    """Controls for the layout's items. `per_char` splits runs (to test run merging)."""
    out: list[ft.Control] = []
    for it in layout.items:
        kind = it[0]
        if kind == "t":
            _k, x, y, text, face, size, sy = it
            pieces = [(x, text)]
            if per_char:
                pieces, cx = [], x
                for ch in text:
                    pieces.append((cx, ch))
                    cx += glyph(face, ch)[0] * size
            for px, chunk in pieces:
                out.append(_text(chunk, px, y, face, size, sy, colour))
        elif kind == "r":
            _k, x, y, w, h = it
            out.append(ft.Container(left=x, top=y, width=w, height=h, bgcolor=colour))
        elif kind == "f":
            _k, x, y, w, h = it
            out.append(
                ft.Container(
                    left=x, top=y, width=w, height=h, border=ft.Border.all(1, colour), opacity=0.7
                )
            )
    return out


def _text(chunk: str, x: float, y: float, face: str, size: float, sy: float, colour: str) -> ft.Text:
    fam, bold, italic, _m = FACES[face]
    off = baseline_offset(face, size)
    scale = None
    if abs(sy - 1.0) > 1e-3:
        # scale vertically about the baseline: alignment is -1..1 across the Text's box (height=size)
        scale = ft.Scale(scale_y=sy, alignment=ft.Alignment(0, 2 * off / size - 1))
    return ft.Text(
        chunk,
        left=x,
        top=y - off,
        size=size,
        color=colour,
        font_family=FAMILY + fam,
        weight=ft.FontWeight.BOLD if bold else None,
        italic=italic,
        no_wrap=True,
        style=ft.TextStyle(height=1.0, letter_spacing=0),  # letter_spacing None drifts 0.24 px/char
        scale=scale,
    )


def count_controls(control: object) -> int:
    """Controls in a tree, counted through `content` and `controls`."""
    n = 1
    content = getattr(control, "content", None)
    if content is not None:
        n += count_controls(content)
    for child in getattr(control, "controls", None) or []:
        n += count_controls(child)
    return n
