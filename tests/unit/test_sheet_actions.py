# Requirements traced here: FR-SHEET-001
"""Fill, Sort, Insert and Delete on the headless sheet (slice 3a): emulator check 6 E6, E12,
E18, check run 2 E12, and the corpus cases `app.sheet.fill-down-fibonacci` and
`app.sheet.sort-column`."""

import pytest

from cassim.core.session import Session
from cassim.sheet import actions
from cassim.sheet.actions import DataLossError
from cassim.sheet.refs import Ref, Span
from cassim.sheet.sheet import Sheet, SheetError

A, B, C, D, E, F, G, H = range(8)


def span(left, top, right, bottom):
    return Span(Ref(left, top), Ref(right, bottom))


def texts(sheet, column, rows):
    return [sheet.shown(column, row).text for row in rows]


def column_of(sheet, column, values):
    for row, value in enumerate(values, start=1):
        sheet.set_cell(column, row, str(value))


# ----- Fill ---------------------------------------------------------------------------------------


def test_fill_down_fibonacci():
    """Corpus app.sheet.fill-down-fibonacci: A1=1, A2=1, A3 =a1+a2, Fill A3 to A3:A20."""
    sheet = Sheet(Session())
    column_of(sheet, A, [1, 1, "=a1+a2"])
    actions.fill(sheet, span(A, 3, A, 3), span(A, 3, A, 20))
    expected = [2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765]
    assert texts(sheet, A, range(3, 21)) == [str(n) for n in expected]
    assert sheet.text(A, 20) == "=a18+a19"


def test_fill_keeps_fixed_references():
    """Check 6, E6: =f1*$g$1 filled H1:H4."""
    sheet = Sheet(Session())
    column_of(sheet, F, [5, "1/3", 4, 6])
    sheet.set_cell(G, 1, "2")
    sheet.set_cell(H, 1, "=f1*$g$1")
    actions.fill(sheet, span(H, 1, H, 1), span(H, 1, H, 4))
    assert texts(sheet, H, range(1, 5)) == ["10", "2/3", "8", "12"]
    assert sheet.text(H, 3) == "=f3*$g$1"


def test_fill_right_and_with_a_block():
    sheet = Sheet(Session())
    column_of(sheet, A, [1, 2, 3, 4])
    sheet.set_cell(B, 1, "=a1*10")
    sheet.set_cell(B, 2, "7")
    actions.fill(sheet, span(B, 1, B, 2), span(B, 1, C, 4))
    assert sheet.text(C, 1) == "=b1*10"
    assert texts(sheet, B, [3, 4]) == ["30", "7"]  # the block repeats down


def test_fill_off_the_sheet_leaves_a_blank():
    sheet = Sheet(Session())
    sheet.set_cell(A, 2, "=a1+1")
    actions.fill(sheet, span(A, 2, A, 2), span(A, 1, A, 1))
    assert sheet.content(A, 1) is None


# ----- Sort ---------------------------------------------------------------------------------------


def test_sort_one_column():
    """Corpus app.sheet.sort-column."""
    sheet = Sheet(Session())
    column_of(sheet, A, [5, 2, 9, 4, 7])
    actions.sort(sheet, span(A, 1, A, 5), A)
    assert texts(sheet, A, range(1, 6)) == ["2", "4", "5", "7", "9"]


def test_sort_moves_rows_and_asks_before_a_formula_column():
    """Check 6, E18: A 9,3,7,1; B a,d,c,b; C =a[]*2, sorted by a."""
    sheet = Sheet(Session())
    column_of(sheet, A, [9, 3, 7, 1])
    column_of(sheet, B, ['"a"', '"d"', '"c"', '"b"'])
    sheet.set_column_formula(C, "=a[]*2")
    with pytest.raises(DataLossError) as raised:
        actions.sort(sheet, span(A, 1, C, 4), A)
    assert raised.value.title == "Data Loss"
    assert texts(sheet, A, range(1, 5)) == ["9", "3", "7", "1"]  # Cancel changes nothing
    actions.sort(sheet, span(A, 1, C, 4), A, confirm=True)
    assert texts(sheet, A, range(1, 5)) == ["1", "3", "7", "9"]
    assert texts(sheet, B, range(1, 5)) == ["b", "d", "c", "a"]
    assert texts(sheet, C, range(1, 5)) == ["2", "6", "14", "18"]
    assert sheet.column(C).formula is None  # the formula is gone, its values stay
    actions.sort(sheet, span(A, 1, C, 4), B, descending=True)  # no dialog the second time
    assert texts(sheet, B, range(1, 5)) == ["d", "c", "b", "a"]
    assert texts(sheet, A, range(1, 5)) == ["3", "7", "1", "9"]


def test_sort_turns_cell_formulas_into_values_and_puts_blanks_last():
    sheet = Sheet(Session())
    column_of(sheet, A, [3, "", 1, "=a1*2"])
    actions.sort(sheet, span(A, 1, A, 4), A)
    assert texts(sheet, A, range(1, 5)) == ["1", "3", "6", ""]
    assert sheet.text(A, 3) == "=6"  # check 6, E18: the sorted formula leaves =6


def test_sort_a_linked_column_sorts_its_list():
    session = Session()
    sheet = Sheet(session)
    column_of(sheet, A, [3, 1, 2])
    sheet.set_name(A, "xs")
    actions.sort(sheet, span(A, 1, A, 3), A, descending=True)
    assert session.eval("xs").text == "{3,2,1}"


def test_sort_by_a_column_outside_the_range_is_refused():
    with pytest.raises(SheetError):
        actions.sort(Sheet(Session()), span(A, 1, A, 3), B)


# ----- Insert and delete --------------------------------------------------------------------------


def test_insert_row_moves_formulas_and_puts_a_gap_in_linked_lists():
    """Check run 2, E12: G1 =c3 becomes =c4; linked columns show _ in the new row."""
    session = Session()
    sheet = Sheet(session)
    column_of(sheet, C, [7, 8, 9])
    sheet.set_name(C, "d1")
    sheet.set_cell(G, 1, "=c3")
    actions.insert_row(sheet, 2)
    assert sheet.text(G, 1) == "=c4"
    assert sheet.shown(G, 1).text == "9"
    assert sheet.shown(C, 2).text == "_"
    assert session.eval("d1").text == "{7,_,8,9}"
    actions.delete_row(sheet, 2)
    assert sheet.text(G, 1) == "=c3"
    assert session.eval("d1").text == "{7,8,9}"


def test_insert_and_delete_cell_shift_only_their_column():
    """Check 6, E12: Insert Cell at K1 moves 7, 8, 9 down; Delete Cell at C3 moves C4 up."""
    sheet = Sheet(Session())
    column_of(sheet, A, [7, 8, 9])
    column_of(sheet, B, [1, 2, 3])
    actions.insert_cell(sheet, A, 1)
    assert texts(sheet, A, range(1, 5)) == ["", "7", "8", "9"]
    assert texts(sheet, B, range(1, 4)) == ["1", "2", "3"]
    actions.delete_cell(sheet, A, 2)
    assert texts(sheet, A, range(1, 4)) == ["", "8", "9"]


def test_insert_column_moves_names_formulas_and_whole_column_references():
    """Check 6, E12: Insert Column at B moves B (4, 5, 6) to C."""
    session = Session()
    sheet = Sheet(session)
    column_of(sheet, A, [1, 2, 3])
    column_of(sheet, B, [4, 5, 6])
    sheet.set_name(B, "ws")
    sheet.set_column_formula(C, "=b[]+a[]")
    sheet.set_cell(D, 1, "=b1")
    actions.insert_column(sheet, B)
    assert texts(sheet, C, [1, 2, 3]) == ["4", "5", "6"]
    assert sheet.column(C).name == "ws"
    assert sheet.column(D).formula == "c[]+a[]"
    assert texts(sheet, D, [1, 2, 3]) == ["5", "7", "9"]
    assert sheet.text(E, 1) == "=c1"
    assert texts(sheet, B, [1]) == [""]


def test_delete_column_moves_the_rest_left():
    """Check 6, E12: Delete Column on A."""
    session = Session()
    sheet = Sheet(session)
    column_of(sheet, A, [1, 2, 3])
    sheet.set_name(A, "xs")
    column_of(sheet, B, [4, 5, 6])
    sheet.set_cell(C, 1, "=b2")
    actions.delete_column(sheet, A)
    assert texts(sheet, A, [1, 2, 3]) == ["4", "5", "6"]
    assert sheet.text(B, 1) == "=a2"
    assert sheet.find("xs") is None
    assert session.eval("xs").text == "{1,2,3}"


def test_restore_reopens_a_saved_sheet():
    session = Session()
    sheet = Sheet(session)
    column_of(sheet, A, [1, 2])
    sheet.set_name(A, "xs")
    sheet.set_column_formula(B, "=a[]^2")
    saved = sheet.contents(), [sheet.column(c) for c in range(26)]
    again = Sheet(Session())
    again.restore(*saved)
    assert texts(again, B, [1, 2]) == ["1", "4"]
    assert again.column(A).name == "xs"
