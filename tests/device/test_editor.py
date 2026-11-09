"""The 2D input editor (FR-CALC-004, FR-DEV-001): key sequences in, TI text and LaTeX out.

Behaviour follows the emulator run in docs/testing/emulator-editor-results.md (decision 0017).
"""

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
    "T": Editor.tab,
    "F": lambda editor: editor.insert_template(Kind.FRACTION),
}


def keys(sequence: str) -> Editor:
    """Type `sequence`; L R U D B X H E T are keys (arrows, Backspace, Delete, Home, End, Tab).

    F is the fraction template from the palette.
    """
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
        ("1F3", "((1)/(3))"),
        ("12.5F3", "((12.5)/(3))"),
        ("xFy", "((x)/(y))"),
        ("2x^2R+3", "2x^(2)+3"),
        ("(a+b)F2", "((a+b)/(2))"),  # a plain sum loses its brackets
        ("(a+b)^2RFc", "(((a+b)^(2))/(c))"),  # a power keeps them
        ("2^3RF4", "((2^(3))/(4))"),  # a power belongs to the numerator term
        ("1+2F3", "1+((2)/(3))"),  # only the term before the cursor
        ("2*3F4", "((2*3)/(4))"),  # a product goes on top
        ("1/3", "1/3"),  # a typed slash stays linear
        ("1/3x", "1/3x"),
        ("√2R*3", "√(2)*3"),
        ("1F2RF3", "((((1)/(2)))/(3))"),  # a finished fraction is a term
        ("1F(2F3R)", "((1)/((((2)/(3)))))"),
    ],
)
def test_linear_text_is_what_the_parser_reads(sequence, linear):
    assert keys(sequence).linear() == linear


@pytest.mark.parametrize(
    ("sequence", "wanted"),
    [
        ("1F3R+1F4", "7/12"),
        ("1F(2F3R)", "3/2"),
        ("2^3R+1", "9"),
        ("√2R*√8", "4"),
        ("(1+2)F3", "1"),
        ("3F4R*8", "6"),
    ],
)
def test_the_engine_evaluates_the_linear_text(sequence, wanted):
    """The editor feeds the unchanged parser, so the result is the engine's."""
    result = Session().eval(keys(sequence).linear())
    assert result.error is None
    assert result.text == wanted


def test_fraction_template_on_an_empty_line_starts_in_the_numerator():
    editor = Editor()
    editor.insert_template(Kind.FRACTION)
    editor.insert_text("1")
    editor.down()
    editor.insert_text("2")
    assert editor.linear() == "((1)/(2))"


def test_up_and_down_move_between_numerator_and_denominator():
    editor = keys("12F34")
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
    editor = keys("1F2")
    editor.left()
    editor.left()  # out of the denominator's start, to the left of the fraction
    assert editor.path == []
    assert editor.pos == 0
    editor.right()  # into the numerator
    editor.tab()  # into the denominator
    assert editor.path == [(0, 1)]
    editor.shift_tab()  # back, at the end of the numerator
    assert editor.path == [(0, 0)]
    editor.shift_tab()  # out on the left
    assert editor.path == []
    assert editor.pos == 0


def test_backspace_highlights_a_template_then_deletes_it():
    editor = keys("1F2R")
    editor.backspace()
    assert editor.selected
    assert editor.linear() == "((1)/(2))"
    editor.backspace()
    assert editor.is_empty
    editor.backspace()  # a third press does nothing
    assert editor.is_empty


def test_typing_over_a_highlighted_template_replaces_it():
    editor = keys("1F2RB")
    editor.insert("9")
    assert editor.linear() == "9"


def test_moving_away_clears_the_highlight():
    editor = keys("1F2RBL")
    assert not editor.selected
    assert editor.linear() == "((1)/(2))"


def test_backspace_at_the_start_of_the_numerator_highlights_the_fraction():
    editor = keys("12F34U")
    editor.left()
    editor.left()
    editor.backspace()
    assert editor.path == []
    assert editor.selected
    assert editor.linear() == "((12)/(34))"


def test_right_leaves_the_numerator():
    editor = keys("12F34U")
    editor.right()
    editor.right()  # end of the numerator: out of the fraction
    assert editor.path == []
    assert editor.pos == 1


def test_an_operator_first_on_an_empty_line_takes_ans():
    assert Editor("/3").linear() == "Ans/3"
    assert Editor("-3").linear() == "Ans-3"
    assert Editor("^2").linear() == "Ans^(2)"
    assert Editor("x+1").linear() == "x+1"
    assert keys("F").linear() == "(()/())"  # the template leaves an empty numerator


def test_backspace_at_the_start_of_a_slot_dissolves_the_template():
    editor = keys("1F2LB")
    assert editor.linear() == "12"
    assert not editor.path
    assert editor.pos == 1


def test_dissolving_from_the_denominator_keeps_the_cursor_between_the_parts():
    editor = keys("1F2")
    editor.left()  # to the start of the denominator
    editor.backspace()
    assert editor.linear() == "12"
    assert editor.pos == 1


def test_delete_removes_the_next_character_and_highlights_a_template():
    editor = keys("12H")
    editor.delete()
    assert editor.linear() == "2"
    editor = keys("√2RH")
    editor.delete()
    assert editor.selected
    editor.delete()
    assert editor.is_empty


def test_backspace_in_an_empty_slot_removes_the_template():
    for sequence in ("x^", "√", "F"):
        editor = keys(sequence)
        editor.backspace()
        assert editor.linear() == ("x" if sequence == "x^" else "")


def test_home_and_end_return_to_the_top_level():
    editor = keys("1F2")
    editor.home()
    assert (editor.path, editor.pos) == ([], 0)
    editor.end()
    assert (editor.path, editor.pos) == ([], 1)


def test_clear_empties_the_entry():
    editor = keys("1F2")
    editor.clear()
    assert editor.is_empty
    assert editor.linear() == ""


def test_text_given_to_the_constructor_is_typed():
    assert Editor("2+3").linear() == "2+3"


class TestLatex:
    def test_cursor_is_a_bar_and_empty_slots_are_boxes(self):
        editor = keys("1F")
        tex = editor.latex()
        assert tex.startswith(r"\frac{1}{{\color")  # the cursor is in the empty denominator
        assert r"\square" not in tex
        editor.up()
        assert r"\square" in editor.latex()  # the empty denominator now shows as a box

    def test_cursor_can_be_left_out(self):
        assert keys("1F2").latex(cursor=False) == r"\frac{1}{2}"

    def test_symbols_are_typeset(self):
        assert Editor("2π*ⅇ").latex(cursor=False) == r"2\pi \cdot \mathbf{e}"

    def test_ans_and_the_logic_words_are_bold_and_keep_their_spaces(self):
        """`ans`, `and` and `or` are not variables, and TeX would drop the spaces round them."""
        tex = Editor("ans x=1 and y=2 or z").latex(cursor=False)
        assert r"\mathbf{a}\mathbf{n}\mathbf{s}\ x=1\ \mathbf{a}\mathbf{n}\mathbf{d}\ y=2" in tex
        assert tex.endswith(r"\ \mathbf{o}\mathbf{r}\ z")
        assert Editor("band").latex(cursor=False) == "band"  # only the whole word

    def test_system_result_names_are_one_bold_name(self):
        """`tvm.pmt` and `stat.sx` are the calculator's own variables, not letters and a dot."""
        assert (
            Editor("tvm.n").latex(cursor=False)
            == r"\mathbf{t}\mathbf{v}\mathbf{m}\mathbf{.}\mathbf{n}"
        )
        assert Editor("x.n").latex(cursor=False) == "x.n"

    def test_typed_constants_are_bold_upright(self):
        """`@e` and `@i` show as the constants; `@exp` and a plain `e` do not."""
        assert Editor("2@e").latex(cursor=False) == r"2\mathbf{e}"
        assert Editor("@i").latex(cursor=False) == r"\mathbf{i}"
        assert Editor("@ex").latex(cursor=False) == "@ex"
        assert Editor("e").latex(cursor=False) == "e"

    def test_defined_function_names_are_bold(self):
        """Only names the engine knows (or the user defined) turn bold, and only before `(`."""
        known = {"sin", "f"}.__contains__
        assert Editor("sin(x)").latex(cursor=False, is_function=known) == (
            r"\mathbf{s}\mathbf{i}\mathbf{n}(x)"
        )
        assert Editor("f(x)").latex(cursor=False, is_function=known) == r"\mathbf{f}(x)"
        assert Editor("g(x)").latex(cursor=False, is_function=known) == "g(x)"
        assert Editor("sin").latex(cursor=False, is_function=known) == "sin"
        assert Editor("xy").latex(cursor=False) == "xy"

    def test_cursor_bar_is_no_taller_than_a_digit(self):
        """A taller bar pushed the denominator down while it was being typed."""
        assert r"\rule[-0.15em]{0.06em}{0.8em}" in keys("1F2").latex()

    def test_a_leading_power_is_valid_latex(self):
        assert keys("^2").latex(cursor=False).endswith(r"{}^{2}")  # after the inserted Ans

    def test_nested_templates(self):
        assert keys("1F(√2R)").latex(cursor=False) == r"\frac{1}{(\sqrt{2})}"


def test_matrix_template_reads_as_ti_text_and_moves_by_cells() -> None:
    """The grid template: Tab goes cell by cell, Up and Down by row (FR-CALC-004)."""
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 2))
    for cell in ("1", "2", "3", "4"):
        editor.insert_text(cell)
        editor.tab()
    assert editor.linear() == "[1,2;3,4]"
    editor.left()  # back into the last cell
    editor.up()
    editor.insert_text("9")
    assert editor.linear() == "[1,29;3,4]"
    editor.down()
    editor.insert_text("8")
    assert editor.linear() == "[1,29;3,48]"


def test_matrix_backspace_steps_back_without_merging_cells() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (1, 2))
    editor.insert_text("5")
    editor.tab()
    editor.backspace()  # at the start of the second cell
    assert editor.linear() == "[5,]"
    assert editor.path == [(0, 0)]


def test_matrix_latex_is_a_bracketed_grid() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 1))
    latex = editor.latex(cursor=False)
    assert r"\begin{matrix}" in latex
    assert r"\\" in latex
