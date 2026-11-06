"""Drive the running app in headless Edge and save screenshots.

Start the app without opening a browser (`flet run --web` always opens one):
    FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=8560 python src/cassim/app/main.py
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "testing" / "app-shots"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8560/"


def press_all(page, keys):  # noqa: ANN001, ANN201
    """Press space-separated Playwright keys (typed text sends no Shift, so symbols need this)."""
    for key in keys.split():
        page.keyboard.press(key)
        page.wait_for_timeout(120)


def shoot(page, name):  # noqa: ANN001, ANN201
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / f"{name}.png"))


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1100, "height": 650})
    logs: list[str] = []
    page.on("console", lambda m: logs.append(m.text))
    page.goto(URL, wait_until="load")
    for _ in range(60):
        if any("CASSIM: READY" in x for x in logs):
            break
        page.wait_for_timeout(500)
    page.mouse.click(700, 300)
    shoot(page, "computer-0-start")
    for _ in range(9):  # fill the page so the scroll behaviour shows
        press_all(page, "f Shift+9 x Shift+0 Shift+Semicolon Equal x Shift+6 2 Enter")
        press_all(page, "f Shift+9 3 Shift+0 Enter")
    press_all(page, "2 Control+Slash 3")
    shoot(page, "computer-1-history")
    page.keyboard.type("x+")
    page.keyboard.press("Enter")
    shoot(page, "computer-2-error-or-result")
    phone = browser.new_context(viewport={"width": 420, "height": 820}).new_page()
    logs.clear()
    phone.on("console", lambda m: logs.append(m.text))
    phone.goto(URL, wait_until="load")
    for _ in range(60):
        if any("CASSIM: READY" in x for x in logs):
            break
        phone.wait_for_timeout(500)
    phone.mouse.click(55, 28)
    shoot(phone, "handheld-0-start")
    # Keypad: 5 keys across from x=85, 62 px pitch; rows from y=328, 48 px pitch.
    for col, row in [(0, 5), (0, 0), (4, 2), (2, 5), (4, 6), (2, 3), (0, 2), (0, 0), (0, 0)]:
        phone.mouse.click(85 + 62 * col, 328 + 48 * row)
        phone.wait_for_timeout(350)
    shoot(phone, "handheld-1-keys")
    print("\n".join(x for x in logs if "rror" in x or "width" in x))
    browser.close()
