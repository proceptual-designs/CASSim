"""The entry line drawn from Flet controls, so a click can place the cursor (decision 0019).

The history is still LaTeX (`ui.math`), but the entry cannot be: the Flutter canvas gives Python no
layout, so there is nothing to turn a click position into a place in the tree. Here every character,
every empty slot and every template is a control of its own. A character has two invisible click
halves (before it, after it); a template has the same behind its contents, so a click on a fraction
bar or a radical sign lands beside the template while a click in a slot lands in that slot. A click
in a row but past its last character puts the cursor at the row's end.

`target_*` helpers and `Hit` keep the mapping from controls to editor targets in plain data, so the
tests can click every region without a GUI.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import flet as ft

from cassim.app.theme import Theme
from cassim.device.editor import Editor, Kind, Row, Template, function_names

_SMALL = 0.6  # limits, indices and bounds are set smaller, as in TeX

Path = Sequence[tuple[int, int]]
type Click = Callable[[Path, int], None]  # a click at (row path, position in that row)
type Chrome = Callable[[ft.Control], ft.Control]

SELECTION = "#7fb2e8"
HIT = "#01ffffff"  # all but invisible, but a coloured box takes clicks where nothing is drawn
_SHOWN = {"*": "·", "-": "−", "ⅇ": "ⅇ", "ᴇ": "ᴇ", "/": "/", " ": " "}
# The fonts flutter_math draws the history with, so the entry matches it: letters in KaTeX_Math
# (italic by design), everything else in KaTeX_Main.
_MATH_FONT = "packages/flutter_math_fork/KaTeX_Math"
_MAIN_FONT = "packages/flutter_math_fork/KaTeX_Main"
_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZπ")
_BINARY = frozenset("+-*=<>≤≥≠")  # set with a little space either side, as TeX does


class EntryLine:
    """Builds the control for one editor state; `click` is told where the user clicked."""

    def __init__(
        self,
        theme: Theme,
        size: float,
        click: Click,
        is_function: Callable[[str], bool] = lambda _: False,
    ) -> None:
        self.theme = theme
        self.size = size
        self.click = click
        self.is_function = is_function

    def build(self, editor: Editor) -> ft.Control:
        """The whole line. A click past the end of it puts the cursor at the end of the entry."""
        self._editor = editor
        row = self._row(editor.root, [])
        return ft.GestureDetector(
            ft.Container(
                row,
                padding=ft.Padding.symmetric(vertical=2),
                alignment=ft.Alignment.CENTER_LEFT,
                bgcolor=HIT,
            ),
            on_tap=lambda _: self.click([], len(editor.root)),
        )

    # ---- rows -------------------------------------------------------------------------------

    def _row(
        self,
        row: Row,
        here: list[tuple[int, int]],
        pad: ft.Padding | None = None,
        *,
        center: bool = False,
    ) -> ft.Control:
        """A row of nodes with the cursor bar and the selection; `here` is the row's path."""
        editor = self._editor
        on_cursor = editor.path == here
        low, high = editor.span if on_cursor else (0, 0)
        names = function_names(row, self.is_function)
        parts: list[ft.Control] = []
        if not row:
            parts.append(self._cursor() if on_cursor else self._empty_slot())
        for index, node in enumerate(row):
            if on_cursor and editor.pos == index and low == high:
                parts.append(self._cursor())
            chosen = low <= index < high
            body = (
                self._template(node, here, index)
                if isinstance(node, Template)
                else self._char(node, here, index, bold=index in names)
            )
            parts.append(self._highlight(body) if chosen else body)
        if row and on_cursor and low == high and editor.pos == len(row):
            parts.append(self._cursor())
        if row and on_cursor and low != high:
            parts.insert(self._bar_place(low, high, editor.pos), self._cursor(selected=True))
        return ft.GestureDetector(
            ft.Container(
                ft.Row(
                    parts,
                    spacing=0,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=HIT,
                padding=pad,
                alignment=ft.Alignment.CENTER if center else None,
            ),
            on_tap=lambda _: self.click(here, len(row)),
        )

    @staticmethod
    def _bar_place(low: int, high: int, pos: int) -> int:
        # parts are one per node (plus the cursor bar inserted here), so the bar goes before the
        # first selected node or after the last one
        return low if pos == low else high

    def _highlight(self, control: ft.Control) -> ft.Control:
        return ft.Container(control, bgcolor=SELECTION)

    def _cursor(self, *, selected: bool = False) -> ft.Control:
        return ft.Container(
            width=2,
            height=self.size * 1.15,
            bgcolor="#0b3d78" if selected else self.theme.accent,
        )

    def _empty_slot(self) -> ft.Control:
        return ft.Container(
            width=self.size * 0.55,
            height=self.size * 0.75,
            border=ft.Border.all(1, self.theme.screen_text),
            margin=ft.Margin.symmetric(horizontal=1),
        )

    # ---- characters -------------------------------------------------------------------------

    def _char(
        self, char: str, here: list[tuple[int, int]], index: int, *, bold: bool
    ) -> ft.Control:
        text: ft.Control = ft.Text(
            _SHOWN.get(char, char),
            size=self.size,
            color=self.theme.screen_text,
            weight=ft.FontWeight.BOLD if bold else None,
            font_family=_MATH_FONT if char in _LETTERS and not bold else _MAIN_FONT,
            no_wrap=True,
        )
        if char in _BINARY:
            text = ft.Container(text, padding=ft.Padding.symmetric(horizontal=self.size * 0.2))
        return ft.Stack([text, self._halves(here, index)])

    def _halves(self, here: list[tuple[int, int]], index: int) -> ft.Control:
        """Two click zones filling the control they sit in: before the node and after it."""
        zones: list[ft.Control] = [
            ft.GestureDetector(
                ft.Container(expand=True, bgcolor=HIT),
                expand=True,
                on_tap=lambda _, at=at: self.click(here, at),
            )
            for at in (index, index + 1)
        ]
        return ft.Row(zones, spacing=0, left=0, right=0, top=0, bottom=0)

    # ---- templates --------------------------------------------------------------------------

    def _template(self, node: Template, here: list[tuple[int, int]], index: int) -> ft.Control:
        if node.kind in _DRAWN:
            body = _DRAWN[node.kind](_Parts(self, node, here, index))
            return ft.Stack([self._halves(here, index), body])
        size = self.size
        if node.kind is Kind.POWER:
            self.size = size * 0.7  # an exponent is set smaller
        # a slot's own click area takes in what is around its text: a matrix cell's padding and the
        # width a fraction gives a short numerator
        pad = ft.Padding.symmetric(horizontal=6, vertical=1) if node.kind is Kind.MATRIX else None
        centred = node.kind in (Kind.FRACTION, Kind.MATRIX)
        slots = [
            self._row(slot, [*here, (index, s)], pad, center=centred)
            for s, slot in enumerate(node.slots)
        ]
        self.size = size

        def chrome(piece: ft.Control) -> ft.Control:
            # drawn parts that are not slots (bar, radical, brackets) take clicks for the template
            return ft.Stack([piece, self._halves(here, index)])

        if node.kind is Kind.FRACTION:
            body = self._fraction(slots, chrome)
        elif node.kind is Kind.POWER:
            body = self._power(slots[0])
        elif node.kind is Kind.ROOT:
            body = self._root(slots[0], chrome)
        else:
            body = self._matrix(slots, node.cols, chrome)
        # The zones also sit behind the contents, for the gaps the chrome leaves; a slot's own zones
        # are on top, so anything inside a slot is that slot's.
        return ft.Stack([self._halves(here, index), body])

    def _fraction(self, slots: list[ft.Control], chrome: Chrome) -> ft.Control:
        bar = chrome(
            ft.Container(
                ft.Container(height=1.5, bgcolor=self.theme.screen_text),
                padding=ft.Padding.symmetric(vertical=3),
            )
        )
        return ft.Container(
            ft.Column(
                [
                    slots[0],
                    bar,
                    slots[1],
                ],
                spacing=1,
                tight=True,
                intrinsic_width=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.Padding.symmetric(horizontal=2),
        )

    def _power(self, exponent: ft.Control) -> ft.Control:
        # raised by a spacer below the exponent; the base character is centred beside it
        return ft.Column(
            [exponent, ft.Container(height=self.size * 0.9)],
            spacing=0,
            tight=True,
        )

    def _root(self, radicand: ft.Control, chrome: Chrome) -> ft.Control:
        sign = chrome(
            ft.Text(
                "√", size=self.size * 1.15, color=self.theme.screen_text, font_family=_MAIN_FONT
            )
        )
        overline = chrome(
            ft.Container(
                ft.Container(height=1.5, bgcolor=self.theme.screen_text),
                padding=ft.Padding.only(bottom=1),
            )
        )
        return ft.Row(
            [
                sign,
                ft.Container(
                    ft.Column(
                        [overline, radicand],
                        spacing=0,
                        tight=True,
                        intrinsic_width=True,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=ft.Padding.symmetric(horizontal=2),
                ),
            ],
            spacing=0,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _matrix(self, slots: list[ft.Control], cols: int, chrome: Chrome) -> ft.Control:
        line = ft.BorderSide(1.5, self.theme.screen_text)

        def bracket(*, left: bool) -> ft.Control:
            side = (
                ft.Border(left=line, top=line, bottom=line)
                if left
                else ft.Border(right=line, top=line, bottom=line)
            )
            return chrome(ft.Container(width=5, border=side))

        columns = [
            ft.Column(
                [cell for cell in slots[c::cols]],
                spacing=0,
                tight=True,
                intrinsic_width=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
            for c in range(cols)
        ]
        return ft.Row(
            [bracket(left=True), *columns, bracket(left=False)],
            spacing=0,
            tight=True,
            intrinsic_height=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )


class _Parts:
    """What a template drawing is made of: its slots at a size, and drawn signs that click to the
    template as a whole (beside it, as for a fraction bar)."""

    def __init__(
        self, line: EntryLine, node: Template, here: list[tuple[int, int]], index: int
    ) -> None:
        self.line, self.node, self.here, self.index = line, node, here, index

    @property
    def size(self) -> float:
        return self.line.size

    def slot(self, number: int, scale: float = 1.0, *, center: bool = False) -> ft.Control:
        line = self.line
        size = line.size
        line.size = size * scale
        try:
            return line._row(
                self.node.slots[number], [*self.here, (self.index, number)], center=center
            )
        finally:
            line.size = size

    def sign(self, text: str, scale: float = 1.0) -> ft.Control:
        line = self.line
        drawn = ft.Text(
            text,
            size=line.size * scale,
            color=line.theme.screen_text,
            font_family=_MAIN_FONT,
            no_wrap=True,
        )
        return ft.Stack([drawn, line._halves(self.here, self.index)])

    def bar(self, *, across: bool) -> ft.Control:
        """A fraction-style rule (`across`) or an absolute-value bar."""
        colour = self.line.theme.screen_text
        rule = (
            ft.Container(
                ft.Container(height=1.5, bgcolor=colour), padding=ft.Padding.symmetric(vertical=2)
            )
            if across
            else ft.Container(width=1.5, bgcolor=colour, margin=ft.Margin.symmetric(horizontal=2))
        )
        return ft.Stack([rule, self.line._halves(self.here, self.index)])

    def gap(self, height: float) -> ft.Control:
        return ft.Container(height=self.size * height)


def _row(*parts: ft.Control, stretch: bool = False) -> ft.Control:
    return ft.Row(
        list(parts),
        spacing=0,
        tight=True,
        intrinsic_height=stretch,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH
        if stretch
        else ft.CrossAxisAlignment.CENTER,
    )


def _column(*parts: ft.Control) -> ft.Control:
    return ft.Column(
        list(parts),
        spacing=0,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _nth_root(p: _Parts) -> ft.Control:
    index = _column(p.slot(0, _SMALL), p.gap(0.55))
    radicand = p.line._root(p.slot(1), lambda piece: piece)
    return _row(index, radicand)


def _log(p: _Parts) -> ft.Control:
    base = _column(p.gap(0.55), p.slot(0, _SMALL))
    return _row(p.sign("log"), base, p.sign("("), p.slot(1), p.sign(")"))


def _abs(p: _Parts) -> ft.Control:
    return _row(p.bar(across=False), p.slot(0), p.bar(across=False), stretch=True)


def _grid(p: _Parts, joint: str) -> ft.Control:
    cols = p.node.cols
    rows = len(p.node.slots) // cols
    lines = []
    for r in range(rows):
        cells: list[ft.Control] = []
        for c in range(cols):
            if c:
                cells.append(p.sign(joint))
            cells.append(p.slot(r * cols + c))
        lines.append(_row(*cells))
    body = ft.Column(lines, spacing=2, tight=True)
    return _row(p.sign("{", 1.1 * rows), body)


def _derivative(p: _Parts, *, second: bool) -> ft.Control:
    power = "²" if second else ""
    top = p.sign("d" + power, 0.8)
    bottom = _row(p.sign("d", 0.8), p.slot(0, 0.8), *([p.sign("²", 0.6)] if second else []))
    fraction = ft.Column(
        [top, p.bar(across=True), bottom],
        spacing=0,
        tight=True,
        intrinsic_width=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return _row(fraction, p.sign("("), p.slot(1), p.sign(")"))


def _integral(p: _Parts) -> ft.Control:
    sign = _column(p.slot(1, _SMALL), p.sign("∫", 1.5), p.slot(0, _SMALL))
    return _row(sign, p.slot(2), p.sign(" d"), p.slot(3))


def _antiderivative(p: _Parts) -> ft.Control:
    return _row(p.sign("∫", 1.5), p.slot(0), p.sign(" d"), p.slot(1))


def _big_operator(p: _Parts, symbol: str) -> ft.Control:
    below = _row(p.slot(0, _SMALL), p.sign("=", _SMALL), p.slot(1, _SMALL))
    return _row(_column(p.slot(2, _SMALL), p.sign(symbol, 1.4), below), p.slot(3))


def _limit(p: _Parts) -> ft.Control:
    below = _row(p.slot(0, _SMALL), p.sign("→", _SMALL), p.slot(1, _SMALL))
    return _row(_column(p.sign("lim"), below), p.sign(" "), p.slot(2))


# How each function-like template is drawn (the older kinds are drawn by `EntryLine` itself).
_DRAWN: dict[Kind, Callable[[_Parts], ft.Control]] = {
    Kind.NTH_ROOT: _nth_root,
    Kind.LOG: _log,
    Kind.ABS: _abs,
    Kind.PIECEWISE: lambda p: _grid(p, ", "),
    Kind.SYSTEM: lambda p: _grid(p, ""),
    Kind.DERIVATIVE: lambda p: _derivative(p, second=False),
    Kind.DERIVATIVE2: lambda p: _derivative(p, second=True),
    Kind.INTEGRAL: _integral,
    Kind.ANTIDERIVATIVE: _antiderivative,
    Kind.SUM: lambda p: _big_operator(p, "Σ"),
    Kind.PRODUCT: lambda p: _big_operator(p, "Π"),
    Kind.LIMIT: _limit,
}
