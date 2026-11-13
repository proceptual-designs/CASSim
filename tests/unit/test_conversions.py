"""Conversions, strings, polar form, display formats, the inverse spellings and the long tail."""

from decimal import Decimal

import pytest

from cassim.core.format import decimal_text, to_ascii
from cassim.core.session import Session, same_value
from cassim.core.settings import Angle, Domain, Settings

DEGREE = Settings(angle=Angle.DEGREE)
GRADIAN = Settings(angle=Angle.GRADIAN)
POLAR = Settings(domain=Domain.POLAR)


def run(*lines, settings=None):
    session = Session(settings)
    result = None
    for line in lines:
        result = session.eval(line)
    assert result is not None
    return result


def text(*lines, settings=None):
    result = run(*lines, settings=settings)
    assert result.error is None, result.error
    return result.text


def error(*lines, settings=None):
    return run(*lines, settings=settings).error


def same(line, wanted, settings=None, tolerance=None):
    got = run(line, settings=settings).value
    expected = run(wanted).value
    assert got is not None
    assert expected is not None
    assert same_value(got, expected, tolerance), f"{line} gave {text(line, settings=settings)}"


# ---- inverse functions: arcsin, sin⁻¹ and sin^-1 are one function ------------------------------

CIRCULAR = ["sin", "cos", "tan", "sec", "csc", "cot"]


@pytest.mark.parametrize("name", [*CIRCULAR, *(f"{n}h" for n in CIRCULAR[:3])])
def test_every_spelling_of_an_inverse_is_the_same_function(name):
    argument = "1/2" if name in ("sin", "cos") else "3/4"
    argument = (
        "2"
        if name in ("sec", "csc", "cosh") or (name.endswith("h") and name[:-1] in ("sec", "csc"))
        else argument
    )  # arccosh needs an argument of 1 or more to be real
    arc = run(f"arc{name}({argument})")
    assert arc.error is None
    for spelling in (f"{name}⁻¹({argument})", f"{name}^-1({argument})", f"{name}^(-1)({argument})"):
        other = run(spelling)
        assert other.error is None, spelling
        assert other.text == arc.text, spelling


def test_inverse_functions_print_with_the_superscript():
    assert text("arcsin(x)") == "sin⁻¹(x)"
    assert text("arccos(x)") == "cos⁻¹(x)"
    assert text("arctan(x)") == "tan⁻¹(x)"
    assert text("arcsinh(1)") == "sinh⁻¹(1)"
    assert text("arccosh(x)") == "cosh⁻¹(x)"
    assert text("arctanh(x)") == "tanh⁻¹(x)"


def test_the_typed_caret_form_is_the_inverse_and_only_before_a_bracket():
    assert text("sin^-1(1/2)") == "π/6"
    assert text("SIN^(-1)(1/2)") == "π/6"
    assert text("sin(x)^-1") == "1/sin(x)"  # the reciprocal
    assert text("sin(x)^(-1)") == "1/sin(x)"
    assert text("2*tan^-1(1)") == "π/2"


def test_inverse_trig_in_degree_mode():
    assert text("sin^-1(1/2)", settings=DEGREE) == "30"
    assert text("cos⁻¹(1/2)", settings=DEGREE) == "60"
    assert text("tan⁻¹(1)", settings=GRADIAN) == "50"
    assert text("tanh^-1(0)", settings=DEGREE) == "0"


def test_ascii_spelling_of_the_canonical_text():
    assert to_ascii("sin⁻¹(x)+sinh⁻¹(y)") == "arcsin(x)+arcsinh(y)"


def test_user_names_cannot_take_an_inverse_spelling():
    assert error("arcsin:=3") == "Missing ("
    assert error("sin⁻¹:=3") == "Missing ("
    assert "reserved" in (error("arcsin(x):=3") or "")


# ---- number bases and angles -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        ("255@>Base16", "0hFF"),
        ("255@>Base2", "0b11111111"),
        ("0b1011@>Base10", "11"),
        ("0hFF@>Base10", "255"),
        ("-1@>Base16", "0hFFFFFFFFFFFFFFFF"),
        ("0@>Base2", "0b0"),
    ],
)
def test_number_bases(line, shown):
    assert text(line) == shown


def test_a_based_number_still_calculates():
    assert text("a:=255@>Base16", "a+1") == "256"
    assert error("2.5@>Base16") == "Domain error"
    assert error("x@>Base16") == "Domain error"


@pytest.mark.parametrize(
    ("line", "settings", "shown"),
    [
        ("(pi/6)@>DD", None, "30°"),
        ("30@>DD", DEGREE, "30°"),
        ("90@>Rad", DEGREE, "(π/2)ʳ"),
        ("90@>Grad", None, "(18000/π)ᵍ"),
        ("90@>Grad", DEGREE, "100ᵍ"),
        ("30.5@>DMS", DEGREE, "30°30'"),
        ("30.25@>DMS", DEGREE, "30°15'"),
        ("30.504166666667@>DMS", DEGREE, "30°30'15\""),
    ],
)
def test_angle_conversions(line, settings, shown):
    assert text(line, settings=settings) == shown


def test_converted_angles_keep_their_value():
    same("(pi/6)@>DD", "30")
    assert text("a:=(pi/6)@>DD", "a*2") == "60"


def test_decimal_and_fraction_conversions():
    assert text("1/3@>Decimal") == "0.33333333"
    assert text("{1/2,1/4}@>Decimal") == "{0.5,0.25}"
    assert text("0.3333@>approxFraction(0.001)") == "1/3"
    assert text("0.125@>approxFraction(0.01)") == "1/8"
    assert text("{0.5,0.3333}@>approxFraction(0.001)") == "{1/2,1/3}"
    assert error("0.5@>approxFraction(0)") == "Domain error"


def test_unknown_conversions_say_so():
    assert "Not implemented yet" in (error("1@>Nonsense") or "")


# ---- complex and vector forms ----------------------------------------------------------------


def test_polar_and_rectangular_forms():
    assert text("(1+@i)@>Polar") == "ⅇ^(ⅈ*π/4)*√(2)"
    assert text("(1+@i)@>Polar", settings=DEGREE) == "(√(2)∠45)"
    same("5*exp(@i*pi/3)@>Rect", "5/2+5*√(3)/2*ⅈ")
    assert text("3@>Polar") == "3"  # a real number has no polar form


def test_polar_form_is_the_same_number():
    same("(1+@i)@>Polar", "1+@i")
    assert text("z:=(1+@i)@>Polar", "z*z") == "2*ⅈ"


def test_polar_domain_setting_writes_complex_results_in_polar_form():
    assert text("(1+@i)^2", settings=POLAR) == "ⅇ^(ⅈ*π/2)*2"
    assert text("sqrt(-4)", settings=POLAR) == "ⅇ^(ⅈ*π/2)*2"
    assert text("(1+@i)*(1-@i)", settings=POLAR) == "2"
    assert text("exp(@i*pi)", settings=POLAR) == "-1"
    polar = text("3+4*@i", settings=POLAR)
    assert polar.startswith("ⅇ^(ⅈ*")
    assert polar.endswith(")*5")


def test_cylindrical_and_spherical_vectors():
    assert text("[1,1,1]@>Cylind") == "[√(2) ∠π/4 1]"
    assert text("[1,1,1]@>Sphere") == "[√(3) ∠π/4 ∠cos⁻¹(√(3)/3)]"
    assert text("[1,1,1]@>Cylind", settings=DEGREE) == "[√(2) ∠45 1]"
    assert error("[1,1]@>Cylind") == "Dimension mismatch"


# ---- strings, lists and matrices -------------------------------------------------------------


def test_string_and_expr():
    assert text("string(1+2)") == '"3"'
    assert text("string({1,2})") == '"{1,2}"'
    assert text('expr("1+2")') == "3"
    assert text("a:=5", 'expr("a*2")') == "10"
    assert error("expr(5)") == "Data type"
    assert error('expr("a:=5")') == "Syntax error"
    assert error('expr("1+")') == "Syntax error"


def test_list_and_matrix_conversions():
    assert text("list@>mat({1,2,3})") == "[1,2,3]"
    assert text("list@>mat({1,2,3,4},2)") == "[1,2;3,4]"
    assert text("mat@>list([1,2;3,4])") == "{1,2,3,4}"
    assert text("mat@>list([1,2,3;4,5,6])") == "{1,2,3,4,5,6}"
    assert error("list@>mat({1,2,3},2)") == "Dimension mismatch"
    assert error("mat@>list({1,2})") == "Data type"


def test_propfrac_of_a_number_shows_a_whole_part_and_a_fraction():
    assert text("propFrac(7/3)") == "2+1/3"
    assert text("propFrac(-7/3)") == "-2-1/3"
    assert text("propFrac(1/3)") == "1/3"
    assert text("propFrac(6/3)") == "2"
    same("propFrac(7/3)", "7/3")


# ---- algebra and linear algebra --------------------------------------------------------------


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("cFactor(x^2+1,x)", "(x-ⅈ)*(x+ⅈ)"),
        ("cFactor(x^4-1,x)", "(x-1)*(x+1)*(x-ⅈ)*(x+ⅈ)"),
        ("tExpand(sin(2*x))", "2*sin(x)*cos(x)"),
        ("tCollect(sin(x)*cos(x))", "sin(2*x)/2"),
    ],
)
def test_algebra_long_tail(line, wanted):
    same(line, wanted)


def test_eigenvalues_and_eigenvectors():
    same("eigVl([2,1;1,2])", "{3.,1.}", tolerance=1e-9)
    same("eigVc([2,1;1,2])", "[0.70710678,-0.70710678;0.70710678,0.70710678]", tolerance=1e-7)
    same("eigVl([4,0;0,9])", "{9.,4.}", tolerance=1e-9)
    assert error("eigVl([1,2,3])") == "Dimension mismatch"


# ---- random numbers --------------------------------------------------------------------------


def test_random_integers_stay_in_range_and_can_be_repeated():
    assert text("{min(randInt(1,6,50)),max(randInt(1,6,50))}") == "{1,6}"
    first = text("RandSeed 7", "randInt(1,100,5)")
    assert text("RandSeed 7", "randInt(1,100,5)") == first
    assert 1 <= float(text("randInt(3,5)")) <= 5
    assert 0 < float(text("rand()")) < 1
    assert text("dim(rand(4))") == "4"
    assert text("dim(randNorm(0,1,6))") == "6"
    assert 0 <= float(text("randBin(10,0.5)")) <= 10


@pytest.mark.parametrize(
    ("seed", "line", "shown"),
    [
        # Emulator check 5 (docs/testing/emulator-catalog2-results.md, C3).
        (1147, "randInt(3,10,4)", "{4,8,6,4}"),
        (1147, "randBin(80,.5,3)", "{44,34,47}"),
        (1, "randBin(10,0.5,3)", "{6,6,3}"),
        (1, "randNorm(0,1,3)", "{0.62742879,-0.17147098,-0.55931652}"),
        (1147, "{randNorm(0,1),randNorm(3,4.5)}", "{0.49254098,-3.5435597}"),
    ],
)
def test_a_seed_gives_the_handhelds_random_numbers(seed, line, shown):
    """FR-CAT-002: `RandSeed n` repeats the handheld's own sequence (decision 0030)."""
    assert text(f"RandSeed {seed}", line) == shown


def test_seed_zero_starts_the_generator_from_its_reset_state():
    assert text("RandSeed 0", "rand()") == "0.9435974"


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        # Exact in, exact out; decimal in, decimal out (emulator check 5, C3, and the corpus).
        ("iPart({3/2,-2.3,7.003})", "{1,-2.,7.}"),
        ("iPart(-1.234)", "-1."),
        ("iPart(-7/3)", "-2"),
        ("int(2.5)", "2."),
        ("floor(2.7)", "2."),
        ("ceiling(2.3)", "3."),
        ("floor(7/2)", "3"),
    ],
)
def test_rounding_keeps_the_arguments_exact_or_decimal_form(line, shown):
    """FR-CAT-001: `iPart`, `int`, `floor` and `ceiling` follow their argument's form in Auto."""
    assert text(line) == shown


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("randInt(1.5,3)", "Domain error"),
        ("randInt(1,6,-1)", "Domain error"),
        ("randNorm(0,-1)", "Domain error"),
        ("randBin(5,2)", "Domain error"),
        ("RandSeed", "Too few arguments"),
        ("rand(1,2)", "Too many arguments"),
    ],
)
def test_random_errors(line, message):
    assert error(line) == message


# ---- display of numbers: scientific and engineering ------------------------------------------


@pytest.mark.parametrize(
    ("value", "exp_format", "shown"),
    [
        ("12345.6789", "scientific", "1.2345679ᴇ4"),
        ("0.000123", "scientific", "1.23ᴇ-4"),
        ("12345.6789", "engineering", "12.345679ᴇ3"),
        ("0.000123", "engineering", "123.ᴇ-6"),
        ("1234567.5", "engineering", "1.2345675ᴇ6"),
        ("5", "scientific", "5.ᴇ0"),
        ("12345.6789", "normal", "12345.679"),
    ],
)
def test_exponent_formats(value, exp_format, shown):
    assert decimal_text(Decimal(value), "float8", exp_format) == shown


def test_exponent_format_leaves_exact_results_alone():
    settings = Settings(angle=Angle.GRADIAN, exp_format="scientific")
    assert text("sqrt(2)", settings=settings) == "√(2)"
    assert text("1000000*pi", settings=settings) == "1000000*π"
    assert text("12345.6789", settings=settings) == "1.2345679ᴇ4"
    assert text("0", settings=settings) == "0"


# ---- sin(1) in Degree mode, solution families ------------------------------------------------


def test_trig_of_a_number_that_does_not_simplify_prints_as_typed():
    assert text("sin(1)", settings=DEGREE) == "sin(1)"
    assert text("sin(30)", settings=DEGREE) == "1/2"
    assert text("approx(sin(1))", settings=DEGREE) == "0.017452406"
    assert text("sin(1)", settings=Settings()) == "sin(1)"
    assert text("{sin(1),sin(30)}", settings=DEGREE) == "{sin(1),1/2}"


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        # Emulator check 5 (C3): `and`/`or` are bitwise on integers and work through lists.
        ("3 or 4", "7"),
        ("3 and 4", "0"),
        ("{1,2,3} or {3,2,1}", "{3,2,3}"),
        ("1<2 or 3<2", "true"),
        ("x>1 and x<3", "1<x<3"),
    ],
)
def test_and_or_work_on_integers_lists_and_conditions(line, shown):
    """FR-CAT-002: integer operands no longer crash the engine."""
    assert text(line) == shown


def test_and_or_on_a_decimal_is_a_data_type_error():
    """FR-CAT-006: a TI-style error, not a Python exception."""
    assert error("2.5 or 3") == "Data type"


def test_the_family_of_solutions_uses_an_integer_parameter():
    assert text("solve(sin(x)=1/2,x)") == "x=2*π*@n1+π/6 or x=2*π*@n1+5*π/6"
