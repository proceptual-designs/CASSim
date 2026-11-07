"""Click inside the entry line of the running app and save screenshots (decision 0019).

Start the app without opening a browser, on a fresh port (server state persists between runs):
    FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=8560 python src/cassim/app/main.py
Then: python tools/app_click_shots.py http://localhost:8560/ [SCENARIO]

Each scenario builds an entry, then clicks at fixed pixel positions (the layout is deterministic
at this viewport) and stacks one cropped screenshot per click into
docs/testing/app-shots/2d-click-NAME.png. The cursor in each strip should be where the click was.
"""

import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "testing" / "app-shots"

COMPUTER = (194, 73, 400, 90)  # entry strip of the Computer view: x, y, width, height
HANDHELD = (390, 72, 320, 70)
# Toolbar chips and handheld keys that Playwright presses by position.
CLICKS = {"@menu": (645, 27), "@handheld": (36, 27), "@ctrl": (426, 380), "@square": (426, 476)}

type Scenario = tuple[tuple[int, int, int, int], str, list[tuple[int, int, bool]]]
# name: (view strip, keys that build the entry, [(click x, click y, shift held)])
SCENARIOS: dict[str, Scenario] = {
    # 5+7/8+98765: before the 5, numerator right half, denominator left half, between digits,
    # on the fraction bar, past the end of the row, then a shift+click selection
    "fraction-row": (
        COMPUTER,
        "5 Shift+Equal 7 Control+Slash 8 ArrowRight Shift+Equal 9 8 7 6 5",
        [
            (203, 106, False),
            (236, 89, False),
            (230, 123, False),
            (262, 106, False),
            (236, 113, False),
            (600, 106, False),
            (203, 106, False),
            (270, 106, True),
        ],
    ),
    # x^(1/2)+sqrt(57)+3: start, exponent numerator, exponent denominator, radicand, radical sign,
    # past the end, then shift+click from the exponent to the radicand
    "power-root": (
        HANDHELD,
        "@handheld x Shift+6 1 Control+Slash 2 ArrowRight ArrowRight Shift+Equal "
        "@ctrl @square 5 7 ArrowRight Shift+Equal 3",
        [
            (401, 113, False),
            (413, 86, False),
            (414, 113, False),
            (454, 113, False),
            (440, 113, False),
            (600, 113, False),
            (413, 86, False),
            (454, 113, True),
        ],
    ),
    # [1 2; 3 4]+3: each cell, the bracket, past the end, shift+click from cell 3 to cell 2
    "matrix": (
        COMPUTER,
        "@menu 6 1 1 Tab 2 Tab 3 Tab 4 Tab Shift+Equal 3",
        [
            (214, 118, False),
            (243, 89, False),
            (238, 118, False),
            (213, 89, False),
            (257, 100, False),
            (700, 100, False),
            (214, 118, False),
            (243, 89, True),
        ],
    ),
}


def press_all(page, keys):  # noqa: ANN001, ANN201
    for key in keys.split():
        if key in CLICKS:
            page.mouse.click(*CLICKS[key])
            page.wait_for_timeout(450)
            continue
        page.keyboard.press(key)
        page.wait_for_timeout(120)


def start(browser, url):  # noqa: ANN001, ANN201
    page = browser.new_page(viewport={"width": 1100, "height": 650})
    logs: list[str] = []
    page.on("console", lambda m: logs.append(m.text))
    page.goto(url, wait_until="load")
    for _ in range(60):
        if any("CASSIM: READY" in x for x in logs):
            break
        page.wait_for_timeout(500)
    page.mouse.click(700, 300)
    return page


def click(page, x, y, *, shift=False):  # noqa: ANN001, ANN201
    if shift:
        page.keyboard.down("Shift")
        page.wait_for_timeout(200)
    page.mouse.click(x, y)
    if shift:
        page.keyboard.up("Shift")
    page.wait_for_timeout(700)


def strip(page, view):  # noqa: ANN001, ANN201
    x, y, w, h = view
    path = OUT / "_strip.png"
    page.screenshot(path=str(path), clip={"x": x, "y": y, "width": w, "height": h})
    return Image.open(path).copy()


def stack(images, name):  # noqa: ANN001, ANN201
    width, height = images[0].size
    sheet = Image.new("RGB", (width, height * len(images)), "white")
    for i, image in enumerate(images):
        sheet.paste(image, (0, height * i))
    sheet.save(OUT / f"2d-click-{name}.png")
    (OUT / "_strip.png").unlink(missing_ok=True)


def run(url, only=None):  # noqa: ANN001, ANN201
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for name, (view, keys, clicks) in SCENARIOS.items():
            if only and name != only:
                continue
            page = start(browser, url)
            press_all(page, keys)
            page.wait_for_timeout(700)
            shots = [strip(page, view)]
            for x, y, shift in clicks:
                click(page, x, y, shift=shift)
                shots.append(strip(page, view))
            stack(shots, name)
            page.close()
        browser.close()


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
