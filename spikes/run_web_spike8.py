"""Spike 8 (M2 spike C): publish under a project sub-path, then load it and reload it offline.

Simulates GitHub Pages for a project site: files served only under /CASSim/, correct MIME types,
no response headers beyond that. Reports external requests, the service worker's scope, the dist
size, and whether a reload with the network switched off still boots the engine.

    python spikes/run_web_spike8.py [--cdn]
"""

import functools
import http.server
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "spikes" / "spike7_web"
BASE = "CASSim"
MARK = "SPIKE: f(3) = 14"
TYPES = {".mjs": "text/javascript", ".js": "text/javascript", ".wasm": "application/wasm"}


class PagesHandler(http.server.SimpleHTTPRequestHandler):
    """Serve `directory` only below /CASSim/, as a Pages project site does."""

    def translate_path(self, path: str) -> str:
        p = urlparse(path).path
        if not p.startswith(f"/{BASE}/") and p != f"/{BASE}":
            return str(Path(self.directory) / "__missing__")
        return super().translate_path("/" + p.removeprefix(f"/{BASE}").lstrip("/"))

    def guess_type(self, path) -> str:
        return TYPES.get(Path(path).suffix, super().guess_type(path))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def flet(*args: str) -> None:
    exe = Path(sys.executable).with_name("flet.exe")
    done = subprocess.run([str(exe), *args], cwd=APP, capture_output=True, text=True, check=False)
    if done.returncode:
        raise SystemExit(done.stdout + done.stderr)


def build(dist: Path, *, cdn: bool) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "spikes" / "make_cassim_zip.py"), str(APP / "src/assets/cassim.zip")],
        check=True,
        capture_output=True,
    )
    cmd = ["publish", "src/main.py", "--distpath", str(dist), "--base-url", BASE]
    if not cdn:
        cmd.append("--no-cdn")
    flet(*cmd)
    if not cdn:
        index = dist / "index.html"
        text = index.read_text(encoding="utf-8")
        text = text.replace('pyodideUrl="pyodide/pyodide.mjs"', 'pyodideUrl="./pyodide/pyodide.mjs"')
        index.write_text(text, encoding="utf-8")
        subprocess.run(
            [sys.executable, str(ROOT / "spikes" / "vendor_pyodide_pkgs.py"), str(dist), "sympy", "micropip", "msgpack", "six"],
            check=True,
            capture_output=True,
        )
        vendor_pypi_wheels(dist)
    print("precached files:", add_offline_cache(dist))


SERVICE_WORKER = """
// CASSim spike: precache the whole site at install, then answer same-origin GETs cache-first.
const CACHE = "cassim-spike-v1";
self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const list = await (await fetch("precache.json", {cache: "no-store"})).json();
    const cache = await caches.open(CACHE);
    await cache.addAll(list);
    await self.skipWaiting();
  })());
});
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req, {ignoreSearch: true});
    if (hit) return hit;
    try {
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      if (req.mode === "navigate") return (await cache.match("index.html")) || Response.error();
      throw err;
    }
  })());
});
"""


def add_offline_cache(dist: Path) -> int:
    """Replace Flutter's self-unregistering service worker with a precaching one."""
    files = sorted(
        f.relative_to(dist).as_posix()
        for f in dist.rglob("*")
        if f.is_file() and f.suffix != ".map" and f.name != "precache.json"
    )
    (dist / "precache.json").write_text(json.dumps(["./", *files]), encoding="utf-8")
    (dist / "flutter_service_worker.js").write_text(SERVICE_WORKER, encoding="utf-8")
    return len(files)


def vendor_pypi_wheels(dist: Path) -> None:
    """Put `flet` and `repath` (pure-Python PyPI wheels) in dist/pyodide and in its lock file.

    Flet's worker runs `micropip.install` for the app's requirements. micropip looks in
    pyodide-lock.json first, so a package listed there is loaded from this folder, not PyPI.
    """
    pyo = dist / "pyodide"
    lock_path = pyo / "pyodide-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    wanted = {"flet": (flet_version(), ["msgpack", "repath"]), "repath": ("0.9.0", ["six"])}
    for name, (version, depends) in wanted.items():
        meta = json.loads(urlopen(f"https://pypi.org/pypi/{name}/{version}/json").read())
        wheel = next(u for u in meta["urls"] if u["packagetype"] == "bdist_wheel")
        (pyo / wheel["filename"]).write_bytes(urlopen(wheel["url"]).read())
        lock["packages"][name] = {
            "depends": depends,
            "file_name": wheel["filename"],
            "imports": [name],
            "install_dir": "site",
            "name": name,
            "package_type": "package",
            "sha256": wheel["digests"]["sha256"],
            "tool": {},
            "unvendored_tests": False,
            "version": version,
        }
    lock_path.write_text(json.dumps(lock), encoding="utf-8")


def flet_version() -> str:
    import flet.version

    return flet.version.flet_version


def tree_size(root: Path) -> float:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) / 1e6


def main() -> None:
    cdn = "--cdn" in sys.argv
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        dist = Path(tmp) / "dist"
        build(dist, cdn=cdn)
        print(f"dist size {tree_size(dist):.1f} MB; biggest:")
        for f in sorted((x for x in dist.rglob("*") if x.is_file()), key=lambda x: -x.stat().st_size)[:5]:
            print(f"   {f.stat().st_size / 1e6:6.1f} MB  {f.relative_to(dist).as_posix()}")
        handler = functools.partial(PagesHandler, directory=str(dist))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_address[1]}/{BASE}/"
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        external: set[str] = set()
        missing: set[str] = set()
        lines: list[str] = []

        def on_request(r) -> None:
            if not r.url.startswith(("http://127.0.0.1", "blob:", "data:")):
                external.add(urlparse(r.url).netloc + urlparse(r.url).path.rsplit("/", 1)[0])

        page.on("request", on_request)
        page.on("response", lambda r: missing.add(r.url) if r.status == 404 and "127.0.0.1" in r.url else None)
        page.on("console", lambda m: lines.append(m.text))
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        while time.perf_counter() - t0 < 240 and not any(x.startswith(MARK) for x in lines):
            page.wait_for_timeout(500)
        first = time.perf_counter() - t0
        ok = any(x.startswith(MARK) for x in lines)
        print(f"first load: engine ready={ok} in {first:.1f}s")
        print("external hosts:", sorted(external) or "none")
        print("404s:", sorted(missing) or "none")
        regs = page.evaluate(
            "navigator.serviceWorker.getRegistrations().then(r => r.map(x => x.scope + ' active=' + !!x.active))"
        )
        print("service workers:", regs)
        print("python errors:", [x[:200] for x in lines if "Traceback" in x or "rror" in x][:3])
        dbg = page.evaluate("""async () => {
          try {
            const r = await navigator.serviceWorker.register('flutter_service_worker.js');
            const w = r.installing || r.waiting || r.active;
            const log = [r.scope, w && w.state];
            await new Promise(res => { if (!w) return res(); w.addEventListener('statechange', () => { log.push(w.state); if (w.state === 'activated' || w.state === 'redundant') res(); }); setTimeout(res, 60000); });
            return log;
          } catch (e) { return String(e); }
        }""")
        print("sw register:", dbg)
        # Wait for the precache to finish, then go offline and reload.
        for _ in range(240):
            n = page.evaluate("caches.keys().then(async k => k.length ? (await (await caches.open(k[0])).keys()).length : 0)")
            if n >= 100:
                break
            page.wait_for_timeout(500)
        print("cache entries:", n, "; controlled:", page.evaluate("!!navigator.serviceWorker.controller"))
        page.reload(wait_until="load")
        page.wait_for_timeout(1500)
        print("controlled after reload:", page.evaluate("!!navigator.serviceWorker.controller"))
        ctx.set_offline(True)
        lines.clear()
        page.reload(wait_until="load")
        t1 = time.perf_counter()
        while time.perf_counter() - t1 < 120 and not any(x.startswith(MARK) for x in lines):
            page.wait_for_timeout(500)
        ok2 = any(x.startswith(MARK) for x in lines)
        print(f"offline reload: engine ready={ok2} in {time.perf_counter() - t1:.1f}s")
        print("offline errors:", [x[:160] for x in lines if "rror" in x or "ailed" in x][:4])
        browser.close()
        server.shutdown()
        print(json.dumps({"cdn": cdn, "first_ok": ok, "offline_ok": ok2}))


if __name__ == "__main__":
    main()
    _ = re
