"""Spike B demo: LaTeX row above our own box-layout row, same size, editable cursor.

Keys: 1/2/3 choose an expression; Left/Right/Up/Down move the cursor (editor semantics); Shift+Left/
Right select; M toggles a 1 px marker at every computed gap; C toggles one Text per character
(to compare with merged runs); B repeats the first draw 5 times and logs timings. Click places the
cursor via Layout.hit. Timings go to spikes/math_render_b/timings.log.

Run: uv run python spikes/math_render_b/app.py server 8570   (then open http://127.0.0.1:8570/)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import flet as ft  # noqa: E402
from layout import Layout  # noqa: E402
from painter import count_controls, paint  # noqa: E402
from samples import EXPRESSIONS  # noqa: E402

from cassim.app.theme import DARK  # noqa: E402
from cassim.device.editor import Editor  # noqa: E402
from cassim.device.editor_ast import row_from_text  # noqa: E402
from cassim.devices.nspire.ui.entry import EntryLine  # noqa: E402
from cassim.devices.nspire.ui.views import math  # noqa: E402

SIZE = 20.0
THEME = DARK
LOG = HERE / "timings.log"
# page coordinates (everything is absolutely positioned so a screenshot can be analysed)
LATEX_Y, MINE_Y, PAD = 50, 185, 10


def log(msg: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def make_editor(index: int) -> Editor:
    e = Editor()
    e.root = row_from_text(EXPRESSIONS[index])
    e.path, e.pos = [], 0
    for _ in range((7, 9, 5)[index]):
        e.right()
    return e


def main(page: ft.Page) -> None:
    page.padding = 0
    page.bgcolor = "#2b2f36"
    state = {"i": 0, "markers": False, "per_char": False}
    editor = make_editor(0)
    layout: Layout = Layout(editor.root, SIZE)

    latex_holder = ft.Container(left=PAD, top=LATEX_Y + PAD)
    base = ft.Stack(width=700, height=100)
    caret = ft.Container(width=1.5, height=20, bgcolor=THEME.accent, left=0, top=0)
    sel = ft.Container(width=0, height=0, bgcolor="#7fb2e8", opacity=0.5, left=0, top=0)
    marks = ft.Stack(width=700, height=100)
    overlay = ft.Stack([sel, caret, marks], width=700, height=100)
    info = ft.Text("", left=PAD, top=MINE_Y + 120, color="#f2f4f7", size=13)

    def on_tap(e: ft.TapEvent) -> None:
        pos = e.local_position
        path, p = layout.hit(pos.x, pos.y)
        editor.place(list(path), p)
        update_overlay()

    gestures = ft.GestureDetector(
        ft.Stack([base, overlay], width=700, height=100),
        on_tap_down=on_tap,
        left=PAD,
        top=MINE_Y + PAD,
    )

    def build_latex() -> None:
        latex_holder.content = math(editor.latex(cursor=False), THEME, SIZE)

    def draw() -> float:
        nonlocal layout
        t0 = time.perf_counter()
        layout = Layout(editor.root, SIZE)
        t1 = time.perf_counter()
        base.controls = paint(layout, THEME.screen_text, per_char=state["per_char"])
        base.width = overlay.width = max(layout.width, 700)
        base.height = overlay.height = layout.height
        update_overlay(push=False)
        build_latex()
        page.update()
        t2 = time.perf_counter()
        log(
            f"draw expr={state['i'] + 1} layout_ms={(t1 - t0) * 1000:.2f}"
            f" build+update_ms={(t2 - t1) * 1000:.2f} controls={count_controls(base)}"
        )
        return t2 - t0

    def update_overlay(*, push: bool = True) -> None:
        t0 = time.perf_counter()
        x, top, bot = layout.caret(editor.path, editor.pos)
        caret.left, caret.top, caret.height = x - 0.75, top, bot - top
        low, high = editor.span
        rects = layout.selection_rects(editor.path, low, high)
        if rects:
            rx, rt, rw, rh = rects[0]
            sel.left, sel.top, sel.width, sel.height = rx, rt, rw, rh
        else:
            sel.width = sel.height = 0
        marks.controls = []
        if state["markers"]:
            for r in layout.rows.values():
                marks.controls.extend(
                    ft.Container(left=g - 0.5, top=r.top, width=1, height=r.bot - r.top, bgcolor="#e00000")
                    for g in r.gaps
                )
        info.value = f"expr {state['i'] + 1}  path={editor.path} pos={editor.pos} span={editor.span}"
        if push:
            overlay.update()
            info.update()
            log(f"overlay_ms={(time.perf_counter() - t0) * 1000:.2f}")

    def on_key(e: ft.KeyboardEvent) -> None:
        nonlocal editor
        k = e.key.lower().replace(" ", "")
        if k in ("1", "2", "3"):
            state["i"] = int(k) - 1
            editor = make_editor(state["i"])
            draw()
            return
        if k == "m":
            state["markers"] = not state["markers"]
            update_overlay()
            return
        if k == "c":
            state["per_char"] = not state["per_char"]
            draw()
            return
        if k == "b":
            for _ in range(5):
                draw()
            return
        moves = {
            "arrowleft": (editor.left, editor.select_left),
            "arrowright": (editor.right, editor.select_right),
            "arrowup": (editor.up, editor.up),
            "arrowdown": (editor.down, editor.down),
        }
        if k in moves:
            (moves[k][1] if e.shift else moves[k][0])()
            update_overlay()

    page.on_keyboard_event = on_key
    labels = [
        ft.Text("Spike B: LaTeX (flutter_math) above, our box layout below", left=PAD, top=8, color="#f2f4f7"),
        ft.Text("LaTeX row (ft.Markdown, current drawing)", left=PAD, top=LATEX_Y - 18, size=11, color="#a6d2ff"),
        ft.Text("Box layout as positioned Text controls", left=PAD, top=MINE_Y - 18, size=11, color="#a6d2ff"),
    ]
    page.add(
        ft.Stack(
            [
                ft.Container(left=0, top=LATEX_Y, width=1000, height=110, bgcolor=THEME.screen),
                ft.Container(left=0, top=MINE_Y, width=1000, height=110, bgcolor=THEME.screen),
                latex_holder,
                gestures,
                info,
                *labels,
            ],
            width=1000,
            height=400,
        )
    )
    draw()


def entry_line_controls(index: int) -> int:
    """Controls EntryLine builds for the same tree."""
    e = make_editor(index)
    return count_controls(EntryLine(THEME, SIZE, lambda _p, _i: None).build(e))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "server":
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=int(sys.argv[2]))
