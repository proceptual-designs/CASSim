# Requirements traced here: FR-SHEET-001, FR-STAT-001, FR-STAT-002
"""Stat Calculations from a sheet (slice 3c): emulator check 5 E15 and check 6 run 4, S1 to S9
(`docs/testing/emulator-sheet4-results.md`)."""

from collections.abc import Sequence

import pytest

from cassim.core.session import Session
from cassim.sheet import actions
from cassim.sheet.sheet import ConflictError, DataLossError, Sheet

A, B, C, D, E, F, G, H, COL_I, J = range(10)
D1 = [2, 4, 4, 4, 5, 5, 7, 9]
XS = [1, 2, 3, 4, 5, 6, 7, 8]
YS = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2, 13.8, 16.1]


def sheet_with(**columns: Sequence[float]) -> tuple[Session, Sheet]:
    session = Session()
    sheet = Sheet(session)
    for letter, values in columns.items():
        column = ord(letter) - ord("a")
        for row, value in enumerate(values, start=1):
            sheet.set_cell(column, row, str(value))
    return session, sheet


def results(sheet: Sheet, column: int) -> dict[str, str]:
    """The label column `column` and the value column after it, as {label: shown value}."""
    rows = range(1, sheet.last_row(column) + 1)
    return {sheet.shown(column, r).text: sheet.shown(column + 1, r).text for r in rows}


def test_one_variable_statistics():
    """S1: labels in F, values in G from one formula in G's formula row."""
    _, sheet = sheet_with(c=D1)
    actions.stat_calc(sheet, "OneVar", ["c[]"], column=F)
    found = results(sheet, F)
    assert found["Title"] == "One-Variable Statistics"
    assert (found["x̄"], found["Σx"], found["Σx²"], found["n"]) == ("5.", "40.", "232.", "8.")
    assert found["Q₁X"] == "4."  # the median of the lower half (TI's rule)
    assert sheet.column(G).formula == "OneVar c[],1"
    assert sheet.column(F).formula is None
    assert sheet.text(F, 1) == '="Title"'  # S1: the bar shows ="Title"


def test_the_results_follow_the_data():
    """Check 5 E15 (live update); run 4, S2, S3."""
    session, sheet = sheet_with(a=XS, b=YS)
    actions.stat_calc(sheet, "LinRegMx", ["a[]", "b[]"], column=E, save="f1")
    assert results(sheet, E)["m"] == "1.997619"
    assert session.eval("f1(t)").text.startswith("1.997619")
    sheet.set_cell(A, 1, "0")
    assert results(sheet, E)["m"] == "1.8210526"
    assert session.eval("f1(t)").text == "1.8210526*t+1.0578947"
    assert session.eval("stat.m").text == "1.8210526"
    assert sheet.column(F).formula == "LinRegMx a[],b[],1: CopyVar stat.RegEqn,f1"


def test_a_list_name_that_is_also_a_cell_asks_first():
    """S1, S7: `d1` names a list and the cell D1: Conflict Detected, before Data Loss."""
    session, sheet = sheet_with(c=D1)
    session.eval("d1:={2,4,4,4,5,5,7,9}")
    with pytest.raises(ConflictError):
        actions.stat_calc(sheet, "OneVar", ["d1"], column=F)
    actions.stat_calc(sheet, "OneVar", ["d1"], column=F, choose={"d1": "variable"})
    assert results(sheet, F)["x̄"] == "5."
    with pytest.raises(ConflictError):  # again over the results: still Conflict first
        actions.stat_calc(sheet, "OneVar", ["d1"], column=F)
    with pytest.raises(DataLossError):
        actions.stat_calc(sheet, "OneVar", ["d1"], column=F, choose={"d1": "variable"})


def test_results_over_data_ask_first():
    """S5, S7: Data Loss when the result columns hold anything; OK writes over them."""
    _, sheet = sheet_with(c=D1, g=[1, 2])
    with pytest.raises(DataLossError):
        actions.stat_calc(sheet, "OneVar", ["c[]"], column=F)
    actions.stat_calc(sheet, "OneVar", ["c[]"], column=F, confirm=True)
    assert results(sheet, F)["n"] == "8."


def test_two_lists_share_one_label_column():
    """S5: X1 and X2 have a value column each, with its own formula."""
    _, sheet = sheet_with(a=XS, c=D1)
    actions.stat_calc(sheet, "OneVar", ["a[]", "c[]"], column=E)
    assert results(sheet, E)["x̄"] == "4.5"
    assert sheet.shown(G, 2).text == "5."
    assert sheet.column(F).formula == "OneVar a[],1"
    assert sheet.column(G).formula == "OneVar c[],1"


def test_regressions_lay_out_their_rows():
    """S4: Title, RegEqn, the coefficients, r² or R², r, Resid (ResidTrans for ExpReg)."""
    _, sheet = sheet_with(a=XS, b=YS)
    actions.stat_calc(sheet, "QuadReg", ["a[]", "b[]"], column=E)
    assert list(results(sheet, E)) == ["Title", "RegEqn", "a", "b", "c", "R²", "Resid"]
    actions.stat_calc(sheet, "ExpReg", ["a[]", "b[]"], column=G)
    assert list(results(sheet, G))[-2:] == ["Resid", "ResidTrans"]


def test_a_gap_in_the_data_is_left_out():
    """S8: values 1, 2, (gap), 4, 5 give n 4 and mean 3."""
    _, sheet = sheet_with(v=[1, 2])
    sheet.set_cell(21, 4, "4")
    sheet.set_cell(21, 5, "5")
    actions.stat_calc(sheet, "OneVar", ["v[]"], column=COL_I)
    found = results(sheet, COL_I)
    assert (found["x̄"], found["n"]) == ("3.", "4.")


def test_a_category_run_works_as_on_the_calculator():
    """S9: the emulator's sheet gives "Syntax error during insertion" here; its Calculator
    route works, and CASSim follows that."""
    session, sheet = sheet_with(c=D1)
    session.eval('cat:={"a","b","a","c","b","a","c","a"}')
    actions.stat_calc(sheet, "OneVar", ["c[]"], column=F, category="cat", include='{"a"}')
    assert (results(sheet, F)["n"], results(sheet, F)["SSX := Σ(x-x̄)²"]) == ("4.", "26.")


def test_typing_in_a_value_column_clears_the_results_but_a_label_just_goes():
    """S6."""
    _, sheet = sheet_with(c=D1)
    actions.stat_calc(sheet, "OneVar", ["c[]"], column=F)
    sheet.set_cell(F, 3, "")  # Del on a label: no dialog
    assert sheet.shown(F, 3).text == ""
    with pytest.raises(DataLossError):
        sheet.set_cell(G, 2, "7")
    sheet.set_cell(G, 2, "7", confirm=True)
    assert [sheet.shown(G, r).text for r in (1, 2, 3)] == ["", "7", ""]


def test_a_failing_run_shows_err():
    _, sheet = sheet_with(a=[1, 2, 3], b=[1, 2])
    notices = actions.stat_calc(sheet, "LinRegMx", ["a[]", "b[]"], column=E)
    assert [n.title for n in notices] == ["Syntax Error in Column: f"]


def test_the_result_columns_must_fit():
    _, sheet = sheet_with(a=XS)
    with pytest.raises(Exception, match="Invalid input"):
        actions.stat_calc(sheet, "OneVar", ["a[]"], column=25)
