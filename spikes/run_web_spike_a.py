"""Run spike A (page switching and grid drawing) in Edge.

Prints the app's Python-side timings and, for each phase, the browser's frame rate and longest
frame gap from requestAnimationFrame. `--slow N` applies Chromium's CPU throttle to the page's
main thread (Flutter's drawing); the Python worker may not be slowed by it.
"""

import argparse
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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--slow", type=float, default=1.0)
parser.add_argument("--headed", action="store_true")
args = parser.parse_args()

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    dist = Path(tmp)
    webharness.publish(ROOT / "spikes" / "spike_a_web", dist)
    browser = p.chromium.launch(channel="msedge", headless=not args.headed)
    ctx = browser.new_context(viewport={"width": 900, "height": 700})
    ctx.add_init_script(RAF)
    with webharness.serve(dist) as url:
        page = ctx.new_page()
        if args.slow != 1.0:
            ctx.new_cdp_session(page).send("Emulation.setCPUThrottlingRate", {"rate": args.slow})
        lines: list[str] = []
        marks: list[tuple[str, float]] = []

        def on_console(m) -> None:
            lines.append(m.text)
            if m.text.startswith(("SPIKE: PHASE", "SPIKE: DONE")):
                marks.append((m.text.removeprefix("SPIKE: "), page.evaluate("performance.now()")))

        page.on("console", on_console)
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        while time.perf_counter() - t0 < 600 and "SPIKE: DONE" not in lines:
            page.wait_for_timeout(250)
        raf = page.evaluate("window.__raf")
        browser.close()

for x in lines:
    if x.startswith("SPIKE:") and "START" not in x and "PHASE" not in x:
        print(x)
for (name, a), (_, b) in zip(marks, marks[1:], strict=False):
    frames = [t for t in raf if a <= t <= b]
    gaps = [y - x for x, y in zip(frames, frames[1:], strict=False)]
    if gaps:
        print(
            f"BROWSER {name}: {len(frames) / ((b - a) / 1000):.0f} fps, "
            f"max gap {max(gaps):.0f} ms, gaps>50ms: {sum(g > 50 for g in gaps)}"
        )
