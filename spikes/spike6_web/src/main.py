"""Spike 6: template editor model drawn with Flet's native LaTeX, driven by browser key events."""

import time

import flet as ft
from editor import Editor

ARROWS = {"Arrow Left": "L", "Arrow Right": "R", "Arrow Up": "U", "Arrow Down": "D"}
NAMED = {"Slash": "/", "Minus": "-", "Equal": "=", "Period": ".", "Asterisk": "*", "Plus": "+"}


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


async def main(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.DARK
    ed = Editor()
    view = ft.Markdown("$$\\square$$", extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
    linear = ft.Text("", font_family="monospace")
    page.add(view, linear)

    def show() -> None:
        tex = ed.latex().replace("\\\\", r"\cr ")
        view.value = f"$${tex}$$"
        linear.value = ed.linear()
        page.update()

    def on_key(e: ft.KeyboardEvent) -> None:
        t = time.perf_counter()
        say(f"KEY key={e.key!r} shift={e.shift} ctrl={e.ctrl}")
        if e.key in ARROWS:
            {"L": ed.left, "R": ed.right}.get(ARROWS[e.key], lambda: None)()
            if e.key == "Arrow Up":
                ed.vertical(up=True)
            if e.key == "Arrow Down":
                ed.vertical(up=False)
        elif e.key == "Backspace":
            ed.backspace()
        elif e.key in NAMED:
            ed.insert(NAMED[e.key])
        elif len(e.key) == 1:
            ed.insert(e.key if e.shift or not e.key.isalpha() else e.key.lower())
        else:
            return
        show()
        say(f"STATE {ed.linear()} | {(time.perf_counter() - t) * 1000:.0f}ms")

    page.on_keyboard_event = on_key
    say("READY")


ft.run(main)
