# CASSim — plan and architecture (draft for review)

A browser-based simulation of the TI-Nspire CX CAS: a static, installable (PWA) site where Python
(SymPy/SciPy, via Pyodide) runs client-side and the UI is built with Flet. Draft v0.2, 2026-11-02.

**Requirements live in `docs/SRS.md` (draft 0.3, all open questions answered).** This plan is the architecture and milestone view; where the two disagree, the SRS wins for *what*, this file for *how and when*. CASSim is a **simulator, not a hardware emulation**, released under the **Unlicense**.

## 1. What I checked while exploring (and what I didn't)

| Finding | Status |
|---|---|
| `flet publish` produces a static site with `manifest.json`, `flutter_service_worker.js`, icons and `python-worker.js`. Python 3.14 pins Pyodide 314.0.7. | Ran it (Flet 1.0.5) |
| Pyodide 314.0.7 ships numpy 2.4.6, scipy 1.18.0, sympy 1.14.0, mpmath, micropip. | Pyodide docs |
| Flet docs: static sites run Python in the browser; long CPU work can freeze the UI. `python-worker.js` hints Python may run in a worker. | Docs + build output; **worker behaviour unverified** |
| SymPy 1.14 does the core VCE operations quickly (solve, factor, apart, diff, integrate, limit, dsolve, det: each under 0.11 s natively; import 0.22 s, scipy import 1.4 s). | Ran `spikes/sympy_timings.py` |
| A TI-syntax evaluator spike (`:=`, `→`, `f(x)`, `solve(...)|x>0`, `[1,2;3,4]`, implicit multiplication, `√`, `π`) works but only through regex hacks. A real parser is needed. | Ran `spikes/ti_eval_spike.py` |
| **Divergence found:** `solve(sin(x)=1/2,x)` returns only the principal values in SymPy; TI returns the general solution with `@n1`. Expect many such differences, so the golden corpus (section 6) is essential. | Ran |
| `.tns` files are a proprietary container (`*TIMLP0601`, `Document.xml`, `Problem1.xml` entries) with opaque payloads. The community format notes I found say no known way to read them. | Inspected your `mm_*`/`gm_*` files; **not decoded** |
| Whether SymPy + SciPy actually load and run inside the Flet static build, and the cold-start time and download size. | **Not tested yet: first spike in M0** |

## 2. Principles

1. **Engine first, UI second.** A pure-Python core (no Flet imports, enforced by a lint rule) that is usable from a CLI, tests and the browser.
2. **A headless "device model"** (keys, menus, cursor, screen buffer) sits between engine and Flet, so keyboard and page behaviour is tested without a GUI. Flet only renders it.
3. **Behaviour is defined by the simulator, not by SymPy.** Every behaviour we claim is pinned by a golden test captured from the real TI-Nspire CX CAS simulator. The target is "close enough not to confuse a student or teacher": same mathematical content in a familiar form, exact text only where a case says `compare: exact`.
4. **Typed, linted, reproducible:** uv, Ruff, Ty, Git, CI from day one. SymPy is weakly typed, so it is quarantined behind one typed adapter module.
5. **Original implementation.** No TI ROM, TI artwork or logos. The handheld skin is our own design that keeps the familiar layout. A visible disclaimer says CASSim is not affiliated with TI and is not an approved exam calculator.
6. **Private by construction.** No server, no telemetry or analytics, no student data leaves the device. Imported documents and share links never auto-run code.

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
      errors.py                     TI error codes/messages
    basic/                  TI-Basic lexer/parser/interpreter (Prgm, Func, control flow, Disp/Request/Text, Try)
    pylib/                  Python-script bridge + sandbox API (see 5.4)
    libs/                   native Python ports of mm_/sm_/gm_ style libraries, registered as lib\fn
    sheet/                  Lists & Spreadsheet engine (cells, named columns = lists, formula columns, deps graph)
    stats/                  OneVar/TwoVar, regressions, tests/intervals, distributions (SciPy loaded lazily)
    graph/                  function/param/polar/sequence sampling, asymptote handling, analyse-graph tools;
                            emits a backend-neutral scene (paths, points, labels)
    doc/                    Document model (Problems, Pages), JSON schema + versioned (de)serialiser, migrations
    device/                 headless device model: key layers (shift/ctrl/var/menu/doc), menu tree (data-driven),
                            input editor, page controllers, screen buffer
    cli/                    `cassim` REPL (prompt_toolkit) + `cassim run file.tib`
  src/cassim_app/            FLET (thin): layouts, keyboard widget, screen renderer, file pickers, storage, PWA bits
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
- **Heavy dependencies.** SymPy loads at start; SciPy lazily on first stats/numerics call. Service worker caches everything for offline use.
- **2D maths display.** `format.py` returns a layout tree; the renderer draws it (Flet canvas). Input starts as linear text with template insertion (fraction inserts `(`…`)/(`…`)`); a full structured 2D editor is a later, separate sub-milestone (see M2d).
- **Storage.** Documents live in browser storage (IndexedDB via Pyodide `js` interop; localStorage is too small and Flet client_storage may be limited: spike 5). Upload/download of the native `.cassim.json` (versioned schema, schema-validated and size-limited on import). `.tns` import/export is deferred (Won't for now) and nothing depends on it.
- **Sharing.** A document can be shared as a URL: compressed and encoded in the URL **fragment**, so nothing reaches a server. Opening a link asks for confirmation first. Keep links under about 2,000 characters; larger documents fall back to file export.
- **Themes.** Dark is the default. Themes (at least Dark, Light, Outline) are defined in a user-editable config file (keypad, screen and accent colours), persisted in browser storage and exportable; an invalid config falls back to Dark with a message.
- **Accessibility.** Should-have, applied where cheap. Keyboard-only use and visible focus in Computer mode are required. Flet renders to a canvas, so screen-reader support is hard: gaps are recorded in `docs/accessibility.md` and stubbed (labels and semantics hooks), not silently skipped.
- **Graphics.** Engine emits a scene; Flet `canvas` draws it. Charts libraries are not suited to implicit functions, asymptotes and trace; matplotlib is too heavy for Pyodide.
- **Spreadsheet.** Custom calc engine (TI cell/column semantics, columns are shared Problem variables so they can't map onto Excel-style engines like `formulas`/`pycel`). A library is used only for I/O: stdlib `csv` and `openpyxl` (pure Python; confirm it loads in Pyodide) for xlsx import/export.

## 4. GUI modes (one device model, three skins)

| Mode | Layout | Use |
|---|---|---|
| **Computer CAS** (equal top priority) | Wide window: page tabs/sidebar (problems → pages), large 2D calculator pane, scrollable history, templates palette, variable/catalog panel, physical keyboard first | Teacher/student at a desk |
| **Tablet / demo** | Screen on one side, on-screen keyboard on the other (portrait/landscape), big touch targets, optional "show keystrokes" for projection | Live demonstration |
| **Handheld** (equal top priority) | Faithful-layout 320×240 screen + keypad; scales to fullscreen on phones; hardware keyboard mapped | Practising the real handheld workflow |

The device model drives all three; modes differ only in layout components and which panels are visible. Primary test targets: Chromebooks, Chrome, Safari (macOS, iOS, iPadOS); secondary, smoke-tested: Edge, Firefox. Handheld mode must be usable at 360 px wide in both orientations. Hosting is any free or cheap static host (GitHub Pages first) with correct MIME types.

## 5. Features by area

1. **Calculator page.** History, `Ans`, ctrl+enter approximation, templates, catalog, variable menu, copy/paste of results, errors.
2. **Pages:** Calculator, Graphs, Lists & Spreadsheet, Data & Statistics, Notes, Program Editor, Python (new). Geometry is out of scope.
3. **Documents.** Multiple documents, problems, page sorter, settings dialogs, undo/redo, autosave.
4. **Extending beyond the real calculator.** (a) TI-Basic programs/functions, including `Define LibPub` libraries. (b) A Python page and a `py("script","fn",args)` call from the CAS. Scripts get a small `cassim` API (read/write Problem variables, evaluate TI expressions). Python in an uploaded document **never auto-runs**: explicit "Run" with a trust prompt, since documents and share links are untrusted. The Python page is Could-have; if built, the sandbox and prompt are mandatory.
5. **Libraries (mm_/sm_/gm_).** The `.tns` libraries cannot be loaded directly. Plan: reimplement each UDF as native Python (fast, typed, testable), verified against the simulator with the libraries installed. LazyMath is also Unlicense, so porting and redistribution are permitted; still record that check in `docs/decisions/` before the first port.

## 6. Testing strategy ("every stage properly tested")

| Layer | What | Tooling |
|---|---|---|
| Unit | lexer, parser, printer round-trips, values, settings, each catalog function | pytest, Hypothesis |
| **Golden corpus** | Simulator-captured cases, replayed through the engine. This is the regression net | pytest parametrised from YAML |
| Device model | key sequence → expected screen text/state, menu navigation, mode switching | pytest, no GUI |
| Render snapshots | handheld/tablet/computer screens at fixed viewport; image diff with tolerance | Playwright + pixelmatch-style compare |
| E2E / PWA | built static site served locally: loads, types, evaluates, installs, works offline (service worker) | Playwright |
| Static | formatting, lint, strict types | Ruff, Ty |
| Coverage and traceability | At least 90% line and branch on `core/`, 80% on `device`, `doc`, `sheet`, `stats`, `graph`; `cassim_app` excluded (Playwright covers it). Every SRS requirement ID appears in a test or is listed as untested with a reason; `tools/` generates `docs/traceability.md`, checked in CI | pytest-cov, `tools/` |

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

- **uv** (Python 3.14 to match Pyodide 314), lockfile committed. **Ruff** for lint and format (rules: E, F, I, UP, B, SIM, ANN, PL, PT, RUF; `ANN` and strictness on `core/`). **Ty** for types, strict on the core packages; I have not verified Ty's current stability, so M0 checks it and keeps pyright as a fallback if SymPy/Flet stubs block us. **Git** with conventional commits, pre-commit (ruff, ty, fast tests), GitHub Actions CI (lint, types, tests, web build, Playwright smoke), deploy to GitHub Pages or similar static host.
- Flet MCP / Claude Code: helpful from M2 for GUI iteration, so I'd switch to Claude Code before M2 (and for the repo work in M0/M1 too).

## 8. Milestones

Sizes are rough effort (S ≈ days, M ≈ 1–2 weeks, L ≈ several weeks). Each milestone ends with its tests green and a tagged release.

**M0 — Foundations and de-risking (M)**
- Repo, uv, Ruff, Ty, pytest, pre-commit, CI. Decision log in `docs/decisions/`.
- Spike 1: SymPy + SciPy inside the Flet static build (cold-start time, download size, offline, does Python run in a worker, can we cancel?). Spike 2: `.tns` decodability. Spike 3: Flet canvas drawing speed (graph of 2000 points, pan/zoom). Spike 4: IndexedDB from Pyodide. Spike 5: `openpyxl` in Pyodide.
- Corpus tooling (schema, replay, capture checklist) and the first ~60 simulator-captured cases.
- Extract a complete command coverage matrix from the Reference Guide (draft index of ~290 entries already in `docs/reference_index_draft.txt`; extractor misses some, e.g. `solve`, so it needs refining).
- Exit: spikes written up with go/no-go; CI green on an empty package; corpus replays.

**M1 — Text-based CAS with TI syntax (L)**
- 1a Lexer, parser, AST, printer (+ Hypothesis round-trips).
- 1b Values, settings (angle/mode/real-complex/digits), `Ans`, exact vs approximate rules, TI-style formatting and error messages.
- 1c Documents/Problems/scope: `Define`, `:=`, `→`, `DelVar`, `ClearAZ`, `Local`, constraint `|`, libraries namespace.
- 1d Catalog, in tiers. Tier 1 (VCE core): solve/cSolve/zeros, factor/expand/propFrac/completeSquare, derivative/integral/limit/nInt/deSolve, trig and exponentials, lists and matrices (det, inverse, rref), norm/binom/inv distributions, `tvm*`/`eff`/`nom`, regressions and OneVar. Tier 2: remainder of the Reference Guide. Tier 3: edge conversions and unusual templates.
- 1e `cassim` REPL and script runner, tab-completion from the catalog.
- Exit: Tier 1 corpus passes (canonical at minimum), strict types on `core/`, coverage matrix published.

**M2 — GUI shell: keyboard, pages, settings (L)**
- 2a Device model: key layers, menu tree from data, linear input editor, screen buffer; headless key-sequence tests.
- 2b Flet app with the three modes; 2D result rendering from layout tree; physical keyboard mapping.
- 2c Documents, Problems, Pages (add/delete/reorder, page sorter), variable list, document/system settings dialogs, undo/redo.
- 2d Structured 2D input editor (fractions, powers, roots, matrices) as a contained sub-project, shippable after 2a–2c if it slips.
- 2e Storage and files: IndexedDB persistence, autosave, upload/download `.cassim.json`, PWA install and offline, fullscreen handheld on phones.
- Exit: build the static site, install on phone, complete the golden "exam-style" scripted flows via device-model tests and Playwright.

**M3 — Data pages: Lists & Spreadsheet, Data & Statistics, Finance (L)**
- Spreadsheet engine and page (named columns as lists, formula columns, fill, CSV/xlsx I/O).
- Data & Statistics plots (dot, histogram, box, scatter), regression overlays and residuals, OneVar/TwoVar tables, Finance Solver dialog.
- Exit: the General Maths workflows from the cas-solver skill reproduced as tests.

**M4 — Graphs and Tables (L)**
- Graph page with function/parametric/polar/sequence/differential-equation entry, window and zoom, trace, analyse-graph tools (zero, min/max, intersection, ∫, dy/dx), sliders, Table view; Notes page.
- Exit: graph snapshot tests, performance budget met on mid-range phone.

**M5 — Programming and extensions (L)**
- TI-Basic interpreter + Program Editor; library mechanism; Python page and `py()` bridge with trust model; native ports of mm_/sm_/gm_ libraries (licence check first), each verified on the simulator.

**M6 — Polish and extras (M)**
- Accessibility follow-through (`docs/accessibility.md`); localisation-ready strings; exam-restriction mode (Could-have, teacher-configurable); theme config export/import; user docs; public deployment. `.tns` is dropped from scope for now.

## 9. Risks and decisions

Decisions (from the SRS review, 2026-11-02; do not re-litigate):

1. **Fidelity:** canonical equality first, exact text per area as the corpus grows; "close enough not to confuse" is the bar.
2. **Performance and size:** no hard budgets. Cold start (baseline 15 s vendored, 35 s CDN) and download (22 MB CDN, 95 MB vendored) are measured and reported with a progress screen. Tier 1 operations aim for 1 s or less after import; SciPy first use 5 s or less and shown as busy; Cancel within 1 s.
3. **Licensing:** CASSim and LazyMath are both Unlicense. TI marks, artwork and ROM are never shipped; reference screenshots stay in `docs/design/reference/`, not the build.
4. **Appropriate use:** teaching, practice and demonstration. Not an approved exam calculator, and the UI says so.
5. **Python 3.14, no Geometry page, no `.tns` for now.**

Open risks:

1. **Flet static limits** (threading, cancellation, canvas speed): M0 spikes were go; fallback is a thin custom web front-end over the same engine. MathLive/MathQuill in the Flet web build is still unverified.
2. **Simulator capture effort:** driving the simulator by screenshot is slow; budget it per milestone and prioritise Tier 1 cases.
3. **Offline end to end:** wheels must be vendored and `index.html` patched after `flet publish` (decision 0002); verify with Playwright.
4. **Accessibility on a canvas renderer:** screen-reader support may not be achievable in Flet; tracked in `docs/accessibility.md`.

## 10. Design documents

The SDD set (`docs/design/SDD-00` to `SDD-11`: overview, engine, worker and cancel, display and format, device model, Flet UI, document and storage, data pages, graphing, programming and Python, PWA and build, test strategy) is listed in SRS appendix A and written as each area is designed. Requirement IDs (`FR-*`, `NFR-*`) are the stable references between SRS, SDD, tests and corpus tags.
