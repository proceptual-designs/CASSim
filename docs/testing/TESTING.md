# emCAS testing: the first bits

Status: draft 1 (2026-10-31). Covers what must exist before M1 coding starts: the golden corpus, how it is replayed, how comparison works, and how cases are captured from the real emulator. Companion files: `corpus/schema.json`, `corpus/validate.py`, `corpus/seed/001_core.yaml` (20 seed cases).

## 1. Principles

- The TI-Nspire emulator is the oracle. SymPy is only the implementation.
- Correctness means **symbolic or numeric equivalence**, not identical text (decision: Simon, 2026-10-31).
- Every case records where its expectation came from. Only `emulator` provenance counts as verified.
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
  provenance: {source: emulator, emulator_version: "...", captured: 2026-11-02,
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

**Provenance sources:** `emulator` (needs evidence screenshot, enforced by the validator) › `skill_notes` (from Simon's cas-solver skill; reported as verified there, to be re-captured) › `hand_computed` (derived independently, e.g. with SciPy) › `unverified_expectation` (from memory; treat as a hypothesis).

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

## 5. Capturing from the emulator

Use Simon's `vce-cas-solver` workflow (TI-Nspire CX CAS Premium Teacher Software, Handheld page size). For each case:

1. Open or reuse a document; set Document Settings for the course (section 3). Check the title bar shows DEG or RAD.
2. New Problem per case (`new_problem` steps insert another Problem inside the same case).
3. Enter each `in` line in short chunks (about 9 characters). Beware emulator typing quirks that are properties of the keyboard, not the CAS: `^` swallows everything after it as the exponent; a line starting with an operator gets `Ans` in front; ASCII `e` and `i` are plain variables (use `e^(...)` template, `exp()`, `√(-1)`).
4. Screenshot the result region (about 455x303 px) and save as `corpus/shots/<case-id>[-<step>].png`.
5. Transcribe the displayed result into `out`, upgrade `provenance` to `source: emulator` with `emulator_version`, `captured`, `evidence`, `reviewed_by`, and set `status: pending` until the engine passes it.
6. Run `python corpus/validate.py`.

Prioritise: (a) the 20 seed cases, to find where hand-computed or remembered expectations were wrong; (b) one or more cases per Tier 1 catalog entry; (c) VCE exam questions (Methods, Specialist, General) with every part of the ERQs; (d) every trap in the skill; (e) UDF calls only when the library is installed, tagged `udf`.

A small helper (`tools/capture_sheet.py`, to be written) should print the pending, non-emulator cases as a checklist ordered by tier so capture sessions are efficient.

## 6. Seed corpus (`corpus/seed/001_core.yaml`)

20 cases (Methods 14, General 4, Specialist 2), **all captured on the emulator on 2026-10-31**, with 22 screenshots in `corpus/shots/`. Transcription was by Claude from the screenshots and is awaiting human review. The emulator build number was not recorded (add from Help > About). Cases stay `status: pending` until the engine can run them.

Findings that changed the expectations (all now in the corpus):

- `solve(sin(x)=1/2,x)` returns the general solution with `n1` (confirms the SymPy gap).
- `d(x^2,x)` is **not an error**: an undefined function call is returned unevaluated. The engine must treat unknown names as symbolic function applications.
- Matrices are `[1,2;3,4]`; my first draft used a nested-list form that TI does not use.
- `tvmPmt(N,I,PV,FV,PpY,CpY)` order and sign confirmed (-193.32802 for the 60-month example).
- `normCdf(-1,1,0,1)` displays 0.68268948; the exact value is 0.682689492. TI's numerical integration is about 2e-8 off, so tolerances tighter than 1e-7 would fail against the emulator.
- `cSolve(x^2+1=0,x)` lists `x=i` first (order is irrelevant under canonical comparison).
- `LinRegBx x,y,1:stat.results` returns a results matrix with Title "Linear Regression (a+bx)", RegEqn, a, b, r², r and a residual list shown as `{...}`.
- Document settings in a new document default to the previous document's settings, not to the course preset: always set them explicitly.
- The emulator exposes an "Add Python" page type in this build (CX II-T CAS), which is relevant to the plan's Python-scripting milestone.

Still to capture: individual `stat.*` values, residual list contents, Tier 1 catalog coverage, and exam questions.

Emulator typing notes for future capture sessions (in addition to section 5):

- Typed chunks of 16 or more characters are pasted and can fail silently (a 17-character `normCdf` line vanished). Use chunks of about 9-10 characters.
- `x^2` captures the following text as the exponent: press Right after the exponent. A typed `/` stays inline, so no Right is needed after `1/2`.
- Typing `pi` produces π; `sqrt(-1)` gives i in Rectangular mode; use `exp(x)` rather than `e^(x)`.
- Store arrow: click the on-screen ctrl then var keys.
- The Doc menu route for a new Problem is Doc > 4 Insert > 1 Problem; a new page in the same Problem is Doc > 4 Insert > 3 Calculator.
- The corpus YAML uses `<<: *emu` merge keys; any loader other than PyYAML/ruamel must support them or the anchors must be expanded.

## 7. Device-model test cases to write in M2 (not CAS behaviour)

These come from emulator keyboard behaviour and belong to the input editor, not the evaluator:

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

- Type the conversion arrow as `@>`; the emulator shows ▶.
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
