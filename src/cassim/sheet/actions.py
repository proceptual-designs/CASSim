"""Actions that move cells: Fill, Sort, and Insert and Delete of cells, rows and columns.

Each works out the sheet's new contents and hands them to `Sheet.put` or `Sheet.restore`, which
recalculate and write the named columns to their lists. Behaviour from emulator check 6
(`docs/testing/emulator-sheet3-results.md` E6, E12, E18) and check run 2 (E12), and the corpus
cases `app.sheet.fill-down-fibonacci` and `app.sheet.sort-column`.
"""

from collections.abc import Callable
from dataclasses import replace

from cassim.core.compat import sympy_adapter as cas
from cassim.core.values import Expr, MatrixValue, Str, Value
from cassim.sheet import refs
from cassim.sheet.refs import COLUMNS, ROWS, Ref, Span
from cassim.sheet.sheet import (
    ColumnInfo,
    Constant,
    Content,
    DataLossError,
    Failed,
    Formula,
    Key,
    Notice,
    Sheet,
    SheetError,
)

INVALID_INPUT = "Cannot accept change: Invalid input."


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


def generate_sequence(  # noqa: PLR0913 (the dialog's fields)
    sheet: Sheet,
    column: int,
    formula: str,
    *,
    initial: str = "",
    first: int = 1,
    last: int = 255,
    step: int = 1,
    ceiling: str = "",
    confirm: bool = False,
) -> list[Notice]:
    """Menu > Data > Generate Sequence: the dialog's fields (Formula u(n)=, Initial Terms, n0,
    nMax 255, nStep 1, Ceiling Value) become the column formula `seqgen(...)` (check 6, E14;
    corpus `app.sheet.generate-sequence-recursive`). A column that holds data asks first."""
    if sheet.last_row(column) and not confirm:
        raise DataLossError
    terms = initial.strip() or "_"
    text = f"seqgen({formula},n,u,{{{first},{last}}},{{{terms}}},{step}"
    text += f",{ceiling})" if ceiling.strip() else ")"
    return sheet.set_column_formula(column, text)  # replaces what the column held


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


def move_column(sheet: Sheet, column: int, to: int) -> list[Notice]:
    """Actions > Move Column: the column, with its name and formula, goes to position `to` and
    the ones between close up (check 6, E12: B moved right one ends in C). References follow
    the cells they point at."""
    order = list(range(COLUMNS))
    order.insert(to, order.pop(column))  # order[new place] = old column
    place = {old: new for new, old in enumerate(order)}
    infos = [sheet.column(old) for old in order]
    return _rebuild(
        sheet,
        lambda key: (place[key[0]], key[1]),
        lambda ref: replace(ref, column=place[ref.column]),
        infos,
        lambda c: place[c],
    )


# ----- Stat Calculations ------------------------------------------------------------------------


def stat_calc(  # noqa: PLR0913 (the dialog's fields)
    sheet: Sheet,
    command: str,
    lists: list[str],
    *,
    column: int,
    freq: str = "1",
    category: str = "",
    include: str = "",
    save: str = "",
    choose: dict[str, str] | None = None,
    confirm: bool = False,
) -> list[Notice]:
    """Menu > Statistics > Stat Calculations (check 5, E15; run 4, S1 to S7): the results go in
    `column` (the labels, plain text) and the column after it (the values, from one column
    formula that runs the command, so they follow the data). One-Variable Statistics with
    several lists has a value column for each and no frequency or category fields (S5). A name
    that is also a cell asks Cell or Variable first, then a used column asks Data Loss (S7)."""
    if command.casefold() == "onevar" and len(lists) > 1:
        formulas = [f"{command} {name},1" for name in lists]
    else:
        args = [*lists, freq.strip() or "1", *([category, include] if category.strip() else [])]
        formulas = [
            f"{command} {','.join(args)}" + (f": CopyVar stat.RegEqn,{save}" if save else "")
        ]
    values = list(range(column + 1, column + 1 + len(formulas)))
    if values[-1] >= COLUMNS:
        raise SheetError("Syntax Error", INVALID_INPUT)
    choose = choose or {}
    for target, formula in zip(values, formulas, strict=True):
        sheet.check_formula(target, formula, choose)
    used = [c for c in (column, *values) if sheet.last_row(c) or sheet.column(c).formula]
    if used and not confirm:
        raise DataLossError
    notices: list[Notice] = []
    for target, formula in zip(values, formulas, strict=True):
        notices += sheet.set_column_formula(target, f"={formula}", choose=choose)
    results = sheet.variable("stat.results")
    labels: dict[Key, Content | None] = {key: None for key in sheet.contents() if key[0] == column}
    if isinstance(results, MatrixValue):
        for row, cells in enumerate(results.rows, start=1):
            if isinstance(cells[0], Str):
                labels[(column, row)] = Constant(cells[0])
    return notices + sheet.put(labels, confirm=True)


def stat_inference(
    sheet: Sheet,
    formula: str,
    *,
    column: int,
    choose: dict[str, str] | None = None,
    confirm: bool = False,
) -> list[Notice]:
    """Run a confidence interval or test into the selected two-column result area."""
    target = column + 1
    if not 0 <= column < COLUMNS - 1:
        raise SheetError("Syntax Error", INVALID_INPUT)
    choose = choose or {}
    sheet.check_formula(target, formula, choose)
    used = [c for c in (column, target) if sheet.last_row(c) or sheet.column(c).formula]
    if used and not confirm:
        raise DataLossError
    notices = sheet.set_column_formula(target, f"={formula}", choose=choose)
    results = sheet.variable("stat.results")
    labels: dict[Key, Content | None] = {key: None for key in sheet.contents() if key[0] == column}
    if isinstance(results, MatrixValue):
        for row, cells in enumerate(results.rows, start=1):
            if isinstance(cells[0], Str):
                labels[(column, row)] = Constant(cells[0])
    return notices + sheet.put(labels, confirm=True)
