"""FR-GRAPH-002, FR-GRAPH-004 and FR-GRAPH-006: graph sampling and discontinuities."""

import math

import pytest
import sympy as sp

from cassim.core.compat import sympy_adapter
from cassim.core.compat.sympy_adapter import _check_math_source, compile_math
from cassim.core.session import Session
from cassim.core.values import Expr
from cassim.graph.sampling import (
    CompiledFunction,
    GraphCompileError,
    Viewport,
    Window,
    automatic_tick_step,
    compile_function,
    function_scene,
    sample_function,
    tick_values,
)
from cassim.graph.scene import Polyline, Stroke


def expression(source: str) -> Expr:
    result = Session().eval(source)
    assert result.error is None, result.error
    assert isinstance(result.value, Expr)
    return result.value


def test_compiled_expression_uses_only_the_approved_math_subset() -> None:
    function = compile_function(expression("x^2+sin(x)"), expression("x"))
    assert function.source.startswith("(")
    assert function(2) == pytest.approx(4 + math.sin(2))

    exact = compile_function(expression("x/3+π"), expression("x"))
    assert "math.pi" in exact.source
    assert exact(3) == pytest.approx(math.pi + 1)

    floor = compile_function(expression("floor(x)"), expression("x"))
    assert floor(1.7) == 1


def test_graph_compiler_refuses_an_extra_symbol() -> None:
    with pytest.raises(GraphCompileError, match="only use the variable"):
        compile_function(expression("x+z"), expression("x"))
    with pytest.raises(GraphCompileError, match="variable must be a symbol"):
        compile_function(expression("x^2"), expression("2"))


def test_math_printer_supports_piecewise_conditions_and_rejects_unknown_functions() -> None:
    x = sp.Symbol("x")
    piecewise = sp.Piecewise((x**2, sp.And(x > 0, x < 2)), (x, True))
    _, function = compile_math(piecewise, x)
    assert function(1) == 1
    assert function(3) == 3

    _, minimum = compile_math(sp.Min(x, 1), x)
    assert minimum(2) == 1
    _, maximum = compile_math(sp.Max(x, 1), x)
    assert maximum(2) == 2
    with pytest.raises(ValueError, match="unsupported graph expression"):
        compile_math(sp.gamma(x), x)


def test_math_printer_supports_approved_functions() -> None:
    x = sp.Symbol("x")
    cases = (
        (sp.sin(x), math.sin, 0.3),
        (sp.cos(x), math.cos, 0.3),
        (sp.tan(x), math.tan, 0.3),
        (sp.asin(x), math.asin, 0.3),
        (sp.acos(x), math.acos, 0.3),
        (sp.atan(x), math.atan, 0.3),
        (sp.sinh(x), math.sinh, 0.3),
        (sp.cosh(x), math.cosh, 0.3),
        (sp.tanh(x), math.tanh, 0.3),
        (sp.asinh(x), math.asinh, 0.3),
        (sp.acosh(x), math.acosh, 1.5),
        (sp.atanh(x), math.atanh, 0.3),
        (sp.exp(x), math.exp, 0.3),
        (sp.log(x), math.log, 1.5),
        (sp.Abs(x), math.fabs, -0.3),
        (sp.floor(x), math.floor, 1.5),
        (sp.ceiling(x), math.ceil, 1.5),
    )
    for expression, math_function, argument in cases:
        _, function = compile_math(expression, x)
        assert function(argument) == pytest.approx(math_function(argument))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (sp.true, True),
        (sp.false, False),
        (sp.pi, math.pi),
        (sp.E, math.e),
        (sp.oo, math.inf),
        (-sp.oo, -math.inf),
        (sp.nan, math.nan),
        (sp.Rational(3, 2), 1.5),
        (sp.Integer(4), 4),
        (sp.Float(1.25), 1.25),
    ],
)
def test_math_printer_supports_real_and_boolean_constants(
    value: sp.Expr, expected: float | bool
) -> None:
    _, function = compile_math(value, sp.Symbol("x"))
    result = function(0)
    if isinstance(expected, float) and math.isnan(expected):
        assert math.isnan(result)
    else:
        assert result == pytest.approx(expected)


def test_math_printer_supports_relational_operators() -> None:
    x = sp.Symbol("x")
    relations = (
        (sp.Eq(x, 0, evaluate=False), False),
        (sp.Ne(x, 0, evaluate=False), True),
        (sp.Lt(x, 0, evaluate=False), False),
        (sp.Le(x, 0, evaluate=False), False),
        (sp.Gt(x, 0, evaluate=False), True),
        (sp.Ge(x, 0, evaluate=False), True),
    )
    for relation, expected in relations:
        _, function = compile_math(relation, x)
        assert function(1) is expected


def test_math_printer_supports_or_not_and_piecewise_without_default() -> None:
    x = sp.Symbol("x")
    piecewise = sp.Piecewise((x, sp.Or(x < 0, sp.Not(sp.Eq(x, 0)))))
    _, function = compile_math(piecewise, x)
    assert function(-1) == -1
    assert math.isnan(function(0))
    _, negate = compile_math(sp.Not(sp.Eq(x, 0, evaluate=False), evaluate=False), x)
    assert negate(1) is True
    assert negate(0) is False


def test_math_printer_rejects_an_unmapped_relation(monkeypatch: pytest.MonkeyPatch) -> None:
    x = sp.Symbol("x")
    relation = sp.Eq(x, 0, evaluate=False)
    monkeypatch.delitem(sympy_adapter._GRAPH_BINARY_OPERATORS, "==")
    with pytest.raises(ValueError, match="unsupported graph relation"):
        compile_math(relation, x)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("lambda x: x", "unsupported syntax"),
        ("__import__('os')", "unsupported function call"),
        ("foo", "unsupported name"),
        ("math.__dict__", "unsupported attribute"),
        ("math.sin(x, key=1)", "unsupported function call"),
        ("'text'", "only numeric and boolean constants"),
    ],
)
def test_math_source_validator_rejects_unapproved_ast(source: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _check_math_source(source)


def test_default_window_and_auto_tick_spacing_match_the_capture() -> None:
    window = Window()
    assert (window.x_min, window.x_max) == (-10, 10)
    assert (window.y_min, window.y_max) == pytest.approx((-20 / 3, 20 / 3))
    assert automatic_tick_step(-10, 10) == 1
    assert tick_values(-10, 10) == tuple(float(value) for value in range(-10, 11))
    assert automatic_tick_step(-100, 100) == 10
    assert automatic_tick_step(-10 / 3, 10 / 3) == 0.5
    assert len(tick_values(-10 / 3, 10 / 3)) <= 20


def test_window_maps_upward_math_to_upward_screen_coordinates() -> None:
    window = Window(-2, 2, -2, 2)
    assert window.to_screen(0, 0, 100, 100) == (50, 50)
    assert window.to_screen(0, 2, 100, 100) == (50, 0)


def test_adaptive_sampling_adds_points_for_a_curved_function() -> None:
    viewport = Viewport(Window(-2, 2, -1, 4), 4, 50)
    curves = sample_function(lambda x: x * x, viewport)
    assert len(curves) == 1
    assert len(curves[0].points) > 5
    assert (2, 40) in curves[0].points


def test_sampling_splits_undefined_points_and_vertical_asymptotes() -> None:
    viewport = Viewport(Window(-1, 1, -10, 10), 100, 100)
    curves = sample_function(lambda x: 1 / x, viewport)
    assert len(curves) == 2
    assert curves[0].points[-1][0] < 50
    assert curves[1].points[0][0] > 50


def test_sampling_skips_non_real_values_from_fractional_powers() -> None:
    function = compile_function(expression("x^(3/2)"), expression("x"))
    curves = sample_function(function, Viewport(Window(-1, 1, -1, 1), 40, 40))
    assert curves
    assert all(x >= 20 for curve in curves for x, _ in curve.points)


def test_an_odd_root_is_real_for_negative_x() -> None:
    """R6-A10: the device draws x^(1/3) for x<0 (the real cube root); x^(2/3) is positive."""
    cube_root = compile_function(expression("x^(1/3)"), expression("x"))
    assert cube_root(-8.0) == pytest.approx(-2.0)
    assert compile_function(expression("x^(2/3)"), expression("x"))(-8.0) == pytest.approx(4.0)


def test_sampling_splits_step_discontinuities() -> None:
    curves = sample_function(math.floor, Viewport(Window(-2, 2, -2, 2), 80, 80))
    assert len(curves) >= 3


def test_function_scene_emits_one_curve_layer_with_the_requested_stroke() -> None:
    stroke = Stroke("curve2", 2)
    function = CompiledFunction("x", lambda x: x)
    scene = function_scene([(function, stroke)], Viewport(Window(-1, 1, -1, 1), 20, 20))
    layer = scene.layer("curves")
    assert layer is not None
    assert len(layer.shapes) == 1
    assert isinstance(layer.shapes[0], Polyline)
    assert layer.shapes[0].stroke == stroke
    assert (scene.width, scene.height) == (20, 20)


@pytest.mark.parametrize(
    "bounds",
    [(1, 1, -1, 1), (-1, 1, 2, 2), (-math.inf, 1, -1, 1)],
)
def test_invalid_windows_are_rejected(bounds: tuple[float, float, float, float]) -> None:
    with pytest.raises(ValueError, match=r"window (bounds|minimums)"):
        Window(*bounds)


def test_invalid_plot_dimensions_and_sampling_limits_are_rejected() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        Viewport(Window(), 0, 10)
    with pytest.raises(ValueError, match="max_depth"):
        sample_function(lambda x: x, Viewport(Window(), 10, 10), max_depth=0)


def test_a_function_that_is_undefined_everywhere_produces_no_curve() -> None:
    assert sample_function(lambda x: math.nan, Viewport(Window(), 10, 10)) == ()
