"""Warm-start and offline test for a flet static build (Edge via Playwright)."""

import functools
import http.server
import sys
import threading
import time
from collections import Counter
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

root, port = sys.argv[1], 8767
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
handler.log_message = lambda *a, **k: None


class Q(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "text/javascript",
        ".js": "text/javascript",
        ".wasm": "application/wasm",
    }

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=root))
threading.Thread(target=srv.serve_forever, daemon=True).start()


def run(page, label, offline_ctx=None):
    seen, hosts = [], Counter()
    page.on("console", lambda m: seen.append(m.text))
    page.on(
        "request",
        lambda r: (
            hosts.update([urlparse(r.url).netloc]),
            "127.0.0.1" not in r.url and print("EXT", r.url[:140]),
        ),
    )
    t = time.perf_counter()
    page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
    while time.perf_counter() - t < 120:
        if any("SPIKE: DONE" in x for x in seen) or any("Traceback" in x for x in seen):
            break
        page.wait_for_timeout(300)
    ok = any("SPIKE: DONE" in x for x in seen)
    if not ok:
        print(chr(10).join(x[:200] for x in seen[-12:]))
    print(f"{label}: ok={ok} {time.perf_counter() - t:.1f}s hosts={dict(hosts)}")
    for x in seen:
        if "SPIKE:" in x and "DONE" not in x:
            print("   ", x)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context()
    run(ctx.new_page(), "cold")
    ctx.pages[0].wait_for_timeout(3000)  # let service worker finish caching
    ctx.pages[0].wait_for_timeout(2000)
    run(ctx.new_page(), "second visit")
    ctx.set_offline(True)
    run(ctx.new_page(), "offline")
    b.close()
srv.shutdown()
