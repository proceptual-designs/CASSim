# CASSim — plan and architecture (draft for review)

A browser-based simulation of the TI-Nspire CX CAS: a static, installable (PWA) site where Python
(SymPy/SciPy, via Pyodide) runs client-side and the UI is built with Flet. Draft v0.4, 2026-11-08.

**Requirements live in `docs/SRS.md` (draft 0.5; every question is answered except Q17, Q18, Q19 and Q22, which concern ClassPad and HP Prime, and Q21, which is partly answered).** This plan is the architecture and milestone view; where the two disagree, the SRS wins for *what*, this file for *how and when*. CASSim is a **simulator, not a hardware emulation**, released under the **Unlicense**.

**Scope after the Nspire simulator (added 2026-11-02).** Once the Nspire work (M0–M6) is done, CASSim grows into a multi-device simulator: first a web-based Python and pseudocode environment that is both a standalone mode and a page type inside the simulators (M7, Should), then a device switcher with a Casio ClassPad profile (M8, Could), and possibly an HP Prime profile (M9, Would). See section 3.2 and milestones M7–M9. Nothing in M0–M6 is reordered or delayed; the only obligation on earlier work is the M2 guard (section 8).

## 1. What I checked while exploring (and what I didn't)

| Finding | Status |
|---|---|
| `flet publish` produces a static site with `manifest.json`, `flutter_service_worker.js`, icons and `python-worker.js`. Python 3.14 pins Pyodide 314.0.7. | Ran it (Flet 1.0.5) |
| Pyodide 314.0.7 ships numpy 2.4.6, scipy 1.18.0, sympy 1.14.0, mpmath, micropip. | Pyodide docs |
| Flet docs: static sites run Python in the browser; long CPU work can freeze the UI. `python-worker.js` hints Python may run in a worker. | Docs + build output; worker, cancel and restore verified (decision 0005) and built in M2e |
| SymPy 1.14 does the core VCE operations quickly (solve, factor, apart, diff, integrate, limit, dsolve, det: each under 0.11 s natively; import 0.22 s, scipy import 1.4 s). | Ran `spikes/sympy_timings.py` |
| A TI-syntax evaluator spike (`:=`, `→`, `f(x)`, `solve(...)|x>0`, `[1,2;3,4]`, implicit multiplication, `√`, `π`) works but only through regex hacks. A real parser is needed. | Ran `spikes/ti_eval_spike.py` |
| **Divergence found:** `solve(sin(x)=1/2,x)` returns only the principal values in SymPy; TI returns the general solution with `@n1`. Expect many such differences, so the golden corpus (section 6) is essential. | Ran |
| `.tns` files are a proprietary container (`*TIMLP0601`, `Document.xml`, `Problem1.xml` entries) with opaque payloads. The community format notes I found say no known way to read them. Any future decoding follows the clean-room rule (NFR-LEG-008): public documentation or black-box comparison of files Simon made, never decompiling TI software. | Inspected your `mm_*`/`gm_*` files; **not decoded** |
| Whether SymPy + SciPy actually load and run inside the Flet static build, and the cold-start time and download size. | Tested in M0 spike 1: go (decision 0002) |

## 2. Principles

1. **Engine first, UI second.** A pure-Python core (no Flet imports, enforced by a lint rule) that is usable from a CLI, tests and the browser.
2. **A headless "device model"** (keys, menus, cursor, screen buffer) sits between engine and Flet, so keyboard and page behaviour is tested without a GUI. Flet only renders it.
3. **Behaviour is defined by the simulator, not by SymPy.** Every behaviour we claim is pinned by a golden test captured from the real TI-Nspire CX CAS simulator. The target is "close enough not to confuse a student or teacher": same mathematical content in a familiar form, exact text only where a case says `compare: exact`.
4. **Typed, linted, reproducible:** uv, Ruff, Ty, Git, CI from day one. SymPy is weakly typed, so it is quarantined behind one typed adapter module.
5. **Original implementation.** Copy behaviour, structure and vocabulary; never copy expression or code (decision 0028). No TI ROM, TI artwork or logos. The handheld skin is our own design that keeps the familiar layout, drawn from scratch rather than traced. Behaviour is learned only by using TI's software and handheld (the corpus), never by decompiling, disassembling or inspecting their binaries (NFR-LEG-008), and help and explanatory text is CASSim's own (NFR-LEG-009). A visible disclaimer says CASSim is not affiliated with TI and is not an approved exam calculator.
6. **Private by construction.** No server, no telemetry or analytics, no student data leaves the device. Imported documents and share links never auto-run code.
7. **Nspire first, then the rest.** Other devices and the Python/pseudocode environment start only after the Nspire simulator (M0–M6) is done. Until then the only obligation is not to make that later work harder (the M2 guard in section 8).

## 3. Architecture

```
cassim/
  pyproject.toml            uv project; ruff + ty + pytest config; dependency groups: dev, test, web
  src/cassim/
    core/                   PURE PYTHON, no Flet
      lexer.py parser.py ast.py     TI grammar -> AST (Pratt parser), pretty-printer
      values.py                     typed Value union: Number, Expr, List, Matrix, Str, Bool, Eq, Void, Unit
      settings.py                   angle, calc mode (Auto/Exact/Approx), Real/Rect/Polar, float digits, base
      scope.py                      Document > Problem > Variables; library namespace (lib\fn); Local; Ans
      evaluator.py                  AST -> Value, mode-aware
      catalog/                      command registry by area: algebra, calculus, linalg, lists, stats, prob,
                                    finance, number, complex, string, trig/hyp, convert (►Polar etc.)
      compat/sympy_adapter.py       ONLY place that touches SymPy internals; TI-compat fixes (solve families
                                    @n1, cSolve, domain constraints, simplification/format differences)
      format.py                     Value -> TI linear text AND a 2D layout tree (fraction, sqrt, power, matrix)
      results.py builtin_names.py   what the UI holds without importing SymPy (decision 0027)
      errors.py                     TI error codes/messages
    basic/                  [placeholder] TI-Basic lexer/parser/interpreter (Prgm, Func, control flow, Disp/Request/Text, Try)
    pylib/                  [placeholder] Python-script bridge + sandbox API (see 5.4)
    libs/                   [placeholder] native Python ports of mm_/sm_/gm_ style libraries, registered as lib\fn
    sheet/                  Lists & Spreadsheet engine, headless (slice 3a): refs.py (cell, `$`, range and `a[]`
                            references in formulas), sheet.py (cells, named columns = lists, formula columns, deps graph)
    stats/                  [placeholder] Data & Statistics plot models; the statistics maths is in core/ (pure Python and
                            mpmath, no SciPy: decision 0031)
    graph/                  scene.py: the backend-neutral scene (FR-GRAPH-006, slice 3.0); to come: function/param/polar/sequence sampling, asymptote handling, analyse-graph tools;
                            emits a backend-neutral scene (paths, points, labels)
    doc/                    Document > Problem > Page, the versioned JSON serialiser (migrations, replay_steps) and share
                            links. Page types are registered by the device, not named here (decision 0032, M2x step 2)
    device/                 headless device framework: key layers (shift/ctrl/var/menu/doc), menu tree (data-driven), input
                            editor, wizard, clipboard, the Profile type; and, until slice 3.0, the engine protocol (engine.py)
    cli/                    `cassim` REPL (prompt_toolkit) + `cassim run file.tib`
  src/cassim/app/            FLET: the shell only (decision 0032): main.py picks the device from bundle.py and mounts its UI;
                            shell.py is what a device's UI may use (storage, files, clipboard, links, notices, About, install
                            and full screen, the engine worker); web.py, about.py, theme.py, keyboard.py, assets
  src/cassim/devices/        one plug-in package per calculator (decision 0032): the Device interface, the table of sites,
                            load(id). A device never imports another device, and imports without Flet
    nspire/                 DEVICE; keymap.py, menus.py, syntax.py (the profile data); pages/ (page types and the Calculator
                            model); screen.py, runner.py, document.py; ui/ (FLET: app.py joins state.py to views.py, entry.py,
                            layout.py; the only part of a device that imports Flet)
  src/cassim/bundle.py       the devices in this build; tools.publish writes its own copy (M2x step 5)
  src/cassim/runtime/        pseudocode lexer, parser, interpreter, trace, syntax file, printer (M7b, built)
  tests/  unit/  corpus/  device/  e2e/
  corpus/                   golden cases (YAML) + simulator screenshots as evidence
  tools/                    capture + replay tooling for the simulator corpus
  docs/  references/  spikes/
```

### 3.1 Key design decisions

- **Parser.** Pratt parser over a real tokenizer for: `:=`, `→`/`->` store, `|` constraint (lowest precedence), implicit multiplication (`2x(x-1)` vs `f(x)` call vs `ax` variable), `^` with TI's unary-minus rules, `√`, `π`, `ᵀ`/`@t`, `≤ ≥ ≠`, `and/or/not/xor`, lists `{}`, matrices `[1,2;3,4]`, strings, `lib\fn`, `@n1` arbitrary-constant names, `#` indirection, `'` primes, units `_m`. Round-trip tested (parse → print → parse) with Hypothesis.
- **Values.** Typed `Value` union; arithmetic wraps SymPy objects but exposes only our types. Exact/Approx is a property of evaluation (mode + a decimal point forces approximate), matching TI's rules.
- **Settings.** Document-level (angle, calc mode, real/complex, digits) plus system-level. Presets for the three VCE courses (General: Degree/Approximate/Real; Methods: Radian/Auto/Real; Specialist: Radian/Auto/Rectangular, from the cas-solver skill).
- **Scoping.** Document → Problems → Pages. All pages in a Problem share variables; a new Problem is a blank slate; `Define`/`→` writes the current Problem; library functions are document-wide and read-only; `Local` for programs.
- **Long-running work.** Evaluation must be cancellable (TI's On/Esc). Plan: CAS runs in a worker; cancel = terminate and restart worker with state restored from the document model. Verified in M0 spike 1.
- **Heavy dependencies.** SymPy loads at start. SciPy and NumPy are not shipped: the statistics and numerics are pure Python and mpmath, with SciPy used only by the tests as an independent check (decision 0031). Service worker caches everything for offline use.
- **Shared data.** Within a Problem every page is a view of the same variables, which live in the engine worker. The document stores definitions and view state; values are recomputed. Variables carry revision numbers so a page redraws only what changed, and each page's model and scene are kept so switching does not wait for the engine (decision 0031; FR-DOC-008, NFR-PERF-006).
- **2D maths display.** `format.py` returns a layout tree; the renderer draws it (Flet canvas). Input is a 2D template editor (decision 0015): the tree model in `device/editor.py` draws itself as LaTeX with a cursor glyph and writes the linear TI text for the parser, so the engine is unchanged.
- **Storage.** *As built (M3 slice 3.0): the autosave and System Settings are in IndexedDB in the browser (`TextStore` in `app/web.py`, reached through the shell), and the autosave waits half a second after the last change; an older localStorage copy is read until it is next written. The desktop app keeps Flet `SharedPreferences`.* Documents live in browser storage (IndexedDB via Pyodide `js` interop; localStorage is too small and Flet client_storage may be limited: spike 5). Upload/download of the native `.cassim.json` (versioned schema, schema-validated and size-limited on import). Open and Save read and write only `.cassim.json`. `.tns` is deferred (Won't for now) and nothing depends on it; if it is built it goes under File > Import… and Export…, never Open or Save (FR-DOC-006).
- **Sharing.** A document can be shared as a URL: compressed and encoded in the URL **fragment**, so nothing reaches a server. Opening a link asks for confirmation first. Keep links under about 2,000 characters; larger documents fall back to file export.
- **Themes.** Dark is the default. Themes (at least Dark, Light, Outline) are defined in a user-editable config file (keypad, screen and accent colours), persisted in browser storage and exportable; an invalid config falls back to Dark with a message.
- **Accessibility.** Should-have, applied where cheap. Keyboard-only use and visible focus in Computer mode are required. Flet renders to a canvas, so screen-reader support is hard: gaps are recorded in `docs/accessibility.md` and stubbed (labels and semantics hooks), not silently skipped.
- **Graphics.** Engine emits a scene; Flet `canvas` draws it. Charts libraries are not suited to implicit functions, asymptotes and trace; matplotlib is too heavy for Pyodide.
- **Spreadsheet.** Custom calc engine (TI cell/column semantics, columns are shared Problem variables so they can't map onto Excel-style engines like `formulas`/`pycel`). A library is used only for I/O: stdlib `csv` and `openpyxl` (pure Python; confirm it loads in Pyodide) for xlsx import/export.

### 3.2 Beyond the Nspire: device profiles and a shared runtime (M7–M9)

Nothing here is built before M7 (the runtime) or M8 (profiles and ClassPad), with one exception decided on 2026-11-13: the device interface, the move of the Nspire behind it and the bundle-aware build come before M3 (section 15). It is recorded now so that M0–M6 do not paint it into a corner.

**Device profile.** Everything that makes one calculator behave like itself is bundled as a profile; the engine pieces that are genuinely common stay shared.

| Layer | Shared | Per profile |
|---|---|---|
| Maths | SymPy adapter, Value types, exact/approximate machinery, stats and distribution maths, spreadsheet calc engine, graph sampler and scene format | Compat fixes (solution forms, simplification differences), number-display rules, error codes and messages |
| Language | Tokenizer and Pratt-parser framework | Dialect: grammar tables, symbols, command names and arity, catalogue |
| Document model | Storage, versioned-schema machinery, autosave | What a document is (Nspire: Document > Problem > Page; the others as their oracle shows) and its page/app types |
| Device model | Key-layer, menu and screen-buffer framework | Keymap, menu tree, skin, presets (e.g. the VCE settings) |
| Evidence | Corpus format and replay tool | `corpus/<device>/` cases captured from that device's oracle |

Layout: `src/cassim/devices/nspire/`, `.../classpad/`, `.../pseudocode/`, `.../prime/` (each a plug-in, section 15), with `core/` keeping the shared parts. Today's TI-specific parts of `core/` (grammar tables, catalogue, error table, display conventions) move under `devices/nspire/` in M8a, when the ClassPad shows what is shared (decision 0032 item 7, agreed 2026-11-13; M2x moved everything else); the Nspire corpus is the safety net, and the refactor is done when every Nspire case replays unchanged. The Nspire symbol and statistics conventions (SRS C-4, C-5) stay the Nspire profile's; other profiles take theirs from their own oracle.

**Runtime for Python and pseudocode** (`src/cassim/runtime/`). A small `Interpreter` interface: run source against an I/O context, stream output, accept input, report errors with line and column, cancel. Two implementations:
- *Python*: CPython from Pyodide in a **dedicated worker**, separate from the CAS engine. A runaway script is cancelled by terminating its worker (as in decision 0005) without touching CAS state. The goal is no network and no host-page access for user code; how that is enforced (CSP, removing the `js` bridge, or both) is a spike before the build, and any gap that cannot be closed is documented rather than hidden.
- *Pseudocode*: our own tokenizer, parser and tree-walking interpreter in pure Python, so the same code runs in the CLI, the tests and the browser. The dialect is the VCAA pseudocode as extended by the author's conventions document (`docs/pseudocode/dialect.md`): numeric types (integer, rational, real, complex) and basic strings only, function-valued parameters, and tolerant of the slips found in real exam text. Errors are reported in pseudocode terms and an execution-step limit stops runaway loops. A tree-walker is preferred over translating to Python because it gives clean errors, a step budget and a trace for free.

**Where it appears.** (1) A **Code view**: editor and console with no device skin, files in browser storage, import/export of `.py` and `.txt`. It is the `pseudocode` device: one entry in the all-in-one app's switcher and its own small site (section 15; Q23 revised 2026-11-13). (2) **Page types**, Python and Pseudocode, registered by any profile that wants them. The Nspire profile gets both: as I understand it the CX II models have a native Python page (the plain CX does not), and pseudocode is a deliberate extension that the UI labels as not a handheld feature. Whether ClassPad and Prime offer them is SRS Q22. Pages are self-contained in M7. A bridge to the Problem's variables and a `py()` call from the CAS is a Could-have for after M7 (the real Nspire does not allow it, so it would be a CASSim extension). Nothing auto-runs, ever (SRS C-7).

**One program tree, two languages.** Pseudocode (our parser) and the supported Python subset (the standard `ast` module) are both turned into one internal program tree. Printers turn the tree back into pseudocode or readable Python, which gives translation in both directions. Normal Python **Run** still uses CPython; the tree interpreter exists for pseudocode and for tracing. The risk is the two drifting apart, so every golden program is run both ways (differential test, reals compared numerically) and round trips are property-tested.

**Stepwise trace tables.** The interpreter emits an event per step (assignment, condition with values substituted, call, return, output, input). The events are kept, so stepping forwards **and backwards** moves a cursor instead of re-running, and random numbers and input replay identically. Two views of the same events: a **vertical** trace table (one row per executed line, a variable cell filled where it changes) that works for anything, and a **horizontal** desk check (code down the side, one column per loop pass) when the run has one main loop and no nesting. Auto picks; the user can switch. Layouts and the reference example: `docs/pseudocode/trace-tables.md`.

**Settings bar.** The Code view's editor has a bar at the top with two controls, Number mode (Approx / Auto / Exact, the TI rule being Auto) and Angle (Radian / Degree), and a "…" menu for everything else (display precision, default 6 significant digits Mathematica-style; Real/Complex; Gradian; random seed; step limit; syntax). They govern pseudocode runs, traces and translation (Auto and Exact emit `Fraction`, Degree wraps trigonometry in `radians()`); a direct CPython run cannot honour them, so they show as disabled with the reason. On a Nspire page the bar starts from the document settings.

**Configurable syntax.** The pseudocode grammar is driven by a **syntax file** (`docs/pseudocode/syntax-default.yaml`) kept in browser storage, editable in the app and exportable. It lets one construct be written several ways, each spelling accepted, warned about or rejected, with optional tokens (`then`, `do`, the colon, parentheses) and several block terminators (`end for`, `endfor`, `next`). The same file's emit section sets what the printer writes. The parser is therefore table-driven rather than hard-coded; the code pane always shows the user's own text. Because a free grammar can become ambiguous, files are validated, data-only, size-limited and fall back to the default if invalid; property tests restyle and re-parse every golden program under every preset.

**Switching.** A profile switcher in the shell of the all-in-one app (`cassim-app`, `cassim-calc`). Each profile has its own documents, settings and theme namespace in storage, and its assets load lazily on first use and are then cached offline, so someone who only uses the Nspire never downloads the rest. Display modes (section 4) apply to every profile. Each profile can also be published on its own, smaller site (section 15).

**Oracle per device.** The Nspire uses the TI teacher software. For ClassPad and Prime the natural oracles are the manufacturers' own PC emulators (as I understand it, ClassPad Manager and the HP Prime Virtual Calculator); I have not checked availability or licence terms. The capture effort that dominated M0/M1 will recur, so each new profile ships Tier 1 first. Python semantics need no oracle (it is CPython); device-specific Python modules (e.g. TI's `ti_system`, `ti_plotlib`) are a later extra if wanted.

## 4. GUI modes (one device model, three skins)

| Mode | Layout | Use |
|---|---|---|
| **Computer CAS** (equal top priority) | Wide window: page tabs/sidebar (problems → pages), large 2D calculator pane, scrollable history, templates palette, variable/catalog panel, physical keyboard first | Teacher/student at a desk |
| **Tablet / demo** | Screen on one side, on-screen keyboard on the other (portrait/landscape), big touch targets, optional "show keystrokes" for projection | Live demonstration |
| **Handheld** (equal top priority) | Faithful-layout 320×240 screen + keypad; scales to fullscreen on phones; hardware keyboard mapped | Practising the real handheld workflow |

The device model drives all three; modes differ only in layout components and which panels are visible. Primary test targets: Chromebooks, Chrome, Safari (macOS, iOS, iPadOS); secondary, smoke-tested: Edge, Firefox. Handheld mode must be usable at 360 px wide in both orientations. Hosting is any free or cheap static host with correct MIME types (Cloudflare Pages, section 14).

**Profiles and modes (M8).** Switching device is orthogonal to these modes: a profile supplies its own handheld skin, keymap and page set, while the Computer and Tablet layouts are shared components that the profile configures. The Code view has no skin. The ClassPad is stylus/touch-driven, so its Handheld mode may need a touch-first interaction model rather than a key-sequence one (SRS Q19).

## 5. Features by area

1. **Calculator page.** History, `Ans`, ctrl+enter approximation, templates, catalog, variable menu, copy/paste of results, errors.
2. **Pages:** Calculator, Graphs, Lists & Spreadsheet, Data & Statistics, Notes, Program Editor, Python (new), Pseudocode (new, M7). Geometry is out of scope.
3. **Documents.** Multiple documents, problems, page sorter, settings dialogs, undo/redo, autosave.
4. **Extending beyond the real calculator.** (a) TI-Basic programs/functions, including `Define LibPub` libraries. (b) A Python page, built in M7 with the pseudocode pages (not M5). It is self-contained in M7. A `py("script","fn",args)` call from the CAS and a `cassim` API for Problem variables are a Could-have for a later stage, since the real Nspire does not allow that bridge. Python in an uploaded document **never auto-runs**: explicit "Run" with a trust prompt, since documents and share links are untrusted. The sandbox and prompt are mandatory.
5. **Libraries (mm_/sm_/gm_).** The `.tns` libraries cannot be loaded directly. Plan: reimplement each UDF as native Python (fast, typed, testable), verified against the simulator with the libraries installed. LazyMath is also Unlicense, so porting and redistribution are permitted; still record that check in `docs/decisions/` before the first port.
6. **Beyond the Nspire (M7–M9).** Python and pseudocode as a standalone Code view and as page types (M7, Should); device switcher and Casio ClassPad profile (M8, Could); HP Prime profile (M9, Would, behind a go/no-go). Details in section 3.2.

## 6. Testing strategy ("every stage properly tested")

| Layer | What | Tooling |
|---|---|---|
| Unit | lexer, parser, printer round-trips, values, settings, each catalog function | pytest, Hypothesis |
| **Golden corpus** | Simulator-captured cases, replayed through the engine. This is the regression net | pytest parametrised from YAML |
| Device model | key sequence → expected screen text/state, menu navigation, mode switching | pytest, no GUI |
| Render snapshots | handheld/tablet/computer screens at fixed viewport; image diff with tolerance | Playwright + pixelmatch-style compare |
| E2E / PWA | built static site served locally: loads, types, evaluates, installs, works offline (service worker) | Playwright |
| Static | formatting, lint, strict types | Ruff, Ty |
| Coverage and traceability | At least 90% line and branch on `core/`, 80% on `device`, `doc`, `sheet`, `stats`, `graph`; `cassim.app` excluded (Playwright covers it). Every SRS requirement ID appears in a test or is listed as untested with a reason; `tools/` generates `docs/traceability.md`, checked in CI | pytest-cov, `tools/` |

**Corpus case format**

```yaml
- id: methods.solve.quadratic-001
  course: methods                # applies document-settings preset
  tags: [solve, tier1]
  steps:
    - in:  "f(x):=x^2-4"
      out: "Done"
    - in:  "solve(f(x)=0,x)"
      out: "x=-2 or x=2"
  provenance: {source: simulator, version: "<TI-Nspire CX CAS Teacher Software x.y>", captured: 2026-11-xx,
               evidence: shots/methods.solve.quadratic-001.png}
  status: pass                   # pass | xfail(reason) | hand-verified (not yet simulator-checked)
  compare: exact                 # exact text | canonical (symbolically equal) | numeric(tol)
```

- Capture is done with the simulator via the existing cas-solver workflow (new Problem per case, document settings first). Each case stores a screenshot as evidence and a human review flag.
- Seed it from the skill's known traps (`d(` unsupported, `1.` forcing approximate, `^` capturing exponents, `Ans` insertion, `solve|domain`, GM Approximate mode, `eff`/`nom`, `tvm*` argument order) plus VCE exam questions across Methods/Specialist/General, plus one or more cases per catalog entry.
- Failing-but-known cases are `xfail(strict=True)`: fixing one forces removing its marker, so progress ratchets and regressions fail CI.
- `compare: canonical` lets early milestones check maths correctness before output formatting matches TI exactly; tighten to `exact` per area over time.

## 7. Dev environment

- **uv** (Python 3.14 to match Pyodide 314), lockfile committed. **Ruff** for lint and format (rules: E, F, I, UP, B, SIM, ANN, PL, PT, RUF; `ANN` and strictness on `core/`). **Ty** for types, strict on the core packages; I have not verified Ty's current stability, so M0 checks it and keeps pyright as a fallback if SymPy/Flet stubs block us. **Git** with conventional commits, pre-commit (ruff, ty, fast tests), GitHub Actions CI (lint, types, tests, web build, Playwright smoke), deploy to Cloudflare Pages (section 14).
- Flet MCP / Claude Code: helpful from M2 for GUI iteration, so I'd switch to Claude Code before M2 (and for the repo work in M0/M1 too).

## 8. Milestones

Sizes are rough effort (S ≈ days, M ≈ 1–2 weeks, L ≈ several weeks). Each milestone ends with its tests green and a tagged release.

**M0 — Foundations and de-risking (M)**
- Repo, uv, Ruff, Ty, pytest, pre-commit, CI. Decision log in `docs/decisions/`.
- Spike 1: SymPy + SciPy inside the Flet static build (cold-start time, download size, offline, does Python run in a worker, can we cancel?). Spike 2: `.tns` decodability. Spike 3: Flet canvas drawing speed (graph of 2000 points, pan/zoom). Spike 4: IndexedDB from Pyodide. Spike 5: `openpyxl` in Pyodide.
- Corpus tooling (schema, replay, capture checklist) and the first ~60 simulator-captured cases.
- Extract a complete command coverage matrix from the Reference Guide (draft index of ~290 entries already in `docs/reference_index_draft.txt`; extractor misses some, e.g. `solve`, so it needs refining).
- Exit: spikes written up with go/no-go; CI green on an empty package; corpus replays.
- **Status: done (2026-11-02).** Spikes 1–5 are written up in `docs/decisions/` (go, except `.tns`, which is a no-go for now), CI is green, and the corpus replays (179 cases, all passing).

**M1 — Text-based CAS with TI syntax (L)**
- 1a Lexer, parser, AST, printer (+ Hypothesis round-trips).
- 1b Values, settings (angle/mode/real-complex/digits), `Ans`, exact vs approximate rules, TI-style formatting and error messages.
- 1c Documents/Problems/scope: `Define`, `:=`, `→`, `DelVar`, `ClearAZ`, `Local`, constraint `|`, libraries namespace.
- 1d Catalog, in tiers. Tier 1 (VCE core): solve/cSolve/zeros, factor/expand/propFrac/completeSquare, derivative/integral/limit/nInt/deSolve, trig and exponentials, lists and matrices (det, inverse, rref), norm/binom/inv distributions, `tvm*`/`eff`/`nom`, regressions and OneVar. Tier 2: remainder of the Reference Guide. Tier 3: edge conversions and unusual templates.
- 1e `cassim` REPL and script runner, tab-completion from the catalog.
- Exit: Tier 1 corpus passes (canonical at minimum), strict types on `core/`, coverage matrix published.
- **Status: done (2026-11-02).** See `docs/decisions/0007` to `0011`.

**M2 — GUI shell: keyboard, pages, settings (L)**

**Status (2026-11-12):** 2a to 2h, the 2d editor completion and the exam-style flows are merged. M2 is not closed, but nothing left can be done without a device or a decision.

Done since the 2026-11-08 list:
- The site was published on GitHub Pages and loaded (Simon); it moved to Cloudflare Pages on 2026-11-13 (section 14).
- Installed on Simon's phone; save and load work (Simon, 2026-11-12). It is slow there: see section 12, A6, for a later session.
- Stub pages (2026-11-12): Doc > Insert adds Graphs, Lists & Spreadsheet, Data & Statistics and Notes pages. They have no model; the screen shows the page type's name and a notice that it is not built yet. Names come from the profile (`Profile.pages`). The menu key does nothing on a stub page, and ctrl+Z takes the page away again.
- Disclaimer (NFR-LEG-002): the About CASSim dialog (Doc > 8 About CASSim, and an About chip in Computer mode) holds the disclaimer, privacy, licence, third-party notices (NFR-LEG-003) and versions; no footer line, by choice (2026-11-08). The repo link is private until the repo is public.
- The documentation gaps of section 11 (2026-11-09).
- Emulator shortcut follow-up (2026-11-12, `docs/testing/emulator-shortcuts-results.md` S7 e to g, S5 b2, S8 a): ctrl+Z with nothing to undo on a fresh page undoes the page insert and ctrl+Y redoes it; the keypad has ctrl+Z and ctrl+Y (shift+esc is not redo); keypad ctrl+7 picks the first history row and ctrl+1 returns to the entry line; a second Delete on a highlighted template leaves its first slot's content, selected.
- Handheld splitter drag (2026-11-12): drag steps are coalesced into one redraw, and a redraw rebuilds only the part whose scale changed, with no autosave, toolbar or sidebar work (`App.resize_soon`). Tested headless only; not yet timed in a browser.

Still open, each waiting on something:
1. Runs on Safari (macOS and iOS) and a Chromebook, which are primary targets (NFR-PORT-001). No devices are available; only Chromium has been driven by the tests (`docs/testing/browsers.md`).
2. Typed-character capture on non-US keyboard layouts (2d, decision 0024). Needs such a keyboard.
3. Tablet mode (FR-DEV-003, Should) has no code yet.
4. The 2f/2g items still to check on the simulator (0022, 0023; `docs/testing/emulator-templates-results.md`).
5. A one-off review of FR-DEV-007: `app/state.py` imports `profiles.nspire` directly as its default profile, which is acceptable only if everything else comes through the `Profile` object.
6. Emulator check 3 (`docs/testing/emulator-history-results.md`, a partial run on 2026-11-10): fixed 2026-11-12 except the history layout, which Simon chose to keep (a thin rule between pairs, not grey banding). Built to match the emulator: undo and redo cross evaluations and deletes (a store is not undone) and, once a page has nothing left to undo, the page insert; Del or Backspace on an empty entry line does nothing; Enter on an empty line runs the last entry again, with or without `Ans`; `ans` in a history line is shown as the value it had (14 digits, bracketed unless a plain number), while a saved file and the repeat keep `ans`; `Ans` follows the history after an undo or delete; Home with a history line picked goes to the first line; an error leaves its entry in the history with the message as a quoted string. Not run on the emulator: the mouse (H3), keypad ctrl and shift layers, most of H7 and H8, scrolling and spacing. Not copied: the long-input ▸ cut-off (CASSim wraps), the redo that re-shows an error dialog.

- Keys to carry over from the handheld: **Ctrl+Enter** gives the answer as a decimal, the same as wrapping the entry in `approx(...)`. The engine already has it as `Session.eval(line, approximate=True)`; the REPL uses `:approx` and Alt+Enter (see `docs/user/repl.md`).
- **Guard for the profile work in M8 (no extra scope):** framework code in `device/` and `cassim.app` holds no Nspire-specific constants. Key layers, menu trees, page types, skin and theme values come from data or registries that the Nspire profile supplies, and page types are registered, not hard-coded in a switch. This costs almost nothing now and avoids a rewrite later (section 3.2; SRS FR-DEV-007).
- Decisions and the four spikes that precede 2b to 2e are in `docs/decisions/0013-m2-planning.md` (2D rendering, MathLive, GitHub Pages publish, cancel and restore). The skin is driven by a config file; the display mode is remembered, with a media query on a first visit; Document Settings gain `case` and `ascii`.
- 2a Device model (started 2026-11-06: `device/keys.py`, `device/calculator.py` with entry, history, recall, undo and redo, and the Nspire keymaps in `profiles/nspire.py` are done; the `device/document.py` with Problems, Pages, the page sorter order and document settings is done; the menu tree and screen buffer are next): key layers, menu tree from data, the 2D template input editor (`device/editor.py`: fractions, powers, roots done; matrices, lists, copy and paste to do; shift-arrow and ctrl+A selection done), screen buffer; headless key-sequence tests.
- 2b Flet app (started 2026-11-06): `cassim.app` has the state, browser key mapping, and Handheld and Computer views with the on-screen keypad, running in-process (`flet run src/cassim/app/main.py`); the engine worker, Tablet mode and the first-visit width rule are still to do.
- 2c Documents, Problems, Pages (add/delete/reorder, page sorter), variable list, document/system settings dialogs, undo/redo. **Started 2026-11-07:** page add/delete/next/previous (keys and toolbar), clickable page list, variable list, Document Settings dialog are done; the Doc and Menu menus from data (`device/menu.py`, trees in `profiles/nspire.py`; F4 and F2 on a computer, doc and menu keys on the keypad) are done too; page reorder (sidebar buttons and Doc > Page) and document-level undo/redo of page changes are done; the Page Sorter dialog (tiles, click to go, move, delete, undo) and System Settings (start view, maths size; kept for the session only until storage in 2e) are done, so **2c is complete**; the Menu tree is a starter set (the full catalog and the Doc layout need checking on the simulator).
- 2d Editor completion: matrix and list templates, selection, copy and paste, history recall as templates (parse an old entry back into the tree), click-to-place the cursor (done, see below), typed-character capture on other keyboard layouts (needs a Dart key handler or a hidden text field; see 0015). **Known problems (Simon, 2026-11-06):** the selection box still leaves a gap at the cursor; selection does not handle fractions gracefully (a fraction is one unit, shift-arrows cannot select inside its slots or across a slot boundary, and the numerator and denominator rows do not highlight together). **Done 2026-11-07:** click-to-place (2026-11-07, decision 0019): the entry line is now drawn from Flet controls with a hit zone per character, slot and template, so a click places the cursor in plain rows, fraction slots, exponents, radicands and matrix cells, and shift+click extends the selection (`Editor.place`); selection gap fixed (cursor drawn inside the highlight); selection leaving a slot takes the whole template and carries on; history recall keeps templates (entries store their nodes); matrix grid template (Menu > Matrix & Vector, Tab by cell, Up/Down by row, `[a,b;c,d]` text); click a history row to pick it and click again to recall it. **Done 2026-11-08 (decision 0024):** a list template, selecting (and copying, cutting, deleting) matrix rows and columns, shift-extend by touch (long press, or the keypad shift key then a tap) and a stretching radical. **Caps Lock done 2026-11-08** (the key and the keypad's ctrl+shift, shown as CAPS; 0024). **Still to do (later, needs a non-US keyboard to check):** typed-character capture on other keyboard layouts, which would also fix a lock that starts on; see 0024 for what was tried and how to pick it up.
- 2e Storage and files: IndexedDB persistence, autosave, upload/download `.cassim.json`, PWA install and offline, fullscreen handheld on phones. **Started 2026-11-07:** done: `device/serialize.py` (versioned `.cassim.json`, entries replayed on load so results are recomputed, templates kept), autosave and recovery after reload (Flet `SharedPreferences`, which is browser localStorage, not IndexedDB; IndexedDB stays for named files in M7), Doc > File > New, Open file and Save to file. **To do:** Safari and Chromebook runs (the GitHub Pages site is published and loads). **Done 2026-11-07:** Handheld fills a phone (`app/layout.py`: the screen, text and keys are drawn at a scale that fits the window, keypad under the screen in portrait and beside it in landscape; a first visit starts in Handheld when the window's short side is under 600 px; a compact toolbar with a Tools dialog, an Install button (the page keeps the browser's install prompt and the app, which runs in a worker with no DOM, asks for it over a BroadcastChannel: `app/web.py` `Bridge`) and a Fullscreen button; the Google fallback fonts Flutter asks for are vendored, and an e2e test fails on any other font 404; the manifest asks for fullscreen); the installable offline site (`python -m tools.publish`: manifest, generated icons, versioned precaching service worker with an update bar, loading screen, vendored Pyodide packages, wheels and symbols font; `tests/e2e/test_pwa.py` boots it under `/CASSim/` and reloads it offline) and the engine worker: `device/engine.py` (`EngineCore`, `RemoteSession` with a journal and a variable snapshot, `LocalEngine`), `device/runner.py` (`Runner`: queued entries, sync of settings, Cancel and rebuild, async document load), `app/web.py` (a second Pyodide worker with a spare). Esc cancels a run in about 0.2 s and the engine is back in about 2 s with Problems and variables intact; `CASSIM_ENGINE=remote` runs the same path on the desktop. Also URL-fragment share links (`device/share.py`, Doc > File > Copy share link; the page uses the hash route strategy so the fragment arrives as `page.route`, and a link asks before it replaces the document) and System Settings kept in browser storage.
- 2f Keypad and menus like the Nspire (2026-11-07, decision 0022): the CX II key layout and ctrl/shift labels in CASSim's own drawing; the Calculator Menu with the handheld's numbering; trig, templates, catalog, variables, relations, punctuation and symbol menus; clickable cascading menus; syntax hints; data-driven dialogs for the multi-argument commands (distributions, stats, regressions, Finance Solver, Derivative at a Point, Create Matrix, systems, polynomial roots); an optional keypad beside the screen in Computer mode; an ABC or QWERTY letter block (System Settings). Checked against the Teacher Software on 2026-11-08 (Cowork run; greyed placeholders keep every device number).
- 2g More 2D templates (2026-11-08, decision 0023): nth root, log with base, absolute value, piecewise, systems, d/dx and d²/dx², definite and indefinite integrals, Σ, Π, limit; wired to the keys (ctrl+^, ctrl+10ˣ, shift+−, shift++), the templates grid, the Calculus menu and the dialogs; engine `root(` and `piecewise(`. Checked against the Teacher Software (Cowork run 2, 2026-11-08); also `linSolve(`, `invBinomN(`, the Differential Equation Solver dialog and a Non-real result error for even roots.
- 2h Sizing (PR 37, 2026-11-08): menus show up to 10 rows with no 'more' rows, Handheld draws the keypad at 0.8 of the screen scale with a draggable splitter, and a Zoom setting in System Settings; both saved with the system settings.
- Exit: build the static site, install on phone, complete the golden "exam-style" scripted flows via device-model tests and Playwright.
  - **Flows done 2026-11-08 (decision 0025):** `corpus/flows/exam.yaml` holds 12 exam-style flows (Methods, Specialist, General, handheld keypad), played key by key by `tools/flows.py` through `AppState` (`tests/flows/`) and, for the 5 marked `browser`, typed into the built site by Playwright (`tests/e2e/test_flows_browser.py`, all pass). Installed on Simon's phone, with save and load, on 2026-11-12.

**M2x — Device interface and bundles (M), before M3 (decided 2026-11-13). Done 2026-11-13 (PRs 83 to 87 and the bundles PR).** Section 15.4 steps 1 to 3: the ADR on the device interface and bundle format; the Nspire moved to `devices/nspire/` behind it (this is 8a, brought forward, and it carries decision 0031's A4 move of the document model); a bundle-aware `tools.publish` with the `tin` bundle and its site. No behaviour changes. Exit: every corpus case replays unchanged, the e2e suite passes, coverage floors hold, and download size is reported per bundle.

**M3 — Data pages: Lists & Spreadsheet, Data & Statistics, Finance (L)**

**Status (2026-11-13):** planned (decision 0031); no code yet. Emulator check 6 has done most of what M3 needs: run 1 did most of parts E and F, run 2 parts G, H and J (summarised in decision 0031). Run 3 does the E, F, G and H leftovers. The touch-first rule (decision 0031, section 7) applies to every page. Spikes A and B are done (results in decision 0031). The design rules (one owner for data, pages as views built from kept data, two-pane split pages, no SciPy) are in decision 0031 and are not repeated here.

- Spikes A and B (done 2026-11-13, decision 0031): a switch rebuilds controls from kept data (about 19 ms on a desktop; keeping controls alive is slower); the grid is one canvas text per column; replies must be deltas and sheet stores must not format the whole list. Not yet timed on a phone.
- 3.0 Foundations, shared with M4: SDD-07; section 12 rows A1 (typed ops) and A5 (A4, documents and the page-model boundary in `doc/`, was done in M2x step 2); variable revisions, the delta reply and the UI-side store (FR-DOC-008); the per-page scene cache and `tools/switchtime.py` (NFR-PERF-006); the shared scene type (FR-GRAPH-006); two-pane split pages (FR-DOC-009); the warning triangle (FR-CALC-007); debounced autosave in IndexedDB; schema bump with a migration. **Done 2026-11-13 (PRs 89 to 93 and the SDD-07 PR):** typed ops and replies, revisions, delta replies and the store; the scene type and its canvas; the IndexedDB autosave; `tools/switchtime.py` (about 125 ms a switch on the laptop, decision 0031); the warning triangle; SDD-07. **Left:** split pages and the schema bump wait for emulator check 6 part H; the per-page scene cache comes with the sheet page in 3b, the first page with a scene.
- 3a Sheet engine, headless (`sheet/`): cells, columns linked to list variables, formula columns, `a[]`, ranges, `$` references, the dependency graph and recalculation, indexed assignment (`xs[2]:=20`, done 2026-11-13: replaces, appends one past the end, else "Dimension error"), voids, `#UNDEF`, the Data Loss and Conflict Detected cases, sort, fill, insert and delete. Replays the `app_spreadsheet`, `app_sheet_sort` and `app_sheet_fill` corpus cases. **Progress 2026-11-13:** indexed store (PR 98), empty elements `_` in core (PR 99), and `sheet/refs.py` and `sheet/sheet.py`: cells, entries, formulas, references, linked and formula columns, `sync` with the Problem's variables, the dependency graph, `#UNDEF`, `#ERR`, the refused-edit dialogs and Conflict Detected (PR 100). Then (PRs 101, 102, 103 and 105; **3a done 2026-11-14**): Fill, Sort, Insert and Delete (`sheet/actions.py`), `seqgen` and Generate Sequence, the variable locks ("variable in use", formula columns read-only), and the engine's `sheet` op (`device/sheets.py`), through which the formula-column, seq-column, Generate Sequence, Sort and Fill corpus cases replay (`tests/device/test_engine_sheet.py`). **Left for 3b:** copy and paste with Data Loss (a UI clipboard), Move Column, the status-bar text of the Fill case, and journalling a sheet as its contents (`restore`) rather than as its edits.
- 3b Sheet page: canvas grid, edit bar, keys, selection, clipboard, Go To, resize, the Menu and context menus from checks 4 to 6. **Part 1 (headless) done 2026-11-14:** the page model `devices/nspire/pages/spreadsheet.py` (cursor, block, row and column selection, editing with a caret, Enter moving down, Fill, Move Column and Resize modes, copy, cut and paste with formulas moved and Data Loss for rows, Del, page undo falling through to the document's, Go To, the Menu and four context menus with check 6's numbering, var > Link To on a name cell, wizards for Sort, Generate Sequence and Conflict Detected); `device/sheet_link.py` (one channel per Problem, local or through the Runner; a deleted page drops its sheet); replies carry the definitions' edits, so the page saves without the engine; the journal keeps one `restore` per sheet; a loaded sheet rebuilds after its Problem's other pages. **Part 2:** the Flet grid (scene, canvas, touch), `tools/switchtime.py` and an end-to-end test.
- 3c Statistics from the sheet: the Stat Calculations dialogs writing live result columns; Distributions, Confidence Intervals and Stat Tests (the 22 commands of check 6 group 3, written on mpmath).
- 3d Data & Statistics page: dot plot, box plot, histogram, scatter and XY line; **dot chart, bar chart and pie chart with Force Categorical X and summary lists (FR-STAT-005, needed for General Maths)**; regression overlays, residuals, Plot Function, Plot Value, Show Normal PDF, window and zoom.
- 3e Quick Graph and Summary Plot (split page); CSV, then xlsx.
- Finance: the Finance Solver was built in 2f; pin `PmtAt` and `amortTbl` (`simulator-todo.md` D19).
- Greyed, not built: the movable line, Data Capture, Multiple Regression, ANOVA 2-Way, Custom Split and layouts of more than two panes.
- Exit: the General Maths workflows from the cas-solver skill reproduced as flows (`corpus/flows`), headless and in the browser; the page-switch and recalculation timings reported.

**M4 — Graphs and Tables (L)**

**Status (2026-11-13):** planned (decision 0031); no code yet. Waiting on M3 slice 3.0, the basic rows of emulator check 6 part D (run 2 did D12 to D30 in part, summarised in decision 0031), and part N for Notes. Spikes C and D are done (decision 0031): curves are sampled in the UI worker at one point a pixel column and redrawn inside each pan, pinch or wheel event (6 to 7 ms a frame on a desktop); fills use fewer points; relations use marching squares in pure Python (6 to 8 ms at 4 px cells).

- 4a Sampler and scene, headless (`graph/`): compile a function to `math` source for sampling in the UI worker, adaptive sampling, branch splitting at discontinuities (FR-GRAPH-004), restricted domains, the window, zoom and tick rules; scene snapshot tests (the scene as data, not pixels).
- 4b Graphs page: the `f1` to `f99` entry line on the template editor, pan and zoom with throttled gestures, labels, attributes, Hide/Show.
- 4c Trace and Analyze Graph: zero, minimum, maximum, intersection, inflection, dy/dx, integral with typed bounds, bounded area. Replays the `app_graph_analysis` corpus cases.
- 4d Other entry types, in this order: scatter plot, parametric, relations and conics (marching squares, spike D; drop false lines at jumps), polar, sequence, differential equations.
- 4e Table (split page, ctrl+T from the graph and from the sheet) and sliders.
- 4f Notes page, text only (FR-NOTE-001); maths boxes are a later Could.
- Greyed, not built: Plane Geometry, 3D Graphing and the Geometry menu.
- Exit: scene snapshot tests green; pan and zoom timed on a mid-range phone and a Chromebook and reported (FR-GRAPH-007).

**M5 — Programming and extensions (L)**
- TI-Basic interpreter + Program Editor; library mechanism; native ports of mm_/sm_/gm_ libraries (licence check first), each verified on the simulator.
- The Python page is not part of M5: it is built once, in M7, on the shared `Interpreter` interface.

**M6 — Polish and extras (M)**
- Accessibility follow-through (`docs/accessibility.md`); localisation-ready strings; exam-restriction mode (Could-have, teacher-configurable); theme config export/import; user docs; public deployment. `.tns` is dropped from scope for now.

**M7 — Python and pseudocode: Code view, translation and trace tables (L), Should.** Starts only when M0–M6 are done. The Code view ships as the `pseudocode` device (section 15).
- 7a `runtime/`: `Interpreter` interface; Python runtime in its own worker with cancel (within 1 s), streamed output, `input()` and the trust prompt. Spike first on keeping user code off the network and the host page.
- 7b Pseudocode language: syntax-file-driven tokenizer, parser and tree interpreter for the dialect (`docs/pseudocode/dialect.md`, `syntax-default.yaml`); numeric tower (integer, rational, real, complex) and strings; Approx / Auto / Exact number modes and Radian / Degree; 6-digit display; `input` type inference; lists (1-based by default) and seeded random numbers (Should); function-valued parameters; pseudocode-level diagnostics; step limit. Replay `corpus/pseudocode/seed.yaml` (58 cases) from the start. *7b was built ahead of the rest of the plan (it needs no GUI); 7c to 7f still wait for M2 to M6. The batch 3 replay fixes (mod/div operand binding, TRUE/FALSE and list printing) were merged in PR 44; the `m7-batch3` branch is gone.* **Built 2026-11-07 (PR #25; decisions 0020, 0021):** tokenizer, parser, interpreter, vertical and horizontal trace tables, the table-driven syntax file with presets and validation (FR-SYN-001 to 004, 008, 009), and the printer (FR-SYN-005, 007); 58 golden programs replay green. Remaining: 7c to 7f.
- 7c Translation: the shared program tree; pseudocode to Python and Python (subset) to pseudocode; differential and round-trip tests.
- 7d Trace engine and tables: event recording, forwards/backwards cursor, vertical and horizontal views, Auto layout, step-limit handling. The reference bisection example must reproduce the author's two tables.
- 7e Shared editor and console, the settings bar with its … menu, the Syntax editor (validation, live check, reset, export/import), the Regularise button (FR-SYN-010), symbol equivalents with the Convert symbols button (FR-SYN-011, FR-SYN-012) and the symbol palette (FR-EDT-006), unlimited undo/redo (FR-EDT-001), named files in browser storage with download and upload (FR-EDT-002 to 004), and the standalone Code view as the `pseudocode` device, in the switcher and on its own site (360 px layout; SRS Q23, Q35).
- 7f Page types: Python and Pseudocode pages in the Nspire profile (the bar starts from the document settings; pages are self-contained, and the variable bridge is deferred past M7), document schema bump with a migration (FR-DOC-004).
- Exit: every golden program passes in both languages and the two agree; trace tables match the reference tables; cancel and trust-prompt E2E pass; the installed PWA works offline.

**M8 — Device profiles and Casio ClassPad (L), Could.**
- 8a (brought forward to M2x, before M3; section 15.4) ADR on the profile boundary, then move the Nspire onto the profile interface. Gate: every Nspire corpus case replays unchanged, coverage targets (NFR-MAINT-004) still met, render snapshots unchanged. No other 8x item starts until this is green.
- 8b Profile switcher in the shell of the all-in-one app (section 15), per-profile storage namespaces (SRS Q20), lazy asset loading and offline caching per profile.
- 8c Decide the model and oracle (SRS Q17), record the emulator's licence terms in `docs/decisions/`, and capture the first ~60 corpus cases in `corpus/classpad/` before writing code, as M0 did for the Nspire. Nothing is assumed to behave like the Nspire.
- 8d Dialect, settings presets and display conventions from the corpus; Tier 1 catalogue (VCE core) first, tiers as in M1d.
- 8e Apps/pages as the oracle shows them (calculation, graph and table, statistics, spreadsheet), reusing the M3/M4 engines through the profile. Geometry excluded.
- 8f Device model, keymap and skin in our own artwork; decide touch-first vs key-driven interaction (SRS Q19).
- 8g Python and Pseudocode pages if SRS Q22 says yes (the M7 runtime is reused).
- Exit: Nspire corpus unchanged; Tier 1 ClassPad corpus passes (canonical); scripted exam-style flows for Methods and Specialist; profile switching E2E.

**M9 — HP Prime profile (M–L), Would.** Not planned; kept so the option stays visible.
- 9a Go/no-go review after M8: oracle availability and terms (SRS Q18), M8's actual effort, whether anyone needs it. A "no" costs nothing elsewhere in the plan.
- 9b If go: the same recipe as M8 (corpus first, Tier 1 catalogue, then the apps the oracle shows; as I understand it, Home and CAS views plus an app set). The HP PPL programming language, if wanted, is a separate dialect on the runtime interface.
- Exit: as M8.

## 9. Risks and decisions

Decisions (from the SRS review, 2026-11-02; do not re-litigate):

1. **Fidelity:** canonical equality first, exact text per area as the corpus grows; "close enough not to confuse" is the bar.
2. **Performance and size:** no hard budgets. Cold start (baseline 15 s vendored, 35 s CDN) and download (22 MB CDN, 95 MB vendored) are measured and reported with a progress screen. Tier 1 operations aim for 1 s or less after import; SciPy first use 5 s or less and shown as busy; Cancel within 1 s.
3. **Licensing:** CASSim and LazyMath are both Unlicense. TI marks, artwork and ROM are never shipped; reference screenshots stay in `docs/design/reference/`, not the build. IP boundary and clean-room rule per decision 0028: layout, menus, names and syntax may match the device; artwork, prose and code may not, and behaviour is learned by observation only.
4. **Appropriate use:** teaching, practice and demonstration. Not an approved exam calculator, and the UI says so.
5. **Python 3.14, no Geometry page, no `.tns` for now.** If `.tns` is ever built, it is File > Import/Export only (FR-DOC-006).
6. **Sequencing and priorities (confirmed 2026-11-02):** the Nspire simulator (M0–M6) is finished first. Then Code (Python and pseudocode, standalone and as page types) is Should (M7); the device-profile refactor and the Casio ClassPad are Could (M8); HP Prime is Would, behind a go/no-go review (M9). The M2 guard and the M7 sandbox spike are accepted.
7. **Pseudocode choices (2026-11-02):** the TI "Auto" rule is a third number mode; printed reals default to 6 significant digits (Mathematica style); `input` infers number versus string; the settings bar is Number mode and Angle plus a "…" menu; the syntax is user-configurable through a stored syntax file; VCAA cases stay in the repo with attribution (decision 0012, revised 2026-11-12).

Open risks:

1. **Flet static limits** (threading, cancellation, canvas speed): M0 spikes were go and the engine worker, cancel and offline site are built; fallback is a thin custom web front-end over the same engine. The 2D editor is CASSim's own template editor (decisions 0015, 0018), so MathLive and MathQuill are dropped, and Dart code in the static build is verified.
2. **Simulator capture effort:** driving the simulator by screenshot is slow; budget it per milestone and prioritise Tier 1 cases.
3. **Offline end to end:** wheels must be vendored and `index.html` patched after `flet publish` (decision 0002); verify with Playwright.
4. **Accessibility on a canvas renderer:** screen-reader support may not be achievable in Flet; tracked in `docs/accessibility.md`.
5. **Oracle access for ClassPad and Prime.** Unverified: that the manufacturers' emulator software is available to you and permits corpus capture. Screenshot-driven capture was the bottleneck for the Nspire and will be again; hence Tier 1 first and the Prime go/no-go.
6. **Maintenance load multiplies.** Each profile is its own corpus, catalogue and skin. Mitigation: shared engines, a strict profile boundary, Tier 1 per profile before widening.
7. **Refactor regression.** Moving the Nspire onto profiles could change its behaviour. Mitigation: the corpus gate in 8a.
8. **Sandbox for user code.** Pyodide is CPython with a `js` bridge, so "no network, no host access" needs a spike (7a) before it is claimed. Until it passes, the trust prompt is the control and the limit is stated.
9. **Touch-first ClassPad.** The device model is key-sequence based; a stylus-driven device may need a different interaction layer (SRS Q19).
10. **Trademarks.** Casio and HP marks, artwork and firmware are treated exactly as TI's (SRS NFR-LEG-005).
11. **Two interpreters must agree.** Tracing and pseudocode use our tree interpreter while Python runs on CPython. Mitigation: differential tests on every golden program and on generated programs, numeric comparison for reals, and the number and angle semantics defined once, in the dialect spec.
12. **VCAA material.** Several pseudocode corpus cases come from VCAA exams (`third_party: true`, attributed in `source`). They hold the algorithm listings and CASSim's own answers, not VCAA's question prose, and stay in the public repository (decision 0012, update 2026-11-12; SRS NFR-LEG-007). Remove any case VCAA objects to.
13. **Configurable grammar.** A user-editable syntax file can make the grammar ambiguous or break saved programs. Mitigation: validation (FR-SYN-004), data-only files, fall-back to the default, and property tests that restyle and re-parse every golden program under every preset (FR-SYN-007).
14. **Documentation and traceability debt.** Largely paid on 2026-11-09 (section 11). Traceability is generated and checked in CI; 108 of 195 requirements are not cited by any test, each with a reason in `docs/traceability-reasons.yaml`, and the list shrinks as tests cite IDs. The SDDs for the built areas (02, 04, 05, 10) exist; the others wait for their areas.
15. **Browser coverage.** All e2e runs use Chromium; Simon has loaded the GitHub Pages site and installed it on his phone; the Cloudflare site passed a headless smoke test with an offline reload. Safari and Chromebook are primary targets and are untested because no devices are available; Flutter canvas, service worker and fullscreen behave differently there. Run them as soon as a device can be borrowed, not at M6.
16. **Branch and worktree hygiene.** Several chats work in parallel. A leftover folder (`worktrees/m2f-menus`) outlived its merged branch and looked like a live worktree. Use `git worktree list` and remove finished ones. (Checked 2026-11-12: no stale worktrees or branches; `m7-batch3` was merged as PR 44.)

## 10. Design documents

The SDD set (`docs/design/SDD-00` to `SDD-13`: overview, engine, worker and cancel, display and format, device model, Flet UI, document and storage, data pages, graphing, programming and Python, PWA and build, test strategy, device profiles, Python and pseudocode runtime) is listed in SRS appendix A. **SDD-02, 04, 05 and 10 were written on 2026-11-09, and SDD-07 (data pages) on 2026-11-13; the rest are not.** The material is in `docs/decisions/` (0002, 0005, 0013 to 0022) and in the code. Proposal: write SDD-02 (worker and cancel), SDD-04 (device model), SDD-05 (Flet UI) and SDD-10 (PWA and build) now, assembling them from those decisions, because those areas are built; write the others when their milestone starts. Mark each SDD with the requirement IDs it covers. Requirement IDs (`FR-*`, `NFR-*`) are the stable references between SRS, SDD, tests and corpus tags.

## 11. Documentation and planning follow-ups (proposed 2026-11-08)

These came out of a review of PLAN.md, the SRS, CLAUDE.md and `docs/` against the repository. Recommendations, in the order to do them.

1. **DONE 2026-11-09.** **Traceability generator (NFR-MAINT-006, Must).** Add `tools/traceability.py`: parse requirement IDs from `docs/SRS.md`, find them in `tests/` (docstrings and markers) and corpus tags, write `docs/traceability.md` with an "untested, reason" list, and check it in CI. Run it first: the gap list is the best view of what the tests do not yet claim.
2. **DONE 2026-11-09.** **Enforce coverage (NFR-MAINT-004).** CI runs `--cov=cassim` but has no threshold. Add `fail_under` per package once the first report shows where things stand; set it just below today's figures so it ratchets.
3. **DONE 2026-11-09.** **`docs/accessibility.md` (NFR-USE-002).** Start with what is known: keyboard operation in Computer mode, focus, the canvas-renderer limit, and the Semantics hooks. Short is fine; the file's job is to record gaps.
4. **DONE 2026-11-09.** **SDD-02, 04, 05, 10** from the decisions (section 10).
5. **DONE 2026-11-09.** **Browser matrix.** A short `docs/testing/browsers.md`: what has been run on which browser and device, with dates, so NFR-PORT-001 has evidence. Do the Safari, iOS and Chromebook runs before the M2 exit.
6. **Keep CLAUDE.md short.** Its "Current state" had grown into one 400-word paragraph that went stale within a day. It now lists the state in a few lines and points here; milestone detail belongs in this file only.
7. **DONE 2026-11-09.** **Number the open "to check on the simulator" items in one place.** They are scattered across decisions 0007 to 0010, 0022 and the emulator results files. Collect them in `docs/testing/simulator-todo.md` so the next capture session has a single list.
8. **Sequencing.** After M2 closes, take M3 (data pages) then M4 (graphs); both are Must for VCE use (planned in decision 0031, 2026-11-13). M5 is mostly Could (TI-Basic, library ports); consider doing only the `mm_`/`sm_`/`gm_` ports Simon actually uses and leaving the TI-Basic interpreter until after M7c to M7f, since the program tree built for pseudocode may be reusable.
9. **Public release gate.** The third-party notices (NFR-LEG-003) have no owner or milestone. Add them to the M6 exit. (NFR-LEG-007, the VCAA cases, was settled on 2026-11-12: they stay, attributed; decision 0012.)
10. **Release gate: original text (NFR-LEG-009, NFR-LEG-006).** Before public release, audit the in-app help, catalog and error strings against both Reference Guides for verbatim copying (decision 0028 records the method and a first clean run on 2026-11-12; repeat it once help and catalog text exist). Add it to the M6 exit with item 9. TI screenshots may stay in the repository but never go in the build (decision 0029).
11. **TODO, early 2027: VCAA approved technology.** The VCAA site was down when the help page "Other calculators and CAS software" (`docs/wiki/`) was written (2026-11-13), so its exam section is from search results. Check the 2027 approved calculator and software lists and the new restrictions (user-defined functions restricted from 2027), then update that page, the wiki's exam wording and any SRS text that names approved devices.

**Warning triangle (FR-CALC-007): built in slice 3.0, 2026-11-13.** `Result.warnings` is raised in `Evaluator._finish` (Real mode, a non-real step with a real answer), carried by the worker reply and drawn left of the entry by the shared `cassim.app.warning.warning_mark`. Still to capture on the simulator: where else the device shows it (Graphs, Lists & Spreadsheet, Data & Statistics); those pages use the same mark.

## 12. Architecture follow-ups (from a structural review, 2026-11-08)

Done in branch `arch-cleanup`: the replay interface is public (`serialize.replay_steps`, used by `from_dict` and `Runner.load`), the architecture map above matches the code, and `tests/test_architecture.py` enforces the import rules and checks that this map lists every package. The rest is deliberately deferred and **tied to a trigger**: do it when the trigger happens, not before.

| # | Change | Trigger | Notes |
|---|--------|---------|-------|
| A1 | Typed action names (`keys.py` string pairs). (Typed worker messages were done in slice 3.0: `TypedDict`s checked by `check_op` and `check_reply`.) | The next change to the worker protocol or the menu data. | First step needs no refactor: a test that every enabled menu or profile action resolves to a handler, not only that wizard names exist. Add that test with the next menu work. |
| A3 | Split `devices/nspire/ui/views.py` (about 1,100 lines: calculator view, keypad, sidebar, several dialogs) into cohesive modules; derive the compact tools menu and the toolbar from one shared action list (currently duplicated in `ui/app.py`). | Move code as each part is next touched; do the shared action list the next time either menu changes. | Duplicated lists drift, so the shared list matters more than the file split. |
| A5 | Extend `tests/test_architecture.py` with new dependency rules as packages gain code (for example `sheet`, `graph`, `stats` must not import `device` or `app`). | Whenever a placeholder package gets its first module. | Also remove its `[placeholder]` tag in section 3. |
| A6 | Re-check the spare engine (`app/web.py`, decisions 0016, 0027, SDD-02). Each load still boots three Pyodide runtimes (Flet, the engine, the spare). Remaining options: skip the spare on phones (Cancel would then restart in about 2 to 4 s since 0027), or share one runtime. | Phone memory trouble or key-press lag, or Cancel changes. | Simon's phone install (2026-11-12) works but was slow (about 11 s to load on a Pixel 6). Partly done in 0027 (2026-11-12): engine boot cut from 7 to 9 s to 2 to 4 s, and the spare now waits 3 s after the engine is ready (`SPARE_DELAY`). Key-press lag was cut earlier (keypad not rebuilt per press: 322 ms to 34 ms per refresh, 2026-11-09). Still to do: time start-up, memory and key presses on the Pixel 6 (`tools/loadtime.py` for desktop) and record them in 0027. |
| A7 | Lazy-load catalog areas in the engine: register each function's name and arity up front, and import its module (calculus, matrices, distributions, finance and so on) on first use. | The phone timing (A6) shows the engine, not the UI, is what the user waits for, or a new area (SciPy statistics, M4) makes engine start-up slower. | Deferred in 0027: the engine boots in the background in about 2 s, and lazy loading moves that wait to the first use of a feature, perhaps mid-question. `core/builtin_names.py` already holds every name, so the registry change is small. Measure with `tools/loadtime.py` and a first-use timing per area; SciPy must stay lazy whatever is decided (PLAN section 3, `stats/`). |

**Keeping the map in sync.** `tests/test_architecture.py` fails if a package under `src/cassim/` is missing from the map in section 3, or still tagged `[placeholder]` after it has code. CLAUDE.md tells Claude to update the map in the same commit as any package move. Review the table above when a trigger is met and delete the row when done.

## 13. Future: native builds (Would, NFR-PORT-004)

Only the static web site is built and tested today (`python -m tools.publish`, output `build/web`). `flet build` can also make `windows`, `macos`, `linux`, `apk`, `aab`, `ipa` and `ios-simulator` packages from the same code. None has been tried. What each needs, so the work can be picked up later:

1. **Project setup.** A `[tool.flet]` section in `pyproject.toml` and a thin `src/main.py` that calls `cassim.app.main.run`; today only `tools/publish.py` stages a web entry point. Run `flet build` with `PYTHONUTF8=1` on Windows (decision 0018).
2. **Cancel.** `make_runner()` uses the worker engine only in the browser; native builds run the engine in-process, where `LocalEngine.cancel()` returns False. Cancel within 1 s (SRS) needs the engine in a subprocess or isolate.
3. **Dependencies.** The core needs only SymPy, mpmath and PyYAML (pure Python). SciPy and NumPy are not used by the app (decision 0031), so they do not block Android or iOS.
4. **Browser-only code.** The service worker, install prompt, share-link base URL and the engine worker assume a browser. File open and save, storage and the clipboard need a native check.
5. **Toolchains.** Flutter (the Flet CLI installs it). Windows needs Visual Studio with the C++ workload; Android needs the Android SDK and a JDK; macOS and iOS need a Mac with Xcode, and an Apple developer account beyond the simulator; Linux needs Linux. CI would need a runner per platform.
6. **Release.** Signing, store listings and updates are out of scope until a target is chosen.

## 14. Hosting on Cloudflare Pages (done 2026-11-13)

The site moved from GitHub Pages to Cloudflare Pages, and the repository is private. `.github/workflows/deploy.yml` builds and deploys three projects with `wrangler pages deploy`:

| Project | Address | Deployed on |
|---|---|---|
| `cassim-app` (stable) | <https://cassim-app.pages.dev/> | a published GitHub release, or a manual run with target `stable` |
| `cassim-calc` (testing) | <https://cassim-calc.pages.dev/> | every push to `main` |
| `cassim-wiki` (help) | <https://cassim-wiki.pages.dev/> | every push to `main`; `docs/wiki/` built by `python -m tools.wiki_site` |

Notes:

1. **Built at the root.** `tools.publish` now defaults to `--base-url ''`; `tests/e2e/test_pwa.py` still boots the site under `/CASSim/` so a sub-path build stays tested.
2. **Secrets.** The workflow needs `CLOUDFLARE_API_TOKEN` (Cloudflare Pages: Edit) and `CLOUDFLARE_ACCOUNT_ID` as repository secrets.
3. **Moving users.** Share links, installed apps and autosaved documents belong to an origin, so they do not carry over from the GitHub Pages address or between the stable and testing sites: save a document to a file and open it on the new site.
4. **Releasing.** `gh release create vX.Y.Z --generate-notes` deploys the current `main` to the stable site. The steps are in the README (Publishing).
5. **Verified.** The workflow deployed the testing site and the help pages from GitHub Actions on 2026-11-13.

## 15. Pluggable devices and separate bundles (decided 2026-11-13)

Simon's direction. `cassim-app` (stable) and `cassim-calc` (testing) become **all-in-one** apps: a shell that switches between the TI-Nspire, the Casio ClassPad, the pseudocode interpreter and tracer, the HP Prime and any later device, when each is built. Each device can also be published as its own **bundle** on its own site, so someone who needs one device downloads only that one. The cold start today is about 90 MB and a minute or more on a first visit, nearly all of it the engine (SymPy, SciPy, Pyodide) and the Flet app. Requirements: FR-PROF-001 to FR-PROF-009 and FR-RUN-009 in the SRS.

### 15.1 Devices, bundles and sites

| Device id (package `devices/<id>/`) | Bundle | Product name | Site (Cloudflare Pages project) | When |
|---|---|---|---|---|
| every built device, with the switcher | `all` | CASSim | `cassim-app` (stable), `cassim-calc` (testing) | live now, Nspire only |
| `nspire` | `tin` | CASSim-TIN | `cassim-tin` | M2x |
| `pseudocode` | `pseudo` | CASSim-pseudo | `cassim-pseudo` | M7 |
| `classpad` | `cp` | CASSim-CP | `cassim-cp` | M8 |
| `prime` | `prime` | CASSim-Prime | `cassim-prime` | M9, if go |

- Ids and package names in the code are the long ones; bundle and site names are the short ones.
- Single-device sites are **stable only**: they deploy on a release, like `cassim-app`. Testing happens on `cassim-calc`, which holds every device.
- The help site (`cassim-wiki`) stays one site, with a section per device, and lists every site.
- All seven Cloudflare Pages projects exist (the four single-device ones were reserved, empty, on 2026-11-13); a single-device site has no content until its bundle is first built.

### 15.2 Architecture: pluggable modules, separable UIs

1. **A device is a plug-in.** A device profile (FR-PROF-001) is a package, `src/cassim/devices/<id>/`, that exposes one `Device` object: id and title; the engine it needs (worker module and the Pyodide packages it loads); its page types; keymap, menus, skin and presets; its document schema namespace; and its help section. It depends on the shared layers and never on another device.
2. **Shared layers stay shared.** `core/` (maths, values, Pratt-parser framework), `runtime/` (interpreters), `device/` (key layers, menu and screen frameworks), the document model and storage, and the shell (`app/`: window, switcher, storage, share links, PWA, themes). Core still never imports Flet.
3. **Separable UIs.** Each device's Flet views live with the device (`devices/<id>/ui/`) and talk to the shell through a small interface: mount, unmount, menu and toolbar contributions, and dialogs. The shell knows device ids, not device classes.
4. **Registry by build, not by discovery.** Pyodide has no reliable entry points, so `tools.publish` writes a generated `bundle.py` that lists the devices in the bundle. The shell imports only what that file lists; a test checks that no device package imports another.
5. **One engine worker per device kind.** The Nspire engine boots SymPy; the pseudocode engine is pure Python and boots without it. The all-in-one app starts a device's worker when it is first opened.
6. **Documents name their device.** `.cassim.json` and share links carry the device id. Any bundle that contains that device opens them; one that does not names the site that does and links to it (FR-PROF-009). Storage namespaces are per device (FR-PROF-004, Q20), and each site is its own origin, so documents move between sites as files or share links.

### 15.3 Build, cache and deploy

- `python -m tools.publish --bundle all|tin|pseudo|cp|prime` builds one bundle. A bundle's packages, archives and service-worker list come from its devices.
- In the all-in-one app each device is its own archive (`device-<id>.zip` and its engine packages), fetched on first use. The service worker always precaches the shell. It also precaches each device once that device has been opened, so the device works offline from then on. The first visit therefore downloads only the shell and the device in use. An "Available offline" setting can fetch every device in advance.
- `deploy.yml` grows a matrix: `main` deploys `all` to `cassim-calc`; a release deploys `all` to `cassim-app` and each single-device bundle to its own project.
- Download size and cold start are measured per bundle and reported (no budgets, as in the SRS).

### 15.4 Order of work

Steps 1 to 3 are milestone M2x and come **before M3** (decided 2026-11-13), while only the Calculator page exists, so that Graphs, Lists & Spreadsheet and Statistics are built inside the new structure and never need moving. They change structure, not behaviour.

1. ADR on the device interface and bundle format: `docs/decisions/0032` (written 2026-11-13). It replaces the ADR planned for 8a, and splits step 2 into three PRs: `doc/` and registered page types; `devices/nspire/` with the profile data and the Calculator page model; the shell and `devices/nspire/ui/`. Its item 7 leaves the split of `core/` to M8a (agreed 2026-11-13).
2. Move the Nspire into `devices/nspire/` behind the interface, together with decision 0031's A4 (the document model moves to `doc/`, page types are registered). Gate: every corpus case replays unchanged, the e2e suite passes, and coverage targets hold.
3. Bundle-aware `tools.publish`, the `tin` bundle and its site, and download-size reporting. **Steps 1 to 3 done 2026-11-13** (decision 0032). `cassim-tin` gets its first content at the next release. The `tin` and `all` bundles are the same size today (90 MB, of which Flutter 57, Pyodide 16, the engine archive 11 and the app archive 2); the sizes differ once a second device is built.
4. (M7) The `pseudocode` device, from the built `runtime/` plus the M7 editor and trace views, as the second device and the first small bundle.
5. (M8) The switcher in the all-in-one app (8b), then ClassPad, and Prime (M9) as plug-ins.

### 15.5 Decisions (Simon, 2026-11-13)

- Pseudocode is its own device and site, and also an entry in the all-in-one app. This revises SRS Q23 and FR-RUN-009, which had the Code view as a mode inside one app.
- Steps 1 to 3 go before M3.
- Single-device sites are stable only.
- Long ids in code (`nspire`, `classpad`, `pseudocode`, `prime`); short names for bundles and sites.
