# SDD-05. User interface (Flet)

Status: describes `src/cassim/app/` and the pseudocode teaching workspace at 2026-11-19.
Requirements: FR-DEV-001, FR-DEV-002, FR-DEV-004, FR-DEV-006, FR-DEV-010,
FR-CALC-003 to FR-CALC-005, FR-RUN-008, FR-RUN-012, FR-XLT-001 to FR-XLT-006,
FR-TRC-001 to FR-TRC-008, FR-SET-001, FR-SYN-013, FR-THEME-001,
FR-PROF-010 to FR-PROF-018, NFR-PERF-007, NFR-PORT-002, NFR-PORT-003.
Decisions: 0004, 0013 (items 2 and 3), 0014, 0015, 0018, 0019, 0022 to 0025, 0032.

## Rule

`cassim.app` is a thin renderer. State and behaviour live in `AppState` and the device model (SDD-04); the Flet controls draw `Screen` data and send key names back. Anything that can be decided without Flet is a plain function with a test: `layout.py` (sizes), `keyboard.py` (key names), `entry_line.py` (click targets), `state.py`.

## Modules

| Module | Role |
|---|---|
| `state.py` | `AppState`: the `Document`, the `Mode`, a `Profile`, two `Keyboard`s (keypad and computer), the open menu, caps lock, `System` settings. Drives everything from `press_keypad` and `key_event`. No Flet import. |
| `keyboard.py` | Browser key events to key names. Flet reports the key, not the typed character, so shifted symbols come from a US/AU layout table. Wrong on other layouts until typed characters are captured (decision 0024). |
| `layout.py` | Pure sizing: `starting_mode` (a short side under 600 px starts Handheld), `handheld_plan` (fits the 320 x 240 screen and the keypad to the window, scaled together), the splitter range (0.15 to 0.8), zoom (0.5 to 2.0). |
| `theme.py` | `Theme`, Dark, Light and High contrast presets, colour validation and contrast calculation. Appearance overrides are saved per preset in System Settings. |
| `entry_line.py` | The entry line drawn from controls: every character, empty slot and template is its own control with invisible click halves, so a click maps to an editor target (decision 0019). `Hit` and `target_*` keep the mapping as data. |
| `ui.py` | `CalculatorView` (title bar, history, entry, menu overlay), `Keypad`, `Sidebar` (page sorter and variable list), and the dialogs: Document Settings, Handheld Setup, About, Page Sorter, wizards. `math()` draws LaTeX. |
| `main.py` | `Application`: chooses Home, or the device a direct route or share link names; imports and mounts a device UI only when selected. |
| `home.py` | The all-in-one Home screen, fixed choice order, unavailable state and shared appearance setting. It imports no device UI. |
| `shell.py` | Shared page services and storage for Home and a mounted device, including shell-wide preferences. |
| `web.py` | Browser-only: the engine worker and the page bridge (SDD-02). |
| `about.py` | The About text (disclaimer, privacy, licence, notices, versions) as data. |

## Views and modes

Two display modes, equal in priority (SRS):

- **Handheld:** the 320 x 240 screen and the keypad drawn at natural size and scaled to the window, the keypad under the screen in portrait and beside it in landscape. The keypad is drawn at 0.8 of the screen's scale by default, with a draggable splitter. On a phone the app forces Handheld.
- **Computer:** a sidebar (page sorter, variables), a large screen, the Doc and Menu chips, and an optional keypad beside the screen.

The first visit chooses by window size; afterwards `System.start_mode` wins. `--view` on the command line overrides it for a run.

## Rendering maths

Results and history are LaTeX drawn by `ft.Markdown` with a LaTeX style (decision 0014). The entry is not LaTeX, because the Flutter canvas gives Python no layout from which to map a click to a place in the tree; it is built from controls (above). `core.format.latex_for_markdown` adapts TI-style LaTeX to Flet's transport. One `Points` canvas shape per curve is the rule for graphs (decision 0004, M4).

The active Calculator page reuses unchanged history-pair controls between redraws. A change to
either line, selection, scale, maths size or theme rebuilds the affected pair; switching pages or
opening the sorter releases the cache. Pointer measurement also rebuilds the pairs, because Flet
reports sizes on change and pointer hit-testing needs fresh measurements. This caches history
rows only, not hidden page trees.

Arrows and shapes are drawn in a vendored Noto Sans Symbols 2 (`assets/fonts`, names in `ui.SYMBOLS`) because the browser's fallback fonts come from Google, which the offline build cannot reach. The publish step vendors the other fallback fonts (SDD-10).

## Input

One `KeyboardListener` with autofocus wraps the page. `track_shift` records Shift, because Flet clicks carry no modifiers (decision 0019). Key down goes to `AppState.key_event`; on-screen keys go to `press_keypad`; menu rows go to `MenuState.pick`. All three end in the same `Binding` performed on the current `Calculator`. A cancel key (Esc) while the Runner is busy goes to `Runner.cancel` (SDD-02).

Graphs function entries use the same `Editor`, Calculator editing actions and `EntryLine` renderer.
Each function retains its own structured draft; Enter or Plot compiles its linear expression, and
saved pages preserve templates and drafts separately from the last plotted expression.
The default graph scene draws axes with tick marks and end values instead of a full grid. Graphs
View can hide axes or end values and select a dot or lined grid; grid and axes are independent.
These settings are saved per Graphs page in CASSim; their scope on the simulator still needs
verification (`docs/testing/simulator-todo.md`, I1). Colours follow the selected CASSim theme.

## Refresh and persistence

`App.refresh` autosaves, redraws the view, keypad and sidebar, rebuilds the toolbar and calls `kick`, which starts a queued entry or a settings sync when the engine is idle. Autosave writes the document JSON to Flet `SharedPreferences` (browser localStorage, not IndexedDB) when it changed; System Settings are saved under their own key. `recover` reads both on start, then `--course` and `--set` (from `cassim`) replace the document's settings. A damaged autosave is ignored and overwritten.

## Pseudocode teaching workspace

The standalone pseudocode device uses `devices/pseudocode/ui/` rather than the Nspire screen
renderer. Wide layouts hold a Code/Console column beside Run controls, Symbols and
the Trace Table; layouts below 900 px stack those columns in that order. A draggable divider
resizes the two wide columns. Every content pane owns its visible title, collapse state and a
clamped vertical height. The bottom-right drag grip changes only the pane height; the CodeMirror
overlay, when available, is repositioned from the same pane state. The Flet editor and line-number
gutter are the fallback path.

Run records one `RunResult`, fills the trace headings and Symbols panel, then leaves the cursor
at zero. Step, Start and End only move the cursor through that result, so random values and input
are not regenerated. Constants show their recorded values and are excluded from the trace by
default. Constants, variables, functions and conditions are wrapped symbol rows with a vertical
scroller; their checkboxes change the trace view without a second execution. Console begins
folded, opens automatically for output or an error, scrolls vertically, and is moved to its end
after each update. Console expressions remove the source program's existing output before
appending the expression result.

The trace heading is a separate fixed row above a vertically scrolling body. A horizontal
scroller contains the table when its columns exceed the pane. Header grip controls resize each
column live; row cells follow the same width map. Number, angle and trace-cycle buttons share the
top toolbar with CASSim and Doc.

Line numbers and the optional typing aid live in Settings. The aid replaces only unambiguous
operator suffixes and terminated LaTeX-style spellings; plain names remain unchanged. The
Pseudocode/Python selector calls the runtime's program-tree converters before changing the source
or language. A `TranslationError` leaves both unchanged and is shown to the user.

## Dialogs and services

Dialogs are plain `ft.AlertDialog`s opened with `page.show_dialog`. The device model asks for one by name through `AppState.show_dialog` (`document_settings`, `system_settings`, `page_sorter`, `save_file`, `open_file`, `share_link`, `about`, `help`); `App.show_dialog` dispatches. Wizard dialogs are drawn from `Wizard` data. A dialog with text boxes sets `typing_dialog` so the page's key listener does not steal the keys. A shared-link open always asks before replacing the document. Help opens the project wiki through `ft.UrlLauncher`.

## Startup

The `all` bundle renders Home on every normal launch; it does not remember the last device. A
direct route (`#/app/pseudocode`) or a share link opens the bundled device it names. A `tin`, `pseudo`, `cp` or `prime` single-device bundle always mounts its one device.
Developer `#/debug` routes also open the first device so existing browser flows can drive it.

`cassim` with no arguments calls `app.main.run`, which starts Flet (a window, or the browser with `--web`). The static site runs the same `main` from a staged entry point (SDD-10). In the browser `make_runner` creates the worker engine and `make_bridge` the page bridge; elsewhere the engine is in-process.

Home is part of the shell worker only. `Application.open_device` calls `devices.load` and imports
the module named by `Device.ui`; only then does the Nspire (or another profile) create its engine
worker. The CASSim menu can call `Application.show_home`, which first saves the current document
and releases the device-owned page controls.
The fixed Home order is Nspire, Classpad, Prime, Pseudocode & Python and Scientific; enablement is derived
from `cassim.bundle.DEVICES`, so unbuilt choices stay visible without becoming profile imports.

## Known gaps

- Theme-file import/export and a separate Outline preset (FR-THEME-002) are not built; the three appearance presets can be edited in the app and persist in System Settings.
- Accessibility is unaudited (`docs/accessibility.md`).
- `app/main.py` (about 650 lines) and `devices/nspire/ui/views.py` (about 780) mix several concerns; the split is a recorded follow-up (PLAN.md A2, A3).
- Dragging the splitter rebuilds the screen and keys and feels slow (PLAN.md note, 2026-11-08).
- Tablet mode is not built. Graphs has an initial function-plotting view with pointer pan and anchored zoom; Lists & Spreadsheet and Data & Statistics have their own views. Notes remains a stub: `Screen.stub` carries the page type's name (from `Profile.pages`) and the view draws a notice in place of the history and entry line.
- Tested headless (`tests/app/`) and in Chromium (`tests/e2e/`). Safari, iOS and Chromebook are not (`docs/testing/browsers.md`).
