# Requirements traced here: FR-CALC-004, FR-SHEET-001
"""Held arrow keys repeat in the Calculator and spreadsheet."""

import re
from pathlib import Path

import pytest
from playwright.sync_api import Browser, expect
from tests.e2e.test_flows_browser import AppPage

pytestmark = pytest.mark.e2e

ENTRY = "123456789" * 2


def _repeated_results(entry: str) -> set[str]:
    return {
        *(str(int(entry[:-moves]) - int(entry[-moves:])) for moves in range(2, len(entry))),
        str(-int(entry)),
    }


REPEATED_RESULTS = _repeated_results(ENTRY)


def _hold(app: AppPage, key: str) -> None:
    app.page.keyboard.down(key)
    app.page.wait_for_timeout(2500)
    app.page.keyboard.up(key)
    app.page.wait_for_timeout(500)


def test_arrow_repeat_moves_calculator_caret_and_sheet_cursor(
    browser: Browser, site: tuple[Path, str]
) -> None:
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), site[1])
    app.page.evaluate("""() => {
      window.cassimKeyEvents = [];
      for (const type of ["keydown", "keyup"]) {
        document.addEventListener(type, event => {
          if (event.code.startsWith("Arrow")) {
            window.cassimKeyEvents.push({
              type, code: event.code, repeat: event.repeat, target: event.target.tagName
            });
          }
        }, true);
      }
    }""")
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    app.type_text(ENTRY)
    app.page.wait_for_timeout(1000)
    _hold(app, "ArrowLeft")
    app.type_text("-")
    app.press("Enter")
    app.wait(lambda: bool(app.results), "calculator result")
    assert app.results[-1] in REPEATED_RESULTS, app.logs

    for key in ("F4", "4", "6"):
        app.press(key)
    app.wait(lambda: "CASSIM: SHEET A1" in app.logs, "sheet A1")
    _hold(app, "ArrowDown")
    app.wait(
        lambda: any(
            (match := re.fullmatch(r"CASSIM: SHEET A(\d+)", line)) and int(match.group(1)) >= 3
            for line in app.logs
        ),
        "at least two sheet movements",
    )
    sheet_rows = [
        int(match.group(1))
        for line in app.logs
        if (match := re.fullmatch(r"CASSIM: SHEET A(\d+)", line))
    ]
    row = sheet_rows[-1]
    app.type_text("=" + ENTRY)
    app.page.wait_for_timeout(1000)
    _hold(app, "ArrowLeft")
    app.type_text("-")
    app.press("Enter")
    app.press("Up")
    app.wait(
        lambda: any(f"CASSIM: SHEET A{row} {result}" in app.logs for result in REPEATED_RESULTS),
        "sheet formula result " + str(app.page.evaluate("window.cassimKeyEvents")),
    )
    app.page.close()


def test_held_on_screen_arrow_repeats_and_stops(browser: Browser, site: tuple[Path, str]) -> None:
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), site[1])
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    app.page.get_by_role("button", name="Handheld", exact=True).click()
    left = app.page.get_by_role("button", name=re.compile(r"◀$"))
    expect(left).to_be_attached()
    entry = "123456789"
    app.type_text(entry)
    app.page.wait_for_timeout(1000)
    box = left.bounding_box()
    assert box is not None
    app.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    app.page.mouse.down()
    app.page.wait_for_timeout(2000)
    app.page.mouse.up()
    app.page.wait_for_timeout(400)
    app.type_text("-")
    app.press("Enter")
    app.wait(lambda: bool(app.results), "calculator result")
    assert app.results[-1] in _repeated_results(entry), app.results
    app.page.close()
