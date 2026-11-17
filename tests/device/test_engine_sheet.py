# Requirements traced here: FR-SHEET-001, FR-SHEET-002, FR-DOC-008
"""Sheets through the engine protocol (slice 3a): `sheet` ops, replies, and the Problem's sheets
kept in step with its variables. The corpus app cases are replayed here as ops, with their
expected values read from the corpus files."""

from pathlib import Path
from typing import cast
from unicodedata import normalize

import pytest
import yaml

from cassim.device.engine import (
    EngineCore,
    EngineError,
    Op,
    RemoteSession,
    check_op,
    check_reply,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    case["id"]: case
    for name in ("016_app_spreadsheet.yaml", "021_app_sheet_sort.yaml", "024_app_sheet_fill.yaml")
    for case in yaml.safe_load((ROOT / "corpus" / "seed" / name).read_text(encoding="utf-8"))[
        "app_cases"
    ]
}
COLUMNS_OF_NOTHING = [[None, None, None]] * 26


def sheet(action, page=2, **args):
    return {"op": "sheet", "page": page, "action": action, "args": args}


def cell(column, row, text, page=2, *, choose=None):
    args = {"column": column, "row": row, "text": text, "choose": choose or {}}
    return sheet("cell", page, **args, confirm=False)


def view(left, top, right, bottom, page=2):
    return sheet("view", page, span=[left, top, right, bottom])


def shown(reply, page=2):
    """The view's cells as {(column, row): shown text}."""
    found = next(s for s in reply["sheets"] if s["page"] == page)
    return {(c, r): text for c, r, text, _, _ in found["cells"]}


def column_texts(reply, column, rows, page=2):
    cells = shown(reply, page)
    return [cells.get((column, row), "") for row in rows]


def error_of(reply):
    error = reply["sheets"][0]["error"]
    assert error is not None
    return error


def expected(case_id, check=0):
    return [str(n) for n in CASES[case_id]["checks"][check]["expect"]]


# ----- the corpus app cases -----------------------------------------------------------------------


def test_formula_column():
    core = EngineCore()
    ops = [cell(0, row, str(v)) for row, v in enumerate([2, 4, 4, 4, 5, 5, 7, 9], start=1)]
    ops += [sheet("formula", column=1, text="=a[]^2", choose={}), view(0, 1, 1, 8)]
    reply = core.apply(1, ops)
    assert column_texts(reply, 1, range(1, 9)) == expected("app.sheet.formula-column")


def test_seq_column():
    core = EngineCore()
    ops = [sheet("formula", column=2, text="=seq(n^2,n,1,8)", choose={}), view(2, 1, 2, 8)]
    assert column_texts(core.apply(1, ops), 2, range(1, 9)) == expected("app.sheet.seq-column")


def test_generate_sequence_recursive():
    core = EngineCore()
    generate = sheet(
        "generate",
        column=0,
        formula="2*u(n-1)+1",
        initial="1",
        first=1,
        last=6,
        step=1,
        ceiling="",
        confirm=False,
    )
    reply = core.apply(1, [generate, view(0, 1, 0, 7)])
    texts = column_texts(reply, 0, range(1, 8))
    assert texts[:6] == expected("app.sheet.generate-sequence-recursive")
    assert texts[6] == ""


def test_sort_column():
    core = EngineCore()
    ops = [cell(0, row, str(v)) for row, v in enumerate([5, 2, 9, 4, 7], start=1)]
    ops += [
        sheet("sort", span=[0, 1, 0, 5], by=0, descending=False, confirm=False),
        view(0, 1, 0, 5),
    ]
    assert column_texts(core.apply(1, ops), 0, range(1, 6)) == expected("app.sheet.sort-column")


def test_fill_down_fibonacci():
    core = EngineCore()
    ops = [cell(0, 1, "1"), cell(0, 2, "1"), cell(0, 3, "=a1+a2")]
    ops += [sheet("fill", source=[0, 3, 0, 3], target=[0, 3, 0, 20]), view(0, 1, 0, 20)]
    reply = core.apply(1, ops)
    assert column_texts(reply, 0, range(3, 21)) == expected("app.sheet.fill-down-fibonacci")


# ----- sharing with the Calculator and other sheets (check run 2, G) ------------------------------


def linked_core():
    core = EngineCore()
    ops = [cell(0, row, str(v)) for row, v in enumerate([1, 2, 3], start=1)]
    core.apply(1, [*ops, sheet("name", column=0, text="xs")])
    return core


def test_a_named_column_is_sent_as_a_variable():
    core = EngineCore()
    reply = core.apply(1, [cell(0, 1, "4"), sheet("name", column=0, text="xs")])
    assert {row["name"]: row["text"] for row in reply["changed"]} == {"xs": "{4}"}


def test_a_calculator_store_reaches_the_sheet_before_the_reply():
    core = linked_core()
    reply = core.apply(1, [{"op": "eval", "line": "xs[2]:=20", "approximate": False}])
    assert reply["result"]["text"] == "20"
    assert reply["sheets"][0]["revision"] > 0
    assert column_texts(core.apply(1, [view(0, 1, 0, 3)]), 0, [1, 2, 3]) == ["1", "20", "3"]


def test_a_type_change_to_a_linked_list_is_refused():
    core = linked_core()
    reply = core.apply(1, [{"op": "eval", "line": "xs:=5", "approximate": False}])
    assert reply["result"]["error"].startswith("Cannot accept change, variable in use")


def test_two_sheets_link_the_same_list():
    core = linked_core()
    core.apply(1, [sheet("name", page=3, column=1, text="xs")])
    reply = core.apply(1, [cell(0, 1, "9"), view(1, 1, 1, 3, page=3)])
    assert column_texts(reply, 1, [1, 2, 3], page=3) == ["9", "2", "3"]


def test_one_sheet_unlinking_keeps_the_lock_another_holds():
    core = linked_core()
    core.apply(1, [sheet("name", page=3, column=1, text="xs"), sheet("name", column=0, text="")])
    reply = core.apply(1, [{"op": "eval", "line": "xs:=5", "approximate": False}])
    assert reply["result"]["error"] is not None
    core.apply(1, [sheet("drop", page=3)])
    reply = core.apply(1, [{"op": "eval", "line": "xs:=5", "approximate": False}])
    assert reply["result"]["error"] is None


def test_a_settings_change_redisplays_the_sheet():
    core = EngineCore()
    core.apply(1, [cell(5, 1, "5"), cell(5, 2, "1/3")])
    reply = core.apply(1, [{"op": "settings", "values": {"calc": "approximate"}}, view(5, 1, 5, 2)])
    assert column_texts(reply, 5, [1, 2]) == ["5.", "0.33333333"]


def test_problems_have_their_own_sheets():
    core = linked_core()
    reply = core.apply(2, [sheet("name", column=0, text="xs"), view(0, 1, 0, 3)])
    assert column_texts(reply, 0, [1, 2, 3]) == ["", "", ""]


# ----- dialogs ------------------------------------------------------------------------------------


def test_a_refused_edit_comes_back_as_an_error():
    reply = EngineCore().apply(1, [cell(8, 5, "=i5")])
    assert reply["sheets"][0]["error"] == {
        "title": "Syntax Error",
        "message": "Circular definition",
        "names": [],
    }


def test_conflict_detected_names_the_choices_and_a_choice_settles_it():
    core = EngineCore()
    core.apply(1, [{"op": "eval", "line": "d1:=100", "approximate": False}])
    reply = core.apply(1, [cell(4, 1, "=d1+1")])
    assert error_of(reply)["names"] == ["d1"]
    reply = core.apply(1, [cell(4, 1, "=d1+1", choose={"d1": "variable"}), view(4, 1, 4, 1)])
    assert reply["sheets"][0]["error"] is None
    assert shown(reply) == {(4, 1): "101"}


def test_a_kept_change_with_a_dialog_comes_back_as_a_notice():
    reply = EngineCore().apply(1, [cell(3, 8, "={1,2}")])
    assert reply["sheets"][0]["notices"] == [
        {"title": "Syntax Error in Cell: d8", "message": "Syntax"}
    ]


def test_data_loss_asks_then_goes_ahead():
    core = EngineCore()
    core.apply(1, [cell(0, 1, "3"), sheet("formula", column=1, text="=a[]", choose={})])
    sort = {"span": [0, 1, 1, 1], "by": 0, "descending": False}
    reply = core.apply(1, [sheet("sort", **sort, confirm=False)])
    assert error_of(reply)["title"] == "Data Loss"
    reply = core.apply(1, [sheet("sort", **sort, confirm=True)])
    assert reply["sheets"][0]["error"] is None


# ----- the view, restore, insert and delete -------------------------------------------------------


def test_view_sends_entry_text_alignment_and_columns():
    core = EngineCore()
    reply = core.apply(1, [cell(0, 1, "pi"), cell(0, 2, "=1+1"), view(0, 1, 0, 2)])
    cells = reply["sheets"][0]["cells"]
    assert cells == [(0, 1, "π", False, "pi"), (0, 2, "2", True, "=1+1")]
    assert len(reply["sheets"][0]["columns"]) == 26


def test_restore_rebuilds_a_saved_sheet():
    columns = [["xs", "xs", None], [None, None, "a[]^2"], *COLUMNS_OF_NOTHING[2:]]
    cells = [[0, 1, "entry", "3"], [0, 2, "formula", "a1+1"]]
    reply = EngineCore().apply(
        1, [sheet("restore", cells=cells, columns=columns), view(0, 1, 1, 2)]
    )
    assert shown(reply) == {(0, 1): "3", (0, 2): "4", (1, 1): "9", (1, 2): "16"}
    assert {row["name"] for row in reply["changed"]} == {"xs"}


@pytest.mark.parametrize(
    ("action", "what", "texts"),
    [
        ("insert", "row", ["1", "", "2"]),
        ("delete", "row", ["1", "3", ""]),
        ("insert", "cell", ["1", "", "2"]),
        ("delete", "cell", ["1", "3", ""]),
    ],
)
def test_insert_and_delete(action, what, texts):
    core = EngineCore()
    core.apply(1, [cell(0, 1, "1"), cell(0, 2, "2"), cell(0, 3, "3")])
    reply = core.apply(1, [sheet(action, what=what, column=0, row=2), view(0, 1, 0, 3)])
    assert column_texts(reply, 0, [1, 2, 3]) == texts


@pytest.mark.parametrize("action", ["insert", "delete"])
def test_insert_and_delete_a_column(action):
    core = EngineCore()
    core.apply(1, [cell(0, 1, "1"), cell(1, 1, "2")])
    reply = core.apply(1, [sheet(action, what="column", column=0, row=1), view(0, 1, 1, 1)])
    assert shown(reply) == ({(1, 1): "1"} if action == "insert" else {(0, 1): "2"})


def test_recalculate_and_a_reset_draw_new_random_numbers():
    core = EngineCore()
    journal = [check_op(cell(0, 1, "=rand()"))]
    first = shown(core.apply(1, [*journal, view(0, 1, 0, 1)]))
    seen = {first[(0, 1)]}
    for _ in range(4):
        seen.add(shown(core.apply(1, [sheet("recalculate"), view(0, 1, 0, 1)]))[(0, 1)])
    core.reset({1: journal})
    seen.add(shown(core.apply(1, [view(0, 1, 0, 1)]))[(0, 1)])
    assert len(seen) > 1


def test_a_reply_without_sheets_has_no_sheet_list():
    assert "sheets" not in EngineCore().apply(
        1, [{"op": "eval", "line": "1", "approximate": False}]
    )


# ----- checking ops and replies -------------------------------------------------------------------


@pytest.mark.parametrize(
    "op",
    [
        {"op": "sheet", "page": 1, "action": "nope", "args": {}},
        {"op": "sheet", "page": "1", "action": "view", "args": {"span": [0, 1, 0, 1]}},
        {"op": "sheet", "page": 1, "action": "view", "args": {"span": [0, 1, 0]}},
        {"op": "sheet", "page": 1, "action": "view", "args": {}},
        {
            "op": "sheet",
            "page": 1,
            "action": "insert",
            "args": {"what": "x", "column": 0, "row": 1},
        },
        {
            "op": "sheet",
            "page": 1,
            "action": "cell",
            "args": {"column": True, "row": 1, "text": "", "choose": {}},
        },
        {
            "op": "sheet",
            "page": 1,
            "action": "formula",
            "args": {"column": 0, "text": "", "choose": {"d1": "both"}},
        },
        {
            "op": "sheet",
            "page": 1,
            "action": "restore",
            "args": {"cells": [[0, 1, "x", "1"]], "columns": []},
        },
        {
            "op": "sheet",
            "page": 1,
            "action": "restore",
            "args": {"cells": [], "columns": [[1, None, None]]},
        },
    ],
)
def test_bad_sheet_ops_are_refused(op):
    with pytest.raises(EngineError):
        check_op(op)


def test_a_reply_with_sheets_checks():
    reply = EngineCore().apply(1, [cell(0, 1, "1"), view(0, 1, 0, 1)])
    assert check_reply(reply)["sheets"] == reply["sheets"]
    with pytest.raises(EngineError):
        check_reply({**reply, "sheets": [{"page": 1}]})


# ----- what the page keeps: edits, put, move, compact (slice 3b) ----------------------------------


def test_replies_carry_the_definitions_that_changed():
    core = EngineCore()
    reply = core.apply(1, [cell(0, 1, "5"), cell(0, 2, "=a1*2")])
    assert reply["sheets"][0]["edits"] == [(0, 1, "entry", "5"), (0, 2, "formula", "a1*2")]
    reply = core.apply(1, [cell(0, 1, "")])
    assert reply["sheets"][0]["edits"] == [(0, 1, "", "")]


def test_a_list_stored_from_the_calculator_comes_back_as_cell_edits():
    core = linked_core()
    reply = core.apply(1, [{"op": "eval", "line": "xs:={1/2,7}", "approximate": False}])
    assert reply["sheets"][0]["edits"] == [
        (0, 1, "entry", "1/2"),
        (0, 2, "entry", "7"),
        (0, 3, "", ""),
    ]


def test_columns_are_sent_when_they_change():
    core = EngineCore()
    reply = core.apply(1, [sheet("name", column=0, text="Xs")])
    assert reply["sheets"][0]["columns"][0] == ("xs", "Xs", None)
    assert core.apply(1, [cell(1, 1, "1")])["sheets"][0]["columns"] == []


def test_put_sets_and_clears_cells():
    core = EngineCore()
    cells = [[0, 1, "entry", "3"], [0, 2, "formula", "a1+1"]]
    core.apply(1, [sheet("put", cells=cells, confirm=False)])
    reply = core.apply(
        1, [sheet("put", cells=[[0, 1, "entry", ""]], confirm=False), view(0, 1, 0, 2)]
    )
    assert shown(reply) == {(0, 2): "_"}  # a blank cell read by a formula is `_` (a guess)


def test_move_a_column():
    core = EngineCore()
    core.apply(1, [cell(1, 1, "4")])
    reply = core.apply(1, [sheet("move", column=1, to=3), view(0, 1, 3, 1)])
    assert shown(reply) == {(3, 1): "4"}


def test_a_view_taken_before_a_change_in_the_same_batch_is_not_sent():
    reply = EngineCore().apply(1, [view(0, 1, 0, 1), cell(0, 1, "8")])
    assert reply["sheets"][0]["span"] == []


def test_compact_keeps_one_op_per_sheet_where_its_last_was():
    session = RemoteSession(0)
    entry = {"op": "eval", "line": "a:=1", "approximate": False}
    other = cell(0, 1, "1", page=3)
    session.journal = cast("list[Op]", [cell(0, 1, "1"), entry, cell(0, 2, "2"), other])
    restore = sheet("restore", cells=[], columns=[])
    session.compact(2, restore)
    assert session.journal == [entry, restore, other]
    session.compact(9, restore)  # a page with nothing in the journal
    assert len(session.journal) == 3


# ----- Stat Calculations: the statistics corpus app cases (slice 3c) -----------------------------

# The corpus names each check in words; these are the labels the results carry.
LABELS = {
    "mean x": "x̄",
    "sum x": "Σx",
    "sum x^2": "Σx²",
    "sx (sample sd)": "sx := sn-1x",
    "sx": "sx := sn-1x",
    "sigma x (population sd)": "σx := σnx",
    "sigma x": "σx := σnx",
    "mean y": "ȳ",
    "sum y": "Σy",
    "sum y^2": "Σy²",
    "sy": "sy := sn-1y",
    "sigma y": "σy := σny",
    "sum xy": "Σxy",
    "Q1X": "Q₁X",
    "Q3X": "Q₃X",
    "Q1Y": "Q₁Y",
    "Q3Y": "Q₃Y",
    "SSX": "SSX := Σ(x-x̄)²",
    "SSY": "SSY := Σ(y-ȳ)²",
    "r^2": "r²",
}


def stat(command, lists, column, **fields):
    args = {"freq": "1", "category": "", "include": "", "save": "", "choose": {}}
    return sheet(
        "stat", command=command, lists=lists, column=column, confirm=False, **{**args, **fields}
    )


def inference(formula, column):
    return sheet(
        "inference",
        formula=formula,
        column=column,
        choose={},
        confirm=False,
    )


def results_of(reply, column):
    """{label: value} from a view of the label column and the value column after it."""
    cells = shown(reply)
    rows = sorted(r for c, r in cells if c == column)
    # NFC: a label such as ȳ may be one character or y and a combining macron
    return {normalize("NFC", cells[(column, r)]): cells.get((column + 1, r), "") for r in rows}


def check_case(case_id, found):
    for check in CASES[case_id]["checks"]:
        label = normalize("NFC", LABELS.get(check["what"], check["what"]))
        tolerance = check.get("tol", 1e-9)
        assert float(found[label]) == pytest.approx(check["expect"], abs=tolerance), label


def a_and_c(core):
    """A1:A8 = 2,4,4,4,5,5,7,9 and C1:C8 = n^2, as the cases set them up."""
    ops = [cell(0, row, str(v)) for row, v in enumerate([2, 4, 4, 4, 5, 5, 7, 9], start=1)]
    ops += [cell(2, row, str(row * row)) for row in range(1, 9)]
    core.apply(1, ops)


def test_one_variable_statistics():
    """Corpus app.sheet.one-variable-statistics: X1 List a[], 1st Result Column e[]."""
    core = EngineCore()
    a_and_c(core)
    reply = core.apply(1, [stat("OneVar", ["a[]"], 4), view(4, 1, 5, 14)])
    check_case("app.sheet.one-variable-statistics", results_of(reply, 4))


def test_two_variable_statistics():
    """Corpus app.sheet.two-variable-statistics: X a[], Y c[], 1st Result Column h[]."""
    core = EngineCore()
    a_and_c(core)
    reply = core.apply(1, [stat("TwoVar", ["a[]", "c[]"], 7), view(7, 1, 8, 27)])
    check_case("app.sheet.two-variable-statistics", results_of(reply, 7))


def test_linear_regression():
    """Corpus app.sheet.linear-regression: X a[], Y c[], RegEqn to f1, 1st Result Column k[]."""
    core = EngineCore()
    a_and_c(core)
    reply = core.apply(1, [stat("LinRegMx", ["a[]", "c[]"], 10, save="f1"), view(10, 1, 11, 8)])
    check_case("app.sheet.linear-regression", results_of(reply, 10))
    reply = core.apply(1, [{"op": "eval", "line": "f1(2)", "approximate": False}])
    assert reply["result"] is not None
    assert float(reply["result"]["text"]) == pytest.approx(10.0625 * 2 - 24.8125)


def test_inference_result_columns_run_through_the_engine():
    core = EngineCore()
    ops = [cell(0, row, str(value)) for row, value in enumerate([1, 2, 3, 4], start=1)]
    ops += [inference("tInterval a[],1,.95", 4), view(4, 1, 5, 6)]
    reply = core.apply(1, ops)
    assert column_texts(reply, 4, [1, 2, 3]) == ["Title", "x̄", "CLower"]
    assert column_texts(reply, 5, [1, 2, 3]) == ["t Interval", "2.5", "0.44573974"]
