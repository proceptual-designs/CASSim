"""The list template and row/column selection in a matrix (M2d, FR-CALC-004)."""

from __future__ import annotations

from cassim.device.editor import Editor, Kind, Template
from cassim.device.keys import Binding
from cassim.devices.nspire.keymap import COMPUTER
from cassim.devices.nspire.pages.calculator import Calculator


def matrix(rows: int, cols: int, *cells: str) -> Editor:
    """A rows x cols matrix with `cells` typed in reading order, the cursor in the last cell."""
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (rows, cols))
    for index, cell in enumerate(cells):
        editor.insert_text(cell)
        if index < len(cells) - 1:
            editor.tab()
    return editor


class TestList:
    def test_a_comma_starts_the_next_element(self):
        editor = Editor()
        editor.insert_template(Kind.LIST, (1, 1))
        editor.insert_text("1,2,3")
        assert editor.linear() == "{1,2,3}"
        assert len(_list(editor).slots) == 3

    def test_a_comma_splits_the_element_at_the_cursor(self):
        editor = Editor()
        editor.insert_template(Kind.LIST, (1, 1))
        editor.insert_text("12")
        editor.left()
        editor.insert(",")
        assert editor.linear() == "{1,2}"
        editor.insert_text("x")  # the cursor is at the start of the second element
        assert editor.linear() == "{1,x2}"

    def test_backspace_at_the_start_of_an_element_undoes_the_comma(self):
        editor = Editor()
        editor.insert_template(Kind.LIST, (1, 1))
        editor.insert_text("1,2")
        editor.left()
        editor.backspace()
        assert editor.linear() == "{12}"
        assert editor.path == [(0, 0)]
        assert editor.pos == 1

    def test_backspace_in_the_first_element_keeps_the_old_dissolve(self):
        editor = Editor()
        editor.insert_template(Kind.LIST, (1, 1))
        editor.insert_text("5")
        editor.left()
        editor.backspace()  # highlights the template, as for any non-empty template
        assert editor.selected

    def test_tab_visits_each_element_then_leaves(self):
        editor = Editor()
        editor.insert_template(Kind.LIST, (1, 3))
        editor.insert_text("a")
        editor.tab()
        editor.insert_text("b")
        editor.tab()
        editor.insert_text("c")
        editor.tab()
        editor.insert_text("+1")
        assert editor.linear() == "{a,b,c}+1"

    def test_a_term_before_a_list_gets_a_star(self):
        editor = Editor("2")
        editor.insert_template(Kind.LIST, (1, 2))
        assert editor.linear() == "2*{,}"

    def test_latex_has_braces_and_the_elements(self):
        editor = Editor()
        editor.insert_template(Kind.LIST, (1, 2))
        assert editor.latex(cursor=False) == r"\left\{\square,\,\square\right\}"

    def test_the_list_key_action_takes_a_count(self):
        calc = Calculator()
        calc.perform(_template("list:4"))
        assert len(_list(calc.editor).slots) == 4


class TestSelectRowsAndColumns:
    def test_first_press_takes_the_row_the_cursor_is_in(self):
        editor = matrix(2, 2, "1", "2", "3", "4")  # the cursor is in the 4
        editor.select_cells("row", 1)
        assert editor.selected_cells() == [2, 3]

    def test_a_second_press_grows_it(self):
        editor = matrix(3, 2, *"123456")
        editor.path[-1] = (0, 2)  # the middle row
        editor.select_cells("row", 1)
        editor.select_cells("row", 1)
        assert editor.selected_cells() == [2, 3, 4, 5]
        editor.select_cells("row", -1)  # and back
        assert editor.selected_cells() == [2, 3]

    def test_it_stops_at_the_edges(self):
        editor = matrix(2, 2, *"1234")
        editor.path[-1] = (0, 0)
        editor.select_cells("row", -1)
        editor.select_cells("row", -1)
        assert editor.selected_cells() == [0, 1]

    def test_columns(self):
        editor = matrix(2, 3, *"123456")
        editor.path[-1] = (0, 1)
        editor.select_cells("col", 1)
        editor.select_cells("col", 1)
        assert editor.selected_cells() == [1, 2, 4, 5]

    def test_switching_axis_starts_again(self):
        editor = matrix(2, 2, *"1234")
        editor.select_cells("row", 1)
        editor.select_cells("col", 1)
        assert editor.selected_cells() == [1, 3]

    def test_outside_a_matrix_it_does_nothing(self):
        editor = Editor("12")
        editor.select_cells("row", 1)
        assert editor.cell_sel is None

    def test_arrows_and_clicks_drop_it(self):
        for drop in (lambda e: e.left(), lambda e: e.right(), lambda e: e.place([], 0)):
            editor = matrix(2, 2, *"1234")
            editor.select_cells("row", 1)
            drop(editor)
            assert editor.cell_sel is None
            assert editor.linear() == "[1,2;3,4]"

    def test_copy_gives_a_matrix_of_the_selected_rows(self):
        editor = matrix(3, 2, *"123456")
        editor.path[-1] = (0, 2)
        editor.select_cells("row", 1)
        (part,) = editor.selection()
        assert isinstance(part, Template)
        assert (part.kind, part.cols, len(part.slots)) == (Kind.MATRIX, 2, 2)
        assert Editor().paste([part]) is None

    def test_copy_a_column_is_a_matrix_one_wide(self):
        editor = matrix(2, 3, *"123456")
        editor.path[-1] = (0, 1)
        editor.select_cells("col", 1)
        (part,) = editor.selection()
        assert isinstance(part, Template)
        assert (part.cols, len(part.slots)) == (1, 2)
        copy_editor = Editor()
        copy_editor.paste([part])
        assert copy_editor.linear() == "[2;5]"

    def test_typing_replaces_the_selected_cells(self):
        editor = matrix(2, 2, *"1234")
        editor.select_cells("row", 1)
        editor.insert_text("9")
        assert editor.linear() == "[1,2;9,]"

    def test_backspace_removes_the_selected_row(self):
        editor = matrix(3, 2, *"123456")
        editor.path[-1] = (0, 2)
        editor.select_cells("row", 1)
        editor.backspace()
        assert editor.linear() == "[1,2;5,6]"
        assert editor.cell_sel is None
        assert editor.path == [(0, 2)]  # the row that closed up into its place

    def test_delete_removes_the_selected_column(self):
        editor = matrix(2, 3, *"123456")
        editor.path[-1] = (0, 1)
        editor.select_cells("col", 1)
        editor.delete()
        assert editor.linear() == "[1,3;4,6]"
        assert _matrix(editor).cols == 2

    def test_removing_the_last_row_removed_clamps_the_cursor(self):
        editor = matrix(2, 2, *"1234")
        editor.select_cells("row", 1)  # the cursor is in the last row
        editor.backspace()
        assert editor.linear() == "[1,2]"
        assert editor.path == [(0, 1)]

    def test_removing_every_row_only_empties_the_cells(self):
        editor = matrix(1, 2, "1", "2")
        editor.select_cells("row", 1)
        editor.backspace()
        assert editor.linear() == "[,]"

    def test_paste_a_row_over_a_row(self):
        editor = matrix(2, 2, *"1234")
        editor.path[-1] = (0, 0)
        editor.select_cells("row", 1)
        part = editor.selection()
        editor.cell_sel = None
        editor.path[-1] = (0, 3)
        editor.select_cells("row", 1)
        editor.paste(part)
        assert editor.linear() == "[1,2;1,2]"

    def test_paste_of_another_shape_nests(self):
        editor = matrix(2, 2, *"1234")
        editor.select_cells("row", 1)
        editor.paste([Template(Kind.MATRIX, [[], [], []], 3)])
        assert editor.linear() == "[1,2;[,,],]"

    def test_cut_takes_the_row_out(self):
        editor = matrix(2, 2, *"1234")
        editor.select_cells("row", 1)
        nodes = editor.cut()
        assert len(nodes) == 1
        assert editor.linear() == "[1,2;,]"


def test_undo_forgets_a_row_selection() -> None:
    calc = Calculator()
    calc.perform(_template("matrix:2,2"))
    calc.perform(COMPUTER["shift+ArrowDown"])
    assert calc.editor.cell_sel is not None
    calc.perform(COMPUTER["Backspace"])
    assert calc.editor.cell_sel is None
    calc.perform(COMPUTER["ctrl+z"])
    assert calc.editor.cell_sel is None


def test_shift_arrows_select_and_grow_rows_and_columns_by_key() -> None:
    calc = Calculator()
    calc.perform(_template("matrix:3,3"))  # the cursor is in the first cell
    calc.perform(COMPUTER["shift+ArrowDown"])
    calc.perform(COMPUTER["shift+ArrowDown"])
    assert calc.editor.selected_cells() == [0, 1, 2, 3, 4, 5]
    calc.perform(COMPUTER["alt+shift+ArrowRight"])  # a different axis starts again
    calc.perform(COMPUTER["alt+shift+ArrowRight"])
    assert calc.editor.selected_cells() == [0, 1, 3, 4, 6, 7]


def _template(spec: str) -> Binding:
    return Binding("template", spec)


def _list(editor: Editor) -> Template:
    node = editor.root[0]
    assert isinstance(node, Template)
    return node


def _matrix(editor: Editor) -> Template:
    return _list(editor)
