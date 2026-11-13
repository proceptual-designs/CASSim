# SDD-07. Data pages: Lists & Spreadsheet, Data & Statistics, Finance

Status: the foundations built in M3 slice 3.0 (2026-11-13), and the design of slices 3a to 3e, which are not built. Requirements: FR-DOC-008, FR-DOC-009, FR-SHEET-001 to 003, FR-STAT-001 to 005, FR-CALC-007, NFR-PERF-006, FR-DOC-003. Decisions: 0031 (plan, spikes A to D, switch timings), 0032 (devices and page types), 0026 (warnings), 0003 (IndexedDB).

## Problem

On the handheld every page of a Problem sees the same variables. A spreadsheet column named `xs` is the list `xs`: `xs[2]:=20` typed on a Calculator page changes the cell at once, and a regression placed in the sheet recalculates when its list changes. In CASSim the variables live in the engine worker, apart from the UI, so pages must draw from a copy that the engine keeps up to date without sending everything on every key, and a page switch must not wait for the engine.

## Built in slice 3.0

| Part | Where | Role |
|---|---|---|
| Revisions | `core/scope.py` | Every store or delete raises the scope's revision and records it against the name: `revision_of`, `changed_since`. |
| Delta reply | `device/engine.py` `EngineCore` | A reply carries only the rows changed since the last reply for that Problem, and deleted names. Every row is sent after a settings change, for a new Problem and after `reset`. Only those rows are formatted (`Session.rows`). |
| Typed protocol | `device/engine.py` | Ops and replies are `TypedDict`s; `check_op` checks ops entering the engine, `check_reply` replies leaving the worker (`app/web.py`). |
| UI store | `device/engine.py` `VariableStore` | One per Problem, inside its `RemoteSession`. Applies each delta, keeps a revision per name of its own (so it keeps rising after a Cancel replaces the engine) and skips rows that did not change. |
| Scene | `graph/scene.py` | Backend-neutral shapes in named layers (FR-GRAPH-006). |
| Canvas | `app/scene_canvas.py` | A scene as Flet canvas shapes, one canvas per layer. |
| Warning mark | `app/warning.py` | The shared triangle (FR-CALC-007), first used by the Calculator history. |
| Autosave | `app/shell.py`, `app/web.py` `TextStore`, `devices/nspire/ui/app.py` | Written 0.5 s after the last change and at once when the tab is hidden, to IndexedDB in the browser. |
| Switch timing | `tools/switchtime.py` | Times page switches in the built site (NFR-PERF-006). |

A page reads its data through its Problem's session: `variables()` and `revision_of(name)`, the same on a local `Session` (desktop) and a `RemoteSession` (browser).

## Data flow for a page

1. A page model records, for each variable it draws, the revision it drew.
2. A user action becomes ops on the Problem's `RemoteSession` (an entry, a cell store, a sort).
3. The Runner sends them; the engine applies them, recalculates what depends on the changed variables (3a), and replies with the delta.
4. `accept` applies the delta to the store. Each visible page compares its recorded revisions with the store's and redraws only if one is newer.
5. A hidden page does the same check when it is shown: it draws at once from its cached scene, then refreshes if anything it uses moved on.

## Page models and scenes

- A page type (`doc/document.py` `PageType`) makes, saves and loads its own model; the device registers its types (decision 0032). The sheet and the plots are new Nspire page types in `devices/nspire/pages/`.
- A model keeps its last `Scene`. A switch builds the canvas from it without the engine (spike A: rebuilding controls from kept data, 19 ms, beat keeping hidden controls alive, 38 to 67 ms).
- A cursor move replaces only the cursor layer, so no text is sent (`Scene.replace`).
- The sheet draws visible cells only, one multi-line `Label` per column (`column_label`; spike A: 11 ms a move at Computer size against 76 ms for a text per cell). Numbers right-aligned and text left-aligned in one column will need two labels per column; not yet tried.

## Slices to come

- **3a, sheet engine (`sheet/`, headless).** Cells, columns linked to list variables, formula columns, `a[]`, ranges, `$` references, a dependency graph that recalculates in the engine before it replies, indexed assignment (`xs[2]:=20`), voids, `#UNDEF` and `#ERR`, Data Loss and Conflict Detected, sort, fill, insert and delete. Behaviour from `docs/testing/emulator-sheet3-results.md`. A store from the sheet skips result formatting (spike B). A `=rand()` cell draws a new value when a Cancel rebuilds the engine, as Ctrl+R does (decision 0031). **Built 2026-11-14:** `sheet/refs.py`, `sheet/sheet.py`, `sheet/actions.py`, and the engine side in `device/sheets.py` (the `sheet` op: cell, formula, name, fill, sort, insert, delete, generate, recalculate, view, restore, drop; replies carry each changed page's revision, dialogs, and the cells of a view).
- **3b, sheet page.** The grid scene, keys and touch routes (decision 0031 item 7), the per-page scene cache, the sheet in `tools/switchtime.py`. Part 1 built 2026-11-14: the page model (`devices/nspire/pages/spreadsheet.py`) keeps the sheet's definitions from each reply's `edits` and the formatted cells of its last `view`, and talks to the engine through `device/sheet_link.py` (`LocalLink` here, `RemoteLink` through the Runner's outbox and `RemoteSession.sheet_inbox`). A view taken before a change in the same batch is not sent. The journal keeps one `restore` per sheet, where its last op was; an entry made between two edits of a sheet replays against its later state. A sheet whose page is deleted is dropped from the engine, so its lists are free again, and an undone delete restores it. Part 2 built 2026-11-14: `devices/nspire/sheet_scene.py` makes the grid a scene of four layers and maps taps to cells; `devices/nspire/ui/sheet_view.py` draws it, keeping the canvas of every layer that did not change, so a cursor move sends only the cursor layer. A switch to a sheet page takes 66 ms on the laptop.
- **3c to 3e.** Statistics from the sheet, the Data & Statistics page with the categorical charts (FR-STAT-005), Quick Graph, Summary Plot, CSV and xlsx. Statistics stay pure Python and mpmath (no SciPy or NumPy in the build).
- **Split pages (FR-DOC-009) and file schema 2.** A page holding two panes needs emulator check 6 part H, which has not been run. The schema bump and its migration come with it.

## Measured

| What | Result | Source |
|---|---|---|
| Switch to a Calculator page with 15 entries, laptop | about 125 ms, of which our Python is about 40 ms | decision 0031 |
| Cursor move in a 10 by 20 grid | 11 ms | spike A |
| `sq:=xs^2`, 2,500 decimals, Pyodide | 0.56 s | spike B |
| Curve frame at one point a pixel column | 6 to 7 ms | spike C |

None of these has been measured on a phone.
