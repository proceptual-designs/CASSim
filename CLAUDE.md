# CASSim: instructions for Claude Code

Read `PLAN.md` first. It holds the architecture, milestones and decisions. This file is the working brief.

## Project
A static, installable (PWA) browser simulation of the TI-Nspire CX CAS. Python (SymPy/SciPy) runs client-side via Pyodide; the UI is Flet. Owner: Simon Tyler, a VCE maths teacher (Methods, Specialist), strong in maths and physics, writes Python. Be accurate and concise.

## Current state
M0 is done. Tooling, all spikes, the command coverage matrix and 177 simulator-captured corpus cases exist; every case is still `pending` and awaits Simon's review. The repo has no Git remote yet, so CI has never run. M1a (parser) and M1b (values, settings, display, `Session`, replay harness) are done; choices still to check on the simulator are in `docs/decisions/0007-parser-grammar.md` and `0008-values-and-display.md`. `python -m tools.replay` shows corpus progress. Next is M1c (variables, `Define`, `|`). Do not start GUI work before M1 exit criteria are met.

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
- Library UDFs (`mm_`, `sm_`, `gm_`) are `.tns` and not loadable. Port them to native Python later (M5), after checking the LazyMath licence.

## Verified vs unverified
Spike results and go/no-go decisions are in `docs/decisions/`; read those rather than assuming. Verified on the CAS side: the Flet static build runs SymPy and SciPy, the engine runs in its own worker and is cancelled by terminating it, canvas speed is fine with one `Points` shape per curve, and IndexedDB works from Pyodide. `.tns` is a no-go for now. Offline PWA still needs the wheels vendored (see 0002).
**Unverified:** embedding MathLive (fallback MathQuill) in the Flet web build; offline behaviour end to end.

## Conventions
- Small commits, conventional commit messages. Every behaviour change ships with a test. Fix lint and type errors rather than suppressing them.
- Known failing corpus cases are `xfail(strict=True)` with a reason.
- Never use TI logos, artwork or ROM content. The product name is CASSim.
- Reference material is in `references/` (Reference Guide, shortcuts, VCE teacher resource books, LazyMath UDF guides and libraries). Do not edit it.

## Simulator corpus capture (needs Simon's machine)
The TI-Nspire CX CAS Premium Teacher Software is on Simon's computer. Use the `vce-cas-solver` skill workflow: Handheld-page-size document, set Document Settings first (General: Degree/Approximate/Real; Methods: Radian/Automatic/Real; Specialist: Radian/Automatic/Rectangular; Float 8), a new Problem per case, type in short chunks, screenshot the result, store the screenshot beside the YAML case. Tell Simon which cases were simulator-verified and which were hand-verified only.
