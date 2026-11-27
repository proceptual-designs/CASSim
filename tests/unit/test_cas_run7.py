"""Emulator check 6, run 7 (2026-11-27): the warning triangles and the forms CASSim now gives.

The results are corpus cases (`corpus/seed/039_check6_run7.yaml`); these tests check which rows
carry a warning, which a corpus case cannot say. The warning texts are CASSim's own wording.

Requirements: FR-CALC-007.
"""

from __future__ import annotations

import pytest

from cassim.core import errors
from cassim.core.session import Session


def warnings_of(line: str) -> tuple[str, ...]:
    return Session().eval(line).warnings


@pytest.mark.parametrize(
    "line",
    [
        "(x^2-1)/(x-1)",  # run 5, H9h
        "derivative((x+1)/(x-1),x)",  # R7-A1a
        "tCollect(dotP([5cos(t)-4cos(5t/2),5sin(t)-4sin(5t/2)],"
        "[5cos(t)-4cos(5t/2),5sin(t)-4sin(5t/2)]))",  # R7-A1b
        "expand((x^2+a)/(b*x+c))",  # R7-A4
    ],
)
def test_domain_warning(line: str) -> None:
    assert warnings_of(line) == (errors.DOMAIN_WIDER,)


@pytest.mark.parametrize(
    "line",
    [
        # run 6, R6-C4: derivatives with no triangle
        "derivative(x^2*sin(x),x)",
        "derivative(ln(x^2-1),x)",
        "derivative(x*@e^(-x),x)",
        "derivative((x^2+1)^3,x)",
        "derivative(sqrt(x^2+1),x)",
        "expand((x^2+a)/(b*x+c),x)",  # R7-A4: no triangle with the variable
        "x^2+1",
        "1/x+1/x^2",
    ],
)
def test_no_domain_warning(line: str) -> None:
    assert warnings_of(line) == ()


def test_an_unsolved_equation_warns() -> None:
    """R7-A1c: TI rearranges the equation and warns that there may be more solutions."""
    assert warnings_of("solve(x*@e^(-2y)+y^2*@e^(x)=8*@e^(4),y)") == (errors.MORE_SOLUTIONS,)


def test_a_condition_that_is_not_a_constant_bound_warns() -> None:
    """R7-A1d: `|0<x<h/2` and `|0<x and x<h/2` both warn; `|x>0` does not (R7-A2)."""
    session = Session()
    session.eval("v(x):=2*x*(h-2*x)*(h-x)")
    for constraint in ("0<x<h/2", "0<x and x<h/2"):
        result = session.eval(f"solve(derivative(v(x),x)=0,x)|{constraint}")
        assert errors.CONSTRAINT_IGNORED in result.warnings
    assert warnings_of("solve(x^2=4,x)|x>0") == ()
    assert warnings_of("solve(x^2=4,x)|0<x<5") == ()


def test_logarithms_with_huge_denominators_are_not_combined() -> None:
    """Combining ln(2)/1000003+ln(3)/999983 would build a power with millions of digits; the sum
    is left as it is, and answers at once."""
    import time  # noqa: PLC0415

    start = time.monotonic()
    result = Session().eval("ln(2)/1000003+ln(3)/999983")
    assert result.error is None
    assert time.monotonic() - start < 5
    assert Session().eval("ln(2)/2+ln(3)/3").error is None
