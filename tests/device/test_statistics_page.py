# Requirements traced here: FR-STAT-001, FR-STAT-003, FR-STAT-005, FR-DOC-010
"""Data & Statistics views over live Problem variables."""

from types import SimpleNamespace
from typing import Any, cast

import pytest

from cassim.app.theme import DARK
from cassim.core.session import Session
from cassim.devices.nspire.pages.statistics import (
    Statistics,
    dump_statistics,
    load_statistics,
)
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.statistics_view import StatisticsView
from cassim.graph.scene import Box, Fill, Label


def _eval(session: Session, expression: str) -> None:
    result = session.eval(expression)
    assert result.error is None, result.error


def test_plot_data_refreshes_after_a_list_changes() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3}")
    statistics = Statistics(session)
    statistics.perform(f"x:{statistics.lists[0]}")
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


def test_a_dragged_point_stores_three_decimal_places() -> None:
    """FR-STAT-005 (emulator run 6, S1): the point (3,5) dragged up stored ys[3] as 6.949."""
    session = Session()
    _eval(session, "xs:={1,2,3,4,5,6}")
    _eval(session, "ys:={2,3,5,4,6,8}")
    statistics = Statistics(session)
    statistics.perform("x:xs")
    statistics.perform("y:ys")

    expression = statistics.drag_expression(2, 3.0000000001, 6.94912345678)
    assert expression == "xs[3]:=3:ys[3]:=6.949"
    assert statistics.drag_expression(2, 3, -0.0001) == "xs[3]:=3:ys[3]:=0"


def test_dragging_a_dot_plot_point_updates_its_source_list() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3}")
    statistics = Statistics(session)
    statistics.perform(f"x:{statistics.lists[0]}")

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
    statistics.perform(f"x:{statistics.lists[0]}")
    statistics.perform("sort-order:List Order")
    statistics.perform("plot:Bar Chart")

    restored = load_statistics(Statistics(session), dump_statistics(statistics))
    assert restored.category_order == "List Order"
    assert restored.plot_data().x == ("B", "A", "B")


def test_force_categorical_and_numeric_x_switch_numeric_string_lists() -> None:
    session = Session()
    _eval(session, 'labels:={"7","8","7"}')
    statistics = Statistics(session)
    statistics.perform(f"x:{statistics.lists[0]}")
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
    statistics.perform(f"x:{statistics.lists[0]}")
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
    statistics.perform(f"x:{statistics.lists[0]}")
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


def _rows(state: AppState) -> list[tuple[str, bool]]:
    assert state.menu is not None
    return [(row.label, row.enabled) for row in state.menu.view().rows]


def _d1_page(plot: str) -> AppState:
    state = AppState()
    state.run_action("add_page", "statistics")
    statistics = state.statistics
    assert statistics is not None
    session = cast("Session", statistics.session)
    _eval(session, "d1:={2,4,4,4.536,5,5,7.536,9}")
    _eval(session, "xs:={1,2,3,4.435,5,6,7,8}")
    statistics.update()
    statistics.perform("x:d1")
    statistics.perform(f"plot:{plot}")
    return state


def test_box_plot_and_histogram_context_menus() -> None:
    """FR-STAT-001, FR-STAT-003 (stats4, R5-G2): the device's items, numbers and grey states."""
    state = _d1_page("Box Plot")
    state.run_action("context_menu", "statistics_context_box")
    assert _rows(state) == [
        ("Dot Plot", True),
        ("Histogram", True),
        ("Normal Probability Plot", True),
        ("Extend Box Plot Whiskers", True),
        ("Zoom", True),
        ("Color", True),
    ]
    state.run_action("insert", "5")
    assert _rows(state)[-4:] == [
        ("Window settings…", True),
        ("Zoom - data", True),
        ("Zoom - in", False),
        ("Zoom - out", False),
    ]
    state.menu = None
    state.run_action("context_menu", "statistics_context_box")
    state.run_action("insert", "2")
    statistics = state.statistics
    assert statistics is not None
    assert statistics.plot_type.value == "Histogram"
    state.run_action("context_menu", "statistics_context_histogram")
    assert [label for label, _ in _rows(state)] == [
        "Dot Plot",
        "Box Plot",
        "Normal Probability Plot",
        "Scale",
        "Bin settings",
        "Zoom",
        "Color",
    ]
    state.run_action("insert", "4")
    assert _rows(state)[-2:] == [("Percent", True), ("Density", True)]
    state.run_action("insert", "2")
    assert statistics.histogram_scale == "Density"
    state.run_action("context_menu", "statistics_context_histogram")
    state.run_action("insert", "5")
    assert _rows(state)[-2:] == [("Equal bin width", True), ("Variable bin width", False)]


def test_regression_context_menu() -> None:
    """Stats4, R5-G2: the line and its label have the same list."""
    state = _d1_page("Dot Plot")
    statistics = state.statistics
    assert statistics is not None
    statistics.perform("x:xs")
    statistics.perform("y:d1")
    statistics.perform("regression:LinRegMx")
    state.run_action("context_menu", "statistics_context_regression")
    assert _rows(state) == [
        ("Remove regression", True),
        ("Shade under function", False),
        ("Show Residual Squares", True),
        ("Show Residual Plot", True),
        ("Graph trace", False),
        ("Color", True),
    ]
    state.run_action("insert", "6")
    assert _rows(state)[-3:] == [
        ("Line color", False),
        ("Fill color", False),
        ("Text color", False),
    ]
    state.menu = None
    state.run_action("context_menu", "statistics_context_regression")
    state.run_action("insert", "1")
    assert statistics.regression == ""


def test_a_right_click_finds_the_mark_under_it() -> None:
    """R5-G2: a right-click on the regression's label, a bar or a box opens that mark's menu."""
    session = Session()
    _eval(session, "d1:={2,4,4,4.536,5,5,7.536,9}")
    _eval(session, "xs:={1,2,3,4.435,5,6,7,8}")
    statistics = Statistics(session)
    actions: list[tuple[str, str]] = []
    view = StatisticsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1)

    def data_shapes() -> tuple[Any, ...]:
        layer = statistics.scene(view._width, view._chart_height, axis_labels=False).layer("data")
        assert layer is not None
        return layer.shapes

    def right_click(x: float, y: float) -> str:
        view._context(cast("Any", SimpleNamespace(local_position=SimpleNamespace(x=x, y=y))))
        return actions[-1][1]

    statistics.perform("x:xs")
    statistics.perform("y:d1")
    statistics.perform("regression:LinRegMx")
    view.refresh(statistics, 320, 220)
    label = next(
        shape
        for layer in statistics.scene(view._width, view._chart_height, axis_labels=False).layers
        for shape in layer.shapes
        if isinstance(shape, Label) and shape.colour == "curve2"
    )
    assert right_click(label.x + 5, label.y + 5) == "statistics_context_regression"

    statistics.perform("y:")
    statistics.perform("x:d1")
    statistics.perform("plot:Histogram")
    view.refresh(statistics, 320, 220)
    bar = next(shape for shape in data_shapes() if isinstance(shape, Fill))
    x = sum(px for px, _ in bar.points) / len(bar.points)
    y = sum(py for _, py in bar.points) / len(bar.points)
    assert right_click(x, y) == "statistics_context_histogram"
    statistics.perform("plot:Box Plot")
    view.refresh(statistics, 320, 220)
    box = next(shape for shape in data_shapes() if isinstance(shape, Box))
    assert right_click(box.x + 2, box.y + 2) == "statistics_context_box"


def _scatter(session: Session) -> Statistics:
    _eval(session, "time:={1,2,3,4}")
    _eval(session, "distance:={2,4,6,8}")
    statistics = Statistics(session)
    statistics.perform("x:time")
    statistics.perform("y:distance")
    return statistics


def test_zooming_a_scatter_plot_keeps_the_point_under_the_pointer() -> None:
    """Simon's note 4 (2026-11-25): the wheel and a pinch zoom a plot about the pointer; the
    device has no wheel zoom (run 6 S1), so this is CASSim's own (decision 0034 item 1)."""
    statistics = _scatter(Session())
    point = statistics.plotted_points(320, 200)[2]
    before = statistics.drag_value_at(320, 200, point.screen_x, point.screen_y)
    statistics.perform(f"zoom:320,200,0.5,{point.screen_x},{point.screen_y}")
    assert statistics.window is not None
    after = statistics.drag_value_at(320, 200, point.screen_x, point.screen_y)
    assert before is not None
    assert after is not None
    assert after[0] == pytest.approx(before[0])
    assert after[1] == pytest.approx(before[1])
    xmin, xmax, ymin, ymax = statistics.window
    assert statistics.message == ""
    statistics.perform("zoom:320,200,2,160,100")
    assert statistics.window[1] - statistics.window[0] == pytest.approx(2 * (xmax - xmin))
    assert statistics.window[3] - statistics.window[2] == pytest.approx(2 * (ymax - ymin))


def test_a_one_variable_plot_zooms_along_x_only() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3,9}")
    statistics = Statistics(session)
    statistics.perform(f"x:{statistics.lists[0]}")
    statistics.perform("zoom:320,200,0.5,160,100")
    assert statistics.window is not None
    statistics.perform("zoom:320,200,2,160,100")
    xmin, xmax, _, _ = statistics.window
    assert xmax - xmin == pytest.approx(9 - 1 + 0.8)  # the 5% padding each side, back again


def test_the_wheel_and_a_pinch_send_a_zoom_and_one_finger_still_drags() -> None:
    statistics = _scatter(Session())
    actions: list[tuple[str, str]] = []
    view = StatisticsView(DARK, lambda action, arg: actions.append((action, arg)), lambda: 1)
    view.refresh(statistics, 320, 220)
    view._scroll(
        cast(
            Any,
            SimpleNamespace(
                scroll_delta=SimpleNamespace(y=-120), local_position=SimpleNamespace(x=100, y=50)
            ),
        )
    )
    assert actions[-1][0] == "statistics"
    assert actions[-1][1].startswith("zoom:")
    pinch = SimpleNamespace(pointer_count=2, local_focal_point=SimpleNamespace(x=100, y=50))
    view._scale_start(cast(Any, pinch))
    view._scale_update(cast(Any, SimpleNamespace(**vars(pinch), scale=2.0)))
    assert actions[-1][1].startswith("zoom:")
    view._scale_end(cast(Any, None))
    point = statistics.plotted_points(view._width, view._chart_height)[1]
    at = SimpleNamespace(x=point.screen_x, y=point.screen_y)
    view._scale_start(cast(Any, SimpleNamespace(pointer_count=1, local_focal_point=at)))
    assert view._drag_index == 1


# ---- saved pages keep their lists (a bug: Save and Open lost the plot) ------------------------


def test_a_loaded_page_keeps_lists_that_have_not_arrived_yet() -> None:
    """FR-DOC-010: a saved Data & Statistics page is loaded before its lists exist (in the
    browser the engine replays the sheet later; on any computer the sheet may come after it).
    Its X, Y, summary and split lists must survive that, and fill in once the lists arrive."""
    session = Session()
    statistics = load_statistics(
        Statistics(session),
        {"x": "heights", "y": "weights", "summary": "", "split": "", "plot": "Scatter Plot"},
    )
    assert (statistics.x_name, statistics.y_name) == ("heights", "weights")
    _eval(session, "heights:={150,160,170}")
    _eval(session, "weights:={50,60,70}")
    statistics.update()
    assert (statistics.x_name, statistics.y_name) == ("heights", "weights")
    assert statistics.plot_data().x == (150.0, 160.0, 170.0)


def test_a_deleted_list_is_still_dropped() -> None:
    session = Session()
    _eval(session, "scores:={1,2,3}")
    statistics = Statistics(session)
    statistics.perform(f"x:{statistics.lists[0]}")
    assert statistics.x_name == "scores"
    _eval(session, "DelVar scores")
    statistics.update()
    assert statistics.x_name == ""


def test_save_and_open_through_the_browsers_engine_keep_the_statistics_page() -> None:
    """FR-DOC-010, FR-STAT-001: the browser opens a document with `Runner.load`, whose engine
    is in a worker. The document that comes back is the one that was saved: the sheet's data,
    the Graphs function and the statistics page's list."""
    import asyncio  # noqa: PLC0415

    from tests.device.test_spreadsheet_page import (  # noqa: PLC0415
        NAME_ROW,
        Recording,
        sheet_app,
        sheet_of,
        type_cell,
    )

    from cassim.device.engine import LocalEngine  # noqa: PLC0415
    from cassim.devices.nspire.pages import PAGES  # noqa: PLC0415
    from cassim.devices.nspire.pages.graphs import graphs_of  # noqa: PLC0415
    from cassim.devices.nspire.runner import Runner  # noqa: PLC0415
    from cassim.doc.serialize import dumps, to_dict  # noqa: PLC0415

    runner = Runner(LocalEngine())
    state = sheet_app(Recording(sessions=runner.new_session))
    sheet = sheet_of(state)
    sheet.go((0, NAME_ROW))
    type_cell(state, "xs")
    for row, value in ((1, "4"), (2, "5"), (3, "6")):
        sheet.go((0, row))
        type_cell(state, value)
    state.run_action("add_page", "graphs")
    graphs = graphs_of(state.document.current)
    assert graphs is not None
    graphs.submit(0, "x^2")
    for _ in range(2):  # the engine has the sheet's list before the page is added
        asyncio.run(runner.sync(state.document))
        state.prepare()
    state.run_action("add_page", "statistics")
    asyncio.run(runner.sync(state.document))
    state.prepare()
    saved = state.document.problems[0].pages[3].model
    assert isinstance(saved, Statistics)
    saved.perform("x:xs")  # a new page has no variable until one is chosen (run 7)
    assert saved.x_name == "xs"

    fresh = Runner(LocalEngine())
    loaded = asyncio.run(fresh.load(dumps(state.document), PAGES))
    assert to_dict(loaded) == to_dict(state.document)
    asyncio.run(fresh.sync(loaded))
    statistics = loaded.problems[0].pages[3].model
    assert isinstance(statistics, Statistics)
    statistics.update()
    assert statistics.plot_data().x == (4.0, 5.0, 6.0)
    graph = graphs_of(loaded.problems[0].pages[2])
    assert graph is not None
    graph.update()
    compiled = graph.functions[0].compiled
    assert compiled is not None
    assert compiled(3) == 9


def test_a_dragged_point_is_stored_to_a_ten_thousandth_of_the_window() -> None:
    """FR-STAT-005 (emulator run 7, R7-C1): on a window of x 0 to 100 and y 0 to 1000 a drag
    stores 40.06 and 567.8; a selected point moves by the same rounded shift."""
    session = Session()
    _eval(session, "xs:={1,2,3,4,5,6,7,8}")
    _eval(session, "ys:={2,4,5,4,5,7,8,9}")
    statistics = Statistics(session)
    statistics.perform("x:xs")
    statistics.perform("y:ys")
    statistics.window = (0.0, 100.0, 0.0, 1000.0)
    assert statistics.drag_expression(7, 40.0612, 567.8333) == "xs[8]:=40.06:ys[8]:=567.8"
    _eval(session, "xs[8]:=40.06:ys[8]:=567.8")
    statistics.plot_data()  # the page reads the lists again
    statistics.select(7)
    statistics.select(6)
    moved = statistics.drag_expression(6, 72.2712, 219.8123)
    assert moved == "xs[7]:=72.27:ys[7]:=219.8:xs[8]:=105.33:ys[8]:=779.6"


def test_a_new_page_shows_the_first_list_as_a_caption_plot() -> None:
    """FR-STAT-001 (emulator runs 3, 5 and 7, R7-C7): before a variable is chosen, a new page shows
    the alphabetically first list's values as labelled dots under `Caption: name`."""
    session = Session()
    _eval(session, "xs:={1,2,3}")
    _eval(session, 'cat:={"a","b","c"}')
    statistics = Statistics(session)
    scene = statistics.scene(300, 200)
    layer = scene.layer("caption")
    assert layer is not None
    texts = [shape.text for shape in layer.shapes if isinstance(shape, Label)]
    assert texts == ["Caption: cat", "a", "b", "c"]
    statistics.perform("x:xs")
    assert statistics.scene(300, 200).layer("caption") is None
