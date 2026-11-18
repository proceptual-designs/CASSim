# Requirements traced here: FR-STAT-001, FR-STAT-005
"""The Data & Statistics page renders from live Problem variables in the built site."""

from pathlib import Path

import pytest
from playwright.sync_api import Browser, expect
from tests.e2e.test_flows_browser import AppPage

pytestmark = pytest.mark.e2e


def test_statistics_page_renders_for_a_live_list(browser: Browser, site: tuple[Path, str]) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    app.type_text("scores:={1,2,2,3}")
    app.press("Enter")
    app.wait(lambda: app.results, "the list assignment")

    for key in ("F4", "4", "7"):
        app.press(key)

    expect(app.page.get_by_role("button", name="X: scores")).to_be_visible(timeout=30000)
    expect(app.page.get_by_role("button", name="Dot Plot")).to_be_visible()
    app.page.close()
