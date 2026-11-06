"""Run spike 5 (native LaTeX in Flet) in Edge: save a screenshot and report frame timing."""

import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import webharness  # noqa: E402

OUT = ROOT / "spikes" / "spike5_web" / "shots"
OUT.mkdir(exist_ok=True)
RAF = "window.__raf = []; (function tick(t) { window.__raf.push(t); requestAnimationFrame(tick); })(0);"

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    dist = Path(tmp)
    webharness.publish(ROOT / "spikes" / "spike5_web", dist)
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 700, "height": 1500})
    ctx.add_init_script(RAF)
    with webharness.serve(dist) as url:
        page = ctx.new_page()
        lines: list[str] = []
        stamps: dict[str, float] = {}

        def on_console(m) -> None:
            lines.append(m.text)
            if m.text.startswith("SPIKE:"):
                stamps[m.text.split()[1]] = page.evaluate("performance.now()")

        page.on("console", on_console)
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        shot = False
        while time.perf_counter() - t0 < 240 and "SPIKE: DONE" not in lines:
            if "SPIKE: SAMPLES" in lines and not shot:
                page.wait_for_timeout(1500)
                page.screenshot(path=str(OUT / "latex.png"))
                shot = True
            page.wait_for_timeout(250)
        raf = page.evaluate("window.__raf")
        mem = page.evaluate("performance.memory ? performance.memory.usedJSHeapSize/1e6 : null")
        browser.close()

for x in lines:
    if x.startswith("SPIKE:") or "rror" in x:
        print(x)
a, b = stamps.get("STRESS_START"), stamps.get("DONE")
if a and b:
    frames = [t for t in raf if a <= t <= b]
    gaps = [y - x for x, y in zip(frames, frames[1:], strict=False)]
    print(f"stress window {(b - a) / 1000:.1f}s: {len(frames)} frames, max gap {max(gaps):.0f} ms")
    print("slow frames (>100ms):", [round(g) for g in gaps if g > 100])
print("JS heap MB:", mem)
