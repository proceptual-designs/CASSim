"""Spike 3: Flet canvas drawing speed for a 2000-point graph with pan and zoom.

Three ways to draw the same curve are compared, each over scripted pan and zoom steps:
one ``Path`` (MoveTo + LineTo), one ``Points`` in POLYGON mode, and one ``Line`` per segment.
Python-side cost per step (build shapes + ``canvas.update()``) is reported; the browser test
measures the rendering side with requestAnimationFrame.
"""

import asyncio
import math
import statistics
import time

import flet as ft
import flet.canvas as cv

W, H = 640, 400
N = 2000
STEPS = 40
PAINT = ft.Paint(color=ft.Colors.BLUE, stroke_width=2, style=ft.PaintingStyle.STROKE)


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def curve(x0: float, x1: float) -> list[tuple[float, float]]:
    """Return N pixel-space points of f(x)=sin(x)+0.3*sin(7x) over [x0, x1]."""
    pts = []
    span = x1 - x0
    for i in range(N):
        x = x0 + span * i / (N - 1)
        y = math.sin(x) + 0.3 * math.sin(7 * x)
        pts.append((W * i / (N - 1), H / 2 - y * H / 5))
    return pts


def shapes_path(pts: list[tuple[float, float]]) -> list[cv.Shape]:
    els = [cv.Path.MoveTo(pts[0][0], pts[0][1])]
    els += [cv.Path.LineTo(x, y) for x, y in pts[1:]]
    return [cv.Path(els, paint=PAINT)]


def shapes_points(pts: list[tuple[float, float]]) -> list[cv.Shape]:
    return [cv.Points(pts, point_mode=cv.PointMode.POLYGON, paint=PAINT)]


def shapes_lines(pts: list[tuple[float, float]]) -> list[cv.Shape]:
    return [cv.Line(a[0], a[1], b[0], b[1], paint=PAINT) for a, b in zip(pts, pts[1:], strict=False)]


VARIANTS = {"path": shapes_path, "points": shapes_points, "lines": shapes_lines}


async def run_variant(canvas: cv.Canvas, name: str, build) -> None:  # noqa: ANN001
    """Time STEPS pans (window slides) then STEPS zooms (window width changes)."""
    steps = 5 if name == "lines" else STEPS  # per-segment shapes are far too slow to repeat 40x
    for phase in ("pan", "zoom"):
        build_ms: list[float] = []
        update_ms: list[float] = []
        t_phase = time.perf_counter()
        for k in range(steps):
            if phase == "pan":
                x0, x1 = -6 + k * 0.1, 6 + k * 0.1
            else:
                half = 6 * (0.97**k)
                x0, x1 = -half, half
            t0 = time.perf_counter()
            canvas.shapes = build(curve(x0, x1))
            t1 = time.perf_counter()
            canvas.update()
            await asyncio.sleep(0)
            t2 = time.perf_counter()
            build_ms.append((t1 - t0) * 1000)
            update_ms.append((t2 - t1) * 1000)
        total = time.perf_counter() - t_phase
        say(
            f"RESULT {name} {phase} steps={steps} total={total:.2f}s "
            f"build_med={statistics.median(build_ms):.1f}ms "
            f"update_med={statistics.median(update_ms):.1f}ms "
            f"update_max={max(update_ms):.1f}ms fps={steps / total:.1f}"
        )


async def main(page: ft.Page) -> None:
    canvas = cv.Canvas(width=W, height=H)
    page.add(ft.Text("spike3"), canvas)
    await asyncio.sleep(1)
    say("START")
    for name, build in VARIANTS.items():
        try:
            await run_variant(canvas, name, build)
        except Exception as e:  # noqa: BLE001
            say(f"{name} ERROR {e!r}")
    canvas.shapes = []
    canvas.update()
    say("DONE")


ft.run(main)
