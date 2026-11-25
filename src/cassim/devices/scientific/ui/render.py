"""Natural display: draw a layout tree (`layout.py`) with Flet controls.

The LCD uses Roboto Mono, whose characters are all 0.6 em wide, so the width of any part can be
worked out without measuring. That is how a fraction bar is made as wide as the wider of its two
parts, and how a long entry is scrolled to keep the cursor on screen (◀ ▶ show there is more).
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft
import flet.canvas as cv

from cassim.devices.scientific.layout import (
    Abs,
    Box,
    Cursor,
    Frac,
    Node,
    Root,
    Seq,
    Sqrt,
    Sub,
    Sup,
    Text,
)

FONT = "CASSim LCD"
FONT_FILE = "fonts/RobotoMono-Regular.ttf"
FALLBACK = ["CASSim Math", "CASSim Symbols"]
FONTS = {
    FONT: FONT_FILE,
    "CASSim Math": "fonts/NotoSansMath-Regular.ttf",
    "CASSim Symbols": "fonts/NotoSansSymbols2-Regular.ttf",
}
ADVANCE = 0.6  # Roboto Mono's character width, in em
SMALL = 0.62  # exponents and root indices
FRACTION = 0.82  # numerators and denominators
MIXED_GAP = 0.0  # em between a mixed number's whole part and its fraction: none, as typed
RADICAL = 0.55  # the √ sign's width, in em


@dataclass(frozen=True)
class Gap:
    """Space between drawn parts, in em."""

    em: float


def _tight(seq: Seq) -> list[Node | Gap]:
    """The sequence as drawn: a mixed number's "1 " before its fraction becomes "1" and a small
    `Gap`, so the answer 1 3/4 is spaced as the typed entry is."""
    out: list[Node | Gap] = []
    for index, node in enumerate(seq):
        following = seq[index + 1] if index + 1 < len(seq) else None
        if isinstance(node, Text) and node.text.endswith(" ") and isinstance(following, Frac):
            out.extend((Text(node.text.rstrip(" ")), Gap(MIXED_GAP)))
        else:
            out.append(node)
    return out


def width(seq: Seq, size: float) -> float:
    return sum(
        part.em * size if isinstance(part, Gap) else node_width(part, size) for part in _tight(seq)
    )


def height(seq: Seq, size: float) -> float:
    """The drawn height of a row (its tallest part), worked out as `width` is."""
    return max(
        (node_height(part, size) for part in _tight(seq) if not isinstance(part, Gap)),
        default=size,
    )


def _stroke(size: float) -> float:
    return max(1.0, size * 0.07)


def _bar(size: float) -> float:
    return max(1.5, size * 0.08)


def node_height(node: Node, size: float) -> float:  # noqa: PLR0911
    match node:
        case Text():
            return size
        case Frac(num, den):
            inner = size * FRACTION
            return height(num, inner) + height(den, inner) + _bar(size) + 2
        case Sqrt(arg):
            return height(arg, size) + 2 * _stroke(size) + 2
        case Root(index, arg):
            return max(height(index, size * SMALL) + size * 0.5, node_height(Sqrt(arg), size))
        case Sup(exp):
            return height(exp, size * SMALL) + size * 0.6
        case Sub(arg):
            return height(arg, size * SMALL) + size * 0.5
        case Abs(arg):
            return max(size, height(arg, size))
        case Box():
            return size * 0.8
        case Cursor():
            return size * 1.1
    return size


def node_width(node: Node, size: float) -> float:  # noqa: PLR0911
    match node:
        case Text(text):
            return len(text) * ADVANCE * size
        case Frac(num, den):
            return max(width(num, size * FRACTION), width(den, size * FRACTION)) + 4
        case Sqrt(arg):
            return RADICAL * size + width(arg, size) + 3
        case Root(index, arg):
            return width(index, size * SMALL) + RADICAL * size + width(arg, size) + 3
        case Sup(exp):
            return width(exp, size * SMALL)
        case Sub(arg):
            return width(arg, size * SMALL)
        case Abs(arg):
            return 2 * ADVANCE * size + width(arg, size)
        case Box():
            return ADVANCE * size
        case Cursor():
            return 2
    return 0


def _text(text: str, size: float, color: str) -> ft.Text:
    return ft.Text(
        text,
        size=size,
        color=color,
        font_family=FONT,
        style=ft.TextStyle(font_family_fallback=FALLBACK, height=1.0),
        no_wrap=True,
    )


class Renderer:
    def __init__(self, color: str, cursor: str) -> None:
        self.color = color
        self.cursor = cursor

    def row(self, seq: Seq, size: float) -> ft.Row:
        return ft.Row(
            [
                ft.Container(width=part.em * size)
                if isinstance(part, Gap)
                else self.node(part, size)
                for part in _tight(seq)
            ],
            spacing=0,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def node(self, node: Node, size: float) -> ft.Control:  # noqa: PLR0911
        match node:
            case Text(text):
                return _text(text, size, self.color)
            case Frac(num, den):
                inner = size * FRACTION
                bar = max(width(num, inner), width(den, inner)) + 2
                return ft.Container(
                    ft.Column(
                        [
                            self.row(num, inner),
                            ft.Container(width=bar, height=_bar(size), bgcolor=self.color),
                            self.row(den, inner),
                        ],
                        spacing=1,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=1),
                )
            case Sqrt(arg):
                return self.radical(arg, size)
            case Root(index, arg):
                return ft.Row(
                    [
                        ft.Container(
                            self.row(index, size * SMALL),
                            padding=ft.Padding.only(bottom=size * 0.5),
                        ),
                        self.radical(arg, size),
                    ],
                    spacing=0,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                )
            case Sup(exp):
                return ft.Container(
                    self.row(exp, size * SMALL), padding=ft.Padding.only(bottom=size * 0.6)
                )
            case Sub(arg):
                return ft.Container(
                    self.row(arg, size * SMALL), padding=ft.Padding.only(top=size * 0.5)
                )
            case Abs(arg):
                return ft.Row(
                    [
                        _text("|", size, self.color),
                        self.row(arg, size),
                        _text("|", size, self.color),
                    ],
                    spacing=0,
                    tight=True,
                )
            case Box():
                return ft.Container(
                    width=ADVANCE * size,
                    height=size * 0.8,
                    border=ft.Border.all(1, self.color),
                )
            case Cursor():
                return ft.Container(width=2, height=size * 1.1, bgcolor=self.cursor)
        return ft.Container()

    def radical(self, arg: Seq, size: float) -> ft.Control:
        """√ and its vinculum as one stroke, sized to the argument: a short tick, down to the
        baseline, up to the top, then along over the argument. (A √ character and a separate
        line meet only by luck, and never over a fraction.)"""
        stroke = _stroke(size)
        sign = RADICAL * size
        top = stroke / 2
        gap = 2 * stroke + 2  # the argument starts below the vinculum
        total_w = sign + width(arg, size) + 3
        total_h = height(arg, size) + gap
        path = cv.Path(
            elements=[
                cv.Path.MoveTo(0, total_h * 0.6),
                cv.Path.LineTo(sign * 0.25, total_h * 0.52),
                cv.Path.LineTo(sign * 0.55, total_h - stroke / 2),
                cv.Path.LineTo(sign - stroke / 2, top),
                cv.Path.LineTo(total_w, top),
            ],
            paint=ft.Paint(
                color=self.color,
                stroke_width=stroke,
                style=ft.PaintingStyle.STROKE,
                stroke_join=ft.StrokeJoin.ROUND,
                stroke_cap=ft.StrokeCap.ROUND,
            ),
        )
        return cv.Canvas(
            shapes=[path],
            content=ft.Container(
                self.row(arg, size), padding=ft.Padding.only(left=sign + 2, right=1, top=gap)
            ),
            width=total_w,
            height=total_h,
        )

    def line(self, seq: Seq, size: float, available: float, *, keep: str = "cursor") -> ft.Row:
        """One LCD line in `available` pixels: a long entry scrolls to keep the cursor visible
        (keep='cursor'); a long answer shrinks (keep='shrink')."""
        total = width(seq, size)
        if total <= available:
            return self.row(seq, size)
        if keep == "shrink":
            return self.row(seq, max(size * 0.55, size * available / total))
        widths = [node_width(node, size) for node in seq]
        at = next((i for i, node in enumerate(seq) if isinstance(node, Cursor)), len(seq) - 1)
        marker = ADVANCE * size
        start, end = at, at + 1
        used = widths[at] if seq else 0
        room = available - 2 * marker
        while True:
            grew = False
            if start > 0 and used + widths[start - 1] <= room:
                start -= 1
                used += widths[start]
                grew = True
            if end < len(seq) and used + widths[end] <= room:
                used += widths[end]
                end += 1
                grew = True
            if not grew:
                break
        nodes: list[Node] = []
        if start > 0:
            nodes.append(Text("◀"))
        nodes.extend(seq[start:end])
        if end < len(seq):
            nodes.append(Text("▶"))
        return self.row(tuple(nodes), size)
