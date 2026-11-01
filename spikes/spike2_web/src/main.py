"""Spike 4 (IndexedDB from Pyodide) and Spike 5 (openpyxl in Pyodide)."""

import asyncio
import io
import time

import flet as ft


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


async def idb_request(req):
    from pyodide.ffi import create_proxy

    fut = asyncio.get_running_loop().create_future()

    def ok(_e):
        if not fut.done():
            fut.set_result(req.result)

    def err(_e):
        if not fut.done():
            fut.set_exception(RuntimeError(str(req.error)))

    p_ok, p_err = create_proxy(ok), create_proxy(err)
    req.onsuccess = p_ok
    req.onerror = p_err
    try:
        return await fut
    finally:
        p_ok.destroy()
        p_err.destroy()


async def open_db():
    from js import indexedDB
    from pyodide.ffi import create_proxy

    req = indexedDB.open("cassim-spike", 1)
    upgrade = create_proxy(lambda e: e.target.result.createObjectStore("docs"))
    req.onupgradeneeded = upgrade
    return await idb_request(req)


async def idb_spike() -> None:
    import json

    t = time.perf_counter()
    db = await open_db()

    def store(mode: str):
        # One transaction per operation: a transaction auto-commits once control
        # returns to the event loop with no pending request.
        return db.transaction("docs", mode).objectStore("docs")

    prev = await idb_request(store("readonly").get("counter"))
    n = (prev if prev is not None else 0) + 1
    await idb_request(store("readwrite").put(n, "counter"))
    doc = {"name": "Doc1", "problems": [{"lines": ["f(x):=x^2", "solve(f(x)=4,x)"]}]}
    big = json.dumps(doc) + "x" * 2_000_000
    await idb_request(store("readwrite").put(big, "doc1"))
    back = await idb_request(store("readonly").get("doc1"))
    say(f"IDB ok counter={n} roundtrip_len={len(str(back))} in {time.perf_counter() - t:.3f}s")
    db.close()


async def xlsx_spike() -> None:
    import micropip

    t = time.perf_counter()
    await micropip.install("openpyxl")
    say(f"micropip openpyxl {time.perf_counter() - t:.2f}s")
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["x", "y"])
    for i in range(1, 6):
        ws.append([i, i * i])
    ws["C2"] = "=A2+B2"
    buf = io.BytesIO()
    wb.save(buf)
    data = buf.getvalue()
    wb2 = openpyxl.load_workbook(io.BytesIO(data))
    ws2 = wb2.active
    say(
        f"XLSX ok {openpyxl.__version__} bytes={len(data)} B6={ws2['B6'].value} C2={ws2['C2'].value}"
    )


async def main(page: ft.Page) -> None:
    page.add(ft.Text("spike2"))
    for name, fn in (("idb", idb_spike), ("xlsx", xlsx_spike)):
        try:
            await fn()
        except Exception as e:
            say(f"{name} ERROR {e!r}")
    say("DONE")


ft.run(main)
