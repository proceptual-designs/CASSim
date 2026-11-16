"""Fixtures for browser tests: build a Flet static site, serve it, drive Edge/Chromium."""

import functools
import gzip
import http.server
import json
import os
import threading
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Error, sync_playwright
from tools import publish, webharness

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def _session_browser() -> Iterator[Browser]:
    """Use the installed Edge (no download), else Playwright's Chromium, else skip."""
    with sync_playwright() as p:
        for channel in ("msedge", "chrome", None):
            try:
                b = p.chromium.launch(headless=True, channel=channel)
            except Error:
                continue
            try:
                yield b
            finally:
                b.close()
            return
    if os.environ.get("CI"):
        pytest.fail("no Chromium-family browser available")
    pytest.skip("no Chromium-family browser available")


@pytest.fixture
def browser(_session_browser: Browser) -> Iterator[Browser]:
    """Close each test's contexts, including those created by browser.new_page()."""
    try:
        yield _session_browser
    finally:
        with ExitStack() as stack:
            for context in _session_browser.contexts:
                stack.callback(context.close)


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
    with patch.object(publish, "STAGE", tmp_path_factory.mktemp("stage") / "app"):
        publish.build(dist, BASE)
    handler = functools.partial(PagesHandler, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield dist, f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
    server.shutdown()


@pytest.fixture(scope="session")
def root_site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, str]]:
    dist = tmp_path_factory.mktemp("pwa-root") / "dist"
    with patch.object(publish, "STAGE", tmp_path_factory.mktemp("stage-root") / "app"):
        publish.build(dist, "")

    class RootHandler(PagesHandler):
        def translate_path(self, path: str) -> str:
            return http.server.SimpleHTTPRequestHandler.translate_path(self, path)

    handler = functools.partial(RootHandler, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield dist, f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture(params=["root_site", "site"], ids=["root", "subpath"])
def redirecting_site(request: pytest.FixtureRequest) -> Iterator[str]:
    """Serve the site with Cloudflare Pages' index.html-to-directory redirect."""
    dist, _ = request.getfixturevalue(request.param)
    prefix = "" if request.param == "root_site" else f"{BASE}/"

    class Handler(PagesHandler):
        def translate_path(self, path: str) -> str:
            if not prefix:
                return http.server.SimpleHTTPRequestHandler.translate_path(self, path)
            return super().translate_path(path)

        def do_GET(self) -> None:
            if urlparse(self.path).path == f"/{prefix}index.html":
                self.send_response(308)
                self.send_header("Location", f"/{prefix}")
                self.end_headers()
            elif urlparse(self.path).path == f"/{prefix}":
                content = gzip.compress((dist / "index.html").read_bytes())
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                super().do_GET()

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=str(dist))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/{prefix}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def failing_site(site: tuple[Path, str]) -> Iterator[tuple[str, list[str], Callable[[str], None]]]:
    """Serve the site, then simulate an outage, network filter or new worker."""
    dist, _ = site
    requests: list[str] = []
    failure = ""

    class Handler(PagesHandler):
        def do_GET(self) -> None:
            requests.append(urlparse(self.path).path)
            if failure == "error":
                self.send_error(503)
            elif failure == "block":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"Blocked by the network")
            elif failure in {"update", "update-broken", "update-interrupted"} and urlparse(
                self.path
            ).path.endswith("/flutter_service_worker.js"):
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript")
                self.end_headers()
                original = (dist / "flutter_service_worker.js").read_text(encoding="utf-8")
                version = json.loads((dist / "version.json").read_text(encoding="utf-8"))["version"]
                self.wfile.write(
                    original.replace(
                        f'CACHE_PREFIX + "{version}"', 'CACHE_PREFIX + "test-update"'
                    ).encode()
                )
            elif failure in {
                "install-broken",
                "update-broken",
                "install-interrupted",
                "update-interrupted",
            } and urlparse(self.path).path.endswith("/pyodide/python.bat"):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                if failure.endswith("interrupted"):
                    self.send_header("Content-Length", "4096")
                self.end_headers()
                self.wfile.write(b"incorrect content")
                self.close_connection = True
            else:
                super().do_GET()

    def fail(mode: str) -> None:
        nonlocal failure
        failure = mode

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=str(dist))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/{BASE}/", requests, fail
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
