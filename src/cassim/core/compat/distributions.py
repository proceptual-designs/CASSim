"""Continuous distributions on plain floats, computed with mpmath (which SymPy already needs).

Everything here takes and returns Python floats and raises ValueError for an argument outside
the distribution's domain. Infinite bounds are allowed where a cumulative probability is asked.
"""

import math
from collections.abc import Callable

import mpmath as mp

# Digits kept while working; the answer is shown to at most 15.
_DIGITS = 30
_BISECTIONS = 200
_BRACKET_DOUBLINGS = 200
_MEDIAN = 0.5


def _check_probability(area: float) -> None:
    if not 0 < area < 1:
        raise ValueError(area)


def _check_positive(value: float) -> None:
    if not value > 0:
        raise ValueError(value)


def norm_pdf(x: float, mean: float, deviation: float) -> float:
    _check_positive(deviation)
    with mp.workdps(_DIGITS):
        return float(mp.npdf(x, mean, deviation))


def norm_cdf(lower: float, upper: float, mean: float, deviation: float) -> float:
    _check_positive(deviation)
    with mp.workdps(_DIGITS):
        return float(mp.ncdf(upper, mean, deviation) - mp.ncdf(lower, mean, deviation))


def inv_norm(area: float, mean: float, deviation: float) -> float:
    _check_probability(area)
    _check_positive(deviation)
    with mp.workdps(_DIGITS):
        return float(mean + deviation * mp.sqrt(2) * mp.erfinv(2 * mp.mpf(area) - 1))


def _t_below(t: float, df: float) -> mp.mpf:
    """P(T <= t) for Student's t."""
    if math.isinf(t):
        return mp.mpf(1 if t > 0 else 0)
    x = mp.mpf(df) / (df + mp.mpf(t) ** 2)
    tail = mp.betainc(mp.mpf(df) / 2, mp.mpf(1) / 2, 0, x, regularized=True) / 2
    return 1 - tail if t > 0 else tail


def t_pdf(x: float, df: float) -> float:
    _check_positive(df)
    with mp.workdps(_DIGITS):
        half = mp.mpf(df) / 2
        scale = mp.gamma(half + mp.mpf(1) / 2) / (mp.sqrt(df * mp.pi) * mp.gamma(half))
        return float(scale * (1 + mp.mpf(x) ** 2 / df) ** (-(half + mp.mpf(1) / 2)))


def t_cdf(lower: float, upper: float, df: float) -> float:
    _check_positive(df)
    with mp.workdps(_DIGITS):
        return float(_t_below(upper, df) - _t_below(lower, df))


def _chi2_below(x: float, df: float) -> mp.mpf:
    if x <= 0:
        return mp.mpf(0)
    if math.isinf(x):
        return mp.mpf(1)
    return mp.gammainc(mp.mpf(df) / 2, 0, mp.mpf(x) / 2, regularized=True)


def chi2_pdf(x: float, df: float) -> float:
    _check_positive(df)
    if x < 0:
        return 0.0
    with mp.workdps(_DIGITS):
        half = mp.mpf(df) / 2
        return float(mp.mpf(x) ** (half - 1) * mp.exp(-mp.mpf(x) / 2) / (2**half * mp.gamma(half)))


def chi2_cdf(lower: float, upper: float, df: float) -> float:
    _check_positive(df)
    with mp.workdps(_DIGITS):
        return float(_chi2_below(upper, df) - _chi2_below(lower, df))


def _f_below(x: float, numerator: float, denominator: float) -> mp.mpf:
    if x <= 0:
        return mp.mpf(0)
    if math.isinf(x):
        return mp.mpf(1)
    top = numerator * mp.mpf(x)
    return mp.betainc(
        mp.mpf(numerator) / 2,
        mp.mpf(denominator) / 2,
        0,
        top / (top + denominator),
        regularized=True,
    )


def f_pdf(x: float, numerator: float, denominator: float) -> float:
    _check_positive(numerator)
    _check_positive(denominator)
    if x < 0:
        return 0.0
    with mp.workdps(_DIGITS):
        a, b = mp.mpf(numerator), mp.mpf(denominator)
        x_ = mp.mpf(x)
        density = (a * x_) ** a * b**b / (a * x_ + b) ** (a + b)
        return float(mp.sqrt(density) / (x_ * mp.beta(a / 2, b / 2)))


def f_cdf(lower: float, upper: float, numerator: float, denominator: float) -> float:
    _check_positive(numerator)
    _check_positive(denominator)
    with mp.workdps(_DIGITS):
        return float(
            _f_below(upper, numerator, denominator) - _f_below(lower, numerator, denominator)
        )


def _invert(below: Callable[[float], mp.mpf], area: float, *, two_sided: bool) -> float:
    """Find x with P(X <= x) = area for a rising distribution function, by bisection."""
    _check_probability(area)
    target = mp.mpf(area)
    low, high = (-1.0, 1.0) if two_sided else (0.0, 1.0)
    for _ in range(_BRACKET_DOUBLINGS):
        if below(low) <= target <= below(high):
            break
        low, high = (low * 2 if two_sided else 0.0), high * 2
    for _ in range(_BISECTIONS):
        middle = (low + high) / 2
        if below(middle) < target:
            low = middle
        else:
            high = middle
    return float((low + high) / 2)


def inv_t(area: float, df: float) -> float:
    _check_positive(df)
    _check_probability(area)
    if area == _MEDIAN:
        return 0.0
    with mp.workdps(_DIGITS):
        return _invert(lambda x: _t_below(x, df), area, two_sided=True)


def inv_chi2(area: float, df: float) -> float:
    _check_positive(df)
    with mp.workdps(_DIGITS):
        return _invert(lambda x: _chi2_below(x, df), area, two_sided=False)


def inv_f(area: float, numerator: float, denominator: float) -> float:
    _check_positive(numerator)
    _check_positive(denominator)
    with mp.workdps(_DIGITS):
        return _invert(lambda x: _f_below(x, numerator, denominator), area, two_sided=False)
