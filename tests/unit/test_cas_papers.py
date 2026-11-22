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


# B4: solve falls back to decimal roots, with a warning (FR-CALC-007)


def warnings(*lines: str) -> tuple[str, ...]:
    session = Session(PRESETS["specialist"])
    result = None
    for line in lines:
        result = session.eval(line)
    assert result is not None
    return result.warnings


def test_solve_with_no_exact_answer_gives_decimal_roots():
    assert text("solve(@e^(-2*x)-2*@e^(-x)+1=x+2,x)") == "x=-0.75040316"


def test_a_numeric_solution_has_a_warning():
    assert warnings("solve(cos(x)=x,x)") == ("Solved numerically: there may be other solutions",)


def test_an_exact_solution_has_no_warning():
    assert warnings("solve(x^2=4,x)") == ()


def test_a_numeric_search_finds_every_crossing():
    assert text("solve(cos(x)=x/5,x)").count(" or ") == 2


def test_an_equation_with_a_parameter_is_still_echoed():
    assert text("solve(cos(x)=a*x,x)").startswith("solve(")


# B5: `|` constraints


def test_a_binding_is_applied_after_implicit_differentiation():
    assert text("eqn:=x*y^2+y=x^3", "impDif(eqn,x,y)|x=1 and y=1") == "2/3"


def test_a_binding_reaches_a_user_functions_result():
    assert text("eq(z):=z^2+a*z+b=0", "eq(z)|a=-3 and b=2") == "z^2-3*z+2=0"


def test_a_bound_with_a_parameter_filters_roots_and_names_the_parameter():
    assert text("solve(x*(x-h)*(2*x-h)=0,x)|0<x<3*h/4") == "x=h/2 and h>0"


def test_a_derivative_at_a_point_still_works():
    assert text("derivative(x^3,x)|x=2") == "12"


# B6: vectors


def test_the_derivative_of_a_vector_valued_function_is_taken_element_by_element():
    assert text("r(t):=[t^2,sin(t)]", "dr(t):=derivative(r(t),t)", "dr(0)") == "[0,1]"


def test_the_integral_of_a_vector_is_taken_element_by_element():
    assert text("integral([t,t^2],t,0,1)") == "[1/2,1/3]"


def test_a_vector_equation_is_solved_by_component():
    assert text("solve([2,3,1]+t*[1,2,-1]=[1,3,2]+s*[-1,-1,1],s,t)") == "s=-2 and t=1"


def test_a_vector_equation_with_too_many_components_solves_for_the_other_variable():
    assert text("solve([2+l;r-l;-3+4*l]=[4;3;t],l,t)") == "l=2 and r=5 and t=5"


# B7: derivatives and substitutions in TI's simplified form


def test_the_derivative_of_a_product_of_polynomials_is_expanded():
    assert text("derivative(2*x*(25-2*x)*(25-x),x)") == "12*x^2-300*x+1250"


def test_the_derivative_of_a_power_stays_factored():
    assert text("derivative((x^2+1)^3,x)") == "6*x*(x^2+1)^2"


def test_a_derivative_with_logarithms_is_cancelled():
    assert text("derivative(ln(x^2-1)-ln(1-x),x)") == "1/(x+1)"


def test_a_derivative_with_a_root_is_over_one_denominator():
    assert "/" in text("derivative(t/sqrt(t^2+k),t)")
    assert "+" not in text("derivative(t/sqrt(t^2+k),t)").split("/")[0]


def test_a_substituted_product_is_multiplied_out_when_shorter():
    assert text("v(x):=2*x*(h-2*x)*(h-x)", "v(x)|x=h/2") == "0"
    assert text("(x+1)^2|a=2") == "(x+1)^2"


# B8: the printer


def test_a_negative_exponent_of_e_stays_on_top():
    assert text("derivative(@e^(-2*a)-2*@e^(-a)+1,a)") == "2*ⅇ^(-a)-2*ⅇ^(-2*a)"
    assert text("@e^(-x)") == "ⅇ^(-x)"


def test_a_number_is_not_multiplied_into_a_bracket_over_a_denominator():
    assert text("derivative(3*x/(x^3+x+2),x)").startswith("-6*(x^3-1)/")


def test_ordinary_quotients_print_as_before():
    assert text("3*x/4") == "3*x/4"
    assert text("2/(3*x)") == "2/(3*x)"
    assert text("x^(-1/2)") == "1/√(x)"
