"""Experiment: is a Flutter Text run as wide as the sum of KaTeX hmtx advances?

Each case is (face, run, terminator). A draws run+terminator as one Text; B draws the run and then
the terminator as a separate Text at the computed x. The terminator's ink shifts between A and B by
the run's width error. Run: uv run python spikes/math_render_b/probe_advance.py
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

HERE = Path(__file__).parent
FAMILY = "packages/flutter_math_fork/KaTeX_"
SIZE = 40
PITCH = 50
FACES = {
    "Main": ("Main", False, False, "Main-Regular"),
    "Bold": ("Main", True, False, "Main-Bold"),
    "Math": ("Math", False, True, "Math-Italic"),
}
SIZES = [14, 20, 28]
import os

LS = float(os.environ.get("LS", "-0.24"))
CASES = [
    (face, run, "H", size)
    for size in SIZES
    for face, run in [("Main", "a" * 30), ("Main", "l" * 30), ("Main", "x+1=2" * 8), ("Bold", "a" * 30),
                      ("Math", "xyz" * 13), ("Main", "a" * 5), ("Main", "a" * 20)]
]


def server(port: int) -> None:
    import flet as ft

    metrics = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))

    def main(page: ft.Page) -> None:
        page.padding = 0
        page.bgcolor = "#ffffff"
        kids: list[ft.Control] = []
        for row, (face, run, term, size) in enumerate(CASES):
            fam, bold, italic, key = FACES[face]
            g = metrics[key]["glyphs"]
            w = sum(g[c][0] for c in run) * size

            def text(s: str, left: float, top: float, fam=fam, bold=bold, italic=italic):
                return ft.Text(
                    s,
                    left=left,
                    top=top,
                    no_wrap=True,
                    size=size,
                    color="#000000",
                    font_family=FAMILY + fam,
                    weight=ft.FontWeight.BOLD if bold else None,
                    italic=italic,
                    style=ft.TextStyle(height=1.0, letter_spacing=LS),
                )

            kids.append(text(run + term, 10, row * PITCH))
            if run:
                kids.append(text(run, 900, row * PITCH))
            kids.append(text(term, 900 + w, row * PITCH))
        page.add(ft.Stack(kids, width=1700, height=len(CASES) * PITCH))

    ft.run(main, view=ft.AppView.WEB_BROWSER, port=port)


def client() -> None:
    from PIL import Image
    from playwright.sync_api import sync_playwright

    metrics = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))
    with harness.server(Path(__file__), 8562) as url, sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        page = b.new_page(viewport={"width": 1700, "height": len(CASES) * PITCH})
        page.goto(url, wait_until="load")
        time.sleep(7)
        png = page.screenshot()
        b.close()
    img = Image.open(io.BytesIO(png)).convert("L")
    img.save(HERE / "probe_advance.png")
    for row, (face, run, term, size) in enumerate(CASES):
        top = row * PITCH
        g = metrics[FACES[face][3]]["glyphs"]
        w = sum(g[c][0] for c in run) * size

        def last_ink_right(x0: int, x1: int, top: int = top) -> int:
            mask = img.crop((x0, top, x1, top + PITCH)).point(lambda v: 255 if v < 140 else 0)
            bbox = mask.getbbox()
            return x0 + bbox[2] if bbox else -999

        a = last_ink_right(0, 880) - 10
        bb = last_ink_right(890, 1700) - 900
        print(f"size {size:2d} {face:5s} {run[:6]:7s} n={len(run):2d} width {w:6.1f}px  A-B: {a - bb:+d}px = {(a - bb) / len(run):+.3f}px/char = {(a - bb) / len(run) / size:+.4f}em/char")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server(int(sys.argv[2]))
    else:
        client()
