# 0005. Spike 4: UI responsiveness and cancel

Date: 2026-11-01. Status: **GO. Run the engine in its own Pyodide worker and cancel by terminating it.**
Code: `spikes/spike4_web/`, `spikes/run_web_spike4.py`, `tests/e2e/test_spike_cancel.py`.
Closes the first open question in 0002. Environment as in 0002 (Flet 1.0.5, Pyodide 314.0.7, headless Edge, CDN build).

## Findings

1. **A busy Flet worker does not freeze the UI thread.** With a 3 s busy loop in Flet's own Python worker, the browser main thread kept drawing: 240 frames in 4.0 s (60 fps), max `requestAnimationFrame` gap 17 ms.
2. **But it does freeze everything that needs Python.** Flet runs all event handlers, `print` forwarding and its asyncio loop in that same worker. While a long evaluation runs there, a Cancel button click is never handled and even the "start" marker is not flushed. Evaluation therefore cannot run in Flet's worker.
3. **A second worker works.** Flet's Python can spawn a module `Worker` from a `Blob` URL (`js.Worker.new`), which imports `js.pyodideUrl`, boots its own Pyodide, loads SymPy and answers `postMessage` requests. It was driven entirely through `pyodide.ffi.create_proxy` and `to_js`.
4. **Cancel is `worker.terminate()`.** With the engine stuck in `while True: pass`, Flet's loop kept running (39 ticks of 50 ms in 2.0 s), `terminate()` took 0.3 ms, and the pending future was cancelled. A freshly spawned engine then solved correctly.

| Measure | Result |
|---|---|
| Engine worker boot (Pyodide + SymPy, CDN build, first) | about 9 s |
| Engine worker re-boot after cancel (HTTP cache warm) | about 7 s |
| `solve(x^2 - 4)` first call in the engine worker | 0.28 s |
| `terminate()` | under 1 ms |

## Decision
- Architecture: Flet's worker holds the UI, device model and document; the **engine worker** (a Blob-spawned module worker running `cassim.core`) evaluates. The Flet side talks to it with an async request/response protocol and shows a "busy" state.
- Cancel (On/Esc) terminates the engine worker, discards pending requests and boots a new one. Session state is rebuilt from the document model, as planned in PLAN.md section 3.
- Keep a **spare engine pre-booted** after startup so a cancel feels instant. The roughly 7 s re-boot is too slow to do on demand. Booting the spare in the background costs memory; measure that in M2.
- Do not use Pyodide's interrupt buffer. It needs `SharedArrayBuffer`, which needs cross-origin isolation headers (COOP/COEP) that plain static hosting (for example GitHub Pages) cannot set.
- The engine bundle is loaded twice by design: once per Pyodide instance. The service worker cache means the second load is not a second download.

## Not measured (carry into M2)
- Memory of two Pyodide instances with SymPy loaded, especially on phones.
- The first load with the real `cassim.core` wheel rather than just SymPy, and whether the engine can be booted from a local (`--no-cdn`) build with vendored packages.
- Large-result transfer cost across `postMessage`. Results should travel as JSON or LaTeX strings plus a layout tree, not Python objects.
- Safari and iOS: module workers created from Blob URLs, and nested worker limits.
