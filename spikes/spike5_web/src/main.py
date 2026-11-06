"""Spike 5 (M2 spike A): render engine LaTeX through Flet's native Markdown LaTeX support.

Phase 1 shows every engine sample. Phase 2 adds 200 matrices and reports the Python-side build
time; the browser harness measures frames.
"""

import asyncio
import json
import time
from pathlib import Path

import flet as ft

MD = ft.MarkdownExtensionSet.GITHUB_WEB


def for_markdown(tex: str) -> str:
    """Same as `cassim.core.format.latex_for_markdown`."""
    return tex.replace("\\\\", r"\cr ")


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def formula(tex: str) -> ft.Markdown:
    return ft.Markdown(f"$${for_markdown(tex)}$$", extension_set=MD)


async def main(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.DARK
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=2)
    page.add(column)
    for c in cases:
        if c["latex"]:
            column.controls += [ft.Text(c["in"], size=11), formula(c["latex"])]
    page.update()
    say("SAMPLES")
    await asyncio.sleep(3)
    matrix = next(c["latex"] for c in cases if "bmatrix" in c["latex"])
    column.controls.clear()
    say("STRESS_START")
    t = time.perf_counter()
    column.controls += [formula(matrix) for _ in range(200)]
    page.update()
    say(f"STRESS_BUILD {(time.perf_counter() - t) * 1000:.0f}ms")
    await asyncio.sleep(3)
    say("DONE")


ft.run(main)
