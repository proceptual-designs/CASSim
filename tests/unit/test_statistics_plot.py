# Requirements traced here: FR-STAT-004
import math

import pytest

from cassim.devices.nspire.statistics_plot import (
    AreaPlot,
    PValuePlot,
    area_scene,
    normal_density,
    p_value_scene,
    t_density,
)
from cassim.graph.scene import Fill, Label, Polyline


def test_two_sided_p_value_scene_shades_both_tails():
    scene = p_value_scene(PValuePlot(0.8944, 0.3711, 0), 160, 180)
    layer = scene.layer("plot")
    assert layer is not None
    assert sum(isinstance(shape, Fill) for shape in layer.shapes) == 2
    assert any(isinstance(shape, Polyline) for shape in layer.shapes)
    assert any(isinstance(shape, Label) and "PVal = 0.3711" in shape.text for shape in layer.shapes)


def test_one_sided_p_value_scene_shades_the_selected_tail():
    scene = p_value_scene(PValuePlot(-1.25, 0.1056, 1), 160, 180)
    layer = scene.layer("plot")
    assert layer is not None
    assert sum(isinstance(shape, Fill) for shape in layer.shapes) == 1


def test_right_tail_beyond_the_visible_window_has_no_fill():
    scene = p_value_scene(PValuePlot(5, 0.0000003, 2), 160, 180)
    layer = scene.layer("plot")
    assert layer is not None
    assert not any(isinstance(shape, Fill) for shape in layer.shapes)
    assert any(isinstance(shape, Label) and "z = 5.0000" in shape.text for shape in layer.shapes)


def test_a_t_pane_uses_the_t_density_and_names_its_statistic():
    """R5-I2 (t Test, Ha: μ > μ0): `t = 1.4661`, the right tail shaded, the axis named t."""
    scene = p_value_scene(PValuePlot(1.4661, 0.0930, 2, "t", 7), 160, 180)
    layer = scene.layer("plot")
    assert layer is not None
    assert sum(isinstance(shape, Fill) for shape in layer.shapes) == 1
    texts = [shape.text for shape in layer.shapes if isinstance(shape, Label)]
    assert "t = 1.4661    PVal = 0.0930" in texts
    assert "t" in texts
    assert t_density(0, 7) < normal_density(0)  # heavier tails, lower peak


def test_shade_area_labels_the_normal_curve_and_its_area():
    """Split2 H14: Normal Cdf from −∞ to 1 with Shade area: `normPdf(x,0,1)`, Area .841…"""
    plot = AreaPlot(-math.inf, 1)
    assert plot.area == pytest.approx(0.84134475)
    layer = area_scene(plot, 160, 180).layer("plot")
    assert layer is not None
    texts = [shape.text for shape in layer.shapes if isinstance(shape, Label)]
    assert texts[:2] == ["normPdf(x,0,1)", "Area: 0.841345"]
    assert sum(isinstance(shape, Fill) for shape in layer.shapes) == 1
