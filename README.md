# CASSim

A free, installable simulator of the TI-Nspire CX CAS that runs entirely in your browser.
Plans for other simulated devices are in [PLAN.md](PLAN.md).
Built for the VCE Mathematics courses, but should be more generally useful.
Usable on a desktop, laptop, netbook (Chromebook), tablet or a phone.

> **Status: in development.** The calculation engine is complete and the app shell is working.
> Graphs, lists and spreadsheet, and statistics pages are not built yet. See [PLAN.md](PLAN.md).

CASSim is an independently made simulator for educational purposes. 
For this reason, the behaviour, layout, and menu structure of the simulator is designed to be similar to the TI-Nspire CX CAS, but it is not an exact copy.
It is not affiliated with, endorsed by or sponsored by Texas Instruments. 
It is not an approved exam calculator and must not be used in assessments that require an approved device. 
TI-Nspire is a trademark of Texas Instruments.

## What it does

- **Calculator page** with an Nspire-like keypad, numbered menus, 2D templates (fractions, roots,
  piecewise, systems, calculus) and the document, problem and page model.
- **CAS engine** (SymPy and SciPy through Pyodide) that parses TI syntax with a real tokenizer
  and parser. Results are judged by symbolic and numeric equality, not TI's exact text.
- **Two views**: Handheld (a keypad you tap or type on) and Computer (a laptop layout).
- **Pseudocode runtime** with trace tables for the VCE algorithms and programming content
  (engine only; its pages are not in the app yet).
- **Private and offline.** No server, no telemetry, no account. The site installs as a PWA and
  runs without a network. Documents are saved in the browser's local storage or as files 
  or shared as a link that carries the document in the URL fragment.

## How it is tested

A corpus of 186 and counting calculator cases was tested on the TI-Nspire CX CAS and reviewed, 
and every case replays against the engine in CASSim. See `python -m tools.replay` for
progress and [docs/testing/TESTING.md](docs/testing/TESTING.md) for the method.

## Try it

You need [uv](https://docs.astral.sh/uv/). Python 3.14 is installed by uv.

```
uv sync --group web
uv run cassim                         # the app in a window (for development)
uv run cassim --web                   # the app in your browser (for development)
uv run cassim --view handheld         # choose the view (handheld or computer)
uv run cassim --course methods        # the app with the Methods settings
uv run cassim --text                  # text interface, like the Calculator page
uv run cassim -c "solve(x^2=2,x)"     # one entry, then exit
uv run python -m tools.publish        # build the installable offline site into build/web
```

The text interface is described in [docs/user/repl.md](docs/user/repl.md).

## Builds

CASSim is released as a **static web site** (`tools.publish`). It is the only supported build and the
only one tested: copy `build/web` to any static host (GitHub Pages, for example) under the sub-path
`/CASSim/`, or pass `--base-url ''` to `tools.publish` for a site at the root. Users open it in a
browser and can install it as an app (PWA); it then works offline.

The window opened by `uv run cassim` is for development. Native desktop (Windows, macOS, Linux) and
mobile (Android, iOS) builds with `flet build` are possible later but not started; see
[PLAN.md](PLAN.md) section 13 and NFR-PORT-004 in [docs/SRS.md](docs/SRS.md).

## Development

```
uv run ruff format && uv run ruff check
uv run ty check
uv run pytest -m "not e2e"            # fast suite; add -m slow for the long simulations
python -m tools.replay                # corpus progress
```

- Core engine (`src/cassim/core`) is pure Python, never imports Flet and passes Ty strict.
  SymPy is touched only in `core/compat/sympy_adapter.py`.
- Every behaviour change ships with a test that cites the SRS requirement ID where one applies.
- Layout: `core` (engine), `device` and `profiles` (the Nspire as data), `app` (Flet UI),
  `runtime` (pseudocode), `tools` (build and corpus scripts), `corpus` (golden cases).

## Documents

| | |
|---|---|
| [PLAN.md](PLAN.md) | Architecture, milestones, open work |
| [docs/SRS.md](docs/SRS.md) | Requirements with stable IDs and MoSCoW priorities |
| [docs/decisions/](docs/decisions/) | Decision records and spike results |
| [docs/testing/](docs/testing/) | Test method and emulator comparison results |
| [CLAUDE.md](CLAUDE.md) | Working brief for AI-assisted development |

## Licence

Released under the [Unlicense](LICENSE): public domain. Third-party notices for Flet, Pyodide,
SymPy, SciPy, NumPy and the bundled font are in the app's About dialog.

No TI logos, artwork or ROM content are included. 