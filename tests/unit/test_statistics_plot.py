# Requirements traced here: FR-STAT-004
from cassim.devices.nspire.statistics_plot import PValuePlot, p_value_scene
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
