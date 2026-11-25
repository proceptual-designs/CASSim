"""Run math-render spike A in headless Chromium: timings, screenshots and ink-position checks.

    uv run python spikes/math_render_a/make_cases.py     # once, needs cassim (trees + LaTeX)
    uv run python spikes/run_math_render_a.py [--headed]

Screenshots go to spikes/math_render_a/shots/. Ink checks compare the ink bounding box found in
the screenshot (threshold at half coverage) with the box predicted from the font metrics.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import webharness  # noqa: E402

SHOTS = ROOT / "spikes" / "math_render_a" / "shots"
INK = 128

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--headed", action="store_true")
parser.add_argument("--analyse-only", action="store_true", help="reuse shots/ and console.txt")
args = parser.parse_args()


def ink_bbox(img: Image.Image, box: tuple[int, int, int, int], masks: list[list[float]]) -> tuple[int, int, int, int] | None:
    x0, y0, x1, y1 = box
    px = img.load()
    found = None
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            if px[x, y] < INK:
                continue
            if any(m[0] - 1 <= x <= m[2] + 1 and m[1] - 1 <= y <= m[3] + 1 for m in masks):
                continue
            if found is None:
                found = [x, y, x + 1, y + 1]
            else:
                found = [min(found[0], x), min(found[1], y), max(found[2], x + 1), max(found[3], y + 1)]
    return None if found is None else tuple(found)  # type: ignore[return-value]


def deltas(actual, predicted) -> list[float]:
    return [round(a - p, 1) for a, p in zip(actual, predicted, strict=True)]


def run_browser() -> None:
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        dist = Path(tmp)
        webharness.publish(ROOT / "spikes" / "math_render_a" / "app", dist)
        browser = p.chromium.launch(headless=not args.headed)
        try:
            ctx = browser.new_context(viewport={"width": 1120, "height": 1500}, device_scale_factor=1)
            with webharness.serve(dist) as url:
                page = ctx.new_page()
                page.on("console", lambda m: lines.append(m.text))
                t0 = time.perf_counter()
                page.goto(url, wait_until="load")
                while time.perf_counter() - t0 < 300 and "SPIKE: READY" not in lines:
                    page.wait_for_timeout(250)
                print(f"ready after {time.perf_counter() - t0:.1f}s")
                page.wait_for_timeout(500)
                page.screenshot(path=SHOTS / "initial.png")
                page.mouse.click(5, 5)  # focus
                page.keyboard.press("m")
                page.wait_for_timeout(400)
                page.screenshot(path=SHOTS / "markers.png")
                page.keyboard.press("m")
                page.keyboard.press("b")
                page.wait_for_timeout(400)
                page.screenshot(path=SHOTS / "boxes.png")
                page.keyboard.press("b")
                page.wait_for_timeout(300)
                targets = {}
                for x in lines:
                    if x.startswith("SPIKE: TARGETS "):
                        n, data = x.removeprefix("SPIKE: TARGETS ").split(" ", 1)
                        targets[int(n)] = json.loads(data)
                for n in sorted(targets):
                    for tx, ty, key in targets[n][:2]:
                        page.mouse.click(tx, ty)
                        page.wait_for_timeout(250)
                        lines.append(f"(clicked panel {n} at {tx:.1f},{ty:.1f} meaning row {key} pos 0/1)")
                page.screenshot(path=SHOTS / "after_clicks.png")
                for _ in range(3):
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(150)
                page.screenshot(path=SHOTS / "after_keys.png")
                # end to end: key press to next frame with the moved cursor is not observable from
                # here; time the Python-side handler via the KEY lines instead
        finally:
            browser.close()


sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
SHOTS.mkdir(parents=True, exist_ok=True)
lines: list[str] = []
if args.analyse_only:
    lines = (SHOTS / "console.txt").read_text(encoding="utf-8").splitlines()
else:
    run_browser()

(SHOTS / "console.txt").write_text("\n".join(lines), encoding="utf-8")
for x in lines:
    if x.startswith(("SPIKE: LAYOUT", "SPIKE: DRAW", "SPIKE: CURSOR", "SPIKE: TAP", "SPIKE: KEY", "(clicked")) or "rror" in x:
        print(x)

img = Image.open(SHOTS / "initial.png").convert("L")
cal = json.loads(next(x for x in lines if x.startswith("SPIKE: CAL ")).removeprefix("SPIKE: CAL "))
print("\nCalibration (actual - predicted ink box, px: left top right bottom):")
for x0, y0, x1, y1, label in cal:
    found = ink_bbox(img, (int(x0) - 15, int(y0) - 15, int(x1) + 16, int(y1) + 16), [])
    print(f"  {label:28s} {deltas(found, [x0, y0, x1, y1]) if found else 'no ink'}")

worst = []
for x in lines:
    if not x.startswith("SPIKE: BOXES "):
        continue
    n, data = x.removeprefix("SPIKE: BOXES ").split(" ", 1)
    d = json.loads(data)
    errs = []
    for i, g in enumerate(d["glyphs"]):
        others = [o[:4] for j, o in enumerate(d["glyphs"]) if j != i] + d["other"]
        found = ink_bbox(img, (int(g[0]) - 4, int(g[1]) - 4, int(g[2]) + 5, int(g[3]) + 5), others)
        if found:
            e = deltas(found, g[:4])
            errs.append(max(abs(v) for v in e))
            worst.append((max(abs(v) for v in e), n, g[4], e))
    print(f"panel {n}: {len(errs)} glyph runs checked, median max-edge error "
          f"{statistics.median(errs):.1f}px, max {max(errs):.1f}px")
    c = d["canvas"]
    lt = d["latex_top"]
    crop = Image.open(SHOTS / "initial.png").crop((0, int(lt) - 4, int(c[0] + c[2] + 10), int(c[1] + c[3] + 4)))
    crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save(SHOTS / f"compare_{n}.png")
    mk = Image.open(SHOTS / "markers.png").crop((int(c[0]), int(c[1]), int(c[0] + c[2]), int(c[1] + c[3])))
    mk.resize((mk.width * 3, mk.height * 3), Image.NEAREST).save(SHOTS / f"markers_{n}_x3.png")
    bx = Image.open(SHOTS / "boxes.png").crop((int(c[0]), int(c[1]), int(c[0] + c[2]), int(c[1] + c[3])))
    bx.resize((bx.width * 3, bx.height * 3), Image.NEAREST).save(SHOTS / f"boxes_{n}_x3.png")
worst.sort(reverse=True)
print("largest glyph edge errors (px, panel, item, [left top right bottom]):")
for w in worst[:8]:
    print("  ", w)
