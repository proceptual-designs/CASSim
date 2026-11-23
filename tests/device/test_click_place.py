"""Placing the cursor from a click target (FR-CALC-004, decision 0019): no GUI needed."""

from cassim.device.editor import Editor, Kind, format_target, parse_target
from cassim.device.keys import Binding
from cassim.devices.nspire.pages.calculator import Calculator


def fraction_editor() -> Editor:
    """`5+(7)/(8)+9`, the cursor at the end."""
    editor = Editor("5+")
    editor.insert_text("7")
    editor.insert_template(Kind.FRACTION)
    editor.insert("8")
    editor.right()
    editor.insert_text("+9")
    return editor


def test_place_in_a_plain_row() -> None:
    editor = Editor("abc")
    editor.place([], 1)
    assert (editor.path, editor.pos) == ([], 1)
    editor.insert("X")
    assert editor.linear() == "aXbc"


def test_place_clamps_past_the_end_and_before_the_start() -> None:
    editor = Editor("abc")
    editor.place([], 99)
    assert editor.pos == 3
    editor.place([], -4)
    assert editor.pos == 0


def test_place_clears_selection() -> None:
    editor = Editor("abc")
    editor.select_all()
    editor.place([], 2)
    assert editor.anchor is None
    assert editor.span == (2, 2)


def test_place_in_fraction_numerator_and_denominator() -> None:
    editor = fraction_editor()
    assert editor.linear() == "5+((7)/(8))+9"
    editor.place([(2, 0)], 0)  # before the 7
    editor.insert("1")
    assert editor.linear() == "5+((17)/(8))+9"
    editor.place([(2, 1)], 1)  # after the 8
    editor.insert("2")
    assert editor.linear() == "5+((17)/(82))+9"
    editor.place([(2, 1)], 99)  # past the end of the denominator: its end
    assert editor.pos == 2


def test_place_in_a_fraction_inside_a_power() -> None:
    editor = Editor("x")
    editor.insert("^")
    editor.insert("1")
    editor.insert_template(Kind.FRACTION)
    editor.insert("2")
    assert editor.linear() == "x^(((1)/(2)))"
    editor.place([(1, 0), (0, 0)], 0)  # numerator of the fraction in the exponent
    editor.insert("9")
    assert editor.linear() == "x^(((91)/(2)))"
    editor.place([(1, 0)], 0)  # the exponent row itself, before the fraction
    editor.insert("3")
    assert editor.linear() == "x^(3*((91)/(2)))"
    assert editor.path == [(1, 0)]


def test_place_in_a_root() -> None:
    editor = Editor()
    editor.insert("√")
    editor.insert_text("25")
    editor.place([], 1)  # after the root
    editor.insert("+")
    editor.place([(0, 0)], 1)  # between the 2 and the 5
    editor.insert("0")
    assert editor.linear() == "√(205)+"


def test_place_in_matrix_cells() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 2))
    for cell, digit in enumerate("1234"):
        editor.place([(0, cell)], 0)
        editor.insert(digit)
    assert editor.linear() == "[1,2;3,4]"
    editor.place([(0, 3)], 0)  # cell 4, before the 4
    editor.insert("0")
    assert editor.linear() == "[1,2;3,04]"


def test_place_in_a_three_by_three_matrix() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (3, 3))
    editor.place([(0, 8)], 0)
    editor.insert("9")
    editor.place([(0, 4)], 0)
    editor.insert("5")
    assert editor.linear() == "[,,;,5,;,,9]"
    assert editor.path == [(0, 4)]


def test_a_stale_path_is_cut_where_it_stops_being_valid() -> None:
    editor = Editor("ab")
    editor.place([(0, 0)], 3)  # node 0 is a letter, not a template
    assert (editor.path, editor.pos) == ([], 2)
    editor = fraction_editor()
    editor.place([(2, 5)], 0)  # a fraction has no slot 5
    assert editor.path == []
    editor.place([(2, 1), (4, 0)], 7)  # the denominator has no template at 4
    assert (editor.path, editor.pos) == ([(2, 1)], 1)
    editor.place([(40, 0)], 0)
    assert editor.path == []


def test_shift_click_extends_within_a_row() -> None:
    editor = Editor("abcdef")
    editor.place([], 2)
    editor.place([], 5, extend=True)
    assert editor.span == (2, 5)
    editor.place([], 0, extend=True)  # drags back past the start: the anchor stays at 2
    assert editor.span == (0, 2)
    editor.place([], 2, extend=True)
    assert editor.anchor is None  # back to where it began: nothing selected


def test_shift_click_with_no_earlier_selection_starts_at_the_cursor() -> None:
    editor = Editor("abcdef")  # cursor at the end
    editor.place([], 1, extend=True)
    assert editor.span == (1, 6)


def test_shift_click_inside_a_slot_stays_in_the_slot() -> None:
    editor = Editor()
    editor.insert("√")
    editor.insert_text("abcd")
    editor.place([(0, 0)], 1)
    editor.place([(0, 0)], 3, extend=True)
    assert editor.path == [(0, 0)]
    assert editor.span == (1, 3)


def test_shift_click_across_slots_selects_the_whole_template() -> None:
    editor = fraction_editor()
    editor.place([(2, 0)], 1)  # numerator
    editor.place([(2, 1)], 0, extend=True)  # denominator
    assert editor.path == []
    assert editor.span == (2, 3)  # the fraction, as one unit


def test_shift_click_from_outside_into_a_template_takes_it_whole() -> None:
    editor = fraction_editor()
    editor.place([], 1)
    editor.place([(2, 1)], 1, extend=True)
    assert editor.path == []
    assert editor.span == (1, 3)
    editor.place([], 5, extend=True)  # then out to the right
    assert editor.span == (1, 5)


def test_shift_click_backwards_into_a_template() -> None:
    editor = fraction_editor()
    editor.place([], 4)
    editor.place([(2, 0)], 1, extend=True)
    assert editor.span == (2, 4)
    assert editor.pos == 2  # the free end is on the left


def test_shift_click_in_matrix_cells_selects_the_matrix() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 2))
    editor.insert("1")
    editor.insert_text("+")
    editor.place([(0, 2)], 0)
    editor.place([(0, 1)], 0, extend=True)
    assert editor.path == []
    assert editor.span == (0, 1)


def test_target_text_round_trips() -> None:
    for path, pos in [([], 0), ([(2, 1)], 7), ([(1, 0), (0, 3)], 2)]:
        assert parse_target(format_target(path, pos)) == (path, pos)


def test_calculator_place_and_extend_actions() -> None:
    calc = Calculator()
    calc.perform(Binding("insert", "abcdef"))
    calc.perform(Binding("place", format_target([], 2)))
    assert (calc.editor.path, calc.editor.pos) == ([], 2)
    calc.perform(Binding("extend", format_target([], 5)))
    assert calc.editor.span == (2, 5)
    calc.perform(Binding("place", "garbage"))  # malformed: ignored
    assert calc.editor.span == (2, 5)
    calc.perform(Binding("insert", "Z"))  # typing replaces the selection
    assert calc.editor.linear() == "abZf"
