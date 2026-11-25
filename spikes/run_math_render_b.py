"""Run spike B headlessly (Edge via Playwright), print the measurements and save screenshots.

uv run python spikes/run_math_render_b.py            measure
uv run python spikes/run_math_render_b.py --serve    serve on http://127.0.0.1:8570/ until Ctrl+C
"""

from __future__ import annotations

import io
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "spikes" / "math_render_b"
sys.path.insert(0, str(B))
sys.path.insert(0, str(ROOT))
import harness  # noqa: E402

PORT = 8570
W, H = 1000, 420


def changed(a, b) -> bool:
    from PIL import ImageChops

    return ImageChops.difference(a, b).getbbox() is not None


def shot(page, clip=None):
    from PIL import Image

    return Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB")


def settle(page, seconds: float = 1.5) -> None:
    time.sleep(seconds)


def end_to_end(page, action, clip, timeout: float = 5.0) -> float:
    before = shot(page, clip)
    t0 = time.perf_counter()
    action()
    while time.perf_counter() - t0 < timeout:
        if changed(before, shot(page, clip)):
            return (time.perf_counter() - t0) * 1000
    return -1.0


def measure() -> None:
    from playwright.sync_api import sync_playwright

    log = B / "timings.log"
    log.unlink(missing_ok=True)
    with harness.server(B / "app.py", PORT) as url, sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": W, "height": H})
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        clip = {"x": 0, "y": 40, "width": W, "height": 280}
        for _ in range(100):
            if log.exists() and "draw" in log.read_text(encoding="utf-8"):
                break
            time.sleep(0.1)
        print(f"page load to first server draw: {(time.perf_counter() - t0) * 1000:.0f} ms")
        settle(page, 2.5)
        page.mouse.click(900, 380)  # focus the canvas, outside the editor
        settle(page, 0.5)
        shot(page).save(B / "shot_expr1.png")
        # (d) cursor moves
        moves = [
            end_to_end(page, lambda: page.keyboard.press("ArrowRight"), {"x": 0, "y": 185, "width": W, "height": 120})
            for _ in range(8)
        ]
        print("cursor move, key to changed pixels (incl. screenshot polling), ms:", [round(m) for m in moves])
        shot(page).save(B / "shot_expr1_moved.png")
        # selection
        page.keyboard.press("Shift+ArrowRight")
        page.keyboard.press("Shift+ArrowRight")
        settle(page, 0.8)
        shot(page).save(B / "shot_expr1_selection.png")
        # click: click in the middle of the numerator-ish area
        page.mouse.click(150, 205)
        settle(page, 0.8)
        shot(page).save(B / "shot_expr1_click.png")
        # redraw end to end (switch expression)
        redraw = end_to_end(page, lambda: page.keyboard.press("2"), clip)
        print(f"switch expression, key to changed pixels: {redraw:.0f} ms")
        settle(page, 1.0)
        shot(page).save(B / "shot_expr2.png")
        page.keyboard.press("3")
        settle(page, 1.5)
        shot(page).save(B / "shot_expr3.png")
        page.keyboard.press("1")
        settle(page, 1.5)
        # markers, and per-character comparison
        merged = shot(page, {"x": 0, "y": 185, "width": W, "height": 120})
        page.keyboard.press("c")
        settle(page, 1.5)
        per_char = shot(page, {"x": 0, "y": 185, "width": W, "height": 120})
        from PIL import ImageChops

        diff = ImageChops.difference(merged, per_char).convert("L").point(lambda v: 255 if v > 40 else 0)
        print("merged runs vs one Text per char, pixels differing:", sum(diff.histogram()[255:]), "bbox", diff.getbbox())
        page.keyboard.press("c")
        settle(page, 1.0)
        page.keyboard.press("m")
        settle(page, 1.0)
        shot(page).save(B / "shot_expr1_markers.png")
        browser.close()
    print("--- server log ---")
    lines = log.read_text(encoding="utf-8").splitlines()
    draws = [x for x in lines if x.startswith("draw")]
    overlays = [float(x.split("=")[1]) for x in lines if x.startswith("overlay_ms")]
    for d in draws:
        print(d)
    print(f"overlay updates (Python side) n={len(overlays)} median={statistics.median(overlays):.2f} ms max={max(overlays):.2f} ms")


def serve() -> None:
    with harness.server(B / "app.py", PORT) as url:
        print("serving", url, "(Ctrl+C to stop)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    serve() if "--serve" in sys.argv else measure()
