# Requirement traced here: FR-STAT-004
import statistics

import pytest

from cassim.core.compat import inference

_X = [1, 2, 3, 4, 5, 6]
_Y = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2]


def test_one_sample_t_interval_matches_the_captured_vce_example():
    lower, upper, margin = inference.mean_interval(
        statistics.mean(_Y), statistics.stdev(_Y), len(_Y), 0.95, degrees=len(_Y) - 1
    )
    assert lower == pytest.approx(3.0805522)
    assert upper == pytest.approx(11.019448)
    assert margin == pytest.approx(3.9694478)


def test_welch_interval_and_pooled_interval_use_their_own_degrees_of_freedom():
    sample_x = inference.Sample(statistics.mean(_X), statistics.stdev(_X), len(_X))
    sample_y = inference.Sample(statistics.mean(_Y), statistics.stdev(_Y), len(_Y))
    welch = inference.two_sample_mean_interval(sample_x, sample_y, 0.95, pooled=False)
    pooled = inference.two_sample_mean_interval(sample_x, sample_y, 0.95, pooled=True)
    assert welch[3] == pytest.approx(7.3082162)
    assert pooled[3] == 10
    assert welch != pooled


def test_proportion_interval_and_test_are_bounded_by_input_validation():
    lower, upper, margin = inference.proportion_interval(12, 20, 0.95)
    assert lower == pytest.approx(0.3853, abs=1e-3)
    assert upper == pytest.approx(0.8147, abs=1e-3)
    assert margin == pytest.approx((upper - lower) / 2)
    z, p_value = inference.proportion_test(12, 20, 0.5)
    assert z == pytest.approx(0.89442719)
    assert p_value == pytest.approx(0.37109337)
    with pytest.raises(ValueError, match="21"):
        inference.proportion_interval(21, 20, 0.95)


def test_chi_square_and_regression_tests_use_the_expected_tail_areas():
    statistic, p_value = inference.chi_square_goodness([10, 20, 30], [20, 20, 20], 2)
    assert statistic == 10
    assert p_value == pytest.approx(0.00673795)
    t, reg_p_value, degrees, intercept, slope, residual_deviation = inference.regression_slope_test(
        _X, _Y
    )
    assert t == pytest.approx(47.238425, rel=1e-6)
    assert reg_p_value < 0.000002
    assert degrees == 4
    assert intercept == pytest.approx(-0.02)
    assert slope == pytest.approx(2.02)
    assert residual_deviation == pytest.approx(0.17888544)
