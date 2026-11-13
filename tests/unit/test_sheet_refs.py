# Requirements traced here: FR-SHEET-002
"""Cell references inside spreadsheet formulas (slice 3a)."""

import pytest

from cassim.sheet import refs
from cassim.sheet.refs import Column, Ref, Span, Variable


def kinds(text):
    return [item.reference for item in refs.scan(text)]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("f1+1", [Ref(5, 1)]),
        ("f1*$g$1", [Ref(5, 1), Ref(6, 1, fixed_column=True, fixed_row=True)]),
        ("$a2+a$2", [Ref(0, 2, fixed_column=True), Ref(0, 2, fixed_row=True)]),
        ("sum(f1:f4)", [Span(Ref(5, 1), Ref(5, 4))]),
        ("mean(c1 : c6)", [Span(Ref(2, 1), Ref(2, 6))]),
        ("a[]^2", [Column(0)]),
        ("'d1+qq", [Variable("d1")]),
        ("mean(xs)", []),  # a list name is a variable, not a cell
        ("seq(n^2,n,1,8)", []),
        ('"a1"&b2', [Ref(1, 2)]),  # nothing inside a string
        ("f1(2)", []),  # a call
        ("stat.r2", []),
        ("x2y", []),
    ],
)
def test_scan(text, found):
    assert kinds(text) == found


def test_off_sheet_references_are_found_but_not_valid():
    assert not refs.scan("a2501")[0].reference.valid
    assert refs.scan("z1")[0].reference.valid


@pytest.mark.parametrize(
    ("text", "columns", "rows", "expected"),
    [
        ("a1+a2", 0, 1, "a2+a3"),  # Fill down (corpus app.sheet.fill-down-fibonacci)
        ("f1*$g$1", 0, 2, "f3*$g$1"),  # check 6, E6
        ("$a1+a$1", 1, 1, "$a2+b$1"),
        ("sum(a1:b2)", 1, 0, "sum(b1:c2)"),
        ("a[]+1", 0, 3, "a[]+1"),
    ],
)
def test_shifted(text, columns, rows, expected):
    assert refs.shifted(text, columns, rows) == expected


def test_shifted_off_the_sheet_is_none():
    assert refs.shifted("a1", 0, -1) is None


def test_remapped_moves_references_past_an_inserted_row():
    def down(ref):
        moved = Ref(ref.column, ref.row + 1, ref.fixed_column, ref.fixed_row)
        return moved if ref.row >= 2 else ref

    assert refs.remapped("c3+c1+sum(c1:c4)", down) == "c4+c1+sum(c1:c5)"


@pytest.mark.parametrize(
    ("text", "ref"), [("h40", Ref(7, 40)), (" A12 ", Ref(0, 12)), ("a2501", None), ("aa1", None)]
)
def test_address(text, ref):
    assert refs.address(text) == ref
