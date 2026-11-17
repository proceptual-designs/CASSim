# Requirements traced here: FR-DOC-001, FR-DOC-008
"""Exercise the Computer sidebar in the built app, including its rendered layout."""

import re
from itertools import pairwise
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Locator, Page, expect
from tests.e2e.test_flows_browser import AppPage

from cassim.devices.nspire.ui.sidebar import LIST_BATCH

pytestmark = pytest.mark.e2e


def open_app(browser: Browser, site: tuple[Path, str]) -> AppPage:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    expect(app.page.get_by_role("button", name="Hide pages Pages")).to_be_attached()
    return app


def button(page: Page, name: str) -> Locator:
    return page.get_by_role("button", name=name, exact=True)


def test_mode_segment_switches_to_handheld(browser: Browser, site: tuple[Path, str]) -> None:
    """FR-DEV-002, FR-DEV-004: the mode selector switches to the Handheld view."""
    app = open_app(browser, site)
    page = app.page
    button(page, "Handheld").click()
    expect(button(page, "Hide pages Pages")).not_to_be_attached()
    expect(page.get_by_role("button", name=re.compile(r"enter$"))).to_be_attached()
    page.close()


def test_computer_controls_align_at_minimum_sidebar_width(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-DEV-002: aligned controls remain visible and usable in the minimum-width sidebar."""
    app = open_app(browser, site)
    page = app.page
    names = ("CASSim", "Doc", "Settings", "Menu", "Page manager", "+ Page", "+ Problem")
    boxes = {}
    for name in names:
        locator = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}(?:\s|$)"))
        box = locator.bounding_box()
        assert box, f"{name} is not visible"
        boxes[name] = box
    for row in (("CASSim", "Doc", "Settings"), ("Page manager", "+ Page", "+ Problem")):
        assert max(boxes[name]["y"] for name in row) - min(boxes[name]["y"] for name in row) < 2
        assert all(
            boxes[left]["x"] + boxes[left]["width"] <= boxes[right]["x"]
            for left, right in pairwise(row)
        )
    assert boxes["Settings"]["y"] < boxes["Menu"]["y"] < boxes["Page manager"]["y"]
    expect(button(page, "delete page")).not_to_be_attached()
    button(page, "Page manager").click()
    expect(page.get_by_role("button", name=re.compile("Close the sorter"))).to_be_attached()
    page.close()


def test_computer_divider_resizes_and_grip_swaps_columns(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-DEV-002: the divider resizes and its top grip moves a column."""
    app = open_app(browser, site)
    page = app.page
    heading = button(page, "Hide pages Pages")
    initial = heading.bounding_box()
    mode = button(page, "Handheld").bounding_box()
    last = button(page, "+ Problem").bounding_box()
    assert initial
    assert mode
    assert last
    divider_x = last["x"] + last["width"] + 4
    page.mouse.move(divider_x + 12, initial["y"] + 20)
    page.mouse.down()
    page.mouse.move(divider_x + 52, initial["y"] + 20, steps=10)
    page.mouse.up()
    app.wait(
        lambda: (
            (box := heading.bounding_box()) is not None and box["width"] > initial["width"] + 20
        ),
        "sidebar to widen",
    )
    resized = heading.bounding_box()
    assert resized
    grip_x = divider_x + 40 + 6
    grip_y = mode["y"] + 8
    page.mouse.move(grip_x, grip_y)
    page.mouse.down()
    page.mouse.move(grip_x + 40, grip_y, steps=10)
    page.wait_for_timeout(500)
    page.mouse.move(grip_x + 220, grip_y + 100, steps=15)
    page.wait_for_timeout(500)
    page.mouse.up()
    app.wait(
        lambda: (box := heading.bounding_box()) is not None and box["x"] > resized["x"] + 100,
        "columns to swap",
    )
    page.close()


def test_column_controls_can_be_enabled_from_system_settings(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """NFR-USE-002: the optional column controls are exposed through System Settings."""
    app = open_app(browser, site)
    page = app.page
    for key in ("F4", "7", "3"):
        app.press(key)
    checkbox = page.get_by_role("checkbox", name="Show keyboard-accessible column controls")
    checkbox.focus()
    page.keyboard.press("Space")
    expect(checkbox).to_be_checked()
    button(page, "OK").focus()
    page.keyboard.press("Enter")
    move = page.get_by_role("button", name=re.compile(r"^Move calculation left")).last
    expect(move).to_be_attached()
    before = button(page, "Hide pages Pages").bounding_box()
    assert before
    resize = page.get_by_role("button", name=re.compile(r"^Widen the column on the left")).last
    resize.focus()
    page.keyboard.press("Enter")
    app.wait(
        lambda: (
            (box := button(page, "Hide pages Pages").bounding_box()) is not None
            and box["width"] > before["width"] + 10
        ),
        "keyboard column resize",
        seconds=8,
    )
    move.focus()
    page.keyboard.press("Enter")
    app.wait(
        lambda: (
            (box := button(page, "Hide pages Pages").bounding_box()) is not None
            and box["x"] > before["x"] + 100
        ),
        "keyboard column swap",
        seconds=8,
    )
    page.close()


def page_button(page: Page, number: str, name: str) -> Locator:
    return page.get_by_role("button", name=re.compile(rf"^{re.escape(number)}\s+{name}"))


def check_page_layout(page: Page, first: Locator, pages: Locator) -> None:
    heading = button(page, "Hide pages Pages").bounding_box()
    page_box = pages.bounding_box()
    fold = button(page, "Collapse Problem 1").bounding_box()
    title = first.bounding_box()
    assert heading, "Pages heading not rendered"
    assert page_box, "Page list not rendered"
    assert fold, "Problem fold button not rendered"
    assert title, "First page not rendered"
    assert abs(page_box["width"] - heading["width"]) < 1
    assert title["width"] > page_box["width"] * 0.7
    assert abs(title["x"] + title["width"] - fold["x"]) <= 3
    assert abs(fold["x"] + fold["width"] - page_box["x"] - page_box["width"]) < 1
    assert not button(page, "Move page earlier").count()
    assert not button(page, "Move page later").count()


def check_variable_layout(page: Page, variables: Locator) -> None:
    box = variables.bounding_box()
    expand = button(page, "Expand stat.values")
    expand.scroll_into_view_if_needed()
    label = expand.locator("xpath=preceding-sibling::*[1]").bounding_box()
    control = expand.bounding_box()
    assert box
    assert label
    assert control
    assert label["width"] > box["width"] * 0.7
    assert label["x"] + label["width"] <= control["x"]
    assert abs(control["x"] + control["width"] - box["x"] - box["width"]) < 1


def test_pages_and_problems_render_fold_and_scroll(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-DOC-001: all offered types are visible, laid out, scrollable and foldable."""
    app = open_app(browser, site)
    page = app.page
    for number, (key, name) in enumerate(
        [
            ("2", "Graphs"),
            ("4", "Lists & Spreadsheet"),
            ("5", "Data & Statistics"),
            ("6", "Notes"),
            ("9", "Program Editor"),
            ("a", "Python"),
        ],
        2,
    ):
        app.press("ctrl+i")
        app.press(key)
        expect(page_button(page, f"1.{number}", name)).to_be_attached()
    app.press("ctrl+alt+i")
    app.press("1")
    expect(page_button(page, "2.1", "Calculator")).to_be_attached()
    for number in range(2, 9):
        app.press("ctrl+i")
        app.press("1")
        expect(page_button(page, f"2.{number}", "Calculator")).to_be_attached()

    first = page_button(page, "1.1", "Calculator")
    pages = first.locator("..")
    check_page_layout(page, first, pages)
    page_box = pages.bounding_box()
    assert page_box
    page.mouse.move(page_box["x"] + 20, page_box["y"] + page_box["height"] - 10)
    page.mouse.wheel(0, 450)
    app.wait(lambda: pages.evaluate("(element) => element.scrollTop") > 0, "pages to scroll")
    scrolled = first.bounding_box()
    assert scrolled
    assert scrolled["y"] < page_box["y"]
    page.mouse.wheel(0, -450)
    app.wait(lambda: pages.evaluate("(element) => element.scrollTop") == 0, "pages to scroll back")
    button(page, "Collapse Problem 1").click()
    expect(page_button(page, "1.2", "Graphs")).not_to_be_attached()
    button(page, "Collapse Problem 2").click()
    expect(page_button(page, "2.2", "Calculator")).not_to_be_attached()
    button(page, "Expand Problem 1").click()
    expect(page_button(page, "1.7", "Python")).to_be_attached()
    button(page, "Hide pages Pages").click()
    expect(page_button(page, "1.1", "Calculator")).not_to_be_attached()
    expect(button(page, "Move page earlier")).not_to_be_attached()
    button(page, "Show pages Pages").click()
    expect(page_button(page, "1.7", "Python")).to_be_attached()
    expect(button(page, "Expand Problem 2")).to_be_attached()
    page.close()


def solve_finance(app: AppPage) -> None:
    page = app.page
    for key in ("F2", "8", "1"):  # Menu > Finance > Finance Solver
        app.press(key)
    for label, value in (("N", "12"), ("I (%)", "6"), ("PV", "10000")):
        page.get_by_label(label, exact=True).fill(value)
    payment = page.get_by_label("Pmt", exact=True)
    payment.click()
    page.wait_for_timeout(500)
    payment.press("Enter")
    page.wait_for_timeout(1000)
    button(page, "OK").click()


def test_variables_stats_and_finance_render_fold_and_scroll(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-DOC-008: actual engine results are visible and folding does not destroy them."""
    app = open_app(browser, site)
    page = app.page
    for expression in ("xs:={1,2,3}", "TwoVar xs,{2,4,6}"):
        before = len(app.results)
        app.type_text(expression)
        app.press("Enter")
        app.wait(lambda n=before: len(app.results) > n, expression)
    solve_finance(app)
    expect(button(page, "Collapse tvm variables")).to_be_attached()

    variables = page.get_by_role(
        "button", name=re.compile(r"^(Collapse|Expand) stat variables$")
    ).locator("..")
    box = variables.bounding_box()
    assert box
    page.mouse.move(box["x"] + 20, box["y"] + box["height"] - 10)
    page.mouse.wheel(0, 500)
    app.wait(
        lambda: variables.evaluate("(element) => element.scrollTop") > 0, "variables to scroll"
    )
    assert "tvm.pv = 10000" in variables.inner_text()
    assert "tvm.pmt = -" in variables.inner_text()
    button(page, "Expand stat.results").click()
    app.wait(
        lambda: '1: ["Title","Two-Variable Statistics"]' in variables.inner_text(), "stat rows"
    )
    check_variable_layout(page, variables)
    button(page, "Expand stat.values").click()
    app.wait(lambda: '1: "Two-Variable Statistics"' in variables.inner_text(), "stat values")
    button(page, "Collapse stat variables").click()
    expect(button(page, "Expand stat.values")).not_to_be_attached()
    expect(button(page, "Expand stat variables")).to_be_attached()
    tvm = button(page, "Collapse tvm variables")
    tvm.scroll_into_view_if_needed()
    tvm.click()
    expect(button(page, "Expand tvm variables")).to_be_attached()
    assert "tvm.pv = 10000" not in variables.inner_text()
    button(page, "Expand xs").click()
    app.wait(lambda: "1: 1" in variables.inner_text(), "expanded list")
    button(page, "Collapse xs").click()
    expect(button(page, "Expand xs")).to_be_attached()
    button(page, "Hide variables Variables").click()
    expect(button(page, "Show variables Variables")).to_be_attached()
    expect(button(page, "Expand tvm variables")).not_to_be_attached()
    button(page, "Show variables Variables").click()
    button(page, "Expand stat variables").click()
    expect(button(page, "Collapse stat.results")).to_be_attached()
    expect(button(page, "Collapse stat.values")).to_be_attached()
    button(page, "Expand tvm variables").click()
    app.wait(lambda: "tvm.pv = 10000" in variables.inner_text(), "expanded finance variables")
    page.close()


def test_long_variable_list_batches_and_scrolls(browser: Browser, site: tuple[Path, str]) -> None:
    """FR-DOC-008: a long variable list can be expanded and navigated in batches."""
    app = open_app(browser, site)
    page = app.page
    app.type_text(f"xs:=seq(x,x,1,{LIST_BATCH + 2})")
    app.press("Enter")
    app.wait(lambda: bool(app.results), "long list result")
    button(page, "Expand xs").click()
    variables = button(page, "Collapse xs").locator("..")
    app.wait(lambda: f"{LIST_BATCH}: {LIST_BATCH}" in variables.inner_text(), "first batch")
    assert f"{LIST_BATCH + 1}: {LIST_BATCH + 1}" not in variables.inner_text()
    box = variables.bounding_box()
    assert box
    page.mouse.move(box["x"] + 20, box["y"] + box["height"] - 10)
    page.mouse.wheel(0, 1500)
    app.wait(
        lambda: variables.evaluate("(element) => element.scrollTop") > 0,
        "list to scroll",
        seconds=10,
    )
    more = button(page, "Show more (2)")
    more.scroll_into_view_if_needed()
    more.click()
    app.wait(lambda: f"{LIST_BATCH + 2}: {LIST_BATCH + 2}" in variables.inner_text(), "last item")
    expect(more).not_to_be_attached()
    button(page, "Collapse xs").click()
    expect(button(page, "Expand xs")).to_be_attached()
    collapsed = button(page, "Expand xs").locator("..")
    assert f"{LIST_BATCH + 2}: {LIST_BATCH + 2}" not in collapsed.inner_text()
    button(page, "Expand xs").click()
    expect(button(page, "Show more (2)")).to_be_attached()


def test_keypad_palette_switching_and_cycling_in_browser(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-DEV-007: on-screen key presses switch palettes and select the next symbol."""
    app = open_app(browser, site)
    page = app.page
    button(page, "Keypad").click()
    button(page, "π▸").click()
    symbol = page.get_by_role("button", name="ⅈ ⅈ")
    expect(symbol).to_be_attached()
    button(page, "trig").click()
    expect(symbol).not_to_be_attached()
    button(page, "π▸").click()
    expect(symbol).to_be_attached()
    button(page, "π▸").click()
    enter = page.get_by_role("button", name=re.compile(r"enter$"))
    enter.click()
    expect(symbol).not_to_be_attached()
    enter.click()
    app.wait(lambda: bool(app.results), "selected symbol result", seconds=30)
    assert app.results[-1] == "ⅈ"
    page.close()
