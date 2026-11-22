"""Responsive Code workspace and trace controls (FR-RUN-008, FR-TRC-001 to -008)."""

import re
from collections.abc import Generator
from contextlib import contextmanager

import pytest
from playwright.sync_api import Browser, Page, expect
from tests.e2e.test_home_browser import clear_editor

from cassim.app.home import WELCOME

pytestmark = pytest.mark.e2e


@contextmanager
def code_app(browser: Browser, url: str, width: int, height: int) -> Generator[Page]:
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    try:
        page.goto(url, wait_until="load")
        placeholder = page.locator("flt-semantics-placeholder")
        expect(placeholder).to_be_attached(timeout=60_000)
        placeholder.evaluate("(element) => element.click()")
        pseudocode = page.get_by_role("button", name=re.compile("^Pseudocode"))
        expect(pseudocode).to_be_attached(timeout=45_000)
        pseudocode.click()
        expect(page.get_by_role("button", name="Pseudocode", exact=True)).to_be_attached(
            timeout=15_000
        )
        expect(page.get_by_text("Code", exact=True)).to_be_attached(timeout=15_000)
        yield page
    finally:
        if errors:
            print("\n".join(errors))
        context.close()


@pytest.mark.parametrize(
    ("width", "height"),
    [(390, 844), (768, 1024), (1024, 768), (1366, 768)],
)
@pytest.mark.parametrize("theme", ["Dark", "Light"])
def test_code_workspace_is_responsive_in_both_themes(
    browser: Browser,
    site,
    width: int,
    height: int,
    theme: str,
) -> None:
    with code_app(browser, site[1], width, height) as page:
        if theme == "Light":
            page.get_by_role("button", name=re.compile("^CASSim")).click()
            page.get_by_role("button", name="Appearance…").click()
            page.get_by_role("button", name="Light", exact=True).click()
            page.get_by_role("button", name="Apply", exact=True).click()

        expect(page.get_by_text("Code", exact=True)).to_be_attached()
        expect(page.get_by_text("Console", exact=True)).to_be_attached()
        expect(page.get_by_text("Symbols", exact=True)).to_be_attached()
        expect(page.get_by_text("Trace Table", exact=True)).to_be_attached()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        line_numbers = page.get_by_text(re.compile(r"^1\s+2\s+3"))
        expect(line_numbers).to_be_attached()
        editor = page.locator("textarea").first.bounding_box()
        gutter = line_numbers.bounding_box()
        assert editor is not None
        assert gutter is not None
        assert abs(editor["y"] - gutter["y"]) < 16

        code = page.get_by_text("Code", exact=True).bounding_box()
        trace = page.get_by_text("Trace Table", exact=True).bounding_box()
        assert code is not None
        assert trace is not None
        top_controls = [
            page.get_by_role("button", name="CASSim", exact=True).bounding_box(),
            page.get_by_role("button", name="Doc", exact=True).bounding_box(),
            page.get_by_role("button", name="Approx", exact=True).bounding_box(),
            page.get_by_role("button", name="Radian", exact=True).bounding_box(),
            page.get_by_role("button", name="Trace: Vertical", exact=True).bounding_box(),
        ]
        assert all(box is not None for box in top_controls)
        assert (
            max(box["y"] for box in top_controls if box is not None)
            - min(box["y"] for box in top_controls if box is not None)
            < 6
        )
        if width < 900:
            assert trace["y"] > code["y"]
        else:
            assert trace["x"] > code["x"]


def test_trace_controls_discover_and_toggle_constants(browser: Browser, site) -> None:
    with code_app(browser, site[1], 1100, 760) as page:
        page.get_by_role("button", name="Run", exact=True).click()

        terms = page.get_by_role("checkbox", name="terms = 10", exact=True)
        expect(terms).not_to_be_checked()
        expect(page.get_by_text("0 /", exact=False)).to_be_attached()
        terms.click()
        page.wait_for_timeout(300)
        expect(terms).to_be_checked()
        page.get_by_role("button", name="Step", exact=True).click()
        expect(page.get_by_text("1 /", exact=False)).to_be_attached()
        page.get_by_role("button", name="Last", exact=True).click()
        expect(page.get_by_text("steps", exact=False)).to_be_attached()
        page.get_by_role("button", name="First", exact=True).click()
        expect(page.get_by_text("0 /", exact=False)).to_be_attached()

        expect(page.get_by_text("Variables", exact=True)).to_be_attached()
        expect(page.get_by_text("Constants", exact=True)).to_be_attached()
        expect(page.get_by_text("Functions", exact=True)).to_be_attached()
        expect(page.get_by_text("Resize Symbols column 1", exact=True)).to_be_attached()
        expect(page.get_by_text("Resize Symbols column 2", exact=True)).to_be_attached()
        expect(page.get_by_role("textbox", name="Input or expression", exact=True)).to_be_attached()
        page.get_by_role("button", name="Trace: Vertical", exact=True).click()
        expect(page.get_by_text("Resize Code column", exact=True)).to_be_attached()
        expect(page.get_by_text("Resize Line column", exact=True)).not_to_be_attached()


def test_boxed_panes_offer_grips_and_resize(browser: Browser, site) -> None:
    with code_app(browser, site[1], 1100, 760) as page:
        for title in ("Code", "Symbols", "Trace Table"):
            expect(page.get_by_text(f"Resize {title}", exact=True)).to_be_attached()

        console_before = page.get_by_text("Console", exact=True).bounding_box()
        grip = page.get_by_text("Resize Code", exact=True).bounding_box()
        assert console_before is not None
        assert grip is not None
        page.mouse.move(grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2)
        page.mouse.down()
        page.mouse.move(
            grip["x"] + grip["width"] / 2,
            grip["y"] + grip["height"] / 2 + 60,
            steps=5,
        )
        page.mouse.up()
        page.wait_for_timeout(300)
        console_after = page.get_by_text("Console", exact=True).bounding_box()
        assert console_after is not None
        assert console_after["y"] > console_before["y"] + 40


def test_workspace_and_trace_columns_resize(browser: Browser, site) -> None:
    with code_app(browser, site[1], 1100, 760) as page:
        split = page.get_by_text("Resize columns", exact=True).bounding_box()
        trace = page.get_by_text("Trace Table", exact=True).bounding_box()
        assert split is not None
        assert trace is not None
        original_trace_x = trace["x"]
        page.mouse.move(split["x"] + 6, split["y"] + 20)
        page.mouse.down()
        page.mouse.move(split["x"] + 80, split["y"] + 20, steps=5)
        page.mouse.up()
        page.wait_for_timeout(300)
        moved_trace = page.get_by_text("Trace Table", exact=True).bounding_box()
        assert moved_trace is not None
        assert moved_trace["x"] > original_trace_x + 40

        page.get_by_role("button", name="Run", exact=True).click()
        header = page.get_by_text("Line", exact=True).bounding_box()
        assert page.get_by_text("Resize Line column", exact=True).count() == 0
        variable_grip = page.get_by_text("Resize a column", exact=True).bounding_box()
        assert header is not None
        assert header["width"] <= 45
        assert variable_grip is not None
        original_header_y = header["y"]
        page.mouse.move(header["x"] + 12, header["y"] + 140)
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(200)
        locked_header = page.get_by_text("Line", exact=True).bounding_box()
        assert locked_header is not None
        assert abs(locked_header["y"] - original_header_y) < 2
        expect(page.get_by_text("Resize a column", exact=True)).to_be_attached()


def test_settings_hold_line_numbers_and_typing_aid(browser: Browser, site) -> None:
    with code_app(browser, site[1], 1100, 760) as page:
        page.get_by_role("button", name=re.compile("^CASSim")).click()
        page.get_by_role("button", name="Settings…").click()
        expect(page.get_by_role("switch", name="Line numbers", exact=True)).to_be_checked()
        expect(page.get_by_role("switch", name="Typing aid", exact=True)).not_to_be_checked()
        expect(
            page.get_by_text("Plain names such as pi are never changed.", exact=False)
        ).to_be_attached()


def test_python_toggle_translates_and_traces(browser: Browser, site) -> None:
    with code_app(browser, site[1], 1100, 760) as page:
        page.get_by_role("button", name="Python", exact=True).click()
        editor = page.locator("textarea").first
        expect(editor).not_to_have_value(re.compile("CASSim pseudocode translation"))
        page.get_by_role("button", name=re.compile("^Run")).click()
        expect(page.get_by_text("0 /", exact=False)).to_be_attached()

        page.get_by_role("button", name="Pseudocode", exact=True).click()
        page.get_by_role("button", name=re.compile("^Run")).click()
        expect(page.get_by_text("0 /", exact=False)).to_be_attached()


ANDROID_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
)


def test_phone_opens_runs_and_traces_typed_pseudocode(browser: Browser, site) -> None:
    """FR-RUN-008, FR-PROF-014: on a touch phone Home opens Pseudocode, and code typed as an
    on-screen keyboard types it runs and traces. No request fails (fallback fonts are shipped)."""
    context = browser.new_context(
        viewport={"width": 412, "height": 839},
        device_scale_factor=2.625,
        is_mobile=True,
        has_touch=True,
        user_agent=ANDROID_UA,
    )
    page = context.new_page()
    failed: list[str] = []
    page.on("response", lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    page.on("pageerror", lambda error: failed.append(str(error)))
    try:
        page.goto(site[1], wait_until="load")
        pseudocode = page.get_by_role("button", name=re.compile("^Pseudocode"))
        placeholder = page.locator("flt-semantics-placeholder")
        expect(placeholder).to_be_attached(timeout=60_000)
        for _ in range(20):  # a mobile Flutter page enables semantics on a real tap
            if pseudocode.count():
                break
            if placeholder.count():
                placeholder.tap(force=True, timeout=5_000)
            page.wait_for_timeout(500)
        expect(page.get_by_text(WELCOME)).to_be_attached()
        pseudocode.tap()
        editor = page.locator("textarea").first
        expect(editor).to_be_attached(timeout=15_000)
        editor.tap()
        clear_editor(page, editor)  # waits until the app has seen the clear
        page.keyboard.insert_text("total ← 0\nfor k from 1 to 4\n  total ← total + k\nend for\n")
        page.keyboard.insert_text("print total")
        page.get_by_role("button", name=re.compile("^Run")).tap()
        expect(page.get_by_text("0 / 10 steps", exact=False)).to_be_attached(timeout=15_000)
        page.get_by_role("button", name="Last", exact=True).tap()
        expect(page.get_by_text("10 / 10 steps", exact=False)).to_be_attached()
        expect(page.get_by_role("checkbox", name="total", exact=True)).to_be_attached()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert failed == []
    finally:
        context.close()


def test_typing_aid_rewrites_only_while_enabled(browser: Browser, site) -> None:
    with code_app(browser, site[1], 1100, 760) as page:
        page.get_by_role("button", name=re.compile("^CASSim")).click()
        page.get_by_role("button", name="Settings…").click()
        typing_aid = page.get_by_role("switch", name="Typing aid")
        for _ in range(3):  # a click can be dropped while the dialog is still opening
            typing_aid.click()
            try:
                expect(typing_aid).to_be_checked(timeout=5_000)
                break
            except AssertionError:
                continue
        expect(typing_aid).to_be_checked()
        save = page.get_by_role("button", name="Save", exact=True)
        save.click()
        expect(save).not_to_be_attached(timeout=10_000)  # the dialog has closed and redrawn

        editor = page.locator("textarea").first
        clear_editor(page, editor)  # waits until the app has seen the clear
        editor.press_sequentially("x <-", delay=50)  # a fast human typist
        expect(editor).to_have_value("x ←")
