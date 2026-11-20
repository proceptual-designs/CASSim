"""FR-GRAPH-002: the Graphs page's Window / Zoom menu, Window Settings and the zoom tools."""

import pytest

from cassim.device.keys import Binding
from cassim.device.wizard import Wizard
from cassim.devices.nspire.pages import graph_tools
from cassim.devices.nspire.pages.graphs import Graphs
from cassim.devices.nspire.ui.state import AppState
from cassim.graph.sampling import Window
from cassim.graph.scene import Box, Label
from cassim.graph.zoom import QUADRANT_1, STANDARD, TRIG


def graphs_state() -> tuple[AppState, Graphs, list[Wizard]]:
    state = AppState()
    shown: list[Wizard] = []
    state.show_wizard = shown.append
    state.run_action("add_page", "graphs")
    graphs = state.graphs
    assert graphs is not None
    graphs.submit(0, "x^2")
    graphs.scene(318, 212)  # the handheld's plot size
    return state, graphs, shown


def pick(state: AppState, *keys: str) -> None:
    state.key_event("F2")
    for key in keys:
        state.key_event(key)


def test_window_zoom_menu_is_numbered_as_on_the_device() -> None:
    state, _, _ = graphs_state()
    pick(state, "4")
    assert state.menu is not None
    rows = state.menu.view().rows
    assert [(row.key, row.label) for row in rows] == [
        ("1", "Window Settings…"),
        ("2", "Zoom – Box"),
        ("3", "Zoom – In"),
        ("4", "Zoom – Out"),
        ("5", "Zoom – Standard"),
        ("6", "Zoom – Quadrant 1"),
        ("7", "Zoom – User"),
        ("8", "Zoom – Trig"),
        ("9", "Zoom – Data"),
        ("A", "Zoom – Fit"),
        ("B", "Zoom – Square"),
        ("C", "Zoom – Decimal"),
    ]
    assert all(row.enabled for row in rows)


def test_preset_zooms_from_the_menu() -> None:
    state, graphs, _ = graphs_state()
    pick(state, "4", "6")
    assert graphs.window == QUADRANT_1
    pick(state, "4", "8")
    assert graphs.window == TRIG
    pick(state, "4", "5")
    assert graphs.window == STANDARD
    pick(state, "4", "C")
    assert graphs.window == Window(-32, 32, -21.3, 21.3)


def test_window_settings_dialog_shows_full_digits_and_sets_the_window() -> None:
    state, graphs, shown = graphs_state()
    pick(state, "4", "1")
    assert len(shown) == 1
    wizard = shown[0]
    assert wizard.title == "Window Settings"
    assert [field.label for field in wizard.fields] == [
        "XMin",
        "XMax",
        "XScale",
        "YMin",
        "YMax",
        "YScale",
    ]
    defaults = wizard.defaults()
    assert defaults == {
        "xmin": "-10",
        "xmax": "10",
        "xscale": "Auto",
        "ymin": "-6.6666666666667",
        "ymax": "6.6666666666667",
        "yscale": "Auto",
    }
    values = {**defaults, "xmin": "-1", "xmax": "2·π"}
    assert state.finish_wizard(wizard, values) == []
    assert graphs.window.x_min == -1
    assert graphs.window.x_max == pytest.approx(6.283185307179586)
    assert graphs.window.y_max == pytest.approx(20 / 3)

    pick(state, "4", "8")
    pick(state, "4", "1")
    assert shown[-1].defaults()["xmin"] == "-2·π"


def test_window_settings_refuses_bad_values_and_keeps_the_window() -> None:
    state, graphs, shown = graphs_state()
    pick(state, "4", "1")
    wizard = shown[0]
    defaults = wizard.defaults()
    assert state.finish_wizard(wizard, {**defaults, "xmin": "abc"}) == ["XMin: enter a number"]
    assert state.finish_wizard(wizard, {**defaults, "xmin": "10"}) == [
        "XMin must be less than XMax"
    ]
    assert state.finish_wizard(wizard, {**defaults, "ymin": "7"}) == ["YMin must be less than YMax"]
    assert graphs.window == STANDARD


def test_zoom_user_returns_to_the_last_window_set_by_hand() -> None:
    """graphs2 D8: User went back to the window after Zoom - In, after Fit and Square."""
    state, graphs, _ = graphs_state()
    pick(state, "4", "7")
    assert graphs.window == STANDARD  # nothing stored yet: no change (graphs4 D8)
    pick(state, "4", "3")
    state.run_action("graphs", "tap:159,106")
    user = graphs.window
    state.key_event("Escape")
    pick(state, "4", "A")
    pick(state, "4", "B")
    assert graphs.window != user
    pick(state, "4", "7")
    assert graphs.window == user


def test_zoom_fit_square_and_data_from_the_menu() -> None:
    state, graphs, _ = graphs_state()
    pick(state, "4", "A")
    assert (graphs.window.x_min, graphs.window.x_max) == (-10, 10)
    assert graphs.window.y_min == pytest.approx(-10.0012137898067, rel=1e-3)
    assert graphs.window.y_max == pytest.approx(110.0197745302515, rel=1e-3)
    pick(state, "4", "B")
    assert graphs.window.y_max - graphs.window.y_min == pytest.approx(20 * 212 / 318)
    pick(state, "4", "8")
    pick(state, "4", "9")
    assert graphs.window.x_max == pytest.approx(7.2831853071796)


def test_zoom_in_asks_for_a_centre_and_stays_on_until_escape() -> None:
    """D8: `Center?` at the pointer; Enter zooms about it; the tool stays on."""
    state, graphs, _ = graphs_state()
    pick(state, "4", "3")
    assert graphs.tools.tool is graph_tools.Tool.ZOOM_IN
    tool = graphs.scene(318, 212).layer("tool")
    assert tool is not None
    assert "Center?" in [shape.text for shape in tool.shapes if isinstance(shape, Label)]
    state.key_event("Enter")
    assert graphs.window.x_max - graphs.window.x_min == pytest.approx(10)
    assert (graphs.window.x_min + graphs.window.x_max) / 2 == pytest.approx(0)
    state.key_event("ArrowRight")
    state.key_event("ArrowUp")
    state.key_event("Enter")
    assert graphs.window.x_max - graphs.window.x_min == pytest.approx(5)
    assert (graphs.window.x_min + graphs.window.x_max) / 2 > 0
    state.key_event("Escape")
    assert graphs.tools.tool is None
    tool = graphs.scene(318, 212).layer("tool")
    assert tool is not None
    assert tool.shapes == ()


def test_zoom_out_doubles_about_the_tapped_point() -> None:
    state, graphs, _ = graphs_state()
    pick(state, "4", "4")
    state.run_action("graphs", "tap:238.5,53")  # (5, 3.33) on the Standard window
    assert graphs.window.x_min == pytest.approx(-15)
    assert graphs.window.x_max == pytest.approx(25)
    assert graphs.window.y_max - graphs.window.y_min == pytest.approx(80 / 3)
    assert graphs.tools.tool is graph_tools.Tool.ZOOM_OUT


def test_zoom_box_takes_two_corners_then_starts_again() -> None:
    """graphs2 D8: `1st corner?`, `2nd corner?`, the window is the box, Box stays on."""
    state, graphs, _ = graphs_state()
    pick(state, "4", "2")

    def prompts() -> list[str]:
        layer = graphs.scene(318, 212).layer("tool")
        assert layer is not None
        return [shape.text for shape in layer.shapes if isinstance(shape, Label)]

    assert prompts() == ["1st corner?"]
    state.run_action("graphs", "tap:159,106")
    assert prompts() == ["2nd corner?"]
    layer = graphs.scene(318, 212).layer("tool")
    assert layer is not None
    assert any(isinstance(shape, Box) for shape in layer.shapes)
    state.run_action("graphs", "tap:238.5,53")
    window = graphs.window
    assert (window.x_min, window.x_max) == pytest.approx((0, 5))
    assert (window.y_min, window.y_max) == pytest.approx((0, 10 / 3))
    assert prompts() == ["1st corner?"]
    before = graphs.window
    state.run_action("graphs", "tap:10,10")
    state.run_action("graphs", "tap:10,10")  # no width: refused, the window stays
    assert graphs.window == before
    state.key_event("Escape")
    assert graphs.tools.tool is None


def test_taps_without_a_tool_do_nothing_and_the_wheel_zoom_stays() -> None:
    """Decision 0034 item 1: the wheel and pinch zoom are kept."""
    state, graphs, _ = graphs_state()
    state.run_action("graphs", "tap:10,10")
    assert graphs.window == STANDARD
    state.run_action("graphs_gesture", "0,0,0.5,159,106")
    assert graphs.window.x_max - graphs.window.x_min == pytest.approx(10)


def test_unknown_graphs_actions_are_refused() -> None:
    state, graphs, _ = graphs_state()
    with pytest.raises(ValueError, match="unknown graphs action"):
        graph_tools.perform(graphs, "spin:1")
    with pytest.raises(ValueError, match="four values"):
        state.run_action("graphs", "window:1,2")
    assert graph_tools.key(graphs, Binding("left")) is False
