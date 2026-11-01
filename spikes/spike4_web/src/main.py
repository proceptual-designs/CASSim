"""Spike 4: responsiveness and cancel. Engine runs in a second Pyodide worker that Flet's
Python spawns from a Blob; cancel is ``Worker.terminate()`` plus a fresh worker.

Phase A: busy loop inside Flet's own worker (browser test checks the UI thread keeps drawing).
Phase B: engine worker: boot, solve, hang, cancel while Flet's loop stays alive, reboot, solve.
"""

import asyncio
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
      py.runPython("import sympy as sp");
      postMessage({id: m.id, ok: true, value: "booted"});
    } else if (m.op === "eval") {
      const v = py.runPython(m.code);
      postMessage({id: m.id, ok: true, value: String(v)});
    }
  } catch (err) {
    postMessage({id: m.id, ok: false, value: String(err)});
  }
};
"""


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


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
            op="boot", pyodideUrl=str(js.URL.new(str(js.pyodideUrl), js.location.href).href)
        )
        assert ok, val

    async def eval(self, code: str) -> str:
        ok, val = await self.call(op="eval", code=code)
        assert ok, val
        return val

    def terminate(self) -> None:
        self.worker.terminate()
        js.URL.revokeObjectURL(self.url)
        self._cb.destroy()
        for fut in self.pending.values():
            fut.cancel()


async def phase_a_busy_in_flet_worker() -> None:
    say("A_START")
    await asyncio.sleep(1)  # let the marker flush before the worker goes busy
    t = time.perf_counter()
    while time.perf_counter() - t < 3:
        pass
    say("A_END")


async def phase_b_cancel() -> None:
    t = time.perf_counter()
    eng = Engine()
    await eng.boot()
    say(f"B boot1 {time.perf_counter() - t:.2f}s")

    t = time.perf_counter()
    r = await eng.eval("str(sp.solve(sp.Symbol('x')**2 - 4))")
    say(f"B solve1 {r} {time.perf_counter() - t:.3f}s")

    # Hang the engine, and confirm Flet's own event loop stays responsive meanwhile.
    hang = eng.call(op="eval", code="exec('while True: pass')")
    t = time.perf_counter()
    ticks = 0
    while time.perf_counter() - t < 2.0:
        await asyncio.sleep(0.05)
        ticks += 1
    say(
        f"B flet_loop_alive_during_hang ticks={ticks} in {time.perf_counter() - t:.2f}s hang_done={hang.done()}"
    )

    t = time.perf_counter()
    eng.terminate()
    say(f"B terminate {(time.perf_counter() - t) * 1000:.1f}ms hang_cancelled={hang.cancelled()}")

    t = time.perf_counter()
    eng2 = Engine()
    await eng2.boot()
    say(f"B boot2 {time.perf_counter() - t:.2f}s")
    r = await eng2.eval("str(sp.solve(sp.Symbol('x')**2 - 9))")
    say(f"B solve2 {r}")
    eng2.terminate()


async def main(page: ft.Page) -> None:
    page.add(ft.Text("spike4"))
    await asyncio.sleep(1)
    for name, fn in (("A", phase_a_busy_in_flet_worker), ("B", phase_b_cancel)):
        try:
            await fn()
        except Exception as e:
            say(f"{name} ERROR {e!r}")
    say("DONE")


ft.run(main)
