# Requirements traced here: FR-FX-MOD-001, FR-FX-FNC-001, FR-FX-STA-001, FR-FX-STA-002
"""Unit tests for CASSim fx calculation engine and mathematical routines."""

import math

from cassim.devices.scientific.engine import (
    calculate_1var_stats,
    calculate_linear_regression,
    factorial,
    format_dms,
    format_prime_factors,
    from_degrees,
    from_dms,
    gcd,
    lcm,
    nCr,
    nPr,
    prime_factors,
    safe_eval,
    to_degrees,
    to_dms,
    to_exact_or_decimal,
    to_mixed_fraction,
    to_polar,
    to_rectangular,
)


def test_angle_conversions() -> None:
    # DEG to RAD and back
    assert math.isclose(to_degrees(math.pi, "RAD"), 180.0)
    assert math.isclose(from_degrees(180.0, "RAD"), math.pi)

    # DEG to GRA and back
    assert math.isclose(to_degrees(100.0, "GRA"), 90.0)
    assert math.isclose(from_degrees(90.0, "GRA"), 100.0)

    # DEG identity
    assert to_degrees(45.0, "DEG") == 45.0
    assert from_degrees(45.0, "DEG") == 45.0


def test_dms_conversions() -> None:
    deg = 12.58222222
    d, m, s = to_dms(deg)
    assert d == 12
    assert m == 34
    assert round(s) == 56

    reconstructed = from_dms(12, 34, 56)
    assert math.isclose(reconstructed, deg, rel_tol=1e-5)

    formatted = format_dms(deg)
    assert formatted == "12°34'56\""


def test_coordinate_conversions() -> None:
    # Rectangular to Polar: (3, 4) in DEG -> r=5, θ≈53.13°
    r, theta = to_polar(3.0, 4.0, "DEG")
    assert math.isclose(r, 5.0)
    assert math.isclose(theta, 53.13010235, rel_tol=1e-5)

    # Polar to Rectangular: (5, 53.13010235°) -> x=3, y=4
    x, y = to_rectangular(5.0, 53.13010235, "DEG")
    assert math.isclose(x, 3.0, abs_tol=1e-4)
    assert math.isclose(y, 4.0, abs_tol=1e-4)


def test_prime_factors() -> None:
    assert prime_factors(360) == [(2, 3), (3, 2), (5, 1)]
    assert format_prime_factors(360) == "2³×3²×5"

    assert prime_factors(17) == [(17, 1)]
    assert format_prime_factors(17) == "17"

    assert prime_factors(1) == []
    assert format_prime_factors(1) == "1"


def test_discrete_math() -> None:
    assert gcd(84, 30) == 6
    assert lcm(84, 30) == 420

    assert nPr(5, 2) == 20
    assert nCr(5, 2) == 10
    assert factorial(5) == 120
    assert factorial(0) == 1


def test_australian_1var_stats_school_median_split() -> None:
    """TI/Australian school median-split quartile convention (median excluded when n is odd)."""
    # Even dataset: {1, 4, 9, 16, 25, 36, 49, 64} (n=8)
    # Lower half: {1, 4, 9, 16} -> Q1 = (4+9)/2 = 6.5
    # Upper half: {25, 36, 49, 64} -> Q3 = (36+49)/2 = 42.5
    # Median = (16+25)/2 = 20.5
    even_data = [(float(x), 1) for x in [1, 4, 9, 16, 25, 36, 49, 64]]
    stats_even = calculate_1var_stats(even_data)
    assert stats_even.n == 8
    assert math.isclose(stats_even.q1, 6.5)
    assert math.isclose(stats_even.med, 20.5)
    assert math.isclose(stats_even.q3, 42.5)

    # Odd dataset: {2, 5, 8, 12, 18} (n=5)
    # Median = 8. Lower half {2, 5} -> Q1 = 3.5. Upper half {12, 18} -> Q3 = 15.0
    odd_data = [(2.0, 1), (5.0, 1), (8.0, 1), (12.0, 1), (18.0, 1)]
    stats_odd = calculate_1var_stats(odd_data)
    assert stats_odd.n == 5
    assert math.isclose(stats_odd.q1, 3.5)
    assert math.isclose(stats_odd.med, 8.0)
    assert math.isclose(stats_odd.q3, 15.0)

    # Sample standard deviation sx (n-1) vs population sd σx (n)
    assert stats_odd.sx > stats_odd.sigma_x


def test_linear_regression() -> None:
    # Perfect linear: y = 2x + 1
    pairs = [(1.0, 3.0), (2.0, 5.0), (3.0, 7.0), (4.0, 9.0)]
    reg = calculate_linear_regression(pairs)
    assert reg.n == 4
    assert math.isclose(reg.a, 1.0)
    assert math.isclose(reg.b, 2.0)
    assert math.isclose(reg.r, 1.0)
    assert math.isclose(reg.estimate_y(5.0), 11.0)
    assert math.isclose(reg.estimate_x(11.0), 5.0)


def test_safe_eval() -> None:
    res = safe_eval("2 + 3 * 4", "DEG")
    assert res == 14.0

    res_trig = safe_eval("sin(30)", "DEG")
    assert math.isclose(float(res_trig), 0.5)

    res_rad = safe_eval("sin(pi/6)", "RAD")
    assert math.isclose(float(res_rad), 0.5)

    res_frac = safe_eval("1/2 + 1/3", "DEG")
    assert math.isclose(float(res_frac), 5 / 6)


def test_fractions_and_mixed() -> None:
    exact, dec = to_exact_or_decimal(0.75)
    assert exact == "3/4"
    assert dec == "0.75"

    mixed = to_mixed_fraction("7/3")
    assert mixed == "2 1/3"

    mixed_neg = to_mixed_fraction("-7/3")
    assert mixed_neg == "-2 1/3"
