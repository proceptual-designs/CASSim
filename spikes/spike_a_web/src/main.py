"""Spike A (decision 0031): page switching and spreadsheet grid drawing in Flet.

Three views are built: a Calculator history (30 entry and result rows), a spreadsheet grid over a
2,500-row model, and a graph with three 2,000-point curves.

1. Switching. Two ways to change page are timed over the same cycle of views:
   `visible`: all three stay in a Stack and only `visible` changes (a kept-alive view);
   `rebuild`: the page's content is replaced by a newly built view each time (as today).
2. The grid. Three ways to draw the visible cells, at Handheld size (4 x 5 cells) and Computer
   size (10 x 20), are timed for a cursor move and for a one-row scroll (every cell text changes):
   `canvas`: one canvas `Text` shape per cell;
   `columns`: one multi-line canvas `Text` per column;
   `controls`: a pooled `ft.Text` control per cell.

Times are the Python side of `update()` plus one event-loop yield (diff, serialise, send), as in
spike 3. The runner samples requestAnimationFrame for the browser side.
"""

import asyncio
import math
import statistics
import time

import flet as ft
import flet.canvas as cv

W, H = 640, 480
ROWS = 2500
STEPS = 30
ROW_H = 22
HEAD_W = 40
INK = ft.Colors.BLACK
RULE = ft.Paint(color=ft.Colors.GREY_400, stroke_width=1, style=ft.PaintingStyle.STROKE)
CURSOR = ft.Paint(color=ft.Colors.BLUE, stroke_width=2, style=ft.PaintingStyle.STROKE)
STYLE = ft.TextStyle(size=13, color=INK)


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def cell(row: int, col: int) -> str:
    return f"{((row * 37 + col * 11) % 1000) / 7:.4f}"


# ---- the three views --------------------------------------------------------------------------


def history_view() -> ft.Control:
    rows: list[ft.Control] = []
    for i in range(30):
        rows.append(
            ft.Row(
                [
                    ft.Text(f"solve(x^2-{i}=0,x)", size=14),
                    ft.Text(f"x=-√({i}) or x=√({i})", size=14),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )
    return ft.Column(rows, width=W, height=H, scroll=ft.ScrollMode.AUTO, spacing=2)


def curve_shapes(shift: float) -> list[cv.Shape]:
    shapes: list[cv.Shape] = []
    for k, colour in enumerate((ft.Colors.BLUE, ft.Colors.RED, ft.Colors.GREEN)):
        pts = []
        for i in range(2000):
            x = -6 + shift + 12 * i / 1999
            y = math.sin(x + k) + 0.3 * math.sin(7 * x)
            pts.append((W * i / 1999, H / 2 - y * H / 5))
        paint = ft.Paint(color=colour, stroke_width=2, style=ft.PaintingStyle.STROKE)
        shapes.append(cv.Points(pts, point_mode=cv.PointMode.POLYGON, paint=paint))
    return shapes


def graph_view() -> cv.Canvas:
    return cv.Canvas(curve_shapes(0.0), width=W, height=H)


class Grid:
    """The visible window of the sheet, drawn one of three ways."""

    def __init__(self, kind: str, cols: int, rows: int) -> None:
        self.kind, self.cols, self.rows = kind, cols, rows
        self.col_w = (W - HEAD_W) / cols
        self.top = 0
        self.cursor = (0, 0)
        self.texts: list[list[ft.Text]] = []
        if kind == "controls":
            self.texts = [
                [
                    ft.Text(cell(r, c), size=13, width=self.col_w - 4, no_wrap=True)
                    for c in range(cols)
                ]
                for r in range(rows)
            ]
            self.heads = [ft.Text(str(r + 1), size=13, width=HEAD_W) for r in range(rows)]
            self.box = ft.Container(
                width=self.col_w,
                height=ROW_H,
                border=ft.Border.all(2, ft.Colors.BLUE),
                left=HEAD_W,
                top=0,
            )
            lines = [
                ft.Row([self.heads[r], *self.texts[r]], spacing=4, height=ROW_H)
                for r in range(rows)
            ]
            self.control: ft.Control = ft.Stack(
                [ft.Column(lines, spacing=0), self.box], width=W, height=rows * ROW_H
            )
        else:
            self.control = cv.Canvas(self.shapes(), width=W, height=rows * ROW_H)

    def shapes(self) -> list[cv.Shape]:
        out: list[cv.Shape] = []
        for r in range(self.rows + 1):
            out.append(cv.Line(0, r * ROW_H, W, r * ROW_H, paint=RULE))
        for c in range(self.cols + 1):
            x = HEAD_W + c * self.col_w
            out.append(cv.Line(x, 0, x, self.rows * ROW_H, paint=RULE))
        if self.kind == "canvas":
            for r in range(self.rows):
                out.append(cv.Text(2, r * ROW_H + 3, str(self.top + r + 1), style=STYLE))
                for c in range(self.cols):
                    out.append(
                        cv.Text(
                            HEAD_W + c * self.col_w + 3,
                            r * ROW_H + 3,
                            cell(self.top + r, c),
                            style=STYLE,
                        )
                    )
        else:  # one multi-line text per column; the line height is set to the row height
            style = ft.TextStyle(size=13, color=INK, height=ROW_H / 13)
            heads = "\n".join(str(self.top + r + 1) for r in range(self.rows))
            out.append(cv.Text(2, 0, heads, style=style))
            for c in range(self.cols):
                column = "\n".join(cell(self.top + r, c) for r in range(self.rows))
                out.append(cv.Text(HEAD_W + c * self.col_w + 3, 0, column, style=style))
        r, c = self.cursor
        out.append(cv.Rect(HEAD_W + c * self.col_w, r * ROW_H, self.col_w, ROW_H, paint=CURSOR))
        return out

    def move(self, step: int) -> None:
        self.cursor = (step % self.rows, (step // self.rows) % self.cols)
        if self.kind == "controls":
            self.box.top = self.cursor[0] * ROW_H
            self.box.left = HEAD_W + self.cursor[1] * self.col_w
        else:
            assert isinstance(self.control, cv.Canvas)
            self.control.shapes = self.shapes()

    def scroll(self, top: int) -> None:
        self.top = top % (ROWS - self.rows)
        if self.kind == "controls":
            for r in range(self.rows):
                self.heads[r].value = str(self.top + r + 1)
                for c in range(self.cols):
                    self.texts[r][c].value = cell(self.top + r, c)
        else:
            assert isinstance(self.control, cv.Canvas)
            self.control.shapes = self.shapes()


# ---- timing -----------------------------------------------------------------------------------


async def step(change, target: ft.Control | ft.Page) -> tuple[float, float]:
    t0 = time.perf_counter()
    change()
    t1 = time.perf_counter()
    target.update()
    await asyncio.sleep(0)
    return (t1 - t0) * 1000, (time.perf_counter() - t1) * 1000


def report(name: str, times: list[tuple[float, float]], seconds: float) -> None:
    build = [b for b, _ in times]
    update = [u for _, u in times]
    say(
        f"RESULT {name} steps={len(times)} build_med={statistics.median(build):.1f}ms "
        f"update_med={statistics.median(update):.1f}ms update_max={max(update):.1f}ms "
        f"per_step={seconds * 1000 / len(times):.1f}ms"
    )


async def grids(holder: ft.Container) -> None:
    for cols, rows, label in ((4, 5, "handheld"), (10, 20, "computer")):
        for kind in ("canvas", "columns", "controls"):
            say(f"PHASE grid_{kind}_{label}")
            grid = Grid(kind, cols, rows)
            holder.content = grid.control
            holder.update()
            await asyncio.sleep(0.5)
            for action in ("move", "scroll"):
                t = time.perf_counter()
                fn = grid.move if action == "move" else grid.scroll
                times = [
                    await step(lambda k=k, fn=fn: fn(k + 1), grid.control) for k in range(STEPS)
                ]
                report(f"grid {kind} {label} {action}", times, time.perf_counter() - t)
                await asyncio.sleep(0.2)


async def switching(holder: ft.Container) -> None:
    def sheet() -> ft.Control:
        return Grid("columns", 10, 20).control

    builders = [history_view, sheet, graph_view]
    views = [build() for build in builders]
    for i, view in enumerate(views):
        view.visible = i == 0
    holder.content = ft.Stack(views, width=W, height=H)
    holder.update()
    await asyncio.sleep(0.5)

    say("PHASE switch_visible")
    current = 0

    def show(index: int) -> None:
        nonlocal current
        views[current].visible = False
        views[index].visible = True
        current = index

    t = time.perf_counter()
    times = [await step(lambda k=k: show((k + 1) % 3), holder) for k in range(STEPS)]
    report("switch visible", times, time.perf_counter() - t)
    for target, name in ((0, "history"), (1, "sheet"), (2, "graph")):
        show((target + 1) % 3)
        holder.update()
        await asyncio.sleep(0.1)
        one = [await step(lambda target=target: show(target), holder)]
        report(f"switch visible to_{name}", one, sum(one[0]) / 1000)

    # The same, but only the two views that changed are diffed and sent.
    say("PHASE switch_visible_targeted")

    async def flip(index: int) -> tuple[float, float]:
        before = views[current]
        t0 = time.perf_counter()
        show(index)
        t1 = time.perf_counter()
        before.update()
        views[index].update()
        await asyncio.sleep(0)
        return (t1 - t0) * 1000, (time.perf_counter() - t1) * 1000

    t = time.perf_counter()
    times = [await flip((k + 1) % 3) for k in range(STEPS)]
    report("switch visible_targeted", times, time.perf_counter() - t)
    for target, name in ((0, "history"), (1, "sheet"), (2, "graph")):
        await flip((target + 1) % 3)
        await asyncio.sleep(0.1)
        one = [await flip(target)]
        report(f"switch visible_targeted to_{name}", one, sum(one[0]) / 1000)

    say("PHASE switch_rebuild")

    def rebuild(index: int) -> None:
        holder.content = builders[index]()

    t = time.perf_counter()
    times = [await step(lambda k=k: rebuild((k + 1) % 3), holder) for k in range(STEPS)]
    report("switch rebuild", times, time.perf_counter() - t)
    for target, name in ((0, "history"), (1, "sheet"), (2, "graph")):
        one = [await step(lambda target=target: rebuild(target), holder)]
        report(f"switch rebuild to_{name}", one, sum(one[0]) / 1000)

    # A kept-alive graph that changed while hidden: redraw on arrival.
    say("PHASE switch_visible_stale_graph")
    holder.content = ft.Stack(views, width=W, height=H)
    holder.update()
    await asyncio.sleep(0.3)
    graph = views[2]
    assert isinstance(graph, cv.Canvas)

    def arrive(k: int) -> None:
        graph.shapes = curve_shapes(0.1 * k)
        show(2)

    times = []
    t = time.perf_counter()
    for k in range(10):
        show(0)
        holder.update()
        await asyncio.sleep(0.05)
        times.append(await step(lambda k=k: arrive(k), holder))
    report("switch visible to_graph resampled", times, time.perf_counter() - t)


async def main(page: ft.Page) -> None:
    holder = ft.Container(width=W, height=H)
    page.add(ft.Text("spike A"), holder)
    await asyncio.sleep(1)
    say("START")
    for part in (grids, switching):
        try:
            await part(holder)
        except Exception as error:
            say(f"ERROR {part.__name__} {error!r}")
    say("DONE")


ft.run(main)
