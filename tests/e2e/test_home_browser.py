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


# Playwright full speed: with a per-key delay Flutter web drops shifted keys such as "<"
# (seen 6 times in 6 runs, 2026-11-22), which a real keyboard does not do.
HUMAN_TYPING = 0
REDRAW = 300  # ms for Python and Flutter to catch up, as a person pauses to look
AID_WAIT = 1500  # ms: well past the typing aid's 0.5 s pause, before typing on (PLAN.md A12)


def clear_editor(page: Page, editor: Locator) -> None:
    """Select all and delete until the app has seen it, then let it settle.

    Right after the editor opens, keys can reach the browser's text box before Flutter's field
    is attached: they never reach Python and Flutter later restores its own text. Python draws
    the line-number gutter, so the example's "1 2 3 ..." disappearing proves the first clear
    arrived (a single "1" is not exposed to the test, so later clears get a pause instead)."""
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
            break
    expect(gutter).to_have_count(0)
    expect(editor).to_have_value("")
    page.wait_for_timeout(REDRAW)


def set_typing_aid(page: Page, on: bool) -> None:
    """Turn the typing aid on or off in the Pseudocode CASSim menu's Settings dialog."""
    page.get_by_role("button", name=re.compile("^CASSim")).click()
    page.get_by_role("button", name="Settings…").click()
    switch = page.get_by_role("switch", name="Typing aid")
    for _ in range(3):  # a click can be dropped while the dialog is still opening
        if switch.is_checked() == on:
            break
        switch.click()
        page.wait_for_timeout(REDRAW)
    expect(switch).to_be_checked(checked=on)
    save = page.get_by_role("button", name="Save", exact=True)
    save.click()
    expect(save).not_to_be_attached(timeout=10_000)  # the dialog has closed and redrawn


def test_pseudocode_typing_aid_is_on_token_aware_undoable_and_a_setting(
    browser: Browser, site
) -> None:
    """FR-SYN-013: convenience symbols are on by default, do not rewrite strings, undo with
    Ctrl+Z, and are turned off in Settings (not the toolbar), which is remembered."""
    page = browser.new_page(viewport={"width": 1100, "height": 760})
    try:
        page.goto(site[1], wait_until="load")
        expect(page.locator("flt-semantics-placeholder")).to_have_count(1)
        enable_semantics(page)
        page.get_by_role("button", name=re.compile("^Pseudocode")).click()
        editor = page.get_by_role("textbox", name="Code")
        expect(editor).to_be_attached()
        expect(page.get_by_role("switch", name="Typing aids")).not_to_be_attached()

        def replace(value: str) -> None:
            for _ in range(3):  # after focus moves away and back, typed keys can be lost
                clear_editor(page, editor)
                editor.press_sequentially(value, delay=HUMAN_TYPING)
                page.wait_for_timeout(REDRAW)  # Python has this text before the next key
                if editor.input_value() == value:
                    break
            expect(editor).to_have_value(value)

        replace("x <")
        editor.press_sequentially("-", delay=HUMAN_TYPING)
        expect(editor).to_have_value("x ←")  # on by default
        page.wait_for_timeout(REDRAW)  # let Flutter settle before the undo
        page.keyboard.press("Control+z")
        expect(editor).to_have_value("x <-")

        replace("print @")
        editor.press_sequentially("pi", delay=HUMAN_TYPING)
        expect(editor).to_have_value("print π")
        page.wait_for_timeout(REDRAW)
        page.keyboard.press("Control+z")
        expect(editor).to_have_value("print @pi")

        replace('print "<')
        editor.press_sequentially("-", delay=HUMAN_TYPING)
        expect(editor).to_have_value('print "<-')  # not inside a string

        set_typing_aid(page, on=False)
        editor = page.get_by_role("textbox", name="Code")
        # A different line each time: Python only sees the field's latest value, so retyping
        # the same text quickly can reach it as no change at all.
        replace("y <")
        editor.press_sequentially("-", delay=HUMAN_TYPING)
        expect(editor).to_have_value("y <-")

        page.goto(site[1] + "#/app/pseudocode", wait_until="load")  # remembered when reopened
        enable_semantics(page)
        editor = page.get_by_role("textbox", name="Code")
        expect(editor).to_be_attached(timeout=60_000)
        page.wait_for_timeout(REDRAW)
        replace("z <")
        editor.press_sequentially("-", delay=HUMAN_TYPING)
        expect(editor).to_have_value("z <-")
    finally:
        page.close()
