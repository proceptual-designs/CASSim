# CASSim testing: the first bits

Status: draft 1 (2026-10-31). Covers what must exist before M1 coding starts: the golden corpus, how it is replayed, how comparison works, and how cases are captured from the real simulator. Companion files: `corpus/schema.json`, `corpus/validate.py`, `corpus/seed/001_core.yaml` (20 seed cases).

## Where the evidence is

The results files in this folder and the corpus cases are the written record: what was typed, what the simulator showed, and how CASSim compares. The screenshots they were transcribed from (`corpus/shots/`, `docs/testing/*-shots/` other than `app-shots/`), the capture briefs and run plans (`emulator-*-capture.md`, `*-brief.md`, `*-plan.md`, `*-remaining.md`) and `simulator-todo.md` are kept in the separate evidence repository at the same relative paths (decision 0039). Where a file here names one of those paths, it means the file in the evidence repository. `uv run python corpus/validate.py --check-evidence` checks the corpus screenshots when that repository is present.

## Development and pre-merge test selection

CI runs once per batch PR (AGENTS.md, "Development workflow"), so the complete checks run locally.
During development, run the narrowest test that can fail because of the change, then widen to the
affected boundary. Pre-commit runs Ruff and Ty only.

Before a feature branch merges into local `main`, run the same checks CI runs:

```powershell
uv run python -m tools.local_ci             # python and browser groups; records the pass
uv run python -m tools.local_ci --full-e2e  # also the whole browser suite, for cross-cutting work
uv run python -m tools.local_ci --status    # has HEAD's tree passed?
```

`tools.local_ci` holds the one list of browser tests CI runs; CI calls it for each job. The
pre-push hook (`uv run pre-commit install`) refuses a push whose tree has not passed. Only one
run goes at a time on the machine, from any worktree or clone: a second run waits on the lock
`%LOCALAPPDATA%\CASSim\local_ci.lock` and says which run holds it, because two at once make the
time-based tests fail. The holder's folder, process and start time are in `local_ci.holder`
beside it (Windows will not let another process read the locked file); the note is left behind
after a run and is harmless. On Linux and macOS the lock is in `$XDG_STATE_HOME/CASSim/`, or
`~/.local/state/CASSim/` when that is unset.

While working, also run `uv run pytest tests/flows/` and the affected test directories or files
from this map:

| Change | Focused tests | Add before a PR |
|---|---|---|
| `core/` maths, parser, formatting, settings | matching `tests/unit/` file | corpus replay, plus flows when the public Session behaviour changes |
| `device/` or a Nspire page model | matching `tests/device/` file | `tests/flows/` and the matching browser flow/page |
| `app/` or Nspire UI | matching `tests/app/` file | matching `tests/e2e/` file; all e2e for shared shell or startup work |
| `doc/`, autosave or storage | matching app/device document tests | autosave/reload e2e and relevant PWA/offline e2e |
| `sheet/`, `graph/` or `stats/` | matching unit and device tests | corresponding sheet/statistics browser test when rendering or controls change |
| `runtime/` | matching `tests/runtime/` file | browser coverage when the Code UI is involved |
| `devices/scientific/` (CASSim Scientific) | `tests/devices/scientific/` (keys, values, calc, stat, files, tutorials, layouts, ui; `test_scientific_ui.py` also lays the app out at four simulated phone sizes and checks the calculator and every dialog fit) | a manual browser check until an fx e2e test exists; Flet draws to a canvas, so overflow is tested in the layout tests, not the browser |
| publishing, PWA, worker or Pyodide | matching tool/unit tests | full e2e suite |

Run a single e2e file when the browser path is local, for example:

```powershell
uv run pytest -m e2e tests/e2e/test_sheet_browser.py
```

Run the complete browser suite for a cross-cutting change:

```powershell
uv run pytest -m e2e tests/e2e
```

Browser tests should share a startup only when their scenarios can safely share one state. Keep
fresh installs, broken caches/updates, online/offline transitions, root and sub-path hosting, and
touch-specific contexts in separate tests: that isolation is part of the behaviour under test.
When several features can be exercised in one flow, prefer a natural student task or VCE-style
problem rather than a synthetic sequence of controls. Enter data, carry results between pages,
analyse the maths, and check the answer in the same order a student would. Use short synthetic
steps only for behaviours that do not fit a meaningful problem, such as a cache-repair or
accessibility control.

## 1. Principles

- The TI-Nspire simulator is the oracle. SymPy is only the implementation.
- Correctness means **symbolic or numeric equivalence**, not identical text (decision: Simon, 2026-10-31).
- Every case records where its expectation came from. Only `simulator` provenance counts as verified.
- Known failures are tracked, not hidden: `xfail` with a reason, and a fixed case must have its marker removed.

## 2. Test layers (in order of when they appear)

| Layer | Appears | Notes |
|---|---|---|
| Corpus validation (`corpus/validate.py`) | now | schema + invariants, runs in CI with no engine |
| Unit tests: lexer, parser, printer | M1a | Hypothesis round-trip `parse(print(parse(s))) == parse(s)` |
| **Golden corpus replay** | M1b onward | section 4 |
| Device-model tests | M2a | key sequences to expected state (section 7) |
| Render snapshots, Playwright e2e, PWA offline | M2 | |

## 3. Corpus format

One or more YAML files under `corpus/`, validated by `corpus/schema.json` (JSON Schema 2020-12). A case is a short scripted session.

```yaml
- id: methods.define.solve-with-domain     # unique, lowercase, dot-separated: course.area.name
  course: methods                          # applies the document-settings preset (below)
  tier: 1                                  # 1 = VCE core, 2 = rest of Reference Guide, 3 = edge
  tags: [define, solve, constraint]
  steps:
    - {in: "f(x):=x^2-4", out: "Done"}
    - {in: "solve(f(x)=0,x)|x>0", out: "x=2"}
  provenance: {source: simulator, simulator_version: "...", captured: 2026-11-02,
               evidence: shots/methods.define.solve-with-domain.png}
  status: pass                             # pending | pass | xfail
```

**Step kinds:** `{in, out}` expects a result; `{in, error: true, error_contains?}` expects an error; `{new_problem: true}` inserts a fresh Problem (variables cleared); `{set: {...}}` changes document settings mid-case.

**Course presets** (from the cas-solver skill, Float 8, CAS on). A case's `settings:` overrides individual fields.

| course | angle | calc | domain |
|---|---|---|---|
| general | degree | approximate | real |
| methods | radian | auto | real |
| specialist | radian | auto | rectangular |
| none | engine defaults (radian / auto / real) | | |

**Provenance sources:** `simulator` (needs evidence screenshot, enforced by the validator) › `skill_notes` (from Simon's cas-solver skill; reported as verified there, to be re-captured) › `hand_computed` (derived independently, e.g. with SciPy) › `unverified_expectation` (from memory; treat as a hypothesis).

**YAML pitfall:** PyYAML reads `1e-9` as a string. Write tolerances as `1.0e-9` (the validator catches this).

**Status lifecycle:** `pending` (engine can't run it yet; replay skips it) → `pass` once the engine passes it → `xfail` + `xfail_reason` if it regresses or is a known gap. Replay marks `xfail` as `strict`, so an unexpected pass fails the run.

## 4. Replay harness (to build in M0/M1)

A single parametrised pytest module `tests/corpus/test_replay.py` that loads every case and runs it against the engine's public API. The harness depends only on this small contract, which the engine must provide:

```python
class Session:
    def __init__(self, settings: Settings) -> None: ...
    def eval(self, line: str) -> Result: ...  # one entry line, mutates Problem scope
    def new_problem(self) -> None: ...
    def set(self, **settings) -> None: ...


@dataclass(frozen=True)
class Result:
    text: str  # TI-style linear text
    latex: str  # for rendering
    value: Value  # typed value (for comparison)
    error: str | None  # error message, None on success
```

**Comparison modes** (per step, default `canonical`):

| compare | rule |
|---|---|
| `canonical` | parse expected `out` with our own parser, then check symbolic equality of the two values: expressions via `simplify(a-b)==0`; equations as sides moved to one side; `or`/`and` results compared as unordered sets of solutions; lists and matrices elementwise; `Done` and `Void` by text |
| `numeric` | relative tolerance `tol` (absolute near 0), elementwise for lists and matrices |
| `family` | solutions with arbitrary-integer constants (`@n1`): substitute n1 in a fixed range (e.g. -3..3), compare resulting solution sets within a window |
| `text` | exact string; only for errors and `Done` |
| `ignore` | run for side effects only |

Errors: `error: true` passes on any engine error; `error_contains` additionally checks the message. Exact TI error text is recorded when captured but is not enforced until the engine mirrors TI messages.

**Outputs:** a pass/xfail/pending summary by course, tier and tag so progress is visible per milestone. CI gates: validator clean; no regressions in `pass` cases; Tier 1 pass rate recorded in the release notes.

## 5. Capturing from the simulator

Use Simon's `vce-cas-solver` workflow (TI-Nspire CX CAS Premium Teacher Software, Handheld page size). For each case:

1. Open or reuse a document; set Document Settings for the course (section 3). Check the title bar shows DEG or RAD.
2. New Problem per case (`new_problem` steps insert another Problem inside the same case).
3. Enter each `in` line in short chunks (about 9 characters). Beware simulator typing quirks that are properties of the keyboard, not the CAS: `^` swallows everything after it as the exponent; a line starting with an operator gets `Ans` in front; ASCII `e` and `i` are plain variables (use `e^(...)` template, `exp()`, `√(-1)`).
4. Screenshot the result region (about 455x303 px) and save as `corpus/shots/<case-id>[-<step>].png` in the evidence repository.
5. Transcribe the displayed result into `out`, upgrade `provenance` to `source: simulator` with `simulator_version`, `captured`, `evidence`, `reviewed_by`, and set `status: pending` until the engine passes it.
6. Run `python corpus/validate.py`.

Prioritise: (a) the 20 seed cases, to find where hand-computed or remembered expectations were wrong; (b) one or more cases per Tier 1 catalog entry; (c) VCE exam questions (Methods, Specialist, General) with every part of the ERQs; (d) every trap in the skill; (e) UDF calls only when the library is installed, tagged `udf`.

A small helper (`tools/capture_sheet.py`, to be written) should print the pending, non-simulator cases as a checklist ordered by tier so capture sessions are efficient.

## 6. Seed corpus (`corpus/seed/001_core.yaml`)

20 cases (Methods 14, General 4, Specialist 2), **all captured on the simulator on 2026-10-31**, with 22 screenshots in `corpus/shots/`. Transcription was by Claude from the screenshots and is awaiting human review. The simulator build number was not recorded (add from Help > About). Cases stay `status: pending` until the engine can run them.

Findings that changed the expectations (all now in the corpus):

- `solve(sin(x)=1/2,x)` returns the general solution with `n1` (confirms the SymPy gap).
- `d(x^2,x)` is **not an error**: an undefined function call is returned unevaluated. The engine must treat unknown names as symbolic function applications.
- Matrices are `[1,2;3,4]`; my first draft used a nested-list form that TI does not use.
- `tvmPmt(N,I,PV,FV,PpY,CpY)` order and sign confirmed (-193.32802 for the 60-month example).
- `normCdf(-1,1,0,1)` displays 0.68268948; the exact value is 0.682689492. TI's numerical integration is about 2e-8 off, so tolerances tighter than 1e-7 would fail against the simulator.
- `cSolve(x^2+1=0,x)` lists `x=i` first (order is irrelevant under canonical comparison).
- `LinRegBx x,y,1:stat.results` returns a results matrix with Title "Linear Regression (a+bx)", RegEqn, a, b, r², r and a residual list shown as `{...}`.
- Document settings in a new document default to the previous document's settings, not to the course preset: always set them explicitly.
- The simulator exposes an "Add Python" page type in this build (CX II-T CAS), which is relevant to the plan's Python-scripting milestone.

Still to capture: individual `stat.*` values, residual list contents, Tier 1 catalog coverage, and exam questions.

Simulator typing notes for future capture sessions (in addition to section 5):

- Typed chunks of 16 or more characters are pasted and can fail silently (a 17-character `normCdf` line vanished). Use chunks of about 9-10 characters.
- `x^2` captures the following text as the exponent: press Right after the exponent. A typed `/` stays inline, so no Right is needed after `1/2`.
- Typing `pi` produces π; `sqrt(-1)` gives i in Rectangular mode; use `exp(x)` rather than `e^(x)`.
- Store arrow: click the on-screen ctrl then var keys.
- The Doc menu route for a new Problem is Doc > 4 Insert > 1 Problem; a new page in the same Problem is Doc > 4 Insert > 3 Calculator.
- The corpus YAML uses `<<: *emu` merge keys; any loader other than PyYAML/ruamel must support them or the anchors must be expanded.

## 7. Device-model test cases to write in M2 (not CAS behaviour)

These come from simulator keyboard behaviour and belong to the input editor, not the evaluator:

- Typing after `^` stays in the exponent until the cursor is moved out (`0.4^3*100` means 0.4^300 unless navigated).
- An entry line beginning with a binary operator is prefixed with `Ans`.
- `ctrl+enter` evaluates in approximate form.
- `shift`/`ctrl`/`var`/`menu`/`doc` layers select the expected key meanings; `esc` cancels a running evaluation.
- Adding a page keeps the Problem's variables; adding a Problem clears them.

## 8. Open items

- Decide the on-disk shape of Hypothesis settings and which parser properties to fuzz first.
- Decide whether `family` comparison uses a numeric window or a symbolic check (start numeric).
- Decide how screenshots are stored (git LFS vs plain PNG; start plain, keep them small).

## 9. CAS Mode: On / Exact Arithmetic / Off (probed 2026-10-31)

Document Settings has a third axis, **CAS Mode**: On, Exact Arithmetic, Off. The corpus `settings` block now has a `cas_mode` field (`on` | `exact_arithmetic` | `off`, default `on`); the replay harness must honour it.

Probe results (Radian, Auto, Real, Float 8; screenshots `corpus/shots/casmode.exact-arithmetic.*.jpg`; the 20 seed cases were also run in CAS Off and filed as `corpus/seed/002_cas_off.yaml`, evidence `corpus/shots/casoff.*.jpg`):

| input | CAS On | Exact Arithmetic | CAS Off |
|---|---|---|---|
| `sqrt(8)` | 2·√2 | 2·√2 | 2.8284271 |
| `1/3+1/4` | 7/12 | 7/12 | 7/12 |
| `sin(pi/5)` | exact radical | √(-2·(√5-5))/4 (exact) | 0.58778525 |
| `(x+1)^2` | (x+1)² (not expanded; not probed in this run) | error | error |

- Error text (both restricted modes): `CAS computations are restricted in CAS Off and Exact Arithmetic modes.`
- CAS Off only: derivative gives `Use Derivative at a Point in CAS Off and Exact Arithmetic modes.`; definite integral returns a numeric value (1.); commands that need no symbolic work (stats, tvm, normCdf, invNorm, regression, numeric matrices) matched CAS On.
- Exact Arithmetic = exact numbers (radicals, fractions, π) but no symbolic variables or CAS commands.
- Further CAS Off findings: an undefined variable raises the restricted error (CAS On echoes the symbol); `df(x):=derivative(f(x),x)` is accepted and `df(3)` gives 6; `47/10` stays a fraction in Auto. expand, symbolic propFrac, `exact()` are restricted in CAS Off; `propFrac(7/3)`, `approx`, `▶DD`, `▶Base16`, `string`, `list▶mat` work (see `003_representations.yaml`).
- Exact Arithmetic has only the four-line probe above, no per-case corpus yet.

## 10. Representation cases (`corpus/seed/003_representations.yaml`)

13 cases (8 CAS On, 5 CAS Off) covering expand/factor/propFrac, `approx`/`exact`, `▶Base16`/`▶Base10`, `▶DD`, `▶Polar`, `string`/`expr`, `list▶mat`/`mat▶list`. Notes:

- Type the conversion arrow as `@>`; the simulator shows ▶.
- `propFrac(7/3)` displays `2+1/3` (mixed form); `▶DD` shows `30°`; `255▶Base16` shows `0hFF`.
- `▶Polar` needs Real or Complex = Rectangular and returns `e^(ⅈ·θ)` forms with an `arctan` term.
- `mat▶list([1,2;3,4])` gave `{1,2,3,4}`; check the ordering again with a non-symmetric matrix.
- Batch 2 (`004_representations_2.yaml`, 12 cases) adds `▶Rect`, `▶Cylind`/`▶Sphere`, `▶Rad`/`▶DMS` in Degree mode, `comDenom`, `approxFraction`, `cFactor`, ctrl+enter approximation, row-major `mat▶list` (confirmed with a 2x3 matrix), and Exact Arithmetic (`ea.*`): number conversions work, `expand` and `exact()` are restricted. All stay `pending`: failing until implemented is expected.
- Not captured: `partFrac` (not found in this build's catalog), `▶Grad`, `▶Decimal`, and Exact Arithmetic `comDenom`/`cFactor`.

## 11. Core batch 3 (`corpus/seed/005_core_batch3.yaml`, captured 2026-11-01)

26 cases: solve and inequalities, `fMax`/`fMin`, `zeros`, limits, Taylor series, derivative forms, `nInt`, sequences and counting, list statistics, `OneVar`, distributions, matrices, vectors, complex numbers, `deSolve`, TVM solve-for, Approximate mode, `LinRegMx`, `QuadReg`. All `pending`.

Findings worth designing for:

- **Undefined names echo, lower-cased and italic**: `stdDev`, `stdDevSamp`, `stdDevPop`, `variance`, `sort` and `transpose` are not evaluated as functions in this build (they behave like unknown symbolic functions). Use `OneVar` for statistics and `^T` for transpose. Check the Catalog before relying on this for `stdDevSamp`, `stdDevPop` and `variance`.
- A decimal in a CAS expression forces approximate output: `solve(sin(x)=0.5,x)|0<=x<=2*pi` gives `x=0.52359878 or x=2.6179939`.
- `solve(x^2+1=0,x)` is real-only, even with Real or Complex = Rectangular, and returns `false`; `cSolve` gives the complex roots.
- `eigVl([2,1;1,2])` returns decimals in the order `{3.,1.}` in Auto mode.
- `solve` on inequalities returns chained forms, for example `-3≤x≤1` and `x<-2 or x>2`.
- `OneVar`: `sx` is the sample standard deviation, `σx` the population one.
- `QuadReg` on exact data shows `b=1.E-13`, `c=-1.E-13`: use an absolute tolerance near zero.
- TVM solvers return `59.999998`, `6.000001` (≈1e-6 relative error). Argument orders: `tvmN(I,PV,Pmt,FV,PpY,CpY)`, `tvmI(N,PV,Pmt,FV,PpY,CpY)`, `tvmPV(N,I,Pmt,FV,PpY,CpY)`, `tvmFV(N,I,PV,Pmt,PpY,CpY)`.
- In Approximate mode `floor(2.7)` displays `2.`.

Typing notes added in this session:

- After `stat.` a variable popup opens: type `stat.res`, then `ults`, then Escape; if the line shows a Syntax error, press Return to dismiss, clear, and type `stat.` then `results`, then Escape.
- `^` followed by `-1` (for `[1,2;3,4]^-1`) works: type `^-1` then Right.
- `Insert > Problem` adds the new Problem after the current one, so tab numbers shift.
- A single computer-use batch times out after about 60 s; keep it under roughly 12 entry lines.
- Zoom images are sometimes captured mid-redraw (results column missing): repeat the zoom after a 1 s wait.

## 12. Core batch 4 (`corpus/seed/006_core_batch4.yaml`)

Eight cases, captured 2026-11-01 (Methods/Specialist presets, CAS On): user-defined functions with `when()`, recursion, transpose operator, inverse/geometric distributions, inverse trig, log behaviour, parametric and system solves.

Findings worth implementing against:

- `ln(x*y)` is returned unexpanded; do not auto-expand logs (no positivity assumption).
- `solve(x^2=a,x)` returns `x=-√(a) and a≥0 or x=√(a) and a≥0`: parametric solves carry domain conditions.
- System solutions are `x=-1 and y=1 or x=3 and y=9`.
- `g(a+1)` for `g(x):=x^2-3x` comes back factored, `(a-2)·(a+1)`.
- `invNorm(0.9,50,10)` = 62.815516; `invBinom(0.5,10,0.5)` = 5; `geomPdf(0.3,3)` = 0.147.
- Matrix transpose is the postfix operator (typed `@t`), not a `transpose()` function.

Typing note: `solve(...)|0<=x<=2*pi` works in the entry line; keep chunks to 11 characters or fewer.

## 13. Batches 5 to 10 and corpus status (`corpus/seed/007` to `012`)

Added 2026-11-01, all `status: pending`, Methods or Specialist presets (Radian, Auto, Real or Rectangular), CAS On.

| File | Cases | Content |
|---|---|---|
| 007_core_batch5 | 6 | VCE-style solves, `abs` integral, `normCdf`/`binomPdf`, product rule and parts, `factor`, limit at infinity |
| 008_core_batch6 | 7 | `crossP`, `simult`, `tExpand`, `deSolve` with initial condition, integration by parts, exact inverse trig, log equation |
| 009_general_batch7 | 4 | `ExpReg`, `PowerReg`, `amortTbl`, `SortA`/`dim` |
| 010_vce_batch8 | 9 | `Define`, `tangentLine`, restricted `fMax`, `tCollect`, `eigVc`/`augment`, `impDif`, `sec`/`cot`/`sinh`, `cZeros`, volume and arc length, second-order ODE |
| 011_vce_batch9 | 10 | Trig quadratic with domain, quartic, quotient/chain rule, piecewise integral, limits and sums, 3x3 system, partial fractions, separable ODE |
| 012_final_batch10 | 6 | `TwoVar`, `csc`/`cosh`, compound interest and depreciation via TVM, `tvmPmt`, `invNorm`/`binomCdf`, arithmetic sequence |

Behaviours worth implementing against:

- Results are returned in particular forms: the quotient rule gives `-(x²-1)/(x²+1)²`; `cos(π/12)` gives `(√3+1)·√2/4`; `∫1/(x²-1)dx` gives `-ln(|x+1|/|x-1|)/2`; `ln(x·y)` is not expanded.
- `integral(abs(x-x^2),x,0,2)` returns the decimal `1.` (numeric), whereas a `when()` piecewise integral returns exact `1`.
- `real()`/`imag()` and powers of `sqrt(-1)` show a warning triangle in Real mode but still compute.
- `TwoVar` results are in `stat.values` (column, matrix indexing `v[k,1]`); OneVar and the regressions use `stat.results`.
- `amortTbl` with only NPmt, N, I and PV treats periods per year as 1.
- `eigVc` and `eigVl` return decimals even in Auto mode.

Open items before the corpus is final:

- Every case needs human review of the transcription (all are `pending`).
- (Done) Simulator build recorded as 6.0.3.374 in all provenance fields.
- (Done) The echo cases were not missing features: the real list functions are `stDevSamp`, `stDevPop`, `varSamp`, `varPop` (m11).
- Not captured: CAS Off and Exact Arithmetic coverage beyond the first 32 cases, graphs/geometry (out of scope), programs and Python.

## 14. Batches 11 to 16: settings, errors, state, long tail, and app screens (`corpus/seed/013` to `018`)

Added 2026-11-01 on simulator version 6.0.3.374, all `status: pending`. Corpus total: 177 (141 earlier + 6 settings/lists + 8 errors/state + 11 long tail + 11 `app_cases`).

| File | Cases | Content |
|---|---|---|
| 013_settings_and_lists | 6 | Degree/Approximate (General preset), Float 3, Fix 2, Polar complex; correct list statistic names |
| 014_errors_and_state | 8 | `undef` results, undefined variable, syntax and argument-count errors, `:=`, `delVar`, redefining and multi-argument functions, `ans`, `→` |
| 015_long_tail_functions | 11 | `nPr`, `lcm`, `ceiling`, `int`, `sign`, `fPart`, `round`, `polyRoots`, `polyEval`, `▶Decimal`, `▶Grad`, one-sided limits, `invT`, `tCdf`, `chi2Cdf`, `arcsinh`, 3x3 `det`/inverse, `rref`, `comDenom`/`cFactor`, `randInt` range |
| 016_app_spreadsheet | 6 | Lists & Spreadsheet: formula column, `seq`, Generate Sequence, OneVar, TwoVar, linear regression |
| 017_app_graph_analysis | 4 | Graphs: zero, minimum/maximum, intersection, integral |
| 018_app_scatter | 1 | Data & Statistics scatter plot with linear regression overlay |

### New: `app_cases`

Screens other than the Calculator are recorded in a top-level `app_cases` list (schema `$defs/app_case`): `app` (`spreadsheet`, `graphs`, `data-statistics`), `setup` (ordered UI steps), `checks` (`what`, `expect`, optional `tol`, `compare`), `provenance` and `status`. The screenshot is the primary evidence; numeric `expect` values are the pass criteria.

### Behaviours worth implementing against

- Settings: in Approximate mode even symbolic results carry decimal points (`x^3+3.·x^2+3.·x+1.`). Float 3 uses scientific notation outside roughly 1e-3 to 1e5 (`3.14E6`, `1.23E-4`). Fix 2 shows `0.005` as `5.00E-3`. Polar complex results print as `r·e^(ⅈθ)`.
- `1/0` and `ln(0)` give `undef` (not errors). An undefined variable echoes back unchanged. Syntax, `Too many arguments` and `Too few arguments` are dialogs.
- `int(-2.5)` = -3 (floor); `ceiling(2.3)` = `3.`; `fPart(7/3)` stays exact. `90▶Grad` in Radian mode treats 90 as radians.
- `arcsinh(1)` stays unevaluated as `sinh⁻¹(1)` in Auto mode.
- Spreadsheet: whole-column reference is `a[]`; naming column A `d` and using `d` in a formula raises a "Conflict Detected" dialog. Statistics results are decimals. Quartiles use the median-of-halves rule (Q1 of {1,4,9,16,25,36,49,64} is 6.5, Q3 is 42.5).
- Spreadsheet selection (FR-SHEET-004 to FR-SHEET-008): without Shift, an arrow replaces a range with the adjacent single cell. Shift+arrows grow or shrink an inclusive rectangular range; physical Shift and latched keypad Shift are equivalent. A mouse click collapses to one cell, while a drag in either direction selects the rectangle between its endpoints. Reaching a row or column heading through range extension gives whole-row or whole-column selection. These requirements apply in grid-navigation mode: Shift+Left and Shift+Right while editing ordinary cell text select text instead. While a formula is being edited and a reference is accepted at the caret, pointing or selecting cells inserts a reference there; extending the selection updates that reference in place and leaves the destination cell fixed.
- Graphs: coordinates are labelled to three significant figures (decision 0034; first recorded as 2 decimal places); Intersection with two graphs goes straight to the bounds prompt; Integral accepts typed bounds and asks "graph?" when several graphs exist.

### Batches 17 to 19 (`019` to `021`)

| File | Cases | Content |
|---|---|---|
| 019_app_graph_analysis_2 | 3 | Graphs: inflection (0,0), dy/dx at x=2 (9), bounded area between x^3-3x and x on [0,2] (4) |
| 020_more_settings | 3 | Gradian angle, Exponential Format Scientific and Engineering (new `exp_format` settings key) |
| 021_app_sheet_sort | 1 | Spreadsheet sort |

More behaviours: Gradian is exact (`sin(100)=1`, `arcsin(1)=100`). Scientific gives `1.2345679ᴇ4`; Engineering gives `12.345679ᴇ3` and `123.ᴇ-6`; exact results are unaffected. Bounded Area shows a warning dialog unless Real or Complex is Real. Document Settings carry over from the last changed document: a new document opened with Real or Complex = Polar (set earlier) rather than a fixed factory default, so every capture must set its settings explicitly.

### Still open

- Human review of every transcription: done 2026-11-02 (Simon Tyler); provenance.reviewed_by records it. The `status: pending` field is the engine-runnable status (not review status) and stays until each case is wired into the test runner.
- Spreadsheet Fill is now covered (`024_app_sheet_fill.yaml`): context menu 6 Fill, or Menu > 3 Data > 3 Fill, then arrow keys to extend the destination range and Enter.
- Not captured: none of the originally listed items remain; further ideas: Graphs Hyperbola/Parabola templates in other orientations with decimals, Diff Eq with several equations, Sequence with two-term recursion.
- Overlay labels are clipped at the plot edge when wide, and for every overlay the label should later be draggable (TODO milestone).

Batch 24 (`030_app_overlays_2.yaml`, `031_app_graph_entry_types.yaml`): Data & Statistics overlays for quartic, logarithmic, median-median, sinusoidal and logistic (d=0) fits, and Graphs entry for Parametric (error "No expression specified for y" if y1 is empty on Enter), Polar, Sequence (recursive with Initial Terms) and Diff Eq (slope field). Batch 25 (`032_logisticd.yaml`, `033_app_last_items.yaml`): LogisticD (a=4, b=0.5, c=10, d=2) and its overlay, Diff Eq initial condition (two Tabs from the equation line, solution curve y1_1 plus slope field), Sequence > Custom (needs existing sequence names), decimal/negative template parameters. In the Logistic RegEqn b is the coefficient in e^(-b·x), so b is positive for a rising curve. Regression submenu: 3 MedMed, 4 Quad, 5 Cubic, 6 Quartic, 7 Power, 8 Exp, 9 Log, A Sin, B Logistic (d=0), C Logistic (d≠0).

Batch 20 (`022_app_stats_plots.yaml`, `023_app_stats_quadreg.yaml`): Data & Statistics dot plot, histogram (default bin width 1 starting at the minimum) and box plot (median-of-halves quartiles: Q1 4, median 4.5, Q3 6 for {2,4,4,4,5,5,7,9}); QuadReg of {1..5} vs {2,5,10,17,26} gives a=1, c=1 and b≈1e-13 (shown as 100.ᴇ-15), so compare b with a tolerance. Typing `stat.results` in the Calculator is mangled by autocomplete.
- Settings: Degree with Methods/Auto not captured.


Batch 21 (`025_degree_and_regressions.yaml`, `026_app_graph_table_conic.yaml`): Degree with Auto (exact special angles, `sin(1)` stays unevaluated, constraint after `|` needed in solve), ExpReg/PowerReg/CubicReg on exact data (b and c of the cubic are ~1e-11 noise), Generate Sequence sixth term 63, Graphs split-screen table, typed ellipse relation. Typing `stat.` opens an autocomplete list that swallows the next key.

Batch 22 (`027_app_overlays_conics.yaml`): exponential, power and cubic overlays in Data & Statistics; circle (centre form), parabola (vertex form) and hyperbola (east-west) Equation Templates. The simulator prints negative parameters literally (`y--2`, `+-3`, `+-4.9ᴇ-11`), and the hyperbola template's Tab order is h, a, k, b.

Batch 23 (`028_app_templates_all.yaml`, `029_more_regressions.yaml`): every Equation Template form (Line x3, Parabola x4, Circle x2, Ellipse, Hyperbola x2, Conic General), plus quartic, logarithmic (`LnReg`), median-median, sinusoidal and logistic regressions. Notable: `SinReg` returns b in radians even in Degree mode; template Tab orders differ (hyperbola east-west h,a,k,b; south-north k,a,h,b; x-parabola a,k,h; circle standard has a linked second `a` box so needs two Tabs); the simulator prints negative parameters as `+-` / `--`.

### Check 6, run 7 (`039_check6_run7.yaml`, 2026-11-27)

Results in `emulator-calc8-results.md`. What CASSim now follows:
- **Warning triangles** (CASSim's own wording; tested in `tests/unit/test_cas_run7.py`):
  - *Domain of the result*: shown when putting the result over one denominator cancels a factor in a variable. The device appears to use the product of the denominators, so `(x²-1)/(x-1)` (now `x+1`) and `d/dx((x+1)/(x-1))` warn, and `d/dx(ln(x²-1))` does not. Also on `expand` without a variable when it divides a term out, and on `tCollect` when it multiplies a sum out first. The rule comes from about ten examples, triangle or none; more may break it.
  - *More solutions*: on a `solve` that returns unsolved.
  - *Condition*: on a solving command whose `|` condition is not a variable compared with a constant (`|0<x<h/2`).
- **Families:** a family that merges two (cos(x)=0) is written `(2·n1-1)·π/2`; one family keeps the sum form (`n1·π+π/4`).
- **fMin and fMax:**
  - Of a single sine or cosine, they solve f = its extreme value, with no `(-1)^n` condition: `(4·n1+1)·π/2`, `2·n1·π`.
  - A sum such as sin+cos keeps the condition (run 6).
  - An extremum approached towards ±∞ is `x=-∞`. `fMax(x^2,x)` giving `x=-∞ or x=∞` follows from that and is not seen on the device.
- **Logarithms:** logs of fractions in a sum are combined (`ln(9/2)/8`), and so is an equation's number side (`t=150·ln(59/40)`).
- **Still different:**
  - `fMin(cos(x)^2,x)`: the device adds `x=-∞ or … or x=∞` (xfail).
  - The order of the three terms of `∫₀² 1/(x³+x+2)dx` and of `expand`'s terms.
  - The unsolved equation is echoed; the device rearranges it.

### Check 6, run 7: Graphs Actions (2026-11-27)

FR-GRAPH-008; tested in `tests/unit/test_graph_actions.py`.

- **Actions menu**, numbered as on the device:
  - Pointer, Attributes, Text, Coordinates and Equations, and Calculate work;
  - Select, Hide/Show, Set Conditions, Delete all and Redefine keep their places, greyed.
- **Attributes** come in a dialog with the panel's rows: line weight, line style, label style 1 to 5, continuous or discrete, number of points. A discrete graph's step is the window's width over points + 1, which gives the device's 0.769231 for 25 points on -10 to 10. A label is drawn once a label style is chosen; the device shows one from the start.
- **A drag that starts on a curve** translates it by two significant figures (`2·sin(x-0.91)-0.044`), applied when the drag ends; the device moves the curve as you drag.
- **Graph Entry/Edit:**
  - lists every entry type and every Equation Template form in its place, greyed except Function, since CASSim cannot plot relations yet;
  - the device puts an empty template in the entry line as `e1`.
- **Coordinates and Equations** labels a kept or analysed point with its coordinates, and a curve with its equation, as fixed text.

### Review fixes (2026-11-02)

- Gradian marker is `ᵍ` (U+1D4D, lowercase superscript g, ASCII `@g`), not `ᴳ`. Changed in the corpus, `CLAUDE.md`, the lexer, evaluator, formatter, AST and unit tests (tests not re-run in this pass).
- `@i` is used in `in:` lines for the imaginary unit (cSolve/abs case); `sqrt(-1)` kept as an alternative spelling.
- CAS Off: derivative at a point works (`derivative(x^2*sin(x),x)|x=2` = 1.9726024 in Radian).
- Transpose is `ᵀ` (U+1D40, ASCII `@t`). On the simulator it is entered with Menu > Matrix & Vector > Transpose; typing `@t` on the keyboard is not converted.
- `∞` can be typed as the character or spelled `infinity`.
- `undef` carries through calculations (`0*ln(0)`, `undef+1` are `undef`) while `limit(x*ln(x),x,0,1)` = 0.
- Error dialogs for syntax and argument errors leave the cursor in the entry line for editing.
- `int` equals `floor` (checked for positive and negative decimals).
- The Finance Solver window is built on top of the individual `tvm*` functions.
- Checked every `out:`/`expect:` string in the corpus for a plain `e`, `E` or `i` standing for ⅇ, ᴇ or ⅈ: none found. The corpus holds `ⅇ` everywhere (for example `x=ⅇ^2`).
- Case setup fixed: the regression cases now define `cx` (or `cu`) themselves.

### Later milestones (TODO)

- Data & Statistics screens animate (for example when plot types or variables change). Reproduce the animations in a much later milestone.
- Regression overlays: the equation label can be clicked and dragged to move it so it is easier to read. Implement for every overlay.
