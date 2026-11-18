# SDD-07. Data pages: Lists & Spreadsheet, Data & Statistics, Finance

Status: foundations and slices 3a to 3e are built; M3 is mostly met (PRs #149, #152, and #154 merged). Hand-worked General Maths data-page flows and switch/recalculation timings are recorded in PR #161 and decision 0031. Spreadsheet navigation and heading-selection edge cases remain. Quick Graph and Summary Plot defaults and save/reload behavior remain unverified on the TI simulator and are listed for the next Cowork capture. Requirements: FR-DOC-008, FR-DOC-009, FR-SHEET-001 to 008, FR-STAT-001 to 005, FR-CALC-007, NFR-PERF-006, FR-DOC-003. Decisions: 0031 (plan, spikes A to D, switch timings), 0032 (devices and page types), 0026 (warnings), 0003 (IndexedDB).

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

## Implemented and remaining slices

- **3a, sheet engine (`sheet/`, headless).** Cells, columns linked to list variables, formula columns, `a[]`, ranges, `$` references, a dependency graph that recalculates in the engine before it replies, indexed assignment (`xs[2]:=20`), voids, `#UNDEF` and `#ERR`, Data Loss and Conflict Detected, sort, fill, insert and delete. Behaviour from `docs/testing/emulator-sheet3-results.md`. A store from the sheet skips result formatting (spike B). A `=rand()` cell draws a new value when a Cancel rebuilds the engine, as Ctrl+R does (decision 0031). **Built 2026-11-14:** `sheet/refs.py`, `sheet/sheet.py`, `sheet/actions.py`, and the engine side in `device/sheets.py` (the `sheet` op: cell, formula, name, fill, sort, insert, delete, generate, recalculate, view, restore, drop; replies carry each changed page's revision, dialogs, and the cells of a view).
  A linked list name prompts for Column or Variable only when it is a single letter A–Z; longer names are variables. Cell-address conflicts such as `d1` retain their separate Cell or Variable prompt. The simulator capture tested `u`, not longer list names.
- **3b, sheet page.** The grid scene, keys and touch routes (decision 0031 item 7), the per-page scene cache, the sheet in `tools/switchtime.py`. Part 1 built 2026-11-14: the page model (`devices/nspire/pages/spreadsheet.py`) keeps the sheet's definitions from each reply's `edits` and the formatted cells of its last `view`, and talks to the engine through `device/sheet_link.py` (`LocalLink` here, `RemoteLink` through the Runner's outbox and `RemoteSession.sheet_inbox`). A view taken before a change in the same batch is not sent. The journal keeps one `restore` per sheet, where its last op was; an entry made between two edits of a sheet replays against its later state. A sheet whose page is deleted is dropped from the engine, so its lists are free again, and an undone delete restores it. Part 2 built 2026-11-14: `devices/nspire/sheet_scene.py` makes the grid a scene of four layers and maps taps to cells; `devices/nspire/ui/sheet_view.py` draws it, keeping the canvas of every layer that did not change, so a cursor move sends only the cursor layer. A switch to a sheet page takes 66 ms on the laptop.
  The formula bar uses the Calculator's structured editor and clickable renderer. A formula's nodes are saved alongside matching cell definitions and retained when copied, with relative references shifted; values remain in the engine. Grid navigation and whole-row/column selection still need the edge cases in FR-SHEET-004 to 007.
- **3c, statistics from the sheet.** Stat Calculations write labels as text into the first result column and set a formula on the next (`OneVar c[],1`; a regression adds `: CopyVar stat.RegEqn,f1`). The sheet runs the command when the value column is evaluated and fills it from `stat.results`, so values, `stat.` variables and saved equations follow source data. Confidence intervals and significance tests use pure-Python/mpmath-backed commands and write live label/value columns. The 1-Prop z Test uses the captured `a[]` default and has a Draw: Shade P Value checkbox; the checked state stores the alternative as view state, while the statistic and PVal are read from the Problem's variables. Its second pane is a normal-curve scene with the selected tail(s) shaded. Exact defaults and result layout for other inference dialogs, and Shade behavior for tests other than the observed two-sided 1-Prop z Test, remain for simulator follow-up.
- **3d, Data & Statistics page implemented.** `stats/data.py` reads calculator-formatted list items; `stats/plots.py` builds backend-neutral scenes; `devices/nspire/pages/statistics.py` keeps only view options and derives plots from live Problem variables; the Flet view renders the scenes and menus. It supports numeric distribution plots, scatter/XY plots, categorical dot/bar/pie charts, summary and split categories, regression/residual overlays, Plot Function/Value, histogram settings, windows and Zoom–Data. Plot Value supports `mean(list)`; unsupported function/value syntax reports a validation message. Only view state is serialized. The page marks its plot area for right-click context handling. The full test suite and browser smoke test pass; this change has not been verified on the TI simulator.
- **3e, implemented:** Quick Graph adds a Statistics view for the selected named list. Summary Plot offers category and numeric-list choices and can show the plot beside the sheet or on a new Statistics page. CSV and basic XLSX import/export use the native sheet cells and formulas; XLSX reads the active worksheet. CSV exports displayed values, while XLSX can retain formulas. Importing over existing values asks for confirmation. The web app archive includes openpyxl and et-xmlfile. Statistics stay pure Python and mpmath (no SciPy or NumPy in the build). Focused tests cover formula calculation, overwrite confirmation, plot state, and the Flet split-pane rendering. These defaults and workflows are implementation guesses, not TI-simulator verified.
  - **Emulator check 6 part S (run 4, 2026-11-14; `docs/testing/emulator-sheet4-results.md`)** settles slice 3c's questions:
    - A Stat Calculation asks Num of Lists first (One-Variable only; with 2 lists the dialog drops Frequency and the category fields). Its defaults are X List from the current column, Save RegEqn to the next free `fN`, and 1st Result Column the next free column. Only a single-letter result column is accepted.
    - The results go in two columns. Labels are plain strings with no formula; values have one formula in their `=` row (`=OneVar('d1,1): CopyVar Stat., Stat…`). With two lists, one label column is shared by two value columns, each with its own formula.
    - A list name that is also a cell (`d1`) asks Conflict Detected (Cell or Variable) and writes `'d1` for Variable. An occupied result column then asks Data Loss. Typing in a value cell asks Data Loss and OK clears the whole value column and its formula; a label cell clears with no dialog.
    - The saved `fN` and the `stat.` variables follow the data (`xs[1]:=0` refits). Only the last run's `stat.` names exist.
    - A void cell is left out of the statistics (n = 4 for 1, 2, _, 4, 5). In column and cell formulas a void gives a void in that row only.
    - The category run from the sheet fails on the simulator with "Syntax error during insertion". The Calculator form `OneVar d1,1,cat,{"a"}` works and is now built in `_read` (n = 4, SSX = 26).
    - Distributions write their formula into the selected cell (`=binomCdf(10,0.5,0,5)`), not result columns. Stat Tests write a label column and a value column; Draw (Shade P Value) splits the page with a shaded normal plot.
    - Delete Cells and Delete Row shift up with no dialog, and Sort, Insert Row and Delete Row are each one undo step. A column letter's context menu has no Delete Column. Fill did nothing in four tries, so it is still to establish.

- **General split pages (FR-DOC-009).** Shade P Value and Quick Graph show a sheet beside one Statistics view; Summary Plot can split the page or open a new Statistics page. When a sheet has multiple plot views, they stack vertically in the right pane; the app still has at most two panes. The document schema migrates older sheet pages with no saved plot views. The exact TI Summary Plot/Quick Graph workflow, defaults, and save/reload behaviour remain for the next Cowork simulator investigation (emulator check 6 part H was not captured).

## Measured

| What | Result | Source |
|---|---|---|
| Switch to a Calculator page with 15 entries, laptop | about 125 ms, of which our Python is about 40 ms | decision 0031 |
| Cursor move in a 10 by 20 grid | 11 ms | spike A |
| `sq:=xs^2`, 2,500 decimals, Pyodide | 0.56 s | spike B |
| Curve frame at one point a pixel column | 6 to 7 ms | spike C |

None of these has been measured on a phone.
