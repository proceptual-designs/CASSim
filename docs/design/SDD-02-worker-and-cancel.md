# SDD-02. Engine worker, Cancel and restore

Status: describes the code at 2026-11-08 (M2e). Requirements: FR-EVAL-006, NFR-REL-001, NFR-REL-002, NFR-PERF-003; Cancel within 1 s (SRS 5.1). Decisions: 0005 (spike 4), 0016 (publish and cancel), 0018, 0027 (start-up time).

## Problem

Flet runs the UI, the document model and every event handler in one Pyodide worker. A long calculation there would stop Cancel from ever being handled. Nothing in that worker can interrupt Python, and Pyodide's interrupt buffer needs `SharedArrayBuffer`, which needs COOP and COEP headers that plain static hosting cannot send. So the maths runs in a second worker, and Cancel is `worker.terminate()`.

## Parts

| Part | Where | Role |
|---|---|---|
| `EngineCore` | `device/engine.py` | One `Session` per Problem id. `apply(problem, ops)` runs a list of ops and returns the last eval's result and a snapshot. `reset(journals)` rebuilds every session by replaying journals. Pure Python. |
| `Engine` (protocol) | `device/engine.py` | Async transport: `run`, `reset`, `cancel`. |
| `LocalEngine` | `device/engine.py` | `EngineCore` in-process. `cancel()` returns False. Used by tests and by `CASSIM_ENGINE=remote` on the desktop. |
| `WorkerEngine`, `_Worker` | `app/web.py` | Browser only (`sys.platform == "emscripten"`). Spawns a module `Worker` from a Blob URL that boots its own Pyodide, unpacks `cassim.zip` (fetched while Pyodide starts; it holds SymPy and mpmath as bytecode) and creates an `EngineCore`. |
| `RemoteSession` | `device/engine.py` | The UI's stand-in for a `Session`. Answers `is_function` and `variables` from the last snapshot, queues settings changes in an outbox, and keeps a journal of every op the engine has accepted. |
| `Runner` | `device/runner.py` | Owns the status (`idle`, `busy`, `restarting`), sends the Calculator's pending entry, finishes it, and implements `cancel`, `sync` and `load`. |
| Packaging | `tools/publish.py` | `write_engine_zip` builds `cassim.zip` (`cassim` without the UI, SymPy and mpmath, as bytecode) served beside the site. |
| `local_session` | `device/engine.py` | Makes an in-process `Session` with a deferred import, so the UI worker never loads SymPy (0027). |

## Protocol

Everything crossing the worker boundary is JSON, so it survives `postMessage`.

- **Op:** a dict. `{"op": "new_problem"}`, `{"op": "settings", "values": {...}}` (every field as a string), `{"op": "eval", "line": ..., "approximate": bool}`.
- **Request** (page to worker): `{"id": n, "op": "boot", "pyodideUrl": ..., "zipUrl": ...}` once; then `{"id": n, "op": "message", "message": "<json>"}` where the inner message is `{"op": "run", "problem": id, "ops": [...]}` or `{"op": "reset", "journals": {...}}`.
- **Reply:** `{"id": n, "ok": true, "value": "<json>"}` or `{"ok": false, "value": "<error text>"}`, which becomes an `EngineError`.
- A `run` reply holds `result` (`text`, `latex`, `error`) and a snapshot (the variable list).

`_Worker` keeps a `pending` map from id to future, so replies are matched however they interleave.

## An entry, step by step

1. The Calculator is on a `RemoteSession` (`deferred = True`), so Enter only sets `Calculator.pending`.
2. `Runner.evaluate` takes the session's queued ops, appends the `eval` op, sets status to `busy` and awaits `engine.run`.
3. The reply is passed to `session.accept(sent, reply)`, which adds the ops to the journal and stores the snapshot, then `calculator.finish` writes the history row.
4. An `EngineError` (a crashed worker) becomes a result row with that text. A TI error is an ordinary result with `error` set.

## Cancel and restore

`Runner.cancel` returns False unless status is `busy` and `engine.cancel()` is True.

1. `WorkerEngine.cancel` terminates the active worker (0.7 to 1.8 ms measured, decision 0016), fails its pending futures and makes the spare the active engine, or starts a new `_Worker` if there is none.
2. The status becomes `restarting` and the awaiting task is cancelled. `evaluate` catches `CancelledError`, clears `pending` and leaves the entry in the editor as typed.
3. `engine.reset` sends every `RemoteSession`'s journal to the new engine, which replays them into fresh sessions. Variables, functions, Problems and settings come back. The journal holds only accepted ops, so the cancelled entry is not in it.
4. Status returns to `idle`, and `WorkerEngine.reset` starts a new spare.

**Measured (0016):** Cancel to a ready, restored engine takes 16 to 19 ms with the spare already booted. Replay is linear at about 10 ms an entry. Flet's loop and the main thread stay at 60 fps throughout.

**The spare.** Booting an engine took 7 to 9 s in 0016 and about 2 to 4 s since 0027, still too slow to do on demand, so a spare is booted 3 s after the active engine is ready at start-up (`SPARE_DELAY`, so it does not compete with the autosave replay) and at once after each reset. If Cancel is pressed again before the replacement spare is ready, the swap has to boot a worker; the measured worst case is about 22 s. This is the known weak spot in 0016.

## Loading a document

`Runner.load` replays a saved document through the engine, entry by entry, with `serialize.replay_steps`, so results are recomputed under the current engine and settings. If the user cancels, loading raises `CancelledError`.

## Settings changes

`RemoteSession.set` and the settings setter queue a `settings` op in the outbox. `Runner.dirty` tells the app one is waiting and `Runner.sync` sends them, so the variable list is redrawn in the new format before the next entry.

## Boundaries and gaps

- Desktop and native builds run `LocalEngine`, so Cancel is refused there (PLAN.md section 13, item 2).
- Only one run is in flight at a time. `App.kick` starts a queued entry or settings sync only when the runner is idle, and the status line reads "Calculating... press Esc to cancel" while one runs.
- A crashed worker is reported as a result row; there is no automatic restart other than Cancel.
- Tests: `tests/device/test_engine.py` (RemoteSession, Runner, and Cancel through a `StuckEngine` test double), `tests/e2e/test_spike_cancel.py` and `tests/e2e/test_flows_browser.py` (the real worker in Chromium).
