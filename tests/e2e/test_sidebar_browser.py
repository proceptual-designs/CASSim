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
    actions = [
        button(page, name).bounding_box()
        for name in ("Move page earlier", "Move page later", "Undo page change", "Redo page change")
    ]
    assert all(box is not None for box in actions)
    boxes = [box for box in actions if box is not None]
    assert max(box["y"] for box in boxes) - min(box["y"] for box in boxes) < 1
    assert all(a["x"] + a["width"] <= b["x"] for a, b in pairwise(boxes))
    assert boxes[-1]["x"] + boxes[-1]["width"] <= page_box["x"] + page_box["width"]


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
    for key in ("F2", "8", "1"):  # Menu > Finance > Finance Solver
        app.press(key)
    for label, value in (("N", "12"), ("I (%)", "6"), ("PV", "10000")):
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_label("Pmt", exact=True).press("Enter")
    button(page, "OK").click()
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
    button(page, "Collapse tvm variables").click()
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
