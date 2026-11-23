"""FR-GRAPH-003: headless graph analysis over user-selected bounds."""

import math

import pytest

from cassim.graph.analysis import (
    GraphEvaluationError,
    bounded_area,
    derivative,
    find_inflection,
    find_intersection,
    find_maximum,
    find_minimum,
    find_zero,
    integral,
)


def cubic(x: float) -> float:
    return x**3 - 3 * x


def test_zero_refines_a_user_selected_bracket() -> None:
    assert find_zero(cubic, 1.2, 2.2) == pytest.approx(3**0.5, abs=1e-8)


def test_extrema_are_refined_inside_the_selected_intervals() -> None:
    assert find_minimum(cubic, 0.3, 1.8) == pytest.approx((1, -2), abs=1e-7)
    assert find_maximum(cubic, -2.4, -0.8) == pytest.approx((-1, 2), abs=1e-7)


def test_intersection_and_inflection_return_screenable_points() -> None:
    assert find_intersection(cubic, lambda x: x, 1.5, 2.5) == pytest.approx((2, 2), abs=1e-8)
    assert find_inflection(cubic, -1, 1) == pytest.approx((0, 0), abs=1e-6)


def test_derivative_integral_and_bounded_area_match_the_corpus() -> None:
    assert derivative(cubic, 2) == pytest.approx(9, abs=1e-7)
    assert integral(cubic, 0, 2) == pytest.approx(-2, abs=1e-10)
    assert bounded_area(cubic, lambda x: x, 0, 2) == pytest.approx(4, abs=1e-9)


def test_integral_preserves_orientation_for_reversed_bounds() -> None:
    assert integral(lambda x: x, 1, -1) == pytest.approx(0)
    assert integral(lambda x: x, 0, 2) == pytest.approx(2)
    assert bounded_area(lambda x: x, lambda _: 0, 2, 0) == pytest.approx(2)
    with pytest.raises(ValueError, match="finite"):
        bounded_area(lambda x: x, lambda _: 0, 0, math.nan)


def test_zero_search_requires_a_bracket_and_rejects_a_pole() -> None:
    with pytest.raises(ValueError, match="do not bracket"):
        find_zero(lambda x: x * x + 1, -1, 1)
    with pytest.raises(GraphEvaluationError, match="undefined"):
        find_zero(lambda x: 1 / x, -1, 1)
    with pytest.raises(ArithmeticError, match="did not converge"):
        find_zero(lambda x: 1 / (x - 0.123), -1, 1)


def test_zero_search_uses_position_tolerance_for_small_scale_functions() -> None:
    assert find_zero(lambda x: 1e-12 * (x - 1), 0, 4) == pytest.approx(1, abs=1e-9)


def test_non_finite_evaluations_and_invalid_bounds_are_explicit() -> None:
    with pytest.raises(GraphEvaluationError, match="undefined"):
        integral(lambda x: 1 / x, -1, 1)
    with pytest.raises(ValueError, match="increasing"):
        find_minimum(cubic, 2, 1)
    with pytest.raises(ValueError, match="finite"):
        derivative(cubic, float("inf"))
    with pytest.raises(ValueError, match="max_depth"):
        integral(cubic, 0, 2, max_depth=25)


def test_zero_at_a_bound_is_returned_without_extra_iteration() -> None:
    assert find_zero(lambda x: x * (x - 1), 0, 0.5) == 0


def test_zero_at_upper_bound_and_iteration_limit_are_handled() -> None:
    assert find_zero(lambda x: x - 1, 0, 1) == 1
    with pytest.raises(ValueError, match="max_iterations"):
        find_zero(cubic, 0, 2, max_iterations=0)
    with pytest.raises(ArithmeticError, match="iteration limit"):
        find_zero(lambda x: x - 1.3, 0, 2, max_iterations=1)


def test_analysis_rejects_non_finite_values_and_invalid_tolerances() -> None:
    with pytest.raises(GraphEvaluationError, match="not finite"):
        derivative(lambda _: math.inf, 0)

    def invalid_result(_: float) -> float:
        raise ValueError("not numeric")

    with pytest.raises(GraphEvaluationError, match="undefined"):
        derivative(invalid_result, 0)
    with pytest.raises(ValueError, match="finite and increasing"):
        find_zero(lambda x: x, -math.inf, 1)
    with pytest.raises(ValueError, match="tolerance"):
        find_minimum(cubic, 0, 1, tolerance=0)
    with pytest.raises(ValueError, match="tolerance"):
        integral(cubic, 0, 1, tolerance=math.inf)


def test_integral_handles_equal_and_reversed_bounds_and_reports_depth_limit() -> None:
    assert integral(cubic, 2, 2) == 0
    assert integral(lambda x: x, 2, 0) == pytest.approx(-2)
    with pytest.raises(ValueError, match="bounds must be finite"):
        integral(cubic, math.inf, math.inf)
    with pytest.raises(ArithmeticError, match="subdivision limit"):
        integral(math.exp, 0, 1, tolerance=1e-20, max_depth=1)


def test_find_zero_accepts_a_root_found_to_rounding() -> None:
    """A converged bracket whose midpoint residual is rounding noise is still a root."""
    assert find_zero(lambda x: x**3 - 3 * x, -2.5, -1.0000000000000004) == pytest.approx(
        -math.sqrt(3)
    )
