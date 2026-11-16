# CASSim

A free, installable simulator of the TI-Nspire CX CAS that runs entirely in your browser.

**Try it: <https://cassim-app.pages.dev/>** (installable as an app; works offline after setup).

| Site | Address | What it is |
|---|---|---|
| CASSim (stable) | <https://cassim-app.pages.dev/> | The released version. Use this one. |
| CASSim (testing) | <https://cassim-calc.pages.dev/> | The newest changes, updated on every merge. May break. |
| Help | <https://cassim-wiki.pages.dev/> | The user guide; the app's Help link opens it. |

Plans for other simulated devices are in [PLAN.md](PLAN.md).
Built for the VCE Mathematics courses, but should be more generally useful.
Usable on a desktop, laptop, netbook (Chromebook), tablet or a phone.

> **Status: in development.** The calculation engine is complete and the app shell is working.
> Graphs, lists and spreadsheet, statistics and notes pages are not built yet: Doc > Insert adds them as placeholders that say so. See [PLAN.md](PLAN.md).

CASSim is an independently made simulator for educational purposes. 
For this reason, the behaviour, layout, and menu structure of the simulator is designed to be similar to the TI-Nspire CX CAS, but it is not an exact copy.
It is not affiliated with, endorsed by or sponsored by Texas Instruments. 
It is not an approved exam calculator and must not be used in assessments that require an approved device. 
TI-Nspire is a trademark of Texas Instruments.

### Design and IP

CASSim mirrors the handheld's layout, menus and commands so that practice transfers to the real
calculator. All artwork and help text are CASSim's own. Its behaviour was learned only by using
TI's software as a user, typing inputs and recording the outputs; nothing was decompiled. It is not
an approved exam calculator. The rule is written up in
[docs/decisions/0028-ip-boundary-and-clean-room.md](docs/decisions/0028-ip-boundary-and-clean-room.md).

**Wolfram Language and Mathematica.** There are no plans to implement the Wolfram Language or
Mathematica in CASSim. If that is what you need, see **Woxi** (<https://github.com/ad-si/Woxi>,
docs at <https://woxi.ad-si.com/>), an open-source interpreter for a subset of the Wolfram
Language with a notebook editor, Woxi Studio. CASSim and Woxi are separate, unaffiliated
projects. Wolfram Language and Mathematica are trademarks of Wolfram Research.

## What it does

- **Calculator page** with an Nspire-like keypad, numbered menus, 2D templates (fractions, roots,
  piecewise, systems, calculus) and the document, problem and page model.
- **CAS engine** (SymPy and SciPy through Pyodide) that parses TI syntax with a real tokenizer
  and parser. Results are judged by symbolic and numeric equality, not TI's exact text.
- **Two views**: Handheld (a keypad you tap or type on) and Computer (a laptop layout).
- **Pseudocode runtime** with trace tables for the VCE algorithms and programming content
  (engine only; its pages are not in the app yet).
- **Private and offline.** No server, no telemetry, no account. Wait for “Ready for offline use”
  before disconnecting. Documents are saved in browser storage or as files
  or shared as a link that carries the document in the URL fragment.
- **Files.** Open and Save use CASSim's own `.cassim.json` format. TI's `.tns` files cannot be
  opened or saved; if that is ever added it will be under Import and Export, not Open and Save.

## Related software

The calculator makers sell their own computer and phone versions, and there are free CAS programs
too. The help page [Other calculators and CAS software](https://cassim-wiki.pages.dev/Other-calculators-and-CAS-software)
compares them for the TI-Nspire CX CAS, ClassPad II and HP Prime G2, and for the computer-based
exam options (Mathematica, Maple, MATLAB).

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
uv run python -m tools.publish        # build the installable offline site into build/web (--bundle all|tin)
```

The text interface is described in [docs/user/repl.md](docs/user/repl.md).

## Builds

CASSim is released as a **static web site** (`tools.publish`). It is the only supported build and the
only one tested: copy `build/web` to the root of any static host, or pass `--base-url SUBPATH` to
serve it below a sub-path. Users can install it as an app (PWA); once the offline-ready indicator
appears, it works offline. Clearing browser storage removes the offline installation.

The stable and testing sites are the all-in-one app. Smaller single-device sites (CASSim-TIN,
CASSim-pseudo, and later CASSim-CP) are planned: see [PLAN.md](PLAN.md) section 15.

## Publishing

The sites are Cloudflare Pages projects, deployed by `.github/workflows/deploy.yml` with
`wrangler pages deploy`. Nothing is deployed from a developer's machine in normal use.

| Project | Built from | Deployed when |
|---|---|---|
| `cassim-calc` (testing) | `python -m tools.publish --bundle all` | every merge to `main` |
| `cassim-wiki` (help) | `python -m tools.wiki_site`, from `docs/wiki/` | every merge to `main` |
| `cassim-app` (stable) | `python -m tools.publish --bundle all` | a published GitHub release |
| `cassim-tin` (the Nspire alone, stable) | `python -m tools.publish --bundle tin` | a published GitHub release |

**Testing and help.** Merge a pull request into `main` (CI's `check` job must pass). The Deploy
workflow then builds and publishes both. Edit the help pages in `docs/wiki/`; a `[[Page name]]` link
to a page that does not exist fails the build.

**A stable release.**

1. Check the testing site: <https://cassim-calc.pages.dev/> loads, evaluates, and reloads offline.
2. Set `version` in `pyproject.toml` in a pull request and merge it. The About dialog shows this
   version; the offline cache is renewed on every build whether or not the number changes.
3. Publish a release whose tag matches: `gh release create v0.2.0 --generate-notes`. The Deploy
   workflow builds that commit and publishes it to `cassim-app`.
4. Open <https://cassim-app.pages.dev/>. An installed copy shows an "update available" bar.

**By hand.** Actions > Deploy > Run workflow, target `testing` or `stable`, or
`gh workflow run deploy.yml -f target=stable`.

**Rolling back.** In the Cloudflare dashboard, open the project's Deployments and choose
"Rollback to this deployment" on an earlier one, or publish a new release from a fixed `main`.

**Set-up (done once).** The workflow needs two repository secrets: `CLOUDFLARE_API_TOKEN` (a token
with Account > Cloudflare Pages > Edit) and `CLOUDFLARE_ACCOUNT_ID`. A new Pages project is made
with `npx wrangler pages project create NAME --production-branch main`.

Each site is its own origin: an installed app, its autosaved document and its settings belong to
the site they were made on. Move a document between sites by saving it to a file or a share link.

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
- Layout: `core` (engine), `device` (framework), `doc` (documents), `devices/nspire` (the Nspire), `app` (Flet UI),
  `runtime` (pseudocode), `tools` (build and corpus scripts), `corpus` (golden cases).

## Documents

| | |
|---|---|
| [PLAN.md](PLAN.md) | Architecture, milestones, open work |
| [docs/SRS.md](docs/SRS.md) | Requirements with stable IDs and MoSCoW priorities |
| [docs/decisions/](docs/decisions/) | Decision records and spike results |
| [docs/testing/](docs/testing/) | Test method and emulator comparison results |
| [AGENTS.md](AGENTS.md) | Shared working brief for AI-assisted development |

## Licence

Released under the [Unlicense](LICENSE): public domain. Third-party notices for Flet, Pyodide,
SymPy, SciPy, NumPy and the bundled font are in the app's About dialog.

No TI logos, artwork or ROM content are included. 