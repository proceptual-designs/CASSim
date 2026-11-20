"""FR-GRAPH-002: Graphs pointer gestures and plot layout."""

from collections.abc import Callable

import flet as ft
import pytest

from cassim.app.theme import DARK, THEMES, contrast
from cassim.core.session import Session
from cassim.device.editor import Kind
from cassim.device.keys import Action
from cassim.devices.nspire.pages.graphs import FUNCTION_COLOURS, Graphs
from cassim.devices.nspire.ui.graphs_view import GraphsView, graph_colours


def test_graph_rows_use_shared_entry_renderer_and_target_the_selected_function() -> None:
    actions: list[tuple[Action, str]] = []
    view = GraphsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1.0)
    graphs = Graphs(Session())
    graphs.submit(0, "x^2")
    graphs.select_function(1)
    view.refresh(graphs, 600, 400)

    assert len(view.functions.controls) == 1
    container = view.functions.controls[0]
    assert isinstance(container, ft.Container)
    row = container.content
    assert isinstance(row, ft.Row)
    area = row.controls[2]
    assert isinstance(area, ft.GestureDetector)
    container = area.content
    assert isinstance(container, ft.Container)
    field = container.content
    assert isinstance(field, ft.Row)
    entry = field.controls[0]
    assert isinstance(entry, ft.GestureDetector)
    assert entry.on_tap is not None
    tap: Callable[..., object] = entry.on_tap
    tap(None)
    assert actions == [("place", "1::0")]


def test_graph_controls_use_cassim_styles_and_menu_actions() -> None:
    actions: list[tuple[Action, str]] = []
    view = GraphsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1.0)
    view.refresh(Graphs(Session()), 320, 300)
    container = view.functions.controls[0]
    assert isinstance(container, ft.Container)
    row = container.content
    assert isinstance(row, ft.Row)
    assert isinstance(row.controls[0], ft.Checkbox)
    assert row.controls[0].fill_color == DARK.accent
    assert isinstance(row.controls[1], ft.Text)
    assert row.controls[1].color == DARK.screen_text
    history = row.controls[-1]
    assert isinstance(history, ft.TextButton)
    assert isinstance(history.content, ft.Semantics)
    assert history.content.label == "Graph function history"
    icon = history.content.content
    assert isinstance(icon, ft.Icon)
    assert icon.icon == ft.Icons.LIST
    assert icon.color == DARK.menu_accent
    assert history.on_click is not None
    click: Callable[..., object] = history.on_click
    click(None)
    assert actions == [("open_menu", "graphs_history")]


def test_only_the_selected_graph_expression_row_is_drawn() -> None:
    view = GraphsView(DARK, lambda _action, _argument: None, lambda: 1.0)
    graphs = Graphs(Session())
    graphs.submit(0, "x^2")
    graphs.submit(1, "2*x")
    graphs.select_function(1)

    view.refresh(graphs, 600, 400)

    assert len(view.functions.controls) == 1
    container = view.functions.controls[0]
    assert isinstance(container, ft.Container)
    row = container.content
    assert isinstance(row, ft.Row)
    assert isinstance(row.controls[1], ft.Text)
    assert row.controls[1].value == "f2(x) ="


def test_tall_templates_expand_the_entry_without_clipping_the_plot() -> None:
    view = GraphsView(DARK, lambda _action, _argument: None, lambda: 1.0)
    graphs = Graphs(Session())
    editor = graphs.functions[0].editing.editor
    editor.insert_template(Kind.FRACTION)
    editor.insert_template(Kind.FRACTION)
    view.refresh(graphs, 320, 400)

    container = view.functions.controls[0]
    assert isinstance(container, ft.Container)
    row = container.content
    assert isinstance(row, ft.Row)
    assert row.height is not None
    assert row.height > 56
    assert isinstance(view.plot.content, ft.Stack)
    assert view.plot.content.height == 400 - row.height


def test_plot_canvas_uses_the_space_below_the_controls() -> None:
    view = GraphsView(DARK, lambda _action, _argument: None, lambda: 1.0)
    view.refresh(Graphs(Session()), 320, 300)

    assert isinstance(view.plot.content, ft.Stack)
    assert view.plot.content.height == 248


def test_graph_labels_are_in_the_curve_colour() -> None:
    view = GraphsView(DARK, lambda _action, _argument: None, lambda: 1.0)
    graphs = Graphs(Session())
    graphs.submit(0, "x^2")

    view.refresh(graphs, 600, 400)

    assert isinstance(view.plot.content, ft.Stack)
    label = view.plot.content.controls[1]
    assert isinstance(label, ft.Container)
    assert isinstance(label.content, ft.Markdown)
    assert label.content.latex_style is not None
    assert label.content.latex_style.color == DARK.graph_blue
    assert "mathbf{f1}" in label.content.value


def test_function_number_sets_the_label_colour_and_black_is_the_screen_text() -> None:
    """FR-GRAPH-001: f3 is TI's black, drawn in the theme's foreground colour."""
    view = GraphsView(DARK, lambda _action, _argument: None, lambda: 1.0)
    graphs = Graphs(Session(), ("f1", "f2"))
    graphs.submit(0, "x")

    view.refresh(graphs, 600, 400)

    assert isinstance(view.plot.content, ft.Stack)
    label = view.plot.content.controls[1]
    assert isinstance(label, ft.Container)
    assert isinstance(label.content, ft.Markdown)
    assert label.content.latex_style is not None
    assert label.content.latex_style.color == DARK.screen_text


@pytest.mark.parametrize("name", list(THEMES))
def test_graph_colours_read_well_on_the_screen_in_every_theme(name: str) -> None:
    """FR-GRAPH-001: TI's colour order as theme tokens, legible on the screen colour."""
    theme = THEMES[name]
    colours = graph_colours(theme)
    values = [colours[colour] for colour in FUNCTION_COLOURS]
    assert len(set(values)) == len(values)
    for value in values:
        assert contrast(value, theme.screen) >= 3


def test_pinch_event_dispatches_an_anchored_zoom_gesture() -> None:
    actions: list[tuple[Action, str]] = []
    view = GraphsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1.0)
    point = ft.Offset(30, 25)
    control = view._plot_gestures
    view._scale_start(
        ft.ScaleStartEvent(
            name="scale_start",
            control=control,
            local_focal_point=point,
            global_focal_point=point,
            pointer_count=2,
        )
    )
    view._scale_update(
        ft.ScaleUpdateEvent(
            name="scale_update",
            control=control,
            local_focal_point=point,
            global_focal_point=point,
            focal_point_delta=ft.Offset(12, 20),
            pointer_count=2,
            horizontal_scale=2,
            vertical_scale=2,
            scale=2,
            rotation=0,
        )
    )

    assert actions == [("graphs_gesture", "12,20,0.5,30,25")]


def test_wheel_zoom_uses_the_pointer_as_its_anchor() -> None:
    actions: list[tuple[Action, str]] = []
    view = GraphsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1.0)
    point = ft.Offset(30, 25)
    view._scroll(
        ft.ScrollEvent(
            name="scroll",
            control=view._plot_gestures,
            local_position=point,
            global_position=point,
            scroll_delta=ft.Offset(0, 120),
        )
    )

    assert actions == [("graphs_gesture", "0,0,1.2214027581601699,30,25")]
