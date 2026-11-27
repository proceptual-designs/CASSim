# Requirements traced here:
# FR-SHEET-001 to 008, FR-STAT-001, FR-STAT-004, FR-DOC-009, FR-DOC-008, FR-DOC-003, FR-DOC-010
"""The Lists & Spreadsheet page model (slice 3b), driven by keys and menu items as the app drives
it. Behaviour from emulator check 6 part E and check run 2 (G, E finish rows)."""

import asyncio
import json

import pytest

from cassim.device.editor import MARK, Kind, Template
from cassim.device.engine import LocalEngine
from cassim.device.keys import Binding
from cassim.devices.nspire.document import loads
from cassim.devices.nspire.pages import PAGES
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.pages.spreadsheet import (
    DEFAULT_WIDTH,
    FORMULA_ROW,
    NAME_ROW,
    ROWS,
    WIDE,
    AreaPane,
    ShadePane,
    Spreadsheet,
    _sheet_text,
    _shift_entry_nodes,
    dump,
    load,
    pane_boxes,
    spreadsheet_of,
)
from cassim.devices.nspire.pages.statistics import Statistics
from cassim.devices.nspire.runner import Runner
from cassim.devices.nspire.screen import thumbnail
from cassim.devices.nspire.sheet_inference import RHO
from cassim.devices.nspire.ui.state import AppState
from cassim.doc.serialize import DocumentFileError, dumps
from cassim.sheet.fileio import FileCell

A, B, C, D, E, F, G, H, _, J = range(10)


class Recording(AppState):
    """An app state that keeps the dialogs it was asked to open."""

    def __init__(self, document=None, **options) -> None:
        super().__init__(document, **options)
        self.wizards: list = []
        self.show_wizard = self.wizards.append


def sheet_app(state=None):
    """An app with a Calculator page 1.1 and a sheet page 1.2, on the sheet."""
    state = state or Recording()
    state.run_action("add_page", "spreadsheet")
    return state


def sheet_of(state) -> Spreadsheet:
    sheet = state.sheet
    assert sheet is not None
    return sheet


def keys(state, *names):
    for name in names:
        if len(name) == 1 or name.startswith("="):
            state.run(Binding("insert", name))
        else:
            state.run(Binding(name))


def type_cell(state, text):
    state.run(Binding("insert", text))
    state.run(Binding("enter"))


def shown(state, column, row):
    sheet = sheet_of(state)
    state.prepare()
    cell = sheet.view.get((column, row))
    return "" if cell is None else cell.text


def column(state, col, rows):
    return [shown(state, col, row) for row in rows]


def finish_wizard(state, **values):
    wizard = state.wizards.pop()
    state.finish_wizard(wizard, {**wizard.defaults(), **values})


# ----- typing -------------------------------------------------------------------------------------


def test_enter_puts_a_value_in_and_moves_down():
    """Run 2, E4: typing 7, Return, 8, Return, 9, Return fills C1:C3."""
    state = sheet_app()
    for value in ("7", "8", "9"):
        type_cell(state, value)
    assert column(state, A, [1, 2, 3]) == ["7", "8", "9"]
    assert sheet_of(state).cursor == (A, 4)


def test_typing_edits_with_a_caret_and_escape_cancels():
    state = sheet_app()
    keys(state, "1", "2", "left", "backspace", "3")  # 12, then 32
    sheet = sheet_of(state)
    assert sheet.editing == "32"
    keys(state, "escape")
    assert sheet.editing is None
    assert shown(state, A, 1) == ""


def test_enter_on_a_filled_cell_edits_what_it_holds():
    state = sheet_app()
    type_cell(state, "=1+1")
    keys(state, "up", "enter")
    assert sheet_of(state).editing == "=1+1"


def test_the_bar_shows_the_cell_name_and_its_content():
    state = sheet_app()
    type_cell(state, "=2*3")
    keys(state, "up")
    screen = sheet_of(state).screen()
    assert (screen.address, screen.entry) == ("A1", "=2*3")
    assert screen.cells[(A, 1)] == ("6", True)


def test_formula_arrows_select_references_and_keep_the_destination():
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "7")
    sheet.go((B, 1))
    keys(state, "=", "left")
    assert (sheet.cursor, sheet.editing, sheet.screen().reference) == ((B, 1), "=a1", (A, 1, A, 1))
    keys(state, "+", "left", "down")
    assert sheet.editing == "=a1+a2"
    keys(state, "enter")
    assert sheet.entry_text((B, 1)) == "=a1+a2"
    assert sheet.entry_text((A, 1)) == "7"


def test_formula_range_by_arrow_and_mouse():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((C, 1))
    state.run(Binding("insert", "=sum("))
    keys(state, "left")
    state.run(Binding("select_cells", "row:2"))
    assert sheet.editing == "=sum(b1:b3"
    assert sheet.screen().reference == (B, 1, B, 3)
    state.run(Binding("sheet_tap", "0,1"))
    state.run(Binding("sheet_tap", "0,3,extend"))
    assert sheet.editing == "=sum(a1:a3"
    keys(state, ")", "enter")
    assert sheet.entry_text((C, 1)) == "=sum(a1:a3)"


def test_pointing_after_a_comparison_but_not_inside_a_string():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    state.run(Binding("insert", "=2>"))
    keys(state, "left")
    assert sheet.editing == "=2>a1"
    keys(state, "escape")
    state.run(Binding("insert", '="a+'))
    keys(state, "left")
    assert sheet.editing == '="a+'
    assert sheet.caret == 3


def test_quoted_formula_text_keeps_power_symbols_and_does_not_point_on_tap():
    """FR-SHEET-008: quoted text is not a spreadsheet reference or a maths template."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    state.run(Binding("insert", '="a^2"'))
    assert sheet.editing == '="a^2"'
    keys(state, "left")
    state.run(Binding("sheet_tap", "0,1"))
    assert sheet.reference is None
    assert sheet.entry_text((B, 1)) == '="a^2"'
    assert sheet.cursor == (A, 1)


def test_pasting_formula_text_preserves_quoted_powers_and_spaces():
    state = sheet_app()
    state.run(Binding("insert", "="))
    state.run(Binding("paste", '"a  ^2"'))
    assert sheet_of(state).editing == '="a  ^2"'


def test_point_mode_cannot_be_enabled_inside_a_quoted_formula():
    """FR-SHEET-008: forcing point mode still leaves quoted text alone."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    state.run(Binding("insert", '="a+"'))
    keys(state, "left")
    assert state.key_event("F2")
    keys(state, "left")
    assert sheet.editing == '="a+"'
    assert sheet.reference is None


def test_clicking_a_cell_where_a_reference_is_not_accepted_commits_the_formula():
    """FR-SHEET-008: a click only points when the caret accepts a reference."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    state.run(Binding("insert", "=12"))
    state.run(Binding("sheet_tap", "0,1"))
    assert sheet.entry_text((B, 1)) == "=12"
    assert sheet.cursor == (A, 1)
    assert sheet.reference is None


def test_formula_point_mode_can_be_toggled_and_fixed_references_cycled():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 2))
    keys(state, "=", "left")
    assert sheet.editing == "=a2"
    for expected in ("=$a$2", "=a$2", "=$a2", "=a2"):
        assert state.key_event("F4")
        assert sheet.editing == expected
    assert state.key_event("F4")
    keys(state, "up")
    assert sheet.editing == "=$a$1"
    for _ in range(3):
        assert state.key_event("F4")
    assert state.key_event("F2")
    keys(state, "left")
    assert sheet.caret == 2
    assert sheet.cursor == (B, 2)
    assert state.key_event("F2")
    keys(state, "down")
    assert sheet.editing == "=a2"
    keys(state, "escape")
    assert sheet.entry_text((B, 2)) == ""


def test_shift_arrow_while_editing_cannot_write_into_another_cell():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, 2))
    type_cell(state, "9")
    sheet.go((B, 2))
    state.run(Binding("insert", "=2"))
    state.run(Binding("select_left"))
    keys(state, "enter")
    assert sheet.entry_text((A, 2)) == "9"
    assert sheet.entry_text((B, 2)) == "=2"


def test_shift_arrow_selects_text_when_not_pointing():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("insert", "=12"))
    state.run(Binding("select_left"))
    assert sheet.screen().edit_selection == (2, 3)
    state.run(Binding("insert", "3"))
    assert sheet.editing == "=13"
    state.run(Binding("select_all"))
    state.run(Binding("insert", "=4"))
    keys(state, "enter")
    assert sheet.entry_text((A, 1)) == "=4"


def test_copy_cut_and_paste_selected_formula_text():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("insert", "=123"))
    state.run(Binding("select_left"))
    state.run(Binding("select_left"))
    state.run(Binding("copy"))
    assert state.document.clipboard.text == "23"
    state.run(Binding("cut"))
    assert sheet.editing == "=1"
    state.run(Binding("paste"))
    assert sheet.editing == "=123"


def test_deleting_a_pointed_reference_removes_it_as_a_unit():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    state.run(Binding("insert", "=2+"))
    keys(state, "left", "backspace")
    assert sheet.editing == "=2+"
    assert sheet.cursor == (B, 1)


def test_clicking_bar_edits_existing_formula_without_replacing_it():
    state = sheet_app()
    type_cell(state, "=2+3")
    keys(state, "up")
    state.run(Binding("sheet_bar"))
    sheet = sheet_of(state)
    assert (sheet.editing, sheet.caret, sheet.selected) == ("=2+3", 4, False)
    state.run(Binding("insert", "+1"))
    keys(state, "enter")
    assert sheet.entry_text((A, 1)) == "=2+3+1"


def test_fraction_template_points_to_a_cell_inside_its_denominator():
    """FR-SHEET-001: structured slots retain spreadsheet reference pointing."""
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "2")
    sheet.go((B, 1))
    state.run(Binding("insert", "=1"))
    state.run(Binding("template", "fraction"))
    keys(state, "left")
    assert sheet.editing == "=((1)/(a1))"
    assert sheet.screen().reference == (A, 1, A, 1)
    state.run(Binding("sheet_ref_fixed"))
    assert sheet.editing == "=((1)/($a$1))"
    state.run(Binding("insert", "+1"))
    keys(state, "right")
    state.run(Binding("insert", "+1"))
    keys(state, "enter")
    assert shown(state, B, 1) == "4/3"


def test_copying_a_spreadsheet_template_preserves_it_on_the_calculator():
    """FR-SHEET-001: the shared clipboard keeps structured templates between pages."""
    state = sheet_app()
    state.run(Binding("insert", "=1"))
    state.run(Binding("template", "fraction"))
    state.run(Binding("insert", "2"))
    state.run(Binding("select_all"))
    state.run(Binding("copy"))
    state.run_action("prev_page")
    state.run(Binding("paste"))
    calculator = calculator_on(state.document.current)
    assert any(
        isinstance(node, Template) and node.kind is Kind.FRACTION for node in calculator.editor.root
    )


def test_sheet_template_is_preserved_when_reopened_and_after_save():
    """FR-DOC-003: a saved formula reopens with its structured editor nodes."""
    state = sheet_app()
    state.run(Binding("insert", "=1"))
    state.run(Binding("template", "fraction"))
    state.run(Binding("insert", "2"))
    state.run(Binding("enter"))
    state.run(Binding("up"))
    state.run(Binding("sheet_bar"))
    sheet = sheet_of(state)
    assert sheet.editor is not None
    assert any(
        isinstance(node, Template) and node.kind is Kind.FRACTION for node in sheet.editor.root
    )
    state.run(Binding("escape"))

    restored = Recording(loads(dumps(state.document)))
    restored.run(Binding("sheet_bar"))
    sheet = sheet_of(restored)
    assert sheet.editor is not None
    assert any(
        isinstance(node, Template) and node.kind is Kind.FRACTION for node in sheet.editor.root
    )


def test_formula_column_template_survives_normalisation_and_reload():
    """FR-DOC-003: an implicit leading equals does not discard the template."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, FORMULA_ROW))
    state.run(Binding("insert", "1"))
    state.run(Binding("template", "fraction"))
    state.run(Binding("insert", "2"))
    keys(state, "enter")
    assert sheet.entry_text((B, FORMULA_ROW)) == "=((1)/(2))"
    restored = Recording(loads(dumps(state.document)))
    restored_sheet = sheet_of(restored)
    restored_sheet.go((B, FORMULA_ROW))
    restored.run(Binding("sheet_bar"))
    assert restored_sheet.editor is not None
    assert any(isinstance(node, Template) for node in restored_sheet.editor.root)


def test_invalid_saved_template_metadata_is_rejected():
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "=1")
    saved = dump(sheet)
    saved["entry_nodes"] = [[A, 1, [{"kind": "matrix", "slots": ["1"], "cols": 0}]]]
    with pytest.raises(DocumentFileError, match="template shape"):
        load(sheet, saved)


def test_rejected_structured_formula_keeps_its_template():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, 5))
    state.run(Binding("insert", "=a5+1"))
    state.run(Binding("template", "fraction"))
    state.run(Binding("insert", "2"))
    keys(state, "enter")
    assert sheet.screen().dialog is not None
    assert sheet.editor is not None
    assert any(isinstance(node, Template) for node in sheet.editor.root)


def test_undo_restores_the_original_structured_entry():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("insert", "=1"))
    state.run(Binding("template", "fraction"))
    state.run(Binding("insert", "2"))
    keys(state, "enter", "up")
    type_cell(state, "=3")
    keys(state, "undo")
    sheet.go((A, 1))
    state.run(Binding("sheet_bar"))
    assert sheet.editor is not None
    assert any(isinstance(node, Template) for node in sheet.editor.root)


def test_power_followed_by_a_term_preserves_its_exponent_boundary():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("insert", "=2"))
    state.run(Binding("power", "2"))
    keys(state, "right")
    state.run(Binding("insert", "*3"))
    keys(state, "enter")
    assert shown(state, A, 1) == "12"
    assert sheet.entry_text((A, 1)) == "=2^2*3"


def test_caret_after_a_power_does_not_change_its_serialisation():
    state = sheet_app()
    state.run(Binding("insert", "=2"))
    state.run(Binding("power", "2"))
    keys(state, "right")
    sheet = sheet_of(state)
    assert sheet.editing == "=2^2"
    assert sheet.screen().editing == f"=2^2{MARK}"


def test_a_formula_column():
    """Corpus app.sheet.formula-column: =a[]^2 in B's formula row."""
    state = sheet_app()
    for value in (2, 4, 4, 4, 5, 5, 7, 9):
        type_cell(state, str(value))
    sheet = sheet_of(state)
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=a[]^2")
    sheet.go((B, 1))
    assert column(state, B, range(1, 6)) == ["4", "16", "16", "16", "25"]
    assert sheet.entry_text((B, FORMULA_ROW)) == "=a[]^2"
    assert sheet.screen().columns[1][3] == "a[]^2"


def test_naming_a_column_links_it_to_the_calculator():
    state = sheet_app()
    type_cell(state, "1")
    type_cell(state, "2")
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    assert sheet.columns[A][1] == "xs"
    sheet.go((A, NAME_ROW))
    assert sheet.screen().address == "A"
    state.run_action("prev_page")
    calculator = calculator_on(state.document.current)
    calculator.session.eval("xs[2]:=20")
    state.run_action("next_page")
    assert column(state, A, [1, 2]) == ["1", "20"]


# ----- dialogs ------------------------------------------------------------------------------------


def test_a_refused_formula_shows_its_dialog_and_goes_back_to_editing():
    """Check 6, E6: =i5 in I5 is circular; after OK the cell is still being edited."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, 5))
    type_cell(state, "=a5")
    dialog = sheet.screen().dialog
    assert dialog is not None
    assert (dialog.title, dialog.message) == ("Syntax Error", "Circular definition")
    keys(state, "enter")  # OK
    assert sheet.editing == "=a5"
    assert sheet.cursor == (A, 5)


def test_a_kept_change_with_a_dialog():
    state = sheet_app()
    type_cell(state, "={1,2}")
    sheet = sheet_of(state)
    assert sheet.dialogs[0].title == "Syntax Error in Cell: a1"
    keys(state, "escape")
    assert not sheet.dialogs
    assert shown(state, A, 1) == "#ERR"


def test_conflict_detected_asks_cell_or_variable():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.session.eval("d1:=100")
    sheet.go((D, 1))
    type_cell(state, "7")
    sheet.go((E, 1))
    type_cell(state, "=d1+1")
    wizard = state.wizards[-1]
    assert wizard.title == "Conflict Detected"
    assert wizard.fields[0].label == "d1 :  Cell or Variable?"
    finish_wizard(state, d1="variable")
    assert shown(state, E, 1) == "101"
    assert sheet.entry_text((E, 1)) == "='d1+1"


def test_sort_asks_before_a_formula_column_then_sorts():
    """Check 6, E18."""
    state = sheet_app()
    sheet = sheet_of(state)
    for value in (9, 3, 7, 1):
        type_cell(state, str(value))
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=a[]*2")
    sheet.go((A, 1))
    for _ in range(3):
        state.run(Binding("select_cells", "row:1"))
    state.run(Binding("select_cells", "col:1"))
    assert sheet.screen().address == "A1:B4"
    state.run(Binding("sheet", "sort"))
    finish_wizard(state)
    assert sheet.dialogs[0].title == "Data Loss"
    keys(state, "enter")  # OK
    assert column(state, A, [1, 2, 3, 4]) == ["1", "3", "7", "9"]
    assert column(state, B, [1, 2, 3, 4]) == ["2", "6", "14", "18"]


def test_sort_needs_a_block():
    state = sheet_app()
    state.run(Binding("sheet", "sort"))
    assert not state.wizards


def test_data_loss_cancel_does_nothing():
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "5")
    sheet.go((A, 1))
    state.run(Binding("sheet", "generate"))
    finish_wizard(state, formula="n", last="3")
    assert sheet.dialogs[0].title == "Data Loss"
    keys(state, "escape")
    assert column(state, A, [1, 2]) == ["5", ""]


def test_generate_sequence():
    """Corpus app.sheet.generate-sequence-recursive."""
    state = sheet_app()
    state.run(Binding("sheet", "generate"))
    wizard = state.wizards[-1]
    assert [f.label for f in wizard.fields] == [
        "Formula: u(n)=",
        "Initial Terms",
        "n0",
        "nMax",
        "nStep",
        "Ceiling Value",
    ]
    finish_wizard(state, formula="2*u(n-1)+1", initial="1", last="6")
    assert column(state, A, range(1, 6)) == ["1", "3", "7", "15", "31"]


# ----- Fill, Go To, scrolling ---------------------------------------------------------------------


def test_fill_down_fibonacci():
    """Corpus app.sheet.fill-down-fibonacci: A3 =a1+a2, Fill, Down to A20, Enter."""
    state = sheet_app()
    for value in ("1", "1", "=a1+a2"):
        type_cell(state, value)
    sheet = sheet_of(state)
    sheet.go((A, 3))
    state.run(Binding("sheet", "fill"))
    for _ in range(17):
        keys(state, "down")
    assert sheet.screen().marker == (A, 3, A, 20)
    keys(state, "enter")
    sheet.go((A, 20))
    assert shown(state, A, 20) == "6765"
    assert sheet.entry_text((A, 20)) == "=a18+a19"


def test_go_to_a_cell_scrolls_as_little_as_it_can():
    """Run 2, G39: Go To h40 shows rows 36 to 40 with the cursor on H40."""
    state = sheet_app()
    keys(state, "goto")
    finish_wizard(state, ref="h40")
    sheet = sheet_of(state)
    assert sheet.cursor == (H, 40)
    assert (sheet.top, sheet.left) == (36, 4)


def test_go_to_a_list_selects_its_column_and_a_bad_reference_says_so():
    """Check 6, E10, E11; run 2, E24."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    keys(state, "goto")
    finish_wizard(state, ref="xs")
    assert sheet.whole == "column"
    for bad in ("k", "a2501", "aa1"):
        keys(state, "goto")
        finish_wizard(state, ref=bad)
        assert sheet.dialogs.pop().message == "Invalid reference. Please try again."


def test_page_keys_and_the_last_filled_cell():
    """Check 6, E10: PageUp from B10 goes to B6; ctrl+1 goes to the column's last cell."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 10))
    keys(state, "page_up")
    assert sheet.cursor == (B, 6)
    keys(state, "page_down")
    assert sheet.cursor == (B, 10)
    sheet.go((C, 1))
    for value in ("1", "2", "3"):
        type_cell(state, value)
    sheet.go((C, 1))
    keys(state, "last_line")
    assert sheet.cursor == (C, 3)
    keys(state, "first_line")
    assert sheet.cursor == (C, 1)


def test_taps_select_and_a_drag_scrolls():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("sheet_tap", "2,3"))
    state.run(Binding("sheet_tap", "3,4,extend"))
    assert sheet.screen().address == "C3:D4"
    state.run(Binding("sheet_drag", "0,10"))
    assert sheet.top == 11


def test_a_tap_elsewhere_enters_what_was_typed():
    state = sheet_app()
    keys(state, "4")
    state.run(Binding("sheet_tap", "1,1"))
    assert shown(state, A, 1) == "4"
    assert sheet_of(state).cursor == (B, 1)


# ----- clipboard, Del, undo -----------------------------------------------------------------------


def test_copy_and_paste_move_formulas():
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("1", "2", "3"):
        type_cell(state, value)
    sheet.go((B, 1))
    type_cell(state, "=a1*10")
    sheet.go((B, 1))
    keys(state, "copy")
    sheet.go((B, 3))
    keys(state, "paste")
    assert shown(state, B, 3) == "30"
    assert sheet.entry_text((B, 3)) == "=a3*10"


def test_copying_a_structured_formula_shifts_references_and_preserves_templates():
    """FR-SHEET-001: copied formulae retain their editor structure and relative references."""
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "2")
    type_cell(state, "4")
    sheet.go((B, 1))
    state.run(Binding("insert", "=a1"))
    state.run(Binding("template", "fraction"))
    state.run(Binding("insert", "2"))
    keys(state, "enter")
    sheet.go((B, 1))
    keys(state, "copy")
    sheet.go((B, 2))
    keys(state, "paste")
    assert shown(state, B, 2) == "2"
    assert sheet.entry_text((B, 2)) == "=((a2)/(2))"
    state.run(Binding("sheet_bar"))
    assert sheet.editor is not None
    assert isinstance(sheet.editor.root[1], Template)
    assert sheet.editor.root[1].slots[0] == list("a2")


def test_shifting_nested_structured_references_keeps_strings_and_fixed_parts():
    nodes = [
        *'="a1"+',
        Template(
            Kind.FRACTION,
            [
                list("$a1+b$2"),
                [Template(Kind.NTH_ROOT, [list("2"), list("c3")])],
            ],
        ),
    ]
    shifted = _shift_entry_nodes(nodes, 1, 2)
    assert shifted is not None
    assert _sheet_text(shifted) == '="a1"+(($a3+c$2)/(root(d5,2)))'
    assert _sheet_text(nodes) == '="a1"+(($a1+b$2)/(root(c3,2)))'
    assert _shift_entry_nodes(nodes, -3, 0) is None


def test_cut_and_undo():
    """Check 6, E11: cut empties the cells, ctrl+Z brings them back."""
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("7", "8", "9"):
        type_cell(state, value)
    sheet.go((A, 1))
    state.run(Binding("select_cells", "row:2"))
    keys(state, "cut")
    assert column(state, A, [1, 2, 3]) == ["", "", ""]
    keys(state, "undo")
    assert column(state, A, [1, 2, 3]) == ["7", "8", "9"]
    keys(state, "redo")
    assert column(state, A, [1, 2, 3]) == ["", "", ""]


def test_undo_with_nothing_left_undoes_the_page_insert():
    state = sheet_app()
    assert len(state.document.problems[0].pages) == 2
    keys(state, "undo")
    assert len(state.document.problems[0].pages) == 1


def test_a_name_cell_cannot_be_pasted_into_cells():
    """Check 6, E11: "Cannot Paste"."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    sheet.go((A, NAME_ROW))
    keys(state, "copy")
    sheet.go((C, 1))
    keys(state, "paste")
    assert sheet.dialogs[0].title == "Cannot Paste"


def test_pasting_whole_rows_over_data_asks_first():
    """Check 6, E11: a copied row pasted over data gives Data Loss."""
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("1", "2", "3", "4", "5"):
        type_cell(state, value)
    sheet.go((A, 1))
    state.run(Binding("sheet", "select_row"))
    keys(state, "copy")
    sheet.go((A, 5))
    keys(state, "paste")
    assert sheet.dialogs[0].title == "Data Loss"
    keys(state, "enter")
    assert shown(state, A, 5) == "1"


def test_text_from_elsewhere_pastes_as_cells():
    state = sheet_app()
    state.run(Binding("paste", "1\t2\n3\t=a1+b1"))
    assert column(state, B, [1, 2]) == ["2", "3"]


def test_del_clears_cells_a_name_and_a_formula():
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "4")
    sheet.go((A, 1))
    keys(state, "delete")
    assert shown(state, A, 1) == ""
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    sheet.go((A, NAME_ROW))
    keys(state, "delete")
    assert sheet.columns[A][1] is None
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=seq(n,n,1,3)")
    sheet.go((B, FORMULA_ROW))
    keys(state, "delete")
    assert sheet.columns[B][2] is None
    assert column(state, B, [1, 2, 3]) == ["1", "2", "3"]  # the values stay (run 2, E20)


# ----- the Menu -----------------------------------------------------------------------------------


def test_the_menu_and_context_menus():
    state = sheet_app()
    keys(state, "open_menu")
    state.run(Binding("open_menu", "menu"))
    assert state.menu is not None
    assert [row.label for row in state.menu.view().rows][:5] == [
        "Actions",
        "Insert",
        "Data",
        "Statistics",
        "Table",
    ]
    state.menu = None
    state.press_keypad("ctrl")
    state.press_keypad("menu")
    assert state.menu is not None
    assert state.menu.view().title.startswith("Cell")
    state.menu = None
    state.run(Binding("select_cells", "row:1"))
    keys(state, "context_menu")
    assert state.menu is not None
    assert state.menu.view().title.startswith("Cells")


def test_menu_numbers_reach_the_items():
    """Menu 2 2 is Insert Row (check 6, E12)."""
    state = sheet_app()
    for value in ("1", "2"):
        type_cell(state, value)
    sheet_of(state).go((A, 1))
    state.run(Binding("open_menu", "menu"))
    state.run(Binding("insert", "2"))
    state.run(Binding("insert", "2"))
    assert column(state, A, [1, 2, 3]) == ["", "1", "2"]


def test_list_math_writes_the_function_in_the_formula_row():
    """Check 6, E14: List Math > Mean puts =mean( in the formula row, cursor inside."""
    state = sheet_app()
    state.run(Binding("sheet", "formula:=mean("))
    sheet = sheet_of(state)
    assert sheet.cursor == (A, FORMULA_ROW)
    assert sheet.editing == "=mean("


def test_insert_and_delete_from_the_menu():
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("1", "2", "3"):
        type_cell(state, value)
    sheet.go((A, 2))
    state.run(Binding("sheet", "delete_row"))
    assert column(state, A, [1, 2, 3]) == ["1", "3", ""]
    state.run(Binding("sheet", "insert_column"))
    assert column(state, B, [1, 2]) == ["1", "3"]


def test_move_column_and_resize():
    """Check 6, E12 (Move Column) and E13 (resize)."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    type_cell(state, "4")
    sheet.go((B, 1))
    state.run(Binding("sheet", "move_column"))
    keys(state, "right", "enter")
    assert column(state, C, [1]) == ["4"]
    assert sheet.cursor == (C, 1)
    state.run(Binding("sheet", "resize"))
    keys(state, "right", "right", "enter")
    assert sheet.width(C) == DEFAULT_WIDTH + 24
    state.run(Binding("sheet", "maximize"))
    assert sheet.width(C) == WIDE


def test_var_on_a_name_cell_links_to_a_list():
    """Check 6, E7: var on a linked name cell: Store Var, Unlink, Link To ▶ the lists."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.session.eval("qq:={7,8,9}")
    sheet.session.eval("pp:={1}")
    sheet.go((C, NAME_ROW))
    state.run(Binding("sheet", "link:pp"))
    state.run(Binding("open_menu", "variables"))
    assert [row.label for row in state.menu.view().rows] == ["Store Var", "Unlink", "Link To:"]
    state.menu = None
    state.run(Binding("sheet", "link:qq"))
    assert column(state, C, [1, 2, 3]) == ["7", "8", "9"]


def test_sheet_keys_do_nothing_on_a_calculator_page():
    state = AppState()
    for action in ("goto", "recalculate", "page_up"):  # context_menu: the Calculator's own
        state.run(Binding(action))
    assert state.menu is None


# ----- pages, saving and the engine ---------------------------------------------------------------


def test_deleting_the_page_frees_its_lists_and_undo_brings_them_back():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    session = sheet.session
    assert session.eval("xs:=5").error is not None
    state.run_action("delete_page")
    assert session.eval("xs:=5").error is None
    session.eval("xs:={1,2}")
    state.run_action("undo_pages")
    assert session.eval("xs:=5").error is not None


def test_save_and_open_keep_the_sheet_and_its_values_win():
    state = sheet_app()
    sheet = sheet_of(state)
    calculator = calculator_on(state.document.problems[0].pages[0])
    calculator.session.eval("xs:={1,2,3}")
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    sheet.go((A, 2))
    type_cell(state, "20")  # after the Calculator's entry: the sheet's value is the newer
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=xs*2")
    assert not state.wizards
    sheet.widths[B] = 100
    text = dumps(state.document)
    data = json.loads(text)["problems"][0]["pages"][1]
    assert data["columns"]["a"] == ["xs", "xs", None]
    again = Recording(loads(text))
    again.document.go(0, 1)
    copy = sheet_of(again)
    assert copy.widths[B] == 100
    assert column(again, B, [1, 2, 3]) == ["2", "40", "6"]
    assert copy.session.eval("xs").text == "{1,20,3}"


def test_the_sorter_shows_a_sheet():
    """FR-DOC-001: previews use the sheet's displayed column names."""
    state = sheet_app()
    type_cell(state, "1")
    assert thumbnail(state.document.current, names={"spreadsheet": "Lists & Spreadsheet"}) == (
        "Lists & Spreadsheet",
        "1 cells",
    )
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "time")
    sheet.go((C, NAME_ROW))
    type_cell(state, "distance")
    assert thumbnail(state.document.current, names={"spreadsheet": "Lists & Spreadsheet"}) == (
        "Lists & Spreadsheet",
        "time, distance",
        "1 cells",
    )


def test_the_screen_carries_the_sheet():
    state = sheet_app()
    assert state.screen().sheet is not None


def test_through_a_remote_engine():
    """In the browser the ops wait for the Runner; the replies reach the page after it."""
    runner = Runner(LocalEngine())
    state = sheet_app(Recording(sessions=runner.new_session))
    sheet = sheet_of(state)
    type_cell(state, "=6*7")
    assert sheet.waiting == {(A, 1): "=6*7"}
    assert sheet.screen().cells[(A, 1)] == ("=6*7", False)  # what was typed, until the reply
    asyncio.run(runner.sync(state.document))
    state.prepare()  # takes the reply, asks for a view
    asyncio.run(runner.sync(state.document))
    assert shown(state, A, 1) == "42"
    journal = state.document.problems[0].session.journal
    assert [op["action"] for op in journal if op["op"] == "sheet"] == ["restore"]


def test_a_remote_rebuild_replays_the_sheet():
    runner = Runner(LocalEngine())
    state = sheet_app(Recording(sessions=runner.new_session))
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    sheet.go((A, 1))
    type_cell(state, "5")
    asyncio.run(runner.sync(state.document))
    state.prepare()
    session = state.document.problems[0].session
    asyncio.run(runner.engine.reset({session.id: list(session.journal)}))
    reply = asyncio.run(
        runner.engine.run(session.id, [{"op": "eval", "line": "xs", "approximate": False}])
    )
    assert reply["result"] is not None
    assert reply["result"]["text"] == "{5}"


@pytest.mark.parametrize("bad", [{"cells": [[0, 0, "entry", "x"]]}, {"widths": {"a": 5000}}])
def test_a_damaged_page_loads_what_it_can(bad):
    state = sheet_app()
    page = PAGES["spreadsheet"]
    problem = state.document.problems[0]
    model = next(iter(page.load(page, problem, bad)), None)
    assert model is None  # the generator never yields; its value is the model


# ----- the rest of the keys and items -------------------------------------------------------------


def test_the_window_size_and_scrolling_right():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.set_window(10, 6)
    assert (sheet.rows_shown, sheet.columns_shown) == (10, 6)
    sheet.go((H, 1))
    assert sheet.left == 2
    keys(state, "home_key")
    assert (sheet.cursor, sheet.left) == ((A, 1), 0)


def test_whole_rows_and_columns():
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("1", "2"):
        type_cell(state, value)
    sheet.go((A, 2))
    state.run(Binding("sheet", "select_row"))
    assert (sheet.address(), sheet.context_menu()) == ("2", "sheet_row")
    assert sheet.selection() == (0, 2, 25, 2)
    state.run(Binding("sheet", "select_column"))
    assert (sheet.address(), sheet.context_menu()) == ("A", "sheet_column")
    assert sheet.selection() == (0, 1, 0, ROWS)
    keys(state, "escape")
    assert sheet.selection() is None
    sheet.go((A, FORMULA_ROW))
    assert sheet.address() == "A="


def test_sheet_navigation_replaces_selection_stays_in_bounds_and_follows_cursor():
    """FR-SHEET-004: arrows move one cell without wrapping and keep the cursor visible."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.set_window(3, 2)
    sheet.go((0, 1))
    keys(state, "left")
    assert sheet.cursor == (0, 1)
    keys(state, "right")
    assert sheet.cursor == (1, 1)
    state.run(Binding("select_cells", "col:1"))
    assert sheet.selection() == (1, 1, 2, 1)
    keys(state, "right")
    assert sheet.cursor == (3, 1)
    assert sheet.selection() is None
    state.run(Binding("select_cells", "row:1"))
    assert sheet.cursor == (3, 2)
    keys(state, "down")
    assert sheet.cursor == (3, 3)
    assert sheet.top == 1
    keys(state, "down")
    assert sheet.cursor == (3, 4)
    assert sheet.top == 2
    sheet.go((25, 2500))
    keys(state, "right", "down")
    assert sheet.cursor == (25, 2500)


def test_shift_arrows_select_ranges_and_heading_edges_select_whole_axes():
    """FR-SHEET-005, FR-SHEET-007: extend ranges and convert at row/column headings."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((1, 2))
    state.run(Binding("select_cells", "col:-1"))
    assert sheet.selection() == (0, 2, 1, 2)
    state.run(Binding("select_cells", "col:-1"))
    assert sheet.whole == "row"
    assert sheet.selection() == (0, 2, 25, 2)
    state.run(Binding("select_cells", "row:1"))
    assert sheet.selection() == (0, 2, 25, 3)
    assert sheet.address() == "2:3"

    sheet.go((2, 1))
    state.run(Binding("select_cells", "row:-1"))
    assert sheet.whole == "column"
    assert sheet.selection() == (2, 1, 2, ROWS)
    state.run(Binding("select_cells", "col:1"))
    assert sheet.selection() == (2, 1, 3, ROWS)
    assert sheet.address() == "C:D"
    state.run(Binding("select_cells", "col:-1"))
    assert sheet.address() == "C"

    sheet.go((1, 2))
    state.run(Binding("select_cells", "row:-1"))
    assert sheet.selection() == (1, 1, 1, 2)
    state.run(Binding("select_cells", "row:1"))
    assert sheet.selection() is None
    assert sheet.cursor == (1, 2)
    state.run(Binding("select_cells", "row:1"))
    assert sheet.selection() == (1, 2, 1, 3)


def test_clicking_a_column_heading_selects_the_column_for_header_actions():
    """FR-SHEET-007: the column heading selects its logical column."""
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("sheet_tap", "2,-1"))
    assert sheet.cursor == (2, NAME_ROW)
    assert sheet.whole == "column"
    assert (sheet.address(), sheet.context_menu()) == ("C", "sheet_column")


def test_select_all_and_end():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((C, 3))
    type_cell(state, "1")
    sheet.go((A, 1))
    keys(state, "shift_tab")
    assert sheet.address() == "A1:C3"
    sheet.go((A, 1))
    keys(state, "end")
    assert sheet.cursor == (C, 1)


def test_editing_keys():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("insert", "abc"))
    keys(state, "clear")
    assert sheet.editing == ""
    state.run(Binding("insert", "abc"))
    keys(state, "home", "delete", "end", "left", "right")
    state.run(Binding("power", "2"))
    assert sheet.editing == "bc^2"


def test_a_quote_pair_leaves_the_caret_inside():
    state = sheet_app()
    state.run(Binding("insert_linear", f'"{MARK}"'))
    state.run(Binding("insert", "hi"))
    assert sheet_of(state).editing == '"hi"'


def test_a_tap_on_the_cell_being_edited_keeps_editing():
    state = sheet_app()
    keys(state, "4")
    state.run(Binding("sheet_tap", "0,1"))
    assert sheet_of(state).editing == "4"


def test_nothing_to_undo_redo_or_paste():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.undo()
    sheet.redo()
    sheet.paste()
    assert not sheet.dialogs


def test_delete_cells_store_var_unlink_and_minimize():
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("1", "2", "3", "4"):
        type_cell(state, value)
    sheet.go((A, 1))
    state.run(Binding("select_cells", "row:1"))
    state.run(Binding("sheet", "delete_cells"))
    assert column(state, A, [1, 2]) == ["3", "4"]
    state.run(Binding("sheet", "clear"))
    assert column(state, A, [1]) == [""]
    state.run(Binding("sheet", "store_var"))
    assert (sheet.cursor, sheet.editing) == ((A, NAME_ROW), "var")
    keys(state, "clear")
    state.run(Binding("insert", "ws"))
    keys(state, "enter")
    assert sheet.columns[A][1] == "ws"
    state.run(Binding("sheet", "unlink"))
    assert sheet.columns[A][1] is None
    state.run(Binding("sheet", "minimize"))
    assert sheet.width(A) < DEFAULT_WIDTH


def test_menu_copy_cut_paste_recalculate_and_goto():
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "5")
    sheet.go((A, 1))
    state.run(Binding("sheet", "copy"))
    sheet.go((B, 1))
    state.run(Binding("sheet", "paste"))
    state.run(Binding("sheet", "cut"))
    state.run(Binding("sheet", "recalculate"))
    assert column(state, B, [1]) == [""]
    state.run(Binding("sheet", "goto"))
    assert state.wizards[-1].title == "Go To"


def test_escape_ends_a_mode_and_fill_with_nothing_chosen():
    state = sheet_app()
    sheet = sheet_of(state)
    state.run(Binding("sheet", "move_column"))
    keys(state, "escape")
    assert sheet.mode is None
    state.run(Binding("sheet", "fill"))
    sheet._fill_from = None
    keys(state, "enter")
    assert sheet.mode is None


def test_a_sort_range_typed_wrong_sorts_the_selection():
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("3", "1", "2"):
        type_cell(state, value)
    sheet.go((A, 1))
    state.run(Binding("select_cells", "row:2"))
    state.run(Binding("sheet", "sort"))
    finish_wizard(state, range="nonsense", order="descending")
    assert column(state, A, [1, 2, 3]) == ["3", "2", "1"]


# ----- from emulator check 6 run 4, part S ------------------------------------------------------


def test_return_on_a_filled_cell_selects_it_so_typing_replaces():
    """Run 4, S16: Return on F1 holding 7, then 8: F1 is 8, not 78."""
    state = sheet_app()
    type_cell(state, "7")
    keys(state, "up", "enter")
    sheet = sheet_of(state)
    assert (sheet.editing, sheet.selected) == ("7", True)
    keys(state, "8", "enter")
    assert shown(state, A, 1) == "8"
    keys(state, "up", "enter", "right", "9")  # a move first: the caret goes to the end
    assert sheet.editing == "89"
    keys(state, "escape", "enter", "backspace")
    assert sheet.editing == ""


def test_typing_into_a_formula_column_asks_first():
    """Check 5, E8; run 4, S16: Data Loss; OK leaves only the typed value."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=seq(n,n,1,3)")
    sheet.go((B, 3))
    type_cell(state, "99")
    assert sheet.dialogs[0].title == "Data Loss"
    keys(state, "enter")  # OK
    assert column(state, B, [1, 2, 3]) == ["", "", "99"]
    assert sheet.columns[B][2] is None


def test_a_columns_name_in_a_formula_asks_column_or_variable():
    """Run 4, S11."""
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("5", "1"):
        type_cell(state, value)
    sheet.go((A, NAME_ROW))
    type_cell(state, "u")
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=u*3")
    wizard = state.wizards[-1]
    assert wizard.fields[0].label == "u :  Column or Variable?"
    assert [label for _, label in wizard.fields[0].choices] == [
        "Column Reference",
        "Variable Reference",
    ]
    finish_wizard(state, u="variable")
    assert column(state, B, [1, 2]) == ["15", "3"]


def test_a_long_list_name_in_a_formula_does_not_open_a_conflict_dialog():
    state = sheet_app()
    sheet = sheet_of(state)
    for value in ("5", "1"):
        type_cell(state, value)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    sheet.go((B, FORMULA_ROW))
    type_cell(state, "=xs*3")

    assert not state.wizards
    assert column(state, B, [1, 2]) == ["15", "3"]


def test_the_name_cell_has_its_own_context_menu():
    """Run 4, S12: Cut (grey), Paste, Variables, Resize, Summary Plot, Quick Graph, Color."""
    state = sheet_app()
    sheet_of(state).go((A, NAME_ROW))
    keys(state, "context_menu")
    assert state.menu is not None
    rows = state.menu.view().rows
    assert [row.label for row in rows] == [
        "Cut",
        "Paste",
        "Variables",
        "Resize",
        "Summary Plot",
        "Quick Graph",
        "Color",
    ]
    assert not rows[0].enabled
    assert not rows[5].enabled


def test_quick_graph_context_item_enables_for_a_named_list():
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("scores:={1,2,3}").error is None
    sheet.go((A, NAME_ROW))
    sheet.menu_action("link:scores")

    keys(state, "context_menu")

    assert state.menu is not None
    quick_graph = next(row for row in state.menu.view().rows if row.label == "Quick Graph")
    assert quick_graph.enabled


# ----- spreadsheet file interchange (slice 3e) -------------------------------------------------


def test_imported_formulas_calculate_and_export_can_include_the_formula():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((C, 1))

    sheet.import_rows([[FileCell("2"), FileCell("C1+3", True)]])

    assert column(state, C, [1]) == ["2"]
    assert column(state, D, [1]) == ["5"]
    sheet.request_export_view()
    sheet.update()
    assert sheet.export_rows(formulas=True) == [
        [FileCell(""), FileCell(""), FileCell("2"), FileCell("C1+3", True)]
    ]
    assert sheet.export_rows() == [[FileCell(""), FileCell(""), FileCell("2"), FileCell("5")]]


@pytest.mark.parametrize(("action", "expected"), [("enter", "9"), ("escape", "7")])
def test_importing_over_cells_prompts_before_replacing_them(action, expected):
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "7")
    sheet.go((A, 1))

    sheet.import_rows([[FileCell("9")]])

    assert shown(state, A, 1) == "7"
    assert sheet.dialogs[0].title == "Data Loss"
    keys(state, action)
    assert shown(state, A, 1) == expected


def test_importing_over_a_linked_list_prompts_before_replacing_it():
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("scores:={7,8}").error is None
    sheet.go((A, NAME_ROW))
    sheet.menu_action("link:scores")
    sheet.go((A, 1))

    sheet.import_rows([[FileCell("9")]])

    assert sheet.dialogs[0].title == "Data Loss"
    assert shown(state, A, 1) == "7"
    keys(state, "enter")
    assert shown(state, A, 1) == "9"
    assert sheet.session.eval("scores[1]").text == "9"


def test_quick_graph_uses_the_selected_named_list():
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("scores:={1,2,3}").error is None
    sheet.go((A, NAME_ROW))
    sheet.menu_action("link:scores")
    sheet.menu_action("quick_graph")

    assert len(sheet.split_statistics) == 1
    assert sheet.split_statistics[0].plot_data().x == (1.0, 2.0, 3.0)


def test_summary_plot_can_split_the_page_and_persist_its_plot():
    state = Recording()
    type_cell(state, 'labels:={"cat","dog"}')
    type_cell(state, "counts:={5,3}")
    state.run_action("add_page", "spreadsheet")
    sheet = sheet_of(state)

    sheet.menu_action("summary_plot")
    state.prepare()
    finish_wizard(state, x="labels", summary="counts", display="split")

    assert len(sheet.split_statistics) == 1
    plot = sheet.split_statistics[0].plot_data()
    assert plot.x == ("cat", "dog")
    assert plot.summary == (5.0, 3.0)
    restored_document = loads(dumps(state.document))
    restored_sheet = spreadsheet_of(restored_document.current)
    assert restored_sheet is not None
    assert restored_sheet.split_statistics[0].plot_data().summary == (5.0, 3.0)


def test_summary_plot_can_open_a_new_statistics_page():
    state = Recording()
    type_cell(state, 'labels:={"cat","dog"}')
    type_cell(state, "counts:={5,3}")
    state.run_action("add_page", "spreadsheet")
    sheet = sheet_of(state)

    sheet.menu_action("summary_plot")
    state.prepare()
    finish_wizard(state, x="labels", summary="counts", display="new")

    statistics = state.statistics
    assert statistics is not None
    assert statistics.plot_data().summary == (5.0, 3.0)
    assert sheet.split_statistics == []


# ----- Statistics from the sheet (slice 3c) -----------------------------------------------------


def stats_sheet():
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((C, 1))
    for value in (2, 4, 4, 4, 5, 5, 7, 9):
        type_cell(state, str(value))
    sheet.go((C, 1))
    return state, sheet


def test_one_variable_asks_how_many_lists_then_for_the_fields():
    """Check 5 E15; run 4, S1: Num of Lists, then X1 List (this column), Frequency List 1,
    Category List, Include Categories, 1st Result Column (the next free column)."""
    state, sheet = stats_sheet()
    for key in ("4", "1", "1"):  # Menu 4 Statistics, 1 Stat Calculations, 1 One-Variable
        state.run(Binding("open_menu", "menu")) if key == "4" else None
        state.run(Binding("insert", key))
    assert state.wizards[-1].fields[0].label == "Num of Lists:"
    finish_wizard(state)
    wizard = state.wizards[-1]
    assert wizard.title == "One-Variable Statistics"
    assert [(f.label, f.default) for f in wizard.fields] == [
        ("X1 List", "c[]"),
        ("Frequency List", "1"),
        ("Category List", ""),
        ("Include Categories", ""),
        ("1st Result Column", "d[]"),
    ]
    finish_wizard(state)
    sheet.go((D, 1))
    assert column(state, D, [1, 2]) == ["Title", "x̄"]
    assert column(state, E, [1, 2, 7]) == ["One-Variable Statistics", "5.", "8."]


def test_two_lists_have_only_the_lists_and_the_result_column():
    """Run 4, S5."""
    state, _ = stats_sheet()
    state.run(Binding("sheet", "stat:OneVar:2"))
    assert [f.label for f in state.wizards[-1].fields] == [
        "X1 List",
        "X2 List",
        "1st Result Column",
    ]


def test_a_regression_saves_to_the_next_free_function():
    """Run 4, S2, S4: Save RegEqn to f1, then f2."""
    state, sheet = stats_sheet()
    state.run(Binding("sheet", "stat:LinRegMx"))
    wizard = state.wizards[-1]
    assert [(f.label, f.default) for f in wizard.fields][:3] == [
        ("X List", "c[]"),
        ("Y List", ""),
        ("Save RegEqn to", "f1"),
    ]
    finish_wizard(state, x2="c[]")
    assert sheet.session.is_defined("f1")
    state.run(Binding("sheet", "stat:QuadReg"))
    assert state.wizards[-1].fields[2].default == "f2"


def test_dialog_checks():
    """Run 4, S2 (an empty Y List) and S10 (a result column of more than one letter)."""
    state, sheet = stats_sheet()
    state.run(Binding("sheet", "stat:TwoVar"))
    finish_wizard(state)
    assert sheet.dialogs.pop().title == "Input Error"
    state.run(Binding("sheet", "stat:TwoVar"))
    finish_wizard(state, x2="c[]", results="pz[]")
    assert sheet.dialogs.pop().message == "Cannot accept change: Invalid input."


def test_over_data_it_asks_first():
    state, sheet = stats_sheet()
    sheet.go((D, 1))
    type_cell(state, "1")
    sheet.go((C, 1))
    state.run(Binding("sheet", "stat:OneVar:1"))
    finish_wizard(state, results="d[]")
    assert sheet.dialogs[0].title == "Data Loss"
    keys(state, "enter")
    assert column(state, E, [2]) == ["5."]


def test_a_distribution_puts_its_formula_in_the_cell():
    """Run 4, S10: the formula waits in the cell's entry line; Return enters it."""
    state, sheet = stats_sheet()
    sheet.go((F, 2))
    state.run(Binding("wizard", "normCdf"))
    finish_wizard(state, lower="-1", upper="1")
    assert sheet.editing is not None
    assert sheet.editing.startswith("=normCdf(-1,1")
    keys(state, "enter")


def test_inference_wizard_writes_a_live_result_column():
    state, sheet = stats_sheet()
    sheet.go((F, 2))
    state.run(Binding("sheet", "inference:tInterval"))
    assert state.wizards[-1].title == "t Interval"
    finish_wizard(state, method="stats")
    finish_wizard(state, mean="5", sd="2", n="8", level="0.95")
    assert sheet.columns[H][2] == "tInterval 5,2,8,0.95"
    assert column(state, G, [1, 2, 3]) == ["Title", "CLower", "CUpper"]


def test_shade_p_value_splits_the_spreadsheet_view():
    state, sheet = stats_sheet()
    sheet.go((F, 2))
    state.run(Binding("sheet", "inference:zTest_1Prop"))
    finish_wizard(
        state,
        p0="0.5",
        successes="12",
        n="20",
        alternative="0",
        shade="1",
    )
    (pane,) = sheet.panes
    assert isinstance(pane, ShadePane)
    assert pane.plot is not None
    assert pane.plot.statistic == pytest.approx(0.89442719)
    assert pane.plot.p_value == pytest.approx(0.37109337)
    restored = load(Spreadsheet(sheet.session, sheet.clipboard), dump(sheet))
    (kept,) = restored.panes
    assert isinstance(kept, ShadePane)
    assert kept.plot == pane.plot


def test_the_result_column_is_the_one_after_the_cursor_and_data_loss_asks():
    """R5-I2: with the cursor in A, 1st Result Column is b[] even when B holds data; OK then
    asks before writing over it."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((B, 1))
    type_cell(state, "1")
    sheet.go((A, 1))
    state.run(Binding("sheet", "inference:zTest_1Prop"))
    assert state.wizards[-1].fields[-2].default == "b[]"
    finish_wizard(state, p0="0.5", successes="12", n="20")
    assert sheet.dialogs[-1].title == "Data Loss"


def test_inference_wizard_rejects_missing_fields_and_invalid_result_columns():
    state, sheet = stats_sheet()
    state.run(Binding("sheet", "inference:tInterval"))
    finish_wizard(state, method="stats")
    finish_wizard(state, mean="", sd="2", n="8")
    assert sheet.dialogs[-1].title == "Input Error"
    keys(state, "enter")

    state.run(Binding("sheet", "inference:tInterval"))
    finish_wizard(state, method="stats")
    finish_wizard(state, mean="5", sd="2", n="8", results="aa[]")
    assert sheet.dialogs[-1].title == "Syntax Error"
    assert sheet.dialogs[-1].message == "Cannot accept change: Invalid input."


def test_cancelling_inference_data_loss_discards_pending_shade():
    state, sheet = stats_sheet()
    sheet.go((D, 1))
    type_cell(state, "17")
    state.run(Binding("sheet", "inference:zTest_1Prop"))
    finish_wizard(
        state,
        p0="0.5",
        successes="12",
        n="20",
        results="d[]",
        shade="1",
    )
    assert sheet.dialogs[-1].title == "Data Loss"
    assert sheet.panes == []
    keys(state, "escape")
    assert sheet.panes == []
    assert shown(state, D, 1) == "17"


def test_the_statistics_menu():
    state, _ = stats_sheet()
    state.run(Binding("open_menu", "menu"))
    state.run(Binding("insert", "4"))
    assert state.menu is not None
    assert [row.label for row in state.menu.view().rows] == [
        "Stat calculations",
        "Distributions",
        "Confidence intervals",
        "Stat tests",
    ]
    state.run(Binding("insert", "1"))
    rows = state.menu.view().rows
    assert (rows[0].label, rows[2].label, rows[-1].enabled) == (
        "One-Variable Statistics…",
        "Linear Regression (mx+b)…",
        False,
    )


# ----- panes (decision 0034 item 2) ---------------------------------------------------------------


def test_pane_layouts_go_from_halves_to_three_to_two_by_two():
    """FR-DOC-009 (R5-I2): a second pane on the right, a third under it, a fourth making 2×2."""
    assert pane_boxes(1, 320, 200) == [(0, 0, 320, 200)]
    assert pane_boxes(2, 320, 200) == [(0, 0, 160, 200), (160, 0, 160, 200)]
    assert pane_boxes(3, 320, 200) == [(0, 0, 160, 200), (160, 0, 160, 100), (160, 100, 160, 100)]
    assert pane_boxes(4, 320, 200)[2:] == [(0, 100, 160, 100), (160, 100, 160, 100)]


def test_a_fourth_pane_goes_bottom_left_and_a_fifth_replaces_the_newest():
    """R5-I2: scatter top right and the t pane under it; the z pane then goes bottom left and
    the t pane bottom right. Beyond four the newest pane is replaced (not seen on the device)."""
    state = sheet_app()
    sheet = sheet_of(state)
    scatter, t, z, again = (ShadePane(name, 0) for name in ("x", "t", "z", "again"))
    for pane in (scatter, t, z):
        sheet.add_pane(pane, undoable=False)
    assert sheet.panes == [scatter, z, t]
    sheet.add_pane(again, undoable=False)
    assert sheet.panes == [scatter, again, t]


# ----- Quick Graph (sheet5, R5-Q1) ----------------------------------------------------------------


def lists_sheet():
    """A sheet whose columns A and B are linked to xs and ys."""
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("xs:={1,2,3}").error is None
    assert sheet.session.eval("ys:={2,4,7}").error is None
    for col, name in ((A, "xs"), (B, "ys")):
        sheet.go((col, NAME_ROW))
        sheet.menu_action(f"link:{name}")
    return state, sheet


def data_menu(state):
    """Menu > 3 Data, as rows."""
    state.run(Binding("open_menu", "menu"))
    state.run(Binding("insert", "3"))
    assert state.menu is not None
    rows = {row.label: row.enabled for row in state.menu.view().rows}
    state.menu = None
    return rows


def test_quick_graph_is_grey_for_a_block_and_a_single_cell():
    """FR-SHEET-008 (R5-Q1, R5-S): grey, not a dialog, unless a column is selected."""
    state, sheet = lists_sheet()
    sheet.go((A, 1))
    assert data_menu(state)["Quick Graph"] is False
    state.run(Binding("select_cells", "row:1"))  # shift+Down: A1:A2
    assert sheet.selection() is not None
    assert data_menu(state)["Quick Graph"] is False
    sheet.go((A, NAME_ROW))
    assert data_menu(state)["Quick Graph"] is True


def test_two_selected_columns_make_a_scatter_plot_and_one_undo_removes_it():
    """FR-SHEET-008, FR-STAT-001 (R5-Q1): from the name cell of xs, shift+Right takes ys too;
    Quick Graph makes a scatter plot with the first column on x; one ctrl+Z takes it away and
    leaves the columns selected."""
    state, sheet = lists_sheet()
    sheet.go((A, NAME_ROW))
    keys(state, "select_right")
    assert sheet.whole_columns() == (A, B)
    assert data_menu(state)["Quick Graph"] is True
    state.run(Binding("sheet", "quick_graph"))
    (plot,) = sheet.split_statistics
    assert (plot.x_name, plot.y_name, plot.plot_type.value) == ("xs", "ys", "Scatter Plot")
    keys(state, "undo")
    assert sheet.panes == []
    assert sheet.whole_columns() == (A, B)
    keys(state, "redo")
    assert len(sheet.panes) == 1


def test_quick_graph_of_one_column_undoes_in_one_step():
    """R5-Q1: a dot plot of d1; ctrl+Z gives the full-width sheet back."""
    state, sheet = lists_sheet()
    sheet.go((B, NAME_ROW))
    keys(state, "up")  # stays on the name cell
    state.run(Binding("sheet", "quick_graph"))
    assert sheet.split_statistics[0].plot_type.value == "Dot Plot"
    keys(state, "undo")
    assert sheet.panes == []


# ----- Summary Plot (sheet5, R5-Q2) ---------------------------------------------------------------


def test_summary_plot_takes_a_numeric_x_list_from_the_selected_columns():
    """FR-STAT-003, FR-SHEET-008 (R5-Q2): with xs and ys selected the dialog offers X List xs and
    Summary List ys, Display On Split Page first; the plot is a histogram of ys against xs."""
    state, sheet = lists_sheet()
    state.wizards.clear()
    sheet.go((A, NAME_ROW))
    keys(state, "select_right")
    state.run(Binding("sheet", "summary_plot"))
    state.prepare()
    wizard = state.wizards[-1]
    assert [(f.label, f.default) for f in wizard.fields] == [
        ("X List", "xs"),
        ("Summary List", "ys"),
        ("Display On", "split"),
    ]
    assert wizard.fields[2].choices == (("split", "Split Page"), ("new", "New Page"))
    assert ("xs", "xs") in wizard.fields[0].choices
    finish_wizard(state)
    (plot,) = sheet.split_statistics
    data = plot.plot_data()
    assert (data.plot_type.value, data.x, data.summary) == (
        "Histogram",
        (1.0, 2.0, 3.0),
        (2.0, 4.0, 7.0),
    )
    keys(state, "undo")
    assert sheet.panes == []


def test_a_single_selected_column_offers_the_first_other_numeric_list_to_summarise():
    """R5-Q2 (Computer view): name cell xs, Summary Plot: X List xs, Summary List the first
    other numeric list."""
    state, sheet = lists_sheet()
    state.wizards.clear()
    sheet.go((B, NAME_ROW))
    state.run(Binding("sheet", "summary_plot"))
    state.prepare()
    assert [f.default for f in state.wizards[-1].fields][:2] == ["ys", "xs"]


# ----- stat test and interval dialogs (stats4, R5-I2) ---------------------------------------------


def test_t_test_asks_the_data_input_method_then_has_the_device_defaults():
    """FR-STAT-004 (R5-I2): Data first; List is the cursor's column, Frequency 1, Ha μ ≠ μ0 with
    > first, 1st Result Column the next column, Draw: Shade P Value unticked."""
    state, sheet = stats_sheet()
    sheet.go((A, 1))
    state.run(Binding("sheet", "inference:tTest"))
    method = state.wizards[-1]
    assert (method.title, method.fields[0].label, method.fields[0].default) == (
        "t Test",
        "Data Input Method",
        "data",
    )
    assert [label for _, label in method.fields[0].choices] == ["Data", "Stats"]
    finish_wizard(state)
    wizard = state.wizards[-1]
    assert [(f.label, f.default) for f in wizard.fields] == [
        ("μ0", ""),
        ("List", "a[]"),
        ("Frequency List", "1"),
        ("Alternate Hyp", "0"),
        ("1st Result Column", "b[]"),
        ("Draw: Shade P Value", "0"),
    ]
    assert [label for _, label in wizard.fields[3].choices] == [
        "Ha: μ > μ0",
        "Ha: μ ≠ μ0",
        "Ha: μ < μ0",
    ]


def test_a_shaded_t_test_adds_a_t_pane_and_a_shaded_z_test_makes_a_third():
    """FR-STAT-004, FR-DOC-009 (R5-I2): t Test of d1 against μ0 = 4, Ha μ > μ0, shaded: a t pane
    with t = 1.4661 and PVal = 0.0930 (d1 as after the drag); then a 1-Prop z Test pane."""
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("d1:={2,4,4,4.536,5,5,7.536,9}").error is None
    sheet.go((C, 1))
    state.run(Binding("sheet", "inference:tTest:data"))
    finish_wizard(state, null="4", x="d1", alternative="1", shade="1")
    assert state.wizards[-1].title == "Conflict Detected"  # d1 is also a cell
    finish_wizard(state, d1="variable")
    (pane,) = sheet.panes
    assert isinstance(pane, ShadePane)
    assert pane.plot is not None
    assert (pane.plot.variable, pane.plot.df) == ("t", 7)
    assert pane.plot.statistic == pytest.approx(1.4661067, abs=1e-6)
    assert pane.plot.p_value == pytest.approx(0.09302381, abs=1e-7)
    sheet.go((F, 1))
    state.run(Binding("sheet", "inference:zTest_1Prop"))
    finish_wizard(state, p0="0.5", successes="30", n="50", alternative="1", shade="1")
    assert [p.plot.variable for p in sheet.panes if isinstance(p, ShadePane) and p.plot] == [
        "t",
        "z",
    ]
    z_pane = sheet.panes[1]
    assert isinstance(z_pane, ShadePane)
    assert z_pane.plot is not None
    assert z_pane.plot.statistic == pytest.approx(1.4142, abs=1e-4)
    assert sheet.panes[0] is pane  # the t pane kept its own numbers


def test_two_sample_t_interval_and_linear_reg_t_test_fields():
    """R5-I2: 2-Sample t Interval: List 1 (this column), List 2, Frequency 1 and 2, C Level 0.95,
    Pooled No, then the result column; Linear Reg t Test saves RegEqn to f1 and has no Draw."""
    state, sheet = stats_sheet()
    sheet.go((E, 1))
    state.run(Binding("sheet", "inference:tInterval_2Samp"))
    assert [label for _, label in state.wizards[-1].fields[0].choices] == ["Data", "Stats"]
    finish_wizard(state)
    assert [(f.label, f.default) for f in state.wizards[-1].fields] == [
        ("List 1", "e[]"),
        ("List 2", ""),
        ("Frequency 1", "1"),
        ("Frequency 2", "1"),
        ("C Level", "0.95"),
        ("Pooled", "0"),
        ("1st Result Column", "f[]"),
    ]
    sheet.go((H, 1))
    state.run(Binding("sheet", "inference:LinRegtTest"))
    wizard = state.wizards[-1]
    assert [(f.label, f.default) for f in wizard.fields] == [
        ("X List", "h[]"),
        ("Y List", ""),
        ("Save RegEqn to", "f1"),
        ("Frequency List", "1"),
        ("Alternate Hyp", "0"),
        ("1st Result Column", "i[]"),
    ]
    assert wizard.fields[4].choices[1][1] == f"Ha: β & {RHO} ≠ 0"
    finish_wizard(state, x="c[]", y="c[]^2")
    assert sheet.columns[J][2] == "LinRegtTest c[],c[]^2,1,0: CopyVar stat.RegEqn,f1"


@pytest.mark.parametrize(
    ("command", "labels", "values", "formula"),
    [
        (
            "zTest_2Samp",
            ["σ1", "σ2", "x̄1", "n1", "x̄2", "n2", "Alternate Hyp"],
            {"sigma1": "1.2", "sigma2": "1.5", "mean1": "5.4", "n1": "10", "mean2": "4.8"},
            "zTest_2Samp 1.2,1.5,5.4,10,4.8,12,0",
        ),
        (
            "tTest_2Samp",
            ["x̄1", "Sx1", "n1", "x̄2", "Sx2", "n2", "Alternate Hyp", "Pooled"],
            {"mean1": "5.4", "sd1": "1.2", "n1": "10", "mean2": "4.8", "sd2": "1.5"},
            "tTest_2Samp 5.4,1.2,10,4.8,1.5,12,0,0",
        ),
        (
            "tInterval_2Samp",
            ["x̄1", "Sx1", "n1", "x̄2", "Sx2", "n2", "C Level", "Pooled"],
            {"mean1": "5.4", "sd1": "1.2", "n1": "10", "mean2": "4.8", "sd2": "1.5"},
            "tInterval_2Samp 5.4,1.2,10,4.8,1.5,12,0.95,0",
        ),
    ],
)
def test_two_sample_stats_forms(command, labels, values, formula):
    """FR-STAT-004 (run 6, R6-C3): the two-sample tests and interval offer Stats as well as
    Data, with the device's fields; then the result column, and Draw for a test."""
    state, sheet = stats_sheet()
    sheet.go((E, 1))
    state.run(Binding("sheet", f"inference:{command}"))
    assert [label for _, label in state.wizards[-1].fields[0].choices] == ["Data", "Stats"]
    finish_wizard(state, method="stats")
    fields = [field.label for field in state.wizards[-1].fields]
    tail = ["1st Result Column", *(["Draw: Shade P Value"] if "Test" in command else [])]
    assert fields == [*labels, *tail]
    finish_wizard(state, **values, n2="12")
    assert sheet.columns[G][2] == formula


def test_two_sample_t_interval_stats_in_the_sheet_matches_run_6():
    """Run 6, S2: x̄1 5.4, Sx1 1.2, n1 10, x̄2 4.8, Sx2 1.5, n2 12, C 0.95, not pooled."""
    state, sheet = stats_sheet()
    sheet.go((E, 1))
    state.run(Binding("sheet", "inference:tInterval_2Samp"))
    finish_wizard(state, method="stats")
    finish_wizard(state, mean1="5.4", sd1="1.2", n1="10", mean2="4.8", sd2="1.5", n2="12")
    rows = list(range(1, 13))
    assert column(state, F, rows) == [
        "Title",
        "CLower",
        "CUpper",
        "x̄Diff",
        "ME",
        "df",
        "x̄1",
        "x̄2",
        "sx1",
        "sx2",
        "n1",
        "n2",
    ]
    assert column(state, G, [1, 4, 6]) == ["2-Sample t Interval", "0.6", "19.980327"]


def test_t_test_in_the_sheet_matches_run_6():
    """Run 6, R6-C2: t Test on d1 = {2,4,4,4,5,5,7,9}, μ0 4, Ha μ ≠ μ0: eight rows, labels in
    one column and values in the next."""
    state, _ = stats_sheet()
    state.run(Binding("sheet", "inference:tTest"))
    finish_wizard(state)
    finish_wizard(state, null="4")
    rows = list(range(1, 9))
    assert column(state, D, rows) == [
        "Title",
        "Alternate Hyp",
        "t",
        "PVal",
        "df",
        "x̄",
        "sx := sn-1x",
        "n",
    ]
    assert column(state, E, rows) == [
        "t Test",
        "μ ≠ μ0",
        "1.3228757",
        "0.22745282",
        "7.",
        "5.",
        "2.1380899",
        "8.",
    ]


def test_escape_in_a_tests_fields_goes_back_to_the_data_input_method():
    """Run 6, R6-C3: Esc in the fields dialog reopens the Data Input Method box; a dialog with
    no such box just closes."""
    state, _ = stats_sheet()
    state.run(Binding("sheet", "inference:zTest_2Samp"))
    finish_wizard(state, method="stats")
    fields = state.wizards.pop()
    state.escape_wizard(fields)
    assert state.wizards[-1].fields[0].label == "Data Input Method"
    assert [label for _, label in state.wizards[-1].fields[0].choices] == ["Data", "Stats"]
    state.wizards.clear()
    state.run(Binding("sheet", "inference:zTest_1Prop"))
    state.escape_wizard(state.wizards.pop())
    assert state.wizards == []


def test_the_stat_tests_and_intervals_lists():
    """R5-I2: the Stat Tests and Confidence Intervals lists as recorded."""
    state, _ = stats_sheet()
    labels = []
    for key in ("3", "4"):
        state.run(Binding("open_menu", "menu"))
        state.run(Binding("insert", "4"))
        state.run(Binding("insert", key))
        assert state.menu is not None
        labels.append([row.label for row in state.menu.view().rows])
        state.menu = None
    assert labels[0] == [
        "z Interval…",
        "t Interval…",
        "2-Sample z Interval…",
        "2-Sample t Interval…",
        "1-Prop z Interval…",
        "2-Prop z Interval…",
        "Linear Reg t Intervals…",
        "Multiple reg intervals…",
    ]
    assert labels[1][:10] == [
        "z Test…",
        "t Test…",
        "2-Sample z Test…",
        "2-Sample t Test…",
        "1-Prop z Test…",
        "2-Prop z Test…",
        "χ² GOF…",
        "χ² 2-way Test…",
        "2-Sample F Test…",
        "Linear Reg t Test…",
    ]


def test_normal_cdf_with_shade_area_fills_the_cell_and_undo_keeps_the_plot():
    """FR-STAT-004, FR-DOC-009 (split2 H14): A1 holds 1; Normal Cdf, Upper Bound 1, Shade area:
    A1 gets =normCdf(-∞,1,0,1) (0.841…) and a shaded curve joins the page; ctrl+Z puts the 1
    back and the plot stays."""
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "1")
    sheet.go((A, 1))
    state.run(Binding("open_menu", "menu"))
    for key in ("4", "2", "2"):
        state.run(Binding("insert", key))
    wizard = state.wizards[-1]
    assert [(f.label, f.default) for f in wizard.fields] == [
        ("Lower Bound", "-∞"),
        ("Upper Bound", ""),
        ("μ", "0"),
        ("σ", "1"),
        ("Draw: Shade area", "0"),
    ]
    finish_wizard(state, upper="1", shade="1")
    assert shown(state, A, 1).startswith("0.841")
    (pane,) = sheet.panes
    assert isinstance(pane, AreaPane)
    assert pane.plot.area == pytest.approx(0.84134475)
    keys(state, "undo")
    assert shown(state, A, 1) == "1"
    assert sheet.panes == [pane]


def test_normal_cdf_without_shading_waits_in_the_entry_line():
    """Run 4, S10: unticked, the formula waits in the cell's entry line."""
    state, sheet = stats_sheet()
    sheet.go((F, 2))
    state.run(Binding("sheet", "distribution:normCdf"))
    finish_wizard(state, upper="1")
    assert sheet.editing == "=normCdf(-∞,1,0,1)"
    assert sheet.panes == []


# ----- sheet details (sheet5) ---------------------------------------------------------------------


def test_the_data_menu_greys_items_by_what_is_selected():
    """FR-SHEET-002 (sheet5, R5-Q1 and R5-S): a single cell, a block, a column, the name cell."""
    state, sheet = lists_sheet()
    sheet.go((C, 1))
    grey = {label for label, enabled in data_menu(state).items() if not enabled}
    assert grey == {"Clear Data", "Quick Graph"}

    state.run(Binding("select_cells", "row:1"))
    grey = {label for label, enabled in data_menu(state).items() if not enabled}
    assert grey >= {
        "Generate Sequence…",
        "Clear Data",
        "Random",
        "List math",
        "List operations",
        "Quick Graph",
        "Data capture",
    }
    assert "Fill" not in grey
    assert "Summary Plot" not in grey
    state.run(Binding("open_menu", "menu"))
    assert state.menu is not None
    top = {row.label: row.enabled for row in state.menu.view().rows}
    state.menu = None
    assert (top["Insert"], top["Statistics"], top["Data"]) == (False, False, True)

    sheet.go((A, NAME_ROW))
    rows = data_menu(state)
    assert (rows["Fill"], rows["Clear Data"], rows["Quick Graph"]) == (False, True, True)


def test_the_random_list_math_and_list_operations_submenus():
    """Sheet5, R5-S: the three submenus in the device's order."""
    state, sheet = lists_sheet()
    sheet.go((C, 1))
    lists = []
    for key in ("5", "6", "7"):
        state.run(Binding("open_menu", "menu"))
        for press in ("3", key):
            state.run(Binding("insert", press))
        assert state.menu is not None
        lists.append([(row.label, row.enabled) for row in state.menu.view().rows][-10:])
        state.menu = None
    assert [label for label, _ in lists[0][-5:]] == [
        "Number",
        "Integer",
        "Binomial",
        "Normal",
        "Sample",
    ]
    assert [label for label, _ in lists[1]] == [
        "Minimum",
        "Maximum",
        "Mean",
        "Median",
        "Sum of Elements",
        "Product of Elements",
        "Sample Standard Deviation",
        "Sample Variance",
        "Population Standard Deviation",
        "Population Variance",
    ]
    assert lists[2][-7:] == [
        ("Cumulative Sum List", True),
        ("Difference list", True),
        ("Augment", True),
        ("Convert matrix to list", False),
        ("Left", True),
        ("Mid", True),
        ("Right", True),
    ]


@pytest.mark.parametrize("name", ["1a", "sin"])
def test_an_invalid_column_name_says_so_and_stays_in_the_name_cell(name):
    """FR-SHEET-003 (sheet5, R5-E7): Syntax Error, Cannot accept change: Invalid input.; after OK
    the name cell is still being edited with the name."""
    state = sheet_app()
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, name)
    assert (sheet.dialogs[0].title, sheet.dialogs[0].message) == (
        "Syntax Error",
        "Cannot accept change: Invalid input.",
    )
    keys(state, "enter")
    assert (sheet.cursor, sheet.editing) == ((A, NAME_ROW), name)


def test_naming_a_column_after_a_list_links_it_without_a_conflict():
    """Sheet5, R5-E7: ws holds {1,2,3}; typing ws in A's name cell shows 1, 2, 3."""
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("ws:={1,2,3}").error is None
    sheet.go((A, NAME_ROW))
    type_cell(state, "ws")
    assert sheet.dialogs == []
    assert sheet.wizard is None
    assert column(state, A, [1, 2, 3]) == ["1", "2", "3"]


def test_the_var_key_in_an_empty_name_cell_lists_the_variables():
    """Sheet5, R5-E7: functions and lists alike; choosing a list links the column."""
    state = sheet_app()
    sheet = sheet_of(state)
    assert sheet.session.eval("Define f1(x)=x^2").error is None
    assert sheet.session.eval("ws:={1,2,3}").error is None
    sheet.go((B, NAME_ROW))
    state.run(Binding("open_menu", "variables"))
    assert state.menu is not None
    assert [row.label for row in state.menu.view().rows] == ["f1", "ws"]
    state.menu = None
    state.run(Binding("sheet", "link:ws"))
    assert column(state, B, [1, 2, 3]) == ["1", "2", "3"]


def test_return_on_a_filled_cell_edits_it_with_its_text_selected():
    """Sheet5, R5-S19: typing replaces (8, not 78); Return on the cell edits 8, selected."""
    state = sheet_app()
    sheet = sheet_of(state)
    type_cell(state, "7")
    sheet.go((A, 1))
    type_cell(state, "8")
    assert shown(state, A, 1) == "8"
    sheet.go((A, 1))
    keys(state, "enter")
    assert (sheet.editing, sheet.selected, sheet.cursor) == ("8", True, (A, 1))


def test_save_and_reopen_keep_split_pages_plots_and_axes_but_not_the_selection():
    """FR-DOC-003, FR-DOC-009 (sheet5, R5-Q3): a split page with a scatter of xs and ys, a
    regression page and a summary plot come back; selected points and the sheet's cursor do not
    (the cursor is at A1)."""
    state = Recording()
    type_cell(state, "xs:={1,2,3,4.435,5}")
    type_cell(state, "ys:={2.1,3.9,6.2,9.776,10.1}")
    state.run_action("add_page", "statistics")
    regression = state.statistics
    assert regression is not None
    for action in ("x:xs", "y:ys", "regression:LinRegMx"):
        regression.perform(action)
    regression.select(3)
    state.run_action("add_page", "spreadsheet")
    sheet = sheet_of(state)
    for col, name in ((A, "xs"), (B, "ys")):
        sheet.go((col, NAME_ROW))
        sheet.menu_action(f"link:{name}")
    sheet.go((A, NAME_ROW))
    keys(state, "select_right")
    state.run(Binding("sheet", "quick_graph"))
    sheet.go((C, 4))

    reopened = loads(dumps(state.document))
    problem = reopened.problems[0]
    restored = spreadsheet_of(problem.pages[2])
    assert restored is not None
    (scatter,) = restored.split_statistics
    assert (scatter.x_name, scatter.y_name, scatter.plot_type.value) == ("xs", "ys", "Scatter Plot")
    assert (restored.cursor, restored.selection()) == ((A, 1), None)
    page = problem.pages[1].model
    assert isinstance(page, Statistics)
    assert (page.x_name, page.y_name, page.regression) == ("xs", "ys", "LinRegMx")
    assert page.selected == set()
    assert scatter.plot_data().selected == frozenset()


# ----- run 6: Fill from one cell, Insert Cell and Insert Row (R6-C7, R6-C8, S4, S5) ----------


def test_fill_from_one_cell_copies_relative_formulas_and_undoes_in_one_step():
    """FR-SHEET-001 (run 6, R6-C7 and S4): F1 `=a1+1`, Fill, Down three times, Return: F2:F4 hold
    `=a2+1` to `=a4+1`; one ctrl+Z removes all three and F1 keeps its formula."""
    state = sheet_app()
    for value in ("1", "2", "3", "4"):
        type_cell(state, value)
    sheet = sheet_of(state)
    sheet.go((F, 1))
    type_cell(state, "=a1+1")
    sheet.go((F, 1))
    state.run(Binding("sheet", "fill"))
    keys(state, "down", "down", "down")
    assert sheet.screen().marker == (F, 1, F, 4)
    keys(state, "enter")
    assert [sheet.entry_text((F, row)) for row in (2, 3, 4)] == ["=a2+1", "=a3+1", "=a4+1"]
    assert column(state, F, [1, 2, 3, 4]) == ["2", "3", "4", "5"]
    keys(state, "undo")
    assert column(state, F, [1, 2, 3, 4]) == ["2", "", "", ""]
    assert sheet.entry_text((F, 1)) == "=a1+1"


def test_insert_cell_moves_the_cells_below_down():
    """Run 6, S5: Insert Cell on A2 of 1, 2, 3, 4: A2 is blank and 2, 3, 4 move to A3:A5."""
    state = sheet_app()
    for value in ("1", "2", "3", "4"):
        type_cell(state, value)
    sheet = sheet_of(state)
    sheet.go((A, 2))
    state.run(Binding("sheet", "insert_cell"))
    assert column(state, A, [1, 2, 3, 4, 5]) == ["1", "", "2", "3", "4"]


def _insert_menu(state):
    state.run(Binding("open_menu", "menu"))
    state.run(Binding("insert", "2"))
    assert state.menu is not None
    rows = state.menu.view().rows
    state.menu = None
    return {row.label: row.enabled for row in rows}


def test_insert_cell_is_grey_in_a_results_column_and_with_a_range():
    """Run 6, R6-C8 and S5: Insert Cell is grey with the cursor in a results column (and does
    nothing there); with a range selected the whole Insert menu is grey."""
    state, sheet = stats_sheet()
    state.run(Binding("sheet", "inference:tTest"))
    finish_wizard(state)
    finish_wizard(state, null="4")
    assert _insert_menu(state)["Insert Cell"]
    for results in (D, E):
        sheet.go((results, 8))
        assert _insert_menu(state) == {
            "Insert Cell": False,
            "Insert Row": True,
            "Insert Column": True,
        }
    state.run(Binding("sheet", "insert_cell"))
    assert column(state, D, [1, 8, 9]) == ["Title", "n", ""]
    sheet.go((C, 1))
    sheet.move(0, 1, extend=True)
    assert sheet.selection() is not None
    state.run(Binding("open_menu", "menu"))
    assert state.menu is not None
    menu = {row.label: row.enabled for row in state.menu.view().rows}
    assert not menu["Insert"]
    state.menu = None
    state.run(Binding("sheet", "insert_cell"))  # a shortcut does nothing either
    assert column(state, C, [1, 2, 3]) == ["2", "4", "4"]


def test_insert_row_leaves_test_results_where_they_are():
    """Run 6, R6-C8: Insert Row with a t Test's results in D and E: the data moves down, the
    results stay; one ctrl+Z removes the row."""
    state, sheet = stats_sheet()
    state.run(Binding("sheet", "inference:tTest"))
    finish_wizard(state)
    finish_wizard(state, null="4")
    before_labels, before_values = column(state, D, range(1, 10)), column(state, E, range(1, 10))
    sheet.go((C, 2))
    state.run(Binding("sheet", "insert_row"))
    assert column(state, C, [1, 2, 3]) == ["2", "", "4"]
    assert column(state, D, range(1, 10)) == before_labels
    assert column(state, D, [1, 8]) == ["Title", "n"]
    assert column(state, E, [1, 2, 3, 4]) == before_values[:4]
    keys(state, "undo")
    assert column(state, C, [1, 2, 3]) == ["2", "4", "4"]


def test_a_sheet_left_before_its_reply_still_saves_what_was_typed():
    """FR-DOC-010 (a bug): in the browser a sheet takes the engine's replies only while it is
    on screen. Typing a column name and data, then going to another page before the reply was
    taken, saved an empty sheet, so the data and every plot of it were lost on Open."""
    runner = Runner(LocalEngine())
    state = sheet_app(Recording(sessions=runner.new_session))
    sheet = sheet_of(state)
    sheet.go((A, NAME_ROW))
    type_cell(state, "xs")
    sheet.go((A, 1))
    type_cell(state, "4")
    state.run_action("add_page", "graphs")  # another page is on screen now
    asyncio.run(runner.sync(state.document))  # the reply waits for the sheet
    data = json.loads(dumps(state.document))["problems"][0]["pages"][1]
    assert data["columns"]["a"][0] == "xs"
    assert data["cells"] == [[A, 1, "entry", "4"]]
    fresh = Runner(LocalEngine())
    loaded = asyncio.run(fresh.load(dumps(state.document), PAGES))
    asyncio.run(fresh.sync(loaded))
    names = [row.name for row in loaded.problems[0].session.variables()]
    assert "xs" in names


def test_typed_cells_the_engine_has_not_answered_are_saved_as_typed():
    """Saved before the engine has seen the edit (it is still busy): the typed entry and
    formula are kept, as they would be once answered."""
    runner = Runner(LocalEngine())
    state = sheet_app(Recording(sessions=runner.new_session))
    sheet = sheet_of(state)
    sheet.go((A, 1))
    type_cell(state, "4")
    sheet.go((A, 2))
    type_cell(state, "=6*7")
    data = json.loads(dumps(state.document))["problems"][0]["pages"][1]
    assert data["cells"] == [[A, 1, "entry", "4"], [A, 2, "formula", "6*7"]]
