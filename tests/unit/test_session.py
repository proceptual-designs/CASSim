# Requirements traced here: FR-EVAL-001, FR-EVAL-002, FR-EVAL-003, FR-EVAL-004
"""Engine behaviour under each document setting. Expected values are from the corpus."""

from decimal import Decimal

import pytest

from cassim.core.format import decimal_text
from cassim.core.session import Session, same_value
from cassim.core.settings import PRESETS, Angle, Calc, CasMode, Domain, Settings

GENERAL = PRESETS["general"]
AUTO = Settings()
EXACT = Settings(calc=Calc.EXACT)
APPROX = Settings(calc=Calc.APPROXIMATE)
DEGREE = Settings(angle=Angle.DEGREE)
GRADIAN = Settings(angle=Angle.GRADIAN)
CAS_OFF = Settings(cas_mode=CasMode.OFF)
EXACT_ARITHMETIC = Settings(cas_mode=CasMode.EXACT_ARITHMETIC)


def show(line, settings=AUTO):
    result = Session(settings).eval(line)
    assert result.error is None, result.error
    return result.text


def error(line, settings=AUTO):
    return Session(settings).eval(line).error


@pytest.mark.parametrize(
    ("line", "settings", "text"),
    [
        # Auto keeps exact values until a decimal appears
        ("47/10", AUTO, "47/10"),
        ("1./3", AUTO, "0.33333333"),
        ("1/3+1/4", AUTO, "7/12"),
        ("sqrt(8)", AUTO, "2*√(2)"),
        ("sqrt(2)+0.5", AUTO, "1.9142136"),
        ("2^0.5", AUTO, "1.4142136"),
        ("2.*x", AUTO, "2.*x"),
        ("1./3*x", AUTO, "0.33333333*x"),
        # Approximate decimalises everything, including coefficients
        ("47/10", APPROX, "4.7"),
        ("1/3", APPROX, "0.33333333"),
        ("pi", APPROX, "3.1415927"),
        ("exp(1)", APPROX, "2.7182818"),
        ("2", APPROX, "2."),
        ("3*x^2", APPROX, "3.*x^2"),
        # Exact keeps decimals as fractions
        ("0.75", EXACT, "3/4"),
        ("1.5ᴇ3", EXACT, "1500"),
        # CAS Off keeps fractions but no other exact form
        ("47/10", CAS_OFF, "47/10"),
        ("1/3+1/4", CAS_OFF, "7/12"),
        ("sqrt(8)", CAS_OFF, "2.8284271"),
        ("sin(pi/5)", CAS_OFF, "0.58778525"),
        # Exact Arithmetic keeps exact numbers
        ("sqrt(8)", EXACT_ARITHMETIC, "2*√(2)"),
        ("1/3+1/4", EXACT_ARITHMETIC, "7/12"),
        # approx and ▶Decimal work in any mode
        ("approx(47/10)", AUTO, "4.7"),
        ("approx(sqrt(8))", EXACT, "2.8284271"),
        ("1/3@>Decimal", AUTO, "0.33333333"),
        ("approx({1/2,1/4})", AUTO, "{0.5,0.25}"),
    ],
)
def test_exact_and_approximate_rules(line, settings, text):
    assert show(line, settings) == text


@pytest.mark.parametrize(
    ("line", "settings", "text"),
    [
        ("sin(pi/6)", AUTO, "1/2"),
        ("sin(30)", AUTO, None),
        ("sin(30)", DEGREE, "1/2"),
        ("sin(45)", DEGREE, "√(2)/2"),
        ("sin(30)", GENERAL, "0.5"),
        ("tan(45)", GENERAL, "1."),
        ("cos(100)", GRADIAN, "0"),
        ("sin(x)", DEGREE, "sin(x)"),
        # Post operators convert to the document's angle mode
        ("30°", AUTO, "π/6"),
        ("30°", DEGREE, "30"),
        ("100°", GRADIAN, "1000/9"),
        ("(π/6)ʳ", DEGREE, "30"),
        ("(π/6)ʳ", AUTO, "π/6"),
        ("100ᵍ", DEGREE, "90"),
        ("100ᵍ", AUTO, "π/2"),
        ("sin(30°)", AUTO, "1/2"),
        ("sin(30@d)", DEGREE, "1/2"),
        ("30@d30'", DEGREE, "61/2"),
        ("60@d15'45\"", DEGREE, "4821/80"),
    ],
)
def test_angle_modes(line, settings, text):
    if text is not None:
        assert show(line, settings) == text
    else:
        assert show(line, settings) == "sin(30)"


@pytest.mark.parametrize(
    ("line", "text"),
    [
        ("x^3+3*x^2+1", "x^3+3*x^2+1"),
        ("x/2", "x/2"),
        ("-x/2", "-x/2"),
        ("1/x", "1/x"),
        ("-1/2", "-1/2"),
        ("√(2)/2", "√(2)/2"),
        ("2*π", "2*π"),
        ("ⅇ^x", "ⅇ^x"),
        ("exp(x)", "ⅇ^x"),
        ("3+4*@i", "3+4*ⅈ"),
        ("(1+@i)^2", "2*ⅈ"),
        ("-@i", "-ⅈ"),
        ("zz+1", "zz+1"),
        ("ZZ+1", "zz+1"),
        ("e", "e"),
        ("2e-1", "2*e-1"),
        ("x^(1/3)", "x^(1/3)"),
        ("ln(x)", "ln(x)"),
        ("Foo(x,1)", "foo(x,1)"),
        ("{1,2}+1", "{2,3}"),
        ("{1,2}*{3,4}", "{3,8}"),
        ("2*{1,x}", "{2,2*x}"),
        ("{1,2}.^2", "{1,4}"),
        ("{1,{2,3}}+1", "{2,{3,4}}"),
        ("[1,2;3,4]+1", "[2,3;4,5]"),
        ("[1,2;3,4]+[1,1;1,1]", "[2,3;4,5]"),
        ("[1,2;3,4]*[0,1;1,0]", "[2,1;4,3]"),
        ("-[1,2]", "[-1,-2]"),
        ("[1,2;3,4]@t", "[1,3;2,4]"),
        ("{5,6,7}[2]", "6"),
        ("5!", "120"),
        ("{2,3}!", "{2,6}"),
        ("50%", "1/2"),
        ('"a"&"b"', '"ab"'),
        ("0hFF", "255"),
        ("0b101", "5"),
        ("2=2", "true"),
        ("2=3", "false"),
        ("2<3 and 3<2", "false"),
        ("not 2=3", "true"),
        ("x=2", "x=2"),
        ("x<2", "x<2"),
        ("x=1 or x=2", "x=1 or x=2"),
        ("x≠2", "x≠2"),
        ("1/0", "undef"),
        ("ln(0)", "undef"),
        ("1/0+x", "undef"),
        ("undef", "undef"),
        ("∞", "∞"),
        ("-infinity", "-∞"),
    ],
)
def test_result_text(line, text):
    assert show(line) == text


@pytest.mark.parametrize(
    ("value", "digits", "text"),
    [
        ("1.4142135623", "float3", "1.41"),
        ("314.15926", "float3", "314."),
        ("3141592.6", "float3", "3.14ᴇ6"),
        ("0.000123456", "float3", "1.23ᴇ-4"),
        ("12345.6789", "float3", "1.23ᴇ4"),
        ("999.6", "float3", "1.ᴇ3"),
        ("1E-13", "float8", "1.ᴇ-13"),
        # Below 1, Float n keeps n decimal places down to 10^-n (emulator checks 5 and 6).
        ("0.026666667", "float8", "0.02666667"),
        ("0.0010101010", "float8", "0.0010101"),
        ("0.0000012", "float8", "0.0000012"),
        ("0.0000000012345", "float8", "1.2345ᴇ-9"),
        ("0.0009", "float3", "9.ᴇ-4"),
        ("0.00099", "float3", "9.9ᴇ-4"),
        ("0.001", "float3", "0.001"),
        ("0.9999999999", "float8", "1."),
        ("0.33333333333", "float8", "0.33333333"),
        ("59.9999984", "float8", "59.999998"),
        ("2", "float8", "2."),
        ("0.5", "float8", "0.5"),
        ("0", "float8", "0."),
        ("0.33333", "fix2", "0.33"),
        ("314.15926", "fix2", "314.16"),
        ("666.66667", "fix2", "666.67"),
        ("0.005", "fix2", "5.00ᴇ-3"),
        ("12345.6789", "fix2", "12345.68"),
        ("2", "fix2", "2.00"),
        ("0", "fix2", "0.00"),
        ("2.5", "fix0", "3."),
    ],
)
def test_number_display(value, digits, text):
    assert decimal_text(Decimal(value), digits) == text


def test_digits_setting_reaches_results():
    assert show("-1000000*pi", Settings(digits="float3", calc=Calc.APPROXIMATE)) == "-3.14ᴇ6"
    assert show("1/3", Settings(digits="fix2", calc=Calc.APPROXIMATE)) == "0.33"


@pytest.mark.parametrize(
    ("digits", "line", "latex"),
    [
        ("float3", "1/3.", "0.333"),
        ("fix2", "1/3.", "0.33"),
        ("float3", "x+1.23456", "x + 1.23"),
        ("float3", "-1000000.*pi", r"-3.14 \cdot 10^{6}"),
        ("fix2", "0.005", r"5.00 \cdot 10^{-3}"),
    ],
)
def test_digits_setting_reaches_latex_results(digits, line, latex):
    result = Session(Settings(digits=digits)).eval(line)
    assert result.error is None
    assert latex in result.latex
    assert "1.23456" not in result.latex


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("2+*3", "Syntax"),
        ("sin(1,2)", "Too many arguments"),
        ("sin()", "Too few arguments"),
        ("{1,2}+{1}", "Dimension mismatch"),
        ("[1,2]+[1;2]", "Dimension mismatch"),
        ("[1,2]*[3,4]", "Dimension mismatch"),
        ("[1,2;3]", "Invalid list or matrix"),
        ('"a"+1', "Data type"),
        ("5@t", "Data type"),
        ("{1,2}[3]", "Dimension error"),
        ("{1,2}[1.5]", "Domain error"),
    ],
)
def test_errors(line, message):
    assert message in error(line)


@pytest.mark.parametrize("settings", [CAS_OFF, EXACT_ARITHMETIC])
@pytest.mark.parametrize("line", ["x", "x+1", "foo(x)", "{1,x}"])
def test_symbols_are_restricted_without_cas(line, settings):
    assert "restricted" in error(line, settings)


@pytest.mark.parametrize(
    "line",
    [
        "x@>Nonsense",
        "1/[1,2;3,4]",
        "2^[1,2]",
    ],
)
def test_later_milestones_say_so_rather_than_guess(line):
    assert "Not implemented yet" in error(line)


def test_ans_holds_the_last_result():
    session = Session()
    session.eval("2+3")
    assert session.eval("ans*2").text == "10"
    assert session.eval("Ans+1").text == "11"


def test_ans_is_unchanged_by_an_error():
    session = Session()
    session.eval("7")
    session.eval("1+")
    assert session.eval("ans").text == "7"


def test_new_problem_clears_ans():
    session = Session()
    session.eval("7")
    session.new_problem()
    assert session.eval("ans").text == "ans"


def test_settings_change_mid_session():
    session = Session()
    session.set(calc="approximate", digits="float3", domain="polar", angle="degree")
    assert session.settings == Settings(Angle.DEGREE, Calc.APPROXIMATE, Domain.POLAR, "float3")
    assert session.eval("1/3").text == "0.333"


def test_empty_line_has_no_result():
    result = Session().eval("")
    assert result.value is None
    assert result.error is None


def test_results_carry_latex():
    assert Session().eval("x^2").latex == "x^{2}"
    assert Session().eval("{1,2}").latex == r"\{1,2\}"
    assert Session().eval("[1,2;3,4]").latex == r"\begin{bmatrix}1&2\\3&4\end{bmatrix}"
    assert Session().eval('"a"').latex == r"\text{a}"
    assert Session().eval("2=2").latex == r"\text{true}"


def value(line):
    return Session().eval(line).value


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("sin(π/5)", "√(5/8-√(5)/8)"),
        ("(x+1)^2", "x^2+2*x+1"),
        ("x=2 or x=3", "x=3 or x=2"),
        ("{1,x+x}", "{1,2*x}"),
        ("[1,2]", "[1,2]"),
        ("1/0", "undef"),
    ],
)
def test_same_value(left, right):
    assert same_value(value(left), value(right))


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("x", "x+1"),
        ("x=2", "x=3"),
        ("x=2", "x<2"),
        ("{1,2}", "{1}"),
        ("[1,2]", "{1,2}"),
        ("x=2", "2"),
    ],
)
def test_different_values(left, right):
    assert not same_value(value(left), value(right))


def test_same_value_within_a_tolerance():
    assert same_value(value("1.41421356"), value("sqrt(2)"), 1.0e-7)
    assert not same_value(value("1.4142"), value("sqrt(2)"), 1.0e-7)
    assert same_value(value("3.0000000001*x^2"), value("3*x^2"), 1.0e-7)


def test_such_that_reaches_into_ans_and_stored_values():
    session = Session()
    session.eval("x^2")
    assert session.eval("Ans|x=1").text == "1"
    session.eval("b:=x^2+y")
    assert session.eval("b|x=2").text == "y+4"
    assert session.eval("b").text == "x^2+y"


def test_such_that_does_not_leak_into_user_function_locals():
    session = Session()
    session.eval("b:=x^2")
    session.eval("f(x):=x*b")
    assert session.eval("f(2)").text == "2*x^2"
