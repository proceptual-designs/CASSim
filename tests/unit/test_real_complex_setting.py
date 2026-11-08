"""The "Real or Complex" setting as captured on the simulator.

See docs/testing/emulator-domain-results.md.
Build 6.0.3.374, Radian, Auto, Float 8. `@i` is typed ⅈ. The error is "Non-real result".
"""

import pytest

from cassim.core.session import Session

ERROR = "Non-real result"


def run(line: str, domain: str, *, approximate: bool = False) -> str:
    session = Session()
    session.set(domain=domain)
    return session.eval(line, approximate=approximate).text


@pytest.mark.parametrize(
    "line",
    [
        "sqrt(-1)",
        "sqrt(-8)",
        "(-4)^(1/2)",
        "(-1)^(1/2)",
        "ln(-1)",
        "ln(-2)",
        "log(-1)",
        "log(-100,10)",
        "arcsin(2)",
        "arccos(2)",
        "arccosh(0)",
        "arctanh(2)",
        "arcsin(-2)",
        "{1,sqrt(-1)}",
        "root(-4,2)",
    ],
)
def test_real_functions_outside_their_real_domain_are_errors_in_real_mode(line: str) -> None:
    assert run(line, "real") == ERROR


@pytest.mark.parametrize(
    ("line", "real"),
    [
        ("(-8)^(1/3)", "-2"),
        ("root(-8,3)", "-2"),
        ("(-8)^(2/3)", "4"),
        ("sqrt(-1)*sqrt(-1)", "-1"),  # the device warns (triangle) but gives a value
        ("(sqrt(-1))^2", "-1"),
        ("real(3+4*sqrt(-1))", "3"),
        ("imag(3+4*sqrt(-1))", "4"),
        ("sqrt(x)", "√(x)"),
        ("sqrt(-x)", "√(-x)"),
        ("ln(0)", "undef"),
    ],
)
def test_real_mode_values_that_are_not_errors(line: str, real: str) -> None:
    assert run(line, "real") == real


@pytest.mark.parametrize(
    "line",
    [
        "@i",
        "3+4*@i",
        "@i^2",
        "1/@i",
        "(1+@i)^2",
        "ln(@i)",
        "sqrt(@i)",
        "conj(3+4*@i)",
        "abs(3+4*@i)",
    ],
)
def test_a_typed_i_is_never_an_error_in_real_mode(line: str) -> None:
    assert run(line, "real") != ERROR
    assert run(line, "real") == run(line, "rectangular")


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("sqrt(-1)", "ⅈ"),
        ("sqrt(-4)", "2*ⅈ"),
        ("sqrt(-8)", "2*√(2)*ⅈ"),
        ("(-4)^(1/2)", "2*ⅈ"),
        ("(-8)^(1/3)", "1+√(3)*ⅈ"),
        ("(-8)^(2/3)", "-2+2*√(3)*ⅈ"),
        ("root(-8,3)", "-2"),  # the nth-root template is real in every setting
        ("ln(-1)", "ⅈ*π"),
        ("arccos(2)", "ⅈ*ln(√(3)+2)"),
        ("arcsin(2)", "π/2-ⅈ*ln(√(3)+2)"),
        ("arctanh(2)", "ln(3)/2-ⅈ*π/2"),
        ("arccosh(0)", "ⅈ*π/2"),
        ("sqrt(@i)", "√(2)/2+√(2)*ⅈ/2"),
        ("sqrt(-1)*sqrt(-1)", "-1"),
        ("{1,sqrt(-1)}", "{1,ⅈ}"),
    ],
)
def test_rectangular_gives_the_principal_complex_value(line: str, wanted: str) -> None:
    assert run(line, "rectangular") == wanted


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("sqrt(-1)", "ⅇ^(ⅈ*π/2)"),  # a modulus of 1 is left out
        ("sqrt(-4)", "ⅇ^(ⅈ*π/2)*2"),  # the modulus comes after the exponential
        ("(-8)^(1/3)", "ⅇ^(ⅈ*π/3)*2"),
        ("(-8)^(2/3)", "ⅇ^(ⅈ*2*π/3)*4"),
        ("ln(-1)", "ⅇ^(ⅈ*π/2)*π"),
        ("@i", "ⅇ^(ⅈ*π/2)"),
        ("1/@i", "ⅇ^(-ⅈ*π/2)"),
        ("1+@i", "ⅇ^(ⅈ*π/4)*√(2)"),
        ("-1-@i", "ⅇ^(-ⅈ*3*π/4)*√(2)"),
        ("conj(3+4*@i)", "ⅇ^(-ⅈ*tan⁻¹(4/3))*5"),
        ("cZeros(x^2+1,x)", "{ⅇ^(ⅈ*π/2),ⅇ^(-ⅈ*π/2)}"),
        ("{1,sqrt(-1)}", "{1,ⅇ^(ⅈ*π/2)}"),
        ("-3", "-3"),  # real numbers are left alone
        ("abs(3+4*@i)", "5"),
    ],
)
def test_polar_writes_complex_results_as_an_exponential(line: str, wanted: str) -> None:
    assert run(line, "polar") == wanted


def test_approximate_mode_does_not_change_which_inputs_are_errors() -> None:
    assert run("sqrt(-4)", "real", approximate=True) == ERROR
    assert run("(-8)^(1/3)", "real", approximate=True) == "-2."
    assert run("sqrt(-4)", "rectangular", approximate=True) == "2.*ⅈ"


@pytest.mark.parametrize("domain", ["real", "rectangular", "polar"])
def test_solve_is_real_only_and_the_c_commands_are_complex_in_every_setting(domain: str) -> None:
    assert run("solve(x^2+1=0,x)", domain) == "false"
    assert run("solve(x^2=-4,x)", domain) == "false"
    assert run("factor(x^2+1)", domain) == "x^2+1"
    assert run("zeros(x^2+1,x)", domain) == "{}"
    assert run("cSolve(x^2+1=0,x)", domain).startswith("x=")
