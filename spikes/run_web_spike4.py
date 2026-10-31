"""Run spike 4 (UI responsiveness and cancel) in Edge and report Python-side timings plus browser frame rate."""

import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import webharness  # noqa: E402

RAF = """
window.__raf = [];
(function tick(t) { window.__raf.push(t); requestAnimationFrame(tick); })(0);
"""

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    dist = Path(tmp)
    webharness.publish(ROOT / "spikes" / "spike4_web", dist)
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 900, "height": 700})
    ctx.add_init_script(RAF)
    with webharness.serve(dist) as url:
        page = ctx.new_page()
        lines: list[str] = []
        stamps: dict[str, float] = {}

        def on_console(m) -> None:  # noqa: ANN001
            lines.append(m.text)
            if m.text in ("SPIKE: A_START", "SPIKE: A_END", "SPIKE: DONE"):
                stamps[m.text] = page.evaluate("performance.now()")

        page.on("console", on_console)
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        while time.perf_counter() - t0 < 240 and "SPIKE: DONE" not in lines:
            page.wait_for_timeout(250)
        raf = page.evaluate("window.__raf")
        browser.close()

for x in lines:
    if x.startswith("SPIKE:") and "_START" not in x and "A_END" not in x:
        print(x)


def raf_report(label: str, start: str, end: str) -> None:
    if start in stamps and end in stamps:
        a, b = stamps[start], stamps[end]
        frames = [t for t in raf if a <= t <= b]
        gaps = [y - x for x, y in zip(frames, frames[1:], strict=False)]
        print(f"BROWSER rAF {label}: {len(frames)} frames in {(b - a) / 1000:.1f}s, max gap {max(gaps, default=0):.0f} ms")


raf_report("over 1s idle + 3s busy loop in Flet worker", "SPIKE: A_START", "SPIKE: A_END")
