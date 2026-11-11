"""The templates menu's icons, as drawing instructions (CASSim's own artwork, not TI's).

Each icon is a small picture of the template it inserts, with empty squares where the slots are, so
a fraction looks like a fraction and a 2 x 2 matrix like a matrix. Text labels such as `{2` or
`d/d` were hard to read. The shapes are plain data on a `WIDTH` by `HEIGHT` grid, so they can be
checked without Flet; `ui.py` turns them into canvas shapes at the screen's scale.
"""

from __future__ import annotations

from dataclasses import dataclass

WIDTH, HEIGHT = 26.0, 22.0  # one grid cell of a menu, in handheld pixels

Point = tuple[float, float]


@dataclass(frozen=True)
class Stroke:
    """A line through `points`."""

    points: tuple[Point, ...]


@dataclass(frozen=True)
class Slot:
    """An empty square, where the template takes an entry: top-left corner and side."""

    x: float
    y: float
    side: float


@dataclass(frozen=True)
class Word:
    """A few letters, centred on (`x`, `y`)."""

    x: float
    y: float
    text: str
    size: float = 9
    italic: bool = False


Shape = Stroke | Slot | Word
Icon = tuple[Shape, ...]


def _line(*numbers: float) -> Stroke:
    return Stroke(tuple(zip(numbers[::2], numbers[1::2], strict=True)))


def _integral(x: float, top: float, bottom: float) -> Stroke:
    """An integral sign: a tall, leaning stem with a hook at each end, `x` at its middle."""
    return _line(
        *(x + 3.2, top + 1.3, x + 2.4, top, x + 1.4, top + 0.5, x + 0.9, top + 2.5),
        *(x - 0.9, bottom - 2.5, x - 1.4, bottom - 0.5, x - 2.4, bottom, x - 3.2, bottom - 1.3),
    )


def _brace(x: float, top: float, bottom: float, *, opens: int = 1) -> Stroke:
    """A curly bracket whose point is at `x`; `opens` is 1 for `{` and -1 for `}`."""
    middle, quarter = (top + bottom) / 2, (bottom - top) / 4
    arm, tip = 2.5 * opens, 1.2 * opens
    return Stroke(
        (
            (x + arm + tip, top),
            (x + arm, top + 1),
            (x + arm, top + quarter),
            (x + arm, middle - 1.5),
            (x, middle),
            (x + arm, middle + 1.5),
            (x + arm, bottom - quarter),
            (x + arm, bottom - 1),
            (x + arm + tip, bottom),
        )
    )


def _bracket(x: float, top: float, bottom: float, *, opens: int = 1) -> Stroke:
    """A square bracket with its upright at `x`."""
    return _line(x + 2 * opens, top, x, top, x, bottom, x + 2 * opens, bottom)


def _matrix(rows: int, columns: int, side: float) -> Icon:
    """Square brackets around a grid of slots, centred in the cell."""
    gap = 1.5
    wide = columns * side + (columns - 1) * gap
    high = rows * side + (rows - 1) * gap
    left, top = (WIDTH - wide) / 2, (HEIGHT - high) / 2
    slots = tuple(
        Slot(left + c * (side + gap), top + r * (side + gap), side)
        for r in range(rows)
        for c in range(columns)
    )
    return (
        _bracket(left - 2.5, top - 2, top + high + 2),
        *slots,
        _bracket(left + wide + 2.5, top - 2, top + high + 2, opens=-1),
    )


def _rows(count: int, columns: int) -> Icon:
    """A left brace and `count` rows of slots (a piecewise function or a system)."""
    side = 4.5 if count == 2 else 3.6  # noqa: PLR2004 (two rows have room for larger slots)
    pitch = (HEIGHT - 3) / count
    shapes: list[Shape] = [_brace(4, 1.5, HEIGHT - 1.5)]
    for row in range(count):
        y = 1.5 + pitch * row + (pitch - side) / 2
        shapes.append(Slot(10, y, side))
        if columns > 1:
            shapes.append(Word(16.4, y + side - 1.5, ",", 6))
            shapes.append(Slot(18.5, y, side))
    return tuple(shapes)


_RADICAL = (2.0, 13.0, 4.0, 12.0, 7.0, 18.5, 10.0, 4.0, 23.0, 4.0)
_LIMITS = (Slot(5.2, 0.5, 3.6), Slot(5.2, 17.9, 3.6))  # above and below a Σ or Π
_BODY = Slot(16.5, 8, 6)


def _derivative(order: Shape | None, power: Shape | None) -> Icon:
    """`d/d□` in front of a slot; `order` and `power` are the marks of a higher derivative."""
    extra = tuple(shape for shape in (order, power) if shape is not None)
    return (
        Word(5.5, 5, "d", 9, italic=True),
        _line(1, 11, 16, 11),
        Word(4, 16.5, "d", 9, italic=True),
        Slot(7.8, 14, 4.5),
        *extra,
        Slot(19, 8, 6),
    )


ICONS: dict[str, Icon] = {
    "fraction": (Slot(10, 1.5, 6), _line(6.5, 11, 19.5, 11), Slot(10, 14.5, 6)),
    "power": (Slot(6, 8.5, 8), Slot(15.5, 2.5, 5)),
    "root": (_line(*_RADICAL), Slot(13, 8, 7)),
    "nth_root": (Slot(1.5, 2.5, 4.5), _line(*_RADICAL), Slot(13, 8, 7)),
    "exp": (Word(9, 12.5, "e", 14, italic=True), Slot(15.5, 2.5, 5)),
    "log": (Word(7, 9, "log", 9), Slot(13.2, 12.5, 4), Slot(19, 5, 6)),
    "piecewise2": _rows(2, 2),
    "piecewise_n": _rows(3, 2),
    "system2": _rows(2, 1),
    "system_n": _rows(3, 1),
    "abs": (_line(5.5, 2.5, 5.5, 19.5), Slot(9.5, 7.5, 7), _line(20.5, 2.5, 20.5, 19.5)),
    "dms": (
        Slot(1.5, 9.5, 5),
        Word(8.3, 8, "°", 9),
        Slot(10, 9.5, 5),
        Word(16.5, 8, "'", 9),
        Slot(18, 9.5, 5),
        Word(24.6, 8, '"', 9),
    ),
    "matrix22": _matrix(2, 2, 5),
    "matrix12": _matrix(1, 2, 5),
    "matrix21": _matrix(2, 1, 5),
    "matrix_mn": _matrix(3, 3, 3.4),
    "sum": (_line(11, 5.5, 3, 5.5, 7.5, 11, 3, 16.5, 11, 16.5), *_LIMITS, _BODY),
    "product": (
        _line(2.5, 5.5, 11.5, 5.5),
        _line(4.5, 5.5, 4.5, 16.5),
        _line(9.5, 5.5, 9.5, 16.5),
        *_LIMITS,
        _BODY,
    ),
    "derivative": _derivative(None, None),
    "derivative2": _derivative(Word(10, 3, "2", 6), Word(14.5, 13.5, "2", 6)),
    "derivative_n": _derivative(Slot(8.8, 0.8, 3), Slot(13, 12, 3)),
    "integral": (
        _integral(4.5, 2.5, 19.5),
        Slot(8.6, 0.6, 3.4),
        Slot(5.4, 17.9, 3.4),
        Slot(10.6, 8.5, 5),
        Word(18.2, 11, "d", 9, italic=True),
        Slot(21, 9, 4.5),
    ),
    "antiderivative": (
        _integral(4.5, 2.5, 19.5),
        Slot(9.5, 8.5, 5),
        Word(17.5, 11, "d", 9, italic=True),
        Slot(20.5, 9, 4.5),
    ),
    "limit": (
        Word(8.5, 6.5, "lim", 9),
        Slot(1.5, 14, 4),
        _line(7, 16, 11, 16),
        _line(9.5, 14.5, 11, 16, 9.5, 17.5),
        Slot(12.5, 14, 4),
        Slot(18.5, 4.5, 6),
    ),
    "subscript": (Slot(5, 4, 9), Slot(15.5, 12.5, 5.5)),
    "list": (
        _brace(1, 3, 19),
        Slot(5.5, 9, 3.6),
        Word(10.3, 11.5, ",", 8),
        Slot(11.6, 9, 3.6),
        Word(16.4, 11.5, ",", 8),
        Slot(17.7, 9, 3.6),
        _brace(25, 3, 19, opens=-1),
    ),
}
