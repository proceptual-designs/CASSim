"""Spike D (decision 0031): implicit curves by marching squares in pure Python.

A relation such as x^2+y^2=4 is drawn by sampling f(x,y) = left - right on a grid over the
window and joining the points where it changes sign. This times the sampling and the marching for
a Computer-size window (640 by 424) and a Handheld-size one (320 by 212) at cells of 8, 4 and 2
pixels, and measures how far the points of a circle are from the true circle, in pixels.

Run natively (`python spikes/spike_d_implicit.py`) and inside Pyodide
(`python spikes/run_web_spike_b.py spikes/spike_d_implicit.py --dist <a build>`).
"""

from __future__ import annotations

import math
import time

ERRORS = (ValueError, ZeroDivisionError, OverflowError)
NAMES = {name: getattr(math, name) for name in ("sin", "cos", "tan", "exp", "sqrt", "log")}

RELATIONS = {
    "circle x^2+y^2=4": "x*x + y*y - 4",
    "ellipse x^2+x*y+2*y^2=3": "x*x + x*y + 2*y*y - 3",
    "hyperbola x^2-y^2=1": "x*x - y*y - 1",
    "sin(x)+cos(y)=1/2": "sin(x) + cos(y) - 0.5",
    "y=1/x as x*y=1": "x*y - 1",
    "y=tan(x) (jumps)": "y - tan(x)",
    "sqrt(x)+sqrt(y)=2 (domain)": "sqrt(x) + sqrt(y) - 2",
}

Segment = tuple[float, float, float, float]


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def compile_grid(src: str):
    """Rows of f over the grid: a comprehension, or a guarded loop if a point raises."""
    scope: dict[str, object] = dict(NAMES)
    exec(f"def quick(xs, ys):\n    return [[{src} for x in xs] for y in ys]\n", scope)
    code = (
        "def slow(xs, ys):\n"
        "    rows = []\n"
        "    for y in ys:\n"
        "        row = []\n"
        "        for x in xs:\n"
        "            try:\n"
        f"                row.append({src})\n"
        "            except ERRORS:\n"
        "                row.append(None)\n"
        "        rows.append(row)\n"
        "    return rows\n"
    )
    scope["ERRORS"] = ERRORS
    exec(code, scope)
    quick, slow = scope["quick"], scope["slow"]

    def sample(xs: list[float], ys: list[float]) -> list[list[float | None]]:
        try:
            return quick(xs, ys)  # type: ignore[operator]
        except ERRORS:
            return slow(xs, ys)  # type: ignore[operator]

    return sample


def march(rows: list[list[float | None]], xs: list[float], ys: list[float]) -> list[Segment]:
    """Line segments where f changes sign, with the crossing found by linear interpolation."""
    out: list[Segment] = []
    add = out.append
    signs = [[None if v is None else v > 0 for v in row] for row in rows]
    for j in range(len(ys) - 1):
        s0, s1 = signs[j], signs[j + 1]
        if s0 == s1 and None not in s0 and len(set(s0)) == 1:
            continue
        r0, r1 = rows[j], rows[j + 1]
        y0, y1 = ys[j], ys[j + 1]
        for i in range(len(xs) - 1):
            a, b, c, d = s0[i], s0[i + 1], s1[i + 1], s1[i]
            if a == b == c == d or a is None or b is None or c is None or d is None:
                continue
            x0, x1 = xs[i], xs[i + 1]
            va, vb, vc, vd = r0[i], r0[i + 1], r1[i + 1], r1[i]
            pts: list[tuple[float, float]] = []
            if a != b:
                pts.append((x0 + (x1 - x0) * va / (va - vb), y0))
            if b != c:
                pts.append((x1, y0 + (y1 - y0) * vb / (vb - vc)))
            if c != d:
                pts.append((x0 + (x1 - x0) * vd / (vd - vc), y1))
            if d != a:
                pts.append((x0, y0 + (y1 - y0) * va / (va - vd)))
            if len(pts) == 2:
                add((*pts[0], *pts[1]))
            elif len(pts) == 4:  # a saddle: the centre value decides which corners join
                centre = (va + vb + vc + vd) / 4 > 0
                if centre == a:
                    add((*pts[0], *pts[1]))
                    add((*pts[2], *pts[3]))
                else:
                    add((*pts[3], *pts[0]))
                    add((*pts[1], *pts[2]))
    return out


def axis(lo: float, hi: float, n: int) -> list[float]:
    return [lo + (hi - lo) * i / n for i in range(n + 1)]


def run(width: int, height: int, label: str) -> None:
    x0, x1 = -6.0, 6.0
    half = (x1 - x0) * height / width / 2
    for cell in (8, 4, 2):
        nx, ny = width // cell, height // cell
        xs, ys = axis(x0, x1, nx), axis(-half, half, ny)
        for name, src in RELATIONS.items():
            sample = compile_grid(src)
            times = []
            for _ in range(3):
                t0 = time.perf_counter()
                rows = sample(xs, ys)
                t1 = time.perf_counter()
                segs = march(rows, xs, ys)
                t2 = time.perf_counter()
                times.append(((t1 - t0) * 1000, (t2 - t1) * 1000))
            s, m = min(times, key=sum)
            extra = ""
            if name.startswith("circle"):
                scale = width / (x1 - x0)
                err = max(abs(math.hypot(a, b) - 2) for a, b, _, _ in segs) * scale
                extra = f" circle_error={err:.3f}px"
            say(
                f"RESULT {label} cell={cell}px grid={nx}x{ny} {name}: sample={s:.1f}ms "
                f"march={m:.1f}ms total={s + m:.1f}ms segments={len(segs)}{extra}"
            )


if __name__ == "__main__":
    run(320, 212, "handheld")
    run(640, 424, "computer")
    say("DONE")
