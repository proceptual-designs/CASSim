# CASSim: Software Requirements Specification

Status: **DRAFT 0.6** (2026-11-08: implementation status added as appendix B, storage and editor wording brought into line with what is built; earlier, 2026-11-04; Q1–Q15 answered; Q16–Q41 are new and concern the post-Nspire scope in 4.12. **The Code part (M7: Python and pseudocode, 4.12 Code view, runtime, pseudocode, translation, trace, settings, syntax and editor) is finalised: every question it depends on is answered.** Only the ClassPad and HP Prime questions, Q17, Q18, Q19 and Q22, remain open). Structure follows ISO/IEC/IEEE 29148. Source material: `PLAN.md`, `CLAUDE.md`, `docs/decisions/0001-0012`, `docs/testing/TESTING.md`. Items marked **[Q#]** depend on an open question in section 10. Items marked **[TBC]** are inferred, not yet confirmed.

Requirement IDs are stable (`FR-CAS-012`). Priority is MoSCoW (M/S/C/W). "Mx" is the milestone in PLAN.md section 8. Verification: **T** test (unit/corpus/device), **E** E2E (Playwright), **I** inspection, **D** demonstration, **A** analysis (measurement).

---

## 1. Introduction

### 1.1 Purpose
Defines what CASSim must do and the constraints it must meet. It is the baseline for the design documents (SDD, `docs/design/`) and for acceptance testing.

### 1.2 Scope
CASSim is a static, installable (PWA) browser simulation of the TI-Nspire CX CAS for teaching, practice and demonstration. The maths engine (SymPy/SciPy) runs client-side in Pyodide. There is no server component. CASSim reproduces the *behaviour* and *workflow* of the handheld/teacher software, not its ROM, artwork or branding.

CASSim is a **simulator, not a hardware-level emulation**: it need not match TI output exactly, but must be close enough not to confuse students or teachers. CASSim is released under the Unlicense.

**Later scope.** After the Nspire simulator is complete (M0–M6), CASSim adds, in this order, a web-based Python and pseudocode environment, with translation between the two and a stepwise forwards-and-backwards trace table, that works standalone and as page types inside the simulators (Should), a device switcher with a Casio ClassPad profile (Could), and possibly an HP Prime profile (Would) (4.12). Requirements for M0–M6 are unchanged by this.

Out of scope: Geometry page; approved-exam-calculator status; TI, Casio and HP ROM/OS/firmware code, logos or artwork; loading `.tns` libraries (the `mm_`/`sm_`/`gm_` UDFs are ported natively instead); server-side accounts or sync.

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
| Device profile | The bundle that makes one calculator behave like itself: dialect, catalogue, display conventions, document/page model, keys, menus, skin and corpus. The TI-Nspire CX CAS is the first |
| Oracle | The reference implementation a profile's corpus is captured from: the TI simulator for the Nspire; the manufacturer's PC emulator for ClassPad and Prime [Q17, Q18] |
| Pseudocode | A structured, language-neutral notation for algorithms; CASSim implements one dialect [Q16] |
| Code view | The standalone Python/pseudocode environment, with no device skin |
| Trace table | A table recording variable values as a program runs: **vertical** (one row per executed line) or **horizontal** desk check (code down the side, one column per loop pass) |
| Syntax file | The user-editable data file that defines which spellings, optional tokens and block terminators the pseudocode parser accepts and which style the printer writes |

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
| Texas Instruments, Casio, HP | Trademark/IP boundary (no marks, artwork, ROM or firmware) |

---

## 2. Overall description

### 2.1 Product perspective
A self-contained web app: Flet UI (Flutter web, canvas rendered) over a pure-Python core (`src/cassim/core`) that never imports Flet. The engine runs in its own Pyodide worker so the UI stays responsive and evaluation can be cancelled by terminating that worker (decision 0005). Persistence is in the browser: the autosave and System Settings use localStorage (Flet `SharedPreferences`) and named files and larger data use IndexedDB (M7). Hosted as static files.

### 2.2 Product functions (summary)
Calculator page with TI syntax; Graphs and Table; Lists & Spreadsheet; Data & Statistics; Finance; Notes; Program Editor and TI-Basic; documents and Problems; three display modes (Computer, Tablet/demo, Handheld); offline use. From M7: a Python and pseudocode environment, standalone and as page types; later, as Could and Would: a device switcher with Casio ClassPad and HP Prime profiles.

### 2.3 Users and classes
1. **Student**: knows the handheld; wants identical keystrokes and results.
2. **Teacher presenting**: needs readable large display, optional keystroke display, fast recovery from mistakes.
3. **Teacher authoring**: builds documents, programs, Python scripts; shares files with students.
4. **Developer/maintainer**: runs corpus, adds commands.
5. **Student programmer** (from M7): writes and runs short Python or pseudocode programs, standalone or on a calculator page.
6. **Student or teacher on another CAS calculator** (from M8): wants the Casio or HP workflow rather than the Nspire's.

### 2.4 Operating environment
Evergreen desktop and mobile browsers. Primary: Chromebooks, Chrome, Safari. Secondary: Edge, Firefox. Python 3.14 / Pyodide 314.0.7. Static hosting on GitHub Pages or any other free or cheap static host, with correct MIME types (`.mjs`) and no server-side code. Share links must stay within typical URL limits (about 2,000 characters is safe across browsers). Dev: Windows 11, uv, Ruff, Ty, pytest, Hypothesis, Playwright.

### 2.5 Constraints
- C-1 Core is pure Python, fully typed, Ty strict; SymPy is touched only in `core/compat/sympy_adapter.py`.
- C-2 No TI, Casio or HP logos, artwork, ROM or firmware content. Product name is CASSim.
- C-3 TI syntax is parsed by a real tokenizer + Pratt parser, never regexes. The same holds for every other device dialect and for pseudocode.
- C-4 Canonical text is Unicode (`ⅇ ⅈ ᴇ π ∞ ᵀ ʳ ᵍ ° ∠ ▶`); ASCII is an input/REPL spelling only. These conventions are fixed.
- C-5 Statistics follow the TI/school convention (quartiles as medians of halves; `sx` uses n-1, `σx` uses n); `numpy.percentile` is not used.
- C-6 The Flet static build needs a post-publish step (vendor wheels, patch `index.html`) for offline use (decision 0002).
- C-7 Must not auto-run user Python or pseudocode from a loaded document, import or link.
- C-8 The symbol and statistics conventions in C-4 and C-5 belong to the Nspire profile. Other profiles take theirs from their own oracle and must not change the Nspire's.
- C-9 Introducing device profiles must not change any Nspire behaviour (FR-PROF-002).

### 2.6 Assumptions and dependencies
Pyodide continues to bundle SymPy and SciPy at compatible versions; Flet static publishing remains viable (fallback: thin custom web front-end over the same engine); simulator access remains available for corpus capture; LazyMath stays Unlicense (to be recorded in a decision before porting). For M8/M9: the manufacturers' PC emulator software for ClassPad and Prime stays available and its terms allow corpus capture [Q17, Q18].

---

## 3. Fidelity and correctness model

This cross-cuts every functional area.

- **FID-1** (M, T) Correctness is judged by canonical equality against the simulator corpus, not by TI's exact output text. Maths is rendered from LaTeX/layout tree.
- **FID-2** (S, T) Output must be close enough not to confuse a student or teacher used to the handheld: same mathematical content, familiar form (e.g. `x=-2 or x=2`, fractions stay exact in Auto mode). Exact text match is not required. Where the corpus marks an area `compare: exact` (typically number display and simple forms), the text matches the simulator.
- **FID-3** (M, T) Every claimed behaviour has at least one corpus case with provenance (`simulator` or `hand-verified`) and evidence where simulator-captured. No behaviour change ships without a test.
- **FID-4** (M, T) Known divergences are `xfail(strict=True)` with a reason, so fixing one forces removing the marker.
- **FID-5** (M, T) Documented simulator behaviours are matched (TESTING.md section 14), including: Approximate mode shows decimals inside symbolic results; Float 3/Fix 2 switch to `ᴇ` notation for extreme values; `1/0` and `ln(0)` give `undef`; undefined variables echo unchanged; `int(-2.5) = -3`; `sinh⁻¹(1)` is unevaluated in Auto mode.
- **FID-6** (S, T) TI-specific solution forms are reproduced: general solutions with `@n1` constants, `cSolve`, `x=-2 or x=2`, domain constraints via `|`.
- **FID-7** (S, T) Each device profile has its own oracle and corpus (`corpus/<device>/`), and FID-1 to FID-4 apply to it unchanged. The behaviours listed in FID-5 and FID-6 are the Nspire's. Python semantics are CPython's (Pyodide); pseudocode semantics are the chosen dialect's written specification, pinned by golden programs (FR-RUN-006).

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
| FR-CALC-004 | Input is a structured 2D template editor, as on the handheld: a typed `/` stays linear and is stacked after Return; the fraction template (palette, ctrl+/ on a computer keyboard, ctrl+÷ on the handheld keypad) takes the preceding term, `^` and `√` open a slot, Right and Tab leave or move between slots, Backspace highlights a template then deletes it (decisions 0015 and 0017). The handheld's editing shortcuts (Tab and shift+Tab between fields, shift+arrows to select, shift+plus and shift+minus for the derivative and integral templates, ctrl+1 to ctrl+9 for jumps) are listed in `references/TI-Nspire CX II Family Shortcuts 2026.pdf`; each one CASSim supports is to be recorded in a shortcut table in `docs/design/`. Matrices and lists as templates follow. | M | D |
| FR-CALC-005 | Templates palette, Catalog, variable menu, copy/paste of inputs and results, up-arrow recall/edit of history. | M | D |
| FR-CALC-006 | Undo/redo of edits and of deleted history. | S | T |
| FR-CALC-007 | Warning triangle: an entry that completes with a caution shows a yellow triangle beside it, and hovering it (or tapping it on a touch screen) shows the message. It is a shared component, not calculator-only: the device also uses it elsewhere (for example Graphs and Lists & Spreadsheet). First use: Real mode `√(-1)·√(-1)` and `real(3+4·√(-1))` give a value with the warning "Non-real calculation" (decision 0026, `docs/testing/emulator-domain-results.md`). Needs a `warnings` field on the engine result, so it reaches the UI through the worker. | S | D/T |

### 4.4 Documents, Problems and pages — M2
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-DOC-001 | Multiple documents; add/delete/reorder Problems and Pages; page sorter. | M | D |
| FR-DOC-002 | Document and system settings dialogs. | M | D |
| FR-DOC-003 | Autosave to browser storage; recover after reload or crash. As built in M2e it uses localStorage through Flet `SharedPreferences` (enough for a document); IndexedDB is reserved for named files (FR-EDT-002) and larger data. | M | E |
| FR-DOC-004 | Export/import native plain-text `.cassim.json` with a versioned schema and migrations. | M | T |
| FR-DOC-007 | Share a document as a URL: the document is compressed and encoded into the URL fragment (so nothing reaches any server); opening the link loads it after a confirmation. Documents too large for a link fall back to file export. | S | T/E |
| FR-DOC-005 | Page types in scope: Calculator, Graphs, Lists & Spreadsheet, Data & Statistics, Notes, Program Editor, Python; Pseudocode is added in M7 (FR-RUN-010). Geometry excluded. | M | I |
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
| FR-PY-001 | A `py("script","fn",args)` call from the CAS and a small `cassim` API (read/write Problem variables, evaluate TI expressions). **Changed 2026-11-02:** the Python page itself is FR-RUN-010 (M7); this bridge is a later extra, not part of M7, and not something the handheld does (see FR-RUN-011). | C (later, after M7) | T |
| FR-PY-002 | If Python pages are built (FR-RUN-010): scripts run sandboxed in the browser; the user is prompted before any run; scripts in loaded documents or shared links never auto-run. | M (conditional) | T/E |
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
| FR-DEV-007 | Framework code in `device/` and `cassim.app` holds no Nspire-specific constants: key layers, menu trees, page types, skin and theme values come from data or registries supplied by the (Nspire) profile, and page types are registered rather than hard-coded. This is the M2 guard for FR-PROF-001 and adds no features. | S | I |
| FR-DEV-008 | **Menus follow the device.** The Calculator Menu and the Doc menu, the trig, templates, relations, punctuation and symbol grids and the Catalog keep the device's order and numbering (decision 0022), so keystroke habits transfer. An item CASSim cannot do yet is shown greyed as a placeholder, never omitted, and does nothing. Every item is also reachable by mouse and touch. | S | T/D |
| FR-DEV-009 | The multi-argument commands (distributions, statistics, regressions, Finance Solver, derivative at a point, matrices, systems, polynomial roots) have data-driven dialogs that paste or run as on the device (decision 0022). | S | T/D |
| FR-DEV-010 | System Settings are persisted per browser (start view, maths size, keypad letters ABC or QWERTY) and apply to every mode. | C | T |

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

### 4.12 Multi-device profiles and programming environments — M7–M9
Starts only when the Nspire simulator (M0–M6) is complete; nothing here reorders or blocks M0–M6 except the M2 guard FR-DEV-007. **Priorities confirmed 2026-11-02:** Python and pseudocode (Code view and page types) are Should; the ClassPad and the profile infrastructure that exists to serve it are Could; HP Prime is Would (not planned). Order: Code first, then ClassPad, then possibly HP. Question numbers refer to section 10. FR-PY-002 (the trust prompt) applies to every Python and pseudocode page built here, and the Python page itself is FR-RUN-010 (moved from M5 to M7).

**Device profiles (M8)**
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-PROF-001 | Device-specific behaviour (input dialect, command catalogue and its behaviour differences, display conventions, settings and presets, document/page model, key layers, menu tree, keymap and skin, error table, corpus) is packaged as a **device profile**; common maths-engine pieces stay shared. | C | I |
| FR-PROF-002 | The TI-Nspire CX CAS is the first profile. Moving it onto the profile interface changes no behaviour: the full Nspire corpus replays unchanged and the coverage targets in NFR-MAINT-004 still hold. | M (conditional on FR-PROF-001) | T |
| FR-PROF-003 | The app switches between profiles at run time from a visible switcher, and remembers the active profile. | C | E |
| FR-PROF-004 | Each profile has its own documents, settings and theme namespace in browser storage; switching never mixes or overwrites another profile's data. Sharing data between profiles is not required [Q20]. | C | T |
| FR-PROF-005 | Profile assets (grammar tables, catalogue data, skins) load lazily and are cached for offline use on first use, so a user who only opens the Nspire profile does not download the others. Cold start and download size (NFR-PERF-001, -005) are reported per profile. | C | A |
| FR-PROF-006 | Each profile declares its page/app types. Page types are registered, not hard-coded, so a type (Python, Pseudocode) can be offered by any profile that opts in [Q22]. | S | I |
| FR-PROF-007 | The display modes in 4.9 apply to every profile; Handheld mode uses the profile's own layout and artwork. A profile may need a touch-first interaction model [Q19]. | C | D |

**Python and pseudocode runtime (M7)**
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-RUN-001 | A language-neutral `Interpreter` interface: run source against an I/O context, stream output, accept input, report errors with line and column, and cancel. Python and pseudocode implement it, and so does the Nspire Python page (FR-RUN-010). | S | I/T |
| FR-RUN-002 | Python runs on CPython in Pyodide in a dedicated worker, separate from the CAS engine. Cancel terminates that worker within 1 s (NFR-PERF-004) and leaves CAS state intact. | S | T/E |
| FR-RUN-003 | Python environment: the standard library plus only the libraries that are needed (SymPy is shipped for the CAS; numpy and scipy are not assumed); plotting options are decided by a spike (Q21). User code has no network access and no access to the host page. How this is enforced is settled by a spike before the build; any gap that cannot be closed is documented in the SDD and shown in the trust prompt. | S | T/E |
| FR-RUN-004 | The prompt-before-run rule of FR-PY-002 applies to pseudocode as well as Python; code from documents, imports or links never auto-runs (C-7, NFR-SEC-002). | M (conditional) | T/E |
| FR-RUN-005 | **Pseudocode** interpreter: own tokenizer, parser and interpreter (no regexes, no translation by string substitution) implementing the dialect in `docs/pseudocode/dialect.md` (VCAA pseudocode as extended by the author's conventions document); errors reported in pseudocode terms, not Python tracebacks; an execution-step limit that stops runaway programs with a clear message. | S | T |
| FR-RUN-006 | The golden programs in `corpus/pseudocode/seed.yaml` (VCAA and the author's examples, each with a reference Python translation and an expected output) are replayed in CI; known failures are `xfail(strict=True)` as for the CAS corpus (FID-3, FID-4). | S | T |
| FR-RUN-007 | Step-through or trace of a pseudocode run, with a variables panel, for teaching: specified in full by FR-TRC-001 to -008. | S | D |
| FR-RUN-008 | A shared editor and console component: line numbers, indentation, error highlighting, Run/Stop, adjustable text size, keyboard-only operation, usable at 360 px width; the settings bar of FR-SET-001 sits at the top of it. | S | D |
| FR-RUN-009 | **Code view**: standalone mode with no device skin, reachable from the start screen without the profile switcher (FR-PROF-003); files, undo and download as in FR-EDT-001 to FR-EDT-004; imported files never auto-run. The Code view is a mode inside the one app, not a separate installable entry point (Q23, decided 2026-11-04). | S | E |
| FR-RUN-010 | **Page types**: Python and Pseudocode pages can be added to a document in the Nspire profile (FR-DOC-005). Adding them bumps the document schema version with a migration (FR-DOC-004). | S | T |
| FR-RUN-011 | A script on a Python or Pseudocode page can read and write the Problem's variables and evaluate TI expressions through the `cassim` API of FR-PY-001, by name and without evaluating strings outside the engine's parser (NFR-SEC-004). The real TI-Nspire does not allow this, so it is a CASSim extension, scheduled after M7 and only if wanted. Until then the pages are self-contained. | C (later, after M7) | T |
| FR-RUN-012 | A **Stop** button is visible whenever code is running and stops the run within 1 s (NFR-PERF-004), keeping the output and trace so far. It works for pseudocode and Python and does not depend on the run limits of FR-SET-009. | S | T/E |

**Pseudocode language (M7)** — dialect in `docs/pseudocode/dialect.md`
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-PSE-001 | Data: integer, rational, real, complex and basic strings; booleans only as comparison results; function values as arguments; lists (FR-PSE-006). Tuples, sets and dictionaries are Could (FR-PSE-008) and until then produce a "not supported yet" diagnostic naming the construct. | S | T |
| FR-PSE-002 | Function parameters written `f(x)`; an argument may be an expression in that variable or the name of a defined function. **Both forms are required** (2026-11-04): the expression form `trapezium(f(x), x, a, b, n)` called with an expression and its variable, and the first-class form `trapezium(f, a, b, n)` with `f` defined first. Corpus and examples never use `lambda`. **Binding rule (Q40, decided 2026-11-04):** `f(x)` in the header declares `f` an expression in the variable named by the next parameter; the call's variable argument must name the variable the expression uses (a mismatch is an error naming both); inside the function `f(t)` evaluates the expression with that variable set to `t`; assigning to `x` inside the function is local. | S | T |
| FR-PSE-003 | Tolerant input, defined by the syntax file (FR-SYN-001): the default accepts case-insensitive keywords; `end` keywords decide structure while indentation is advisory; optional `then`, `do` and closing `end`; `=` or `<-` for assignment (with a warning); juxtaposed print items (with a warning); Unicode and ASCII operator spellings. Warnings never stop a run. | S | T |
| FR-PSE-004 | Diagnostics in pseudocode terms with line numbers, including a close-name suggestion for an undefined variable. | S | T |
| FR-PSE-005 | Built-ins: abs, sqrt, exp, loge, trigonometric functions honouring the angle setting, rounding, and seeded random functions. | S | T |
| FR-PSE-006 | Lists in pseudocode: literals `[1, 2, 3]`, `[]`, indexing `a[i]` and assignment to an element, `len(a)`, `Append x to a` / `append`, `Sum a`, `for each x in a`, and nested lists of numbers or strings (for tables and tallies). The index base is **1 by default** with a … menu toggle to 0, saved with the program (decided). Translation to Python adjusts indexing. | S | T |
| FR-PSE-007 | Random numbers: `rand()` (uniform on [0, 1)), `randint(a, b)` (inclusive) and `seed(n)`, as in the author's materials. A seed makes a run, its trace and its tests repeatable. Seeded runs reproduce CPython's `random` module exactly (MT19937 with CPython's seeding, `random()` and `randint`/`randrange` algorithms; decided), so seeded programs, including the author's `seed(42)` examples, have exact golden outputs; unseeded programs are tested by properties. A test compares the runtime against CPython for many seeds. | S | T |
| FR-PSE-008 | Could: sets and set builders (`{factors of c}`, `for each m ∈ A`, union, intersection, difference, power set), dictionaries, tuples and tuple return (VCAA `maximum_SA`), `∑` and derivative notation `x'(t)`, and printing of pairs `(t, x)`. | C | T |
| FR-PSE-009 | Could: random distributions beyond `rand` and `randint` (e.g. `rand_norm`), and Counter-style tallies. | C | T |
| FR-PSE-010 | Could: structured-English steps (prose pseudocode such as the middle-square description) can be written in a program; they are shown in the code pane and trace as comments and are never executed. | C | I |
| FR-PSE-011 | **Complex literals**: `1+2i`, `1+2ⅈ` and `complex(1,2)` are accepted (Q28, decided 2026-11-04). The Real/Complex domain is a setting in the … menu (FR-SET-003), Real by default. | S | T |
| FR-PSE-012 | **Symbolic (exact) pseudocode**, promoted from Could to Should on 2026-11-07: the Number mode control (FR-SET-001) works as on the CAS. **Approx** is numeric as now. **Exact** keeps `π`, `ⅇ`, surds, fractions and index forms unevaluated (`√2`, `π/6`, `2^(1/3)`, `3/4`), so `sqrt`, `exp`, `loge`, trigonometry of exact angles and the constants go through the engine (SymPy only inside `core/compat/sympy_adapter.py`) and stay exact through `+ − × ÷` and powers. **Auto** is exact when every input is exact and numeric as soon as a decimal enters (`0.5`, `rand()`, a float). Exact values show in trace cells, in `print` and in the translated Python's comment (the Python itself uses `sympy` when a program needs exact mode). Pure-integer programs are unchanged: `÷` of integers stays a real in Approx and a fraction in Exact and Auto, so Exact and Auto change `7/2` from `3.5` to `7/2`. Loop and `if` tests compare numerically. The default stays Approx in the standalone Code view, so every golden program is unchanged; Exact variants get their own corpus cases. | S | T |

**Translation between Python and pseudocode (M7)**
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-XLT-001 | Pseudocode to Python for the whole dialect, following the author's translation table (assignment, input, print, define/def, if/elif/else, while, for with step, repeat n times, repeat-until as `while True` with a break). Current settings are honoured (`Fraction` in Auto and Exact modes, `radians()` wrapping in Degree mode); `input` becomes a generated `read_value()` helper that infers number or string. Python to pseudocode is written in the style of the syntax file's emit section (FR-SYN-005). The Python is readable and idiomatic. | S | T |
| FR-XLT-002 | Python to pseudocode for the subset that has a pseudocode form: assignment, if/elif/else, while, for over `range`, functions, print, input, and `while True` with an `if c: break` as repeat-until; strings limited to concatenation, comparison and length (Q31, decided 2026-11-04). | S | T |
| FR-XLT-003 | Python outside that subset is refused with the line and construct named; the translator never guesses. | S | T |
| FR-XLT-004 | Semantic equivalence: for every golden program, the pseudocode run by CASSim's interpreter and the translated Python run by CPython agree (differential test; reals compared numerically, integers and strings exactly). | S | T |
| FR-XLT-005 | Round trip: pseudocode to Python to pseudocode gives an equal program tree (comments and layout aside), property-tested on generated programs. | S | T |
| FR-XLT-006 | Names that clash with Python built-ins or keywords (`sum`, `list`, `lambda`, ...) are renamed in the translation, with a comment. | S | T |

**Stepwise trace tables (M7)** — layouts in `docs/pseudocode/trace-tables.md`
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-TRC-001 | Any run (pseudocode, or Python in the supported subset) records its events so the user can step forwards and backwards, return to the start, run to the end and jump to any row, without re-executing (random numbers and input replay identically). | S | T/E |
| FR-TRC-002 | **Vertical** layout: one row per executed line; columns for line number, variables (a value shown on the row where it changes), evaluated conditions, and calculations/output; repeated lines repeat their numbers. | S | T/D |
| FR-TRC-003 | **Horizontal** desk-check layout: the code down the left, an Init column then one column per loop pass, values substituted, ✔/❌ for conditions, "(skip)" for branches not taken, final output in the last column. Offered when the run has exactly one loop and no nesting. | S | T/D |
| FR-TRC-004 | Layout choice: Auto (horizontal when eligible, otherwise vertical) with a manual switch; switching never re-runs and keeps the cursor. | S | T |
| FR-TRC-005 | The run limits of FR-SET-009 (visible, adjustable maximum loop iterations and recursion depth) stop infinite loops; the recorded trace stays steppable and ends in a "stopped after N steps" row. Memory use of the record is bounded and the cap is shown. | S | T |
| FR-TRC-006 | The code pane highlights the current line; a variables panel shows all variables at the cursor; rows after the cursor are hidden until reached, with "show all". | S | D |
| FR-TRC-007 | The same trace engine serves Python in the supported subset (through the shared program tree), so Python and pseudocode give the same table for a translated program. | S | T |
| FR-TRC-008 | Trace cell values follow the settings (Exact/Approx, angle, display digits). | S | T |
| FR-TRC-009 | Fill-in mode: a blank table the student completes, with per-cell checking against the recording. | C | D |
| FR-TRC-010 | Export a trace as CSV, Markdown or an image. | C | D |
| FR-TRC-011 | A third, per-iteration view (one row per loop pass, variables as columns), after the vertical and horizontal views are done (Q33, decided 2026-11-04). | C | D |
| FR-TRC-012 | Line-by-line variable trace for Python outside the supported subset. | C | D |

**Settings bar (M7)**
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-SET-001 | The Code view's editor has a clear settings bar at the top with two controls, **Number mode** (Approx / Auto / Exact) and **Angle** (Radian / Degree), plus a **…** menu that holds every other setting (FR-SET-003, FR-SET-006, FR-SYN-003). The controls are always visible, show the current state, and are saved with the program. | S | D |
| FR-SET-002 | The settings apply to pseudocode runs, traces and translation (dialect.md section 8). A Python run executed directly by CPython cannot honour them: the affected toggles are shown disabled with the reason, never silently ignored. | S | T/D |
| FR-SET-003 | Further settings, in the **…** menu, each Could: Real/Complex domain (Real by default, so `sqrt(-4)` is an error; Complex gives `2ⅈ`), Gradian, random seed. (The step limit is now FR-SET-009.) | C | T |
| FR-SET-004 | On a Nspire Python or Pseudocode page the bar starts from the document's settings (FR-EVAL-002) and can be overridden for that page. | S | T |
| FR-SET-005 | VCE course presets (General, Methods, Specialist; FR-EVAL-003) as a one-click preset on the bar. | C | T |
| FR-SET-006 | Printed real numbers show **6 significant digits** by default (Mathematica style; trailing zeros dropped), adjustable in the … menu (Fix n, Full). Integers and rationals always print exactly. The display never changes the stored value. It applies to pseudocode output and trace cells; a Python run by CPython prints natively. A real with a whole value prints with a trailing point (`5.`), as in Mathematica, so it differs from the integer `5`; this is display only. | S | T |
| FR-SET-007 | **Print ends the line** by default. The … menu (and the syntax file, `print.end`) can change what `print` appends after its output: new line (default), a space, or nothing. The setting applies to the whole program; it cannot express the author's book convention (one `print` of a string followed by a second `print` joined onto the same line), which should be written as a single `print`. Saved with the program. | S | T |
| FR-SET-008 | **Euler's number toggle** in the … menu: when on, an unassigned `e` is the constant 2.71828… (and `e^x` reads naturally); when off, `e` is an ordinary name. A variable the program assigns always shadows the constant either way, so `e ← 0.001` is safe. Saved with the program alongside the number mode and angle. **Default: on** (decided 2026-11-06, revising Q39). | S | T |
| FR-SET-009 | **Run limits** in the … menu, low by default and user-adjustable: a maximum number of passes for any one loop run and a maximum recursion depth. Reaching either stops the run with a clear message naming the limit, the line and the setting to change it, keeps the output so far, and leaves the trace steppable (FR-TRC-005). Applies to pseudocode and, where CPython allows, to Python runs. **Defaults: 1,000 passes per loop, 20,000 recorded trace steps and recursion depth 100** (decided 2026-11-06, revising Q39). | S | T |

**Configurable syntax (M7)** — default in `docs/pseudocode/syntax-default.yaml`
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-SYN-001 | The pseudocode syntax is defined by a **syntax file**, not hard-coded: keyword and symbol spellings, which tokens are optional, how each block may end, comment markers, and the style the printer writes. The built-in default accepts every spelling in `docs/pseudocode/dialect.md`. | S | T |
| FR-SYN-002 | The same construct can be written several ways, and each spelling can be set to accepted, accepted with a warning, or rejected. Must work: `if` with `then` required, optional or forbidden; a `for` loop ending with `end for`, `endfor` or `next` (with or without the variable); a function ending with `end`, `end define`, `end function` or a dedent. | S | T |
| FR-SYN-003 | The file is stored in browser storage per profile, editable in the app (… menu, Syntax) with validation, a live check against a sample program, reset to default, and export/import as a file. An invalid file falls back to the default with a message (as FR-THEME-002). | S | T/D |
| FR-SYN-004 | Validation rejects files that make the grammar ambiguous or contradictory: one spelling mapped to two constructs, a bare `end` accepted for several constructs without the innermost-block rule, no spelling left for a required construct. A new reserved word that collides with a name in the user's saved programs is reported. The message names the entry at fault. | S | T |
| FR-SYN-005 | The file's **emit** section controls what the printer writes (Python to pseudocode, formatting, examples): keyword case (lower, UPPER, Capitalised), indent width, terminator spellings, whether `then` and `do` are written, the assignment, multiplication and division symbols, and the comment marker. | S | T |
| FR-SYN-006 | Code is displayed exactly as the user typed it; the code pane and trace tables refer to the user's own lines and never show a normalised reprint. | S | T/D |
| FR-SYN-007 | Property tests: for every built-in preset and for generated valid syntax files, printing a program tree in that file's style and parsing it again gives the same tree; every golden program survives restyling under every built-in preset. | S | T |
| FR-SYN-008 | Built-in presets: Default (tolerant), VCAA, the author's conventions, and Strict (one spelling per construct, warnings become errors). A user's file starts as a copy of a preset. | C | D |
| FR-SYN-009 | The file is data only (no code, no regular-expression hooks), schema-validated and size-limited on import (NFR-SEC-003). A program shared by file or link may carry its non-default syntax settings; opening it asks first and never changes the viewer's own file (decided 2026-11-02). | S | T |
| FR-SYN-010 | **Regularise** button in the editor toolbar. It takes a program whose syntax is unambiguous under the current syntax file but not in the standard style (for example `=` for assignment, keyword case, `endfor` or `next` instead of `end for`, a missing `then`, `define` versus `function`, juxtaposed print items, an unclosed inner block that an outer closer ends) and rewrites it in the standard in use: the emit section of the syntax file (FR-SYN-005) or a preset chosen in the button's menu. It shows a before/after diff and applies on confirmation as a single undo step (FR-EDT-001). Comments, blank lines and meaning are preserved. It refuses, with the reason and line, when the program is ambiguous or has errors, and never guesses. Tests: the program tree is unchanged by regularising; regularising twice changes nothing; property-tested across every preset and generated syntax files; every golden program, deliberately mis-styled, regularises to its canonical form. Python programs use the same button to apply a consistent layout (indentation, spacing) without changing the tree. | S | T |
| FR-SYN-011 | **Symbol equivalents.** Wherever the language has a mathematical symbol, the ASCII spelling and the Unicode symbol are interchangeable on input, in any mix, each marked ok, warn or no in the syntax file. The default table: `<-` `:=` `←`; `*` `×` `·`; `/` `÷`; `<=` `≤`; `>=` `≥`; `!=` `<>` `≠`; `sqrt(x)` `√(x)` `√x`; `pi` `π`; `inf` `∞`; `abs(x)` `|x|`; `x^2` `x**2` `x²` (integer exponents of the form `^n`, `^-n` and `⁻ⁿ` superscripts); `and` `∧`; `or` `∨`; `not` `¬`; `-` `−` `–`; `ln` `loge`. Strings and comments are never reinterpreted. | S | T |
| FR-SYN-012 | **Convert symbols** button (toggle) in the editor toolbar: rewrites the selection, or the whole program, to Unicode symbols or to ASCII, and a second press converts back. It works on tokens from the tokenizer, never by text search, so strings, comments and names are untouched; a user variable that happens to be called `pi` is left alone and reported. It previews the change as a diff, applies as one undo step (FR-EDT-001), keeps the program tree unchanged, and is idempotent (property-tested: ASCII to Unicode to ASCII returns the original for programs written in the standard ASCII spellings). The target style also feeds Regularise (FR-SYN-010) and the printer's emit section as `symbols: unicode | ascii | keep` (FR-SYN-005). Superscript conversion applies only to integer-literal exponents; `x^(n+1)` stays as typed. | S | T |
| FR-SYN-013 | Typing aid (setting, off by default): as the user types, unambiguous multi-character ASCII sequences become symbols (`<-` to `←`, `<=` to `≤`, `>=` to `≥`, `!=` to `≠`) and a LaTeX-style `\pi`, `\sqrt`, `\le`, `\ge`, `\theta` followed by space or Tab becomes its symbol. Plain words such as `pi` or `sqrt` are never auto-replaced while typing (they may be names); that is what FR-SYN-012 is for. Each replacement is undoable on its own. | C | T |

**Code editor: undo, files, download (M7)** — applies to the shared editor (FR-RUN-008) in the Code view and on Nspire Python and Pseudocode pages
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-EDT-001 | **Unlimited undo and redo** per file: no fixed depth, Ctrl/Cmd+Z, Shift+Ctrl/Cmd+Z and Ctrl+Y, plus toolbar buttons. History is stored compactly (as diffs, with typing coalesced into word-sized steps) and Regularise, Translate, paste, Open and Revert each form one step. Undo never touches output or trace results, which are marked stale instead. The history survives reload and crash where storage allows, is kept per file, and is trimmed oldest-first only when the storage quota is reached, with a visible message and never silently. | S | T/D |
| FR-EDT-002 | **Save to browser storage**: named files in IndexedDB, available in the Code view and from Python and Pseudocode pages: list, open, new, save, save as, rename, duplicate and delete (with confirmation). Unsaved edits autosave as a draft and are recovered after reload or crash (FR-DOC-003). Each file records its language, its list index base and any non-default syntax or settings overrides (FR-SYN-009). A quota warning is shown before saves fail, with a link to export everything. | S | T/D |
| FR-EDT-003 | **Download and upload**: download the current file, or all files as one archive, as plain text with the extension `.py` for Python and `.pseudo.txt` for pseudocode (decided 2026-11-02; opens in any text editor, and the app also accepts `.pseudo` and `.txt` on upload); uploading or dropping a file adds it to the list. The header carrying settings and syntax overrides is a comment block so the file still reads, and runs as Python, elsewhere. Downloads work offline and use the platform's save mechanism, with a fallback on browsers lacking one. | S | T/D |
| FR-EDT-004 | Uploaded or imported files, and files arriving in a shared document or link, are opened but never run until the user chooses Run (FR-RUN-004, C-7, NFR-SEC-002). Overrides in the header are shown and need acceptance (FR-SYN-009). File size and name length are limited and names are sanitised. | S | T |
| FR-EDT-005 | Undo history and files are exported and restored with the rest of the user's data (FR-DOC-004 backup), so clearing the browser is recoverable from a backup file. | C | T |
| FR-EDT-006 | **Symbol palette**: a button opens a panel of tappable symbols that insert at the cursor (or wrap the selection), so students on a phone or a plain keyboard can enter them. Groups: arithmetic and relations (`× ÷ ± ≤ ≥ ≠ ← ≈`), powers and roots (`² ³ ⁿ ⁻¹ √ ^ π e ∞`), logic (`∧ ∨ ¬`), bars and brackets (`|x| ( ) [ ]`), Greek letters (`θ α β` and so on), a Recently used row, and keyword templates (`if`, `for`, `while`, `repeat`, `define`) that insert a block in the user's own syntax style. Each button shows its ASCII equivalent and keyboard shortcut on hover or long press. The contents come from the syntax file (only symbols the current syntax accepts are shown). Keyboard operable, at least 44 px targets, usable at 360 px, and a Python editor gets an ASCII-only variant (`**`, `//`, `%`, `!=`, `<=`). | S | T/D |

**Casio ClassPad (M8)**
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-CPD-001 | A ClassPad profile with its own dialect, catalogue (Tier 1 VCE core first, tiers as in FR-CAT-001 to -003), settings presets, display conventions and error table, each pinned by a corpus captured from the oracle [Q17]. Nothing is inherited from the Nspire profile unless the corpus confirms it. | C | T |
| FR-CPD-002 | The corpus lives in `corpus/classpad/` with the same provenance, status and `xfail(strict=True)` rules as FID-3 and FID-4; Tier 1 passes (canonical) before any exact-text work. | C | T |
| FR-CPD-003 | App/page set as the oracle shows it (calculation, graph and table, statistics, spreadsheet) [TBC], reusing the shared sheet, stats and graph engines through the profile. Geometry is excluded. | C | T/D |
| FR-CPD-004 | Handheld skin and keypad (or touch interface, per Q19) in CASSim's own artwork. | C | D |
| FR-CPD-005 | VCE setting presets for Methods, Specialist and General, and scripted exam-style flows, as for the Nspire. | C | T/E |

**HP Prime (M9, optional)**
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-HPP-001 | A go/no-go review after M8 against oracle availability and terms [Q18], the actual effort of M8, and demand. Nothing else in this specification depends on a "go". | W | I |
| FR-HPP-002 | If go: an HP Prime profile built by the same recipe as FR-CPD-001 to -005, with its programming language handled as a separate dialect on the FR-RUN-001 interface if wanted. | W | T |

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
- NFR-SEC-002 (M) User Python and pseudocode run in the browser sandbox with a trust prompt; imported documents and share links never auto-run code (Python, pseudocode or programs).
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
- NFR-PORT-004 (W) Native builds of the same app with `flet build`: Windows, macOS and Linux desktop, and Android (APK, AAB) and iOS. The static web site is the only release target until M6 is done; see PLAN.md section 13 for what each build needs.

### 5.6 Maintainability and quality
- NFR-MAINT-001 (M) Ruff clean; Ty strict on `core/`; CI (lint, types, tests, web build, Playwright smoke) green before merge. CI runs on GitHub Actions and is green on `main`.
- NFR-MAINT-002 (M) Core never imports Flet (lint rule); SymPy only in the adapter.
- NFR-MAINT-003 (M) Conventional commits; small commits; decisions recorded in `docs/decisions/`.
- NFR-MAINT-004 (S) Line and branch coverage of at least 90% on `src/cassim/core/` and 80% on the other non-UI packages (`device`, `doc`, `sheet`, `stats`, `graph`). `cassim.app` (Flet UI) is excluded and covered by Playwright. CI fails when a package falls below its floor in `pyproject.toml` (`[tool.cassim.coverage]`, checked by `tools/coverage_check.py`). The floors started just below the figures of 2026-11-09 (core 96.9%, device 96.2%, profiles 98.1%, runtime 91.0%, cli 93.6%) and only rise. `sheet`, `stats` and `graph` have no code yet and get a floor when they do.
- NFR-MAINT-006 (M) Every requirement ID appears in at least one test (marker or docstring) or is listed as untested with a reason. A generated traceability table (`docs/traceability.md`) is checked in CI.
- NFR-MAINT-005 (S) Dependency versions pinned (uv lockfile); Pyodide upgrade procedure documented.

### 5.7 Legal and licensing
- NFR-LEG-001 (M) No TI marks, artwork, ROM content or screenshots shipped. Reference screenshots stay in `docs/design/reference/`, not the build.
- NFR-LEG-002 (M) A visible disclaimer: not affiliated with or endorsed by TI; not an approved exam calculator.
- NFR-LEG-003 (M) CASSim is released under the Unlicense. Third-party notices (Flet, Pyodide, SymPy BSD, SciPy BSD, and the vendored fonts) ship with the build.
- NFR-LEG-004 (S) Before porting LazyMath UDFs, record the licence check (LazyMath Unlicense) in `docs/decisions/`.
- NFR-LEG-005 (M) From M8, the disclaimer in NFR-LEG-002 also covers Casio and HP. No Casio or HP marks, artwork, ROM, firmware or emulator software is shipped; reference screenshots stay in `docs/design/reference/`.
- NFR-LEG-006 (C) Before capturing a corpus from a manufacturer's emulator software, record its licence terms and why they allow this use in `docs/decisions/` (as NFR-LEG-004 does for LazyMath).
- NFR-LEG-007 (M) Question text that is (c) VCAA (corpus cases marked `third_party: true`) stays in the private repository for development (decision 0012). VCAA's terms require permission for publication on a website, so before the repository or corpus is made public those cases are either cleared with VCAA or replaced by original programs. The corpus is never part of the app build, and each case keeps its attribution in `source`.

---

## 6. External interfaces
- **User interface**: three display modes (4.9); own-branded skin; reference screenshots in `docs/design/reference/`.
- **Files**: `.cassim.json` (versioned), CSV, optionally xlsx. `.tns` is deferred (FR-DOC-006).
- **Browser APIs**: IndexedDB, Service Worker, Web Workers, Clipboard, File System / download, fullscreen, Web App Manifest.
- **Software**: Pyodide 314.0.7, SymPy 1.14, SciPy 1.18, NumPy 2.4, mpmath, Flet 1.0.x; the 2D editor is CASSim's own template editor drawn from Flet controls (decisions 0015, 0018, 0019); MathLive and MathQuill are not used.
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
- **Acceptance gates** map to milestone exits in PLAN.md section 8: M1 Tier 1 corpus passes (canonical), strict types on `core/`, matrix published; M2 install on a phone and run scripted exam-style flows; M3 the General Maths workflows pass; M4 graph snapshots and performance budget; M7 the Python and pseudocode golden programs pass in both languages and agree (FR-XLT-004), the trace tables for the reference bisection example match the author's vertical and horizontal tables, all golden programs round-trip under each built-in syntax preset (FR-SYN-007), and cancel and trust-prompt E2E pass; M8 the Nspire corpus replays unchanged after the profile refactor and the ClassPad Tier 1 corpus passes (canonical); M9 as M8 if a go is given.

## 9. Requirement traceability
Each FR maps to: milestone (above), corpus tags (e.g. `solve`, `tier1`), tests, and design component (SDD section). A script in `tools/` generates `docs/traceability.md` from the requirement IDs in this file and the markers in tests and corpus tags (NFR-MAINT-006).

---

## 10. Open questions
Q1-Q15 are answered and folded into the text above. Q16-Q41 were added on 2026-11-02 and 2026-11-04 with the post-Nspire scope (4.12); none of them blocks M0-M6. New ones will be added as the design docs surface them.

| # | Question | Needed by |
|---|---|---|
| Q16 | ~~Which pseudocode dialect?~~ **Answered 2026-11-02:** the VCAA pseudocode as extended by the author's conventions document; specification in `docs/pseudocode/dialect.md`, numeric types and basic strings only. | done |
| Q17 | Which ClassPad model(s), and is the manufacturer's PC emulator the oracle? Do its licence terms allow corpus capture? | 8c |
| Q18 | The same for HP Prime (its PC emulator), plus the go/no-go criteria for M9. | 9a |
| Q19 | ClassPad interaction: reproduce stylus/touch operation (tap menus, soft keyboard), or approximate it with the key-driven device model? | 8f |
| Q20 | ~~State shared between profiles?~~ **Answered 2026-11-02:** completely separate environments. Each profile has its own documents, variables, files, settings and theme; nothing is shared or copied between profiles (FR-PROF-004). | done |
| Q21 | ~~Python environment contents~~ **Partly answered 2026-11-02:** import only the libraries that are needed; numpy and scipy are skipped unless something in M7 needs them (the engine's `src` imports neither today, so this also shrinks the download; measure in the 7a spike). **Graphing:** undecided; test the options in a spike first (Flet's own charts, the canvas used in spike 3, matplotlib as the heavy fallback), and prefer Flet's built-in plotting if it is good enough. Device-style modules such as `ti_system` and `ti_plotlib` are still open. | 7a |
| Q22 | Should Python and Pseudocode pages exist on the ClassPad and Prime profiles? Which real models have native Python (not checked), and how do scripts reach CAS variables there? | 8g |
| Q23 | ~~Code view: a mode or its own entry point?~~ **Answered 2026-11-04:** a mode inside the one app, reached from the start screen; one install, one start URL, shared storage and settings (FR-RUN-009). | done |
| Q24 | ~~Number modes~~ **Answered 2026-11-02:** yes, the TI "Auto" rule is added as a third number mode (Approx / Auto / Exact; `dialect.md` section 8). Default in the standalone Code view stays Approx (as proposed; say if you want otherwise). | done |
| Q25 | ~~Real display~~ **Answered 2026-11-02:** Mathematica style, 6 significant digits by default, adjustable in the … menu; applies to reals only (integers and rationals print exactly) and to pseudocode output and traces; Python run by CPython prints natively. | done |
| Q26 | ~~`print a, b` output format~~ **Answered 2026-11-04:** items separated by one space, as every expected output in the corpus shows; `print(a, b)` is the same statement with optional parentheses, not a pair, so it prints the same. | done |
| Q27 | ~~`input x` typing~~ **Answered 2026-11-02:** infer. Anything that can be a number (including a fraction) is a number, otherwise a string; revisit after real usage. | done |
| Q28 | ~~Complex numbers~~ **Answered 2026-11-04:** `1+2i`, `1+2ⅈ` and `complex(1,2)` are all accepted (FR-PSE-011); Real/Complex is a setting in the … menu, Real by default (FR-SET-003). | done |
| Q29 | ~~Are `e` and `π` predefined?~~ **Answered 2026-11-04:** `π` and `pi` are always the constant; `e` is Euler's number only when the toggle of FR-SET-008 is on (default on from 2026-11-06). A name the program assigns always shadows either. | done |
| Q30 | ~~Settings bar contents~~ **Answered 2026-11-02:** the bar has Number mode and Angle; everything else sits behind a **…** menu. | done |
| Q31 | ~~Python to pseudocode scope~~ **Answered 2026-11-04:** the subset with a pseudocode form, as listed in FR-XLT-002; anything else is refused with the line and construct named (FR-XLT-003). | done |
| Q32 | ~~VCAA question text~~ **Answered 2026-11-02:** accepted for development in the private repository; decision 0012 records VCAA's actual terms (website publication needs permission) and the condition before public release. | done |
| Q33 | ~~Per-iteration table as a third trace view~~ **Answered 2026-11-04:** a Could (FR-TRC-011), after the vertical and horizontal views. | done |
| Q34 | ~~Whole-valued reals~~ **Answered 2026-11-02:** copy Mathematica. A real with a whole value prints with a trailing point (`5.`), so reals and integers look different; integers and rationals never get one. Applies to the display only (FR-SET-006). | done |
| Q35 | ~~Syntax settings in shared programs~~ **Answered 2026-11-02:** yes. A shared program carries its non-default syntax settings; opening it asks first and never changes the viewer's own file (FR-SYN-009). | done |
| Q36 | ~~Does `print` end the line?~~ **Answered 2026-11-02:** yes by default, and changeable in the … menu (FR-SET-007) and the syntax file. The setting is all-or-nothing, so the book's linear-search example (two `print` statements shown as one line, split only to fit the page) is kept in the corpus as a single `print` (reviewed 2026-11-04); the two-print original was removed. | done |
| Q37 | ~~List index base~~ **Answered 2026-11-02:** 1-based by default (as the VCAA and the author's book), with a toggle in the … menu to switch to 0-based; the choice is saved with the program, and translation to Python adjusts indexing either way. | done |
| Q38 | ~~Match CPython's seeded random~~ **Answered 2026-11-02:** yes. The pseudocode runtime reproduces CPython's `random` module exactly for `seed(n)`, `rand()` and `randint(a, b)` (MT19937, same seeding and algorithms), so the author's seeded results can be golden tests. | done |
| Q39 | ~~Defaults for the run limits and the Euler toggle~~ **Answered 2026-11-04:** 10,000 loop iterations, recursion depth 100, `e` off (FR-SET-008, FR-SET-009). **Revised 2026-11-06:** 1,000 passes per loop, 20,000 trace steps, depth 100, `e` on. | done |
| Q40 | ~~How does the variable argument bind in the expression form?~~ **Answered 2026-11-04:** the name must match the variable the expression uses, `f(t)` evaluates the expression at `t`, assignments to the variable inside the function are local (FR-PSE-002). | done |
| Q41 | ~~Exact values in Auto and Exact modes~~ **Answered 2026-11-04, revised 2026-11-07:** first decided as not in the first release; Simon then made it a Should (FR-PSE-012), with the same Approx / Auto / Exact toggle as the CAS. | done |

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
| `SDD-09-programming-and-python.md` | TI-Basic, trust/sandbox model |
| `SDD-10-pwa-and-build.md` | Build pipeline, vendoring, service worker, deploy |
| `SDD-11-test-strategy.md` | Corpus, replay, device and E2E tests, CI |
| `SDD-12-device-profiles.md` | Profile interface, shared vs per-profile layers, storage namespaces, lazy loading, refactor plan for the Nspire |
| `SDD-13-runtime-python-pseudocode.md` | `Interpreter` interface, Python worker and sandbox, pseudocode dialect and interpreter, translation, trace engine and tables, settings bar, configurable syntax file, page-type integration (the variable bridge is a later Could) |

---

## Appendix B. Implementation status (2026-11-08)

A summary, not a substitute for the traceability table (`docs/traceability.md`, NFR-MAINT-006).

| Area | Requirements | Status |
|---|---|---|
| Language, evaluation, scope | 4.1 | Built (M1). |
| Command catalogue | 4.2 | Tier 1 built; Tier 2 per the matrix; FR-CAT-005 matrix published (`docs/command_matrix.md`). |
| Calculator page, device model | 4.3, 4.9 | Built through 2h; Tablet mode (FR-DEV-003) not started; typed-character capture on non-US layouts open (decision 0024). Exam-style flows pass headless and in the browser (decision 0025). |
| Documents, files, share links | 4.4 | Built (autosave, `.cassim.json`, share links, Page Sorter). Multiple documents in one session (FR-DOC-001) not checked. |
| PWA, offline, engine worker | 4.11, FR-EVAL-006 | Built and tested on Chromium; real GitHub Pages and Safari, iOS and Chromebook not yet run. |
| Lists & Spreadsheet, Data & Statistics, Finance page | 4.5, 4.6 | Engine commands exist; pages not started (M3). |
| Graphs and Table | 4.7 | Not started (M4). |
| TI-Basic, libraries | 4.8 | Not started (M5, Could). |
| Pseudocode runtime, trace tables, syntax file, printer | 4.12 (FR-RUN-005/006, FR-PSE, FR-TRC, FR-SYN-001 to 009) | Built (M7b), 58 golden programs green. Translation, editor, settings bar, Code view and page types not started. |
| Python runtime | FR-RUN-002/003 | Not started; the sandbox spike (7a) comes first. |
| Profiles, ClassPad, HP Prime | FR-PROF, FR-CPD, FR-HPP | Not started; only the M2 guard applies. |
| Non-functional | 5 | Traceability (`docs/traceability.md`), accessibility notes (`docs/accessibility.md`) and per-package coverage floors exist (2026-11-09). NFR-LEG-002 is in the About dialog; NFR-LEG-003 notices need checking against the shipped files before release. |
