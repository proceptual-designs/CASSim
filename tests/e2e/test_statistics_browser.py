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

    # A new page has no variable yet: both axes ask for one (emulator run 7, R7-C7).
    add = app.page.get_by_role("button", name="Click to add variable", exact=True)
    expect(add).to_have_count(2, timeout=30000)
    expect(app.page.get_by_role("button", name="Dot Plot", exact=True)).to_have_count(0)
    app.press("Tab")  # the x axis's list (R7-C9)
    expect(app.page.get_by_role("group", name="Choose X List")).to_be_visible()
    expect(app.page.get_by_role("button", name="(none)", exact=True)).to_be_visible()
    app.page.get_by_role("button", name="scores", exact=True).click(force=True)
    expect(app.page.get_by_role("button", name="scores", exact=True)).to_be_visible()
    app.page.get_by_role("button", name="Click to add variable", exact=True).click(force=True)
    expect(app.page.get_by_role("group", name="Choose Y List")).to_be_visible()
    app.page.close()


def test_sorter_switches_between_calculator_and_statistics(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-DOC-001: the sorter is visible and usable from Data & Statistics."""
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), site[1])
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    app.type_text("scores:={1,2,3}")
    app.press("Enter")
    app.wait(lambda: app.results, "the list assignment")
    before = len(app.results)
    app.type_text("time:={2,4,6}")
    app.press("Enter")
    app.wait(lambda: len(app.results) > before, "the second list assignment")
    for key in ("F4", "4", "7"):
        app.press(key)
    expect(app.page.get_by_role("button", name="Page sorter 1.2")).to_be_attached()
    app.press("Tab")  # a new page has no variable yet: Tab opens the x axis's list
    app.page.get_by_role("button", name="scores", exact=True).click(force=True)
    # until the x axis shows scores, both axes still ask for a variable
    add = app.page.get_by_role("button", name="Click to add variable", exact=True)
    expect(add).to_have_count(1)
    add.click(force=True)
    app.page.get_by_role("button", name="time", exact=True).click(force=True)
    app.page.get_by_role("button", name="Page manager", exact=True).click()
    close = app.page.get_by_role("button", name="Close the sorter (enter or esc)")
    expect(close).to_be_attached()
    expect(
        app.page.get_by_role(
            "button", name="1.2 Data & Statistics time vs scores Scatter Plot", exact=True
        )
    ).to_be_attached()
    app.press("Left")
    app.press("Enter")
    expect(close).not_to_be_attached()
    expect(app.page.get_by_role("button", name="Page sorter 1.1")).to_be_attached()
    app.page.get_by_role("button", name="Page manager", exact=True).click()
    expect(close).to_be_attached()
    app.press("Right")
    app.press("Enter")
    expect(close).not_to_be_attached()
    expect(app.page.get_by_role("button", name="Page sorter 1.2")).to_be_attached()
    app.page.close()
