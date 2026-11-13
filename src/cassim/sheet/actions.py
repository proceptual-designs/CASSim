"""Actions that move cells: Fill, Sort, and Insert and Delete of cells, rows and columns.

Each works out the sheet's new contents and hands them to `Sheet.put` or `Sheet.restore`, which
recalculate and write the named columns to their lists. Behaviour from emulator check 6
(`docs/testing/emulator-sheet3-results.md` E6, E12, E18) and check run 2 (E12), and the corpus
cases `app.sheet.fill-down-fibonacci` and `app.sheet.sort-column`.
"""

from collections.abc import Callable
from dataclasses import replace

from cassim.core.compat import sympy_adapter as cas
from cassim.core.values import Expr, Str, Value
from cassim.sheet import refs
from cassim.sheet.refs import COLUMNS, ROWS, Ref, Span
from cassim.sheet.sheet import (
    ColumnInfo,
    Constant,
    Content,
    Failed,
    Formula,
    Key,
    Notice,
    Sheet,
    SheetError,
)

DATA_LOSS = "Data Loss"
DATA_LOSS_MESSAGE = (
    "This operation may overwrite data in the current column(s). Do you wish to proceed?"
)


class DataLossError(SheetError):
    """The action needs an OK first: "Data Loss" with OK and Cancel. Call again with
    `confirm=True` after OK."""

    def __init__(self) -> None:
        super().__init__(DATA_LOSS, DATA_LOSS_MESSAGE)


def _bounds(span: Span) -> tuple[int, int, int, int]:
    left, right = sorted((span.start.column, span.end.column))
    top, bottom = sorted((span.start.row, span.end.row))
    return left, right, top, bottom


# ----- Fill ---------------------------------------------------------------------------------------


def fill(sheet: Sheet, source: Span, target: Span) -> list[Notice]:
    """Fill `target` from `source`, repeating it: formulas move with the cell, `$` parts stay
    (check 6, E6; corpus `app.sheet.fill-down-fibonacci`, A3 filled to A3:A20). A formula that
    would point off the sheet leaves its cell blank (a guess)."""
    left, right, top, bottom = _bounds(source)
    width, height = right - left + 1, bottom - top + 1
    target_left, target_right, target_top, target_bottom = _bounds(target)
    changes: dict[Key, Content | None] = {}
    for column in range(target_left, target_right + 1):
        for row in range(target_top, target_bottom + 1):
            from_column = left + (column - target_left) % width
            from_row = top + (row - target_top) % height
            content = sheet.content(from_column, from_row)
            if isinstance(content, Formula):
                moved = refs.shifted(content.text, column - from_column, row - from_row)
                content = Formula(moved) if moved is not None else None
            changes[(column, row)] = content
    return sheet.put(changes)


# ----- Sort ---------------------------------------------------------------------------------------


def _sort_key(value: Value | Failed | None) -> tuple[int, float, str]:
    """Numbers in order, then text in order, then anything else by its text."""
    if isinstance(value, Expr):
        number = cas.number_value(value.raw)
        if number is not None and not number.imag:
            return 0, number.real, ""
    if isinstance(value, Str):
        return 1, 0.0, value.value
    return 2, 0.0, repr(value)


def sort(
    sheet: Sheet, span: Span, by: int, *, descending: bool = False, confirm: bool = False
) -> list[Notice]:
    """Menu > Actions > Sort: the rows of `span` move together, ordered by column `by`
    (check 6, E18; corpus `app.sheet.sort-column`). Blank cells go last. A column formula in the
    range asks first (Data Loss), and its values stay as constants; so do cell formulas."""
    left, right, top, bottom = _bounds(span)
    if not left <= by <= right:
        raise SheetError("Syntax Error", "Cannot accept change: Invalid input.")
    columns = range(left, right + 1)
    if any(sheet.column(column).formula is not None for column in columns):
        if not confirm:
            raise DataLossError
        for column in columns:
            if sheet.column(column).formula is not None:
                sheet.set_column_formula(column, "")
    rows = list(range(top, bottom + 1))
    filled = [row for row in rows if sheet.value(by, row) is not None]
    blank = [row for row in rows if sheet.value(by, row) is None]
    filled.sort(key=lambda row: _sort_key(sheet.value(by, row)), reverse=descending)
    changes: dict[Key, Content | None] = {}
    for new_row, old_row in zip(rows, filled + blank, strict=True):
        for column in columns:
            changes[(column, new_row)] = _kept(sheet, column, old_row)
    return sheet.put(changes)


def _kept(sheet: Sheet, column: int, row: int) -> Content | None:
    """A cell's content to move: a formula is kept as its value (check 6, E18: `=6`)."""
    content = sheet.content(column, row)
    if isinstance(content, Formula):
        value = sheet.value(column, row)
        return None if value is None or isinstance(value, Failed) else Constant(value)
    return content


# ----- Insert and delete --------------------------------------------------------------------------


def _rebuild(
    sheet: Sheet,
    where: Callable[[Key], Key | None],
    move: Callable[[Ref], Ref],
    columns: list[ColumnInfo] | None = None,
    move_column: Callable[[int], int] | None = None,
) -> list[Notice]:
    """Move every cell by `where` (None drops it) and every reference by `move`, then compute
    the sheet again. A reference to a deleted cell keeps its address (a guess: not captured)."""
    contents: dict[Key, Content] = {}
    for key, content in sheet.contents().items():
        new = where(key)
        if new is None:
            continue
        contents[new] = (
            Formula(refs.remapped(content.text, move, move_column))
            if isinstance(content, Formula)
            else content
        )
    infos = columns if columns is not None else [sheet.column(c) for c in range(COLUMNS)]
    infos = [
        replace(info, formula=refs.remapped(info.formula, move, move_column))
        if info.formula is not None
        else info
        for info in infos
    ]
    return sheet.restore(contents, infos)


def _shift_ref(ref: Ref, *, column: int | None = None, row: int, by: int) -> Ref:
    """`ref` moved `by` rows if it is at or below `row` (and in `column`, when given)."""
    if ref.row >= row and (column is None or ref.column == column):
        return replace(ref, row=min(max(ref.row + by, 1), ROWS))
    return ref


def insert_row(sheet: Sheet, row: int) -> list[Notice]:
    """Insert Row: a blank row across the sheet; linked lists get `_` there (check run 2, E12)."""
    return _rebuild(
        sheet,
        lambda key: (key[0], key[1] + 1) if key[1] >= row else key,
        lambda ref: _shift_ref(ref, row=row, by=1),
    )


def delete_row(sheet: Sheet, row: int) -> list[Notice]:
    """Delete Row: the rows below move up (check 6, E12; check run 2, E12)."""
    return _rebuild(
        sheet,
        lambda key: None if key[1] == row else (key[0], key[1] - 1) if key[1] > row else key,
        lambda ref: _shift_ref(ref, row=row + 1, by=-1),
    )


def insert_cell(sheet: Sheet, column: int, row: int) -> list[Notice]:
    """Insert Cell: the cells below in the column move down one (check 6, E12)."""
    return _rebuild(
        sheet,
        lambda key: (key[0], key[1] + 1) if key[0] == column and key[1] >= row else key,
        lambda ref: _shift_ref(ref, column=column, row=row, by=1),
    )


def delete_cell(sheet: Sheet, column: int, row: int) -> list[Notice]:
    """Delete Cell: the cells below in the column move up one (check 6, E12)."""

    def where(key: Key) -> Key | None:
        if key[0] != column or key[1] < row:
            return key
        return None if key[1] == row else (key[0], key[1] - 1)

    return _rebuild(sheet, where, lambda ref: _shift_ref(ref, column=column, row=row + 1, by=-1))


def _moved_column(column: int, at: int, by: int) -> int:
    return min(max(column + by, 0), COLUMNS - 1) if column >= at else column


def insert_column(sheet: Sheet, column: int) -> list[Notice]:
    """Insert Column: a blank column; the columns to its right, names and all, move right
    (check 6, E12). The last column falls off the sheet."""
    infos = [sheet.column(c) for c in range(COLUMNS)]
    infos = [*infos[:column], ColumnInfo(), *infos[column : COLUMNS - 1]]
    return _rebuild(
        sheet,
        lambda key: (key[0] + 1, key[1]) if key[0] >= column else key,
        lambda ref: replace(ref, column=_moved_column(ref.column, column, 1)),
        infos,
        lambda c: _moved_column(c, column, 1),
    )


def delete_column(sheet: Sheet, column: int) -> list[Notice]:
    """Delete Column: the columns to its right move left (check 6, E12). Its list, if it had
    one, is left as a variable (a guess, as for renaming a column in check run 2, G)."""
    infos = [sheet.column(c) for c in range(COLUMNS) if c != column] + [ColumnInfo()]

    def where(key: Key) -> Key | None:
        if key[0] == column:
            return None
        return (key[0] - 1, key[1]) if key[0] > column else key

    return _rebuild(
        sheet,
        where,
        lambda ref: replace(ref, column=_moved_column(ref.column, column + 1, -1)),
        infos,
        lambda c: _moved_column(c, column + 1, -1),
    )
