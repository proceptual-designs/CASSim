# Requirements traced here: FR-CALC-004
"""Engine text becomes an editor tree with its structure kept (`device/editor_ast.py`).

The bug this guards: a recalled result was typed key by key, so a `^` or `√` took in the rest of
the line (`(x-1)^2-1` came down as `(x-1)^(2-1)`).
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cassim.core import ast
from cassim.core.parser import parse_expression
from cassim.core.session import Session
from cassim.device.editor import Kind, Row, Template, linear_text
from cassim.device.editor_ast import normal_form, row_from_ast, row_from_text
from cassim.device.keys import Binding
from cassim.devices.nspire.pages.calculator import Calculator


def kinds(row: Row) -> list[Kind]:
    """Every template in the tree, outermost first."""
    found: list[Kind] = []
    for node in row:
        if isinstance(node, Template):
            found.append(node.kind)
            for slot in node.slots:
                found += kinds(slot)
    return found


def test_a_power_takes_only_its_exponent() -> None:
    row = row_from_text("(x-1)^2-1")
    assert row == [*"(x-1)", Template(Kind.POWER, [["2"]]), "-", "1"]


def test_a_root_takes_only_its_radicand() -> None:
    row = row_from_text("x=-√(3) or x=√(3)")
    assert row == [*"x=-", Template(Kind.ROOT, [["3"]]), *" or x=", Template(Kind.ROOT, [["3"]])]


def test_division_is_stacked_and_a_fraction_needs_no_brackets() -> None:
    row = row_from_text("2*(a/b)")
    assert row == ["2", "*", Template(Kind.FRACTION, [["a"], ["b"]])]


def test_a_fraction_keeps_its_brackets_as_the_base_of_a_power() -> None:
    row = row_from_text("(a/b)^2")
    assert (row[0], row[2]) == ("(", ")")
    fraction = row[1]
    assert isinstance(fraction, Template)
    assert fraction.kind is Kind.FRACTION


@pytest.mark.parametrize(
    ("text", "kind", "slots"),
    [
        ("root(8,3)", Kind.NTH_ROOT, [["3"], ["8"]]),
        ("log(8,2)", Kind.LOG, [["2"], ["8"]]),
        ("abs(x)", Kind.ABS, [["x"]]),
        ("[1,2;3,4]", Kind.MATRIX, [["1"], ["2"], ["3"], ["4"]]),
    ],
)
def test_calls_and_matrices_become_templates(text: str, kind: Kind, slots: list[Row]) -> None:
    (template,) = row_from_text(text)
    assert isinstance(template, Template)
    assert (template.kind, template.slots) == (kind, slots)


def test_powers_and_roots_nest() -> None:
    text = "2*2^(1/3)/((-1-√(3)*ⅈ)*(27+27*√(3)*ⅈ)^(1/3))"
    row = row_from_text(text)
    assert kinds(row).count(Kind.ROOT) == 2
    assert kinds(row).count(Kind.POWER) == 2
    assert parse_expression(linear_text(row)) == parse_expression(text)


@pytest.mark.parametrize("text", ['"Missing )"', "{1,2,x^2}", "x=3 or x=4", "-x^2", "(-2)^2"])
def test_other_results_read_back_the_same(text: str) -> None:
    assert parse_expression(linear_text(row_from_text(text))) == parse_expression(text)


def test_text_the_parser_cannot_read_is_pasted() -> None:
    assert linear_text(row_from_text("2+")) == "2+"


# ---- random expressions -------------------------------------------------------------------------

_LEAVES = st.one_of(
    st.sampled_from(["0", "1", "2", "12", "1.5", "3.ᴇ-4"]).map(ast.Number),
    st.sampled_from(["x", "y", "ab", "π", "ⅇ", "ⅈ"]).map(ast.Name),
)


def _branches(children: st.SearchStrategy[ast.Expr]) -> st.SearchStrategy[ast.Expr]:
    return st.one_of(
        st.builds(ast.Binary, st.sampled_from(["+", "-", "*", "/", "^"]), children, children),
        st.builds(ast.Unary, st.just("-"), children),
        st.builds(ast.Postfix, st.sampled_from(["!", "%"]), children),
        st.builds(lambda a: ast.Call("√", (a,)), children),
        st.builds(lambda a, b: ast.Call("root", (a, b)), children, children),
        st.builds(lambda a, b: ast.Call("log", (a, b)), children, children),
        st.builds(lambda a: ast.Call("abs", (a,)), children),
        st.builds(lambda a: ast.Call("cos", (a,)), children),
        st.builds(lambda a, b: ast.Call("derivative", (a, b)), children, children),
        st.builds(lambda a, b, c: ast.Call("derivative", (a, b, c)), *[children] * 3),
        st.builds(lambda a, b: ast.Call("∫", (a, b)), children, children),
        st.builds(lambda a, b, c, d: ast.Call("∫", (a, b, c, d)), *[children] * 4),
        st.builds(lambda a, b, c, d: ast.Call("Σ", (a, b, c, d)), *[children] * 4),
        st.builds(lambda a, b: ast.ListLit((a, b)), children, children),
        st.builds(lambda a, b, c, d: ast.Matrix(((a, b), (c, d))), *[children] * 4),
        st.builds(lambda a, b: ast.Compare(a, (("=", b),)), children, children),
        st.builds(ast.Binary, st.just("or"), children, children),
    )


_EXPRESSIONS = st.recursive(_LEAVES, _branches, max_leaves=12)


@settings(max_examples=300, deadline=None)
@given(_EXPRESSIONS)
def test_the_tree_reads_back_as_the_same_expression(node: ast.Expr) -> None:
    """Any expression, in the canonical form the parser gives, survives the trip unchanged."""
    expected = parse_expression(str(node))
    assert normal_form(parse_expression(linear_text(row_from_ast(expected)))) == normal_form(
        expected
    )


# ---- the Calculator page ------------------------------------------------------------------------


def bring_down(text: str) -> Calculator:
    calc = Calculator(Session())
    calc.perform(Binding("insert_linear", text))
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("enter"))
    return calc


def test_a_completed_square_comes_down_unchanged() -> None:
    """Up then Enter on `(x-1)^2-1` gave `(x-1)^(2-1)`: the -1 went into the exponent."""
    calc = bring_down("completeSquare(x^(2)-2x,x)")
    assert calc.history[-1].result.text == "(x-1)^2-1"
    assert parse_expression(calc.editor.linear()) == parse_expression("(x-1)^2-1")


def test_moving_in_a_picked_result_keeps_each_root_to_its_radicand() -> None:
    """The picked row is drawn from its editor once moved into; a root took in the rest."""
    calc = Calculator(Session())
    calc.perform(Binding("insert_linear", "solve(x^2=3,x)"))
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    calc.perform(Binding("end"))
    calc.perform(Binding("left"))
    picked = calc.recall_editor
    assert picked is not None
    assert [node.slots for node in picked.root if isinstance(node, Template)] == [[["3"]]] * 2
    assert picked.path == [(len(picked.root) - 1, 0)]  # Left from the end steps into the root
    assert picked.latex(cursor=False).count(r"\sqrt{3}") == 2
