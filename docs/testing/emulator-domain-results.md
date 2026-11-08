# Emulator results: the "Real or Complex" setting (Real, Rectangular, Polar)

Run by Claude (computer use) for `emulator-domain-capture.md`, 8 Nov 2026.

- **Build:** TI-Nspire CX CAS Premium Teacher Software, Version **6.0.3.374** (Help > About). Keypad shows "CX II-T CAS".
- **Document Settings used:** Radian, Auto, Float 8, Exponential Format Normal, CAS On. Only "Real or Complex" was changed between runs (Real, Rectangular, Polar). The settings were checked in the dialog before each run and the title bar read RAD.
- Handheld-page-size document, layout "Keypad + SideScreen".
- Each batch of inputs was run on a **new Calculator page** (ctrl+I), not a new Problem, because none of the inputs use stored variables (`x` is undefined throughout). Page 1.50 hit the 50-pages-per-problem limit during Part 5, so the rest of the Polar run (including Part 5.4 on page 1.50 and everything after) used **Insert > Problem** (pages 2.1, 2.2, 2.3).
- Entry of `ⅈ` and `ⅇ`: typed as `@i` and `@e` (the keyboard's imaginary-unit and e-constant entry). They display as italic bold ⅈ and bold ⅇ and behave as the constants (not variables). The symbols palette was not used. `sqrt(` was typed as text and shows as √. `root(-8,3)` was typed as text (it displays as ³√); the nth-root **template** was not used. Powers were typed as `(-8)^(1/3)`, shown as (-8) to the power 1/3 (the exponent is a stacked fraction). Negative numbers at the start of a line were entered with the (−) key (a typed `-` at the start of a line becomes `Ans-`).
- **Absolute precision note:** results are copied from the screenshots by eye. Where a result was wider than the screen it is cut off with a small arrow on the right; I say so, and I did not scroll sideways to read the rest.

## How the screenshots were taken (deviation from the capture note)
The capture note asks for one screenshot per input per mode. I took **one screenshot per group of 2 to 6 inputs per mode** (history showing input and result together), because the history shows several lines at once. File names are `D<part>-<short-name>-<mode>.png` with an `-a`/`-b` suffix when a group needed a scroll (a = top, b = bottom). They are in `docs/testing/domain-shots/`, cropped to the handheld screen. Dialog text was shot once per kind (`D1-sqrt-neg-real-dialog.png`, `D3-real-imag-sqrt-real-warning.png`, `D5-list-sqrt-real-dialog.png`); every "Non-real result" dialog had the identical text (below), so I did not shoot it for every input. No input was missing a screenshot of its result line, with the exceptions listed under "Not tested / gaps".

## The Real-mode error dialog (exact text, same for every error below)
Title **Error**. Text:

> Non-real result
>
> For example, if the software is in the Real setting, √(−1) is invalid.
> To allow complex calculations, change the "Real or Complex" Mode Setting to RECTANGULAR or POLAR.

Button OK. The history line then reads `"Error: Non-real result"` (a string, shown with quote marks) in the result column, and the entry stays in the history. **The dialog shows after Return; text typed while it is open is lost** (and an extra Return on an empty line re-runs the previous entry).

**Warning triangle** (a yellow triangle at the left of the entry in the history; clicking it opens a dialog titled **Warning** with the text **"Non-real calculation"**, button OK). Triangles appeared only in Real mode, and only on the entries marked ⚠ below. No triangle appeared in Rectangular or Polar anywhere.

## Part 1. Square roots and powers of negatives
Screenshots: `D1-sqrt-neg-{real,rect,polar-a,polar-b}`, `D1-pow-half-real`, `D1-cuberoot-real`, `D1-cuberoot-sqrtx-{rect-a,rect-b,polar-a,polar-b}`, `D1-sqrt-x-and-products-real`, `D1-sqrt-products-real-warning`, `D1-sqrt-products-and-log-rect-a`, `D1-products-ln-polar-a`.

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `√(-1)` | Error: Non-real result (dialog) | ⅈ | ⅇ^(ⅈ·π/2) (stacked exponent: ⅈ·π over 2) |
| `√(-4)` | Error: Non-real result | 2·ⅈ | ⅇ^(ⅈ·π/2)·2 |
| `√(-8)` | Error: Non-real result | 2·√2·ⅈ | ⅇ^(ⅈ·π/2)·2·√2 |
| `(-4)^(1/2)` | Error: Non-real result | 2·ⅈ | ⅇ^(ⅈ·π/2)·2 |
| `(-1)^(1/2)` | Error: Non-real result | ⅈ | ⅇ^(ⅈ·π/2) |
| `(-8)^(1/3)` | **-2** | 1+√3·ⅈ | ⅇ^(ⅈ·π/3)·2 |
| `root(-8,3)` (typed; shows ³√-8) | **-2** | 1+√3·ⅈ | ⅇ^(ⅈ·π/3)·2 |
| `(-8)^(2/3)` | **4** | -2+2·√3·ⅈ | ⅇ^(2·ⅈ·π/3)·4 |
| `√x` (x undefined) | √x | √x | √x |
| `√(-x)` | √-x (shown √ over -x) | √-x | √-x |
| `√(-1)·√(-1)` | **-1, ⚠ warning triangle** (no error dialog) | -1 | -1 |
| `(√(-1))^2` | **-1, ⚠ warning triangle** | -1 | -1 |

Notes:
- The Real-mode `√x` and `√(-x)` entries return unchanged in all three modes (no domain assumption, no warning).
- In Real mode the two product/square entries do **not** raise the error even though each factor alone does. The warning text is "Non-real calculation" (`D1-sqrt-products-real-warning.png`).
- In Real mode `(-8)^(1/3)` is the real cube root, `-2`, and `(-8)^(2/3)` is `4`. In Rectangular they are the principal complex values.

## Part 2. Logs, exponentials and inverse functions
Screenshots: `D2-log-neg-{real,rect}`, `D1-products-ln-polar-a`, `D2-log-polar-b`, `D2-arc-out-of-range-real`, `D2-arcsin-arccos-2-{rect,polar}`, `D2-arccosh-arctanh-arcsin-neg2-rect`, `D2-arccosh-arctanh-polar`, `D2-arcsin-neg2-polar`, `D2-eipi-ln0-lni-{real,rect,polar}`.

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `ln(-1)` | Error: Non-real result | π·ⅈ | ⅇ^(ⅈ·π/2)·π |
| `ln(-2)` | Error: Non-real result | ln(2)+π·ⅈ | ⅇ^(ⅈ·tan⁻¹(π/ln(2)))·√((ln(2))²+π²) (as displayed; the sqrt covers (ln(2))²+π²) |
| `log(-1)` (shown log₁₀(-1)) | Error: Non-real result | π·log₁₀(ⅇ)·ⅈ | cut off at the right edge (an ⅇ^(ⅈ·π/2) factor and "·π·log₁₀(ⅇ)" seen; rest not read) |
| `log(-100,10)` (shown log₁₀(-100)) | Error: Non-real result | 2+π·log₁₀(ⅇ)·ⅈ | cut off at the right edge: ⅇ^(ⅈ·tan⁻¹(π·log₁₀(ⅇ)/2))·√(π²·(log₁₀(ⅇ))²+4 … (rest not read) |
| `arcsin(2)` (shown sin⁻¹(2)) | Error: Non-real result | π/2 − (ln(4·√3+7)/2)·ⅈ | cut off: ⅇ^(-ⅈ·tan⁻¹(ln(4·√3+7)/π))·√((ln(4·√3+7))²+π² … (rest not read) |
| `arccos(2)` | Error: Non-real result | (ln(4·√3+7)/2)·ⅈ | ⅇ^(ⅈ·π/2)·ln(4·√3+7)/2 |
| `arccosh(0)` | Error: Non-real result | π/2·ⅈ | ⅇ^(ⅈ·π/2)·π/2 |
| `arctanh(2)` | Error: Non-real result | ln(3)/2 − π/2·ⅈ | ⅇ^(-ⅈ·tan⁻¹(π/ln(3)))·√((ln(3))²+π²)/2 |
| `arcsin(-2)` | Error: Non-real result | -π/2 + (ln(4·√3+7)/2)·ⅈ | cut off: ⅇ^(ⅈ·(tan⁻¹(π/ln(4·√3+7))+π/2))·√((ln(4·√3+7)) … (rest not read) |
| `ⅇ^(ⅈ·π)` | **-1** (no warning) | -1 | -1 |
| `ln(0)` | undef | undef | undef |
| `ln(ⅈ)` | **π/2·ⅈ** (no warning) | π/2·ⅈ | ⅇ^(ⅈ·π/2)·π/2 |

Notes:
- Every Real-mode error in this part is the same dialog (the one quoted above, which cites √(−1) even for ln and arcsin).
- With a **literal ⅈ** in the input (`ⅇ^(ⅈπ)`, `ln(ⅈ)`) Real mode returns a complex value with no error and no triangle.
- Display forms: inverse functions show as `sin⁻¹(2)`, `cosh⁻¹(0)`, `tanh⁻¹(2)` in the history.
- ln(0) gives the word `undef` in all modes.

## Part 3. The imaginary unit typed directly
Screenshots: `D3-i-basic-{real,real-b,rect,polar-a,polar-b}`, `D3-abs-real-imag-conj-angle-{real,rect}`, `D3-abs-real-polar`, `D3-imag-conj-angle-polar`, `D3-real-imag-sqrt-and-products-{real,rect,polar}`, `D3-real-imag-sqrt-real-warning`.

**3.1**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `ⅈ` | ⅈ | ⅈ | ⅇ^(ⅈ·π/2) |
| `3+4ⅈ` | 3+4·ⅈ | 3+4·ⅈ | ⅇ^(ⅈ·(π/2 − tan⁻¹(3/4)))·5 |
| `ⅈ^2` | -1 | -1 | -1 |
| `ⅈ·ⅈ` | -1 | -1 | -1 |
| `(1+ⅈ)^2` | 2·ⅈ | 2·ⅈ | ⅇ^(ⅈ·π/2)·2 |
| `1/ⅈ` | -ⅈ | -ⅈ | ⅇ^(-ⅈ·π/2) |

**3.2**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `abs(3+4ⅈ)` (shown \|3+4·ⅈ\|) | 5 | 5 | 5 |
| `real(3+4ⅈ)` | 3 | 3 | 3 |
| `imag(3+4ⅈ)` | 4 | 4 | 4 |
| `conj(3+4ⅈ)` | 3−4·ⅈ | 3−4·ⅈ | ⅇ^(ⅈ·(2·tan⁻¹(3/4) − π)/2)·5 (exponent: ⅈ·(2·tan⁻¹(3/4)−π) over 2) |
| `angle(3+4ⅈ)` | π/2 − tan⁻¹(3/4) | π/2 − tan⁻¹(3/4) | π/2 − tan⁻¹(3/4) |

`angle` returns a plain real number in every mode (never in polar form). No warning triangles in 3.1 or 3.2.

**3.3 (the existing-case check)**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `real(3+4·√(-1))` | **3, ⚠ triangle** | 3 | 3 (not shown in the Polar run's top row; the top line of the screenshot reads `real(3+4·√-1)` = 3) |
| `imag(3+4·√(-1))` | **4, ⚠ triangle** | 4 | 4 |

Confirmed: in Real mode the two entries return 3 and 4 with a warning triangle each, and no error dialog. Clicking the triangle gives **Warning: "Non-real calculation"** (OK button). No triangle in Rectangular or Polar.

**3.4**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `(3+4ⅈ)·(1−2ⅈ)` | 11−2·ⅈ | 11−2·ⅈ | ⅇ^(-ⅈ·tan⁻¹(2/11))·5·√5 |
| `(3+4ⅈ)/(1−2ⅈ)` | -1+2·ⅈ | -1+2·ⅈ | ⅇ^(ⅈ·(tan⁻¹(1/2)+π/2))·√5 |

## Part 4. Solving
Screenshots: `D4-solve-cSolve-{real-a,real-b,rect-a,polar-a}`, `D4-zeros-factor-solve-rect-b`, `D4-cSolve-polar-b`, `D4-factor-cFactor-solve-polar`.

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `solve(x²+1=0,x)` | **false** | **false** | **false** |
| `solve(x²=-4,x)` | false | false | false |
| `cSolve(x²+1=0,x)` | x=ⅈ or x=-ⅈ | x=ⅈ or x=-ⅈ | x=ⅇ^(ⅈ·π/2) or x=ⅇ^(-ⅈ·π/2) |
| `cSolve(x³=1,x)` | x=-1/2+√3/2·ⅈ or x=-1/2−√3/2·ⅈ or x=1 (fractions stacked) | same as Real | x=ⅇ^(2·ⅈ·π/3) or x=ⅇ^(-2·ⅈ·π/3) or x=1 |
| `zeros(x²+1,x)` | empty list, drawn as `{▢}` (a dashed empty box inside braces) | same drawing (top of screenshot partly cut; same look) | partly cut off at the top of the screenshot; the visible part is the second line of a list with ⅇ-exponent items (see cZeros). **Not clearly read; treat as untested in Polar.** |
| `cZeros(x²+1,x)` | {ⅈ,-ⅈ} | {ⅈ,-ⅈ} | {ⅇ^(ⅈ·π/2), ⅇ^(-ⅈ·π/2)} (the visible second line shows "ⅇ^(…/2), ⅇ^(…/2)" in braces; the first row is cut off) |
| `factor(x²+1)` | x²+1 | x²+1 | x²+1 |
| `cFactor(x²+1)` | (x−ⅈ)·(x+ⅈ) | (x−ⅈ)·(x+ⅈ) | (x+ⅇ^(-ⅈ·π/2))·(x+ⅇ^(ⅈ·π/2)) |
| `solve(x²+2x+5=0,x)` | false | false | false |

So `solve` is **real-only in all three settings** (returns `false` when there is no real root; it does not switch to complex roots in Rectangular or Polar). `cSolve`, `cZeros`, `cFactor` work in every setting, including Real, and only their display form changes in Polar. `zeros` returned an empty list in Real and Rectangular (empty-list drawing seen; I did not check `dim()`).

## Part 5. How results are displayed
Screenshots: `D5-negatives-{real,rect}`, `D5-negatives-and-3plus4i-polar`, `D5-polar-inputs-{real,rect,polar-b}`, `D5-neg3-1plusi-polar`, `D5-approx-matrix-real`, `D5-approx-list-matrix-{rect,polar}`, `D5-approx-3plus4i-polar`, `D5-degree-polar`.

**5.1 negative reals** (entered with the (−) key): `-3` → -3, `-√2` → -√2, `-1` → -1, identical in all three modes (Polar shows the real negatives unchanged; for Polar `-3` and `-1` were read, `-√2` was cut at the top of the Polar screenshot and is not confirmed in Polar).

**5.2 complex numbers**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `3+4ⅈ` | 3+4·ⅈ | 3+4·ⅈ | ⅇ^(ⅈ·(π/2 − tan⁻¹(3/4)))·5 |
| `-3` | -3 | -3 | -3 |
| `ⅈ` | ⅈ | ⅈ | ⅇ^(ⅈ·π/2) |
| `1+ⅈ` | 1+ⅈ | 1+ⅈ | ⅇ^(ⅈ·π/4)·√2 |
| `-1-ⅈ` | -1−ⅈ | -1−ⅈ | ⅇ^(-3·ⅈ·π/4)·√2 |
| `2·ⅇ^(ⅈ·π/3)` | 1+√3·ⅈ (input shown 2·ⅇ^(ⅈ·π/3)) | 1+√3·ⅈ | ⅇ^(ⅈ·π/3)·2 |

So in Polar the **modulus is written after the exponential** (`ⅇ^(ⅈθ)·r`), the exponent is a stacked fraction, the angle is in radians, and exact angles come out exact (π/4, 3π/4 negative). A negative real stays `-3` (not `ⅇ^(ⅈπ)·3`).

**5.3 Approximate (ctrl+Enter), Auto calculation mode, Radian**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `3+4ⅈ` ctrl+Enter | 3.+4.·ⅈ | 3.+4.·ⅈ | ⅇ^(0.92729522·ⅈ)·5. |
| `1+ⅈ` ctrl+Enter | 1.+ⅈ | 1.+ⅈ | ⅇ^(0.78539816·ⅈ)·1.4142136 |

In Polar the angle is in **radians** (0.92729522, 0.78539816), shown as an ordinary number in the exponent, followed by the modulus (5., 1.4142136). (In Real and Rectangular the "1." keeps its decimal point and the imaginary part of 1+ⅈ stays a bare ⅈ.)

**5.4 Polar with Angle = Degree.** I changed Angle to Degree in Document Settings (title bar read DEG), ran, then **changed it back to Radian** (title bar RAD again; checked).

| Input | Polar, Degree |
|---|---|
| `3+4ⅈ` | (5 ∠ 90−tan⁻¹(3/4)) |
| `ⅈ` | (1 ∠ 90) |
| `3+4ⅈ` with ctrl+Enter | (5. ∠ 53.130102) |

In Degree mode Polar uses the **(r ∠ θ)** notation with the angle in degrees, shown in round brackets, instead of ⅇ^(ⅈθ). The exact angle shown as `90−tan⁻¹(3/4)` means tan⁻¹ is in degrees there. (This page was page 1.50 in a document that already had earlier rows above; the screenshot `D5-degree-polar.png` shows these three rows plus the earlier radian approx row.)

**5.5 lists and matrices**

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `{1,√(-1)}` | **Error: Non-real result** (dialog; shot `D5-list-sqrt-real-dialog`) | input echoed {1,√-1}, result {1,ⅈ} | input echoed {1,√-1}, result {1, ⅇ^(ⅈ·π/2)} |
| `[1,ⅈ;0,1]` (matrix; ⅈ typed `@i`) | matrix [[1,ⅈ],[0,1]] | [[1,ⅈ],[0,1]] | [[1, ⅇ^(ⅈ·π/2)],[0, 1]] (the 1s as is, the ⅈ entry in polar form) |

So lists and matrices are converted element by element. In Real, a literal ⅈ inside a matrix is fine; a `√(-1)` inside a list raises the same error as outside.

## Part 6. Calculation Mode Approximate
Calculation Mode set to **Approximate** in Document Settings (checked in the dialog), run, then set back to Auto. Screenshots: `D6-approx-{real,rect,polar}`.

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `√(-4)` | Error: Non-real result (dialog) | 2.·ⅈ | ⅇ^(1.5707963·ⅈ)·2. |
| `ln(-1)` | Error: Non-real result | 3.1415927·ⅈ | ⅇ^(1.5707963·ⅈ)·3.1415927 |
| `(-8)^(1/3)` | **-2.** | 1.+1.7320508·ⅈ | ⅇ^(1.0471976·ⅈ)·2. |
| `3+4ⅈ` | 3.+4.·ⅈ | 3.+4.·ⅈ | ⅇ^(0.92729522·ⅈ)·5. |

Approximate mode changes only the number format (decimals, trailing "."); it does not change which inputs raise the error in Real mode.

## Part 7. Anything else
Screenshots: `D7-fmin-fmax-nsolve-real`, `D7-solve-complex-sqrti-real`, `D7-fmax-nsolve-solve-sqrti-{rect,polar}`.

| Input | Real | Rectangular | Polar |
|---|---|---|---|
| `fMin(x²+1,x)` | x=0 | not seen (scrolled off the top) | not seen (scrolled off the top) |
| `fMax(x²+1,x)` | x=-∞ or x=∞ | x=-∞ or x=∞ | x=-∞ or x=∞ |
| `nSolve(x²+1=0,x)` | "No solution found" (a string result, no dialog) | "No solution found" | "No solution found" |
| `solve(x²=ⅈ,x)` (complex coefficient) | false | false | false |
| `√ⅈ` | √2/2+√2/2·ⅈ (stacked fractions) | same | ⅇ^(ⅈ·π/4) |

- None of these raised the Real-mode error dialog. `fMin(x²+1,x)` = x=0 (Real) was the only fMin I saw.
- In the Real-mode run I also typed `(-8)^(1/3)*ⅈ`, which the entry line took as `(-8)^((1/3)·ⅈ)` (the `*ⅈ` stayed inside the exponent). Real mode returned `2^ⅈ·ⅇ^(-π/3)` with no warning and no error. This was a typing slip, not a planned case; it is in `D7-solve-complex-sqrti-real.png` (bottom row).
- I did not find any function where Real raises the "Non-real result" error but a literal-ⅈ input does not, other than what is in Parts 1 and 2 (the errors depend on whether a real-only function is given a value outside its real domain, not on whether ⅈ appears).

## Summary for Simon

**Which functions raise "Non-real result" in Real mode** (all with the same dialog text and a `"Error: Non-real result"` string in the history):
- `√` of a negative number (`√(-1)`, `√(-4)`, `√(-8)`);
- an even-denominator fractional power of a negative number (`(-4)^(1/2)`, `(-1)^(1/2)`);
- `ln` and `log` of a negative number (`ln(-1)`, `ln(-2)`, `log(-1)`, `log(-100,10)`);
- inverse trig and inverse hyperbolic functions outside their real domain (`arcsin(2)`, `arccos(2)`, `arccosh(0)`, `arctanh(2)`, `arcsin(-2)`);
- a list containing `√(-1)` (`{1,√(-1)}`).
- The same happens in Real with Approximate calculation mode.

**Which return complex or odd results anyway in Real mode:**
- Odd-denominator powers of negatives return the **real** root: `(-8)^(1/3) = -2`, `root(-8,3) = -2`, `(-8)^(2/3) = 4`. In Rectangular these become 1+√3ⅈ, 1+√3ⅈ and −2+2√3ⅈ.
- Anything with a typed ⅈ is evaluated normally with no warning: `ⅈ`, `3+4ⅈ`, `ⅈ²`, `(1+ⅈ)²`, `1/ⅈ`, products and quotients, `abs/real/imag/conj/angle`, `ⅇ^(ⅈπ) = -1`, `ln(ⅈ) = π/2·ⅈ`, `√ⅈ`, `2ⅇ^(ⅈπ/3) = 1+√3ⅈ`, and a matrix containing ⅈ.
- `√(-1)·√(-1)` and `(√(-1))²` return **-1 with a "Non-real calculation" warning triangle** (no error), and `real(3+4·√(-1))`, `imag(3+4·√(-1))` return 3 and 4 with the triangle. So the error comes from a single `√(-1)` being evaluated alone, while one used inside a product, power or `real`/`imag` gives a value plus a warning.
- `cSolve`, `cZeros`, `cFactor` work normally in Real mode.
- `ln(0)` is `undef` in all modes. `fMax(x²+1,x)` gives `x=-∞ or x=∞`, `nSolve(x²+1=0,x)` gives the string "No solution found", and `solve` with no real solutions gives `false`, in every mode.

**What differs between Real and Rectangular (beyond the errors):**
- The warning triangles disappear in Rectangular.
- Odd roots of negatives are real in Real and the principal complex value in Rectangular (see above).
- Everything else I compared gave identical results: the literal-ⅈ arithmetic, `abs/real/imag/conj/angle`, `cSolve`/`cZeros`/`cFactor`, **`solve` (still real-only and still `false` when no real roots exist)**, `zeros` (empty list), `fMax`/`nSolve`/`√ⅈ`, and the display of negative reals.

**What Polar changes:**
- Only the display of complex results: they appear as `ⅇ^(ⅈθ)·r` (modulus after the exponential, angle in radians, exact angles kept exact, e.g. ⅇ^(ⅈ·π/4)·√2). Real numbers (including negative reals like -3 and -1) are left alone, and so are `abs`, `real`, `imag`, `angle` (these return real numbers). Complex results of lists and matrices are converted element by element.
- Some results get long (logs and inverse trig of out-of-range reals) and run off the right edge of the screen.
- Approximate gives ⅇ^(0.92729522·ⅈ)·5. (angle in radians).
- With **Angle = Degree** Polar changes to `(r ∠ θ)` notation: (5 ∠ 90−tan⁻¹(3/4)), (1 ∠ 90), and (5. ∠ 53.130102) approximate.
- `solve` is still real-only in Polar (returns `false`), and `cSolve` / `cFactor` / `cZeros` results are shown in the ⅇ^(ⅈθ) form.

**Surprising:**
1. Real mode is not a pure "reject complex" mode. It rejects a real-only function whose argument is outside its real domain when it is evaluated on its own, but a `√(-1)` combined in a product or power, or inside `real(...)`/`imag(...)`, comes through with a warning, and a literal ⅈ is accepted anywhere with no warning.
2. `solve` never returns complex roots, even in Rectangular and Polar. `cSolve` does.
3. In Real mode `(-8)^(2/3) = 4` and `(-8)^(1/3) = -2`.
4. Polar mode prints `ⅇ^(ⅈθ)·r`, not "r ∠ θ", unless Angle is Degree.
5. `ln(0)` is `undef`, not an error, in all modes.

## Not tested / gaps (please read)
- **Screenshots are per group, not per input and mode** (see above). Individual inputs are therefore not on their own `D<part>-<name>-<mode>.png`.
- The nth-root **template** (the templates key) was not used; `root(-8,3)` was typed. `real`, `imag` on a typed `√(-1)` were typed linearly. The templates key was not used for anything in this run.
- Warning-triangle text was opened only for the Real-mode `√(-1)·√(-1)` row and the `real(3+4√(-1))` row (same text both times, "Non-real calculation"); I did not click the triangle on `(√(-1))^2` or `imag(...)`; they look identical.
- Wide Polar results were cut off at the right: `log(-1)`, `log(-100,10)`, `arcsin(2)`, `arcsin(-2)`; the first part of each was read, the rest was not.
- `zeros(x²+1,x)` was partially hidden at the top of the Rectangular and Polar screenshots. Real is read as an empty list; Rectangular looks the same; Polar is not confirmed.
- `-√2` in Polar and `fMin(x²+1,x)` in Rectangular and Polar scrolled off the top and were not read. `abs`/`real` rows in Polar were checked in a separate page.
- Part 5.4 (Degree) was run only for Polar, as the capture note asks. Real and Rectangular were not run in Degree.
- Part 7 is limited to the five functions above, plus the one accidental typing case.
- State at the end: Document Settings left at **Polar / Radian / Auto / Float 8 / CAS On**; the document is unsaved ("Document1", problems 1 and 2). No other files were edited, nothing was committed.
