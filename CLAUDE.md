# emCAS: instructions for Claude Code

Read `PLAN.md` first. It holds the architecture, milestones and decisions. This file is the working brief.

## Project
A static, installable (PWA) browser emulation of the TI-Nspire CX CAS. Python (SymPy/SciPy) runs client-side via Pyodide; the UI is Flet. Owner: Simon Tyler, a VCE maths teacher (Methods, Specialist), strong in maths and physics, writes Python. Be accurate and concise.

## Current state
Planning is done; no code exists yet. Next job is **M0 (Foundations and de-risking)**, then M1 (text CAS). Do not start GUI work before M1 exit criteria are met.

## Decisions already made (do not re-litigate)
- Repo lives in this OneDrive folder. Keep the virtualenv out of OneDrive: set `UV_PROJECT_ENVIRONMENT` to a local path (e.g. `C:\dev\venvs\emcas`). Commit and push to a Git remote often.
- Correctness is judged by **symbolic/numeric equality**, not TI's exact output text. Maths is rendered from LaTeX.
- Python scripts in the app are sandboxed in the browser but must prompt before running.
- Geometry page is out of initial scope.
- Python 3.14 (matches Pyodide 314.0.7). Tooling: **uv, Ruff, Ty, Git, pytest, Hypothesis, Playwright**.
- Core engine (`src/emcas/core`) is pure Python and must never import Flet. SymPy is touched only inside `core/compat/sympy_adapter.py`. Core is fully typed and passes Ty strict.
- TI syntax is parsed with a real tokenizer + Pratt parser, not regexes (see `spikes/ti_eval_spike.py` for why).
- Library UDFs (`mm_`, `sm_`, `gm_`) are `.tns` and not loadable. Port them to native Python later (M5), after checking the LazyMath licence.

## Verified vs unverified
Verified: `flet publish` builds a PWA static site; Pyodide 314.0.7 includes numpy, scipy, sympy, mpmath, micropip; SymPy is fast enough for core VCE operations; the parser spike works.
**Unverified (M0 spikes decide):** SymPy and SciPy running inside the Flet static build (size, cold start, offline); whether Python runs in a worker and can be cancelled; Flet canvas drawing speed; IndexedDB from Pyodide; `openpyxl` in Pyodide; embedding MathLive (fallback MathQuill) in the Flet web build; `.tns` decodability; Ty's current stability (fallback: pyright).
Write each spike up in `docs/decisions/` with a go/no-go.

## First steps for M0
1. `git init`, `uv init` (src layout), `pyproject.toml` with ruff + ty + pytest config, `.gitignore`, pre-commit, CI workflow.
2. Create the package skeleton from PLAN.md section 3 (empty modules with docstrings are fine).
3. Run the spikes in PLAN.md section 8 (M0) and record results.
4. Build the golden-corpus tooling: YAML schema (PLAN.md section 6), replay test harness, and a capture checklist.
5. Refine `docs/reference_index_draft.txt` into a full command coverage matrix from `references/TI-Nspire_ReferenceGuide_EN_4.5.pdf` (the draft misses entries such as `solve`).

## Conventions
- Small commits, conventional commit messages. Every behaviour change ships with a test. Fix lint and type errors rather than suppressing them.
- Known failing corpus cases are `xfail(strict=True)` with a reason.
- Never use TI logos, artwork or ROM content. The product name is emCAS.
- Reference material is in `references/` (Reference Guide, shortcuts, VCE teacher resource books, LazyMath UDF guides and libraries). Do not edit it.

## Emulator corpus capture (needs Simon's machine)
The TI-Nspire CX CAS Premium Teacher Software is on Simon's computer. Use the `vce-cas-solver` skill workflow: Handheld-page-size document, set Document Settings first (General: Degree/Approximate/Real; Methods: Radian/Automatic/Real; Specialist: Radian/Automatic/Rectangular; Float 8), a new Problem per case, type in short chunks, screenshot the result, store the screenshot beside the YAML case. Tell Simon which cases were emulator-verified and which were hand-verified only.
