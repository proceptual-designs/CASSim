"""Spike C (decision 0031): sampling curves in the UI worker, fills, and pan, pinch and wheel.

The engine worker holds SymPy; the UI worker does not. The plan is for the engine to send each
curve as Python source over `math` and for the UI worker to sample it, so a pan or a zoom never
waits for the engine. This app measures, inside Flet's Pyodide worker:

1. Sampling: four ways to turn a source string into 2,000 values.
2. Frames: sample three curves, map them to the screen and send them, with and without fills
   (`Path` shapes for an integral region and an inequality region), and 3,000 separate line
   segments as an implicit curve would send them (spike D).
3. Gestures: the runner drags the mouse, pinches with two touches and turns the wheel while the
   app redraws; each way of handling the events is one phase.

The sources below are what `spikes/spike_c_compile.py` prints from SymPy expressions.
"""

import asyncio
import math
import statistics
import time

import flet as ft
import flet.canvas as cv

W, H = 640, 480
STEPS = 30
ERRORS = (ValueError, ZeroDivisionError, OverflowError)
COLOURS = (ft.Colors.BLUE, ft.Colors.RED, ft.Colors.GREEN)

SOURCES = {
    "sin": "math.sin(x) + 0.3*math.sin(7*x)",
    "cubic": "(1/10)*x**3 - x",
    "recip": "1/x",
    "sqrt": "math.sqrt(x)",
    "gauss": "math.exp(-1/2*x**2)",
    "tan": "math.tan(x)",
}
CURVES = ("sin", "cubic", "recip")


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


# ---- samplers ---------------------------------------------------------------------------------


def make_call(src: str):
    """One Python call for each point, with a try around it."""
    f = eval(f"lambda x: {src}", {"math": math})

    def sample(xs: list[float]) -> list[float | None]:
        out: list[float | None] = []
        for x in xs:
            try:
                out.append(f(x))
            except ERRORS:
                out.append(None)
        return out

    return sample


def make_loop(src: str, names: dict[str, object]):
    """The expression pasted into one generated loop, with a try around each point."""
    code = (
        "def sample(xs):\n"
        "    out = []\n"
        "    add = out.append\n"
        "    for x in xs:\n"
        "        try:\n"
        f"            add({src})\n"
        "        except ERRORS:\n"
        "            add(None)\n"
        "    return out\n"
    )
    scope: dict[str, object] = {"ERRORS": ERRORS, **names}
    exec(code, scope)
    return scope["sample"]


def make_fast(src: str, names: dict[str, object]):
    """A list comprehension with no try; the loop is used only if a point raises."""
    scope: dict[str, object] = dict(names)
    exec(f"def sample(xs):\n    return [{src} for x in xs]\n", scope)
    quick = scope["sample"]
    slow = make_loop(src, names)

    def sample(xs: list[float]) -> list[float | None]:
        try:
            return quick(xs)
        except ERRORS:
            return slow(xs)

    return sample


BARE = {name: getattr(math, name) for name in ("sin", "cos", "tan", "exp", "sqrt", "log")}


def bare(src: str) -> str:
    return src.replace("math.", "")


SAMPLERS = {name: make_fast(bare(src), BARE) for name, src in SOURCES.items()}


def grid(x0: float, x1: float, n: int) -> list[float]:
    step = (x1 - x0) / (n - 1)
    return [x0 + i * step for i in range(n)]


# ---- from values to shapes --------------------------------------------------------------------

View = tuple[float, float, float, float]


def segments(xs: list[float], ys: list[float | None], view: View) -> list[list[tuple]]:
    """Screen points, broken where the value is missing or jumps across the whole window."""
    x0, x1, y0, y1 = view
    sx, sy = W / (x1 - x0), H / (y1 - y0)
    out: list[list[tuple]] = []
    cur: list[tuple] = []
    prev = 0.0
    for x, y in zip(xs, ys, strict=True):
        if y is None or y != y or y in (math.inf, -math.inf):
            if len(cur) > 1:
                out.append(cur)
            cur = []
            continue
        py = min(max((y1 - y) * sy, -H), 2 * H)
        if cur and abs(py - prev) > H:
            if len(cur) > 1:
                out.append(cur)
            cur = []
        cur.append(((x - x0) * sx, py))
        prev = py
    if len(cur) > 1:
        out.append(cur)
    return out


def curve_shapes(view: View, n: int) -> list[cv.Shape]:
    xs = grid(view[0], view[1], n)
    shapes: list[cv.Shape] = []
    for name, colour in zip(CURVES, COLOURS, strict=True):
        paint = ft.Paint(color=colour, stroke_width=2, style=ft.PaintingStyle.STROKE)
        for seg in segments(xs, SAMPLERS[name](xs), view):
            shapes.append(cv.Points(seg, point_mode=cv.PointMode.POLYGON, paint=paint))
    return shapes


def fill_shapes(view: View, n: int, fill_n: int = 0) -> list[cv.Shape]:
    """An integral region under `sin` and the region above `cubic`, each one closed Path."""
    x0, x1, y0, y1 = view
    n = fill_n or n
    sy = H / (y1 - y0)
    axis = (y1 - 0) * sy
    out: list[cv.Shape] = []
    a, b = x0 + 0.3 * (x1 - x0), x0 + 0.6 * (x1 - x0)
    xs = grid(a, b, max(n * 3 // 10, 2))
    pts = segments(xs, SAMPLERS["sin"](xs), view)[0]
    els: list[cv.Path.PathElement] = [cv.Path.MoveTo(pts[0][0], axis)]
    els += [cv.Path.LineTo(px, py) for px, py in pts]
    els += [cv.Path.LineTo(pts[-1][0], axis), cv.Path.Close()]
    paint = ft.Paint(color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE), style=ft.PaintingStyle.FILL)
    out.append(cv.Path(els, paint=paint))
    xs = grid(x0, x1, n)
    pts = segments(xs, SAMPLERS["cubic"](xs), view)[0]
    els = [cv.Path.MoveTo(pts[0][0], 0)]
    els += [cv.Path.LineTo(px, py) for px, py in pts]
    els += [cv.Path.LineTo(pts[-1][0], 0), cv.Path.Close()]
    paint = ft.Paint(color=ft.Colors.with_opacity(0.2, ft.Colors.RED), style=ft.PaintingStyle.FILL)
    out.append(cv.Path(els, paint=paint))
    return out


def implicit_shapes(k: int, count: int) -> list[cv.Shape]:
    """`count` separate line segments around a circle, as marching squares would give them."""
    r = 150 + k
    pts: list[tuple] = []
    for i in range(count):
        t0, t1 = 2 * math.pi * i / count, 2 * math.pi * (i + 1) / count
        pts.append((W / 2 + r * math.cos(t0), H / 2 + r * math.sin(t0)))
        pts.append((W / 2 + r * math.cos(t1), H / 2 + r * math.sin(t1)))
    paint = ft.Paint(color=ft.Colors.PURPLE, stroke_width=2, style=ft.PaintingStyle.STROKE)
    return [cv.Points(pts, point_mode=cv.PointMode.LINES, paint=paint)]


# ---- part 1: samplers -------------------------------------------------------------------------


def best(fn, repeats: int = 5) -> float:
    times = []
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t) * 1000)
    return min(times)


async def sampling() -> None:
    xs = grid(-6.0, 6.0, 2000)
    for name, src in SOURCES.items():
        ways = {
            "call": make_call(src),
            "loop": make_loop(src, {"math": math}),
            "loop_bare": make_loop(bare(src), BARE),
            "fast_bare": make_fast(bare(src), BARE),
        }
        parts = " ".join(f"{way}={best(lambda fn=fn: fn(xs)):.2f}ms" for way, fn in ways.items())
        missing = sum(y is None for y in ways["loop"](xs))
        say(f"RESULT sample {name} n=2000 {parts} missing={missing}")
        await asyncio.sleep(0)
    t = time.perf_counter()
    for src in SOURCES.values():
        make_fast(bare(src), BARE)
    say(f"RESULT compile six sources {(time.perf_counter() - t) * 1000:.2f}ms")


# ---- part 2: frames ---------------------------------------------------------------------------


async def frames(canvas: cv.Canvas) -> None:
    def view_at(k: int) -> View:
        return (-6 + 0.1 * k, 6 + 0.1 * k, -4.5, 4.5)

    cases = {
        "curves n=2000": lambda k: curve_shapes(view_at(k), 2000),
        "curves n=640": lambda k: curve_shapes(view_at(k), 640),
        "curves+fills n=2000": lambda k: (
            fill_shapes(view_at(k), 2000) + curve_shapes(view_at(k), 2000)
        ),
        "curves+fills n=640": lambda k: (
            fill_shapes(view_at(k), 640) + curve_shapes(view_at(k), 640)
        ),
        "curves n=640, fills n=160": lambda k: (
            fill_shapes(view_at(k), 640, 160) + curve_shapes(view_at(k), 640)
        ),
        "implicit 3000 segments": lambda k: implicit_shapes(k, 3000),
        "implicit 600 segments": lambda k: implicit_shapes(k, 600),
    }
    for name, build in cases.items():
        say(f"PHASE frames {name}")
        built, sent = [], []
        start = time.perf_counter()
        for k in range(STEPS):
            t0 = time.perf_counter()
            canvas.shapes = build(k)
            t1 = time.perf_counter()
            canvas.update()
            await asyncio.sleep(0)
            built.append((t1 - t0) * 1000)
            sent.append((time.perf_counter() - t1) * 1000)
        per = (time.perf_counter() - start) * 1000 / STEPS
        say(
            f"RESULT frame {name}: build_med={statistics.median(built):.1f}ms "
            f"update_med={statistics.median(sent):.1f}ms update_max={max(sent):.1f}ms "
            f"per_frame={per:.1f}ms"
        )
        await asyncio.sleep(0.3)


# ---- part 3: gestures -------------------------------------------------------------------------


class Plot:
    """A graph window that follows pan, pinch and wheel events in one of several ways."""

    def __init__(self, mode: str, n: int, interval: int) -> None:
        self.mode, self.n = mode, n
        self.view: View = (-6.0, 6.0, -4.5, 4.5)
        self.start_view = self.view
        self.shift = (0.0, 0.0)
        self.canvas = cv.Canvas(curve_shapes(self.view, n), width=W, height=H, left=0, top=0)
        self.events = 0
        self.first = self.last_event = self.last_done = 0.0
        self.draws: list[float] = []
        self.waits: list[float] = []
        self.pending = 0.0
        self.dirty = asyncio.Event()
        self.closed = False
        stack = ft.Stack([self.canvas], width=W, height=H, clip_behavior=ft.ClipBehavior.HARD_EDGE)
        if mode.startswith("pinch"):
            self.control: ft.Control = ft.GestureDetector(
                stack, on_scale_start=self.scale_start, on_scale_update=self.scale
            )
        else:
            self.control = ft.GestureDetector(
                stack,
                drag_interval=interval,
                on_pan_update=self.pan,
                on_pan_end=self.pan_end,
                on_scroll=self.wheel,
            )

    # Each event changes the view, then either redraws at once or leaves it to the redraw task.
    def seen(self) -> None:
        now = time.perf_counter()
        if not self.events:
            self.first = now
        self.events += 1
        self.last_event = now

    def after(self) -> None:
        if "coalesced" in self.mode:
            if not self.dirty.is_set():
                self.pending = time.perf_counter()
            self.dirty.set()
        else:
            self.redraw()

    def pan(self, e: ft.DragUpdateEvent) -> None:
        self.seen()
        d = e.local_delta
        if d is None:
            return
        if self.mode == "pan_translate":
            self.shift = (self.shift[0] + d.x, self.shift[1] + d.y)
            self.canvas.left, self.canvas.top = self.shift
            t = time.perf_counter()
            self.canvas.update()
            self.done(t)
            return
        self.move(d.x, d.y)
        self.after()

    def pan_end(self, e: ft.DragEndEvent) -> None:
        if self.mode == "pan_translate":
            self.move(*self.shift)
            self.shift = (0.0, 0.0)
            self.canvas.left = self.canvas.top = 0
            self.redraw()

    def move(self, dx: float, dy: float) -> None:
        x0, x1, y0, y1 = self.view
        ux, uy = dx * (x1 - x0) / W, dy * (y1 - y0) / H
        self.view = (x0 - ux, x1 - ux, y0 + uy, y1 + uy)

    def zoom(self, base: View, factor: float, fx: float, fy: float) -> None:
        x0, x1, y0, y1 = base
        cx, cy = x0 + fx / W * (x1 - x0), y1 - fy / H * (y1 - y0)
        self.view = (
            cx - (cx - x0) / factor,
            cx + (x1 - cx) / factor,
            cy - (cy - y0) / factor,
            cy + (y1 - cy) / factor,
        )

    def scale_start(self, e: ft.ScaleStartEvent) -> None:
        self.start_view = self.view

    def scale(self, e: ft.ScaleUpdateEvent) -> None:
        self.seen()
        p = e.local_focal_point
        self.zoom(self.start_view, max(e.scale, 0.05), p.x, p.y)
        self.after()

    def wheel(self, e: ft.ScrollEvent) -> None:
        self.seen()
        p = e.local_position
        self.zoom(self.view, math.exp(-e.scroll_delta.y / 500), p.x, p.y)
        self.after()

    def redraw(self) -> None:
        t = time.perf_counter()
        self.canvas.shapes = curve_shapes(self.view, self.n)
        self.canvas.update()
        self.done(t)

    def done(self, t: float) -> None:
        self.last_done = time.perf_counter()
        self.draws.append((self.last_done - t) * 1000)

    async def redraw_task(self) -> None:
        while not self.closed:
            await self.dirty.wait()
            self.dirty.clear()
            if not self.closed:
                self.waits.append((time.perf_counter() - self.pending) * 1000)
                self.redraw()
            await asyncio.sleep(0)


PHASES = (
    ("pan_each_event", 2000, 0),
    ("pan_each_event", 640, 0),
    ("pan_each_event_interval33", 2000, 33),
    ("pan_coalesced", 2000, 0),
    ("pan_coalesced", 640, 0),
    ("pan_translate", 2000, 0),
    ("pinch_each_event", 640, 0),
    ("pinch_coalesced", 640, 0),
    ("wheel_each_event", 640, 0),
    ("wheel_coalesced", 640, 0),
)


async def gestures(holder: ft.Container) -> None:
    for mode, n, interval in PHASES:
        name = f"{mode}_n{n}"
        plot = Plot(mode, n, interval)
        holder.content = plot.control
        holder.update()
        task = asyncio.create_task(plot.redraw_task())
        await asyncio.sleep(0.5)
        say(f"PHASE {name}")
        say(f"READY {name}")
        waited = time.perf_counter()
        while True:
            await asyncio.sleep(0.1)
            now = time.perf_counter()
            if plot.events and now - max(plot.last_event, plot.last_done) > 1.0:
                break
            if not plot.events and now - waited > 20:
                break
        plot.closed = True
        plot.dirty.set()
        await task
        if not plot.draws:
            say(f"RESULT gesture {name}: events={plot.events} no redraws")
            continue
        say(
            f"RESULT gesture {name}: events={plot.events} redraws={len(plot.draws)} "
            f"redraw_med={statistics.median(plot.draws):.1f}ms redraw_max={max(plot.draws):.1f}ms "
            f"span={(plot.last_done - plot.first) * 1000:.0f}ms "
            f"behind_at_end={(plot.last_done - plot.last_event) * 1000:.0f}ms"
            + (f" wait_med={statistics.median(plot.waits):.1f}ms" if plot.waits else "")
        )


async def main(page: ft.Page) -> None:
    page.padding = 0
    holder = ft.Container(width=W, height=H)
    page.add(holder)
    await asyncio.sleep(1)
    say("START")
    try:
        await sampling()
        canvas = cv.Canvas([], width=W, height=H)
        holder.content = canvas
        holder.update()
        await frames(canvas)
        await gestures(holder)
    except Exception as error:
        say(f"ERROR {error!r}")
    say("DONE")


ft.run(main)
