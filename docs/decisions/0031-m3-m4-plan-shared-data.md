# 0031: M3 and M4 plan: shared data, fast page switching, no SciPy

Status: accepted 2026-11-13 (Simon). Requirements: FR-DOC-008, FR-DOC-009, FR-SHEET-001 to 003, FR-STAT-001 to 005, FR-GRAPH-001 to 007, FR-NOTE-001, NFR-PERF-006. The slices are in PLAN.md section 8. Nothing here was built when this was written; the spikes below could change the detail, and their results are recorded here.
Since changed (note added 2026-11-25): M3 is mostly built and M4 is in progress (SDD-07 and PLAN.md section 8 hold the current state). The limit of two panes a page was replaced by up to four (0034 item 2); Custom Split stays greyed.

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
- **Graphs are sampled in the UI worker.** The engine compiles each function once to source that uses only Python's `math`; the UI worker evaluates it for pan, zoom and trace with no round trip, at one point a pixel column, and redraws inside the gesture's event handler (spike C). A function that will not compile is sampled by an engine op.
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

### 7. Behaviour, not look; touch first (Simon, 2026-11-13)

- The emulator captures record behaviour. CASSim matches what a function does (which cells move, what a dialog asks, what is recalculated), not how the emulator draws it: cursor shapes, the hand pointer while resizing, the I-beam and similar are not copied.
- Every function the emulator reaches by a key chord, right-click or mouse gesture gets a conventional touch route in CASSim: tap, long-press for the context menu, swipe, drag handles and on-screen menus. Key chords stay as shortcuts where a keyboard is present.
- **Keep the animation.** When its data or plot type changes, a Data & Statistics plot moves its points to their new places over about a second (a linear interpolation), as the emulator does. This is behaviour, not look: it shows the student where each case went.

## Spikes

Each is a short script under `spikes/` with its numbers added to this file. **All four are done (results below).**

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

### Spike C: sampling in the UI worker, fills and gestures

`spikes/spike_c_web`, run by `spikes/run_web_spike_c.py`, which drags the mouse, pinches with two touches (through the DevTools protocol) and turns the wheel while the app redraws. `spikes/spike_c_compile.py` is the engine side. Headless Edge on the laptop; the browser held 60 frames a second in every phase.

Sampling 2,000 points of one function, in Flet's Pyodide worker:

| Function | Time |
|---|---|
| `sin(x)+0.3*sin(7x)` | 0.5 ms |
| `x^3/10-x`, `1/x`, `exp(-x^2/2)`, `tan(x)` | 0.1 to 0.3 ms |
| `sqrt(x)` with half the points outside the domain | 1.3 ms |

The source is pasted into one generated list comprehension, and a loop with a `try` around each point is used only when a point raises. Calling a function for each point is about half as fast again. Making the source from SymPy takes under 1 ms a function (15 ms for the first, which loads the printer), and compiling six sources in the UI worker takes 2 ms.

One frame of three curves (sample, map to the screen, send):

| What is drawn | Per frame |
|---|---|
| Three curves, 2,000 points each | 19 to 21 ms |
| Three curves, 640 points each (one a pixel) | **6 to 7 ms** |
| The same at 2,000 points, with two filled `Path` regions of 600 and 2,000 points | 60 to 67 ms |
| The same at 640 points, fills of 190 and 640 points | 21 to 25 ms |
| Curves at 640 points, fills at 160 points | **12 ms** |
| 3,000 separate line segments in one `Points` shape (an implicit curve) | 12 to 15 ms |
| 600 separate segments | 3 to 4 ms |

Sampling is under a tenth of the frame. The rest is building the shapes and Flet's `update()`, and a `Path` costs about four times as much a point as a `Points` shape.

Following the pointer (120 mouse moves, 118 pinch events or 60 wheel turns, sent every 16 ms):

| Handling | Redraw | Result |
|---|---|---|
| Redraw inside each event, 640 points | 6 to 7 ms | Keeps up for pan, pinch and wheel; 4 to 8 ms behind at the end |
| Redraw inside each event, 2,000 points | 14 to 18 ms | Falls behind: the 1.9 s drag took 3.0 to 3.4 s to send |
| The same with `drag_interval=33` | 12 to 14 ms | Keeps up at half the events |
| Events only mark the view; one task redraws the latest (2,000 points) | 13 ms | Worse: the task waited 45 ms for its turn each time and finished 2.7 s late |
| The same at 640 points | 5 ms | 0.5 s late over the drag |
| Move the drawn canvas with `left` and `top`, resample at the end | 32 to 38 ms | Slower than redrawing: the update compares the canvas's unchanged points |

**Outcome.**
- Local sampling is confirmed. Curves are sampled at one point a pixel column of the plot (about 320 on the Handheld, 640 on the Computer), not a fixed 2,000; more points are added only where a curve is steep.
- A pan, pinch or wheel event resamples and redraws inside its handler. No redraw task, and no moving of the drawn canvas. Pinch comes through the scale events, which also carry a one-finger drag, so the Graphs page uses those. `drag_interval` is the remedy if a phone falls behind.
- Fills use a quarter of the curve's points, and a filled region is drawn only while it is on show.
- The compiled source must come from CASSim's own printer over a fixed list of names, not from `sympy.pycode` as it stands, since the UI worker runs it with `exec`: only `math` functions, arithmetic and conditional expressions, checked before it is sent.
- Not tested: the asymptote rule (the spike breaks a curve where it jumps more than the window height), trace and analysis points, and touch input on a real phone.

### Spike D: implicit curves

`spikes/spike_d_implicit.py`: marching squares in pure Python, with the same generated-comprehension sampling over a grid, natively and in Pyodide. In Pyodide:

| Window and cell | Grid | Circle | `sin(x)+cos(y)=1/2` | `sqrt(x)+sqrt(y)=2` (points outside the domain) |
|---|---|---|---|---|
| Handheld (320 by 212), 4 px | 80 by 53 | 2 ms | 2 ms | 7 ms |
| Handheld, 2 px | 160 by 106 | 7 ms | 8 ms | 21 ms |
| Computer (640 by 424), 4 px | 160 by 106 | 6 ms | 8 ms | 20 ms |
| Computer, 2 px | 320 by 212 | 24 ms | 31 ms | 82 ms |

A circle's points are within 0.04 px of the true circle at 4 px cells, because the crossing is interpolated along each cell edge. A relation gives 100 to 2,000 segments, which draw in under 15 ms (spike C).

**Outcome.**
- Marching squares in pure Python is fast enough: 4 px cells while a gesture is in progress, 2 px when it ends. No compiled code and no NumPy.
- A relation with a jump (`y=tan(x)`) gets a false line along each asymptote. Slice 4d has to drop a crossing where the values on either side are large.
- Not tested: inequalities as filled regions (the cells are known, so a fill by cell is possible), and joining the segments into polylines.

### Page switch timings (tools/switchtime.py, 2026-11-13)

The first measurement of NFR-PERF-006, on today's Calculator pages: two pages of 15 `expand` entries and an empty one, 20 switches with alt+arrow, from the key press to the app's `CASSIM: PAGE` line (sent once `page.update` returns). Headless Edge on the laptop.

| To | Median | Max | Our Python: build controls / `page.update` |
|---|---|---|---|
| A page with 15 entries | 126 to 130 ms | 147 ms | 9 to 10 ms / 30 to 33 ms |
| The empty page | 58 ms | 62 ms | 3 ms / 12 ms |
| The same, with Chromium's CPU throttle at 4 | 450 to 730 ms | 1,280 ms | 4 to 12 ms / 15 to 38 ms |
| A Lists & Spreadsheet page with a 30-row column (slice 3b, 2026-11-14) | 66 ms | 73 ms | 3 ms / 16 ms |

- On the desktop a full page is a little over the 100 ms aim; an empty one is well under.
- Our Python is about 40 ms of it. The rest is the key's route from Flutter into the Python worker and back, which is fixed: the empty page still takes 58 ms. The throttle slows the browser's main thread (Flutter) and not the worker, and the switch grows five-fold while the Python part does not. So on a phone Flutter's side, not the page code, is what to watch.
- The time Flutter then takes to draw the new page is not included.
- The sheet page is drawn at once from its kept view (its cells as the engine last formatted them), with no wait for the engine, and costs less than a Calculator page: the grid is four canvases (grid, heads, cells, cursor), not a control per line.
- Not yet run on a phone. Graphs joins the cycle when it is built (4b).

### M3 data-page timings (2026-11-18)

Headless Chromium-family browser on Windows, no CPU throttle; two Calculator pages with four
entries each, a spreadsheet with a 30-row formula and dependent formula column, and a Data &
Statistics page using the named list. `tools/switchtime.py` recorded 12 switches (from the key
press to the app's PAGE message) and six recalculations (from Enter through navigating to the
updated dependent B1 value). These include browser and UI communication, not just engine time.

| Measurement | Samples | Median | Max |
|---|---:|---:|---:|
| Calculator page 1.2 switch | 3 | 167 ms | 212 ms |
| Spreadsheet page 1.3 switch | 6 | 118 ms | 145 ms |
| Data & Statistics page 1.4 switch | 3 | 133 ms | 135 ms |
| Dependent-cell recalculation | 6 | 876 ms | 1,310 ms |

This is one desktop run, not a performance limit or a phone measurement. The switch message
precedes Flutter's final drawing; the recalculation measurement includes a Right key and polling.

## Emulator evidence still needed

Check 6 (`docs/testing/emulator-pages-capture.md`) parts E and F are needed before slices 3a and 3b settle, part D before 4b. Check 6 did not cover sharing, so parts G (shared data), H (split pages), J (categorical charts) and N (Notes) are in `docs/testing/emulator-sharing-capture.md`.

The first run of check 6 (2026-11-13) did most of parts E and F: `docs/testing/emulator-sheet3-results.md` and `emulator-stats3-results.md`, with what is left in `emulator-check6-remaining.md`. Points from it that shape slices 3a and 3b:

- A cell entry without `=` that is not a plain number or fraction (`2^0.5`, `sqrt(2)`, `pi`) is kept as typed and shown left-aligned, but formulas still use its value. Approximate mode shows the decimal point on existing numbers (`5.`), and redisplays the column; text entries stay as they were.
- Errors: `=1/0` shows `#UNDEF` with no dialog; a formula that gives a list (`=randint(1,6,5)`) or a range used as a value (`=f1:f3`) gives a "Syntax Error in Cell" dialog, then `#ERR`; an undefined name or a circular reference gives a dialog and leaves the cell in edit mode. `=a1+"x"` shows `"x"+3`, unevaluated.
- `mean` over a range skips empty cells (`mean(c1:c6)` with C5 and C6 empty is the mean of four), and `_` enters a void cell.
- Naming a column after a list that already exists replaces the column's contents with no dialog; naming it after a list already on the sheet gives "Cannot link to same list/variable twice".
- Sort moves whole rows across the selected columns, asks first ("Data Loss") when the range holds a formula column, and turns that column's formula into constants.
- Fill copies a formula down with relative references, `$` references fixed. Generate Sequence writes a `seqgen(...)` column formula (not built in the engine yet).
- Ctrl+R recalculates the sheet, and a `randint` cell gets a new value each time.
- Data & Statistics: a regression adds `stat.freqreg`, `stat.resid`, `stat.xreg` and `stat.yreg` to the variable lists; Sort (List, Value, Alpha order) is live only on categorical charts; points selected on one plot show as selected on the other plots of the Problem.

The second run (2026-11-13) did parts G, H and J and part of D: `emulator-sharing-results.md`, `emulator-split-results.md`, `emulator-categorical-results.md` and `emulator-graphs3-results.md`, with what is left in `emulator-check6-run2-remaining.md`. Parts H and D, and J12 to J19, have no screenshots (Cowork read zooms of the screen). They confirm decision 1 and add:

- **Sharing (G).**
  - A page that is not on show is brought up to date when it is shown. The sheet, plots, regression labels and graphs follow every change to a list or function, whichever page made it.
  - A linked variable cannot change type: `xs:=5`, `xs:="hello"` and `xs:=[1,2;3,4]` give "Cannot accept change, variable in use", and `xs` stays the list. A list of mixed elements is accepted; the plots leave out the elements that are not numbers.
  - `DelVar xs` unlinks column A, which keeps its values as constants; plots lose the variable, and the Graphs scatter comes back when `xs` exists again.
  - A formula column (`sq`, `=xs^2`) is a variable the Calculator can read but not store to: "Cannot accept change: Invalid input."
  - Renaming column A from `xs` to `ws` leaves both variables, not linked to each other. Two sheets can link the same list. Variables belong to one Problem: a column named `xs` in Problem 2 starts empty. Copy and paste across Problems carries values only.
  - Indexed store (needed by slice 3a): `ys[9]:=18` on an eight-element list appends; `ys[12]:=5` gives "Dimension error".
  - Graph functions are Problem variables: `f1(2)` works on the Calculator, and redefining `f` or `f1` there redraws the graph. `DelVar f1` leaves its curve drawn with the label `y=…`; `DelVar f` hides `f1(x)=f(x)` until `f` is defined again.
  - A graph entry with an undefined variable (`a*x`) offers "Create Sliders"; OK makes the variable (1, slider from -5 to 5), Cancel keeps the entry undrawn.
  - Linear Regression from the sheet saves its equation to the next free `fN`, which is not drawn but is recalculated when the data change.
  - Dragging a point on a scatter plot writes unrounded values (4.498, 9.875) into both lists.
  - Float 3 changes new Calculator results only: earlier history lines keep their digits (CASSim already does), and the Data & Statistics labels and the Graphs axes keep theirs (Data & Statistics has its own Display Digits, Float 6).
  - Undo is document-wide: it goes to the page of the last change first, then undoes it.
  - A page keeps its state while another is shown: the sheet's cursor, scroll and block selection, a half-typed cell, a selected point and a shown regression.
- **Split pages (H).** Doc > Page Layout has eight layouts; decision 3 stands (two panes in M3). A tap gives a pane the focus and an empty pane offers the list of applications. Menu is the focused pane's own menu; Undo is not tied to the focused pane. Delete Application gives the pane's space to its neighbour. The residual plot is part of the Data & Statistics application, below its plot, not a second pane, and the Graphs table (Ctrl+T) is a split page.
- **Categorical charts (J).**
  - Categories are in alphabetical order by default. Sort offers List Order (first appearance), Value Order (largest first, ties alphabetical) and Alpha Order, and a category keeps its colour when it moves. Dragging a category label reorders by hand; the order goes back to alphabetical when the data change.
  - The pie runs clockwise from 3 o'clock, with the names outside the slices.
  - A summary plot (X List and Summary List) keeps the list's order, has no Dot Chart, and needs a numeric summary list.
  - Splitting by a second variable gives clustered bars, side by side, with a legend; Pie Chart is greyed while split.
  - There is no percent axis: percentages appear only in the tooltip (`5 cases (50.0%)`) and with Show All Labels (`5 (50.0%)`).
  - An empty string is not drawn. A void cell in the middle of a list stays as `_`; clearing the last cell shortens the list.
  - Selected cases are shared by every plot of the Problem and survive a change of plot type; a bar with some selected cases is drawn in two parts.
  - A numeric list can be forced categorical (Force Categorical X); a categorical x with a numeric y gives one dot plot or box plot per category.
- **Graphs (D, part).**
  - Auto tick marks are a power of ten, about a tenth or a twentieth of the window; only the first tick and the two end values are labelled.
  - Trace steps 0.3 in the standard window.
  - The table starts at 0 with step 1.
  - There is no line across a jump (`1/x`, `tan(x)`, `floor(x)`) and no open or closed end circles.
  - A restricted function (`x^2|x>0`) is labelled in brace form.
  - Relations: inequalities are shaded with a solid boundary, even for `<`.
  - In a Degree document, Graphing Angle Auto graphs in degrees.

The finish-off rows after run 2 (`emulator-finish-results.md`, no screenshots) completed part G and most of the E leftovers:

- **Undo.**
  - Sheet edits undo and redo one step at a time. Typing a cell is two steps: undo first reopens the cell with the typed text, then empties it.
  - A store made on the Calculator (`xs[1]:=55`) was not undone by ctrl+Z on the sheet. Undo moved to another page and changed nothing.
- **What a page keeps.**
  - Kept when the page is left and shown again: the sheet's cursor and scroll (a Go To scrolls as little as it can), a half-typed Calculator line with a picked history row, a trace point (it keeps its x and steps on from there), and a selected point with the regression line.
  - Not kept: a half-typed Graphs entry line comes back open but empty, and an Analyze Graph prompt is dropped partway, though its tool stays chosen.
  - While a menu is open the page cannot be changed.
- **Window.** A pan keeps the window's width and height. Window Settings shows 14 significant figures whatever the Float setting.
- **A formula column cannot be stored to,** even when it was made by Generate Sequence: `big:=big+1` and `big[1]:=7` give "Cannot accept change: Invalid input." A plain list of 500 elements (`seq(n^2,n,1,500)`) updated, and its sheet was shown, with no visible delay.
- **Sheet.**
  - A block's context menu has Cut, Copy, Paste, Fill, Delete Cells, Sort and Color.
  - Inserting a row moves cell references below it (`=c3` becomes `=c4`); linked columns get a void in the new row.
  - A formula naming something that is both a cell and a variable (`=d1+qq`) asks "Cell or Variable?" (dialog "Conflict Detected"). Choosing Variable writes `'d1`, so slice 3a's cell parser needs the `'name` form.
  - A formula column whose lists differ in length gives "Dimension mismatch" and `#ERR` in every cell.
  - The sheet follows Document Settings (Float 3 shows `0.333`, Fix 2 `0.33`), and exact `1/3` stays exact.
  - The handheld's sheet ends at row 2500 and column Z; Go To beyond either gives "Invalid reference". **CASSim does not copy these limits** (Simon, 2026-11-13). Its sheet may be larger, and its size is bounded only by memory and speed (spike B). Go To still gives "Invalid reference" for a cell that cannot exist.

## Decided in slice 3a (2026-11-14)

- A cell holding `=rand()` is not kept across a rebuild after Cancel: the replay recalculates, so it draws a new value, as Ctrl+R does on the handheld (check 6, E23). Keeping it would mean journalling values for one rare case.

## Not decided

- Timings on the Pixel 6 for all four spikes (deferred by Simon, 2026-11-13: wait for `tools/switchtime.py`).
- Where the autosave size limit sits for a document with large lists; share links already fall back to a file above about 2,000 characters.
