"""The all-in-one Home screen in the published web app."""

from __future__ import annotations

import re
import time

import pytest
from playwright.sync_api import Browser, Page, expect

from cassim.app.home import WELCOME

pytestmark = pytest.mark.e2e


def enable_semantics(page: Page) -> None:
    placeholder = page.locator("flt-semantics-placeholder")
    if placeholder.count():
        placeholder.evaluate("(element) => element.click()")


def wait_for_log(page: Page, logs: list[str], line: str, seconds: float = 60) -> bool:
    end = time.monotonic() + seconds
    while line not in logs and time.monotonic() < end:
        page.wait_for_timeout(100)
    return line in logs


def test_home_chooses_an_app_and_remembers_it(browser: Browser, site) -> None:
    """FR-PROF-010 to FR-PROF-016, NFR-PERF-007."""
    page = browser.new_page(viewport={"width": 1100, "height": 760})
    logs: list[str] = []
    page_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: logs.append(message.text) if message.text.startswith("CASSIM:") else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("pageerror", lambda error: logs.append(f"PAGEERROR:{error}"))
    page.on("pageerror", lambda error: logs.append(f"PAGEERROR:{error}"))
    try:
        page.goto(site[1], wait_until="load")
        assert wait_for_log(page, logs, "CASSIM: HOME"), "Home never drew"
        enable_semantics(page)
        expect(page.get_by_text(WELCOME)).to_be_attached()
        nspire = page.get_by_role("button", name=re.compile("Nspire"))
        classpad = page.get_by_role("button", name=re.compile("Classpad"))
        pseudocode = page.get_by_role("button", name=re.compile("^Pseudocode"))
        expect(nspire).to_be_enabled()
        expect(classpad).to_be_disabled()
        expect(pseudocode).to_be_enabled()
        assert not any(line == "CASSIM: UI" for line in logs)

        nspire.click()
        assert wait_for_log(page, logs, "CASSIM: READY"), "Nspire did not open"
        page.reload(wait_until="load")
        logs.clear()
        assert wait_for_log(page, logs, "CASSIM: READY"), "remembered app did not open"
        assert not any(line == "CASSIM: HOME" for line in logs)
    finally:
        page.close()


def test_home_settings_share_the_cassim_appearance(browser: Browser, site) -> None:
    """FR-PROF-017: Home Settings does not need a device UI."""
    page = browser.new_page(viewport={"width": 1100, "height": 760})
    logs: list[str] = []
    page.on(
        "console",
        lambda message: logs.append(message.text),
    )
    try:
        page.goto(site[1], wait_until="load")
        assert wait_for_log(page, logs, "CASSIM: HOME"), "Home never drew"
        enable_semantics(page)
        page.get_by_role("button", name=re.compile("^CASSim")).click()
        page.get_by_role("button", name="Settings").click()
        expect(page.get_by_text("Appearance")).to_be_attached()
        page.get_by_role("button", name="Cancel").click()
    finally:
        page.close()


def test_pseudocode_code_view_has_a_home_menu(browser: Browser, site) -> None:
    """The second enabled Home choice can be entered and left without loading Nspire."""
    page = browser.new_page(viewport={"width": 1100, "height": 760})
    logs: list[str] = []
    page.on(
        "console",
        lambda message: logs.append(message.text) if message.text.startswith("CASSIM:") else None,
    )
    try:
        page.goto(site[1], wait_until="load")
        assert wait_for_log(page, logs, "CASSIM: HOME"), "Home never drew"
        enable_semantics(page)
        page.get_by_role("button", name=re.compile("^Pseudocode")).click()
        expect(page.get_by_role("button", name="Pseudocode", exact=True)).to_be_attached(
            timeout=10_000
        )
        expect(page.get_by_role("switch", name="Line numbers")).to_be_checked()
        assert "CASSIM: UI" not in logs
        page.get_by_role("button", name=re.compile("^Pseudocode")).click()
        expect(page.get_by_role("button", name="Pseudocode", exact=True)).to_be_attached(
            timeout=10_000
        )
    finally:
        page.close()
