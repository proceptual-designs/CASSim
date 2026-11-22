"""Confidence intervals and significance tests using mpmath-backed distributions."""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from cassim.core.compat import distributions

_ALTERNATIVE_TWO_SIDED = 0
_MIN_TWO_SAMPLE = 2
_MIN_REGRESSION = 3


@dataclass(frozen=True, slots=True)
class Sample:
    mean: float
    deviation: float
    count: int


def _normal_below(value: float) -> float:
    return distributions.norm_cdf(-math.inf, value, 0.0, 1.0)


def _level(value: float) -> None:
    if not 0 < value < 1:
        raise ValueError(value)


def _sample_size(value: int) -> None:
    if value < 1:
        raise ValueError(value)


def _alternative_p(statistic: float, cdf: Callable[[float], float], alternative: int) -> float:
    """The p-value for TI's `Hypoth` argument: 0 is ≠, a negative number is <, a positive one
    is > (the Reference Guide's convention, not 0/1/2)."""
    below = cdf(statistic)
    if alternative == _ALTERNATIVE_TWO_SIDED:
        return min(1.0, 2 * min(below, 1 - below))
    if alternative < _ALTERNATIVE_TWO_SIDED:
        return below
    return 1 - below


def mean_interval(
    mean: float, deviation: float, count: int, level: float, *, degrees: float | None = None
) -> tuple[float, float, float]:
    """Return lower bound, upper bound and margin for a z or t interval."""
    _sample_size(count)
    _level(level)
    if deviation < 0 or (degrees is not None and degrees <= 0):
        raise ValueError((deviation, degrees))
    tail = (1 + level) / 2
    critical = (
        distributions.inv_norm(tail, 0.0, 1.0)
        if degrees is None
        else distributions.inv_t(tail, degrees)
    )
    margin = critical * deviation / math.sqrt(count)
    return mean - margin, mean + margin, margin


def two_sample_mean_interval(
    sample1: Sample, sample2: Sample, level: float, *, pooled: bool
) -> tuple[float, float, float, float]:
    """Return Welch or pooled two-sample t interval and its df."""
    _level(level)
    if (
        sample1.count < _MIN_TWO_SAMPLE
        or sample2.count < _MIN_TWO_SAMPLE
        or sample1.deviation < 0
        or sample2.deviation < 0
    ):
        raise ValueError((sample1, sample2))
    if pooled:
        degrees = sample1.count + sample2.count - 2
        variance = (
            (sample1.count - 1) * sample1.deviation**2 + (sample2.count - 1) * sample2.deviation**2
        ) / degrees
        standard_error = math.sqrt(variance * (1 / sample1.count + 1 / sample2.count))
    else:
        term1 = sample1.deviation**2 / sample1.count
        term2 = sample2.deviation**2 / sample2.count
        standard_error = math.sqrt(term1 + term2)
        if standard_error == 0:
            raise ValueError((sample1, sample2))
        degrees = (term1 + term2) ** 2 / (
            term1**2 / (sample1.count - 1) + term2**2 / (sample2.count - 1)
        )
    if standard_error == 0:
        raise ValueError((sample1, sample2))
    estimate = sample1.mean - sample2.mean
    margin = distributions.inv_t((1 + level) / 2, degrees) * standard_error
    return estimate - margin, estimate + margin, margin, degrees


def proportion_interval(successes: int, count: int, level: float) -> tuple[float, float, float]:
    """Wald interval for one proportion, matching the calculator's standard formula."""
    _level(level)
    if count < 1 or not 0 <= successes <= count:
        raise ValueError((successes, count))
    estimate = successes / count
    margin = distributions.inv_norm((1 + level) / 2, 0.0, 1.0) * math.sqrt(
        estimate * (1 - estimate) / count
    )
    return estimate - margin, estimate + margin, margin


def two_proportion_interval(
    successes1: int, count1: int, successes2: int, count2: int, level: float
) -> tuple[float, float, float]:
    _level(level)
    if count1 < 1 or count2 < 1 or not 0 <= successes1 <= count1 or not 0 <= successes2 <= count2:
        raise ValueError((successes1, count1, successes2, count2))
    estimate = successes1 / count1 - successes2 / count2
    standard_error = math.sqrt(
        successes1 / count1 * (1 - successes1 / count1) / count1
        + successes2 / count2 * (1 - successes2 / count2) / count2
    )
    margin = distributions.inv_norm((1 + level) / 2, 0.0, 1.0) * standard_error
    return estimate - margin, estimate + margin, margin


def mean_test(
    sample: Sample,
    null: float,
    *,
    degrees: float | None = None,
    alternative: int = _ALTERNATIVE_TWO_SIDED,
) -> tuple[float, float]:
    _sample_size(sample.count)
    if sample.deviation <= 0 or (degrees is not None and degrees <= 0):
        raise ValueError((sample.deviation, degrees))
    statistic = (sample.mean - null) / (sample.deviation / math.sqrt(sample.count))

    def cdf(value: float) -> float:
        if degrees is None:
            return _normal_below(value)
        return distributions.t_cdf(-math.inf, value, degrees)

    return statistic, _alternative_p(statistic, cdf, alternative)


def two_sample_mean_test(
    sample1: Sample,
    sample2: Sample,
    difference: float,
    *,
    pooled: bool,
    alternative: int = _ALTERNATIVE_TWO_SIDED,
) -> tuple[float, float, float]:
    if (
        sample1.count < _MIN_TWO_SAMPLE
        or sample2.count < _MIN_TWO_SAMPLE
        or sample1.deviation < 0
        or sample2.deviation < 0
    ):
        raise ValueError((sample1, sample2))
    if pooled:
        degrees = sample1.count + sample2.count - 2
        variance = (
            (sample1.count - 1) * sample1.deviation**2 + (sample2.count - 1) * sample2.deviation**2
        ) / degrees
        standard_error = math.sqrt(variance * (1 / sample1.count + 1 / sample2.count))
    else:
        term1 = sample1.deviation**2 / sample1.count
        term2 = sample2.deviation**2 / sample2.count
        standard_error = math.sqrt(term1 + term2)
        if standard_error == 0:
            raise ValueError((sample1, sample2))
        degrees = (term1 + term2) ** 2 / (
            term1**2 / (sample1.count - 1) + term2**2 / (sample2.count - 1)
        )
    if standard_error == 0:
        raise ValueError((sample1, sample2))
    statistic = (sample1.mean - sample2.mean - difference) / standard_error
    p_value = _alternative_p(
        statistic, lambda value: distributions.t_cdf(-math.inf, value, degrees), alternative
    )
    return statistic, p_value, degrees


def proportion_test(
    successes: int, count: int, null: float, *, alternative: int = 0
) -> tuple[float, float]:
    if count < 1 or not 0 < null < 1 or not 0 <= successes <= count:
        raise ValueError((successes, count, null))
    statistic = (successes / count - null) / math.sqrt(null * (1 - null) / count)
    return statistic, _alternative_p(statistic, _normal_below, alternative)


def two_proportion_test(
    successes1: int,
    count1: int,
    successes2: int,
    count2: int,
    *,
    alternative: int = 0,
) -> tuple[float, float]:
    if count1 < 1 or count2 < 1 or not 0 <= successes1 <= count1 or not 0 <= successes2 <= count2:
        raise ValueError((successes1, count1, successes2, count2))
    pooled = (successes1 + successes2) / (count1 + count2)
    if not 0 < pooled < 1:
        raise ValueError(pooled)
    standard_error = math.sqrt(pooled * (1 - pooled) * (1 / count1 + 1 / count2))
    statistic = (successes1 / count1 - successes2 / count2) / standard_error
    return statistic, _alternative_p(statistic, _normal_below, alternative)


def chi_square_goodness(
    observed: list[float], expected: list[float], degrees: float
) -> tuple[float, float]:
    if len(observed) != len(expected) or not observed or degrees <= 0:
        raise ValueError((observed, expected, degrees))
    if any(value < 0 for value in observed) or any(value <= 0 for value in expected):
        raise ValueError((observed, expected))
    statistic = sum(
        (actual - target) ** 2 / target for actual, target in zip(observed, expected, strict=True)
    )
    p_value = 1 - distributions.chi2_cdf(0.0, statistic, degrees)
    return statistic, p_value


def f_test(
    sample1: Sample, sample2: Sample, *, alternative: int = _ALTERNATIVE_TWO_SIDED
) -> tuple[float, float, float, float]:
    if (
        sample1.count < _MIN_TWO_SAMPLE
        or sample2.count < _MIN_TWO_SAMPLE
        or sample1.deviation <= 0
        or sample2.deviation <= 0
    ):
        raise ValueError((sample1, sample2))
    statistic = sample1.deviation**2 / sample2.deviation**2
    df1, df2 = sample1.count - 1, sample2.count - 1

    def cdf(value: float) -> float:
        return distributions.f_cdf(0.0, value, df1, df2)

    return statistic, _alternative_p(statistic, cdf, alternative), df1, df2


def regression_slope_test(
    xs: Sequence[float], ys: Sequence[float], slope0: float = 0.0, *, alternative: int = 0
) -> tuple[float, float, float, float, float, float]:
    if len(xs) != len(ys) or len(xs) < _MIN_REGRESSION:
        raise ValueError((len(xs), len(ys)))
    count = len(xs)
    mean_x = sum(xs) / count
    mean_y = sum(ys) / count
    sxx = sum((value - mean_x) ** 2 for value in xs)
    if sxx == 0:
        raise ValueError(sxx)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / sxx
    intercept = mean_y - slope * mean_x
    residual_sum = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys, strict=True))
    degrees = count - 2
    residual_deviation = math.sqrt(residual_sum / degrees)
    slope_error = residual_deviation / math.sqrt(sxx)
    if slope_error:
        statistic = (slope - slope0) / slope_error
    elif slope != slope0:
        statistic = math.copysign(math.inf, slope - slope0)
    else:
        statistic = 0.0
    p_value = _alternative_p(
        statistic,
        lambda value: distributions.t_cdf(-math.inf, value, degrees),
        alternative,
    )
    return statistic, p_value, degrees, intercept, slope, residual_deviation
