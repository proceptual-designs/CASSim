# 0031: M3 and M4 plan: shared data, fast page switching, no SciPy

Status: accepted 2026-11-13 (Simon). Requirements: FR-DOC-008, FR-DOC-009, FR-SHEET-001 to 003, FR-STAT-001 to 005, FR-GRAPH-001 to 007, FR-NOTE-001, NFR-PERF-006. The slices are in PLAN.md section 8. Nothing here is built yet; the spikes below can change the detail, and their results are recorded here when they run.

## What the emulator shows

Checks 4 and 5 (`docs/testing/emulator-sheet-results.md` E9, E-onevar; `emulator-graphs-results.md` D5/D6) show that within one Problem:

- a spreadsheet column named `xs` **is** the list variable `xs`: `xs[2]:=20` on the Calculator page shows in the cell at once;
- One-Variable results placed in the sheet are live formulas that recompute when the source list changes;
- a function typed on the Graphs page (`f1`) and one defined on the Calculator page (`f`) are the same Problem functions, usable from either page.

So data is shared by every page of a Problem, and a page is a view of it.

## Decisions

### 1. One owner for data

- **The Problem's scope in the engine worker is the only copy of the data.** Columns, plotted lists and graph functions are Problem variables. No page keeps its own copy of values.
- **The document stores definitions and view state only**: cell text, formulas, column names, plot type, axis variables, windows, graph entries. Values are recomputed on load, as Calculator results are today.
- **Recalculation runs in the engine.** The sheet's dependency graph lives in `sheet/` and runs beside the `Session`. After any op that changes a variable, the engine recalculates what depends on it (formula columns, cell formulas, live statistics columns) before it replies, so a reply is always consistent.
- **Each variable has a revision number**, raised on every store or delete. A reply carries only the variables that changed since the last reply, as typed payloads (numbers, and the display text of each element). The UI keeps them in a per-Problem store. A page records the revisions it drew and redraws only when one of them is older than the store's.

Two parts of today's code do not scale to sheet data and change in slice 3.0: `EngineCore.apply` formats every variable on every reply, and `App.refresh` writes the whole document to localStorage on every refresh. The reply becomes a delta; the autosave is debounced and moves to IndexedDB (verified in decision 0003).

### 2. Fast page switching

- **Each page's data is kept alive: its model and its cached scene.** Switching pages builds the new page's controls from that data. It never waits for the engine. If a dependency has a newer revision the page refreshes after it is shown, with the busy mark. *(Changed by spike A: the first draft kept the controls alive and changed `visible`, which is slower.)*
- **The sheet and the plots are drawn on a canvas, visible cells only, one text shape per column** (spike A). Decision 0004 measured about 0.7 ms per shape, so a control per cell for 2,500 rows is not possible.
- **Graphs are sampled in the UI worker.** The engine compiles each function once to source that uses only Python's `math`; the UI worker evaluates it for pan, zoom and trace with no round trip. A function that will not compile is sampled by an engine op.
- **Measured, not enforced** (NFR-PERF-006): `tools/switchtime.py`, beside `tools/loadtime.py`. The aim is 100 ms on a desktop and 250 ms on a mid-range phone from the key press to the new page drawn.

### 3. Split pages

A page has one or two panes. Quick Graph, Summary Plot, Show Residual Plot, the shaded Normal Cdf and the Graphs table all split the page on the emulator. M3 builds two panes only (side by side or one above the other); Custom Split and the three- and four-pane layouts are greyed.

### 4. No SciPy or NumPy in the build

`src/` imports neither today, and check 5 found the pure-Python statistics agree with SciPy to every digit the emulator shows (22 commands). The remaining distributions, tests and intervals are written on mpmath, which already ships. SciPy stays a test-only dependency, used as an independent check. This avoids its download and first-use pause and keeps native builds possible (PLAN.md section 13). FR-STAT-004 and NFR-PERF-003 are reworded.

### 5. Scope

- **In (Must):** the categorical charts (Dot Chart, Bar Chart, Pie Chart) and Force Categorical X, because General Maths uses them (Simon, 2026-11-13).
- **Greyed, not built:** the movable line, Data Capture, 3D Graphing, Plane Geometry and the Geometry menu, Multiple Regression, ANOVA 2-Way.
- **Notes** is text only in M4; maths boxes are a later Could.
- **Graph entry types** are built in this order: function, scatter plot, parametric, relations and conics, polar, sequence, differential equations.

### 6. Structure

The triggers of PLAN.md section 12 rows A1, A4 and A5 are met by slice 3.0:

- A4: `Document`, `Problem`, `Page` and the serialiser move to `doc/`. A page model is a small protocol (kind, keys, menu, scene, dependencies, undo, serialise); page types are registered by the profile, not switched on in `Document`.
- A1: engine ops and replies become `TypedDict`s checked at the worker boundary, since the protocol gains ops for cells, sampling and analysis.
- A5: `sheet`, `stats` and `graph` must not import `device` or `app`; the architecture test gains those rules as each package gets code.

## Spikes

Each is a short script under `spikes/` with its numbers added to this file. **A and B are done (results below); C and D are not.**

| Spike | Question | Decides |
|---|---|---|
| A View cache and grid | Time to switch between three built views (a 30-row history, a 2,500-row sheet, a graph with three curves) by visibility and by rebuilding; cursor-move and scroll time for a canvas grid against pooled text controls. Desktop Chromium and the Pixel 6. | The view cache and the grid renderer (3.0, 3b) |
| B Data transfer | Time to format and send a 2,500-element list across `postMessage`; `xs^2`, `SortA` and `OneVar` at that size; whether plain numbers need a path that avoids SymPy; whether Cancel and document load can restore a snapshot of variables in place of replaying the journal. | The reply format and the rebuild after Cancel (3.0, 3a) |
| C Local sampling | SymPy expression to `math` source, evaluated in the UI worker: 2,000 points for each of three curves per frame; pointer pan and pinch latency with throttling (left unmeasured by 0004); `Path` fills for integrals and inequalities. | The sampler and the gesture handling (4a, 4b) |
| D Implicit curves | Marching squares in pure Python at screen resolution for relations and conics. | Slice 4d only |

Spike B matters most. The rebuild after a Cancel replays every op, which grows with each cell edit, and a cell holding `=rand()` replays to a different value.

## Spike results (2026-11-13)

Both ran in headless Edge on Simon's Windows laptop. **Neither has been run on a phone**, so the 250 ms aim of NFR-PERF-006 is untested.

### Spike A: page switching and the grid

`spikes/spike_a_web`, run by `spikes/run_web_spike_a.py`. Times are the Python side of `update()` plus one event-loop yield (diff, serialise, send), as in spike 3; the browser held 55 to 60 frames a second throughout.

Switching between a 30-row history, a 10 by 20 sheet and a graph of three 2,000-point curves:

| Way of switching | Per switch | To the sheet | To the graph |
|---|---|---|---|
| All three views kept in a Stack, `visible` changed, parent updated | 67 ms | 46 ms | 49 ms |
| The same, updating only the two views that changed | 38 ms | 57 ms | 59 ms |
| Controls rebuilt from data on each switch | **19 ms** | **16 ms** | **18 ms** |

Keeping the controls alive is the slowest, because Flet compares every kept view again on each update, and comparing 6,000 curve points costs more than sending them.

Drawing the sheet's visible cells, per cursor move and per one-row scroll:

| Renderer | Handheld (4 by 5) move / scroll | Computer (10 by 20) move / scroll |
|---|---|---|
| One canvas `Text` per cell | 13 / 11 ms | 76 / 72 ms |
| One multi-line canvas `Text` per column | 5 / 6 ms | **11 / 27 ms** |
| A pooled `ft.Text` control per cell | 2 / 3 ms | 9 / 31 ms, with 13 frame gaps over 50 ms |

**Outcome.**
- Decision 2 is changed: what is kept alive is each page's **data** (its model and its cached scene: sampled points, cell texts), not its controls. A switch builds the controls from that data. Hidden control trees are never left in the page.
- The grid is drawn as one multi-line canvas text per column, with the cursor and selection on a separate layer so a cursor move sends no text.
- Not tested: mixed alignment in one column (numbers right, text left; probably two texts per column), clipping of a cell too wide for its column, and the real `Markdown` maths rows of the history (the spike used plain text).

### Spike B: large lists in the engine

`spikes/spike_b_data.py`, natively and in Pyodide (`spikes/run_web_spike_b.py`, which runs it in a worker against a published build's `cassim.zip`). Pyodide on the desktop is about twice as slow as native. For a list of 2,500 decimals, in Pyodide:

| Operation | Time |
|---|---|
| `xs:={...}` typed as one entry | 0.51 s |
| `sq:=xs^2` | 0.56 s |
| `OneVar xs` | 0.16 s |
| `SortA xs` | 0.05 s |
| `LinRegMx xs,lin` | 0.29 s |
| The variable list as every reply builds it today (three such lists) | 0.68 s |
| Display text of the 2,500 elements of one list | 0.15 s |
| The same as JSON (27 kB) across `postMessage`, and parsed | 1 ms |
| Rebuild by replaying four entries | 1.6 s |
| Rebuild by restoring three variables from their text | 1.9 s |

Whole numbers and exact fractions are about a third faster. At 500 elements everything is under 0.25 s.

**Outcome.**
- The delta reply is confirmed: building the whole variable list costs more than the operation it follows. Sending data is free; formatting it is the cost.
- About half of each entry's time is formatting the result text, twice (as shown, and to 14 digits). A store that comes from the sheet needs neither, and cell text is formatted only for the cells in view.
- Restoring from text is no faster than replaying, since parsing the list is most of the cost. The journal stays, and the sheet's edits are journalled as its current contents, not as a history of edits.
- A fast path for plain numbers is not built now. Squaring 2,500 Python floats and formatting them takes 6 ms natively against 290 ms through SymPy, so it is available if a phone needs it; it would have to keep exact fractions and symbolic elements on the present path.
- Found on the way: `xs[2]:=20` gives "Not implemented yet: indexed assignment". Slice 3a needs it.

## Emulator evidence still needed

Check 6 (`docs/testing/emulator-pages-capture.md`) parts E and F are needed before slices 3a and 3b settle, part D before 4b. Check 6 did not cover sharing, so parts G (shared data), H (split pages), J (categorical charts) and N (Notes) are in `docs/testing/emulator-sharing-capture.md`.

## Not decided

- How a cell holding `=rand()` keeps its value across a rebuild after Cancel (the journal replays it to a new value). Part G of the emulator check shows what the handheld does on recalculation; decide in slice 3a.
- Timings on the Pixel 6 for both spikes.
- Where the autosave size limit sits for a document with large lists; share links already fall back to a file above about 2,000 characters.
