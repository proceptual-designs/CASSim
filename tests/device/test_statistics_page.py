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


def test_plot_pointer_click_does_not_open_a_menu() -> None:
    actions: list[tuple[str, str]] = []
    view = StatisticsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1)

    assert view.click_at(100, 50)
    assert actions == []
