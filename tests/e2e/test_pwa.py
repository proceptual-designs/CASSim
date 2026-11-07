"""The published site is installable and works offline (FR-PWA-001 to FR-PWA-004).

Builds the real site with `tools.publish` (needs network for the vendored packages the first time),
serves it below /CASSim/ as a GitHub Pages project site would, and drives it in a browser.
"""

from __future__ import annotations

import functools
import http.server
import json
import os
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Page
from tools import publish

pytestmark = pytest.mark.e2e

BASE = "CASSim"
TYPES = {
    ".mjs": "text/javascript",
    ".js": "text/javascript",
    ".wasm": "application/wasm",
    ".webmanifest": "application/manifest+json",
}


class PagesHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        p = urlparse(path).path
        if not p.startswith(f"/{BASE}/") and p != f"/{BASE}":
            return str(Path(self.directory) / "__missing__")
        return super().translate_path("/" + p.removeprefix(f"/{BASE}").lstrip("/"))

    def guess_type(self, path: str | os.PathLike[str]) -> str:
        return TYPES.get(Path(path).suffix, super().guess_type(path))

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, str]]:
    dist = tmp_path_factory.mktemp("pwa") / "dist"
    publish.build(dist, BASE)
    handler = functools.partial(PagesHandler, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield dist, f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
    server.shutdown()


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
    assert 'rel="manifest"' in (dist / "index.html").read_text(encoding="utf-8")


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
