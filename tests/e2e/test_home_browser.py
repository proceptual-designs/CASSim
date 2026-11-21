"""The all-in-one Home screen in the published web app."""

from __future__ import annotations

import re
import time
from io import BytesIO

import pytest
from PIL import Image
from playwright.sync_api import Browser, Locator, Page, expect

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


def test_home_chooses_an_app_and_a_reload_returns_home(browser: Browser, site) -> None:
    """FR-PROF-010 to FR-PROF-016, NFR-PERF-007."""
    page = browser.new_page(viewport={"width": 1100, "height": 760})
    logs: list[str] = []
    page.on(
        "console",
        lambda message: logs.append(message.text) if message.text.startswith("CASSIM:") else None,
    )
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
        logs.clear()
        page.goto(site[1], wait_until="load")
        assert wait_for_log(page, logs, "CASSIM: HOME"), "a new launch did not open Home"
        assert not any(line == "CASSIM: READY" for line in logs)
    finally:
        page.close()


def test_home_settings_share_the_cassim_appearance(browser: Browser, site) -> None:
    """FR-PROF-017: Home Settings does not need a device UI."""
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
        page.get_by_role("button", name=re.compile("^CASSim")).click()
        page.get_by_role("button", name=re.compile("^Settings")).click()
        expect(page.get_by_text("Appearance")).to_be_attached()
        page.get_by_role("alertdialog").get_by_role("button").first.click()
        page.get_by_text("Light", exact=True).click()
        page.get_by_role("button", name="Save").click()
        nspire = page.get_by_role("button", name=re.compile("Nspire"))
        expect(nspire).to_be_attached()
        bounds = nspire.bounding_box()
        assert bounds is not None
        pixels = page.screenshot(
            clip={
                "x": bounds["x"] + 16,
                "y": bounds["y"] + bounds["height"] / 2,
                "width": 2,
                "height": 2,
            }
        )
        pixel = Image.open(BytesIO(pixels)).getpixel((0, 0))
        assert isinstance(pixel, tuple)
        assert pixel[:3] == (255, 255, 255)
    finally:
        page.close()


def test_pseudocode_code_view_has_a_home_menu(browser: Browser, site) -> None:
    """FR-PROF-016: Pseudocode returns through Home and can open Nspire."""
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
        expect(page.get_by_role("button", name="Approx", exact=True)).to_be_attached()
        expect(page.get_by_role("button", name="Radian", exact=True)).to_be_attached()
        expect(page.get_by_text("Symbols", exact=True)).to_be_attached()
        expect(page.get_by_text("Trace Table", exact=True)).to_be_attached()
        assert "CASSIM: UI" not in logs
        page.get_by_role("button", name=re.compile("^CASSim")).click()
        logs.clear()
        page.get_by_role("button", name="Home", exact=True).click()
        assert wait_for_log(page, logs, "CASSIM: HOME", seconds=10), "Home did not reopen"
        enable_semantics(page)
        page.get_by_role("button", name=re.compile("^Pseudocode")).click()
        expect(page.get_by_role("button", name="Pseudocode", exact=True)).to_be_attached(
            timeout=10_000
        )
        page.get_by_role("button", name=re.compile("^CASSim")).click()
        logs.clear()
        page.get_by_role("button", name="Home", exact=True).click()
        assert wait_for_log(page, logs, "CASSIM: HOME", seconds=10), "Home did not reopen"
        enable_semantics(page)
        page.get_by_role("button", name=re.compile("Nspire")).click()
        assert wait_for_log(page, logs, "CASSIM: READY", seconds=60), (
            "Nspire did not open from Home"
        )
    finally:
        page.close()


def clear_editor(page: Page, editor: Locator) -> None:
    """Select all and delete until the app has seen it.

    Right after the editor opens, keys can reach the browser's text box before Flutter's field
    is attached to it: they never reach Python and Flutter later restores its own text. Python
    draws the line-number gutter, so the example's "1 2 3 ..." disappearing proves the first
    clear arrived; once attached, later edits always arrive."""
    gutter = page.get_by_text(re.compile(r"^1(\s+\d+)+$"))
    for _ in range(5):
        editor.focus()
        editor.press("Control+A")
        editor.press("Backspace")
        try:
            expect(gutter).to_have_count(0, timeout=3_000)
        except AssertionError:
            continue
        if editor.input_value() == "":
            return
    expect(gutter).to_have_count(0)
    expect(editor).to_have_value("")


def test_pseudocode_typing_aids_are_opt_in_token_aware_and_undoable(browser: Browser, site) -> None:
    """FR-SYN-013: convenience symbols are opt-in and do not rewrite source contexts blindly."""
    page = browser.new_page(viewport={"width": 1100, "height": 760})
    try:
        page.goto(site[1], wait_until="load")
        expect(page.locator("flt-semantics-placeholder")).to_have_count(1)
        enable_semantics(page)
        page.get_by_role("button", name=re.compile("^Pseudocode")).click()
        typing_aids = page.get_by_role("switch", name="Typing aids")
        expect(typing_aids).to_be_enabled()
        expect(typing_aids).not_to_be_checked()
        editor = page.get_by_role("textbox", name="Code")
        expect(editor).to_be_attached()

        def replace(value: str) -> None:
            clear_editor(page, editor)
            editor.press_sequentially(value)
            expect(editor).to_have_value(value)

        def source() -> str:
            return str(editor.input_value())

        replace("x <")
        editor.press_sequentially("-")
        assert source() == "x <-"

        typing_aids.click()
        expect(typing_aids).to_be_checked()
        editor = page.get_by_role("textbox", name="Code")
        expect(editor).to_be_attached()
        replace("x <")
        editor.press_sequentially("-")
        expect(editor).to_have_value("x ←")
        page.keyboard.press("Control+z")
        expect(editor).to_have_value("x <-")

        page.goto(site[1] + "#/app/pseudocode", wait_until="load")
        enable_semantics(page)
        editor = page.get_by_role("textbox", name="Code")
        expect(editor).to_be_attached(timeout=60_000)
        page.wait_for_timeout(300)
        replace("print @")
        editor.press_sequentially("pi", delay=30)
        expect(editor).to_have_value("print π")
        page.keyboard.press("Control+z")
        expect(editor).to_have_value("print @pi")

        replace('print "<')
        editor.press_sequentially("-")
        expect(editor).to_have_value('print "<-')
    finally:
        page.close()
