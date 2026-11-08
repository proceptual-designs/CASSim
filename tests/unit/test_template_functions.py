"""Functions behind the 2D templates: `root(` (nth root) and `piecewise(` (FR-CALC-005)."""

import pytest

from cassim.core.session import Session


def text(line: str, session: Session | None = None) -> str:
    return (session or Session()).eval(line).text


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("root(8,3)", "2"),
        ("root(-8,3)", "-2"),  # an odd root of a negative number is real, as on TI
        ("root(16,4)", "2"),
        ("root(x,3)", "x^(1/3)"),
        ("log(8,2)", "3"),  # the log-with-base template
    ],
)
def test_root_and_log_templates(line: str, wanted: str) -> None:
    assert text(line) == wanted


def test_piecewise_picks_the_first_true_piece() -> None:
    session = Session()
    text("Define f(x)=piecewise(x^2,x<0,x,x>=0)", session)
    assert [text(f"f({x})", session) for x in (-3, 0, 3)] == ["9", "0", "3"]


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("piecewise(1,2>3,5)", "5"),  # a last value with no condition is the otherwise
        ("piecewise(1,2>3)", "undef"),  # no piece true
        ("piecewise(1,2<3,1/0,1>0)", "1"),  # only the chosen piece is evaluated
    ],
)
def test_piecewise_choices(line: str, wanted: str) -> None:
    assert text(line) == wanted


def test_piecewise_stays_symbolic_while_undecided() -> None:
    result = Session().eval("piecewise(x^2,x<0,x,x>=0)")
    assert "cases" in result.latex


def test_undef_is_drawn_as_undef_not_nan() -> None:
    assert Session().eval("1/0").latex == r"\text{undef}"


def test_an_even_root_of_a_negative_is_non_real_in_real_mode() -> None:
    """²√-4 gives "Non-real result" on the device (templates run, part 1)."""
    assert text("root(-4,2)") == "Non-real result"
    session = Session()
    session.set(domain="rectangular")
    assert text("root(-4,2)", session) == "2*ⅈ"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("linSolve({x+y=3,x-y=1},{x,y})", "{2,1}"),  # the device's own example
        ("linSolve(x+y=3 and x-y=1,{x,y})", "{2,1}"),
        ("linSolve({x+y=3},{x,y})", "{3-y,y}"),
        ("linSolve({x+y=3,x+y=4},{x,y})", "No solution found"),
    ],
)
def test_lin_solve(line: str, wanted: str) -> None:
    assert text(line) == wanted


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("invBinomN(0.5,0.5,5)", "12"),  # the device's example: P(X<=5) is exactly 0.5 at n=11
        ("invBinomN(0.05,0.1,0)", "29"),  # fewest trials for P(at least one) > 0.95
    ],
)
def test_inverse_binomial_n(line: str, wanted: str) -> None:
    assert text(line) == wanted
