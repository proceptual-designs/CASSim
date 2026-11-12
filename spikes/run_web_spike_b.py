"""Run a spike script inside Pyodide in a worker, as the engine worker does, and print its lines.

Usage: python spikes/run_web_spike_b.py [script] [--dist build/web] [--slow 4]

It serves an existing build (`python -m tools.publish`), opens a blank same-origin page in headless
Edge and starts a module worker that boots the build's Pyodide, unpacks `cassim.zip` and runs the
script. `--slow N` applies Chromium's CPU throttle to the page; whether it also slows the worker
is not known, so treat it as a rough stand-in
for a phone. It also times a 2,500-cell payload crossing `postMessage`.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import webharness  # noqa: E402

WORKER = """
self.onmessage = async (e) => {
  const m = e.data;
  try {
    const zip = fetch(m.zipUrl).then((r) => r.arrayBuffer());
    const mod = await import(m.pyodideUrl);
    const t0 = Date.now();
    const py = await mod.loadPyodide({stdout: (s) => postMessage({line: s}),
                                      stderr: (s) => postMessage({line: "ERR " + s})});
    py.unpackArchive(await zip, "zip", {extractDir: "/cassim_lib"});
    py.runPython('import sys; sys.path.insert(0, "/cassim_lib")');
    postMessage({line: "SPIKE: pyodide_boot_ms=" + (Date.now() - t0)});
    py.globals.set("__source__", m.source);
    py.runPython('exec(compile(__source__, "spike.py", "exec"), {"__name__": "__main__"})');
    const cells = [];
    for (let i = 0; i < 2500; i++) cells.push(String(i * 37 % 1000 / 7));
    postMessage({payload: JSON.stringify({name: "xs", rev: 1, cells}), sent: Date.now()});
    postMessage({done: true});
  } catch (err) {
    postMessage({line: "SPIKE: WORKER ERROR " + String(err)});
    postMessage({done: true});
  }
};
"""

PAGE = """
async ([worker, source, base]) => {
  window.__lines = [];
  window.__done = false;
  const url = URL.createObjectURL(new Blob([worker], {type: "text/javascript"}));
  const w = new Worker(url, {type: "module"});
  w.onmessage = (e) => {
    if (e.data.line !== undefined) window.__lines.push(e.data.line);
    if (e.data.payload !== undefined) {
      const t = performance.now();
      const parsed = JSON.parse(e.data.payload);
      window.__lines.push("SPIKE: postMessage_ms=" + (Date.now() - e.data.sent) +
        " parse_ms=" + (performance.now() - t).toFixed(1) + " cells=" + parsed.cells.length);
    }
    if (e.data.done) window.__done = true;
  };
  w.postMessage({source, zipUrl: base + "cassim.zip", pyodideUrl: base + "pyodide/pyodide.mjs"});
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", nargs="?", default=str(ROOT / "spikes" / "spike_b_data.py"))
    parser.add_argument("--dist", type=Path, default=ROOT / "build" / "web")
    parser.add_argument("--slow", type=float, default=1.0, help="CPU throttle factor")
    args = parser.parse_args()
    source = Path(args.script).read_text(encoding="utf-8")
    with sync_playwright() as p, webharness.serve(args.dist) as url:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto(url + "version.json")
        if args.slow != 1.0:
            session = page.context.new_cdp_session(page)
            session.send("Emulation.setCPUThrottlingRate", {"rate": args.slow})
        page.evaluate(PAGE, [WORKER, source, url])
        seen = 0
        start = time.perf_counter()
        while time.perf_counter() - start < 900:
            lines = page.evaluate("window.__lines")
            for line in lines[seen:]:
                print(line, flush=True)
            seen = len(lines)
            if page.evaluate("window.__done"):
                break
            page.wait_for_timeout(500)
        browser.close()


if __name__ == "__main__":
    main()
