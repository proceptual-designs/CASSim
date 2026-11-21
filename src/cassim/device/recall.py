"""What a picked result brings down: the full-precision value of what is selected (FR-CALC-004).

A result row shows its digits at the document's Float setting (`0.333`), and the cursor moves
through those digits. What Enter brings down, or copy takes, is the value at full precision
(`0.33333333333333`), as on the device. The shown tree and the full tree have the same shape:
only the length of each number differs. So the selection is carried across unit by unit, a
unit being a template, a character, or a whole number; a selection edge inside a number takes in
the whole number.
"""

from __future__ import annotations

import copy

from cassim.device.editor import Editor, Row, Template

_NUMBER = frozenset("0123456789.ᴇ")

type Units = list[tuple[int, int]]  # [start, end) of each unit in a row


def full_selection(shown: Editor, full: Row) -> Row:
    """The nodes of `full` that the selection in `shown` stands for; all of `full` when nothing
    is selected. If the trees do not line up (they always should), the shown selection."""
    nothing = shown.anchor is None and shown.cell_sel is None and not shown.selected
    if nothing:
        return copy.deepcopy(full)
    moved = _moved(shown, full)
    return moved.selection() if moved is not None else shown.selection()


def _moved(shown: Editor, full: Row) -> Editor | None:
    """An editor on `full` with the cursor, anchor and cell selection of `shown`, carried over."""
    editor = Editor()
    editor.root = full
    shown_row, full_row = shown.root, full
    for index, slot in shown.path:
        pair = _aligned(shown_row, full_row)
        if pair is None:
            return None
        ours, theirs = pair
        unit = _unit_at(ours, index)
        source, target = shown_row[index], full_row[theirs[unit][0]]
        if not (isinstance(source, Template) and isinstance(target, Template)):
            return None
        editor.path.append((theirs[unit][0], slot))
        shown_row, full_row = source.slots[slot], target.slots[slot]
    pair = _aligned(shown_row, full_row)
    if pair is None:
        return None
    ours, theirs = pair
    low, high = shown.span
    start = theirs[_unit_at(ours, low)][0] if low < len(shown_row) else len(full_row)
    end = theirs[_unit_at(ours, high - 1)][1] if high > low else start
    at_low = shown.pos == low
    if shown.anchor is not None:
        editor.anchor, editor.pos = (end, start) if at_low else (start, end)
    else:
        editor.pos = theirs[_unit_at(ours, shown.pos - 1)][1] if shown.pos else 0
    editor.selected = shown.selected
    editor.cell_sel = shown.cell_sel
    return editor


def _aligned(shown: Row, full: Row) -> tuple[Units, Units] | None:
    """Each row's units, if the two rows match unit for unit (numbers may differ in length)."""
    ours, theirs = _units(shown), _units(full)
    if len(ours) != len(theirs):
        return None
    for (a, b), (c, d) in zip(ours, theirs, strict=True):
        left, right = shown[a:b], full[c:d]
        if _is_number(left) and _is_number(right):
            continue
        if len(left) != 1 or len(right) != 1 or not _same_shape(left[0], right[0]):
            return None
    return ours, theirs


def _same_shape(left: object, right: object) -> bool:
    if isinstance(left, Template) and isinstance(right, Template):
        return (left.kind, left.cols, len(left.slots)) == (right.kind, right.cols, len(right.slots))
    return left == right


def _units(row: Row) -> Units:
    """Templates and characters one by one; a number (`12.5`, `1.5ᴇ-7`) as one unit."""
    units: Units = []
    index = 0
    while index < len(row):
        end = index + 1
        if _is_digit(row[index]):
            while end < len(row) and (
                _is_digit(row[end]) or (row[end] == "-" and row[end - 1] == "ᴇ")
            ):
                end += 1
        units.append((index, end))
        index = end
    return units


def _is_digit(node: object) -> bool:
    return isinstance(node, str) and node in _NUMBER


def _is_number(nodes: Row) -> bool:
    return bool(nodes) and _is_digit(nodes[0])


def _unit_at(units: Units, index: int) -> int:
    """The unit holding the node at `index`."""
    for number, (start, end) in enumerate(units):
        if start <= index < end:
            return number
    return len(units) - 1
