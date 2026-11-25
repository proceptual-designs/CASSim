"""Spike A demo: the current LaTeX drawing above our own TeX-style layout painted on a canvas.

Everything sits at absolute positions in one Stack, so the runner knows where each pixel came
from. Output lines start with `SPIKE:` (read from the browser console by the runner).

Keys: Left/Right move the cursor in the active expression (the last one clicked; the first at
start), `m` toggles 1px gap markers, `b` toggles predicted ink boxes. A click places the cursor
with `Layout.hit`.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
from pathlib import Path

import flet as ft
import flet.canvas as cv

import mathlayout as ml
import painter
import treeio

PX = 24  # em size in pixels, for both drawings
PAD = 8
BG, INK = "#101010", "#f0f0f0"
CAL_H = 270
START = {  # where each expression's cursor starts: (path, pos)
    0: (((3, 0), (5, 0), (0, 1)), 1),  # after the 3 in the first exponent's 1/3
    1: (((0, 2),), 2),  # after x² in the integrand
    2: (((0, 3), (0, 0)), 1),  # after x in |x-1|
}


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def ink_box(font: str, text: str, x: float, baseline: float, size: float) -> list[float]:
    """The predicted ink box of a glyph run in pixels."""
    gs = [ml.glyph(font, c) for c in text]
    gs = [g for g in gs if g is not None]
    left = x + gs[0][3] * size
    adv = sum(g[0] for g in gs[:-1])
    right = x + (adv + gs[-1][4]) * size
    top = baseline - max(g[1] for g in gs) * size
    bottom = baseline + max(g[2] for g in gs) * size
    return [round(left, 2), round(top, 2), round(right, 2), round(bottom, 2)]


CAL = [  # font, text, size px, x, baseline
    ("Main-Regular", "1", 90, 10, 140),
    ("Math-Italic", "x", 90, 110, 140),
    ("Math-Italic", "f", 90, 210, 140),
    ("Main-Bold", "e", 90, 310, 140),
    ("Math-BoldItalic", "i", 90, 410, 140),
    ("Size1-Regular", "∫", 90, 500, 140),
    ("Size1-Regular", "∑", 90, 580, 140),
    ("Size4-Regular", "(", 45, 700, 140),
    ("AMS-Regular", "□", 90, 760, 140),
    ("Typewriter-Regular", '"', 90, 860, 140),
    ("Main-Regular", "0123456789", 60, 10, 240),
    ("Math-Italic", "abcxyz", 60, 340, 240),
    ("Main-Regular", "sin", 60, 620, 240),
    ("Main-Regular", "(1+√∣", 60, 760, 240),
]


class Panel:
    def __init__(self, n: int, case: dict, top: float) -> None:
        self.n = n
        self.row = treeio.load_row(case["tree"])
        styles = case["styles"]
        self.lookup = lambda p: styles.get(treeio.path_key(p), {})
        t0 = time.perf_counter()
        self.lay = ml.layout(self.row, self.lookup)
        self.first_layout_ms = (time.perf_counter() - t0) * 1000
        lay = self.lay
        self.w = lay.width * PX + 2 * PAD
        self.h = (lay.height + lay.depth) * PX + 2 * PAD
        self.ox, self.oy = PAD, PAD + lay.height * PX  # root baseline, in the canvas
        self.stops = lay.stops()
        self.k = self.stops.index(START[n]) if START.get(n) in self.stops else 0
        self.latex_top = top
        self.canvas_top = top + self.h + 16
        self.bottom = self.canvas_top + self.h
        self.content = cv.Canvas(self.content_shapes(), width=self.w, height=self.h)
        self.cover = cv.Canvas(self.overlay_shapes(), width=self.w, height=self.h)
        self.marks = cv.Canvas(self.marker_shapes(), width=self.w, height=self.h, visible=False)
        self.boxes = cv.Canvas(self.box_shapes(), width=self.w, height=self.h, visible=False)
        self.touch = ft.GestureDetector(
            content=ft.Container(width=self.w, height=self.h), on_tap_down=self.tap
        )

    def controls(self) -> list[ft.Control]:
        latex = ft.Markdown(
            f"${self.latex_markdown()}$",
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            fit_content=True,
            latex_style=ft.TextStyle(color=INK, size=PX),
        )
        left = 10
        return [
            ft.Container(latex, left=left + PAD, top=self.latex_top),
            ft.Container(self.content, left=left, top=self.canvas_top),
            ft.Container(self.marks, left=left, top=self.canvas_top),
            ft.Container(self.boxes, left=left, top=self.canvas_top),
            ft.Container(self.cover, left=left, top=self.canvas_top),
            ft.Container(self.touch, left=left, top=self.canvas_top),
        ]

    latex_src = ""

    def latex_markdown(self) -> str:
        return self.latex_src.replace("\\\\", r"\cr ")  # latex_for_markdown

    def content_shapes(self) -> list[cv.Shape]:
        return painter.shapes(self.lay, PX, self.ox, self.oy, INK)

    def overlay_shapes(self) -> list[cv.Shape]:
        path, pos = self.stops[self.k]
        return painter.overlay(self.lay, PX, self.ox, self.oy, path, pos, None)

    def marker_shapes(self) -> list[cv.Shape]:
        red = ft.Paint(color="#ff3030", stroke_width=1)
        out: list[cv.Shape] = []
        for r in self.lay.rows.values():
            for g in r.gaps:
                x = round(self.ox + g * PX) + 0.5
                out.append(cv.Line(x, self.oy + (r.baseline - r.height) * PX, x, self.oy + (r.baseline + r.depth) * PX, red))
            y = round(self.oy + r.baseline * PX) + 0.5
            out.append(cv.Line(self.ox + r.x0 * PX, y, self.ox + r.x1 * PX, y, ft.Paint(color="#30ff30", stroke_width=1)))
        return out

    def predicted(self) -> tuple[list[list[float]], list[list[float]]]:
        """Glyph ink boxes and the boxes of rules and radicals, in page pixels."""
        glyphs, other = [], []
        dx, dy = 10 + self.ox, self.canvas_top + self.oy
        for it in self.lay.items:
            if isinstance(it, ml.Glyphs):
                glyphs.append([*ink_box(it.font, it.text, dx + it.x * PX, dy + it.y * PX, it.scale * PX), it.text])
            elif isinstance(it, ml.Rule):
                other.append([dx + it.x * PX, dy + it.y * PX, dx + (it.x + it.w) * PX, dy + (it.y + it.h) * PX])
            else:
                sign = it.points[:4] + it.points[6:]  # the radical sign without its vinculum
                xs, ys = [p[0] for p in sign], [p[1] for p in sign]
                other.append([dx + min(xs) * PX, dy + min(ys) * PX, dx + max(xs) * PX, dy + max(ys) * PX])
        return glyphs, other

    def box_shapes(self) -> list[cv.Shape]:
        paint = ft.Paint(color="#ffcc00", stroke_width=1, style=ft.PaintingStyle.STROKE)
        glyphs, _ = self.predicted()
        dx, dy = 10, self.canvas_top
        return [cv.Rect(a - dx, b - dy, c - a, d - b, paint=paint) for a, b, c, d, *_ in glyphs]

    def move(self, step: int) -> None:
        self.k = max(0, min(len(self.stops) - 1, self.k + step))
        self.cover.shapes = self.overlay_shapes()
        self.cover.update()

    def tap(self, e: ft.TapEvent) -> None:
        p = e.local_position
        if p is None:
            return
        x, y = (p.x - self.ox) / PX, (p.y - self.oy) / PX
        path, pos = self.lay.hit(x, y)
        self.k = self.stops.index((path, pos))
        self.cover.shapes = self.overlay_shapes()
        self.cover.update()
        APP["active"] = self.n
        say(f"TAP {self.n} at ({p.x:.1f},{p.y:.1f}) -> path {treeio.path_key(path) or 'root'} pos {pos}")


APP: dict = {"active": 0}


async def main(page: ft.Page) -> None:
    page.padding = 0
    page.bgcolor = BG
    page.title = "Spike A: TeX layout on a canvas"
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    cal = cv.Canvas(width=1100, height=CAL_H)
    cal_boxes = []
    for font, text, size, x, base in CAL:
        cal.shapes.append(painter.glyph_shape(font, text, x, base, size, INK))
        cal_boxes.append([*ink_box(font, text, x, base, size), f"{font}:{text}"])
    panels: list[Panel] = []
    top = CAL_H
    for n, case in enumerate(cases):
        panel = Panel(n, case, top)
        panel.latex_src = case["latex"]
        panels.append(panel)
        top = panel.bottom + 24
    stack = ft.Stack([ft.Container(cal, left=0, top=0)], width=1100, height=top)
    for panel in panels:
        stack.controls.extend(panel.controls())
    page.add(stack)

    def on_key(e: ft.KeyboardEvent) -> None:
        panel = panels[APP["active"]]
        if e.key == "Arrow Left":
            panel.move(-1)
        elif e.key == "Arrow Right":
            panel.move(1)
        elif e.key in ("M", "B"):
            for p in panels:
                c = p.marks if e.key == "M" else p.boxes
                c.visible = not c.visible
                c.update()
        else:
            return
        path, pos = panel.stops[panel.k]
        say(f"KEY {e.key} {panel.n} -> path {treeio.path_key(path) or 'root'} pos {pos}")

    page.on_keyboard_event = on_key
    await asyncio.sleep(2)  # fonts and first frame

    # (a) layout time under Pyodide
    p0 = panels[0]
    times = []
    for _ in range(20):
        t0 = time.perf_counter()
        ml.layout(p0.row, p0.lookup)
        times.append((time.perf_counter() - t0) * 1000)
    say(f"LAYOUT case0 first={p0.first_layout_ms:.1f}ms median={statistics.median(times):.1f}ms "
        f"items={len(p0.lay.items)} rows={len(p0.lay.rows)} stops={len(p0.stops)}")
    for p in panels[1:]:
        say(f"LAYOUT case{p.n} first={p.first_layout_ms:.1f}ms items={len(p.lay.items)}")

    # (b, c) first draw: clear, then send all shapes; median of 10
    build, send = [], []
    for _ in range(10):
        p0.content.shapes = []
        p0.content.update()
        await asyncio.sleep(0.05)
        t0 = time.perf_counter()
        shapes = p0.content_shapes()
        t1 = time.perf_counter()
        p0.content.shapes = shapes
        p0.content.update()
        await asyncio.sleep(0)
        t2 = time.perf_counter()
        build.append((t1 - t0) * 1000)
        send.append((t2 - t1) * 1000)
    say(f"DRAW case0 shapes={len(shapes)} build_med={statistics.median(build):.1f}ms "
        f"update_med={statistics.median(send):.1f}ms update_max={max(send):.1f}ms")

    # (d) cursor move: overlay only
    moves = []
    for k in range(40):
        t0 = time.perf_counter()
        p0.move(1 if k < 20 else -1)
        await asyncio.sleep(0)
        moves.append((time.perf_counter() - t0) * 1000)
    say(f"CURSOR case0 overlay_shapes={len(p0.cover.shapes)} move_med={statistics.median(moves):.1f}ms "
        f"move_max={max(moves):.1f}ms")

    # predictions for the runner's screenshot checks
    say("CAL " + json.dumps(cal_boxes))
    for p in panels:
        glyphs, other = p.predicted()
        say(f"BOXES {p.n} " + json.dumps({"glyphs": glyphs, "other": other,
                                          "canvas": [10, p.canvas_top, p.w, p.h],
                                          "latex_top": p.latex_top}))
        # a click target per panel: the middle of the first glyph inside a slot two deep
        targets = []
        for path, pos in p.stops:
            if len(path) >= 2 and pos == 0 and len(p.lay.rows[path].nodes) > 0:
                x, a, b = p.lay.caret(path, pos)
                node = p.lay.rows[path].nodes[0]
                cx = (node[0] + node[1]) / 2
                targets.append([10 + p.ox + cx * PX, p.canvas_top + p.oy + (a + b) / 2 * PX,
                                treeio.path_key(path)])
        say(f"TARGETS {p.n} " + json.dumps(targets[:4]))
    say("READY")


ft.run(main)
