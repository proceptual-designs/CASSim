"""Spike 7 (M2 spike D): cancel the real engine mid-calculation and restore state from the document.

The engine is a Blob-spawned Pyodide worker running `cassim.core` (shipped as assets/cassim.zip).
The document model is the list of entries evaluated so far; a fresh engine rebuilds its Session by
replaying them. A spare engine is kept booted so cancel can swap at once (decision 0005).
"""

import asyncio
import json
import time

import flet as ft
import js
from pyodide.ffi import create_proxy, to_js

ENGINE_JS = """
let py = null;
self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.op === "boot") {
      const mod = await import(m.pyodideUrl);
      py = await mod.loadPyodide();
      await py.loadPackage("sympy");
      const buf = await (await fetch(m.zipUrl)).arrayBuffer();
      py.unpackArchive(buf, "zip", {extractDir: "/cassim_lib"});
      py.runPython(`
import sys, json
sys.path.insert(0, "/cassim_lib")
from cassim.core.session import Session
S = Session()
def run(line):
    r = S.eval(line)
    return json.dumps({"text": r.text, "latex": r.latex, "error": r.error})
def restore(lines):
    global S
    S = Session()
    for line in lines:
        S.eval(line)
    return len(lines)
`);
      postMessage({id: m.id, ok: true, value: String(py._module.HEAP8.length / 1e6)});
    } else if (m.op === "eval") {
      postMessage({id: m.id, ok: true, value: py.globals.get("run")(m.line)});
    } else if (m.op === "restore") {
      const n = py.globals.get("restore")(py.toPy(m.lines));
      postMessage({id: m.id, ok: true, value: String(n)});
    }
  } catch (err) {
    postMessage({id: m.id, ok: false, value: String(err)});
  }
};
"""


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def absolute(path: str) -> str:
    return str(js.URL.new(path, js.location.href).href)


class Engine:
    """Proxy to one engine worker."""

    def __init__(self) -> None:
        blob = js.Blob.new(
            [ENGINE_JS], to_js({"type": "text/javascript"}, dict_converter=js.Object.fromEntries)
        )
        self.url = js.URL.createObjectURL(blob)
        self.worker = js.Worker.new(
            self.url, to_js({"type": "module"}, dict_converter=js.Object.fromEntries)
        )
        self.pending: dict[int, asyncio.Future] = {}
        self.next_id = 0
        self._cb = create_proxy(self._on_message)
        self.worker.onmessage = self._cb
        self.wasm_mb = 0.0

    def _on_message(self, e) -> None:
        d = e.data
        fut = self.pending.pop(int(d.id), None)
        if fut and not fut.done():
            fut.set_result((bool(d.ok), str(d.value)))

    def call(self, **msg: object) -> asyncio.Future:
        self.next_id += 1
        fut = asyncio.get_running_loop().create_future()
        self.pending[self.next_id] = fut
        self.worker.postMessage(
            to_js({"id": self.next_id, **msg}, dict_converter=js.Object.fromEntries)
        )
        return fut

    async def boot(self) -> None:
        ok, val = await self.call(
            op="boot", pyodideUrl=absolute(str(js.pyodideUrl)), zipUrl=absolute("cassim.zip")
        )
        assert ok, val
        self.wasm_mb = float(val)

    async def eval(self, line: str) -> dict:
        ok, val = await self.call(op="eval", line=line)
        assert ok, val
        return json.loads(val)

    async def restore(self, lines: list[str]) -> None:
        ok, val = await self.call(op="restore", lines=lines)
        assert ok, val

    def terminate(self) -> None:
        self.worker.terminate()
        js.URL.revokeObjectURL(self.url)
        self._cb.destroy()
        for fut in self.pending.values():
            fut.cancel()


class Calculator:
    """The document model plus an active engine and a pre-booted spare."""

    def __init__(self) -> None:
        self.document: list[str] = []
        self.engine = Engine()
        self.spare: Engine | None = None
        self.spare_boot: asyncio.Task | None = None

    async def start(self) -> None:
        await self.engine.boot()
        self.start_spare()

    def start_spare(self) -> None:
        spare = Engine()
        self.spare = spare
        self.spare_boot = asyncio.ensure_future(spare.boot())

    async def enter(self, line: str) -> dict:
        result = await self.engine.eval(line)
        self.document.append(line)
        return result

    async def cancel(self) -> float:
        """Terminate the busy engine, promote the spare and rebuild its state from the document."""
        t = time.perf_counter()
        self.engine.terminate()
        terminated = (time.perf_counter() - t) * 1000
        assert self.spare is not None and self.spare_boot is not None
        await self.spare_boot  # normally finished long ago
        self.engine = self.spare
        await self.engine.restore(self.document)
        self.start_spare()
        say(f"cancel terminate={terminated:.1f}ms")
        return (time.perf_counter() - t) * 1000


async def main(page: ft.Page) -> None:
    page.add(ft.Text("spike7"))
    await asyncio.sleep(1)
    try:
        t = time.perf_counter()
        calc = Calculator()
        await calc.start()
        say(f"boot1 {time.perf_counter() - t:.2f}s wasm={calc.engine.wasm_mb:.0f}MB")
        await calc.spare_boot  # type: ignore[misc]
        say(f"spare booted {time.perf_counter() - t:.2f}s total wasm={calc.engine.wasm_mb + calc.spare.wasm_mb:.0f}MB")  # type: ignore[union-attr]

        for line in ("a:=5", "f(x):=x^2+a"):
            await calc.enter(line)
        r = await calc.enter("f(3)")
        say(f"f(3) = {r['text']} latex={r['latex']}")

        for round_no in (1, 2):
            hang = calc.engine.call(op="eval", line="expand((x+y+z)^100)")
            await asyncio.sleep(1.0)
            say(f"round{round_no} hang_done={hang.done()}")
            t = time.perf_counter()
            ms = await calc.cancel()
            say(f"round{round_no} cancel_to_ready={ms:.0f}ms hang_cancelled={hang.cancelled()}")
            r = await calc.engine.eval("f(3)")
            say(f"round{round_no} after_cancel f(3) = {r['text']}  (a and f survived: {r['text'] == '14'})")
            r = await calc.engine.eval("1+1")
            say(f"round{round_no} 1+1 = {r['text']}")

        # Replay cost against document length, on the live engine.
        for n in (10, 50, 200, 500):
            lines = []
            for k in range(n):
                lines.append(
                    ("a:=%d" % k, "f(%d)" % k, "solve(x^2-%d=0,x)" % (k + 1), "expand((x+%d)^3)" % k)[
                        k % 4
                    ]
                )
            t = time.perf_counter()
            await calc.engine.restore(lines)
            say(f"replay n={n} {(time.perf_counter() - t) * 1000:.0f}ms")
    except Exception as e:
        say(f"ERROR {e!r}")
    say("DONE")


ft.run(main)
