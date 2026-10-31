"""Build, serve and drive a Flet static site in a real browser (Playwright).

Flet pages render to a canvas, so tests read results from ``print`` lines that the app
emits with a marker prefix (default ``SPIKE:``); they arrive as browser console messages.
"""

from __future__ import annotations

import functools
import http.server
import os
import subprocess
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import BrowserContext, Page

# Windows' registry can map these to the wrong type (e.g. .mjs as text/plain).
_TYPES = {".mjs": "text/javascript", ".js": "text/javascript", ".wasm": "application/wasm"}


class _Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path: str | os.PathLike[str]) -> str:
        """Return the MIME type, overriding the ones Windows' registry gets wrong."""
        return _TYPES.get(Path(path).suffix, super().guess_type(path))

    def log_message(self, format: str, *args: object) -> None:
        """Silence per-request logging."""


def publish(
    app_dir: Path, dist: Path, *, script: str = "src/main.py", no_cdn: bool = False
) -> None:
    """Run ``flet publish`` for the app in ``app_dir`` into ``dist``."""
    flet = Path(sys.executable).with_name("flet.exe" if sys.platform == "win32" else "flet")
    cmd = [str(flet), "publish", script, "--distpath", str(dist)]
    if no_cdn:
        cmd.append("--no-cdn")
    done = subprocess.run(cmd, cwd=app_dir, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        msg = f"flet publish failed:\n{done.stdout}\n{done.stderr}"
        raise RuntimeError(msg)


@contextmanager
def serve(root: Path) -> Generator[str]:
    """Serve ``root`` on a free localhost port; yield the base URL."""
    handler = functools.partial(_Handler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


@dataclass
class PageRun:
    """Console output and timing from one page visit."""

    lines: list[str] = field(default_factory=list)
    seconds: float = 0.0
    finished: bool = False

    def markers(self, prefix: str = "SPIKE: ") -> list[str]:
        """Return marker lines with the prefix stripped."""
        return [x.removeprefix(prefix) for x in self.lines if x.startswith(prefix)]

    def find(self, text: str, prefix: str = "SPIKE: ") -> str:
        """Return the first marker line containing ``text``, or raise AssertionError."""
        for line in self.markers(prefix):
            if text in line:
                return line
        msg = f"no marker line containing {text!r}; got {self.markers(prefix)}"
        raise AssertionError(msg)


def visit(ctx: BrowserContext, url: str, *, done: str = "DONE", timeout: float = 150.0) -> PageRun:
    """Open ``url`` in a new page and wait for the ``SPIKE: <done>`` marker."""
    page: Page = ctx.new_page()
    run = PageRun()
    page.on("console", lambda m: run.lines.append(m.text))
    start = time.perf_counter()
    page.goto(url, wait_until="load")
    while time.perf_counter() - start < timeout:
        if f"SPIKE: {done}" in run.lines or any("Traceback" in x for x in run.lines):
            break
        page.wait_for_timeout(250)
    run.seconds = time.perf_counter() - start
    run.finished = f"SPIKE: {done}" in run.lines
    page.close()
    return run
