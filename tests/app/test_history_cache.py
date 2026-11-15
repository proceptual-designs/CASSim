# Requirements traced here: FR-CALC-004, FR-DEV-004, FR-DEV-005, FR-DOC-001
"""Calculator history rows are reused only while their rendered state is unchanged."""

from dataclasses import replace

from tests.app.test_splitter_drag import handheld_app

from cassim.device.keys import Binding
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.state import SORTER


def rows(app):
    return app.view.history.controls[1:-2]


def with_history():
    app, page = handheld_app()
    for key in ("1", "enter", "2", "enter"):
        app.press(key)
    return app, page


def test_typing_reuses_history_and_recall_rebuilds_only_changed_row():
    app, _ = with_history()
    first, second = rows(app)
    app.press("3")
    assert rows(app)[0] is first
    assert rows(app)[1] is second
    app.view._click_line("0:entry")
    assert rows(app)[0] is not first
    assert rows(app)[1] is second


def test_history_rows_rebuild_after_scale_change_and_truncation():
    app, _ = with_history()
    before = rows(app)
    app.state.scale *= 1.1
    app.refresh()
    assert all(a is not b for a, b in zip(before, rows(app), strict=True))
    calculator = calculator_of(app.state.document.current)
    assert calculator is not None
    calculator.history.pop()
    app.refresh()
    assert len(rows(app)) == 1
    assert len(app.view._history_rows) == 1


def test_history_rows_rebuild_after_math_size_and_theme_changes():
    app, _ = with_history()
    before = rows(app)
    app.state.system.math_size += 1
    app.refresh()
    resized = rows(app)
    assert all(a is not b for a, b in zip(before, resized, strict=True))
    app.view.theme = replace(app.view.theme, screen_text="#123456")
    app.refresh()
    assert all(a is not b for a, b in zip(resized, rows(app), strict=True))


def test_deleting_and_undoing_a_history_pair_restores_its_rendered_content():
    app, _ = with_history()
    calculator = calculator_of(app.state.document.current)
    assert calculator is not None
    app.view._click_line("0:entry")
    calculator.perform(Binding("backspace"))
    app.refresh()
    assert [entry.text for entry in calculator.history] == ["2"]
    assert len(rows(app)) == 1
    calculator.perform(Binding("undo"))
    app.refresh()
    assert [entry.text for entry in calculator.history] == ["1", "2"]
    assert len(rows(app)) == 2
    assert app.view._history_rows[0][0][0].text == "1"
    assert app.view._history_rows[2][0][0].text == "2"


def test_history_cache_does_not_keep_rows_for_another_page():
    app, _ = with_history()
    old = rows(app)
    app.state.run_action("add_page", "calculator")
    app.refresh()
    assert rows(app) == []
    assert not app.view._history_rows
    app.state.run_action("prev_page")
    app.refresh()
    assert len(rows(app)) == len(old)
    assert all(a is not b for a, b in zip(old, rows(app), strict=True))


def test_opening_the_page_sorter_releases_rows_and_rebuilds_on_return():
    app, _ = with_history()
    before = rows(app)
    app.act("dialog", SORTER)
    assert app.state.screen().sorter is not None
    assert not app.view._history_rows
    app.act("dialog", SORTER)
    assert app.state.screen().sorter is None
    assert all(a is not b for a, b in zip(before, rows(app), strict=True))


def test_pointer_measurement_rebuilds_rows_then_reuses_them_afterwards():
    app, page = with_history()
    original = rows(app)
    app.on_stick("start", 0, 0)
    measuring = rows(app)
    assert all(a is not b for a, b in zip(original, measuring, strict=True))
    assert not app.view._history_rows
    assert all(control.on_size_change is not None for control in measuring)
    app.pointer.hide()
    app.view.measuring = False
    app.refresh()
    fresh = rows(app)
    assert all(a is not b for a, b in zip(measuring, fresh, strict=True))
    app.refresh()
    assert all(a is b for a, b in zip(fresh, rows(app), strict=True))
    for task in page.tasks:
        task.close()
