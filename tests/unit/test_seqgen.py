# Requirements traced here: FR-SHEET-001
"""`seqgen` and the spreadsheet's Generate Sequence (slice 3a): check 6 E14 and the corpus case
`app.sheet.generate-sequence-recursive`."""

import pytest

from cassim.core.session import Session
from cassim.sheet import actions
from cassim.sheet.actions import DataLossError
from cassim.sheet.sheet import Sheet


@pytest.mark.parametrize(
    ("line", "text"),
    [
        ("seqgen(2*u(n-1)+1,n,u,{1,6},{1})", "{1,3,7,15,31,63}"),
        ("seqgen(n^2,n,u,{1,5},{_},1)", "{1,4,9,16,25}"),  # the empty box of check 6, E14
        ("seqgen(n^2,n,u,{1,5})", "{1,4,9,16,25}"),
        ("seqgen(u(n-1)+u(n-2),n,u,{1,10},{1,1})", "{1,1,2,3,5,8,13,21,34,55}"),
        ("seqgen(2*u(n-1),n,u,{1,20},{1},1,100)", "{1,2,4,8,16,32,64}"),  # ceiling 100
        ("seqgen(u(n-1)/2,n,u,{0,3},{8})", "{8,4,2,1}"),
        ("seqgen(n,n,u,{1,9},{},2)", "{1,3,5,7,9}"),
        ("seqgen(n,n,u,{1,3},5)", "{5,2,3}"),  # a single initial term
    ],
)
def test_seqgen(line, text):
    assert Session().eval(line).text == text


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("seqgen(u(n-1)+1,n,u,{1,3})", "Domain error"),  # no term before the first
        ("seqgen(n,n,u,{1,3},{},0)", "Domain error"),
        ("seqgen(n,n,u,{1,3,5})", "Dimension mismatch"),
        ("seqgen(n,2,u,{1,3})", "Syntax"),
        ("seqgen(n,n,u,{1.5,3})", "Domain error"),
    ],
)
def test_seqgen_errors(line, message):
    assert message in (Session().eval(line).error or "")


def test_generate_sequence_fills_the_column():
    """Corpus app.sheet.generate-sequence-recursive: u(n)=2*u(n-1)+1, 1, n0 1, nMax 6."""
    sheet = Sheet(Session())
    actions.generate_sequence(sheet, 0, "2*u(n-1)+1", initial="1", last=6)
    shown = [sheet.shown(0, row).text for row in range(1, 8)]
    assert shown == ["1", "3", "7", "15", "31", "63", ""]
    assert sheet.column(0).formula == "seqgen(2*u(n-1)+1,n,u,{1,6},{1},1)"


def test_generate_sequence_without_initial_terms():
    """Check 6, E14: Formula n^2, nMax 5."""
    sheet = Sheet(Session())
    actions.generate_sequence(sheet, 4, "n^2", last=5)
    assert [sheet.shown(4, row).text for row in range(1, 6)] == ["1", "4", "9", "16", "25"]
    assert sheet.column(4).formula == "seqgen(n^2,n,u,{1,5},{_},1)"


def test_generate_sequence_with_a_ceiling():
    sheet = Sheet(Session())
    actions.generate_sequence(sheet, 0, "2*u(n-1)", initial="1", last=20, ceiling="10")
    assert sheet.last_row(0) == 4


def test_generate_sequence_over_data_asks_first():
    sheet = Sheet(Session())
    sheet.set_cell(0, 1, "9")
    with pytest.raises(DataLossError):
        actions.generate_sequence(sheet, 0, "n", last=3)
    actions.generate_sequence(sheet, 0, "n", last=3, confirm=True)
    assert [sheet.shown(0, row).text for row in range(1, 4)] == ["1", "2", "3"]
