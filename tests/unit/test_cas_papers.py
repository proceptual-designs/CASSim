# Requirements traced here: FR-CAT-001
"""CAS fixes from the VCE exam papers of emulator check 6, run 5 (plan section 3, B1 to B9).

The paper entries themselves are corpus cases (`corpus/seed/038_vce_papers.yaml`); these tests
pin the smaller behaviours behind them.
"""

from cassim.core.session import Session
from cassim.core.settings import PRESETS


def text(*lines: str, course: str = "specialist") -> str:
    session = Session(PRESETS[course])
    result = None
    for line in lines:
        result = session.eval(line)
    assert result is not None
    assert result.error is None, result.error
    return result.text


# B1: no SymPy text


def test_a_root_sympy_can_only_name_is_a_decimal():
    assert text("solve(x^5-x-1=0,x)") == "x=1.167304"


def test_a_root_named_in_a_system_is_a_decimal():
    assert "CRootOf" not in text("solve(x^5-x=1 and y=x,x,y)")


def test_roots_of_a_denominator_are_not_shown_as_a_set_difference():
    assert text("solve(derivative(3*x/(x^3+a*x+2),x)=0,x)") == "x=1"


def test_a_decided_relation_is_lowercase_true_or_false():
    assert text("x^2=4|x=2") == "true"
    assert text("x^2=4|x=3") == "false"


def test_an_antiderivative_with_a_parameter_takes_the_generic_case():
    assert text("integral(sin(a*x),x)") == "-cos(a*x)/a"


def test_a_piecewise_integrand_keeps_its_pieces():
    assert "when" in text("integral(when(x<1,x,1),x,0,t)")


# B2: fMin and fMax of a periodic function return


def test_fmin_of_a_periodic_function_is_the_nearest_lowest_point():
    assert text("fMin(sin(x/2)+cos(2*x),x)") == "x=-1.6557595"


def test_fmax_of_a_periodic_function_returns():
    assert text("fMax(sin(x/2)+cos(2*x),x)") == "x=3.1415927"


def test_fmin_of_a_periodic_function_with_decimals():
    assert text("fMin(sin(2.*x)+cos(0.5*x),x)") == "x=5.5430583"


def test_fmin_in_a_domain_still_solves_exactly():
    assert text("fMin(sin(x),x)|0<=x<=2*pi") == "x=3*π/2"


# B3: definite integrals keep their bounds, or give a decimal


def test_a_definite_integral_with_no_closed_form_is_a_decimal():
    assert text("integral(5*sqrt(5-4*cos(3*t/2)),t,0,pi)") == "36.607844"


def test_a_definite_integral_of_a_special_function_is_a_decimal():
    assert text("integral(sin(x)/x,x,1,2)") == "0.65932991"


def test_a_long_exact_definite_integral_is_a_decimal():
    assert text("integral(pi*(3*x/(x^3+x+2))^2,x,0,2)") == "2.2880103"


def test_a_short_exact_definite_integral_stays_exact():
    assert text("integral(sqrt(1+4*x^2),x,0,1)") == "ln(2+√(5))/4+√(5)/2"


def test_an_unsolved_definite_integral_keeps_its_bounds():
    assert text("integral(5*sqrt(5-4*cos(k*t)),t,0,pi)").endswith(",t,0,π)")
