"""Serve a flet static build and measure load in a real browser (Edge via Playwright)."""
import functools
import http.server
import sys
import threading
import time

from playwright.sync_api import sync_playwright

root, port = sys.argv[1], 8765
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context()
    page = ctx.new_page()
    sizes = {"n": 0, "bytes": 0}

    def on_resp(r):
        try:
            sizes["n"] += 1
            sizes["bytes"] += len(r.body())
        except Exception:
            pass

    page.on("response", on_resp)
    seen = []
    t = time.perf_counter()

    def on_console(m):
        seen.append(m.text)
        print(f"[{time.perf_counter() - t:7.2f}s] {m.text[:160]}")

    page.on("console", on_console)
    page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
    print("load event", round(time.perf_counter() - t, 2))
    deadline = time.time() + 150
    last = ""
    while time.time() < deadline:
        if any("SPIKE: DONE" in x or "Traceback" in x for x in seen):
            break
        page.wait_for_timeout(500)
    print("first DONE after", round(time.perf_counter() - t, 2), "s")
    print("network:", sizes)
    print(page.screenshot(path=r"C:\dev\builds\spike1_shot.png") and "")
    b.close()
srv.shutdown()
