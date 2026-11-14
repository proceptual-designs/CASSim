"""The Lists & Spreadsheet grid as a `Scene` (slice 3b, FR-GRAPH-006), without Flet.

Spike A (decision 0031): one multi-line label per column draws the cells (two for a column,
since numbers sit on the right and text on the left), and the cursor and selection are on their
own layer, so a cursor move sends no text. The view keeps each layer's canvas and rebuilds only
the layers that changed.

Sizes are in the handheld's pixels times `scale`, as the rest of the screen. `fit` says how many
rows and columns a view of a given size shows, and `cell_at` turns a tap into a cell.
"""

from __future__ import annotations

from dataclasses import dataclass

from cassim.device.editor import MARK
from cassim.devices.nspire.pages.spreadsheet import (
    FORMULA_ROW,
    NAME_ROW,
    SheetScreen,
    Spreadsheet,
)
from cassim.graph.scene import Align, Box, Fill, Label, Layer, Scene, Segments, Stroke, column_label
from cassim.sheet.refs import COLUMNS

ROW_LABELS = 24  # the row numbers' column
HEAD = 16  # the column letter and name
FORMULA = 15  # the formula row ("=")
ROW = 17  # a data row
FONT = 11
CHAR = 0.62  # a character's width, as a share of the font size (for cutting long text)
PAD = 3
CARET = "|"
SLIVER = 10  # how much of the column off to the left shows, when there is one


@dataclass(frozen=True)
class Grid:
    """Where things are, at a scale."""

    scale: float

    def px(self, size: float) -> float:
        return size * self.scale

    @property
    def top(self) -> float:
        """Where the data rows start."""
        return self.px(HEAD + FORMULA)


def fit(width: float, height: float, sheet: Spreadsheet, scale: float) -> tuple[int, int]:
    """The whole data rows and columns a view `width` by `height` shows, from the sheet's left
    column (one more of each shows in part)."""
    grid = Grid(scale)
    rows = max(int((height - grid.top) // grid.px(ROW)), 1)
    room = width - grid.px(ROW_LABELS) - (grid.px(SLIVER) if sheet.left > 0 else 0)
    columns = 0
    for column in range(sheet.left, COLUMNS):
        room -= grid.px(sheet.width(column))
        if room < 0 and columns:
            break
        columns += 1
    return rows, max(columns, 1)


def _clip(text: str, width: float, size: float) -> str:
    """Text cut to fit a cell, with `...` where it was cut (check 6, E13: `1234...`)."""
    room = int((width - 2 * PAD) / (size * CHAR))
    if len(text) <= room:
        return text
    return text[: max(room - 3, 1)] + "..."


def _columns_x(screen: SheetScreen, grid: Grid) -> list[tuple[int, float, float]]:
    """Each visible column's index, left edge and width; the sliver of the column off to the
    left comes first, mostly hidden behind the row numbers."""
    x = grid.px(ROW_LABELS)
    found = []
    if screen.sliver is not None:
        x += grid.px(SLIVER)
        found.append((screen.sliver, grid.px(ROW_LABELS), grid.px(SLIVER)))
    for column, _, _, _, width in screen.columns:
        found.append((column, x, grid.px(width)))
        x += grid.px(width)
    return found


def sheet_scene(screen: SheetScreen, scale: float, width: float, height: float) -> Scene:
    grid = Grid(scale)
    xs = _columns_x(screen, grid)
    shown = xs[1:] if screen.sliver is not None else xs  # the sliver has lines but no text
    return Scene(
        width,
        height,
        (
            _lines(screen, grid, xs, width, height),
            _heads(screen, grid, shown),
            _cells(screen, grid, shown),
            _cursor(screen, grid, xs),
        ),
    )


def _lines(
    screen: SheetScreen, grid: Grid, xs: list[tuple[int, float, float]], width: float, height: float
) -> Layer:
    right = min(xs[-1][1] + xs[-1][2] if xs else width, width)
    bottom = min(height, grid.top + grid.px(ROW) * len(screen.rows))
    head = (
        (0.0, 0.0),
        (right, 0.0),
        (right, grid.top),
        (0.0, grid.top),
    )
    labels = (
        (0.0, grid.top),
        (grid.px(ROW_LABELS), grid.top),
        (grid.px(ROW_LABELS), bottom),
        (0.0, bottom),
    )
    points: list[tuple[float, float]] = []
    for _, x, _ in xs:
        points += [(x, 0.0), (x, bottom)]
    points += [(right, 0.0), (right, bottom)]
    for n in range(len(screen.rows) + 1):
        y = grid.top + grid.px(ROW) * n
        points += [(0.0, y), (right, y)]
    points += [(0.0, grid.px(HEAD)), (right, grid.px(HEAD))]
    return Layer(
        "grid",
        (
            Fill(head, "header", 1.0),
            Fill(labels, "header", 1.0),
            Segments(tuple(points), Stroke("grid", 1.0)),
        ),
    )


def _heads(screen: SheetScreen, grid: Grid, xs: list[tuple[int, float, float]]) -> Layer:
    size = grid.px(FONT)
    shapes: list[Label] = []
    for (_, x, w), (_, letter, name, formula, _) in zip(xs, screen.columns, strict=True):
        head = f"{letter} {name}" if name else letter
        shapes.append(Label(x + w / 2, grid.px(2), _clip(head, w, size), size, "ink", Align.CENTRE))
        if formula:
            shown = _clip(f"={formula}", w, size)
            shapes.append(Label(x + grid.px(PAD), grid.px(HEAD + 1), shown, size, "axis"))
    numbers = column_label(
        (grid.px(ROW_LABELS - PAD), grid.top + grid.px(2)),
        [str(row) for row in screen.rows],
        grid.px(ROW),
        align=Align.RIGHT,
    )
    shapes.append(
        Label(numbers.x, numbers.y, numbers.text, size, "axis", Align.RIGHT, numbers.line_height)
    )
    return Layer("heads", tuple(shapes))


def _cells(screen: SheetScreen, grid: Grid, xs: list[tuple[int, float, float]]) -> Layer:
    """Two labels a column: the numbers on the right, the rest on the left (spike A)."""
    size = grid.px(FONT)
    shapes: list[Label] = []
    y = grid.top + grid.px(2)
    for column, x, w in xs:
        lefts, rights = [], []
        for row in screen.rows:
            text, right = screen.cells.get((column, row), ("", False))
            text = _clip(text, w, size)
            lefts.append("" if right else text)
            rights.append(text if right else "")
        for texts, align, at in (
            (lefts, Align.LEFT, x + grid.px(PAD)),
            (rights, Align.RIGHT, x + w - grid.px(PAD)),
        ):
            if any(texts):
                label = column_label((at, y), texts, grid.px(ROW), align=align)
                shapes.append(
                    Label(label.x, label.y, label.text, size, "ink", align, label.line_height)
                )
    return Layer("cells", tuple(shapes))


def _cell_box(
    key: tuple[int, int], screen: SheetScreen, grid: Grid, xs: list[tuple[int, float, float]]
) -> tuple[float, float, float, float] | None:
    """(x, y, width, height) of a cell on show, or None."""
    column, row = key
    place = next(((x, w) for c, x, w in xs if c == column), None)
    if place is None:
        return None
    x, w = place
    if row == NAME_ROW:
        return x, 0.0, w, grid.px(HEAD)
    if row == FORMULA_ROW:
        return x, grid.px(HEAD), w, grid.px(FORMULA)
    if row not in screen.rows:
        return None
    return x, grid.top + grid.px(ROW) * screen.rows.index(row), w, grid.px(ROW)


def _rect(left: float, top: float, width: float, height: float) -> tuple[tuple[float, float], ...]:
    return ((left, top), (left + width, top), (left + width, top + height), (left, top + height))


def _block(
    span: tuple[int, int, int, int],
    screen: SheetScreen,
    grid: Grid,
    xs: list[tuple[int, float, float]],
) -> tuple[float, float, float, float] | None:
    """The part of a block on show, as (x, y, width, height)."""
    left, top, right, bottom = span
    shown = [(c, x, w) for c, x, w in xs if left <= c <= right]
    rows = [n for n, row in enumerate(screen.rows) if top <= row <= bottom]
    if not shown or not rows:
        return None
    x = shown[0][1]
    y = grid.top + grid.px(ROW) * rows[0]
    return x, y, shown[-1][1] + shown[-1][2] - x, grid.px(ROW) * len(rows)


def _cursor(screen: SheetScreen, grid: Grid, xs: list[tuple[int, float, float]]) -> Layer:
    shapes: list[Fill | Box | Label] = []
    if screen.selection is not None:
        block = _block(screen.selection, screen, grid, xs)
        if block is not None:
            shapes.append(Fill(_rect(*block), "selection", 0.45))
    if screen.marker is not None:
        block = _block(screen.marker, screen, grid, xs)
        if block is not None:
            shapes.append(Box(*block, Stroke("cursor", 1.5, dashed=True)))
    cell = _cell_box(screen.cursor, screen, grid, xs)
    if cell is not None:
        if screen.editing is not None:
            x, y, w, h = cell
            shapes.append(Fill(_rect(x, y, w, h), "edit", 1.0))
            text = screen.editing.replace(MARK, CARET)
            size = grid.px(FONT)
            room = int((w - 2 * grid.px(PAD)) / (size * CHAR))
            caret = text.index(CARET)
            start = max(0, caret - room + 1)  # keep the caret in view as the text grows
            shapes.append(
                Label(x + grid.px(PAD), y + grid.px(2), text[start : start + room], size, "ink")
            )
        shapes.append(Box(*cell, Stroke("cursor", 2.0)))
    return Layer("cursor", tuple(shapes))


def cell_at(x: float, y: float, screen: SheetScreen, scale: float) -> tuple[int, int] | None:
    """The cell under a tap: (column, row) with row -1 the name cell and 0 the formula cell;
    a tap on a row number is (-1, row); None outside the grid."""
    grid = Grid(scale)
    if y < grid.px(HEAD):
        row = NAME_ROW
    elif y < grid.top:
        row = FORMULA_ROW
    else:
        index = int((y - grid.top) // grid.px(ROW))
        if index >= len(screen.rows):
            return None
        row = screen.rows[index]
    if x < grid.px(ROW_LABELS):
        return (-1, row) if row >= 1 else None
    for column, left, width in _columns_x(screen, grid):
        if left <= x < left + width:
            return column, row
    return None
