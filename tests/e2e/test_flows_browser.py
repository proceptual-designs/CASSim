"""The exam-style flows typed into the built site, key by key (M2 exit criterion).

Plays the flows marked `browser: true` in `corpus/flows` (the headless run is
`tests/flows/test_exam_flows.py`). Results are read from the console: with `#/debug` the app
prints result and selected-sheet-cell lines, since the canvas has nothing to read.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, expect
from tools.flows import (
    RIGHT,
    SHIFTED,
    flow_settings,
    load_flows,
    matches,
    parse_keys,
    playwright_key,
    sheet_matches,
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
        self.wait(lambda: "CASSIM: READY" in self.logs, "READY")  # not ENGINE READY
        page.mouse.click(600, 150)  # focus the calculator

    @property
    def results(self) -> list[str]:
        return [line.removeprefix("CASSIM: RESULT ") for line in self.logs if "RESULT" in line]

    def wait(self, done, what: str, seconds: float = 150) -> None:
        end = time.monotonic() + seconds
        while not done() and time.monotonic() < end:
            self.page.wait_for_timeout(100)
        assert done(), f"timed out waiting for {what}: {self.logs}"

    def until(self, act, done, what: str, *, tries: int = 3, seconds: float = 30) -> None:
        """Do `act` until `done` shows the app received it, at most `tries` times.

        On a loaded machine Flutter web can drop typed input: a key or a filled field never
        reaches Python, and a user would simply type it again. `done` must check something
        the app draws or logs, never the browser's own text box."""
        for _ in range(tries - 1):
            act()
            end = time.monotonic() + seconds
            while not done() and time.monotonic() < end:
                self.page.wait_for_timeout(100)
            if done():
                return
        act()
        self.wait(done, what, seconds)

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


def run_flow(app: AppPage, flow: dict) -> None:
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    current_page = next(
        line.removeprefix("CASSIM: PAGE ").split()[0]
        for line in reversed(app.logs)
        if line.startswith("CASSIM: PAGE ")
    )
    problem = current_page.partition(".")[0]
    if any("plot_x" in step for step in flow["steps"]):
        app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
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
            ), f"{flow['id']} / {label}: got {got}, expected {step['expect']}"
        if "page" in step:
            wanted_page = f"{problem}.{str(step['page']).partition('.')[2]}"
            app.wait(
                lambda expected=wanted_page: (
                    next(
                        (
                            line.removeprefix("CASSIM: PAGE ").split()[0]
                            for line in reversed(app.logs)
                            if line.startswith("CASSIM: PAGE ")
                        ),
                        "",
                    )
                    == expected
                ),
                f"PAGE {wanted_page}",
            )
        if "sheet" in step:
            wanted = step["sheet"]
            app.wait(
                lambda expected=wanted: sheet_matches(
                    expected,
                    next(
                        (
                            line.removeprefix("CASSIM: SHEET ")
                            for line in reversed(app.logs)
                            if line.startswith("CASSIM: SHEET ")
                        ),
                        "",
                    ),
                    settings,
                ),
                f"SHEET {wanted}",
            )
        if "plot_x" in step:
            expect(app.page.get_by_role("button", name=step["plot_x"], exact=True)).to_be_visible(
                timeout=30000
            )


def test_flows_in_the_browser(browser: Browser, site: tuple[Path, str]) -> None:
    _, url = site
    app = AppPage(browser.new_page(viewport={"width": 1100, "height": 700}), url)
    for index, flow in enumerate(FLOWS):
        if index:
            before = sum(line.startswith("CASSIM: PAGE ") for line in app.logs)
            app.press("ctrl+alt+i")
            app.press("1")
            app.wait(
                lambda n=before: sum(line.startswith("CASSIM: PAGE ") for line in app.logs) > n,
                "the new Problem's Calculator page",
            )
        run_flow(app, flow)
    app.page.close()
