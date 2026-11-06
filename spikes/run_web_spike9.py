"""Spike 9 (M2 spike E): does `flet build web` carry a custom Dart extension to a static site?

Builds spikes/spike9_ext/app (uses the FletPing extension in spikes/spike9_ext) with
`flet build web --no-cdn --base-url CASSim`, applies the same post-publish steps as spike 8
(patch pyodideUrl, vendor Pyodide packages and the flet wheels, precaching service worker),
serves it under /CASSim/ like a Pages project site, then:

1. loads it and checks the Dart-drawn control is on screen (screenshot) and Python started;
2. taps the control and checks the Dart -> Python event arrives;
3. reloads with the network off and repeats 1 and 2.

    python spikes/run_web_spike9.py [--skip-build]
"""

import functools
import http.server
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from run_web_spike8 import BASE, PagesHandler, add_offline_cache, tree_size, vendor_pypi_wheels

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "spikes" / "spike9_ext" / "app"
DIST = ROOT / "dist" / "spike9"
SHOT = ROOT / "dist" / "spike9_shots"


def build() -> None:
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    exe = Path(sys.executable).with_name("flet.exe")
    t0 = time.perf_counter()
    done = subprocess.run(
        [str(exe), "build", "web", "--yes", "--no-cdn", "--base-url", BASE, "-o", str(DIST)],
        cwd=APP,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    print(f"flet build web: exit {done.returncode} in {time.perf_counter() - t0:.0f}s")
    if done.returncode:
        raise SystemExit(done.stdout[-3000:] + done.stderr[-3000:])
    index = DIST / "index.html"
    text = index.read_text(encoding="utf-8")
    print(
        "pyodideUrl in index.html:",
        "./pyodide/pyodide.mjs" in text or 'pyodideUrl="pyodide/pyodide.mjs"' in text,
    )
    index.write_text(
        text.replace('pyodideUrl="pyodide/pyodide.mjs"', 'pyodideUrl="./pyodide/pyodide.mjs"'),
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "spikes" / "vendor_pyodide_pkgs.py"),
            str(DIST),
            "micropip",
            "msgpack",
            "six",
        ],
        check=True,
        capture_output=True,
    )
    vendor_pypi_wheels(DIST)
    print("precached files:", add_offline_cache(DIST))


def wait_for(lines: list[str], marker: str, secs: float, page) -> bool:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < secs and not any(marker in x for x in lines):
        page.wait_for_timeout(300)
    return any(marker in x for x in lines)


def exercise(page, lines: list[str], tag: str) -> tuple[bool, bool]:
    lines.clear()
    ready = wait_for(lines, "SPIKE9: python ready", 240, page)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(SHOT / f"{tag}_loaded.png"))
    # The control sits at the top-left of the page; tap inside its box.
    page.mouse.click(60, 40)
    pinged = wait_for(lines, "SPIKE9: ping 1", 10, page)
    page.wait_for_timeout(500)
    page.screenshot(path=str(SHOT / f"{tag}_tapped.png"))
    print(f"{tag}: python ready={ready}, dart->python ping={pinged}")
    return ready, pinged


def main() -> None:
    SHOT.mkdir(parents=True, exist_ok=True)
    if "--skip-build" not in sys.argv:
        build()
    print(f"dist size {tree_size(DIST):.1f} MB")
    handler = functools.partial(PagesHandler, directory=str(DIST))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport={"width": 800, "height": 500})
        page = ctx.new_page()
        lines: list[str] = []
        external: set[str] = set()
        missing: set[str] = set()
        page.on("console", lambda m: lines.append(m.text))
        page.on(
            "request",
            lambda r: (
                external.add(urlparse(r.url).netloc)
                if not r.url.startswith(("http://127.0.0.1", "blob:", "data:"))
                else None
            ),
        )
        page.on(
            "response",
            lambda r: missing.add(r.url) if r.status == 404 and "127.0.0.1" in r.url else None,
        )
        page.goto(url, wait_until="load")
        online = exercise(page, lines, "online")
        print("external hosts:", sorted(external) or "none", "; 404s:", sorted(missing) or "none")
        regs = page.evaluate(
            "navigator.serviceWorker.getRegistrations()"
            ".then(r => r.map(x => x.scope + ' active=' + !!x.active))"
        )
        print("service workers:", regs)
        page.evaluate("navigator.serviceWorker.register('flutter_service_worker.js')")
        for _ in range(240):
            n = page.evaluate(
                "caches.keys().then(async k =>"
                " k.length ? (await (await caches.open(k[0])).keys()).length : 0)"
            )
            if n >= 100:
                break
            page.wait_for_timeout(500)
        print("cache entries:", n)
        page.reload(wait_until="load")
        page.wait_for_timeout(1500)
        ctx.set_offline(True)
        page.reload(wait_until="load")
        offline = exercise(page, lines, "offline")
        print("errors:", [x[:160] for x in lines if "rror" in x][:3])
        browser.close()
    server.shutdown()
    print("RESULT online", online, "offline", offline)


if __name__ == "__main__":
    main()
