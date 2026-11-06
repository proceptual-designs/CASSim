"""Run spike 7 (cancel and restore with the real engine) in Edge and print the markers."""

import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import webharness  # noqa: E402

RAF = "window.__raf = []; (function tick(t) { window.__raf.push(t); requestAnimationFrame(tick); })(0);"

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    dist = Path(tmp)
    webharness.publish(ROOT / "spikes" / "spike7_web", dist)
    print("cassim.zip published:", (dist / "cassim.zip").exists())
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 700, "height": 400})
    ctx.add_init_script(RAF)
    with webharness.serve(dist) as url:
        page = ctx.new_page()
        lines: list[str] = []
        stamps: dict[str, float] = {}

        def on_console(m) -> None:
            lines.append(m.text)
            if m.text.startswith("SPIKE: "):
                stamps[m.text[7:]] = page.evaluate("performance.now()")

        page.on("console", on_console)
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        while time.perf_counter() - t0 < 420 and "SPIKE: DONE" not in lines:
            page.wait_for_timeout(500)
        raf = page.evaluate("window.__raf")
        browser.close()
for x in lines:
    if x.startswith("SPIKE:") or "rror" in x:
        print(x)
def window(label: str, a: float, b: float) -> None:
    frames = [t for t in raf if a <= t <= b]
    gaps = [y - x for x, y in zip(frames, frames[1:], strict=False)]
    print(f"main thread {label}: {len(frames)} frames in {(b - a) / 1000:.1f}s, max gap {max(gaps, default=0):.0f} ms")


window("whole run", raf[0], raf[-1])
start = next((v for k, v in stamps.items() if k.startswith("f(3) =")), None)
end = stamps.get("DONE")
if start and end:
    window("after boot (cancels + replays)", start, end)
