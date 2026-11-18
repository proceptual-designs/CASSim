"""Clicking the title-bar status in the built site changes the settings (browser run).

The canvas has no DOM to read, so the effect is read from results printed by `#/debug`. The status
sits at the right of the title bar; fields are located by their order from the right edge.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from playwright.sync_api import Browser
from test_flows_browser import AppPage

pytestmark = pytest.mark.e2e


def evaluate(app: AppPage, text: str) -> str:
    before = len(app.results)
    app.type_text(text)
    app.press("Enter")
    app.wait(lambda: len(app.results) > before, f"the result of {text!r}")
    return app.results[-1]


def cycle(app: AppPage, field: str) -> None:
    app.page.get_by_role("button", name=re.compile(rf"^{field} ")).click()
    app.page.wait_for_timeout(300)
    app.page.mouse.click(600, 300)  # give the focus back to the calculator


def test_status_fields_change_document_settings(browser: Browser, site: tuple[Path, str]) -> None:
    app = AppPage(
        browser.new_page(viewport={"width": 1100, "height": 700}),
        site[1],
    )
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    assert evaluate(app, "sin(90)") != "1"  # radians
    cycle(app, "angle")
    assert evaluate(app, "sin(90)") == "1"
    cycle(app, "angle")  # restore Radian before checking mode and domain

    assert "." not in evaluate(app, "1/3")
    cycle(app, "calc")
    assert "." in evaluate(app, "1/3")
    cycle(app, "calc")  # restore Auto before checking the complex-domain display

    assert "ⅇ^" not in evaluate(app, "3+4@i")  # Real: rectangular
    cycle(app, "domain")  # Real -> Rect
    assert "ⅇ^" not in evaluate(app, "3+4@i")
    cycle(app, "domain")
    assert "ⅇ^" in evaluate(app, "3+4@i")
    cycle(app, "domain")
    assert "ⅇ^" not in evaluate(app, "3+4@i")
    app.page.close()
