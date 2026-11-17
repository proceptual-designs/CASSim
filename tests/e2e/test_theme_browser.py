# Requirements traced here: FR-THEME-001, FR-THEME-002
"""Appearance editing and recovery in the built site."""

import io
import json
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import Browser
from test_flows_browser import AppPage

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("offline", [False, True])
def test_saved_custom_theme_is_applied_after_reload(
    browser: Browser, site: tuple[Path, str], offline: bool
) -> None:
    context = browser.new_context(viewport={"width": 1100, "height": 700})
    app = AppPage(context.new_page(), site[1])
    app.wait(lambda: "CASSIM: ENGINE READY" in app.logs, "ENGINE READY")
    if offline:
        app.page.wait_for_function(
            "document.getElementById('cassim-offline').dataset.state === 'ready'", timeout=150000
        )
        context.set_offline(True)
    for key in ("F4", "7", "3"):  # Doc > Settings & Status > Handheld Setup
        app.page.keyboard.press(key)
        app.page.wait_for_timeout(300)
    app.page.locator("flt-semantics-placeholder").evaluate("(element) => element.click()")
    app.page.get_by_role("button", name="Appearance…").focus()
    app.page.keyboard.press("Enter")
    app.page.wait_for_timeout(800)
    app.page.mouse.click(600, 150)  # Theme dropdown
    app.page.wait_for_timeout(500)
    app.page.mouse.click(450, 265)  # Light
    background = app.page.get_by_label("Background", exact=True)

    def swatch_is(colour: tuple[int, int, int]) -> bool:
        box = background.bounding_box()
        if box is None:
            return False
        image = Image.open(io.BytesIO(app.page.screenshot())).convert("RGB")
        return image.getpixel((int(box["x"] + box["width"] + 28), int(box["y"] + 20))) == colour

    app.wait(lambda: swatch_is((241, 243, 245)), "Light preset to load")
    background.fill("#e7e8e9")
    app.wait(lambda: swatch_is((231, 232, 233)), "custom background swatch")
    app.page.get_by_role("button", name="Save", exact=True).focus()
    app.page.keyboard.press("Enter")
    app.page.wait_for_timeout(1500)
    stored = app.page.evaluate("""() => new Promise((resolve, reject) => {
        const request = indexedDB.open('cassim');
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const read = request.result.transaction('texts').objectStore('texts')
                .get('cassim.system');
            read.onsuccess = () => resolve(read.result);
            read.onerror = () => reject(read.error);
        };
    })""")
    settings = json.loads(stored)
    assert settings["theme_name"] == "Light"
    assert settings["theme_overrides"]["Light"]["background"] == "#e7e8e9"
    app.page.reload()
    app.wait(lambda: app.logs.count("CASSIM: READY") >= 2, "READY after reload")
    app.page.wait_for_timeout(500)
    screenshot = Image.open(io.BytesIO(app.page.screenshot()))
    assert screenshot.convert("RGB").getpixel((4, 4)) == (231, 232, 233)
    context.close()
