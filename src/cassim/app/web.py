"""The browser engine: a device's `EngineCore` in its own Pyodide worker (decision 0005).

Flet runs the UI, the document model and its event handlers in one Pyodide worker, so a long
calculation there would freeze Cancel too. The engine therefore gets a second worker, spawned from
a Blob URL. Cancel is `worker.terminate()` (under 2 ms, decision 0016); a spare engine is kept
booted so the swap is immediate, and the Runner rebuilds the new engine from the journals.

Imported only where `sys.platform == "emscripten"`: `js` and `pyodide` exist only there.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import js  # ty: ignore[unresolved-import]
from pyodide.ffi import create_proxy, to_js  # ty: ignore[unresolved-import]

from cassim.device.engine import EngineError, Op, Reply, check_reply

ENGINE_JS = """
let py = null;
self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.op === "boot") {
      // cassim.zip holds the engine and SymPy as bytecode (tools/publish.py), so nothing is
      // installed here; it downloads while Pyodide starts.
      const zip = fetch(m.zipUrl).then((r) => r.arrayBuffer());
      const mod = await import(m.pyodideUrl);
      py = await mod.loadPyodide();
      py.unpackArchive(await zip, "zip", {extractDir: "/cassim_lib"});
      py.runPython(`
import sys, json
sys.path.insert(0, "/cassim_lib")
from __ENGINE_MODULE__ import EngineCore
core = EngineCore()
def handle(message):
    m = json.loads(message)
    if m["op"] == "run":
        return json.dumps(core.apply(int(m["problem"]), m["ops"]))
    core.reset({int(k): v for k, v in m["journals"].items()})
    return "{}"
`);
      postMessage({id: m.id, ok: true, value: "{}"});
    } else {
      postMessage({id: m.id, ok: true, value: py.globals.get("handle")(m.message)});
    }
  } catch (err) {
    postMessage({id: m.id, ok: false, value: String(err)});
  }
};
"""


# At start-up the spare waits this long after the active engine is ready, so it does not compete
# with replaying the autosaved document and the first keys on a phone. After a Cancel there is no
# wait: the user may cancel again.
SPARE_DELAY = 3.0


def _absolute(path: str) -> str:
    return str(js.URL.new(path, js.location.href).href)


class _Worker:
    """One engine worker and the requests waiting on it."""

    def __init__(self, module: str) -> None:
        source = ENGINE_JS.replace("__ENGINE_MODULE__", module)
        blob = js.Blob.new(
            [source], to_js({"type": "text/javascript"}, dict_converter=js.Object.fromEntries)
        )
        self._url = js.URL.createObjectURL(blob)
        self._worker = js.Worker.new(
            self._url, to_js({"type": "module"}, dict_converter=js.Object.fromEntries)
        )
        self._pending: dict[int, asyncio.Future[str]] = {}
        self._next = 0
        self._callback = create_proxy(self._on_message)
        self._worker.onmessage = self._callback
        self.ready: asyncio.Future[None] = asyncio.ensure_future(self._boot())

    def _on_message(self, event: js.MessageEvent) -> None:
        data = event.data
        future = self._pending.pop(int(data.id), None)
        if future is None or future.done():
            return
        if data.ok:
            future.set_result(str(data.value))
        else:
            future.set_exception(EngineError(str(data.value)))

    def _call(self, **message: object) -> asyncio.Future[str]:
        self._next += 1
        future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        self._pending[self._next] = future
        self._worker.postMessage(
            to_js({"id": self._next, **message}, dict_converter=js.Object.fromEntries)
        )
        return future

    async def _boot(self) -> None:
        await self._call(
            op="boot",
            pyodideUrl=_absolute(str(js.pyodideUrl)),
            zipUrl=_absolute("cassim.zip"),
        )
        print("CASSIM: ENGINE READY", flush=True)  # read by tools/loadtime.py

    async def send(self, message: dict[str, Any]) -> dict[str, Any]:
        await self.ready
        return json.loads(await self._call(op="message", message=json.dumps(message)))

    def terminate(self) -> None:
        self._worker.terminate()
        js.URL.revokeObjectURL(self._url)
        self._callback.destroy()
        for future in self._pending.values():
            future.cancel()
        self._pending.clear()
        self.ready.cancel()


class WorkerEngine:
    """The `Engine` for the browser: an active worker and, once that has booted, a spare."""

    def __init__(self, module: str) -> None:
        self._module = module  # the device's engine module: it exposes `EngineCore`
        self._active = _Worker(module)
        self._spare: _Worker | None = None
        self._spare_task: asyncio.Future[None]  # kept so the task is not collected
        self._spare_task = asyncio.ensure_future(self._start_spare(SPARE_DELAY))

    async def _start_spare(self, delay: float = 0.0) -> None:
        """Boot the spare once the active engine is ready and `delay` seconds have passed."""
        active = self._active
        try:
            await active.ready
            await asyncio.sleep(delay)
        except asyncio.CancelledError, EngineError:
            return
        if self._active is active and self._spare is None:
            self._spare = _Worker(self._module)

    async def run(self, problem: int, ops: list[Op]) -> Reply:
        return check_reply(await self._active.send({"op": "run", "problem": problem, "ops": ops}))

    async def reset(self, journals: dict[int, list[Op]]) -> None:
        await self._active.send({"op": "reset", "journals": journals})
        self._spare_task = asyncio.ensure_future(self._start_spare())

    def cancel(self) -> bool:
        """End the busy worker at once and make the spare the active engine."""
        self._active.terminate()
        self._active = self._spare if self._spare is not None else _Worker(self._module)
        self._spare = None
        return True


class Bridge:
    """Talks to the page over a BroadcastChannel: this code runs in a Web Worker and has no DOM
    (see `BODY_TAGS` in tools/publish.py for the page's side)."""

    def __init__(self, changed: Callable[[], None]) -> None:
        self.installable = False
        self.standalone = False  # already running as an installed app (or fullscreen)
        self.can_fullscreen = False
        self.in_fullscreen = False  # the page is fullscreen now, so the menu offers to leave it
        self.installed = False  # running as the installed app, so the menu offers Uninstall
        self._changed = changed
        self._channel = js.BroadcastChannel.new("cassim")
        self._callback = create_proxy(self._on_message)
        self._channel.onmessage = self._callback
        self._send("hello")  # the page answers with what the browser offers

    def _on_message(self, event: js.MessageEvent) -> None:
        op = str(event.data.op)
        if op == "installable":
            self.installable = bool(event.data.value)
            self._changed()
        elif op == "env":
            self.standalone = bool(event.data.standalone)
            self.can_fullscreen = bool(event.data.fullscreen)
            self.in_fullscreen = bool(event.data.inFullscreen)
            self.installed = bool(event.data.installed)
            self._changed()

    def _send(self, op: str) -> None:
        self._channel.postMessage(to_js({"op": op}, dict_converter=js.Object.fromEntries))

    def install(self) -> None:
        self._send("install")

    def fullscreen(self) -> None:
        self._send("fullscreen")

    def exit_fullscreen(self) -> None:
        self._send("exit_fullscreen")


async def _request(request: js.IDBRequest) -> object:
    """The result of an IndexedDB request, awaited (decision 0003, spike 4)."""
    future: asyncio.Future[object] = asyncio.get_running_loop().create_future()

    def ok(_event: object) -> None:
        if not future.done():
            future.set_result(request.result)

    def failed(_event: object) -> None:
        if not future.done():
            future.set_exception(OSError(str(request.error)))

    on_ok, on_failed = create_proxy(ok), create_proxy(failed)
    request.onsuccess = on_ok
    request.onerror = on_failed
    try:
        return await future
    finally:
        on_ok.destroy()
        on_failed.destroy()


class TextStore:
    """Texts by key in IndexedDB (FR-DOC-003, decision 0031): unlike localStorage it holds far more
    than 5 MB and writes without blocking. One transaction per request, never held across an
    `await`, since a transaction commits once the event loop is idle (decision 0003)."""

    STORE = "texts"

    def __init__(self, database: str = "cassim") -> None:
        self._database = database
        self._db: object | None = None

    async def _open(self) -> js.IDBDatabase:
        if self._db is None:
            request = js.indexedDB.open(self._database, 1)
            upgrade = create_proxy(lambda e: e.target.result.createObjectStore(self.STORE))
            request.onupgradeneeded = upgrade
            try:
                self._db = await _request(request)
            finally:
                upgrade.destroy()
        return self._db

    async def get(self, key: str) -> str | None:
        db = await self._open()
        found = await _request(
            db.transaction(self.STORE, "readonly").objectStore(self.STORE).get(key)
        )
        return found if isinstance(found, str) else None

    async def put(self, key: str, text: str) -> None:
        db = await self._open()
        await _request(
            db.transaction(self.STORE, "readwrite").objectStore(self.STORE).put(text, key)
        )

    async def delete(self, key: str) -> None:
        db = await self._open()
        await _request(db.transaction(self.STORE, "readwrite").objectStore(self.STORE).delete(key))
