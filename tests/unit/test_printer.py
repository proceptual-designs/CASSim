# Requirements traced here: FR-LANG-003
"""Printer tests: exact text for known cases, and parse/print round trips by Hypothesis."""

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cassim.core import ast
from cassim.core.ast import BINARY_PREC, COMPARE_OPS, POSTFIX_OPS
from cassim.core.errors import TISyntaxError
from cassim.core.format import to_ascii
from cassim.core.lexer import WORD_OPERATORS
from cassim.core.parser import COMMANDS, parse, parse_expression

RESERVED = WORD_OPERATORS | set(COMMANDS) | {"define"}

names = st.one_of(
    st.from_regex(r"[a-z][a-z0-9_]{0,3}", fullmatch=True).filter(lambda s: s not in RESERVED),
    st.sampled_from(["π", "∞", "ⅈ", "@n1", "stat.results", "lib\\fn", "_m", "Σx"]),
)
numbers = st.sampled_from(["0", "1", "2", "1.", ".5", "1.5", "1ᴇ5", "1.ᴇ-13", "0hFF", "0b101"])
strings = st.text(st.characters(codec="utf-8", exclude_categories=("Cs",)), max_size=4).filter(
    lambda s: '"' not in s
)
atoms = st.one_of(
    numbers.map(ast.Number),
    names.map(ast.Name),
    strings.map(ast.String),
    st.just(ast.Dms("30°30'")),
)


def extend(children):
    args = st.lists(children, max_size=3).map(tuple)
    some_args = st.lists(children, min_size=1, max_size=3).map(tuple)
    # A matrix element that is a one-row matrix would flatten, so matrices do not nest here.
    elements = children.filter(lambda e: not isinstance(e, ast.Matrix))
    rows = st.lists(elements, min_size=1, max_size=3).map(tuple)
    relation = st.tuples(st.sampled_from(sorted(COMPARE_OPS)), children)
    return st.one_of(
        st.builds(ast.Call, names, args),
        st.builds(ast.Index, children, some_args),
        st.builds(ast.ListLit, args),
        st.builds(ast.Matrix, st.lists(rows, min_size=1, max_size=3).map(tuple)),
        st.builds(ast.Unary, st.sampled_from(["-", "not", "∠"]), children),
        st.builds(ast.Unary, st.just("#"), names.map(ast.Name)),
        st.builds(ast.Postfix, st.sampled_from(sorted(POSTFIX_OPS)), children),
        st.builds(ast.Binary, st.sampled_from(sorted(BINARY_PREC)), children, children),
        st.builds(ast.Compare, children, st.lists(relation, min_size=1, max_size=3).map(tuple)),
        st.builds(ast.Convert, children, names.map(ast.Name)),
    )


expressions = st.recursive(atoms, extend, max_leaves=12)
targets = st.one_of(
    names.map(ast.Name),
    st.builds(ast.Call, names, st.lists(names.map(ast.Name), max_size=2).map(tuple)),
)
statements = st.one_of(
    expressions,
    st.builds(ast.Assign, targets, expressions),
    st.builds(ast.Store, expressions, targets),
    st.builds(ast.Define, targets, expressions, st.sampled_from([None, "LibPub", "LibPriv"])),
    st.builds(
        ast.Command,
        st.sampled_from(sorted(COMMANDS.values())),
        st.lists(expressions, max_size=3).map(tuple),
    ),
)
lines = st.lists(statements, max_size=3).map(lambda s: ast.Line(tuple(s)))


@pytest.mark.parametrize(
    ("text", "printed"),
    [
        ("2x", "2*x"),
        ("x<=1", "x≤1"),
        ("(x+1)", "x+1"),
        ("(a*b)+c", "a*b+c"),
        ("a*(b+c)", "a*(b+c)"),
        ("a-(b-c)", "a-(b-c)"),
        ("(a-b)-c", "a-b-c"),
        ("2^(3^2)", "2^3^2"),
        ("(2^3)^2", "(2^3)^2"),
        ("(-2)^2", "(-2)^2"),
        ("-(2^2)", "-2^2"),
        ("2^(-1)", "2^-1"),
        ("(a+b)!", "(a+b)!"),
        ("{1,x}", "{1,x}"),
        ("[[1,2],[3,4]]", "[1,2;3,4]"),
        ("solve(x^2=1,x)|x>0", "solve(x^2=1,x) | x>0"),
        ("a and not b", "a and not b"),
        ("255@>Base16", "255▶Base16"),
        ("[1,2;3,4]@t", "[1,2;3,4]ᵀ"),
        ("1 .+x", "1 .+x"),
        ("(2)[1]", "(2)[1]"),
    ],
)
def test_printed_text(text, printed):
    assert str(parse_expression(text)) == printed


@pytest.mark.parametrize(
    ("text", "printed"),
    [
        ("5->a", "5→a"),
        ("x:=1", "x:=1"),
        ("define f(x)=x", "Define f(x)=x"),
        ("sorta l", "SortA l"),
        ("ClearAZ", "ClearAZ"),
        ("OneVar x,1:stat.results", "OneVar x,1:stat.results"),
    ],
)
def test_printed_statements(text, printed):
    assert str(parse(text)) == printed


@settings(deadline=None, max_examples=500)
@given(expressions)
def test_expression_round_trip(tree):
    assert parse_expression(str(tree)) == tree


@settings(deadline=None, max_examples=300)
@given(lines)
def test_line_round_trip(tree):
    assert parse(str(tree)) == tree


FUZZ_ALPHABET = st.sampled_from(
    [*"0123456789.eExyf()[]{},;:+-*/^=<>|!%°'\"&#∠→▶√π ", "and ", "not ", "@>", "@t", ":="]
)


@settings(deadline=None, max_examples=1000)
@given(st.lists(FUZZ_ALPHABET, max_size=14).map("".join))
def test_arbitrary_text_parses_or_reports_a_syntax_error(text):
    try:
        tree = parse(text)
    except TISyntaxError:
        return
    assert parse(str(tree)) == tree


DMS_AND_STRING = '60°15\'45"+"π"'


@pytest.mark.parametrize(
    ("text", "plain"),
    [
        ("2*ⅇ^x", "2*@e^x"),
        ("3+4*ⅈ", "3+4*@i"),
        ("1.ᴇ-13", "1.@E-13"),
        ("x=2*π", "x=2*pi"),
        ("√(2)", "sqrt(2)"),
        ("0≤x≤1", "0<=x<=1"),
        ("a≠b", "a/=b"),
        ("5→a", "5->a"),
        ("x▶Polar", "x@>Polar"),
        ("list▶mat(x)", "list@>mat(x)"),
        ("[1,2]ᵀ", "[1,2]@t"),
        ('"π≤ⅇ"', '"π≤ⅇ"'),
        (DMS_AND_STRING, DMS_AND_STRING.replace("°", "@d", 1)),
        ("e", "e"),
        ("[2∠π,∠π/4]", "[2@<pi,@<pi/4]"),
        ("30°", "30@d"),
        ("30°30'", "30@d30'"),
        ("x→∞", "x->infinity"),
        ("-∞", "-infinity"),
        ("sinh⁻¹(1)+cos⁻¹(x)", "arcsinh(1)+arccos(x)"),
    ],
)
def test_to_ascii(text, plain):
    assert to_ascii(text) == plain


@settings(deadline=None, max_examples=500)
@given(lines)
def test_ascii_text_reads_back_as_the_same_entry(tree):
    plain = to_ascii(str(tree))
    assert to_ascii(str(parse(plain))) == plain


@settings(deadline=None, max_examples=500)
@given(lines)
def test_ascii_output_has_no_symbols_outside_strings(tree):
    outside_strings = re.sub(r'"[^"]*"', "", to_ascii(str(tree)))
    assert not set(outside_strings) & set("ⅇⅈᴇπ√≤≥≠→▶⇒⇔ᵀʳᵍ°∠∞⁻")
