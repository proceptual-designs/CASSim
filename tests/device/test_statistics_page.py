# Requirements traced here: FR-STAT-001, FR-STAT-003, FR-STAT-005
"""Data & Statistics views over live Problem variables."""

from cassim.app.theme import DARK
from cassim.core.session import Session
from cassim.devices.nspire.pages.statistics import (
    Statistics,
    dump_statistics,
    load_statistics,
)
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.statistics_view import StatisticsView
from cassim.graph.scene import Label


def _eval(session: Session, expression: str) -> None:
    result = session.eval(expression)
    assert result.error is None, result.error


def test_plot_data_refreshes_after_a_list_changes() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3}")
    statistics = Statistics(session)
    assert statistics.plot_data().x == (1.0, 2.0, 3.0)

    _eval(session, "scores:={2,4}")
    assert statistics.plot_data().x == (2.0, 4.0)


def test_dragging_a_scatter_point_updates_its_shared_source_lists() -> None:
    session = Session()
    _eval(session, "time:={1,2,3}")
    _eval(session, "distance:={2,4,6}")
    statistics = Statistics(session)
    statistics.perform("x:time")
    statistics.perform("y:distance")

    expression = statistics.drag_expression(1, 2.5, 5.25)
    assert expression is not None
    assert expression == "time[2]:=2.5:distance[2]:=5.25"
    _eval(session, expression)

    assert statistics.plot_data().x == (1.0, 2.5, 3.0)
    assert statistics.plot_data().y == (2.0, 5.25, 6.0)


def test_dragging_a_dot_plot_point_updates_its_source_list() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3}")
    statistics = Statistics(session)

    expression = statistics.drag_expression(1, 2.5, 0)
    assert expression == "scores[2]:=2.5"
    _eval(session, expression)

    assert statistics.plot_data().x == (1.0, 2.5, 3.0)


def test_regression_adds_fit_and_residual_squares_to_the_plot() -> None:
    session = Session()
    _eval(session, "time:={1,2,3,4}")
    _eval(session, "distance:={2,4,5,8}")
    statistics = Statistics(session)
    statistics.perform("x:time")
    statistics.perform("y:distance")
    statistics.perform("regression:LinRegMx")
    statistics.perform("toggle-residual-squares")

    data = statistics.plot_data()
    assert data.regression
    assert data.residuals
    assert data.residual_squares is not None
    assert data.regression_label.startswith("y = 1.9·x+0")
    assert any(
        isinstance(shape, Label) and shape.text.startswith("Σres² =")
        for layer in statistics.scene(320, 220).layers
        for shape in layer.shapes
    )


def test_plot_settings_round_trip_without_copying_list_data() -> None:
    session = Session()
    _eval(session, 'category:={"B","A","B"}')
    statistics = Statistics(session)
    statistics.perform("sort-order:List Order")
    statistics.perform("plot:Bar Chart")

    restored = load_statistics(Statistics(session), dump_statistics(statistics))
    assert restored.category_order == "List Order"
    assert restored.plot_data().x == ("B", "A", "B")


def test_force_categorical_and_numeric_x_switch_numeric_string_lists() -> None:
    session = Session()
    _eval(session, 'labels:={"7","8","7"}')
    statistics = Statistics(session)
    assert statistics.categorical_x
    assert statistics.plot_data().x == ("7", "8", "7")

    statistics.perform("toggle-force-x")
    assert not statistics.categorical_x
    assert statistics.plot_data().x == (7.0, 8.0, 7.0)

    statistics.perform("toggle-force-x")
    assert statistics.categorical_x


def test_plot_value_supports_the_mean_of_a_problem_list() -> None:
    session = Session()
    _eval(session, "scores:={2,4,8}")
    statistics = Statistics(session)

    assert statistics.finish_wizard("value", {"x": "mean(scores)"}) == []
    assert statistics.plot_data().plot_value == 14 / 3


def test_plot_function_rejects_unsupported_expressions() -> None:
    statistics = Statistics(Session())

    assert statistics.finish_wizard("function", {"expression": "x+"}) == [
        "Enter a supported numeric function of x."
    ]


def test_context_menu_key_opens_the_statistics_menu() -> None:
    state = AppState()
    state.run_action("add_page", "statistics")
    state.run_action("context_menu")

    assert state.menu is not None
    assert state.menu.root.label == "Menu"


def test_statistics_axis_picker_includes_none_and_plot_context_menu_is_specific() -> None:
    state = AppState()
    state.run_action("add_page", "statistics")
    state.run_action("open_menu", "statistics_x")
    assert state.menu is not None
    assert state.menu.root.items[0].label == "(none)"

    state.run_action("escape")
    state.run_action("context_menu", "statistics_context_plot")
    assert state.menu is not None
    assert state.menu.root.label == "Plot"


def test_plot_pointer_click_does_not_open_a_menu() -> None:
    actions: list[tuple[str, str]] = []
    view = StatisticsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1)

    assert view.click_at(100, 50)
    assert actions == []


def test_axis_labels_open_their_list_pickers_and_points_are_selectable() -> None:
    session = Session()
    _eval(session, "time:={1,2,3}")
    _eval(session, "distance:={2,4,6}")
    statistics = Statistics(session)
    statistics.perform("x:time")
    statistics.perform("y:distance")
    actions: list[tuple[str, str]] = []
    view = StatisticsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1)
    view.refresh(statistics, 320, 220)

    assert view.click_at(160, view._chart_height - 10)
    assert actions[-1] == ("open_menu", "statistics_x")
    assert view.click_at(10, view._chart_height / 2)
    assert actions[-1] == ("open_menu", "statistics_y")

    point = statistics.plotted_points(view._width, view._chart_height)[1]
    assert view.click_at(point.screen_x, point.screen_y)
    assert actions[-1] == ("statistics_point", "1")
    assert statistics.message == "(2, 4)"


def test_numeric_dot_plot_points_are_selectable_and_draggable() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3}")
    statistics = Statistics(session)
    actions: list[tuple[str, str]] = []
    view = StatisticsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1)
    view.refresh(statistics, 320, 220)
    point = statistics.plotted_points(view._width, view._chart_height)[1]

    assert view.click_at(point.screen_x, point.screen_y)
    assert actions[-1] == ("statistics_point", "1")
    assert statistics.message == "2"
    assert statistics.drag_value_at(
        view._width, view._chart_height, point.screen_x, point.screen_y
    ) == (2.0, 0.0)


def test_dragging_a_selected_dot_moves_every_selected_dot() -> None:
    """FR-STAT-005 (R5-G1): with a 4 selected, dragging the 7 to 7.536 moves the 4 to 4.536."""
    session = Session()
    _eval(session, "d1:={2,4,4,4,5,5,7,9}")
    statistics = Statistics(session)
    statistics.select(3)
    statistics.select(6)

    expression = statistics.drag_expression(6, 7.536, 0)
    assert expression == "d1[4]:=4.536:d1[7]:=7.536"
    _eval(session, expression)
    assert statistics.plot_data().x == (2.0, 4.0, 4.0, 4.536, 5.0, 5.0, 7.536, 9.0)


def test_dragging_a_scatter_point_moves_both_coordinates_of_each_selected_point() -> None:
    """R5-G1: a scatter drag changes both lists; selected points move by the same amounts."""
    session = Session()
    _eval(session, "xs:={1,2,3}")
    _eval(session, "ys:={2,4,6}")
    statistics = Statistics(session)
    statistics.perform("x:xs")
    statistics.perform("y:ys")
    statistics.select(0)
    statistics.select(2)
    assert statistics.drag_expression(2, 3.5, 7) == "xs[1]:=1.5:ys[1]:=3:xs[3]:=3.5:ys[3]:=7"
    assert statistics.drag_expression(1, 2.5, 5) == "xs[2]:=2.5:ys[2]:=5"  # not selected


def test_the_selection_is_shared_by_row_across_the_plots_of_a_problem() -> None:
    """R5-G1: after selecting in the dot plot, the scatter page shows rows 4 and 7 selected;
    a click on nothing clears them; another Problem has its own selection."""
    session = Session()
    _eval(session, "d1:={2,4,4,4,5,5,7,9}")
    _eval(session, "xs:={1,2,3,4,5,6,7,8}")
    dots, scatter = Statistics(session), Statistics(session)
    scatter.perform("x:xs")
    scatter.perform("y:d1")
    before = scatter.scene(320, 200)
    dots.select(3)
    assert scatter.plot_data().selected == frozenset({3})
    assert scatter.scene(320, 200) is not before  # redrawn with the selection
    assert Statistics(Session()).selected == set()
    view = StatisticsView(DARK, lambda action, arg: None, lambda: 1)
    view.refresh(dots, 320, 220)
    view.click_at(300, 20)
    assert scatter.selected == set()
