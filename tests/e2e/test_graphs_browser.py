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

    expect(app.page.get_by_text("f2(x) =")).to_be_visible(timeout=30000)
    expect(app.page.get_by_text("Plotting…")).to_be_hidden(timeout=30000)
    app.press("ctrl+Left")
    app.type_text("f1(3)")
    app.press("Enter")
    app.wait(lambda: bool(app.results), "the graph function result")
    assert app.results[-1] == "5"
    app.page.close()
