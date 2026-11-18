"""Headless numerical tools for Trace and Analyze Graph."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

type Function = Callable[[float], float]
type Point = tuple[float, float]
_MAX_QUADRATURE_DEPTH = 24


@dataclass(frozen=True, slots=True)
class _SimpsonSegment:
    lower: float
    upper: float
    lower_value: float
    midpoint_value: float
    upper_value: float
    estimate: float
    tolerance: float
    depth: int


class GraphEvaluationError(ArithmeticError):
    """A graph function could not be evaluated as a finite real number."""


def _evaluate(function: Function, x: float) -> float:
    try:
        value = float(function(x))
    except (ArithmeticError, TypeError, ValueError) as error:
        raise GraphEvaluationError(f"graph function is undefined at x={x}") from error
    if not math.isfinite(value):
        raise GraphEvaluationError(f"graph function is not finite at x={x}")
    return value


def _validate_interval(lower: float, upper: float, tolerance: float) -> None:
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        msg = "bounds must be finite and increasing"
        raise ValueError(msg)
    if not math.isfinite(tolerance) or tolerance <= 0:
        msg = "tolerance must be finite and positive"
        raise ValueError(msg)


def find_zero(
    function: Function,
    lower: float,
    upper: float,
    *,
    tolerance: float = 1e-9,
    max_iterations: int = 128,
) -> float:
    """Refine a sign-changing bracket with bisection and verify the resulting residual."""
    _validate_interval(lower, upper, tolerance)
    if max_iterations < 1:
        msg = "max_iterations must be positive"
        raise ValueError(msg)
    f_lower = _evaluate(function, lower)
    f_upper = _evaluate(function, upper)
    if f_lower == 0:
        return lower
    if f_upper == 0:
        return upper
    if (f_lower < 0) == (f_upper < 0):
        msg = "bounds do not bracket a zero"
        raise ValueError(msg)

    for _ in range(max_iterations):
        midpoint = (lower + upper) / 2
        f_midpoint = _evaluate(function, midpoint)
        if f_midpoint == 0:
            return midpoint
        if upper - lower <= tolerance:
            break
        if (f_lower < 0) != (f_midpoint < 0):
            upper, f_upper = midpoint, f_midpoint
        else:
            lower, f_lower = midpoint, f_midpoint

    if upper - lower > tolerance:
        msg = "zero search did not converge within the iteration limit"
        raise ArithmeticError(msg)
    midpoint = (lower + upper) / 2
    f_midpoint = abs(_evaluate(function, midpoint))
    if f_midpoint > min(abs(f_lower), abs(f_upper)):
        msg = "zero search did not converge to a root"
        raise ArithmeticError(msg)
    return midpoint


def derivative(function: Function, x: float) -> float:
    """Estimate dy/dx with a scale-aware central difference."""
    if not math.isfinite(x):
        msg = "the derivative position must be finite"
        raise ValueError(msg)
    step = 1e-5 * max(1.0, abs(x))
    return (_evaluate(function, x + step) - _evaluate(function, x - step)) / (2 * step)


def _extremum(
    function: Function, lower: float, upper: float, *, maximum: bool, tolerance: float
) -> Point:
    _validate_interval(lower, upper, tolerance)
    ratio = (math.sqrt(5) - 1) / 2
    left = upper - ratio * (upper - lower)
    right = lower + ratio * (upper - lower)
    f_left = _evaluate(function, left)
    f_right = _evaluate(function, right)

    for _ in range(128):
        if upper - lower <= tolerance:
            break
        keep_left = f_left > f_right if maximum else f_left < f_right
        if keep_left:
            upper, right, f_right = right, left, f_left
            left = upper - ratio * (upper - lower)
            f_left = _evaluate(function, left)
        else:
            lower, left, f_left = left, right, f_right
            right = lower + ratio * (upper - lower)
            f_right = _evaluate(function, right)
    x = (lower + upper) / 2
    return x, _evaluate(function, x)


def find_minimum(
    function: Function, lower: float, upper: float, *, tolerance: float = 1e-8
) -> Point:
    """Find a single local minimum inside a user-selected interval."""
    return _extremum(function, lower, upper, maximum=False, tolerance=tolerance)


def find_maximum(
    function: Function, lower: float, upper: float, *, tolerance: float = 1e-8
) -> Point:
    """Find a single local maximum inside a user-selected interval."""
    return _extremum(function, lower, upper, maximum=True, tolerance=tolerance)


def find_intersection(
    first: Function, second: Function, lower: float, upper: float, *, tolerance: float = 1e-9
) -> Point:
    """Find one intersection inside a user-selected x interval."""
    x = find_zero(
        lambda value: _evaluate(first, value) - _evaluate(second, value),
        lower,
        upper,
        tolerance=tolerance,
    )
    return x, _evaluate(first, x)


def find_inflection(
    function: Function, lower: float, upper: float, *, tolerance: float = 1e-7
) -> Point:
    """Find an inflection by bracketing a sign change in a central second difference."""

    def second_difference(x: float) -> float:
        step = 1e-3 * max(1.0, abs(x))
        return (
            _evaluate(function, x + step)
            - 2 * _evaluate(function, x)
            + _evaluate(function, x - step)
        ) / step**2

    x = find_zero(second_difference, lower, upper, tolerance=tolerance)
    return x, _evaluate(function, x)


def integral(
    function: Function,
    lower: float,
    upper: float,
    *,
    tolerance: float = 1e-9,
    max_depth: int = 20,
) -> float:
    """Integrate a finite function with adaptive Simpson quadrature."""
    if not math.isfinite(tolerance) or tolerance <= 0:
        msg = "tolerance must be finite and positive"
        raise ValueError(msg)
    if not 1 <= max_depth <= _MAX_QUADRATURE_DEPTH:
        msg = f"max_depth must be between 1 and {_MAX_QUADRATURE_DEPTH}"
        raise ValueError(msg)
    if lower == upper:
        if not math.isfinite(lower):
            msg = "bounds must be finite"
            raise ValueError(msg)
        return 0.0
    if lower > upper:
        return -integral(function, upper, lower, tolerance=tolerance, max_depth=max_depth)
    _validate_interval(lower, upper, tolerance)
    f_lower = _evaluate(function, lower)
    f_upper = _evaluate(function, upper)
    midpoint = (lower + upper) / 2
    f_midpoint = _evaluate(function, midpoint)
    whole = (upper - lower) * (f_lower + 4 * f_midpoint + f_upper) / 6

    def refine(segment: _SimpsonSegment) -> float:
        middle = (segment.lower + segment.upper) / 2
        left_middle = (segment.lower + middle) / 2
        right_middle = (middle + segment.upper) / 2
        f_left_middle = _evaluate(function, left_middle)
        f_right_middle = _evaluate(function, right_middle)
        left_estimate = (
            (middle - segment.lower)
            * (segment.lower_value + 4 * f_left_middle + segment.midpoint_value)
            / 6
        )
        right_estimate = (
            (segment.upper - middle)
            * (segment.midpoint_value + 4 * f_right_middle + segment.upper_value)
            / 6
        )
        delta = left_estimate + right_estimate - segment.estimate
        if abs(delta) <= 15 * segment.tolerance:
            return left_estimate + right_estimate + delta / 15
        if segment.depth == 0:
            msg = "integral did not converge within the subdivision limit"
            raise ArithmeticError(msg)
        return refine(
            _SimpsonSegment(
                segment.lower,
                middle,
                segment.lower_value,
                f_left_middle,
                segment.midpoint_value,
                left_estimate,
                segment.tolerance / 2,
                segment.depth - 1,
            )
        ) + refine(
            _SimpsonSegment(
                middle,
                segment.upper,
                segment.midpoint_value,
                f_right_middle,
                segment.upper_value,
                right_estimate,
                segment.tolerance / 2,
                segment.depth - 1,
            )
        )

    return refine(
        _SimpsonSegment(lower, upper, f_lower, f_midpoint, f_upper, whole, tolerance, max_depth)
    )


def bounded_area(
    first: Function,
    second: Function,
    lower: float,
    upper: float,
    *,
    tolerance: float = 1e-9,
) -> float:
    """Return the unsigned area between two functions over typed x bounds."""
    return abs(
        integral(
            lambda x: abs(_evaluate(first, x) - _evaluate(second, x)),
            lower,
            upper,
            tolerance=tolerance,
        )
    )
