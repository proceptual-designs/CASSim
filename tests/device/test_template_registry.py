# Requirements traced here: FR-CALC-004
"""Each template kind is declared once (`device/templates.py`, decision 0035 stage 2)."""

import pytest

from cassim.core.parser import parse_expression
from cassim.core.session import Session
from cassim.device.editor import Editor, Row, Template, linear_text
from cassim.device.editor_ast import row_from_text
from cassim.device.templates import GRIDS, SPECS, WALKED, Kind


def test_every_kind_is_declared() -> None:
    assert set(SPECS) == set(Kind)


@pytest.mark.parametrize("kind", list(Kind))
def test_every_kind_makes_an_empty_template_and_draws(kind: Kind) -> None:
    editor = Editor()
    editor.insert_template(kind)
    assert editor.root[0] == Template.empty(kind, (2, 2))
    assert editor.latex()  # every kind has LaTeX
    editor.linear()  # and linear text, even with empty slots


def test_grids_and_walked_kinds_come_from_the_specs() -> None:
    assert GRIDS == {Kind.MATRIX: 0, Kind.PIECEWISE: 2, Kind.SYSTEM: 1, Kind.LIST: 0}
    assert {Kind.INTEGRAL, Kind.SUM, Kind.LIMIT, Kind.DERIVATIVE} <= WALKED
    assert Kind.FRACTION not in WALKED


_NAMES = "abcd"
CALLED = [kind for kind, spec in SPECS.items() if spec.call is not None]


@pytest.mark.parametrize("kind", CALLED)
def test_a_template_written_as_a_call_reads_back_as_itself(kind: Kind) -> None:
    """The call that writes a template is the one the bridge reads, so they cannot drift."""
    spec = SPECS[kind]
    slots: list[Row] = [[_NAMES[i]] for i in range(spec.slots)]
    if kind is Kind.DERIVATIVE2:
        slots = [["x"], ["a"]]
    template = Template(kind, slots)
    text = linear_text([template])
    parse_expression(text)  # the parser reads it
    assert row_from_text(text) == [template]


def test_a_second_derivative_reads_back_as_the_second_derivative_template() -> None:
    (template,) = row_from_text("derivative(f,x,2)")
    assert isinstance(template, Template)
    assert template.kind is Kind.DERIVATIVE2
    (nth,) = row_from_text("derivative(f,x,n)")
    assert isinstance(nth, Template)
    assert (nth.kind, nth.slots) == (Kind.DERIVATIVE_N, [["n"], ["x"], ["f"]])


def test_an_indefinite_integral_reads_back_as_the_antiderivative() -> None:
    integral = Template(Kind.INTEGRAL, [[], [], ["f"], ["x"]])
    assert row_from_text(linear_text([integral])) == [Template(Kind.ANTIDERIVATIVE, [["f"], ["x"]])]


def test_a_function_template_after_a_term_is_a_product() -> None:
    row = ["x", Template(Kind.ABS, [["y"]])]
    assert linear_text(row) == "x*abs(y)"


@pytest.mark.parametrize(
    ("row", "value"),
    [
        # `x((1)/(2))` was read as a call of a function x, and `x[1,2]` as indexing
        (["x", Template(Kind.FRACTION, [["1"], ["2"]])], "x/2"),
        (["2", Template(Kind.FRACTION, [["1"], ["2"]])], "1"),
        (["x", Template(Kind.MATRIX, [["1"], ["2"]], 2)], "[x,2*x]"),
    ],
)
def test_a_fraction_or_matrix_after_a_term_is_a_product(row: list, value: str) -> None:
    assert Session().eval(linear_text(row)).text == value
