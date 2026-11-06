"""The 2D input editor (FR-CALC-004, FR-DEV-001): key sequences in, TI text and LaTeX out."""

import pytest

from cassim.core.session import Session
from cassim.device.editor import Editor, Kind

# Key sequences use these letters for the non-character keys.
_KEYS = {
    "L": Editor.left,
    "R": Editor.right,
    "U": Editor.up,
    "D": Editor.down,
    "B": Editor.backspace,
    "X": Editor.delete,
    "H": Editor.home,
    "E": Editor.end,
}


def keys(sequence: str) -> Editor:
    """Type `sequence`; the capitals L R U D B X H E are arrows, Backspace, Delete, Home, End."""
    editor = Editor()
    for char in sequence:
        if char in _KEYS:
            _KEYS[char](editor)
        else:
            editor.insert(char)
    return editor


@pytest.mark.parametrize(
    ("sequence", "linear"),
    [
        ("1/3", "((1)/(3))"),
        ("12.5/3", "((12.5)/(3))"),
        ("x/y", "((x)/(y))"),
        ("2x^2R+3", "2x^(2)+3"),
        ("(a+b)/2", "(((a+b))/(2))"),
        ("2^3R/4", "((2^(3))/(4))"),  # a power belongs to the numerator term
        ("1+2/3", "1+((2)/(3))"),  # only the term before the cursor
        ("√2R*3", "√(2)*3"),
        ("1/2R/3", "((((1)/(2)))/(3))"),  # a finished fraction is a term
        ("1/(2/3R)", "((1)/((((2)/(3)))))"),
    ],
)
def test_linear_text_is_what_the_parser_reads(sequence, linear):
    assert keys(sequence).linear() == linear


@pytest.mark.parametrize(
    ("sequence", "wanted"),
    [
        ("1/3R+1/4", "7/12"),
        ("1/(2/3R)", "3/2"),
        ("2^3R+1", "9"),
        ("√2R*√8", "4"),
        ("(1+2)/3", "1"),
        ("3/4R*8", "6"),
    ],
)
def test_the_engine_evaluates_the_linear_text(sequence, wanted):
    """The editor feeds the unchanged parser, so the result is the engine's."""
    result = Session().eval(keys(sequence).linear())
    assert result.error is None
    assert result.text == wanted


def test_fraction_template_from_the_palette_starts_in_the_numerator():
    editor = Editor()
    editor.insert_template(Kind.FRACTION)
    editor.insert_text("1")
    editor.down()
    editor.insert_text("2")
    assert editor.linear() == "((1)/(2))"


def test_up_and_down_move_between_numerator_and_denominator():
    editor = keys("12/34")
    editor.up()
    editor.insert_text("5")
    assert editor.linear() == "((125)/(34))"
    editor.down()
    editor.insert_text("6")
    assert editor.linear() == "((125)/(346))"


def test_right_leaves_a_slot_and_left_comes_back():
    editor = keys("2^3")
    assert editor.path  # still in the exponent
    editor.right()
    assert not editor.path
    editor.left()
    assert editor.path == [(1, 0)]
    assert editor.pos == 1


def test_arrows_walk_through_both_slots_of_a_fraction():
    editor = keys("1/2")
    editor.left()
    editor.left()  # out of the denominator's start into the numerator's end
    assert editor.path == [(0, 0)]
    assert editor.pos == 1
    editor.right()
    editor.right()  # into the denominator
    assert editor.path == [(0, 1)]


def test_backspace_steps_into_a_template_before_deleting_it():
    editor = keys("1/2R")
    editor.backspace()  # into the denominator
    assert editor.path == [(0, 1)]
    editor.backspace()  # deletes the 2
    assert editor.linear() == "((1)/())"


def test_backspace_at_the_start_of_a_slot_dissolves_the_template():
    editor = keys("1/2LB")
    assert editor.linear() == "12"
    assert not editor.path
    assert editor.pos == 1


def test_dissolving_from_the_denominator_keeps_the_cursor_between_the_parts():
    editor = keys("1/2")
    editor.left()  # to the start of the denominator
    editor.backspace()
    assert editor.linear() == "12"
    assert editor.pos == 1


def test_delete_removes_the_next_character_and_enters_a_template():
    editor = keys("12H")
    editor.delete()
    assert editor.linear() == "2"
    editor = keys("√2RH")
    editor.delete()
    assert editor.path == [(0, 0)]


def test_home_and_end_return_to_the_top_level():
    editor = keys("1/2")
    editor.home()
    assert (editor.path, editor.pos) == ([], 0)
    editor.end()
    assert (editor.path, editor.pos) == ([], 1)


def test_clear_empties_the_entry():
    editor = keys("1/2")
    editor.clear()
    assert editor.is_empty
    assert editor.linear() == ""


def test_text_given_to_the_constructor_is_typed():
    assert Editor("2+3").linear() == "2+3"


class TestLatex:
    def test_cursor_is_a_bar_and_empty_slots_are_boxes(self):
        editor = keys("1/")
        tex = editor.latex()
        assert tex.startswith(r"\frac{1}{{\color")  # the cursor is in the empty denominator
        assert r"\square" not in tex
        editor.up()
        assert r"\square" in editor.latex()  # the empty denominator now shows as a box

    def test_cursor_can_be_left_out(self):
        assert keys("1/2").latex(cursor=False) == r"\frac{1}{2}"

    def test_symbols_are_typeset(self):
        assert Editor("2π*ⅇ").latex(cursor=False) == r"2\pi \cdot \mathrm{e}"

    def test_function_names_are_upright_and_variables_are_not(self):
        assert Editor("sin(x)").latex(cursor=False) == r"\mathrm{s}\mathrm{i}\mathrm{n}(x)"
        assert Editor("xy").latex(cursor=False) == "xy"

    def test_a_leading_power_is_valid_latex(self):
        assert keys("^2").latex(cursor=False) == r"{}^{2}"

    def test_nested_templates(self):
        assert keys("1/(√2R)").latex(cursor=False) == r"\frac{1}{(\sqrt{2})}"
