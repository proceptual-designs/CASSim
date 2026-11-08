"""Fixtures for browser tests: build a Flet static site, serve it, drive Edge/Chromium."""

import functools
import http.server
import os
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Error, sync_playwright
from tools import publish, webharness

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Use the installed Edge (no download), else Playwright's Chromium, else skip."""
    with sync_playwright() as p:
        for channel in ("msedge", "chrome", None):
            try:
                b = p.chromium.launch(headless=True, channel=channel)
            except Error:
                continue
            yield b
            b.close()
            return
    pytest.skip("no Chromium-family browser available")


@pytest.fixture(scope="session")
def build(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str], Path]:
    """Return a function that publishes a spike app once per session and serves it."""
    cache: dict[str, Path] = {}

    def _build(name: str) -> Path:
        if name not in cache:
            dist = tmp_path_factory.mktemp(f"dist-{name}")
            webharness.publish(ROOT / "spikes" / name, dist)
            cache[name] = dist
        return cache[name]

    return _build


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


@pytest.fixture(scope="session")
def site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, str]]:
    dist = tmp_path_factory.mktemp("pwa") / "dist"
    publish.build(dist, BASE)
    handler = functools.partial(PagesHandler, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield dist, f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
    server.shutdown()
