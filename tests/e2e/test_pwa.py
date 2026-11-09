# Requirements traced here: FR-PWA-003
"""The published site is installable and works offline (FR-PWA-001 to FR-PWA-004).

Builds the real site with `tools.publish` (needs network for the vendored packages the first time),
serves it below /CASSim/ as a GitHub Pages project site would, and drives it in a browser.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Page
from tools import publish

pytestmark = pytest.mark.e2e


def wait_for(page: Page, js: str, seconds: float = 240) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if page.evaluate(js):
            return True
        page.wait_for_timeout(500)
    return False


def test_manifest_and_icons(site: tuple[Path, str]) -> None:
    """FR-PWA-001: manifest names the app, is standalone, and its icons exist."""
    dist, _ = site
    manifest = json.loads((dist / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["display"] == "standalone"
    assert {"192x192", "512x512"} <= {i["sizes"] for i in manifest["icons"]}
    assert all((dist / i["src"]).is_file() for i in manifest["icons"])
    assert (dist / "favicon.png").is_file()  # the same artwork, linked by index.html
    html = (dist / "index.html").read_text(encoding="utf-8")
    assert html.count('rel="manifest"') == 1
    assert 'href="manifest.webmanifest"' in html
    assert manifest["name"] == "CASSim"
    assert "<title>CASSim</title>" in html
    assert 'apple-mobile-web-app-title" content="CASSim"' in html
    assert not (dist / "manifest.json").exists()


def test_loads_and_works_offline(browser: Browser, site: tuple[Path, str]) -> None:
    """FR-PWA-002/003: boots with no external requests, then reloads with the network off."""
    dist, url = site
    ctx = browser.new_context()
    page = ctx.new_page()
    external: set[str] = set()
    missing: set[str] = set()
    errors: list[str] = []
    page.on(
        "request",
        lambda r: (
            external.add(urlparse(r.url).netloc)
            if not r.url.startswith(("http://127.0.0.1", "blob:", "data:"))
            else None
        ),
    )
    page.on("response", lambda r: missing.add(r.url) if r.status == 404 else None)
    page.on(
        "console",
        lambda m: (
            errors.append(m.text[:300]) if "Traceback" in m.text or "init error" in m.text else None
        ),
    )
    page.goto(url, wait_until="load")
    assert page.locator("#cassim-splash").count() == 1  # the loading screen shows first
    assert wait_for(page, "!document.getElementById('cassim-splash')"), "app never started"
    page.wait_for_timeout(20000)  # the Python worker starts after the first frame
    assert not errors, errors
    assert (
        page.evaluate("getComputedStyle(document.getElementById('cassim-update')).display")
        == "none"
    )
    n = len(json.loads((dist / "precache.json").read_text(encoding="utf-8")))
    assert wait_for(
        page,
        "caches.keys().then(async k => k.length"
        " ? (await (await caches.open(k[0])).keys()).length : 0)"
        f".then(c => c >= {n})",
        120,
    ), "precache did not complete"
    page.reload(wait_until="load")
    page.wait_for_timeout(1500)
    assert page.evaluate("!!navigator.serviceWorker.controller")
    ctx.set_offline(True)
    page.reload(wait_until="load")
    assert wait_for(page, "!document.getElementById('cassim-splash')"), "offline reload failed"
    page.wait_for_timeout(20000)
    assert not errors, errors
    # Only the unused Rive wasm may be requested from outside (decision 0016).
    assert external <= {"cdn.jsdelivr.net"}, external
    assert not [m for m in missing if "rive" not in m], missing
    ctx.close()


def test_version_is_published(site: tuple[Path, str]) -> None:
    """FR-PWA-004: the build writes a version, and the worker's cache name carries it."""
    dist, _ = site
    version = json.loads((dist / "version.json").read_text(encoding="utf-8"))["version"]
    assert version.startswith(publish.project_version())
    assert f'"cassim-{version}"' in (dist / "flutter_service_worker.js").read_text(encoding="utf-8")
    assert "cassim-update" in (dist / "index.html").read_text(encoding="utf-8")


def test_cancel_ends_a_long_calculation_and_keeps_variables(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """The engine runs in its own worker: Esc terminates it and the state is rebuilt
    (decisions 0005 and 0016, NFR-PERF-004)."""
    _, url = site
    page = browser.new_page(viewport={"width": 1100, "height": 700})
    logs: list[str] = []
    page.on("console", lambda m: logs.append(m.text) if m.text.startswith("CASSIM:") else None)

    def count(word: str) -> int:
        return sum(word in line for line in logs)

    def wait(word: str, n: int = 1, seconds: float = 150) -> None:
        end = time.monotonic() + seconds
        while count(word) < n and time.monotonic() < end:
            page.wait_for_timeout(200)
        assert count(word) >= n, f"no {word!r} in {logs}"

    def enter(text: str) -> None:
        shifted = {"(": "Shift+9", ")": "Shift+0"}
        for char in text:
            if char in shifted:
                page.keyboard.press(shifted[char])
            else:
                page.keyboard.type(char)
        page.keyboard.press("Enter")

    page.goto(url + "#/debug", wait_until="load")
    wait("READY")
    page.mouse.click(600, 120)
    enter("a:=5")
    wait("RESULT", 1)
    enter("seq(k,k,1,99999999)")  # far too big to finish
    page.wait_for_timeout(2500)
    started = time.monotonic()
    page.keyboard.press("Escape")
    wait("CANCELLED", 1, 5)
    assert time.monotonic() - started < 1.5  # the run stops at once
    wait("RESTARTED", 1)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    enter("a+1")
    wait("RESULT", 2, 60)
    assert logs[-1] == "CASSIM: RESULT 6"  # the variable survived the engine's replacement
    page.close()


def test_install_and_fullscreen_go_through_the_page(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """FR-PWA-001: the app runs in a worker, so the page holds the install prompt and answers the
    app's requests over a BroadcastChannel."""
    _, url = site
    page = browser.new_page()
    page.goto(url, wait_until="load")
    result = page.evaluate(
        """async () => {
          const app = new BroadcastChannel('cassim');   // stands in for the Python worker
          const heard = [];
          app.onmessage = (m) => heard.push(m.data);
          const wait = () => new Promise((r) => setTimeout(r, 200));
          app.postMessage({op: 'hello'});
          await wait();
          let prompted = 0;
          const e = new Event('beforeinstallprompt', {cancelable: true});
          e.prompt = () => { prompted++; };
          window.dispatchEvent(e);
          await wait();
          const held = e.defaultPrevented;
          app.postMessage({op: 'install'});
          await wait();
          return {heard, held, prompted};
        }"""
    )
    assert result["held"]
    assert result["prompted"] == 1
    values = [m["value"] for m in result["heard"] if m["op"] == "installable"]
    assert values == [False, True, False]  # nothing offered, offered, used
    page.close()


@pytest.mark.parametrize("size", [(1280, 720), (390, 844), (844, 390)])
def test_no_view_needs_the_network_for_fonts(
    browser: Browser, site: tuple[Path, str], size: tuple[int, int]
) -> None:
    """FR-PWA-002: every glyph on the Computer and Handheld views comes from a vendored font, so
    nothing is fetched (and nothing 404s) while offline."""
    _, url = site
    context = browser.new_context(viewport={"width": size[0], "height": size[1]})
    page = context.new_page()
    missing: list[str] = []
    page.on("response", lambda r: missing.append(r.url) if r.status == 404 else None)
    page.goto(url, wait_until="load")
    assert wait_for(page, "!document.getElementById('cassim-splash')")
    page.wait_for_timeout(15000)
    assert not [m for m in missing if "rive" not in m], missing
    context.close()
