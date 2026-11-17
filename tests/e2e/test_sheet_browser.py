# Requirements traced here: FR-SHEET-001, FR-SHEET-002, FR-DOC-008
"""The Lists & Spreadsheet page in the built site (slice 3b), typed key by key.

The canvas has nothing to read, so with `#/debug` the app prints `CASSIM: SHEET <cell> <shown>`
whenever the cursor's cell or what it shows changes, and `CASSIM: RESULT` for the Calculator.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Browser
from tests.e2e.test_flows_browser import AppPage

from cassim.devices.nspire.pages.spreadsheet import DEFAULT_WIDTH
from cassim.devices.nspire.sheet_scene import FORMULA, HEAD, ROW, ROW_LABELS
from cassim.devices.nspire.ui.views import TITLE_H

pytestmark = pytest.mark.e2e


def sheet_line(app: AppPage, text: str) -> None:
    app.wait(lambda: f"CASSIM: SHEET {text}" in app.logs, f"SHEET {text}")


def ready(app: AppPage) -> AppPage:
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    return app


def enter(app: AppPage, text: str) -> None:
    app.type_text(text)  # shifted symbols (`^`) go as Shift and the key, as Flutter reads them
    app.page.keyboard.press("Enter")


def sheet_origin(app: AppPage) -> tuple[float, float]:
    title = app.page.get_by_role("button", name="Page Sorter 1.2")
    app.wait(lambda: title.bounding_box() is not None, "sheet title")
    box = title.bounding_box()
    assert box is not None
    return box["x"] - 6, box["y"] - 2 + TITLE_H


def cell_point(app: AppPage, column: int, row: int) -> tuple[float, float]:
    x, y = sheet_origin(app)
    return (
        x + ROW_LABELS + (column + 0.5) * DEFAULT_WIDTH,
        y + HEAD + FORMULA + (row + 0.5) * ROW,
    )


def sheet_points(app: AppPage) -> tuple[tuple[float, float], tuple[float, float]]:
    x, y = sheet_origin(app)
    return (x + 10, y + 8), cell_point(app, 2, 0)


def test_a_sheet_shares_its_column_with_the_calculator(
    browser: Browser, site: tuple[Path, str]
) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    for key in ("F4", "4", "6"):  # Doc > Insert > Lists & Spreadsheet
        app.press(key)
    sheet_line(app, "A1")
    enter(app, "2")
    enter(app, "4")
    sheet_line(app, "A3")
    app.press("Right")
    for _ in range(3):
        app.press("Up")  # B3 to B1 to the formula row
    enter(app, "=a[]^2")
    sheet_line(app, "B1 4")
    app.press("Down")
    sheet_line(app, "B2 16")
    # name column A `xs`, then store to it from the Calculator page
    app.press("Left")
    for _ in range(3):
        app.press("Up")  # A2 to A1, the formula row, the name row
    enter(app, "xs")
    app.page.keyboard.press("Alt+ArrowLeft")
    before = len(app.results)
    app.type_text("xs[1]:=10")
    app.page.keyboard.press("Enter")
    app.wait(lambda: len(app.results) > before, "the store")
    assert app.results[-1] == "10"
    app.page.keyboard.press("Alt+ArrowRight")
    app.press("Down")  # the formula row to A1
    sheet_line(app, "A1 10")
    app.press("Right")
    sheet_line(app, "B1 100")


def test_pointing_to_a_range_while_entering_a_formula(
    browser: Browser, site: tuple[Path, str]
) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    for key in ("F4", "4", "6"):
        app.press(key)
    sheet_line(app, "A1")
    enter(app, "2")
    enter(app, "3")
    app.press("Up")
    app.press("Up")
    app.press("Right")
    app.type_text("=sum(")
    app.press("Left")
    app.page.keyboard.press("Shift+ArrowDown")
    app.type_text(")")
    app.press("Enter")
    app.press("Up")
    app.wait(lambda: "CASSIM: SHEET B1 5" in app.logs, "B1 5")
    app.page.close()


def test_shift_arrow_does_not_move_a_formula_into_another_cell(
    browser: Browser, site: tuple[Path, str]
) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    for key in ("F4", "4", "6"):
        app.press(key)
    enter(app, "9")
    app.press("Up")
    app.press("Right")
    app.type_text("=2")
    app.page.keyboard.press("Shift+ArrowLeft")
    app.press("Enter")
    app.press("Up")
    app.wait(lambda: "CASSIM: SHEET B1 2" in app.logs, "B1 2")
    app.press("Left")
    app.wait(lambda: "CASSIM: SHEET A1 9" in app.logs, "A1 9")
    app.page.close()


def test_clicking_a_cell_in_a_formula(browser: Browser, site: tuple[Path, str]) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    for key in ("F4", "4", "6"):
        app.press(key)
    sheet_line(app, "A1")
    enter(app, "2")
    app.press("Up")
    app.press("Right")
    app.type_text("=")
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    app.page.mouse.click(*cell_point(app, 0, 0))
    app.page.wait_for_timeout(1000)
    app.type_text("+1")
    app.press("Enter")
    app.press("Up")
    app.wait(lambda: "CASSIM: SHEET B1 3" in app.logs, "B1 3", seconds=20)
    app.page.close()


def test_right_click_context_menus(browser: Browser, site: tuple[Path, str]) -> None:
    app = ready(AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), site[1]))
    for key in ("F4", "4", "6"):
        app.press(key)
    sheet_line(app, "A1")
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    app.page.evaluate("""() => {
      window.contextResults = [];
      window.addEventListener("contextmenu", e => {
        setTimeout(() => window.contextResults.push({
          prevented: e.defaultPrevented, trusted: e.isTrusted
        }), 0);
      }, true);
    }""")

    def right_click(x: float, y: float, *, ctrl: bool = False) -> bool:
        before = app.page.evaluate("window.contextResults.length")
        if ctrl:
            app.page.keyboard.down("Control")
        app.page.mouse.click(x, y, button="right")
        if ctrl:
            app.page.keyboard.up("Control")
        app.page.wait_for_function("n => window.contextResults.length > n", arg=before)
        result = app.page.evaluate("n => window.contextResults[n]", before)
        assert result["trusted"]
        return result["prevented"]

    corner, c1 = sheet_points(app)
    assert not right_click(*corner)  # the grid's top-left corner has no cell
    assert not right_click(*c1, ctrl=True)
    before = app.page.evaluate("window.contextResults.length")
    app.page.keyboard.down("Control")
    app.page.mouse.down(button="right")
    app.page.keyboard.up("Control")
    app.page.mouse.up(button="right")
    app.page.wait_for_function("n => window.contextResults.length > n", arg=before)
    assert not app.page.evaluate("n => window.contextResults[n].prevented", before)
    enter(app, "7")  # Ctrl+right-click neither selected C1 nor opened its menu
    app.press("Up")
    sheet_line(app, "A1 7")
    assert right_click(*c1)
    sheet_line(app, "C1")
    app.press("4")  # Insert Cell from the CASSim menu, not a digit in C1
    enter(app, "9")
    app.press("Up")
    sheet_line(app, "C1 9")

    before = len(app.logs)
    app.page.keyboard.press("Alt+ArrowLeft")
    app.wait(lambda: any("CASSIM: PAGE 1.1 " in s for s in app.logs[before:]), "calculator page")
    app.page.wait_for_function(
        "() => getComputedStyle(document.querySelector('flutter-view')).cursor !== 'context-menu'"
    )
    assert not right_click(*c1)
    before = len(app.logs)
    app.page.keyboard.press("Alt+ArrowRight")
    app.wait(lambda: any("CASSIM: PAGE 1.2 " in s for s in app.logs[before:]), "sheet page")
    app.page.wait_for_function(
        "() => getComputedStyle(document.querySelector('flutter-view')).cursor === 'context-menu'"
    )
    assert right_click(*cell_point(app, 2, 0))
    app.press("Escape")
    app.page.set_viewport_size({"width": 1200, "height": 760})
    app.page.wait_for_timeout(500)
    assert not right_click(*cell_point(app, 2, 0), ctrl=True)
    assert right_click(*cell_point(app, 2, 0))
    app.page.close()


def test_long_press_still_opens_the_cell_menu(browser: Browser, site: tuple[Path, str]) -> None:
    _, url = site
    context = browser.new_context(viewport={"width": 1100, "height": 700}, has_touch=True)
    app = AppPage(context.new_page(), url)
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    for key in ("F4", "4", "6"):
        app.press(key)
    sheet_line(app, "A1")
    app.press("Right")
    app.press("Right")
    enter(app, "9")
    app.press("Up")
    sheet_line(app, "C1 9")
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    x, y = cell_point(app, 2, 0)
    session = context.new_cdp_session(app.page)
    session.send(
        "Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}
    )
    app.page.wait_for_timeout(800)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    ready_count = app.logs.count("CASSIM: ENGINE READY")
    app.page.get_by_role("button", name="4 Insert Cell").click()
    app.wait(lambda: app.logs.count("CASSIM: ENGINE READY") > ready_count, "insert cell")
    app.press("Down")
    sheet_line(app, "C2 9")
    context.close()
