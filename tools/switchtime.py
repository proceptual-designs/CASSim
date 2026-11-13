"""Measure how long a page switch takes in the published site (NFR-PERF-006).

    python -m tools.switchtime [--dist DIR] [--build] [--switches 20] [--entries 15] [--slow 4]

Opens the site in Chromium with `#/debug`, fills two Calculator pages with entries (a third stays
empty), then moves between the pages with alt+arrow and times each move from the key press to the
app's `CASSIM: PAGE p.q` line, which it prints once the new page has been sent to Flutter. The aim
is 100 ms on a desktop and 250 ms on a mid-range phone (decision 0031); nothing fails above it.

`--slow N` applies Chromium's CPU throttle as a rough stand-in for a phone. Whether it also slows
the Python worker is not known (spike A), so a real phone run is still needed.

Pages other than Calculator join the cycle as they are built (Lists & Spreadsheet in 3b, Graphs
in 4b).
"""

from __future__ import annotations

import argparse
import functools
import http.server
import statistics
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import ConsoleMessage, Page, sync_playwright

from tools import publish
from tools.loadtime import BASE, _Handler, launch

READY = "CASSIM: READY"


class Console:
    def __init__(self, page: Page) -> None:
        self.lines: list[tuple[float, str]] = []
        page.on("console", self._on)

    def _on(self, message: ConsoleMessage) -> None:
        if message.text.startswith("CASSIM:"):
            self.lines.append((time.perf_counter(), message.text))

    def wait(self, page: Page, done: Callable[[], bool], what: str, seconds: float = 180) -> None:
        end = time.perf_counter() + seconds
        while not done() and time.perf_counter() < end:
            page.wait_for_timeout(20)
        if not done():
            raise SystemExit(f"timed out waiting for {what}")

    def count(self, text: str) -> int:
        return sum(text in line for _, line in self.lines)


def enter(page: Page, console: Console, text: str) -> None:
    before = console.count("CASSIM: RESULT")
    page.keyboard.type(text, delay=10)
    page.keyboard.press("Enter")
    console.wait(page, lambda: console.count("CASSIM: RESULT") > before, f"the result of {text}")


def fill(page: Page, console: Console, entries: int, offset: int) -> None:
    for i in range(entries):
        enter(page, console, f"expand((x+{i + offset})^3)")


type Times = dict[str, list[tuple[float, float, float]]]  # page: (total, build, send) in ms


def switch(page: Page, console: Console, key: str) -> tuple[str, float, float, float]:
    """Press `key`; return the page it reached, the seconds until its PAGE line, and the app's own
    split of that time in ms: making the controls (`build=`) and `page.update` (`send=`)."""
    before = len(console.lines)
    start = time.perf_counter()
    page.keyboard.press(key)

    def arrived() -> bool:
        return any("CASSIM: PAGE" in line for _, line in console.lines[before:])

    console.wait(page, arrived, f"the page after {key}")
    when, line = next((t, x) for t, x in console.lines[before:] if "CASSIM: PAGE" in x)
    name, *parts = line.removeprefix("CASSIM: PAGE ").split()
    split = dict(part.split("=") for part in parts)
    return name, when - start, float(split["build"]), float(split["send"])


def measure(url: str, *, switches: int, entries: int, slow: float) -> Times:
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_context(viewport={"width": 1100, "height": 700}).new_page()
        console = Console(page)
        page.goto(url + "#/debug", wait_until="load")
        console.wait(page, lambda: console.count(READY) > 0, "the app")
        console.wait(page, lambda: console.count("ENGINE READY") > 0, "the engine")
        page.mouse.click(600, 150)  # focus the calculator
        fill(page, console, entries, 0)
        page.keyboard.press("Control+i")  # a second Calculator page
        fill(page, console, entries, 100)
        page.keyboard.press("Control+i")  # a third, left empty
        page.wait_for_timeout(500)
        if slow != 1.0:
            cdp = page.context.new_cdp_session(page)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": slow})
        times: Times = defaultdict(list)
        keys = ["Alt+ArrowLeft", "Alt+ArrowLeft", "Alt+ArrowRight", "Alt+ArrowRight"]
        for n in range(switches):
            reached, seconds, build, send = switch(page, console, keys[n % len(keys)])
            times[reached].append((seconds * 1000, build, send))
            page.wait_for_timeout(200)
        browser.close()
    return times


def report(times: Times) -> str:
    """Median and max of the whole switch, and medians of the app's build and send parts."""
    head = f"{'to page':<10}{'switches':>9}{'median ms':>11}{'max ms':>9}{'build':>8}{'send':>8}"
    rows = {name: times[name] for name in sorted(times)}
    rows["all"] = [value for values in times.values() for value in values]
    lines = [head]
    for name, values in rows.items():
        total = [value[0] for value in values]
        lines.append(
            f"{name:<10}{len(values):>9}{statistics.median(total):>11.0f}{max(total):>9.0f}"
            f"{statistics.median(value[1] for value in values):>8.0f}"
            f"{statistics.median(value[2] for value in values):>8.0f}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--dist", type=Path, default=publish.DEFAULT_DIST)
    parser.add_argument("--build", action="store_true", help="run tools.publish first")
    parser.add_argument("--switches", type=int, default=20)
    parser.add_argument("--entries", type=int, default=15, help="entries on each full page")
    parser.add_argument("--slow", type=float, default=1.0, help="CPU throttle factor")
    args = parser.parse_args()
    if args.build:
        publish.build(args.dist, BASE)
    handler = functools.partial(_Handler, directory=str(args.dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
        times = measure(url, switches=args.switches, entries=args.entries, slow=args.slow)
    finally:
        server.shutdown()
    print(report(times))


if __name__ == "__main__":
    main()
