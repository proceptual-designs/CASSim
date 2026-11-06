# 0014. Spike A: rendering results as maths

Date: 2026-11-06. Status: **GO. Render engine LaTeX with Flet's native `ft.Markdown` (`$$...$$`).** B, C and D are not started.
Code: `spikes/spike5_web/`, `spikes/run_web_spike5.py`, `spikes/gen_latex_cases.py`. Screenshot: `spikes/spike5_web/shots/latex.png`. Flet 1.0.5, headless Edge.

## Finding
`ft.Markdown` draws LaTeX on the Flutter canvas (`flutter_math`): no JS, no DOM, no extra download, and it works in the static build and offline with the rest of the app. MathJax or KaTeX would need `index.html` changes and a bridge, because Flet's Python runs in a worker with no DOM. The canvas-layout option is not needed.

Rendered correctly: fractions, nested fractions, roots (including cube roots), powers, `\int`, `\sum`, `\lim`, sets, `\sin^{-1}`, `|x|`, `\vee`/`\wedge`, bracket matrices with fractions, and upright ⅇ and ⅈ. 21 engine results look right in `shots/latex.png`.

| Measure | Result |
|---|---|
| Python-side build of 200 matrices | 40 ms |
| Browser, 200 matrices added at once | one 483 ms frame, then about 51 fps (153 frames in 3 s) |
| JS heap after the stress run | 107 MB for the whole page |
| Extra download | none measured; fonts are part of the Flutter build (size of the fonts not measured) |

## Problems found, and the fixes
1. **The Markdown layer collapses `\\` to `\`.** A row break followed by `\frac` printed "frac", and `\\-x` failed with "Undefined control sequence". Flet's Markdown control also takes `{`/`\{` untouched, so braces are fine. `\cr` (the TeX row end) passes through and means the same, so `format.latex_for_markdown` replaces `\\` with `\cr `. Use it on every string sent to `ft.Markdown`. Doubling every backslash, doubling only `\\` and a space after `\\` all fail.
2. **SymPy's LaTeX had the wrong conventions.** SymPy has hooks, and they help. `sp.latex` options `ln_notation=True` and `inv_trig_style="power"` give `\ln` and `\sin^{-1}`. ⅇ and ⅈ have no setting, and a subclass override of `_print_Exp1` is ignored because SymPy prefers the object's own `_latex`. The fix is a `LatexPrinter` subclass whose `_print` intercepts `sp.E`, `sp.I` and `sp.exp` (`_TILatexPrinter` in `core/compat/sympy_adapter.py`). Clearing `printmethod` instead breaks `π`.
3. **Catalog gaps found while checking sum and integral** (fixed, tests in `tests/unit/test_calculus.py`):
   - `sumSeq(expr, k, low, high)` and `prodSeq(...)` did not exist. They are added, with symbolic or infinite bounds, and the templates `Σ(`, `∑(`, `Π(`, `∏(` and `∫(` are aliases of `sumSeq`, `prodSeq` and `integral`. `sum(seq(...))` and `sum({...})` already worked.
   - `integral(expr, x[, lo, hi])` was correct; only the `∫(` spelling was missing.
   - Not changed: `Σ(` casefolds to `σ` in the function table. A user function named `σ` takes precedence, so this is harmless.

## Not fixed, for the catalog
- `piecewise(...)` stays unevaluated (already `later/todo` in `docs/command_matrix.csv`).
- `solve(x^2+y^2=1,y)` returns the two branches with their domain conditions (`1-x^2≥0`); TI shows only `y=-√(1-x²) or y=√(1-x²)`. No corpus case covers it yet.
- `d/dx(...)` typed as a division echoes as a quotient. Probably right for TI (`d(` is the derivative function), but unchecked on the simulator.

## Carry into the GUI work
- Fonts and size: measure the published build with and without the LaTeX fonts.
- Selecting or copying a rendered result is not tested; copy should come from `Result.text`, not the picture.
- Large matrices (say 6 by 6) and long expressions that need to wrap or scroll are not tested.
