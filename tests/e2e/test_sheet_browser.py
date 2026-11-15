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

pytestmark = pytest.mark.e2e


def sheet_line(app: AppPage, text: str) -> None:
    app.wait(lambda: f"CASSIM: SHEET {text}" in app.logs, f"SHEET {text}")


def enter(app: AppPage, text: str) -> None:
    app.type_text(text)  # shifted symbols (`^`) go as Shift and the key, as Flutter reads them
    app.page.keyboard.press("Enter")


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
    for key in ("F4", "4", "6"):
        app.press(key)
    sheet_line(app, "A1")
    enter(app, "2")
    app.press("Up")
    app.press("Right")
    app.type_text("=")
    app.page.mouse.click(250, 112)
    app.page.wait_for_timeout(1000)
    app.type_text("+1")
    app.press("Enter")
    app.press("Up")
    app.wait(lambda: "CASSIM: SHEET B1 3" in app.logs, "B1 3", seconds=20)
    app.page.close()
