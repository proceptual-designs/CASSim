# Requirements traced here: FR-SHEET-001, FR-SHEET-002, FR-DOC-008
"""The headless spreadsheet (slice 3a): cells, formulas, linked and formula columns, recalculation.

Expected behaviour is from emulator check 6 (`docs/testing/emulator-sheet3-results.md`, part E;
`emulator-sharing-results.md`, part G) and the corpus app cases in `corpus/seed/016`, `024`.
"""

import pytest

from cassim.core.session import Session
from cassim.sheet.sheet import ConflictError, Constant, Entry, Sheet, SheetError

A, B, C, D, E, F, G, H, COL_I, COL_J = range(10)


def texts(sheet, column, rows):
    return [sheet.shown(column, row).text for row in rows]


def sheet_with(column, values, session=None):
    sheet = Sheet(session or Session())
    for row, value in enumerate(values, start=1):
        sheet.set_cell(column, row, str(value))
    return sheet


# ----- corpus app cases --------------------------------------------------------------------------


def test_formula_column_squares_column_a():
    """app.sheet.formula-column: B's formula row holds =a[]^2."""
    sheet = sheet_with(A, [2, 4, 4, 4, 5, 5, 7, 9])
    assert sheet.set_column_formula(B, "=a[]^2") == []
    assert texts(sheet, B, range(1, 10)) == ["4", "16", "16", "16", "25", "25", "49", "81", ""]


def test_seq_column():
    """app.sheet.seq-column."""
    sheet = Sheet(Session())
    sheet.set_column_formula(C, "=seq(n^2,n,1,8)")
    assert texts(sheet, C, range(1, 9)) == ["1", "4", "9", "16", "25", "36", "49", "64"]


def test_fibonacci_by_relative_formulas():
    """app.sheet.fill-down-fibonacci, with the formulas Fill would write."""
    sheet = sheet_with(A, [1, 1])
    for row in range(3, 21):
        sheet.set_cell(A, row, f"=a{row - 2}+a{row - 1}")
    assert texts(sheet, A, [16, 17, 18, 19, 20]) == ["987", "1597", "2584", "4181", "6765"]


def test_a_change_flows_down_a_chain():
    sheet = sheet_with(A, [1, 1])
    for row in range(3, 21):
        sheet.set_cell(A, row, f"=a{row - 2}+a{row - 1}")
    sheet.set_cell(A, 1, "2")
    assert sheet.shown(A, 20).text == "9349"


def test_a_long_chain_needs_no_deep_recursion():
    sheet = sheet_with(A, [1])
    for row in range(2, 1201):
        sheet.set_cell(A, row, f"=a{row - 1}+1")
    sheet.set_cell(A, 1, "5")
    assert sheet.shown(A, 1200).text == "1204"


# ----- entries (check 6, E5) ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("typed", "shown", "right"),
    [
        ("5", "5", True),
        ("1/3", "1/3", True),
        ("-2.5", "-2.5", True),
        ("2^0.5", "2^0.5", False),  # kept as typed, on the left
        ("sqrt(2)", "sqrt(2)", False),
        ("pi", "π", False),
        ('"text"', "text", False),
        ("abc", "abc", False),
        ("_", "_", False),  # check 6, E21
    ],
)
def test_entries(typed, shown, right):
    sheet = Sheet(Session())
    sheet.set_cell(F, 1, typed)
    assert sheet.shown(F, 1).text == shown
    assert sheet.shown(F, 1).right is right
    assert sheet.text(F, 1) == typed


def test_formulas_use_the_value_of_an_entry_kept_as_typed():
    sheet = sheet_with(F, [5, "1/3", "2^0.5", "sqrt(2)"])
    sheet.set_cell(G, 1, "2")
    for row in range(1, 5):
        sheet.set_cell(H, row, f"=f{row}*$g$1")  # check 6, E6
    assert texts(sheet, H, range(1, 5)) == ["10", "2/3", "2.8284271", "2*√(2)"]
    assert sheet.text(H, 1) == "=f1*$g$1"


def test_approximate_mode_shows_numbers_as_decimals_and_leaves_text():
    session = Session()
    sheet = sheet_with(F, [5, "1/3", "2^0.5", "pi"], session)
    sheet.set_cell(F, 5, "=f1+1")
    session.set(calc="approximate")
    sheet.recalculate()
    assert texts(sheet, F, range(1, 6)) == ["5.", "0.33333333", "2^0.5", "π", "6."]


def test_clearing_a_cell():
    sheet = sheet_with(A, [1, 2])
    sheet.set_cell(B, 1, "=a1+a2")
    sheet.set_cell(A, 2, "")
    assert sheet.shown(A, 2).text == ""
    assert sheet.shown(B, 1).text == "_"  # guess: a blank cell is an empty element


# ----- formulas and errors (check 6, E6, E20, E21, E23) ------------------------------------------


def test_functions_of_ranges_and_columns():
    sheet = sheet_with(C, [6, 14, 2, 18])
    sheet.set_cell(D, 1, "=mean(c1:c3)")
    sheet.set_cell(D, 2, "=mean(c1:c6)")  # empty cells are left out
    sheet.set_cell(D, 3, "=sum(c[])")
    assert texts(sheet, D, [1, 2, 3]) == ["22/3", "10", "40"]


def test_division_by_zero_shows_undef_without_a_dialog():
    sheet = Sheet(Session())
    assert sheet.set_cell(D, 1, "=1/0") == []
    assert sheet.shown(D, 1).text == "#UNDEF"


def test_undef_spreads_to_a_mean_over_it():
    sheet = sheet_with(C, [1, 2])
    sheet.set_cell(D, 1, "=1/0")
    sheet.set_cell(D, 2, "=mean(d1:d1)")
    assert sheet.shown(D, 2).text == "#UNDEF"


@pytest.mark.parametrize("formula", ["=f1:f3", "=randint(1,6,5)", "={1,2}"])
def test_a_list_in_a_cell_is_an_error_with_a_dialog(formula):
    sheet = sheet_with(F, [1, 2, 3])
    notices = sheet.set_cell(F, 9, formula)
    assert [(n.title, n.message) for n in notices] == [("Syntax Error in Cell: f9", "Syntax")]
    assert sheet.shown(F, 9).text == "#ERR"
    assert sheet.text(F, 9) == formula


def test_an_error_spreads_to_formulas_that_read_it():
    sheet = Sheet(Session())
    sheet.set_cell(A, 1, "={1,2}")
    sheet.set_cell(A, 2, "=a1+1")
    assert sheet.shown(A, 2).text == "#ERR"


@pytest.mark.parametrize(
    ("formula", "message"),
    [
        ("=i5", "Circular definition"),
        ("=undefinedname", "Syntax error during insertion."),
        ("=1+", "Syntax error during insertion."),
        ("=a2501", "Syntax error during insertion."),
    ],
)
def test_refused_formulas_leave_the_cell_as_it_was(formula, message):
    sheet = Sheet(Session())
    sheet.set_cell(COL_I, 5, "7")
    with pytest.raises(SheetError) as raised:
        sheet.set_cell(COL_I, 5, formula)
    assert (raised.value.title, raised.value.message) == ("Syntax Error", message)
    assert sheet.shown(COL_I, 5).text == "7"


def test_a_cycle_through_other_cells_is_refused():
    sheet = Sheet(Session())
    sheet.set_cell(A, 1, "=a2+1")
    sheet.set_cell(A, 2, "=a3+1")
    with pytest.raises(SheetError, match="Circular"):
        sheet.set_cell(A, 3, "=a1")


def test_recalculate_draws_a_new_random_number():
    """Ctrl+R (check 6, E23)."""
    sheet = Sheet(Session())
    sheet.set_cell(D, 9, "=rand()")
    seen = {sheet.shown(D, 9).text}
    for _ in range(5):
        sheet.recalculate()
        seen.add(sheet.shown(D, 9).text)
    assert len(seen) > 1


def test_recalculate_shows_the_dialog_again():
    sheet = Sheet(Session())
    sheet.set_cell(D, 8, "={1,2}")
    assert [n.title for n in sheet.recalculate()] == ["Syntax Error in Cell: d8"]


# ----- column formulas (check run 2, E20) --------------------------------------------------------


def test_a_failing_column_formula_shows_err_in_every_cell():
    session = Session()
    session.eval("qq:={1,2}")
    sheet = sheet_with(D, [7, 8, 9], session)
    sheet.set_name(D, "d1")
    notices = sheet.set_column_formula(E, "=d1+qq", choose={"d1": "variable"})
    assert [(n.title, n.message) for n in notices] == [
        ("Syntax Error in Column: e", "Dimension mismatch")
    ]
    assert texts(sheet, E, [1, 5]) == ["#ERR", "#ERR"]


def test_a_column_formula_follows_its_source():
    sheet = sheet_with(A, [1, 2, 3])
    sheet.set_column_formula(B, "=a[]*10")
    sheet.set_cell(A, 4, "4")
    assert texts(sheet, B, range(1, 5)) == ["10", "20", "30", "40"]


def test_a_shorter_result_clears_the_rows_below():
    sheet = sheet_with(A, [1, 2, 3])
    sheet.set_column_formula(B, "=a[]")
    sheet.set_cell(A, 3, "")
    assert texts(sheet, B, [1, 2, 3]) == ["1", "2", ""]


def test_clearing_a_column_formula_keeps_its_values():
    sheet = sheet_with(A, [1, 2])
    sheet.set_column_formula(B, "=a[]*3")
    sheet.set_column_formula(B, "")
    sheet.set_cell(A, 1, "5")
    assert texts(sheet, B, [1, 2]) == ["3", "6"]
    assert sheet.content(B, 1) == Constant(sheet.value(B, 1))


def test_typing_into_a_formula_column_is_refused():
    sheet = sheet_with(A, [1])
    sheet.set_column_formula(B, "=a[]")
    with pytest.raises(SheetError):
        sheet.set_cell(B, 1, "5")


# ----- linked columns (check 6, E7; check run 2, G) ----------------------------------------------


def test_naming_a_column_makes_the_list():
    session = Session()
    sheet = sheet_with(A, [1, 2, 3], session)
    sheet.set_name(A, "xs")
    assert session.eval("xs").text == "{1,2,3}"
    sheet.set_cell(A, 2, "20")
    assert session.eval("xs").text == "{1,20,3}"


def test_a_gap_in_a_linked_column_is_an_empty_element():
    session = Session()
    sheet = sheet_with(A, [1, 2, 3], session)
    sheet.set_name(A, "xs")
    sheet.set_cell(A, 2, "")
    assert session.eval("xs").text == "{1,_,3}"
    sheet.set_cell(A, 3, "")
    assert session.eval("xs").text == "{1}"  # clearing the last cell shortens the list


def test_naming_a_column_after_an_existing_list_takes_the_list():
    session = Session()
    session.eval("qq:={7,8,9}")
    sheet = sheet_with(COL_I, [1, 2, 3, 4], session)
    assert sheet.set_name(COL_I, "qq") == []
    assert texts(sheet, COL_I, range(1, 5)) == ["7", "8", "9", ""]


def test_a_calculator_store_reaches_the_column_and_its_readers():
    session = Session()
    sheet = sheet_with(A, [2, 4, 6], session)
    sheet.set_name(A, "xs")
    sheet.set_column_formula(B, "=a[]^2")
    sheet.set_cell(C, 1, "=mean(xs)")
    session.eval("xs[2]:=20")
    sheet.sync()
    assert sheet.shown(A, 2).text == "20"
    assert sheet.shown(B, 2).text == "400"
    assert sheet.shown(C, 1).text == "28/3"
    session.eval("xs[4]:=1")  # one past the end appends
    sheet.sync()
    assert sheet.shown(A, 4).text == "1"


def test_sync_with_nothing_new_changes_nothing():
    session = Session()
    sheet = sheet_with(A, [1, 2], session)
    sheet.set_name(A, "xs")
    revision = sheet.revision
    assert sheet.sync() == []
    assert sheet.revision == revision


def test_the_sheets_own_write_does_not_turn_its_formulas_into_values():
    session = Session()
    sheet = sheet_with(A, [1], session)
    sheet.set_cell(A, 2, "=a1+1")
    sheet.set_name(A, "xs")
    session.eval("k:=5")  # some other change, so sync has something to look at
    sheet.sync()
    assert sheet.text(A, 2) == "=a1+1"


def test_delvar_unlinks_the_column_and_keeps_its_values():
    session = Session()
    sheet = sheet_with(A, [1, 2], session)
    sheet.set_name(A, "xs")
    session.eval("DelVar xs")
    sheet.sync()
    assert sheet.column(A).name is None
    assert texts(sheet, A, [1, 2]) == ["1", "2"]


def test_a_named_formula_column_is_a_variable():
    session = Session()
    sheet = sheet_with(A, [1, 2, 3], session)
    sheet.set_name(A, "xs")
    sheet.set_name(B, "sq")
    sheet.set_column_formula(B, "=xs^2")
    assert session.eval("sq").text == "{1,4,9}"
    session.eval("xs:={5,6}")
    sheet.sync()
    assert session.eval("sq").text == "{25,36}"


def test_a_formula_reading_a_list_by_name_follows_it():
    session = Session()
    session.eval("ys:={1,2,3}")
    sheet = Sheet(session)
    sheet.set_cell(A, 1, "=sum(ys)")
    session.eval("ys:={10,20}")
    sheet.sync()
    assert sheet.shown(A, 1).text == "30"


@pytest.mark.parametrize("name", ["1a", "sin", "pi", "a+b"])
def test_invalid_column_names(name):
    sheet = Sheet(Session())
    with pytest.raises(SheetError) as raised:
        sheet.set_name(COL_J, name)
    assert raised.value.message == "Cannot accept change: Invalid input."
    assert sheet.column(COL_J).name is None


def test_a_list_linked_twice_on_one_sheet_is_refused():
    sheet = sheet_with(A, [1])
    sheet.set_name(A, "xs")
    with pytest.raises(SheetError) as raised:
        sheet.set_name(C, "xs")
    assert (raised.value.title, raised.value.message) == (
        "Link Error",
        "Cannot link to same list/variable twice",
    )


def test_find_a_linked_column():
    sheet = sheet_with(A, [1])
    sheet.set_name(A, "Xs")
    assert sheet.find("xs") == A
    assert sheet.column(A).shown_name == "Xs"


# ----- Conflict Detected (check run 2, E7) -------------------------------------------------------


def test_a_name_that_is_both_a_cell_and_a_variable_asks_first():
    session = Session()
    session.eval("d1:=100")
    sheet = sheet_with(D, [7], session)
    with pytest.raises(ConflictError) as raised:
        sheet.set_cell(E, 1, "=d1+1")
    assert raised.value.names == ("d1",)
    assert raised.value.title == "Conflict Detected"


def test_choosing_the_variable_writes_an_apostrophe():
    session = Session()
    session.eval("d1:=100")
    sheet = sheet_with(D, [7], session)
    sheet.set_cell(E, 1, "=d1+1", choose={"d1": "variable"})
    assert sheet.text(E, 1) == "='d1+1"
    assert sheet.shown(E, 1).text == "101"


def test_choosing_the_cell_keeps_the_reference():
    session = Session()
    session.eval("d1:=100")
    sheet = sheet_with(D, [7], session)
    sheet.set_cell(E, 1, "=d1+1", choose={"d1": "cell"})
    assert sheet.shown(E, 1).text == "8"


def test_entry_contents_are_kept_as_typed():
    sheet = Sheet(Session())
    sheet.set_cell(A, 1, " 2^0.5 ")
    assert sheet.content(A, 1) == Entry("2^0.5")


# ----- smaller paths ------------------------------------------------------------------------------


def test_entry_line_text_for_a_value_from_a_list_and_a_formula_column():
    session = Session()
    session.eval("qq:={1/2,7}")
    sheet = Sheet(session)
    sheet.set_name(A, "qq")
    sheet.set_column_formula(B, "=a[]*2")
    assert sheet.text(A, 1) == "1/2"
    assert sheet.text(B, 2) == "14"
    assert sheet.text(C, 1) == ""


def test_find_an_unlinked_name():
    assert Sheet(Session()).find("xs") is None


@pytest.mark.parametrize(("column", "row"), [(0, 0), (0, 2501), (26, 1)])
def test_off_sheet_cells_are_refused(column, row):
    with pytest.raises(SheetError):
        Sheet(Session()).set_cell(column, row, "1")


@pytest.mark.parametrize("typed", ["1+", "(2"])
def test_an_entry_that_does_not_parse_is_refused(typed):
    with pytest.raises(SheetError):
        Sheet(Session()).set_cell(A, 1, typed)


def test_an_entry_that_is_a_store_shows_err():
    sheet = Sheet(Session())
    sheet.set_cell(A, 1, "k:=5")
    assert sheet.shown(A, 1).text == "#ERR"


def test_an_entry_of_two_statements_is_text():
    sheet = Sheet(Session())
    sheet.set_cell(A, 1, "1:2")
    assert sheet.shown(A, 1).right is False


def test_a_column_formula_replaces_the_cells_it_covers():
    sheet = sheet_with(B, [9, 9, 9])
    sheet.set_cell(B, 4, "=b1+1")
    sheet.set_column_formula(B, "={1,2}")
    assert texts(sheet, B, [1, 2, 3, 4]) == ["1", "2", "", ""]


def test_a_column_formula_that_is_not_a_list_is_an_error():
    sheet = Sheet(Session())
    notices = sheet.set_column_formula(B, "=5")
    assert [n.title for n in notices] == ["Syntax Error in Column: b"]
    assert sheet.shown(B, 1).text == "#ERR"


def test_unlinking_a_column_keeps_the_list_and_the_values():
    session = Session()
    sheet = sheet_with(A, [1, 2], session)
    sheet.set_name(A, "xs")
    sheet.set_name(A, "")
    assert sheet.column(A).name is None
    assert session.eval("xs").text == "{1,2}"
    sheet.set_cell(A, 1, "5")
    assert session.eval("xs").text == "{1,2}"


def test_naming_a_column_after_a_number_is_refused():
    session = Session()
    session.eval("k:=5")
    with pytest.raises(SheetError):
        Sheet(session).set_name(A, "k")


def test_a_range_holding_an_error_is_an_error():
    sheet = sheet_with(A, [1])
    sheet.set_cell(A, 2, "={1,2}")
    sheet.set_cell(B, 1, "=sum(a1:a2)")
    assert sheet.shown(B, 1).text == "#ERR"


def test_a_gap_in_a_linked_list_shows_as_an_empty_element():
    session = Session()
    session.eval("xs:={1,_,3}")
    sheet = Sheet(session)
    sheet.set_name(A, "xs")
    assert texts(sheet, A, [1, 2, 3]) == ["1", "_", "3"]  # check run 2, E12
    assert session.eval("xs").text == "{1,_,3}"


def test_replacing_a_formula_drops_its_old_inputs():
    sheet = sheet_with(A, [1, 2])
    sheet.set_cell(B, 1, "=a1")
    sheet.set_cell(B, 1, "=a2")
    sheet.set_cell(A, 1, "7")
    assert sheet.shown(B, 1).text == "2"


# ----- what the Calculator may store to (check run 2, G4, G9, G14, G20) ---------------------------

VARIABLE_IN_USE = "Cannot accept change, variable in use: Cannot change to requested variable type."


def linked(values=(1, 2, 3)):
    session = Session()
    sheet = sheet_with(A, values, session)
    sheet.set_name(A, "xs")
    return session, sheet


@pytest.mark.parametrize("line", ["xs:=5", 'xs:="hello"', "xs:=[1,2;3,4]", "xs(t):=t"])
def test_a_linked_list_stays_a_list(line):
    session, _ = linked()
    assert session.eval(line).error == VARIABLE_IN_USE
    assert session.eval("xs").text == "{1,2,3}"


@pytest.mark.parametrize("line", ["xs:={4,5}", "xs[1]:=9", 'xs:={1,"x",1/3}', "SortA xs"])
def test_a_linked_list_takes_other_lists(line):
    session, _ = linked()
    assert session.eval(line).error is None


@pytest.mark.parametrize("line", ["sq[1]:=3", "sq:={1,2}", "DelVar sq", "sq:=5"])
def test_a_formula_columns_variable_takes_no_store(line):
    session, sheet = linked()
    sheet.set_name(B, "sq")
    sheet.set_column_formula(B, "=xs^2")
    assert session.eval(line).error == "Cannot accept change: Invalid input."
    assert session.eval("sq").text == "{1,4,9}"


def test_unlinking_frees_the_name():
    session, sheet = linked()
    sheet.set_name(A, "")
    assert session.eval("xs:=5").error is None


def test_clearing_a_column_formula_turns_its_variable_into_a_list():
    session, sheet = linked()
    sheet.set_name(B, "sq")
    sheet.set_column_formula(B, "=xs^2")
    sheet.set_column_formula(B, "")
    assert session.eval("sq:={7}").error is None
    assert session.eval("sq:=7").error == VARIABLE_IN_USE


def test_delvar_of_a_linked_list_unlinks_and_frees_it():
    session, sheet = linked()
    assert session.eval("DelVar xs").error is None
    sheet.sync()
    assert session.eval("xs:=5").error is None


def test_an_empty_linked_column_is_a_list_of_one_empty_element():
    session = Session()
    Sheet(session).set_name(A, "x")
    assert session.eval("x").text == "{_}"


def test_a_stat_variable_cannot_name_a_column():
    with pytest.raises(SheetError) as raised:
        Sheet(Session()).set_name(A, "stat.x")
    assert raised.value.title == "Link Error"
    assert "Stat variable" in raised.value.message


def test_restore_puts_the_locks_back():
    _, sheet = linked()
    saved = sheet.contents(), [sheet.column(c) for c in range(26)]
    other = Session()
    Sheet(other).restore(*saved)
    assert other.eval("xs:=5").error == VARIABLE_IN_USE
