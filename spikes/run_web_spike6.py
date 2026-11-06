"""Run spike 6 (template editor in Flet web): type key sequences in Edge, screenshot each state."""

import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import webharness  # noqa: E402

OUT = ROOT / "spikes" / "spike6_web" / "shots"
OUT.mkdir(exist_ok=True)

# (name, keys). Playwright key names; "Shift+6" is ^ on a US keyboard.
SEQUENCES = [
    ("frac", ["1", "Slash", "3", "ArrowRight", "Shift+Equal", "1", "Slash", "4"]),
    ("power-sqrt", ["2", "Shift+6", "3", "ArrowRight", "Shift+Equal", "1"]),
    ("nested", ["2", "Slash", "3", "ArrowDown", "ArrowUp", "ArrowLeft", "Backspace"]),
]

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    dist = Path(tmp)
    webharness.publish(ROOT / "spikes" / "spike6_web", dist)
    browser = p.chromium.launch(channel="msedge", headless=True)
    with webharness.serve(dist) as url:
        for name, keys in SEQUENCES:
            ctx = browser.new_context(viewport={"width": 500, "height": 220})
            page = ctx.new_page()
            lines: list[str] = []
            page.on("console", lambda m, lines=lines: lines.append(m.text))
            page.goto(url, wait_until="load")
            for _ in range(240):
                if "SPIKE: READY" in lines:
                    break
                page.wait_for_timeout(500)
            page.mouse.click(250, 150)
            for k in keys:
                page.keyboard.press(k)
                page.wait_for_timeout(300)
            page.wait_for_timeout(800)
            page.screenshot(path=str(OUT / f"{name}.png"))
            print(f"--- {name}")
            for x in lines:
                if x.startswith("SPIKE: KEY") or x.startswith("SPIKE: STATE") or "rror" in x:
                    print(x)
            ctx.close()
    browser.close()
