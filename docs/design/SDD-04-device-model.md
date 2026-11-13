# SDD-04. Device model

Status: describes `src/cassim/device/` and `src/cassim/profiles/` at 2026-11-08 (M2a to M2h). Requirements: FR-DEV-001, FR-DEV-007 to FR-DEV-009, FR-CALC-001 to FR-CALC-006, FR-DOC-001 to FR-DOC-004, FR-DOC-007, FR-SCOPE-002. Decisions: 0013, 0015, 0017, 0019, 0022, 0023, 0025.

## Purpose and rule

The device model is everything a TI-Nspire does that is not drawing: which key does what, what a menu holds, what the entry line contains, what is on the screen, and how a document is built and saved. It is driven by key names and returns data, so it is tested headless (`tests/device/`, `tests/flows/`) and the GUI is a thin renderer over it.

The model has no Flet and no Nspire constants (the M2 guard, PLAN.md 3.2). The Nspire is a `Profile` of data (`profiles/nspire.py`, `nspire_menus.py`) handed to `AppState`. `tests/test_architecture.py` enforces the import rules.

## Layers

```
profiles/nspire*.py   keymaps, keypad, menu trees, wizards, status text   (data)
        |
device/keys.py        Binding, Keymap, Keyboard (modifier state)
device/menu.py        MenuItem tree, MenuState (walking it), MenuView (what to draw)
device/wizard.py      Field, Wizard (a dialog as data)
device/editor.py      Row/Node/Template tree, cursor path, linear() and latex()
device/calculator.py  Calculator page: Editor + history + Session + undo
doc/document.py    Document > Problem > Page, settings, page order
device/screen.py      render(): the Screen a GUI draws
device/engine.py, runner.py   see SDD-02
doc/serialize.py, share.py, clipboard.py
```

## Keys

A `Binding` is an action name and one optional argument. A profile supplies two keymaps: `handheld` (keypad key names like `ctrl+div`, `shift+esc`) and `computer` (browser key names like `ctrl+Enter`, `F2`). `Keyboard.press(key)` turns a key into a binding:

- The on-screen **ctrl** and **shift** are modifiers that apply to the next key only; pressing the same one again cancels it. A pair that is itself bound (ctrl then shift is caps lock) is looked up first.
- A computer keyboard sends `ctrl+Enter` as one name and never uses the modifier state.
- A printable character with no binding is typed (`insert`). Shift then a letter types a capital.

The action names are the interface between profile and page. `Calculator._actions()` maps each to a method (move, select, edit, enter, undo, templates, menus). An unknown action raises `ValueError`, so a typo in a keymap fails in tests, not in use. Typed action names are a recorded follow-up (PLAN.md A1).

## Menus

A `MenuItem` is a leaf (`action`, `arg`) or has `items`. Position gives the item's key (1 to 9, then A to Z) unless `key` overrides it, so a greyed placeholder (`enabled=False`) keeps the handheld's numbering. A label ending in `…` opens a dialog. Three shapes: a list; a **grid** (`columns`: trig, templates, symbols) with two-dimensional arrow movement and no keys; and a **jump list** (`jump`: Catalog, variables) where a typed letter jumps to the first item starting with it.

`MenuState` walks the tree from keys (`press`) or a click (`pick`) and yields a `MenuView` (panels of `Row`s, cascading to the right) for the GUI. Choosing a leaf returns its `Binding`, which the app performs like any key. `AppState` builds the Variables menu on demand from the current Problem.

The Menu (F2) and Doc (F4) trees, and the trig, templates, relations, punctuation, symbols and catalog menus, are data in `nspire_menus.py` (FR-DEV-008).

## Wizards

Many menu items with several arguments open a dialog on the handheld (distributions, regressions, Create Matrix, Finance Solver, Derivative at a Point). A `Wizard` is that dialog as data: labelled `Field`s (optionally a drop-down of choices) and a function from the typed values to `Binding`s that paste the command, or run it. The GUI draws the fields and calls it (FR-DEV-009).

## The 2D editor

`Editor` holds a `Row` (a list of nodes). A node is a one-character string or a `Template` whose slots are Rows (a fraction has two, an integral four; the `Kind` enum lists every template and its slots in Tab order, which is the device's, decision 0023). The cursor is a path of (node, slot) steps from the root plus a position in the final row.

- `linear()` writes the TI text the parser reads, so the engine is unchanged (decision 0015).
- `latex()` draws the tree with the cursor as a glyph for any LaTeX renderer.
- Selection covers a span within one row (Shift+arrows, Ctrl+A) or cells of a matrix. A template is a unit.
- `parse_target` / `format_target` turn a click region into a cursor path, so a click places the cursor (decision 0019).
- `Clipboard` keeps templates intact on copy and paste; text from outside is typed in.

`tests/device/test_editor_fuzz.py` applies random edits and clicks and requires the cursor to stay on a real row and the line to remain parseable.

## Calculator page

`Calculator` owns an `Editor`, a `history` of `Entry` (input row, result with text and LaTeX, approximate flag), a `Session`, and undo and redo stacks of `Snapshot`s grouped by kind of edit. Enter linearises the editor and calls `session.eval`. With a `RemoteSession` (`deferred`), Enter only sets `pending` and the app's `Runner` finishes the entry (SDD-02); while `pending` is set, keys are ignored. Up recalls a history row as a template (parsed back into the tree). An error shows as a dialog that the next key dismisses.

## Document

`Document` holds Problems; a `Problem` holds `Page`s and one `Session` (one variable scope), so a new Page keeps variables and a new Problem starts clean (FR-SCOPE-002). Document settings (`core.settings.Settings`) apply to every Problem. `PageKind` lists all page types, but only Calculator has a model; the rest are placeholders. A Problem holds at most 50 pages (`MAX_PAGES`, as on the device). The Page Sorter order and the add, delete, move and undo of page changes live here.

## Screen buffer

`render(document, status, menu)` returns a `Screen` of `Line`s (kind `entry` or `result`, LaTeX, plain text, selected flag), the title-bar status and an optional `MenuView`. It holds LaTeX and text only; fonts, sizes and layout belong to the GUI (SDD-05).

## Saving and sharing

`serialize.to_dict` writes versioned JSON. A Calculator page stores the **entries as typed** (the editor nodes, so templates survive), not results. `loads` replays them in order through the engine (`replay_steps`, a generator the `Runner` can drive when the engine is remote), so results are always recomputed and a file cannot hold a stale answer. `migrate` upgrades older versions. Random results differ after a load. `share.encode` compresses the JSON into a URL fragment, refuses more than 2,000 characters (`LinkTooLongError`; the caller offers a file), and `unpack` bounds the expanded size (`MAX_JSON`). Loading a file or link never runs anything beyond replaying the entries.

## Testing

`tests/device/` drives the model by key names. `tests/flows/test_exam_flows.py` plays `corpus/flows/exam.yaml` key by key through `AppState`, and the five flows marked `browser` are typed into the built site (`tests/e2e/test_flows_browser.py`). Behaviour is checked against the Teacher Software in `docs/testing/emulator-*-results.md`.

## Known gaps

- Page types other than Calculator have no model (M3 to M7).
- Typed-character capture on non-US layouts is open (decision 0024).
- Action names and worker messages are strings (PLAN.md A1).
- `app/state.py` imports `profiles.nspire` as its default profile (FR-DEV-007 review item).
