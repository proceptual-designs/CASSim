# 0027: start-up time

Status: accepted 2026-11-12. Requirements: NFR-PERF-001, NFR-PERF-002, NFR-PERF-005. Measured with `python -m tools.loadtime` (new), headless Edge on a Windows laptop, local server below `/CASSim/`. Simon reported about 11 s to load on a Pixel 6 before this change.

## What the time went on

`tools/loadtime.py` times console markers from navigation. Before this change (warm = a reload served by the service worker, which is what an installed app does):

| Milestone | Cold | Warm |
|---|---|---|
| Flutter engine started | 2.3 | 0.3 |
| UI worker runs `main.py` | 5.8 | 2.9 |
| First screen sent | 9.1 | 6.2 |
| Keys work (settings and autosave back) | 9.2 | 6.3 |
| Engine ready (Enter gives an answer) | 13.8 | 10.7 |
| Spare engine ready (instant Cancel) | 18.3 | 15.2 |

1. **The UI worker imported SymPy, which it never uses.** `cassim.app.state` imported `core.session` to name the default session class, and that pulls in the catalog and SymPy. In the browser every Problem has a `RemoteSession`, so the 3.3 s between "runs main.py" and "first screen" was spent loading a CAS that only the engine worker needs. On a phone that is the largest part of the wait.
2. **micropip ran at every start.** `flet publish` puts `flet` in `requirements.txt`, so the UI worker loaded micropip, resolved Flet's dependencies and installed four wheels on each start; the staged `main.py` then asked micropip for SymPy and PyYAML as well.
3. **Nothing was precompiled.** Pyodide's file system is in memory, so each start compiled every imported module from source again: Flet in one worker, SymPy and `cassim` in two (active and spare).
4. **The spare engine competed with start-up.** It boots as soon as the first engine is ready, which on a phone is while the autosaved document is still replaying.

Fetching was not the problem: reading a 9.6 MB `.wasm` from the service-worker cache takes about 25 ms, and compiling it about 20 ms.

## Decisions

- **The UI worker never imports SymPy.** `Result`, `VariableInfo` and `latex_for_markdown` move to `core/results.py`, which imports nothing heavy. `device.engine.local_session` makes a `Session` with a deferred import, and is the default session factory everywhere the UI used `Session`. `RemoteSession.is_function` uses `core/builtin_names.py`, a generated copy of the catalog's function names (`python -m tools.builtin_names`; `tests/unit/test_builtin_names.py` fails when it is stale, and checks in a subprocess that importing the app loads no SymPy, mpmath, PyYAML, session or catalog module).
- **Both archives carry their packages, as bytecode.** `tools/publish.py` replaces Flet's `app.tar.gz` with one holding `main.py`, `cassim` and, under `__pypackages__`, Flet, repath and six (Flet's worker puts that folder on `sys.path`; with no `requirements.txt` micropip is never loaded). `cassim.zip` holds `cassim` without the UI plus SymPy and mpmath, so the engine worker calls no `loadPackage`. Everything is compiled by the build's Python 3.14 (the same minor version as Pyodide 314; the build checks and ships source if they ever differ) with unchecked-hash `.pyc` files. Third-party packages ship as `.pyc` only; `cassim` keeps its source beside `__pycache__` so tracebacks show lines. Wheels are downloaded once into `%TEMP%/cassim_wheels`.
- **The spare engine waits 3 s after the first engine is ready** (`SPARE_DELAY` in `app/web.py`). After a Cancel it is started at once, as before.
- **The engine still boots in parallel with the UI**, not after the first frame. It is in its own worker, so it does not slow the UI worker, and starting it later would only delay the first answer.

## Result

Same machine, interleaved runs (median of three warm reloads):

| Milestone | Cold before | Cold after | Warm before | Warm after |
|---|---|---|---|---|
| UI worker runs `main.py` | 5.8 | 4.9 | 2.9 | 2.6 |
| First screen sent | 9.1 | 4.9 | 6.2 | 2.6 |
| Keys work | 9.2 | 5.1 | 6.3 | 2.7 |
| Engine ready | 13.8 | 6.7 | 10.7 | 4.3 |
| Spare ready | 18.3 | 11.3 | 15.2 | 9.0 |

The first screen arrives about 3.5 s sooner and the engine about 6 s sooner. The site grows from 83.6 to 90.3 MB (94 files), because SymPy's bytecode is larger than its wheel; it is downloaded once and cached.

## Not done, and why

- **Lazy imports inside the engine** (load the catalog's calculus or matrices only when first used). The engine now starts in about 1.7 s after Pyodide on this machine and boots in the background, so the gain is small against the risk of a first-use pause in the middle of an exam question. Worth doing per module if a phone shows the engine as the bottleneck.
- **A Pyodide memory snapshot** of the booted engine. It would make engine and spare boots near-instant but is experimental in Pyodide and ties the build to one exact Pyodide version; revisit when it is stable.
- **Fewer Flet controls in the keypad and entry line.** Responsiveness after start-up is bounded by Flet's diff-and-send per key press; profile it on the phone before changing anything.
- **Not verified on a phone.** The figures above are desktop Chromium. Run the site on the Pixel 6 and record the numbers here; NFR-PERF-001 and 002 ask only that they are measured.
