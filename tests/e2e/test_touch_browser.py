"""Computer view on a touch screen (browser run): a tap on the entry line focuses a text box, so
the on-screen keyboard would open, and text put in through it is calculated."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Browser
from test_flows_browser import AppPage

pytestmark = pytest.mark.e2e


def test_a_tap_on_the_entry_line_takes_typing(browser: Browser, site: tuple[Path, str]) -> None:
    context = browser.new_context(viewport={"width": 1100, "height": 700}, has_touch=True)
    page = context.new_page()
    assert page.evaluate("matchMedia('(pointer: coarse)').matches")
    app = AppPage(page, site[1])
    import os  # noqa: PLC0415

    if shots := os.environ.get("CASSIM_SHOTS"):
        page.screenshot(path=f"{shots}/touch_computer.png")
    page.touchscreen.tap(600, 100)  # the empty entry line
    page.wait_for_timeout(500)
    app.wait(
        lambda: page.evaluate("['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)"),
        "a focused text box",
        20,
    )
    page.keyboard.insert_text("2+3")  # as an on-screen keyboard does: text, no key events
    page.wait_for_timeout(300)
    before = len(app.results)
    page.keyboard.press("Enter")
    app.wait(lambda: len(app.results) > before, "the result")
    assert app.results[-1] == "5"
    context.close()
