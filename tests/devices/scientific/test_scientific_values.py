"""Exact values: fractions, surds and π stay exact; nothing pretends to be exact when it is not.

Requirements: FR-FX-DSP-005, FR-FX-FNC-001, FR-FX-FNC-003.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cassim.devices.scientific import values as v
from cassim.devices.scientific.values import CalcError, Exact


def surd(coeff: Fraction | int, radicand: int, pi: int = 0) -> Exact:
    return Exact(((radicand, pi, Fraction(coeff)),))


def test_square_roots_simplify() -> None:
    assert v.sqrt(v.rational(8)) == surd(2, 2)
    assert v.sqrt(v.rational(Fraction(1, 2))) == surd(Fraction(1, 2), 2)
    assert v.sqrt(v.rational(49)) == v.rational(7)


def test_surds_multiply_and_rationalise() -> None:
    root2 = v.sqrt(v.rational(2))
    assert v.mul(root2, root2) == v.rational(2)
    one_plus = v.add(v.rational(1), root2)
    assert v.inverse(one_plus) == v.sub(root2, v.rational(1))  # 1/(1+√2) = √2 − 1


def test_pi_stays_exact_until_it_cannot() -> None:
    assert v.mul(v.rational(2), v.PI) == surd(2, 1, 1)
    assert isinstance(v.mul(v.PI, v.PI), float)  # π² is not a shape the display has
    assert isinstance(v.add(v.PI, v.rational(1)), float)


def test_the_review_bug_pi_is_not_355_over_113() -> None:
    """FR-FX-DSP-005: S⇔D on a decimal only offers a fraction that really equals it."""
    assert v.recognise_fraction(math.pi) is None
    assert v.recognise_fraction(math.sqrt(2)) is None
    assert v.recognise_fraction(0.75) == Fraction(3, 4)
    assert v.recognise_fraction(0.1 + 0.2) == Fraction(3, 10)


def test_powers_and_roots() -> None:
    assert v.power(v.rational(8), v.rational(Fraction(1, 3))) == v.rational(2)
    assert v.root(3, v.rational(-8)) == v.rational(-2)
    assert v.power(v.rational(2), v.rational(-2)) == v.rational(Fraction(1, 4))
    assert v.power(v.rational(4), v.rational(Fraction(1, 2))) == v.rational(2)
    assert v.power(v.rational(-8), v.rational(Fraction(2, 3))) == v.rational(4)


@pytest.mark.parametrize(
    "bad",
    [
        lambda: v.sqrt(v.rational(-1)),
        lambda: v.div(v.rational(1), v.ZERO),
        lambda: v.power(v.rational(10), v.rational(100)),
        lambda: v.power(v.ZERO, v.ZERO),
        lambda: v.power(v.rational(-2), 0.5),
        lambda: v.root(2, v.rational(-4)),
    ],
)
def test_math_errors(bad) -> None:
    with pytest.raises(CalcError) as raised:
        bad()
    assert raised.value.message == "Math ERROR"


def test_exact_trig_table() -> None:
    """FR-FX-FNC-001: the angles a school course uses come out exact."""
    assert v.exact_trig("sin", Fraction(30)) == v.rational(Fraction(1, 2))
    assert v.exact_trig("cos", Fraction(30)) == surd(Fraction(1, 2), 3)
    assert v.exact_trig("tan", Fraction(60)) == surd(1, 3)
    assert v.exact_trig("sin", Fraction(225)) == surd(Fraction(-1, 2), 2)
    assert v.exact_trig("sin", Fraction(20)) is None
    with pytest.raises(CalcError):
        v.exact_trig("tan", Fraction(90))
    assert v.exact_inverse_trig("asin", v.rational(Fraction(1, 2))) == 30
    assert v.exact_inverse_trig("acos", v.rational(Fraction(1, 2))) == 60
    assert v.exact_inverse_trig("atan", surd(1, 3)) == 60


def test_zero_is_a_float_zero() -> None:
    assert float(v.ZERO) == 0.0
    assert isinstance(float(v.ZERO), float)


@given(st.fractions(max_denominator=50), st.fractions(max_denominator=50))
def test_exact_arithmetic_agrees_with_floats(a: Fraction, b: Fraction) -> None:
    x, y = v.rational(a), v.rational(b)
    assert math.isclose(float(v.add(x, y)), float(a + b), abs_tol=1e-9)
    assert math.isclose(float(v.mul(x, y)), float(a * b), abs_tol=1e-9)
    if b:
        assert v.div(x, y) == v.rational(a / b)


@given(st.integers(min_value=1, max_value=10_000))
def test_square_part(n: int) -> None:
    outside, inside = v.square_part(n)
    assert outside * outside * inside == n
    assert all(inside % (p * p) for p in range(2, 101))
