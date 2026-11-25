"""Pasted text keeps its value (FR-CALC-004): what `insert_linear` builds reads back as what the
parser reads in the text itself. The scan that makes exponents and roots templates is checked by
the parser, and the parser's tree is used when the two disagree."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cassim.core.errors import TIError
from cassim.core.parser import parse_expression
from cassim.device.editor import Editor, Kind, Template
from cassim.device.editor_ast import normal_form
from cassim.device.keys import Binding
from cassim.devices.nspire.pages.calculator import Calculator


def pasted(text: str) -> Editor:
    editor = Editor()
    editor.insert_linear(text)
    return editor


def same_value(text: str, other: str) -> bool:
    return normal_form(parse_expression(text)) == normal_form(parse_expression(other))


@pytest.mark.parametrize(
    ("text", "linear"),
    [
        ("2^-x^2", "2^(-x^(2))"),  # was 2^(-x)^(2): (2^-x)^2
        ("ⅇ^-x^2", "ⅇ^(-x^(2))"),
        ("x^2x", "x^(2)x"),  # was x^(2x); the parser reads x^2*x
        ("3^-2!", "3^(-2!)"),  # was 3^(-2)!: (3^-2)!
        ("x^2ᴇ3+1", "x^(2ᴇ3)+1"),  # was x^(2)ᴇ3+1, which does not parse
        ("a^b^c+1", "a^(b^(c))+1"),
        ("x^2+1", "x^(2)+1"),
        ("x^-2+1", "x^(-2)+1"),
        ("(x-1)^2-1", "(x-1)^(2)-1"),
        ("√(x+1)*2", "√(x+1)*2"),
    ],
)
def test_pasted_exponents_take_what_the_parser_gives_them(text: str, linear: str) -> None:
    editor = pasted(text)
    assert editor.linear() == linear
    assert same_value(text, editor.linear())


def test_pasted_text_keeps_its_spelling() -> None:
    """A `/` stays linear and `2x` stays `2x` when the scan already has the value right
    (decision 0035, stage 2)."""
    editor = pasted("1/2+2x^2")
    assert editor.linear() == "1/2+2x^(2)"
    assert not any(isinstance(n, Template) and n.kind is Kind.FRACTION for n in editor.root)


def test_the_parser_tree_is_used_when_the_scan_changes_the_value() -> None:
    """`x^{1,2}`: the scan has no operand for a list, so the parser's tree is pasted."""
    editor = pasted("x^{1,2}+1")
    assert same_value("x^{1,2}+1", editor.linear())


def test_text_the_parser_cannot_read_is_pasted_as_before() -> None:
    assert pasted("Define f(x)=x^2+1").linear() == "Define f(x)=x^(2)+1"
    assert pasted("^3").linear() == "^(3)"
    assert pasted("+x^2)").linear() == "+x^(2))"


def test_a_spreadsheet_formula_keeps_its_equals_sign() -> None:
    editor = pasted("=2^-a1^2")
    assert editor.linear() == "=2^(-a1^(2))"


def test_paste_inside_a_string_stays_text() -> None:
    editor = Editor()
    editor.insert('"')
    editor.insert_linear("a^2")
    assert editor.linear() == '"a^2'


def test_paste_lands_at_the_cursor_and_the_cursor_follows() -> None:
    editor = Editor()
    editor.insert_text("1+")
    editor.insert_linear("2^-x^2")
    editor.insert("+")
    assert editor.linear() == "1+2^(-x^(2))+"
    assert editor.path == []


def test_system_clipboard_paste_in_the_calculator_keeps_the_value() -> None:
    calc = Calculator()
    calc.perform(Binding("paste", "2^-x^2"))
    assert calc.editor.linear() == "2^(-x^(2))"


_ATOMS = st.sampled_from(["x", "y", "ab", "2", "3.5", "10", "π", "ⅇ", "(x+1)", "f(x)", "-x", "-2"])
_JOINS = st.sampled_from(["^", "^", "^-", "+", "-", "*", "/", "", "!+", "^(", ")", "√(", "√"])


@settings(max_examples=400, deadline=None)
@given(st.lists(st.tuples(_ATOMS, _JOINS), min_size=1, max_size=7), _ATOMS)
def test_any_pasted_text_that_parses_keeps_its_value(
    parts: list[tuple[str, str]], last: str
) -> None:
    text = "".join(atom + join for atom, join in parts) + last
    try:
        wanted = normal_form(parse_expression(text))
    except TIError, RecursionError:
        return
    assert normal_form(parse_expression(pasted(text).linear())) == wanted, text
