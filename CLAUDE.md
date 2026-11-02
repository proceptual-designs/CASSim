# CASSim: instructions for Claude Code

Read `PLAN.md` first. It holds the architecture, milestones and decisions. `docs/SRS.md` holds the requirements (stable IDs such as `FR-CAT-001`, `NFR-SEC-001`; MoSCoW priorities). This file is the working brief.

## Project
A static, installable (PWA) browser simulation of the TI-Nspire CX CAS. Python (SymPy/SciPy) runs client-side via Pyodide; the UI is Flet. Owner: Simon Tyler, a VCE maths teacher (Methods, Specialist), strong in maths and physics, writes Python. Be accurate and concise.

## Current state
M0 is done. Tooling, all spikes, the command coverage matrix and 177 simulator-captured corpus cases exist; Simon has reviewed every case (23 now `pass`, the rest `pending` until the engine can run them). The repo is at https://github.com/simonjtyler/CASSim (private) and CI is green on `main`. M1a (parser), M1b (values, settings, display, `Session`, replay harness) and M1c (variables, `Define`, user functions, `DelVar`, `ClearAZ`, `=` constraints) are done; choices still to check on the simulator are in `docs/decisions/0007-parser-grammar.md`, `0008-values-and-display.md` `0009-variables-and-scope.md` and `0010-catalog.md`. `python -m tools.replay` shows corpus progress. M1d (the catalog) is in progress in slices: slices 1 (elementary, algebra, lists, matrices, vectors, `when`) 2 (`solve`/`cSolve`/`zeros` with `|` domains) 3 (calculus, `deSolve`) and 4 (distributions, finance) are done; next are the statistics and regression commands, then conversions and the long tail. Do not start GUI work before M1 exit criteria are met.

## Decisions already made (do not re-litigate)
- Repo lives at `C:\dev\CASSim`, outside OneDrive. The virtualenv is the in-project `.venv` (uv default; do not set `UV_PROJECT_ENVIRONMENT`). Commit and push to a Git remote often.
- Correctness is judged by **symbolic/numeric equality**, not TI's exact output text. Maths is rendered from LaTeX.
- Python scripts in the app are sandboxed in the browser but must prompt before running.
- Geometry page is out of initial scope.
- Python 3.14 (matches Pyodide 314.0.7). Tooling: **uv, Ruff, Ty, Git, pytest, Hypothesis, Playwright**.
- Core engine (`src/cassim/core`) is pure Python and must never import Flet. SymPy is touched only inside `core/compat/sympy_adapter.py`. Core is fully typed and passes Ty strict.
- TI syntax is parsed with a real tokenizer + Pratt parser, not regexes (see `spikes/ti_eval_spike.py` for why).
- Canonical text is Unicode: `e` is a variable, `ⅇ` is Euler's constant, `ᴇ` is the exponent marker. ASCII is only a REPL spelling (`to_ascii` in `core/format.py`).
  - **Do not overwrite or "normalise" these symbol conventions** (reviewed and confirmed 2026-11-01; see `docs/decisions/0007-parser-grammar.md` and `to_ascii`). Canonical Unicode forms: `ⅇ` Euler's constant, `ⅈ` imaginary unit, `ᴇ` exponent marker (`3.14ᴇ6`), `π`, `∞`, `ᵀ` (U+1D40), `ʳ`, `ᵍ` (U+1D4D, a lowercase superscript g, ASCII `@g`; not the uppercase `ᴳ`), `°`, `∠`, `▶`. Plain `e`, `i`, `E` are ordinary variables, so `2e3` is `2*e3`. Typed (input) spellings in corpus `in:` lines are TI's ASCII ones: `@e`, `@i`, `@E`, `@t`, `@r`, `@g`, `@d`, `@<`, `@>`, `pi`, `infinity`; `out:` lines use the Unicode forms. Never replace `ⅇ`/`ᴇ` with `e`/`E` in outputs, and never replace `@>` with `▶` in inputs.
- Statistics must follow the TI/school convention, not numpy: quartiles are the median of the lower and upper halves (median excluded when n is odd), e.g. Q1 of {1,4,9,16,25,36,49,64} is 6.5 and Q3 is 42.5 (numpy's default gives 7.75 and 39.25). Implement it directly; do not call `numpy.percentile`/`quantile`. Sample sd uses n-1 (`sx`), population uses n (`σx`).
- Other simulator behaviours to match (details in `docs/testing/TESTING.md` section 14): Approximate mode shows decimals inside symbolic results (`3.·x^2`); Float 3 / Fix 2 switch to `ᴇ` notation for very small or large values (`5.00ᴇ-3`); `1/0` and `ln(0)` give `undef`, not errors; undefined variables echo unchanged; `int(-2.5)` = -3 (floor); `sinh⁻¹(1)` stays unevaluated in Auto mode; spreadsheet whole-column references are `a[]`; Graphs coordinates label to 2 dp and Integral accepts typed bounds.
- Library UDFs (`mm_`, `sm_`, `gm_`) are `.tns` and not loadable. Port them to native Python later (M5). LazyMath is Unlicense, so porting is permitted; record the check in `docs/decisions/` first.
- Decisions from the SRS review (2026-11-02; see `docs/SRS.md`):
  - CASSim is a simulator, not a hardware emulation. "Close enough not to confuse a student or teacher" is the bar; exact text only where a case says `compare: exact`. Released under the Unlicense.
  - No telemetry or analytics of any kind; no server; share links carry the document in the URL fragment (keep under about 2,000 characters, else export a file). Imported documents and share links never auto-run Python or programs.
  - Computer and Handheld modes are equal top priority; Tablet/demo is Should. Dark is the default theme; themes come from a user-editable config file with a fallback to Dark.
  - Primary test targets are Chromebooks, Chrome and Safari; Edge and Firefox are smoke-tested. Hosting is any free static host.
  - `.tns` import/export is Won't for now. Python page is Could; if built, sandbox plus trust prompt are mandatory. Exam-restriction mode is Could.
  - No fixed performance or size budgets: cold start and download size are measured and reported. Cancel must take effect within 1 s.
  - Accessibility is Should: gaps go in `docs/accessibility.md` and are stubbed, not skipped.
  - Coverage target 90% on `core/`, 80% on `device`, `doc`, `sheet`, `stats`, `graph`. Every SRS requirement ID must appear in a test or be listed as untested with a reason (`docs/traceability.md`, generated by `tools/`).

## Verified vs unverified
Spike results and go/no-go decisions are in `docs/decisions/`; read those rather than assuming. Verified on the CAS side: the Flet static build runs SymPy and SciPy, the engine runs in its own worker and is cancelled by terminating it, canvas speed is fine with one `Points` shape per curve, and IndexedDB works from Pyodide. `.tns` is a no-go for now. Offline PWA still needs the wheels vendored (see 0002).
**Unverified:** embedding MathLive (fallback MathQuill) in the Flet web build; offline behaviour end to end.

## Conventions
- Small commits, conventional commit messages. Every behaviour change ships with a test; cite the SRS requirement ID in the test where one applies. Design docs go in `docs/design/` (SDD set listed in SRS appendix A). Fix lint and type errors rather than suppressing them.
- Known failing corpus cases are `xfail(strict=True)` with a reason.
- Never use TI logos, artwork or ROM content. The product name is CASSim.
- Reference material is in `references/` (Reference Guide, shortcuts, VCE teacher resource books, LazyMath UDF guides and libraries). Do not edit it.

## Simulator corpus capture (needs Simon's machine)
The TI-Nspire CX CAS Premium Teacher Software is on Simon's computer. Use the `vce-cas-solver` skill workflow: Handheld-page-size document, set Document Settings first (General: Degree/Approximate/Real; Methods: Radian/Automatic/Real; Specialist: Radian/Automatic/Rectangular; Float 8), a new Problem per case, type in short chunks, screenshot the result, store the screenshot beside the YAML case. Tell Simon which cases were simulator-verified and which were hand-verified only.
