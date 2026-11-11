"""Measure how long the published site takes to start (SRS 5.1: start-up is measured and reported).

    python -m tools.loadtime [--dist DIR] [--runs 3] [--build]

Serves the site below /CASSim/ as GitHub Pages would, opens it in Chromium and times the console
markers the app prints. The first visit is cold (nothing cached); the rest are warm reloads served
by the service worker, which is what an installed app does. Times are seconds from navigation.

Milestones, in the order they normally happen:
    flutter     Flutter's engine has started (the splash goes soon after)
    python      Flet's Python worker has Pyodide and Flet, and runs the app's main.py
    ui          the first screen has been sent to Flutter
    ready       saved settings and the autosaved document are back: keys work
    engine      the calculator engine worker has booted: Enter gives an answer
    spare       the spare engine (for Cancel) has booted
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import statistics
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Browser, ConsoleMessage, Error, Page, Playwright, sync_playwright

from tools import publish

BASE = "CASSim"
TYPES = {
    ".mjs": "text/javascript",
    ".js": "text/javascript",
    ".wasm": "application/wasm",
    ".webmanifest": "application/manifest+json",
}
# (name, text the console line contains, which occurrence)
MARKERS = [
    ("flutter", "Flutter app loaded", 1),
    ("python", "CASSIM: MAIN", 1),
    ("ui", "CASSIM: UI", 1),
    ("ready", "CASSIM: READY", 1),
    ("engine", "CASSIM: ENGINE READY", 1),
    ("spare", "CASSIM: ENGINE READY", 2),
]


class _Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        p = urlparse(path).path
        if not p.startswith(f"/{BASE}/") and p != f"/{BASE}":
            return str(Path(self.directory) / "__missing__")
        return super().translate_path("/" + p.removeprefix(f"/{BASE}").lstrip("/"))

    def guess_type(self, path: str | os.PathLike[str]) -> str:
        return TYPES.get(Path(path).suffix, super().guess_type(path))

    def log_message(self, format: str, *args: object) -> None:
        pass


def launch(playwright: Playwright) -> Browser:
    for channel in ("msedge", "chrome", None):
        try:
            return playwright.chromium.launch(headless=True, channel=channel)
        except Error:
            continue
    raise SystemExit("no Chromium-family browser available")


def one_visit(page: Page, url: str, *, reload: bool, timeout: float) -> dict[str, float]:
    """Load (or reload) the page; return each milestone's time in seconds from navigation."""
    seen: list[tuple[float, str]] = []

    def on_console(message: ConsoleMessage) -> None:
        seen.append((time.perf_counter(), message.text))

    page.on("console", on_console)
    start = time.perf_counter()
    if reload:
        page.reload(wait_until="commit")
    else:
        page.goto(url, wait_until="commit")
    found: dict[str, float] = {}
    while time.perf_counter() - start < timeout and len(found) < len(MARKERS):
        page.wait_for_timeout(100)
        for name, text, nth in MARKERS:
            hits = [t for t, line in seen if text in line]
            if name not in found and len(hits) >= nth:
                found[name] = hits[nth - 1] - start
    page.remove_listener("console", on_console)
    return found


def measure(
    dist: Path, runs: int, timeout: float = 180.0
) -> tuple[dict[str, float], list[dict[str, float]]]:
    handler = functools.partial(_Handler, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
    try:
        with sync_playwright() as p:
            browser = launch(p)
            page = browser.new_context().new_page()
            cold = one_visit(page, url, reload=False, timeout=timeout)
            # let the service worker finish precaching before the warm runs
            page.wait_for_function(
                "navigator.serviceWorker.getRegistration().then(r => !!(r && r.active))",
                timeout=timeout * 1000,
            )
            page.wait_for_timeout(3000)
            warm = [one_visit(page, url, reload=True, timeout=timeout) for _ in range(runs)]
            browser.close()
    finally:
        server.shutdown()
    return cold, warm


def report(cold: dict[str, float], warm: list[dict[str, float]]) -> str:
    lines = [f"{'milestone':<10}{'cold':>8}{'warm (median)':>16}"]
    for name, _, _ in MARKERS:
        times = [run[name] for run in warm if name in run]
        middle = f"{statistics.median(times):.1f}" if times else "-"
        first = f"{cold[name]:.1f}" if name in cold else "-"
        lines.append(f"{name:<10}{first:>8}{middle:>16}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--dist", type=Path, default=publish.DEFAULT_DIST)
    parser.add_argument("--runs", type=int, default=3, help="warm reloads to take the median of")
    parser.add_argument("--build", action="store_true", help="run tools.publish first")
    args = parser.parse_args()
    if args.build:
        publish.build(args.dist, BASE)
    cold, warm = measure(args.dist, args.runs)
    print(report(cold, warm))


if __name__ == "__main__":
    main()
