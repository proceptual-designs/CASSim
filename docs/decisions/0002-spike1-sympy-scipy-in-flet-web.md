# 0002. Spike 1: SymPy + SciPy inside the Flet static build

Date: 2026-10-31. Status: **GO (with offline work scheduled)**.
Code: `spikes/spike1_web/`, `spikes/run_web_spike.py`, `spikes/run_web_spike2.py`, `spikes/vendor_pyodide_pkgs.py`.
Environment: Flet 1.0.5, Pyodide 314.0.7 (Python 3.14.2), Edge (headless, Playwright), localhost server, Windows 11.

## Results

| Question | Result |
|---|---|
| Do SymPy 1.14 and SciPy 1.18 run in the Flet static build? | **Yes.** `solve`, `integrate`, `factor`, `norm.cdf` all return correct values. |
| Do they load automatically from `pyproject.toml` dependencies? | **No.** `flet publish` packages only `flet` into `requirements.txt`. Load explicitly with `await micropip.install([...])` in an `async def main`. They resolve to the Pyodide-bundled builds. |
| Does Python run in a worker? | **Yes.** The console shows "Starting up Python worker" (`python-worker.js`). UI-stays-responsive-during-busy-Python is **not yet measured** (Flutter canvas has no DOM to click; needs coordinates or semantics). |
| Cold start (CDN build, empty cache) | About 35 s to results: Flutter ~4 s, Pyodide + flet ~9 s, package load ~10 s, `import sympy` 4-5 s, `import scipy.stats` 5 s. |
| Cold start (`--no-cdn` + vendored packages) | About 15 s: package load 1.5 s, `import sympy` 2.8 s, `import scipy.stats` 2.9 s. |
| Operation cost after import | `solve` 0.28 s (first call), `integrate` 0.15 s, `factor` 5 ms, `norm.cdf` 1 ms. |
| Download size | CDN build: 22 MB dist + about 33 MB fetched in total. `--no-cdn` dist 73 MB + 21.7 MB vendored packages (SymPy 4.2, NumPy 3.0, SciPy 14.0 MB, wheels). |
| Offline? | **Not as shipped.** The default build uses jsdelivr (Pyodide and packages), gstatic (CanvasKit, fonts) and PyPI (the flet wheel via micropip). |

## Offline findings (`flet publish --no-cdn`, Flet 1.0.5)

1. Self-hosts Pyodide core and CanvasKit but writes `flet.pyodideUrl="pyodide/pyodide.mjs"` into `index.html`. The worker `import()`s it as a bare specifier and fails. Patching it to `./pyodide/pyodide.mjs` works.
2. Does **not** vendor Pyodide packages. Fixed by `spikes/vendor_pyodide_pkgs.py`, which downloads wheels listed in `pyodide-lock.json` (and dependencies) into `dist/pyodide/`.
3. Still external after that: `flet-1.0.5` and `repath-0.9.0` wheels from PyPI, and `rive_native` wasm from jsdelivr (unused Flutter dependency). Next step is to vendor the two wheels and point `requirements.txt` at local URLs, then test with the service worker and the browser set offline. Not done in this spike.
4. The static host must serve `.mjs` as `text/javascript` (Python's `http.server` on Windows does not by default).

## Decision

- Go with Flet static + Pyodide for the engine. SymPy and SciPy are fast enough once loaded; SciPy stays lazily imported (about 3-5 s) as planned.
- A post-publish build step (patch `index.html`, vendor packages and wheels) goes in `tools/` as part of M2e. If that is too brittle, the fallback in PLAN.md section 9 (thin custom web front-end over the same engine) remains.
- Show a loading screen with progress: cold start is 15-35 s.

## Still open from this spike

- ~~Is the UI responsive while Python is busy, and can a worker be terminated and restarted for cancel?~~ Answered in 0005: yes to both, by running the engine in a second Pyodide worker spawned from Flet's Python. No patch to `python-worker.js` is needed.
- Warm-start timing with the service worker cache populated (my "warm" run did not isolate cache effects).
- Whether the rive wasm request can be dropped.
