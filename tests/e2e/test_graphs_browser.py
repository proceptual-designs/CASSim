"""FR-GRAPH-001: function entry compiles through the browser engine worker."""

from pathlib import Path

import pytest
from playwright.sync_api import Browser, expect
from tests.e2e.test_flows_browser import AppPage

pytestmark = pytest.mark.e2e


def test_function_entry_finishes_plotting_in_the_browser(
    browser: Browser, site: tuple[Path, str]
) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    for key in ("F4", "4", "4"):
        app.press(key)
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")

    expect(app.page.get_by_text("f1(x) =")).to_be_visible(timeout=30000)
    app.type_text("x^2")
    app.press("ArrowRight")
    app.type_text("-4")
    app.press("Enter")

    expect(app.page.get_by_text("f1(x) =")).to_be_visible(timeout=30000)
    expect(app.page.get_by_text("f2(x) =")).to_be_hidden(timeout=30000)
    app.press("ArrowDown")
    expect(app.page.get_by_text("f2(x) =")).to_be_visible(timeout=30000)
    expect(app.page.get_by_text("Plotting…")).to_be_hidden(timeout=30000)
    app.page.get_by_text("Graph function history", exact=True).evaluate(
        "(element) => element.click()"
    )
    expect(app.page.get_by_role("button", name="1 f1(x) = x^(2)-4")).to_be_visible(timeout=10000)
    expect(app.page.get_by_role("button", name="2 f2(x) = …")).to_be_visible(timeout=10000)
    app.press("Escape")
    app.press("ctrl+Left")
    app.type_text("f1(3)")
    app.press("Enter")
    app.wait(lambda: bool(app.results), "the graph function result")
    assert app.results[-1] == "5"
    app.page.close()


def test_graph_view_menu_updates_grid_and_axes(browser: Browser, site: tuple[Path, str]) -> None:
    """FR-GRAPH-002: Graphs View options are reachable in the browser."""
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    for key in ("F4", "4", "4"):
        app.press(key)
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    expect(app.page.get_by_text("f1(x) =")).to_be_visible(timeout=30000)

    for key in ("F2", "2", "6", "2", "F2", "2", "5", "F2", "2"):
        app.press(key)
    expect(app.page.get_by_role("button", name="5 Show axes", exact=True)).to_be_visible(
        timeout=10000
    )
    expect(
        app.page.get_by_role("button", name="8 Hide axes end values", exact=True)
    ).to_be_visible()
    app.press("Escape")
    app.press("Escape")
    for key in ("F2", "2", "6"):
        app.press(key)
    expect(app.page.get_by_role("button", name="2 Dot Grid", exact=True)).to_be_visible(
        timeout=10000
    )
    app.page.close()


def test_window_zoom_and_trace_menus_work_in_the_browser(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-GRAPH-002, FR-GRAPH-003: Window Settings opens with full digits; Trace and Analyze
    Graph are reachable once a function is plotted."""
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    for key in ("F4", "4", "4"):
        app.press(key)
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    expect(app.page.get_by_text("f1(x) =")).to_be_visible(timeout=30000)
    app.type_text("x^2")
    app.press("ArrowRight")
    app.press("Enter")
    expect(app.page.get_by_text("Plotting…")).to_be_hidden(timeout=30000)
    # sqrt(x) is not real for x < 0: the samples there are gaps, the app carries on
    app.press("ArrowDown")
    app.type_text("sqrt(x")
    app.press("Enter")
    expect(app.page.get_by_text("Plotting…")).to_be_hidden(timeout=30000)
    expect(app.page.get_by_text("encountered an error")).to_have_count(0)

    for key in ("F2", "4"):
        app.press(key)
    expect(app.page.get_by_role("button", name="A Zoom – Fit", exact=True)).to_be_visible(
        timeout=10000
    )
    app.press("1")
    expect(app.page.get_by_text("Window settings")).to_be_visible(timeout=10000)
    # Flutter exposes the value of the focused box only (XMin); the full digits of the other
    # boxes are checked headless in tests/unit/test_graph_window_zoom.py
    expect(app.page.get_by_role("textbox", name="XMin")).to_have_value("-10", timeout=10000)
    expect(app.page.get_by_role("textbox", name="YMin")).to_be_attached()
    app.page.get_by_role("button", name="Cancel").click()

    for key in ("F2", "5"):
        app.press(key)
    expect(app.page.get_by_role("button", name="3 Trace step…", exact=True)).to_be_visible(
        timeout=10000
    )
    app.press("Escape")
    app.press("Escape")
    for key in ("F2", "6"):
        app.press(key)
    expect(app.page.get_by_role("button", name="7 Integral", exact=True)).to_be_visible(
        timeout=10000
    )
    app.page.close()
