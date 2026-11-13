# 0032: The device interface and the bundle format (M2x)

Status: accepted 2026-11-13 (item 7 agreed by Simon the same day). Requirements: FR-PROF-001, FR-PROF-002, FR-PROF-006, FR-PROF-008, FR-PROF-009, FR-DEV-007. It is the ADR that PLAN.md section 15.4 step 1 asks for, and it replaces the one planned for 8a.

## Context

PLAN.md section 15 decides that each calculator is a plug-in, that the all-in-one app holds every built device, and that each device can be published alone. This file fixes the interface and the order of the move, from what the code looks like today:

- `profiles/` already holds the Nspire's keymaps, keypad, menus, wizards and page names as data (the FR-DEV-007 guard), behind a `Profile` dataclass.
- `device/` mixes the framework (keys, menus, editor, wizard, screen) with one page model (`calculator.py`), the document model (`document.py`, `serialize.py`, `share.py`) and the engine protocol (`engine.py`, `runner.py`).
- `Document` and `serialize` know about Calculator pages by name: `Page.calculator`, and the page's JSON is written inside `to_dict`.
- `app/` is both the shell (window, autosave, files, share links, the PWA bridge, About) and the Nspire's views (history, entry line, keypad, sidebar, dialogs), with `App` in `main.py` joining them.
- `core/` is the Nspire's CAS engine as a whole. `runtime/pseudocode` imports nothing from it.
- `tools.publish` builds one site: `app.tar.gz` (Flet and `cassim` with the UI) and `cassim.zip` (`cassim` without `app/`, SymPy and mpmath).

## Decision

### 1. Packages

```
src/cassim/
  devices/__init__.py     the Device interface, the table of sites, load(id); no device code
  devices/nspire/         DEVICE; keymap.py, menus.py, syntax.py (from profiles/);
                          pages/ (page models, starting with calculator.py); screen.py and runner.py
                          (what a Calculator page shows, and its entries sent to the engine: both moved
                          here in step 3, since they are about Calculator pages); ui/ (its Flet views)
  bundle.py               NAME and DEVICES for this build; written by tools.publish
  doc/                    document.py, serialize.py, share.py: Document > Problem > Page, with
                          page types that are registered, not named
  device/                 the framework only: keys, menu, editor, wizard, clipboard, profile
                          (and engine.py until slice 3.0 reworks it)
  app/                    the shell only
```

`profiles/` goes away. The `Profile` dataclass stays as it is and moves to `device/profile.py`, since it is the framework's description of a keypad device.

### 2. The `Device` object

Each device package exposes one frozen `Device` as `DEVICE`:

| Field | What it is |
|---|---|
| `id`, `title` | `nspire`, "TI-Nspire CX CAS" style title for the switcher |
| `profile` | The `Profile`: keymaps, keypad layouts, menus, wizards, status line |
| `pages` | Its page types, in menu order (item 3) |
| `engine` | What its worker needs: the module that handles ops and the Pyodide packages to unpack. `None` for a device with no worker |
| `ui` | The dotted name of its UI module, imported only by the shell |
| `storage` | The prefix of its keys in browser storage |
| `help` | Its section of the help site |

A device package must import without Flet, because the engine worker, the CLI and the headless tests load it. So `ui` is a name, not an import, and only `devices/<id>/ui/` may import Flet.

`devices/__init__.py` also holds the table of every device id with its product name and site (PLAN.md 15.1). The shell needs it to name the right site for a document whose device is not in the bundle (FR-PROF-009), so it cannot live in the device packages.

### 3. Page types

A page type is registered by its device:

| Field | What it is |
|---|---|
| `kind` | The string stored in files (`calculator`, `graphs`, ...) |
| `title` | What the device calls it ("Lists & Spreadsheet") |
| `new(problem)` | Makes the page's model, or `None` for a type that is not built |
| `dump(model)`, `load(problem, data)` | Its part of the document file |

`Page` becomes `kind` and `model`. `Document` is given the device's page types and no longer imports any page model. `PageKind` stays as the list of kind names the Nspire registers; the stub pages are page types whose `new` gives `None`. This is follow-up A4, and M3's sheet and statistics pages are added as page types in `devices/nspire/pages/`.

### 4. Files and share links

A `.cassim.json` file and a share link gain `"device": "<id>"`. A file without it is an Nspire document. The schema number stays 1, because the key is additive and older builds ignore it. A bundle that does not hold the named device refuses the file, names the site that does, and changes nothing.

### 5. The shell and a device's UI

The shell imports `cassim.bundle` and `cassim.devices`, never a device package by name. For the active device it imports the module named by `ui` and calls `mount(shell)`, which returns an object with `start()` and `close()`. `shell` gives a device's UI the few things that belong to the browser and not to the calculator:

- the Flet page and the theme;
- storage: read and write a text by key, already prefixed for the device;
- files: save a text under a name, and pick a file to open;
- the page's address fragment, for share links;
- notices, and the About dialog;
- what the browser offers (install, full screen), as extra Doc menu items.

The Nspire's `App`, `AppState` and views move to `devices/nspire/ui/`. With one device in a bundle there is no switcher. The engine worker's browser plumbing (`app/web.py`) stays in the shell and is started from the device's `engine` field.

### 6. Rules, checked by `tests/test_architecture.py`

- `devices/<a>/` never imports `devices/<b>/`.
- `core`, `device`, `doc` and `runtime` never import `cassim.devices` or `cassim.bundle`.
- `app/` never imports `cassim.devices.<id>`.
- Only `devices/<id>/ui/` and `app/` import Flet.

### 7. `core/` is not split in M2x (agreed by Simon, 2026-11-13)

PLAN.md section 3.2 says the TI-specific parts of `core/` (grammar tables, catalogue, error table, display conventions) move under `devices/nspire/` in this refactor. I propose to leave `core/` where it is for now and do that split in M8a, when the ClassPad is started:

- Nearly all of `core/` is TI-specific in that sense: the lexer, parser, catalogue, errors, formatting and settings. Only the values, the SymPy adapter and the `compat` maths would stay. The move is close to renaming `core` to `devices/nspire/engine`.
- What is shared between two dialects can only be seen with a second dialect. Splitting a "parser framework" from "grammar tables" now would be a guess.
- The pseudocode bundle needs nothing from `core/`, so FR-PROF-008 is met by leaving `core/` out of that bundle.
- The reason given for doing M2x before M3 is that the new pages are built in their final place. Items 1, 3 and 5 do that.
- It touches every corpus and unit test's imports, and the branches of the other chats, for no change a user or a later page sees.

Until then the Nspire's `engine` field names `core/` as it stands, and the VCE presets stay in `core/settings.py`.

### 8. Bundles

`python -m tools.publish --bundle all|tin` (and `pseudo`, `cp`, `prime` as they are built). A bundle is a name, a product name, a site and a list of device ids. The build:

- writes `cassim/bundle.py` into the staged app with `NAME` and `DEVICES`; the copy in the repo lists every built device, so tests and `flet run` behave as the all-in-one app;
- copies only the listed devices' packages, and only the engine packages they name;
- uses the bundle's product name in the manifest, title and icons' labels;
- prints the download size of the bundle.

With one device there is nothing to load lazily, so the per-device archives of section 15.3 (`device-<id>.zip`, fetched on first use) are built with the second device in M7. In M2x `cassim.zip` keeps its name.

`deploy.yml`: a merge to `main` deploys `all` to `cassim-calc`; a release deploys `all` to `cassim-app` and `tin` to `cassim-tin`.

### 9. Storage keys

The Nspire keeps today's keys (`cassim.autosave`, `cassim.system`), so nobody's saved document is lost. Later devices use `cassim.<id>.`. Which of the System Settings are the shell's and which are a device's is decided when the second device arrives (M7).

## Order

Each step is its own PR and changes no behaviour. The gate for each: every corpus case replays unchanged, the unit, device, flow and e2e tests pass, and coverage does not fall.

1. This file.
2. `doc/` and registered page types (items 1, 3, 4).
3. `devices/`, `devices/nspire/` with the profile data and the Calculator page model, `bundle.py`, and the rules of item 6 (items 1, 2).
4. The shell and `devices/nspire/ui/` (item 5). This also does follow-up A2 of PLAN.md section 12 (A3, splitting the views file, is left as it was).
5. Bundle-aware `tools.publish`, the `tin` site and the size report (item 8).

## Not decided

- Whether `Document > Problem > Page` suits the ClassPad or it needs its own container (M8).
- The switcher's design (8b).
