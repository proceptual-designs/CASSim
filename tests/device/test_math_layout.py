# Requirements traced here: FR-CALC-004, FR-CALC-005
"""The maths layout (decision 0038): where each glyph and each cursor stop is, from the fonts'
own metrics, with no drawing. The cursor and the selection are arithmetic on the result, so they
cannot move the maths."""

import pytest

from cassim.device import math_layout as ml
from cassim.device.editor import Editor, Row, Template
from cassim.device.editor_ast import row_from_text
from cassim.device.templates import Kind

BIG = "x=-((1+√(2))^(1/3))/2+1/(2*(1+√(2))^(1/3))+ⅈ*(√(3)/(2*(1+√(2))^(1/3))+√(3)*(1+√(2))^(1/3)/2)"


def _runs(layout: ml.Layout) -> list[ml.Glyphs]:
    return [item for item in layout.items if isinstance(item, ml.Glyphs)]


def _texts(layout: ml.Layout) -> dict[str, ml.Glyphs]:
    return {run.text: run for run in _runs(layout)}


def _rows(row: Row, path: ml.Path = ()) -> list[tuple[ml.Path, Row]]:
    found = [(path, row)]
    for index, node in enumerate(row):
        if isinstance(node, Template):
            for slot, inner in enumerate(node.slots):
                found += _rows(inner, (*path, (index, slot)))
    return found


def test_every_declared_kind_is_set() -> None:
    assert set(Kind) == ml.SET_KINDS


@pytest.mark.parametrize("kind", list(Kind))
def test_every_kind_has_a_place_for_each_slot(kind: Kind) -> None:
    editor = Editor("1+")
    editor.insert_template(kind)
    layout = ml.layout(editor.root)
    for path, row in _rows(editor.root):
        place = layout.rows[path]
        assert len(place.gaps) == max(len(row), 0) + 1 if row or not path else len(place.gaps) == 1
        assert place.x0 <= place.gaps[0] <= place.gaps[-1] <= place.x1 + 1e-9


def test_a_line_of_plain_characters_is_one_run() -> None:
    """What made the old entry line slow was a control or ten a character."""
    layout = ml.layout(row_from_text("12345.678"))
    assert [run.text for run in _runs(layout)] == ["12345.678"]
    assert layout.width == pytest.approx(0.5 * 8 + 0.278)


def test_a_large_result_is_a_few_dozen_items() -> None:
    layout = ml.layout(row_from_text(BIG))
    assert len(layout.items) < 70


def test_a_binary_operator_is_spaced_and_a_sign_is_not() -> None:
    """TeX's rule: a medium space either side of an operator between two terms; none round a
    sign."""
    digit, minus = 0.5, 0.778
    assert ml.width(row_from_text("1-2")) == pytest.approx(2 * digit + minus + 2 * 4 / 18)
    assert ml.width(row_from_text("-2")) == pytest.approx(digit + minus)
    assert ml.width(list("(-2)")) == pytest.approx(digit + minus + 2 * 0.389)


def test_a_relation_has_a_thick_space_and_scripts_have_none() -> None:
    assert ml.width(row_from_text("1=2")) == pytest.approx(1.0 + 0.778 + 2 * 5 / 18)
    exponent = ml.layout(row_from_text("x^(1+2)")).rows[((1, 0),)]
    assert exponent.x1 - exponent.x0 == pytest.approx(0.7 * (0.5 + 0.778 + 0.5))


def test_the_constants_are_drawn_as_bold_letters() -> None:
    """ⅇ is a bold upright e and ⅈ a bold italic i, not the double-struck letters of a fallback
    font (no KaTeX font has those). The text keeps ⅇ and ⅈ."""
    row = row_from_text("ⅇ+ⅈ")
    texts = _texts(ml.layout(row))
    assert texts["e"].font == ml.BOLD
    assert texts["i"].font == ml.BOLD_ITALIC
    assert "ⅇ" not in texts
    assert "ⅈ" not in texts


def test_names_are_upright_bold_or_italic() -> None:
    """A Catalog name is upright, a name the Problem defines bold, any other a variable."""
    row = row_from_text("sin(x)+abc")
    texts = _texts(ml.layout(row, lambda name: name == "abc"))
    assert texts["sin("].font == ml.MAIN
    assert texts["x"].font == ml.ITALIC
    assert texts["abc"].font == ml.BOLD


def test_characters_no_font_has_are_drawn_from_ones_it_has() -> None:
    texts = _texts(ml.layout(list("3ᴇ4")))
    assert "3E4" in texts  # the exponent marker is an upright E
    layout = ml.layout(list("a≠b"))
    assert any(run.text == chr(0xE020) for run in _runs(layout))  # the stroke through `=`
    raised = next(run for run in _runs(ml.layout(list("5ʳ"))) if run.text == "r")
    assert raised.scale == pytest.approx(0.7)
    assert raised.y < 0  # set as a superscript


def test_an_unknown_character_falls_back_to_the_apps_font() -> None:
    run = _runs(ml.layout(["漢"]))[0]
    assert run.font == ml.FALLBACK
    assert not run.joins  # its width is a guess, so nothing is joined on to it


def test_an_empty_slot_is_a_box_and_an_empty_line_is_nothing() -> None:
    editor = Editor()
    assert ml.layout(editor.root).items == []
    assert ml.layout(editor.root).rows[()].gaps == [0.0]
    editor.insert_template(Kind.FRACTION)
    layout = ml.layout(editor.root)
    assert [run.text for run in _runs(layout)].count("□") == 2
    top = layout.rows[((0, 0),)]
    assert top.gaps == [pytest.approx((top.x0 + top.x1) / 2)]  # the cursor in the box


def test_brackets_grow_round_a_fraction_but_not_round_a_power() -> None:
    half = Template(Kind.FRACTION, [["1"], ["2"]])
    tall = ml.layout(["(", half, ")"])
    assert any(run.font.startswith("Size") for run in _runs(tall))
    flat = ml.layout(["(", "x", Template(Kind.POWER, [["2"]]), ")"])
    assert not any(run.font.startswith("Size") for run in _runs(flat))
    assert ml.stretched_brackets(["(", half, ")", "+", "(", "3", ")"]) == {0: 2}


def test_a_radical_grows_with_its_radicand() -> None:
    plain = next(r for r in _runs(ml.layout(row_from_text("√(49)"))) if r.text == "√")
    tall = next(r for r in _runs(ml.layout(row_from_text("√(1/(2/3))"))) if r.text == "√")
    assert plain.font == ml.MAIN
    assert tall.font.startswith("Size")


def test_the_brackets_enter_will_add_are_faint() -> None:
    layout = ml.layout(list("sin(2"), closers=")")
    faint = [run for run in _runs(layout) if run.faint]
    assert [run.text for run in faint] == [")"]
    assert layout.rows[()].gaps[-1] < layout.width  # the cursor stops before them


def test_a_line_is_measured_in_lines_of_text() -> None:
    assert ml.lines(row_from_text("x+1")) == 1
    assert 1.1 < ml.lines(row_from_text("1/2")) < 1.4  # a fraction in a line is set small
    assert ml.lines(row_from_text("(1/2)/3")) > ml.lines(row_from_text("1/2")) + 0.2
    assert 1.0 < ml.lines(row_from_text("x^2")) < 1.2
    matrix = Editor()
    matrix.insert_template(Kind.MATRIX, (3, 2))
    assert 3.5 <= ml.lines(matrix.root) < 4


# ---- the cursor, the selection and clicks -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [BIG, "∫(x^2*sin(x),x,0,π)+Σ(1/n^2,n,1,10)", "[1/2,x^2;√(3),abs(x-1)]*{1,2,3}", "a:=3"],
)
def test_a_click_on_a_cursor_stop_gives_a_place_drawn_there(text: str) -> None:
    """Every place the cursor can be can be clicked, at any depth: a click where the cursor is
    drawn for a place gives a place whose cursor is drawn there. (Two places can share a spot:
    the end of a radicand and the place after its root.)"""
    row = row_from_text(text)
    layout = ml.layout(row)
    for path, inner in _rows(row):
        for pos in range(len(inner) + 1):
            x, top, bottom = layout.caret(path, pos)
            found, at = layout.hit(x, (top + bottom) / 2)
            assert layout.caret(found, at)[0] == pytest.approx(x, abs=0.05), (path, pos)


def test_a_click_inside_a_character_goes_to_its_nearer_side_in_its_own_row() -> None:
    row = row_from_text("12+(34/567)^2")
    layout = ml.layout(row)
    numerator = layout.rows[((4, 0),)]
    left, top, width, height = numerator.nodes[1]  # the 4
    y = top + height / 2
    assert layout.hit(left + 0.2 * width, y) == (((4, 0),), 1)
    assert layout.hit(left + 0.8 * width, y) == (((4, 0),), 2)
    denominator = layout.rows[((4, 1),)]
    left, top, width, height = denominator.nodes[0]
    assert layout.hit(left + 0.2 * width, top + height / 2) == (((4, 1),), 0)


def test_the_width_above_a_fraction_bar_is_the_numerators() -> None:
    """A short numerator over a long denominator: a click beside it, above the bar, is still in
    the numerator (as the old entry line gave a slot the width of its fraction)."""
    row = row_from_text("1/23456")
    layout = ml.layout(row)
    top, bottom = layout.rows[((0, 0),)], layout.rows[((0, 1),)]
    y = top.baseline - 0.2
    assert layout.hit(bottom.x0 + 0.05, y) == (((0, 0),), 0)
    assert layout.hit(bottom.x1 - 0.05, y) == (((0, 0),), 1)


def test_a_matrix_cells_padding_is_the_cells() -> None:
    editor = Editor()
    editor.insert_template(Kind.MATRIX, (2, 2))
    layout = ml.layout(editor.root)
    for cell in range(4):
        left, top, width, _height = layout.cell(((0, cell),))
        assert layout.hit(left + width / 2, top + 0.1) == (((0, cell),), 0)


def test_a_click_outside_the_maths_goes_to_the_nearest_end() -> None:
    layout = ml.layout(row_from_text("1/2+3"))
    assert layout.hit(-5.0, 0.0) == ((), 0)
    assert layout.hit(99.0, 3.0) == ((), 3)


def test_the_cursor_is_a_line_of_its_rows_text_whatever_is_beside_it() -> None:
    layout = ml.layout(row_from_text("1+(2/3)^4"))
    _x, top, bottom = layout.caret((), 2)  # beside the tall bracket
    assert (top, bottom) == (pytest.approx(-0.75), pytest.approx(0.25))
    _x, top, bottom = layout.caret(((5, 0),), 1)  # in the exponent, at script size
    assert bottom - top == pytest.approx(0.7)


def test_a_selection_covers_its_nodes_at_their_full_height() -> None:
    layout = ml.layout(row_from_text("1+2/3+4"))
    x, y, width, height = layout.selection((), 1, 3) or (0, 0, 0, 0)
    plus, fraction = layout.rows[()].nodes[1], layout.rows[()].nodes[2]
    assert x == pytest.approx(plus[0])
    assert x + width == pytest.approx(fraction[0] + fraction[2])
    assert height == pytest.approx(fraction[3])
    assert y == pytest.approx(fraction[1])
    assert layout.selection((), 2, 2) is None


def test_the_layout_knows_nothing_of_the_cursor() -> None:
    """The point of decision 0038: the maths is set from the tree alone, so nothing the cursor
    or the selection does can change a glyph's size or place."""
    editor = Editor()
    editor.root = row_from_text(BIG)
    editor.home()
    before = ml.layout(editor.root)
    for _ in range(25):
        editor.right()
    editor.select_right()
    assert ml.layout(editor.root).items == before.items
