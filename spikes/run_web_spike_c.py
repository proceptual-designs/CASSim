"""Run spike C (sampling, fills, pan, pinch and wheel) in Edge.

Prints the app's timings. For each gesture phase the runner sends the input when the app says
READY: a mouse drag of 120 moves, a two-finger pinch of 60 moves (through the DevTools protocol)
or 60 wheel turns, one every 16 ms. `SENT` is how long the sending took; the app's `span` is how
long it was busy with the events, so span minus SENT is how far it fell behind. The browser's
frame rate and longest frame gap come from requestAnimationFrame. `--slow N` applies Chromium's
CPU throttle to the page's main thread; the Python worker may not be slowed by it.
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
CX, CY = 320, 240
GAP = 0.016

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--slow", type=float, default=1.0)
parser.add_argument("--headed", action="store_true")
args = parser.parse_args()


def paced(count: int, act) -> float:
    """Call `act(i)` every GAP seconds; return the time taken in ms."""
    start = time.perf_counter()
    for i in range(count):
        act(i)
        wait = start + (i + 1) * GAP - time.perf_counter()
        if wait > 0:
            time.sleep(wait)
    return (time.perf_counter() - start) * 1000


def drag(page) -> float:
    page.mouse.move(CX, CY)
    page.mouse.down()
    # Out and back, so the curves stay in view.
    ms = paced(120, lambda i: page.mouse.move(CX + 2 * (i if i < 60 else 120 - i), CY + i % 7))
    page.mouse.up()
    return ms


def pinch(page, cdp) -> float:
    def touch(kind: str, spread: float) -> None:
        points = [
            {"x": CX - spread, "y": CY, "id": 0},
            {"x": CX + spread, "y": CY, "id": 1},
        ]
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": points})

    touch("touchStart", 40)
    ms = paced(60, lambda i: touch("touchMove", 40 + 2 * (i if i < 30 else 60 - i)))
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    return ms


def wheel(page) -> float:
    page.mouse.move(CX, CY)
    return paced(60, lambda i: page.mouse.wheel(0, -40 if i < 30 else 40))


with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    dist = Path(tmp)
    webharness.publish(ROOT / "spikes" / "spike_c_web", dist)
    browser = p.chromium.launch(channel="msedge", headless=not args.headed)
    ctx = browser.new_context(viewport={"width": 900, "height": 700}, has_touch=True)
    ctx.add_init_script(RAF)
    with webharness.serve(dist) as url:
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)
        if args.slow != 1.0:
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": args.slow})
        lines: list[str] = []
        marks: list[tuple[str, float]] = []
        page.on("console", lambda m: lines.append(m.text))
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        seen = 0
        finished = False
        while time.perf_counter() - t0 < 900 and not finished:
            page.wait_for_timeout(100)
            while seen < len(lines):
                line = lines[seen]
                seen += 1
                text = line.removeprefix("SPIKE: ")
                if line.startswith(("SPIKE: PHASE", "SPIKE: DONE")):
                    marks.append((text, page.evaluate("performance.now()")))
                if line.startswith("SPIKE: READY"):
                    name = text.removeprefix("READY ")
                    if name.startswith("pan"):
                        sent = drag(page)
                    elif name.startswith("pinch"):
                        sent = pinch(page, cdp)
                    else:
                        sent = wheel(page)
                    print(f"SENT {name}: {sent:.0f} ms", flush=True)
                elif line.startswith("SPIKE:") and "PHASE" not in line:
                    print(text, flush=True)
                finished = finished or line == "SPIKE: DONE"
        raf = page.evaluate("window.__raf")
        browser.close()

for (name, a), (_, b) in zip(marks, marks[1:], strict=False):
    frames = [t for t in raf if a <= t <= b]
    gaps = [y - x for x, y in zip(frames, frames[1:], strict=False)]
    if gaps:
        print(
            f"BROWSER {name}: {len(frames) / ((b - a) / 1000):.0f} fps, "
            f"max gap {max(gaps):.0f} ms, gaps>50ms: {sum(g > 50 for g in gaps)}"
        )
