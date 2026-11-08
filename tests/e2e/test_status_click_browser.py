"""Clicking the title-bar status in the built site changes the settings (browser run).

The canvas has no DOM to read, so the effect is read from results printed by `#/debug`. The status
sits at the right of the title bar; fields are located by their order from the right edge.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Browser
from test_flows_browser import AppPage

pytestmark = pytest.mark.e2e

DOMAIN_EDGE_X = 1075  # inside the right-most field whatever its width
TITLE_Y = 63  # title bar of the Computer-mode screen at a 1100x700 viewport
REAL_X, AUTO_X, ANGLE_X = 1067, 1028, 992  # centres of REAL, AUTO and RAD in the default status


@pytest.fixture
def app(browser: Browser, site: tuple[Path, str]) -> AppPage:
    page = browser.new_page(viewport={"width": 1100, "height": 700})
    return AppPage(page, site[1])


def evaluate(app: AppPage, text: str) -> str:
    before = len(app.results)
    app.type_text(text)
    app.press("Enter")
    app.wait(lambda: len(app.results) > before, f"the result of {text!r}")
    return app.results[-1]


def click(app: AppPage, x: int) -> None:
    app.page.mouse.click(x, TITLE_Y)
    app.page.wait_for_timeout(300)
    app.page.mouse.click(600, 300)  # give the focus back to the calculator


def test_angle_click_switches_to_degrees(app: AppPage) -> None:
    assert evaluate(app, "sin(90)") != "1"  # radians
    click(app, ANGLE_X)
    assert evaluate(app, "sin(90)") == "1"


def test_calc_click_switches_to_approximate(app: AppPage) -> None:
    assert "." not in evaluate(app, "1/3")
    click(app, AUTO_X)
    assert "." in evaluate(app, "1/3")


def test_domain_click_cycles_to_polar_and_back(app: AppPage) -> None:
    assert "ⅇ^" not in evaluate(app, "3+4@i")  # Real: rectangular
    click(app, REAL_X)  # Real -> Rect
    assert "ⅇ^" not in evaluate(app, "3+4@i")
    click(app, DOMAIN_EDGE_X)  # Rect -> Polar (a wider word, so aim at the right edge)
    assert "ⅇ^" in evaluate(app, "3+4@i")
    click(app, DOMAIN_EDGE_X)  # Polar -> Real
    assert "ⅇ^" not in evaluate(app, "3+4@i")
