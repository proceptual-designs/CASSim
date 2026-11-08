"""The exam-style flows typed into the built site, key by key (M2 exit criterion).

Plays the flows marked `browser: true` in `corpus/flows/exam.yaml` (the headless run is
`tests/flows/test_exam_flows.py`). Results are read from the console: with `#/debug` the app
prints `CASSIM: RESULT <text>` after each calculation, since the canvas has nothing to read.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page
from tools.flows import (
    RIGHT,
    SHIFTED,
    flow_settings,
    load_flows,
    matches,
    parse_keys,
    playwright_key,
    split_text,
)

pytestmark = pytest.mark.e2e

FLOWS = [flow for flow in load_flows() if flow.get("browser")]


class AppPage:
    """A page with the app running, and the results it has printed so far."""

    def __init__(self, page: Page, url: str) -> None:
        self.page = page
        self.logs: list[str] = []
        page.on(
            "console", lambda m: self.logs.append(m.text) if m.text.startswith("CASSIM:") else None
        )
        page.goto(url + "#/debug", wait_until="load")
        self.wait(lambda: any("READY" in line for line in self.logs), "READY")
        page.mouse.click(600, 150)  # focus the calculator

    @property
    def results(self) -> list[str]:
        return [line.removeprefix("CASSIM: RESULT ") for line in self.logs if "RESULT" in line]

    def wait(self, done, what: str, seconds: float = 150) -> None:
        end = time.monotonic() + seconds
        while not done() and time.monotonic() < end:
            self.page.wait_for_timeout(100)
        assert done(), f"timed out waiting for {what}: {self.logs}"

    def type_text(self, text: str) -> None:
        for piece in split_text(text):
            if piece == RIGHT:
                self.page.keyboard.press("ArrowRight")
            elif piece in SHIFTED:  # Flutter reports the key, so shifted symbols go with Shift
                self.page.keyboard.press("Shift+" + SHIFTED[piece])
            else:
                self.page.keyboard.type(piece)
            self.page.wait_for_timeout(25)

    def press(self, spec: str) -> None:
        for key, mods in parse_keys(spec):
            self.page.keyboard.press(playwright_key(key, mods))
            self.page.wait_for_timeout(60)


@pytest.mark.parametrize("flow", FLOWS, ids=[f["id"] for f in FLOWS])
def test_flow_in_the_browser(browser: Browser, site: tuple[Path, str], flow: dict) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    settings = flow_settings(flow)
    for step in flow["steps"]:
        label = step.get("type") or step.get("keys", "")
        before = len(app.results)
        evaluates = False
        if "type" in step:
            app.type_text(step["type"])
            if step.get("enter", True):
                app.press("ctrl+Enter" if step.get("approx") else "Enter")
                evaluates = True
        if "keys" in step:
            app.press(step["keys"])
            evaluates = evaluates or "expect" in step
        if evaluates:
            app.wait(lambda n=before: len(app.results) > n, f"the result of {label!r}")
        if "expect" in step:
            got = app.results[-1]
            assert matches(
                str(step["expect"]),
                got,
                settings,
                step.get("compare", "canonical"),
                step.get("tol", 1.0e-7),
            ), f"{label}: got {got}, expected {step['expect']}"
    app.page.close()
