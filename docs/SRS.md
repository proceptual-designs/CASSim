# CASSim: Software Requirements Specification

Status: **DRAFT 0.3** (2026-11-02; all open questions answered). Structure follows ISO/IEC/IEEE 29148. Source material: `PLAN.md`, `CLAUDE.md`, `docs/decisions/0001-0008`, `docs/testing/TESTING.md`. Items marked **[Q#]** depend on an open question in section 10. Items marked **[TBC]** are inferred, not yet confirmed.

Requirement IDs are stable (`FR-CAS-012`). Priority is MoSCoW (M/S/C/W). "Mx" is the milestone in PLAN.md section 8. Verification: **T** test (unit/corpus/device), **E** E2E (Playwright), **I** inspection, **D** demonstration, **A** analysis (measurement).

---

## 1. Introduction

### 1.1 Purpose
Defines what CASSim must do and the constraints it must meet. It is the baseline for the design documents (SDD, `docs/design/`) and for acceptance testing.

### 1.2 Scope
CASSim is a static, installable (PWA) browser simulation of the TI-Nspire CX CAS for teaching, practice and demonstration. The maths engine (SymPy/SciPy) runs client-side in Pyodide. There is no server component. CASSim reproduces the *behaviour* and *workflow* of the handheld/teacher software, not its ROM, artwork or branding.

CASSim is a **simulator, not a hardware-level emulation**: it need not match TI output exactly, but must be close enough not to confuse students or teachers. CASSim is released under the Unlicense.

Out of scope: Geometry page; approved-exam-calculator status; TI ROM/OS code, logos or artwork; loading `.tns` libraries (the `mm_`/`sm_`/`gm_` UDFs are ported natively instead); server-side accounts or sync.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| CAS | Computer algebra system |
| TI simulator | TI-Nspire CX CAS Premium Teacher Software, the behavioural oracle that CASSim is compared against |
| Corpus | Golden test cases captured from the simulator (`corpus/`) |
| Document / Problem / Page | TI hierarchy: a document holds Problems; Problems share variables; each holds Pages (Calculator, Graphs, ...) |
| Device model | Headless model of keys, menus, cursor and screen, independent of Flet |
| VCE | Victorian Certificate of Education (Methods, Specialist, General Mathematics) |
| Canonical equality | Two results are equal if symbolically/numerically equal, regardless of text form |

### 1.4 References
`PLAN.md`; `CLAUDE.md`; `docs/decisions/`; `docs/command_matrix.md`; `docs/testing/TESTING.md`; `references/` (TI Reference Guide, VCE resources, LazyMath guides); `docs/design/reference/` (layout screenshots).

### 1.5 Stakeholders
| Role | Interest |
|---|---|
| Owner/developer (Simon Tyler) | Accuracy, maintainability, scope control |
| Maths teachers | Demonstration to a class; preparing worked solutions |
| Students (Years 10-12, VCE) | Practising calculator workflow outside class and without a device |
| School IT | Hosting, device compatibility (Chromebooks, iPads), privacy |
| Library authors (LazyMath) | Licence compliance for ported UDFs |
| Texas Instruments | Trademark/IP boundary (no marks, artwork or ROM) |

---

## 2. Overall description

### 2.1 Product perspective
A self-contained web app: Flet UI (Flutter web, canvas rendered) over a pure-Python core (`src/cassim/core`) that never imports Flet. The engine runs in its own Pyodide worker so the UI stays responsive and evaluation can be cancelled by terminating that worker (decision 0005). Persistence is in the browser (IndexedDB). Hosted as static files.

### 2.2 Product functions (summary)
Calculator page with TI syntax; Graphs and Table; Lists & Spreadsheet; Data & Statistics; Finance; Notes; Program Editor and TI-Basic; Python page; documents and Problems; three display modes (Computer, Tablet/demo, Handheld); offline use.

### 2.3 Users and classes
1. **Student**: knows the handheld; wants identical keystrokes and results.
2. **Teacher presenting**: needs readable large display, optional keystroke display, fast recovery from mistakes.
3. **Teacher authoring**: builds documents, programs, Python scripts; shares files with students.
4. **Developer/maintainer**: runs corpus, adds commands.

### 2.4 Operating environment
Evergreen desktop and mobile browsers. Primary: Chromebooks, Chrome, Safari. Secondary: Edge, Firefox. Python 3.14 / Pyodide 314.0.7. Static hosting on GitHub Pages or any other free or cheap static host, with correct MIME types (`.mjs`) and no server-side code. Share links must stay within typical URL limits (about 2,000 characters is safe across browsers). Dev: Windows 11, uv, Ruff, Ty, pytest, Hypothesis, Playwright.

### 2.5 Constraints
- C-1 Core is pure Python, fully typed, Ty strict; SymPy is touched only in `core/compat/sympy_adapter.py`.
- C-2 No TI logos, artwork, ROM content. Product name is CASSim.
- C-3 TI syntax is parsed by a real tokenizer + Pratt parser, never regexes.
- C-4 Canonical text is Unicode (`ⅇ ⅈ ᴇ π ∞ ᵀ ʳ ᵍ ° ∠ ▶`); ASCII is an input/REPL spelling only. These conventions are fixed.
- C-5 Statistics follow the TI/school convention (quartiles as medians of halves; `sx` uses n-1, `σx` uses n); `numpy.percentile` is not used.
- C-6 The Flet static build needs a post-publish step (vendor wheels, patch `index.html`) for offline use (decision 0002).
- C-7 Must not auto-run user Python from a loaded document.

### 2.6 Assumptions and dependencies
Pyodide continues to bundle SymPy and SciPy at compatible versions; Flet static publishing remains viable (fallback: thin custom web front-end over the same engine); simulator access remains available for corpus capture; LazyMath stays Unlicense (to be recorded in a decision before porting).

---

## 3. Fidelity and correctness model

This cross-cuts every functional area.

- **FID-1** (M, T) Correctness is judged by canonical equality against the simulator corpus, not by TI's exact output text. Maths is rendered from LaTeX/layout tree.
- **FID-2** (S, T) Output must be close enough not to confuse a student or teacher used to the handheld: same mathematical content, familiar form (e.g. `x=-2 or x=2`, fractions stay exact in Auto mode). Exact text match is not required. Where the corpus marks an area `compare: exact` (typically number display and simple forms), the text matches the simulator.
- **FID-3** (M, T) Every claimed behaviour has at least one corpus case with provenance (`simulator` or `hand-verified`) and evidence where simulator-captured. No behaviour change ships without a test.
- **FID-4** (M, T) Known divergences are `xfail(strict=True)` with a reason, so fixing one forces removing the marker.
- **FID-5** (M, T) Documented simulator behaviours are matched (TESTING.md section 14), including: Approximate mode shows decimals inside symbolic results; Float 3/Fix 2 switch to `ᴇ` notation for extreme values; `1/0` and `ln(0)` give `undef`; undefined variables echo unchanged; `int(-2.5) = -3`; `sinh⁻¹(1)` is unevaluated in Auto mode.
- **FID-6** (S, T) TI-specific solution forms are reproduced: general solutions with `@n1` constants, `cSolve`, `x=-2 or x=2`, domain constraints via `|`.

---

## 4. Functional requirements

### 4.1 Language and evaluation (core) — M1
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-LANG-001 | Tokenise and parse TI input: `:=`, `→`/`->`, `|` constraint (lowest precedence), implicit multiplication (`2x(x-1)`, `f(x)` call vs `ax`), `^` with TI unary-minus rules, `√`, `π`, `ᵀ`/`@t`, `≤ ≥ ≠`, `and or not xor`, lists `{}`, matrices `[1,2;3,4]`, strings, `lib\fn`, `@n1`, `#` indirection, primes, units `_m`. | M | T |
| FR-LANG-002 | Typed ASCII input spellings are accepted (`@e @i @E @t @r @g @d @< @> pi infinity`); outputs use Unicode forms. | M | T |
| FR-LANG-003 | Printer round-trips: parse -> print -> parse is the identity on the AST (Hypothesis). | M | T |
| FR-LANG-004 | Plain `e`, `i`, `E` are ordinary variables; `2e3` is `2*e3`. | M | T |
| FR-EVAL-001 | Evaluate to a typed Value (Number, Expr, List, Matrix, Str, Bool, Eq, Void, Unit). | M | T |
| FR-EVAL-002 | Settings: angle (Radian/Degree/Gradian), calculation mode (Auto/Exact/Approximate), Real/Rectangular/Polar, float digits (Float n / Fix n), exponential format, base. | M | T |
| FR-EVAL-003 | VCE presets: General (Degree/Approximate/Real), Methods (Radian/Auto/Real), Specialist (Radian/Auto/Rectangular), Float 8. | M | T |
| FR-EVAL-004 | Exact vs approximate follows TI rules (mode, and a decimal point forces approximation); `Ans` and last-answer insertion behave as on the handheld. | M | T |
| FR-EVAL-005 | Errors use TI error codes/messages where known; engine errors never crash the UI. | M | T |
| FR-EVAL-006 | Evaluation is cancellable (On/Esc equivalent) within a bounded time; state is restored after cancel. | M | T/E |
| FR-SCOPE-001 | Document > Problem > Pages scoping; `Define`, `:=`, `→`, `DelVar`, `ClearAZ`, `Local`; library functions are document-wide and read-only. | M | T |
| FR-SCOPE-002 | A new Problem is a blank variable scope. | M | T |

### 4.2 Command catalogue — M1d (tiered)
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-CAT-001 | **Tier 1 (VCE core)**: solve/cSolve/zeros, factor/expand/propFrac/completeSquare, derivative/integral/limit/nInt/deSolve, trig/exponential/log, lists and matrices (det, inverse, rref), norm/binom/inv distributions, `tvm*`/`eff`/`nom`, regressions, OneVar/TwoVar. | M | T |
| FR-CAT-002 | **Tier 2**: remainder of the Reference Guide CAS commands, per `docs/command_matrix.md`. | S | T |
| FR-CAT-003 | **Tier 3**: unusual conversions and templates. | C | T |
| FR-CAT-004 | Catalog is data-driven and powers tab-completion, the Catalog dialog and help text. | S | T |
| FR-CAT-005 | The command coverage matrix is published and kept current. | M | I |
| FR-CAT-006 | Unsupported commands fail with a clear, TI-like error rather than a wrong answer. | M | T |

### 4.3 Calculator page — M2
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-CALC-001 | History of input/result pairs (input left, result right), scrollable, with `Ans`. | M | D/E |
| FR-CALC-002 | Evaluate (Enter) and force-approximate (ctrl+Enter). | M | T |
| FR-CALC-003 | Results rendered as 2D maths (fractions, powers, roots, matrices, summations). | M | D |
| FR-CALC-004 | Input starts as linear text with template insertion; a structured 2D editor follows (M2d). | M / S | D |
| FR-CALC-005 | Templates palette, Catalog, variable menu, copy/paste of inputs and results, up-arrow recall/edit of history. | M | D |
| FR-CALC-006 | Undo/redo of edits and of deleted history. | S | T |

### 4.4 Documents, Problems and pages — M2
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-DOC-001 | Multiple documents; add/delete/reorder Problems and Pages; page sorter. | M | D |
| FR-DOC-002 | Document and system settings dialogs. | M | D |
| FR-DOC-003 | Autosave to browser storage (IndexedDB); recover after reload or crash. | M | E |
| FR-DOC-004 | Export/import native plain-text `.cassim.json` with a versioned schema and migrations. | M | T |
| FR-DOC-007 | Share a document as a URL: the document is compressed and encoded into the URL fragment (so nothing reaches any server); opening the link loads it after a confirmation. Documents too large for a link fall back to file export. | S | T/E |
| FR-DOC-005 | Page types in scope: Calculator, Graphs, Lists & Spreadsheet, Data & Statistics, Notes, Program Editor, Python. Geometry excluded. | M | I |
| FR-DOC-006 | `.tns` import/export: deferred to a later release (Won't for now); no other feature depends on it. | W | D |

### 4.5 Lists & Spreadsheet — M3
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-SHEET-001 | Cells, named columns that are shared Problem list variables, formula columns, fill, sort. | M | T |
| FR-SHEET-002 | Whole-column references `a[]`; dependency graph with recalculation. | M | T |
| FR-SHEET-003 | CSV import/export; xlsx via `openpyxl` if it loads in Pyodide (decision 0003). | S | T |

### 4.6 Data & Statistics and Finance — M3
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-STAT-001 | Plots: dot, histogram, box, scatter; regression overlays and residuals. | M | T/D |
| FR-STAT-002 | OneVar/TwoVar with TI quartile and sd conventions (constraint C-5). | M | T |
| FR-STAT-003 | Regressions (linear, quadratic, cubic, exponential, power, logistic, etc.) per the corpus. | M | T |
| FR-STAT-004 | Distributions, hypothesis tests and intervals; SciPy loaded lazily on first use. | M | T |
| FR-FIN-001 | Finance Solver dialog and `tvm*`/`eff`/`nom` with the TI argument order. | M | T |

### 4.7 Graphs and Table — M4
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-GRAPH-001 | Function, parametric, polar, sequence, conic and differential-equation entry types. | M | T/D |
| FR-GRAPH-002 | Window settings, zoom, pan, trace; coordinates labelled to 2 dp. | M | D |
| FR-GRAPH-003 | Analyse Graph: zero, minimum/maximum, intersection, integral (typed bounds accepted), dy/dx. | M | T |
| FR-GRAPH-004 | Asymptotes and discontinuities handled (no spurious joining lines). | M | T |
| FR-GRAPH-005 | Sliders; Table view of graph functions. | S | D |
| FR-GRAPH-006 | The graph engine emits a backend-neutral scene; one `Points` canvas shape per curve (decision 0004). | M | I |
| FR-GRAPH-007 | Pan/zoom of a 2000-point curve stays interactive on a mid-range phone and a Chromebook. | S | A |

### 4.8 Programming and extensions — M5
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-PROG-001 | TI-Basic interpreter: `Prgm`/`Func`, control flow, `Disp`/`Request`/`Text`, `Try`, `Local`. | C | T |
| FR-PROG-002 | Program Editor page; `Define LibPub` libraries and `lib\fn` namespace. | C | T |
| FR-PY-001 | Python page and `py("script","fn",args)` call from the CAS; small `cassim` API (read/write Problem variables, evaluate TI expressions). | C | T |
| FR-PY-002 | If FR-PY-001 is built: scripts run sandboxed in the browser; the user is prompted before any run; scripts in loaded documents or shared links never auto-run. | M (conditional) | T/E |
| FR-LIB-001 | Native Python ports of `mm_`, `sm_`, `gm_` UDFs registered as `lib\fn`, each checked against the simulator with the library installed. LazyMath is also Unlicense, so redistribution is permitted. | C | T |

### 4.9 Device model and display modes — M2
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-DEV-001 | Headless device model (key layers shift/ctrl/var/menu/doc, data-driven menu tree, input editor, screen buffer) fully testable without a GUI. | M | T |
| FR-DEV-002 | **Computer** mode: page/problem sidebar, large 2D pane, templates/catalog/variable panels, physical keyboard first. Equal top priority with Handheld. | M | D |
| FR-DEV-003 | **Tablet/demo** mode: screen plus on-screen keyboard (portrait/landscape), large touch targets, optional "show keystrokes". | S | D |
| FR-DEV-004 | **Handheld** mode: faithful 320x240 layout and keypad, scales to fullscreen on phones, hardware keyboard mapped. Equal top priority with Computer. | M | D |
| FR-DEV-005 | Key layout and secondary labels (ctrl/shift) match the real device layout, drawn in CASSim's own artwork. | S | I |
| FR-THEME-001 | **Dark** is the default theme. | M | D |
| FR-THEME-002 | Themes (at least Dark, Light, Outline) are selectable in the UI and defined in a config file (colours for keypad, screen, accents) that users can edit; invalid config falls back to Dark with a message. Config persists in browser storage and can be exported/imported. | S | T/D |
| FR-DEV-006 | All three modes use the same device model; they differ only in layout components. | M | I |

### 4.10 Teacher and class features
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-TCH-001 | Large-text/projection mode and "show keystrokes". | S | D |
| FR-TCH-002 | Exam-restriction mode, teacher-configurable (e.g. disable Python page, programs, selected commands). Clearly not an approved exam device. | C | T |
| FR-TCH-003 | Share documents by file or by URL link (see FR-DOC-004, FR-DOC-007). No server. | S | D |

### 4.11 Installation and offline — M2e
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-PWA-001 | Installable PWA (manifest, icons, service worker). | M | E |
| FR-PWA-002 | Fully functional offline after first load, with no external network requests (Pyodide, wheels, CanvasKit, fonts all vendored). | M | E |
| FR-PWA-003 | Loading screen with progress during cold start. | M | D |
| FR-PWA-004 | App shows its version and offers update when a new service worker is available. | S | E |

---

## 5. Non-functional requirements

### 5.1 Performance
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| NFR-PERF-001 | Cold start (no cache) has no hard limit (baseline 15 s vendored, 35 s CDN); it is measured and reported, and shows a progress screen. | C | A |
| NFR-PERF-002 | Warm start (cache populated) is noticeably faster than cold start; measured and tracked, no fixed target. | S | A |
| NFR-PERF-003 | Typical Tier 1 operation (solve, factor, diff, integrate) returns in <= 1 s after import; SciPy first-use delay <= 5 s and shown as busy. | S | A |
| NFR-PERF-004 | UI remains responsive during evaluation; Cancel takes effect within 1 s. | M | E |
| NFR-PERF-005 | Total download is measured and reported. Baseline 22 MB (CDN) / 95 MB (vendored); no fixed budget. | C | A |

### 5.2 Reliability and data safety
- NFR-REL-001 (M) No data loss on reload, crash or worker restart: document state is restorable from storage.
- NFR-REL-002 (M) A worker kill (cancel) restores the document's variables and settings.
- NFR-REL-003 (S) Autosave failure (quota/blocked storage) is reported and export is offered.

### 5.3 Security and privacy
- NFR-SEC-001 (M) No server component; **no telemetry or analytics of any kind**; no student data leaves the device. Share links carry data in the URL fragment, which browsers do not send to servers.
- NFR-SEC-002 (M) User Python runs in the browser sandbox with a trust prompt; imported documents never auto-run code (Python or programs).
- NFR-SEC-003 (M) Imported `.cassim.json` files and share links are schema-validated and size-limited; malformed input is rejected without side effects.
- NFR-SEC-004 (S) No eval of document-supplied strings outside the engine's parser/interpreter.

### 5.4 Usability and accessibility
- NFR-USE-001 (M) Keystroke-for-keystroke workflows match the handheld where the key exists.
- NFR-USE-002 (S) Accessibility is Should-have, applied where cheap. Keyboard-only operation in Computer mode and visible focus are required. Screen-reader support is hard because Flet renders to a canvas: where it is not easy, the gap is flagged in `docs/accessibility.md` and stubbed (labels and semantics hooks in place, behaviour to follow), not silently skipped.
- NFR-USE-003 (S) Adjustable text size; built-in themes meet WCAG AA contrast.
- NFR-USE-004 (C) Localisation-ready strings (English first).

### 5.5 Portability and compatibility
- NFR-PORT-001 (M) **Primary** test targets: Chromebooks (ChromeOS), Chrome, Safari (macOS, iOS, iPadOS). Every release is tested on these. **Secondary** (best effort, smoke-tested): Edge, Firefox.
- NFR-PORT-002 (M) Touch, mouse and hardware keyboard.
- NFR-PORT-003 (S) Handheld mode usable at 360 px wide and in both orientations.

### 5.6 Maintainability and quality
- NFR-MAINT-001 (M) Ruff clean; Ty strict on `core/`; CI (lint, types, tests, web build, Playwright smoke) green before merge. CI is not yet running because there is no remote.
- NFR-MAINT-002 (M) Core never imports Flet (lint rule); SymPy only in the adapter.
- NFR-MAINT-003 (M) Conventional commits; small commits; decisions recorded in `docs/decisions/`.
- NFR-MAINT-004 (S) Line and branch coverage of at least 90% on `src/cassim/core/` and 80% on the other non-UI packages (`device`, `doc`, `sheet`, `stats`, `graph`). `cassim_app` (Flet UI) is excluded and covered by Playwright. CI reports coverage and fails below target.
- NFR-MAINT-006 (M) Every requirement ID appears in at least one test (marker or docstring) or is listed as untested with a reason. A generated traceability table (`docs/traceability.md`) is checked in CI.
- NFR-MAINT-005 (S) Dependency versions pinned (uv lockfile); Pyodide upgrade procedure documented.

### 5.7 Legal and licensing
- NFR-LEG-001 (M) No TI marks, artwork, ROM content or screenshots shipped. Reference screenshots stay in `docs/design/reference/`, not the build.
- NFR-LEG-002 (M) A visible disclaimer: not affiliated with or endorsed by TI; not an approved exam calculator.
- NFR-LEG-003 (M) CASSim is released under the Unlicense. Third-party notices (Flet, Pyodide, SymPy BSD, SciPy BSD, MathLive/MathQuill if used) ship with the build.
- NFR-LEG-004 (S) Before porting LazyMath UDFs, record the licence check (LazyMath Unlicense) in `docs/decisions/`.

---

## 6. External interfaces
- **User interface**: three display modes (4.9); own-branded skin; reference screenshots in `docs/design/reference/`.
- **Files**: `.cassim.json` (versioned), CSV, optionally xlsx; optional `.tns` (M6).
- **Browser APIs**: IndexedDB, Service Worker, Web Workers, Clipboard, File System / download, fullscreen, Web App Manifest.
- **Software**: Pyodide 314.0.7, SymPy 1.14, SciPy 1.18, NumPy 2.4, mpmath, Flet 1.0.x; MathLive (fallback MathQuill) for the 2D editor, **unverified in the Flet web build**.
- **Internal**: engine worker protocol (request/response/cancel/restore); device-model API consumed by Flet; scene format for graphs.

## 7. Data requirements
- Document JSON schema: document -> Problems -> Pages -> page state; variables with Value serialisation; settings; library definitions; schema version; migration chain.
- Corpus YAML case schema (`id`, `course`, `tags`, `steps`, `provenance`, `status`, `compare`) as in PLAN.md section 6.
- Retention: all data local to the browser; user can export and delete everything.

## 8. Verification and acceptance
- **Unit/property** (pytest, Hypothesis): lexer, parser round-trip, values, settings, catalog functions.
- **Golden corpus**: replayed through the engine; `python -m tools.replay` reports progress. Status flow: `pending` -> `pass` / `xfail(reason)` / `hand-verified`, with Simon's review.
- **Device-model tests**: key sequence -> screen/state.
- **Render snapshots** (Playwright): per mode at fixed viewport, tolerance-based diff.
- **E2E/PWA**: build, serve, load, evaluate, install, go offline.
- **Acceptance gates** map to milestone exits in PLAN.md section 8: M1 Tier 1 corpus passes (canonical), strict types on `core/`, matrix published; M2 install on a phone and run scripted exam-style flows; M3 the General Maths workflows pass; M4 graph snapshots and performance budget.

## 9. Requirement traceability
Each FR maps to: milestone (above), corpus tags (e.g. `solve`, `tier1`), tests, and design component (SDD section). A script in `tools/` generates `docs/traceability.md` from the requirement IDs in this file and the markers in tests and corpus tags (NFR-MAINT-006).

---

## 10. Open questions
Q1-Q15 are answered and folded into the text above. No open questions remain; new ones will be added as the design docs surface them.

---

## Appendix A. Proposed design-document set (`docs/design/`)
| Doc | Content |
|---|---|
| `SDD-00-overview.md` | Architecture views, layering, dependency rules, data flow |
| `SDD-01-engine.md` | Lexer/parser/AST, values, evaluator, scope, SymPy adapter, errors |
| `SDD-02-worker-and-cancel.md` | Pyodide worker protocol, cancel/restore, loading |
| `SDD-03-display-and-format.md` | Number display rules, layout tree, LaTeX rendering |
| `SDD-04-device-model.md` | Key layers, menu tree, input editor, screen buffer |
| `SDD-05-ui-flet.md` | Layout modes, renderer, keypad, themes, 2D editor integration |
| `SDD-06-document-and-storage.md` | Schema, versioning, IndexedDB, import/export |
| `SDD-07-data-pages.md` | Spreadsheet, statistics, finance |
| `SDD-08-graphing.md` | Scene format, sampling, analysis tools, performance |
| `SDD-09-programming-and-python.md` | TI-Basic, Python bridge, trust/sandbox model |
| `SDD-10-pwa-and-build.md` | Build pipeline, vendoring, service worker, deploy |
| `SDD-11-test-strategy.md` | Corpus, replay, device and E2E tests, CI |
