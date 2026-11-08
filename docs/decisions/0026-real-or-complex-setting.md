# 0026: the Real or Complex setting

Status: accepted 2026-11-08. Evidence: `docs/testing/emulator-domain-results.md` (simulator build 6.0.3.374, run by Cowork).

## Rules implemented
- **Real mode errors only when a real-only function leaves its real domain and the final value is complex.** `√`, `^` with an even-denominator fraction, `ln`, `log`, `arcsin`, `arccos`, `arccosh`, `arctanh` and `root` of a real number outside the real domain set a flag (`Host.note_non_real`). The evaluator raises "Non-real result" at the end of the entry if the flag is set and the value is not real. So `√(-1)` errors, `{1,√(-1)}` errors, but `√(-1)*√(-1)` is `-1` and `real(3+4√(-1))` is `3`.
- A **typed ⅈ never** errors in Real mode (`ln(ⅈ)`, `√ⅈ`, `(1+ⅈ)^2`).
- **Real mode takes real odd roots**: `(-8)^(1/3)` is `-2`, `(-8)^(2/3)` is `4`. Rectangular and Polar give the principal value (`1+√3ⅈ`).
- **Out-of-domain inverse functions evaluate** in Rectangular and Polar (`arcsin(2)` is `π/2-ⅈ·ln(2+√3)`).
- **Polar** writes `ⅇ^(ⅈθ)*r` with the modulus last and omitted when 1, including a negative angle (`ⅇ^(-ⅈ*π/2)`).
- `solve`, `factor` and `zeros` are real-only in every setting; `cSolve`, `cZeros`, `cFactor` are complex in every setting. This already matched.
- Approximate changes only the number format, not which inputs error.

## Known differences left (not done)
- **Warning triangle** ("Non-real calculation", Real mode, on `√(-1)*√(-1)`, `real(3+4√(-1))`): the value is right but there is no warning in the UI.
- **Polar results are plain text** in the GUI (a `Shown` value), not typeset.
- Polar forms for out-of-range inverse functions differ in shape from the device (equal in value).
- `fMax(x^2+1,x)` should give `x=-∞ or x=∞` and `fMin(x^2+1,x)` gives `x=0`; the engine leaves `fMax` unevaluated.
- `angle(3+4ⅈ)` prints `tan⁻¹(4/3)`; the device prints `π/2-tan⁻¹(3/4)` (equal in value).
- Not captured by Cowork: `zeros` in Polar, a few wide Polar results, and Real/Rectangular with Degree.
- No corpus cases yet: the run kept one screenshot per group, so promoting rows to `corpus/` needs a human review (decision 0012 rules). The behaviour is covered by `tests/unit/test_real_complex_setting.py`.
