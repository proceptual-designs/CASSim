"""Cell addresses and the references inside a spreadsheet formula.

A formula is TI syntax plus four spreadsheet forms the core parser does not read: a cell `b3`, a
fixed cell `$g$1` (either part may be fixed), a range `a1:c4` (`:` separates statements in the
entry line) and a whole column `a[]`. `scan` finds them, outside strings, and `rewrite` puts a
placeholder name in place of each one, so the rest is parsed as an ordinary expression. A name
written `'d1` is the variable d1, not the cell (the Conflict Detected choice, emulator check 6 E7).
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace

COLUMNS = 26  # a to z (emulator check 6, E24)
ROWS = 2500

_LETTERS = "abcdefghijklmnopqrstuvwxyz"
_CELL = r"(\$?)([a-zA-Z])(\$?)([0-9]+)"
# A reference is not part of a longer name, a `stat.` name or a call, and not after `'`.
_BEFORE = r"(?<![\w.'$])"
_AFTER = r"(?![\w(\[])"
_REFERENCE_RE = re.compile(
    rf"{_BEFORE}(?:{_CELL}(?:\s*:\s*{_CELL})?{_AFTER}|([a-zA-Z])\[\])|'([^\W\d]\w*)"
)
_STRING_RE = re.compile(r'"[^"]*"?')
_ADDRESS_RE = re.compile(r"\s*([a-zA-Z])([0-9]+)\s*")


@dataclass(frozen=True, slots=True)
class Ref:
    """A cell: column 0 to 25, row 1 to 2500. A fixed part (`$`) stays put when the formula is
    filled or copied."""

    column: int
    row: int
    fixed_column: bool = False
    fixed_row: bool = False

    @property
    def name(self) -> str:
        return f"{_LETTERS[self.column]}{self.row}"

    def __str__(self) -> str:
        column = ("$" if self.fixed_column else "") + _LETTERS[self.column]
        return f"{column}{'$' if self.fixed_row else ''}{self.row}"

    @property
    def valid(self) -> bool:
        return 0 <= self.column < COLUMNS and 1 <= self.row <= ROWS

    def key(self) -> tuple[int, int]:
        return self.column, self.row


@dataclass(frozen=True, slots=True)
class Span:
    """A rectangle of cells, `a1:c4`, in either order as typed."""

    start: Ref
    end: Ref

    def __str__(self) -> str:
        return f"{self.start}:{self.end}"

    @property
    def valid(self) -> bool:
        return self.start.valid and self.end.valid

    def cells(self) -> Iterator[tuple[int, int]]:
        """The cells row by row, as the handheld lists a range."""
        left, right = sorted((self.start.column, self.end.column))
        top, bottom = sorted((self.start.row, self.end.row))
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                yield column, row


@dataclass(frozen=True, slots=True)
class Column:
    """A whole column, `a[]`: its values from row 1 to its last filled row."""

    column: int

    def __str__(self) -> str:
        return f"{_LETTERS[self.column]}[]"

    @property
    def valid(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class Variable:
    """`'name`: a variable, even where the name is also a cell."""

    name: str

    def __str__(self) -> str:
        return f"'{self.name}"

    @property
    def valid(self) -> bool:
        return True


type Reference = Ref | Span | Column | Variable


@dataclass(frozen=True, slots=True)
class Found:
    reference: Reference
    start: int
    end: int


def column_index(letter: str) -> int:
    return _LETTERS.index(letter.lower())


def column_letter(column: int) -> str:
    return _LETTERS[column]


def address(text: str) -> Ref | None:
    """A typed cell address such as `h40` (Go To), or None."""
    match = _ADDRESS_RE.fullmatch(text)
    if not match:
        return None
    ref = Ref(column_index(match.group(1)), int(match.group(2)))
    return ref if ref.valid else None


def _ref(fixed_column: str, letter: str, fixed_row: str, row: str) -> Ref:
    return Ref(column_index(letter), int(row), bool(fixed_column), bool(fixed_row))


def _strings(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in _STRING_RE.finditer(text)]


def scan(text: str) -> list[Found]:
    """The references in a formula, in order, leaving out anything inside a string."""
    strings = _strings(text)
    found: list[Found] = []
    for match in _REFERENCE_RE.finditer(text):
        if any(start <= match.start() < end for start, end in strings):
            continue
        groups = match.groups()
        reference: Reference
        if groups[9] is not None:
            reference = Variable(groups[9])
        elif groups[8] is not None:
            reference = Column(column_index(groups[8]))
        elif groups[4] is not None:
            reference = Span(_ref(*groups[0:4]), _ref(*groups[4:8]))
        else:
            reference = _ref(*groups[0:4])
        found.append(Found(reference, match.start(), match.end()))
    return found


def rewrite(text: str, found: list[Found], replace_with: Callable[[Found], str]) -> str:
    """`text` with each found reference replaced by `replace_with(found)`."""
    parts: list[str] = []
    last = 0
    for item in found:
        parts.append(text[last : item.start])
        parts.append(replace_with(item))
        last = item.end
    parts.append(text[last:])
    return "".join(parts)


def _shift_ref(ref: Ref, columns: int, rows: int) -> Ref:
    return replace(
        ref,
        column=ref.column if ref.fixed_column else ref.column + columns,
        row=ref.row if ref.fixed_row else ref.row + rows,
    )


def shifted(text: str, columns: int, rows: int) -> str | None:
    """A formula copied `columns` right and `rows` down: relative parts move, `$` parts stay
    (emulator check 6, E6). None if a reference would leave the sheet."""
    found = scan(text)
    moved: dict[int, Reference] = {}
    for index, item in enumerate(found):
        reference = item.reference
        if isinstance(reference, Ref):
            reference = _shift_ref(reference, columns, rows)
        elif isinstance(reference, Span):
            reference = Span(
                _shift_ref(reference.start, columns, rows),
                _shift_ref(reference.end, columns, rows),
            )
        if not reference.valid:
            return None
        moved[index] = reference
    positions = {id(item): index for index, item in enumerate(found)}
    return rewrite(text, found, lambda item: str(moved[positions[id(item)]]))


def renamed(text: str, name: str, spelled: str) -> str:
    """A formula with each use of the name `name` (any case, not inside a string, not part of a
    longer name, not already written `'name`) written as `spelled` instead."""
    strings = _strings(text)
    pattern = re.compile(rf"(?<![\w.'$]){re.escape(name)}(?![\w(\[])", re.IGNORECASE)
    parts: list[str] = []
    last = 0
    for match in pattern.finditer(text):
        if any(start <= match.start() < end for start, end in strings):
            continue
        parts += [text[last : match.start()], spelled]
        last = match.end()
    return "".join([*parts, text[last:]])


def remapped(
    text: str, move: Callable[[Ref], Ref], move_column: Callable[[int], int] | None = None
) -> str:
    """A formula with every cell reference passed through `move`, and every whole column
    through `move_column`, as when a row or column is inserted or deleted (emulator check run 2,
    E12: `=c3` becomes `=c4` after a row above it)."""
    found = scan(text)

    def again(item: Found) -> str:
        reference = item.reference
        if isinstance(reference, Ref):
            return str(move(reference))
        if isinstance(reference, Span):
            return str(Span(move(reference.start), move(reference.end)))
        if isinstance(reference, Column) and move_column is not None:
            return str(Column(move_column(reference.column)))
        return str(reference)

    return rewrite(text, found, again)
