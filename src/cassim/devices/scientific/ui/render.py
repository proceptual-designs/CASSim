"""Natural display: draw a layout tree (`layout.py`) with Flet controls.

The LCD uses Roboto Mono, whose characters are all 0.6 em wide, so the width of any part can be
worked out without measuring. That is how a fraction bar is made as wide as the wider of its two
parts, and how a long entry is scrolled to keep the cursor on screen (◀ ▶ show there is more).
"""

from __future__ import annotations

import flet as ft

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


def width(seq: Seq, size: float) -> float:
    return sum(node_width(node, size) for node in seq)


def node_width(node: Node, size: float) -> float:  # noqa: PLR0911
    match node:
        case Text(text):
            return len(text) * ADVANCE * size
        case Frac(num, den):
            return max(width(num, size * FRACTION), width(den, size * FRACTION)) + 4
        case Sqrt(arg):
            return ADVANCE * size + width(arg, size) + 2
        case Root(index, arg):
            return width(index, size * SMALL) + ADVANCE * size + width(arg, size) + 2
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
            [self.node(node, size) for node in seq],
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
                            ft.Container(
                                width=bar, height=max(1.5, size * 0.08), bgcolor=self.color
                            ),
                            self.row(den, inner),
                        ],
                        spacing=1,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=1),
                )
            case Sqrt(arg):
                return ft.Row(
                    [_text("√", size, self.color), self._overline(arg, size)],
                    spacing=0,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                )
            case Root(index, arg):
                return ft.Row(
                    [
                        ft.Container(
                            self.row(index, size * SMALL),
                            padding=ft.Padding.only(bottom=size * 0.5),
                        ),
                        _text("√", size, self.color),
                        self._overline(arg, size),
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

    def _overline(self, arg: Seq, size: float) -> ft.Container:
        return ft.Container(
            self.row(arg, size),
            border=ft.Border(top=ft.BorderSide(max(1.0, size * 0.07), self.color)),
            padding=ft.Padding.only(left=1, right=1, top=1),
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
