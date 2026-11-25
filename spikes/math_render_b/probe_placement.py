"""Experiment: where does Flutter put glyphs inside a Text box, and is a run the sum of advances?

Serves a page of probes (Flet web, Python backend) and screenshots it with Playwright; prints the
ink top/bottom of an 'H' for each face and a pixel diff between a whole run and the same run
placed as pieces at computed x. Run: uv run python spikes/math_render_b/probe_placement.py
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
FAMILY = "packages/flutter_math_fork/KaTeX_"
# name, family, bold, italic, metrics key, run text
FACES = [
    ("Main", "Main", False, False, "Main-Regular", "Hello(x)+1-2=3.14 office fi fl"),
    ("MainBold", "Main", True, False, "Main-Bold", "Hello(x)+1-2=3.14 office"),
    ("MainItalic", "Main", False, True, "Main-Italic", "Hello(x) office fi"),
    ("Math", "Math", False, True, "Math-Italic", "xyzfabcπθ fi"),
    ("MathBI", "Math", True, True, "Math-BoldItalic", "xyzfabc"),
    ("Size1", "Size1", False, False, "Size1-Regular", "(){}[]∫"),
    ("Typewriter", "Typewriter", False, False, "Typewriter-Regular", 'a"b"(1)'),
]
SIZE = 60
PROBE = {"Size1": "("}
HEIGHTS = [1.0, 1.5]


def server() -> None:
    import flet as ft

    metrics = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))

    def width(key: str, text: str) -> float:
        g = metrics[key]["glyphs"]
        return sum(g[c][0] for c in text) * SIZE

    def main(page: ft.Page) -> None:
        page.padding = 0
        page.bgcolor = "#ffffff"
        kids: list[ft.Control] = []
        for h_i, height in enumerate(HEIGHTS):
            for i, (_name, fam, bold, italic, key, run) in enumerate(FACES):
                top = (h_i * len(FACES) + i) * 200

                def text(s: str, left: float, t: float) -> ft.Text:
                    return ft.Text(
                        s,
                        left=left,
                        top=t,
                        no_wrap=True,
                        size=SIZE,
                        color="#000000",
                        font_family=FAMILY + fam,
                        weight=ft.FontWeight.BOLD if bold else None,
                        italic=italic,
                        style=ft.TextStyle(height=height),
                    )

                probe = PROBE.get(_name, "H" if "H" in metrics[key]["glyphs"] else "x")
                kids.append(text(probe, 10, top))
                # whole run + H, versus the run and the H as two pieces at computed x
                kids.append(text(run + probe, 150, top))
                kids.append(text(run, 150, top + 100))
                kids.append(text(probe, 150 + width(key, run), top + 100))
        page.add(ft.Stack(kids, width=1500, height=len(HEIGHTS) * len(FACES) * 200))

    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8561, no_cdn=False)


def client() -> None:
    from PIL import Image, ImageChops
    from playwright.sync_api import sync_playwright

    metrics = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))
    proc = subprocess.Popen([sys.executable, __file__, "server"], stdout=subprocess.DEVNULL)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge", headless=True)
            page = b.new_page(viewport={"width": 1500, "height": 2800})
            for _ in range(60):
                try:
                    page.goto("http://127.0.0.1:8561/", wait_until="load")
                    break
                except Exception:
                    time.sleep(0.5)
            time.sleep(6)
            png = page.screenshot(full_page=False)
            b.close()
    finally:
        proc.terminate()
    img = Image.open(io.BytesIO(png)).convert("L")
    img.save(HERE / "probe_placement.png")
    for h_i, height in enumerate(HEIGHTS):
        for i, (name, _f, _b, _i, key, run) in enumerate(FACES):
            top = (h_i * len(FACES) + i) * 200
            a = img.crop((0, top, 140, top + 200)).point(lambda v: 255 if v < 128 else 0)
            bbox = a.getbbox()
            g = metrics[key]["glyphs"]
            ch = PROBE.get(name, "H" if "H" in g else "x")
            ymax, ymin = g[ch][1], g[ch][2]
            hh = metrics[key]["hhea"]
            asc, desc = hh[0], -hh[1]
            ink_top, ink_bot = bbox[1], bbox[3]
            base_from_ink_bot = ink_bot + ymin * SIZE  # bottom of ink = baseline - ymin*size
            base_from_ink_top = ink_top + ymax * SIZE
            pred_prop = height * SIZE * asc / (asc + desc)
            pred_half = (height * SIZE - (asc + desc) * SIZE) / 2 + asc * SIZE
            A = img.crop((140, top, 1490, top + 100))
            B = img.crop((140, top + 100, 1490, top + 200))
            diff = ImageChops.difference(A, B).point(lambda v: 255 if v > 60 else 0)
            print(
                f"h={height} {name:10s} baseline(ink) bot={base_from_ink_bot - 0:.1f}"
                f" top={base_from_ink_top:.1f} | pred_prop={pred_prop:.1f} pred_half={pred_half:.1f}"
                f" | run diff bbox={diff.getbbox()}"
            )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server()
    else:
        client()
