# Emulator templates results (TI-Nspire CX CAS Premium Teacher Software)

Run by Claude (computer use) for `emulator-templates-capture.md`. Settings used: Radian, Auto, Real, Float 8, CAS on. Handheld-page-size document, layout "keypad + side screen". Screenshots are in `docs/testing/template-shots/`, named `T<part>-<name>.png` (the file names are given in each section).

Rules I followed: report what I saw, no tidying. Where a screenshot is the only evidence and I could not read a detail, I say so.

## Not obtained: linear text (item b) for every template
The user did not grant clipboard read, so I could not read ctrl+C text. Pasting into a Notes page gives a typeset math box, not plain text. The only plain-text hints I have are the history display and the dialog-pasted lines in Part 2 (for example `linSolve(` and `deSolve(` lines, shown as typed text). **Item (b) is therefore not recorded for Part 1.** Part 1 items a, c and d are recorded.

Templates key at (237,485). Palette navigation: the palette opens on the last-used icon; arrows then Return are reliable, mouse clicks on icons sometimes insert immediately.

## Part 1

### 1. nth root (shots T1-1-nthroot-slots, -results, -keys, -backspace)
- a. Two slots, index (small, top-left) then radicand. Typing `3`, Tab, `8` gives ³√8 (cursor ends after the 8).
- c. ³√8 = 2. ³√−8 = −2. ²√−4 = "Error: Non-real result" (with the index typed as 2 the Real mode gives an error string, not a complex value).
- d. Right at the end of the radicand leaves the template: typed `3`, Tab, `75`, Right, `9` gave ³√75 followed by `9` outside the root (T1-1-nthroot-keys). Backspace in the empty template: the screenshot (T1-1-nthroot-backspace) shows a selected plain √▯ (empty box, highlighted); I did not press Backspace again to see whether the template then disappears.
- I did not test ctrl+^ separately.

### 2. Log with base (T1-2-log-empty, -filled, -result)
- a. Shows as `log▯(▯)`: the base is a small lower slot, then the argument in brackets. Base first, Tab, argument.
- c. log base 2 of 8 = 3.
- d. Not recorded separately.
- I did not test ctrl+10ˣ.

### 3. e^□ (T1-3-exp-empty, -filled, -results, -ekey)
- a. One slot, the exponent.
- c. `e^2` stays `e²` (exact); ctrl+Enter gives 7.3890561.
- The eˣ key (32,547) was also tried (T1-3-ekey).

### 4. Piecewise (T1-4-*)
- 2 pieces, slots: a 2-row brace with `▯,▯` on each row (value, condition). Tab visits value1, condition1, value2, condition2 (checked with 1..6 on the 3-piece version: order is row by row).
- Filled with `x^2`, `x<0`, `x`, `x>=0` (typing `>=` is shown as ≥ after Enter). Result echoes the piecewise: `{x²,x<0 ; x,x≥0}`.
- `f(x):=` that piecewise gives "Done"; f(−3) = 9; f(3) = 3.
- N-piece version: dialog "Create Piecewise Function" with one field "Number of function pieces" (spinner, default looked like 3, partly obscured in the shot). It inserts that many `▯,▯` rows. Pasted/typed check with 3 pieces: `1,2 / 3,4 / 5,6` then 7 outside (T1-4-piecewiseN-*).

### 5. System of equations (T1-5-*)
- 2-equation template: 2 rows, one slot each. Tab goes row 1 then row 2. Alone: `{x+y=3 ; x−y=1}` gives the list `{x+y=3,x−y=1}`.
- Inside `solve(` … `,{x,y})`: gives `x=2 and y=1`.
- N-equation version: dialog "Create a System of Equations", one field "Number of equations" (spinner, default looked like 3). Inserts that many one-slot rows (T1-5-systemN-*). Typed `1`, Tab, `2`, then `3` after leaving: shows 1 over 2 then 3 outside (2-row test).

### 6. Absolute value (T1-6-abs)
- One slot, shown as bars `|▯|`. `|−5|` = 5.

### 7. Degrees-minutes-seconds (T1-7-dms-*)
- Three slots, shown `▯°▯'▯"`. Typed 30, 15, 0 gives `30°15'0"`.
- In **Radian** mode the result is `121·π/720` (exact radians: 30.25° converted). I did not run it in Degree mode.

### 8. Matrices (T1-8-matrix-*)
- 1×2: slots row-wise. Typed 1, Tab, 2, then 3 outside: `[1 2]3`.
- 2×1: `[1;2]` with 3 outside after leaving.
- 2×2: filled 1,2,3,4 in row-major order, then 5 outside.
- m×n: dialog "Create a Matrix", fields "Number of rows" then "Number of columns" (default 3 and 3 looked like). OK inserts an empty m×n grid (I saw a 5-row, 2-column grid with empty boxes).

### 9. Σ and Π (T1-9-*)
- Σ slots (typed 1,2,3,4,5 and read the shot): the shown result was `Σ` with lower `1=2`, upper `3`, body `(4)`, and the 5 outside. So Tab order is **variable, lower bound, upper bound, expression**.
- Σ k=1..10 of k² = 385. Π k=1..5 of k = 120.
- Π: same four-slot layout (shown for k).

### 10. Derivatives (T1-10-*)
- First derivative d/d▯: shown `d/dx(▯)`. With `x^3` gives 3·x².
- Second derivative: `d²/dx²(x^4)` gives 12·x².
- Nth derivative: shows `d` with a small superscript box over `dx`, and a body box. In the empty state (T1-10-derivN-slots) I could see the superscript order box and the body box; I could not tell whether the denominator exponent has its own slot. Run with order 3 and `x^5`: `d³/dx³(x⁵)` = 60·x².
- Variable slot of the first/second derivative templates: the screenshots show `dx` already in the template (I typed the x in the variable slot); I did not record whether it is a separate slot.

### 11. Integrals (T1-11-*)
- Definite: slots typed 1,2,3,4,5 gave `∫` lower 1, upper 2, integrand 3, `d`4, then 5 outside. **Order: lower, upper, integrand, variable.**
- ∫₀¹ x² dx = 1/3.
- Indefinite: `∫x² dx` = `x³/3` (no constant of integration shown).

### 12. Limit (T1-12-*)
- Typed 1,2,3,4: shows `lim` over `1→2` with a small superscript `3` after the limit value and `(4)` as the body. **Order: variable, limit value, direction (superscript), expression.** (Typing the expression into the 3rd slot gave "Syntax" the first time.)
- lim x→0 sin(x)/x = 1.
- Direction slot exists: with `+` in it, `lim x→0⁺ |x|/x` = 1 (shown `0⁺`).

### 13. Subscript (T1-13-*)
- A subscript template on a variable: `a` then subscript `1`.
- It displays `a₁`. Evaluated alone it stays `a₁` (undefined variable).
- After `a_1:=7` (typed underscore): `a_1+1` = 8, but the template `a₁+1` stays `a₁+1` unevaluated in my run. So in this run the template subscript and a typed `a_1` were **not** the same variable. (One earlier entry in the history showed `a₂` echoing as `a₂`.)

## Part 2

### Doc > Insert, items after A Widget (T2-1-*)
See the four shots `T2-1-insert-tail-a`, `-b`, `T2-1-program-editor-submenu`, `T2-1-add-python-submenu`. The tail has a Program Editor submenu and an Add Python submenu; the full lettered list is in those shots (I did not transcribe it into text).

### Algebra > 7 > 2 Solve System of Linear Equations (T2-2-*)
- Dialog "Solve a System of Linear Equations": "Number of equations" (spinner, default 2) and "Variables" (default `x,y`), hint "Enter variable names separated by commas", OK and Cancel.
- Pastes `linSolve({▯,▯},{x,y})` using the 2-row system template (cursor starts in slot 1; Tab to slot 2). Empty it gives Error "Syntax".
- x+y=3, x−y=1 gives `{2,1}`.

### Distributions (T2-3-*)
Menu path on this emulator is **6 Statistics > 5 Distributions** (not Probability). Items: 1 Normal Pdf, 2 Normal Cdf, 3 Inverse Normal, 4 t Pdf, 5 t Cdf, 6 Inverse t, 7 χ² Pdf, 8 χ² Cdf, 9 Inverse χ², A Binomial Pdf, B Binomial Cdf, C Inverse Binomial, D Inverse Binomial N, E F Pdf, F F Cdf, G Inverse F, H Geometric Pdf, I Geometric Cdf, J Poisson Pdf, K Poisson Cdf (and I saw nothing more below K).
- Each dialog: fields are filled with Tab; pressing Return once moves to OK, a second Return pastes **and evaluates** the line.
- **t Cdf**: Lower Bound (default `−∞`), Upper Bound (empty), Deg of Freedom df (empty). −1, 1, 5 pastes `tCdf(-1,1,5)` = 0.63678253.
- **χ² Cdf**: Lower Bound (default `0`), Upper Bound, Deg of Freedom df. 0, 3, 2 pastes `χ²Cdf(0,3,2)` = 0.77686984.
- **F Cdf**: Lower Bound (default `0`), Upper Bound, Numerator df, Denominator df. 0, 2, 3, 4 pastes `FCdf(0,2,3,4)` = 0.7436128.
- **Binomial Cdf** dialog (seen for reference): Num Trials n, Prob Success p, Lower Bound (default 0), Upper Bound.

### Inverse Binomial C and D (T2-4-*)
- **C Inverse Binomial**: dialog titled "Num Successes": Cumulative Prob, Num Trials n, Prob Success p, and a "Display Result: Matrix Form" checkbox. 0.5, 10, 0.5 pastes `invBinom(0.5,10,0.5)` = 5.
- **D Inverse Binomial N**: dialog titled "Num Trials": Cumulative Prob, Prob Success p, Successes x, and the Matrix Form checkbox. 0.5, 0.5, 5 pastes `invBinomN(0.5,0.5,5)` = 12.

### Functions & Programs > 8 Mode (T2-5-*)
Functions & Programs is menu 9; its items: 1 Program Editor, 2 Func…EndFunc, 3 Prgm…EndPrgm, 4 Local, 5 Control, 6 Transfer, 7 I/O, 8 Mode, 9 Add New Line.
Mode items: 1 Display Digits, 2 Angle, 3 Exponential Format, 4 Real or Complex, 5 Auto or Approx, 6 Vector Format, 7 Base, 8 Unit System, 9 Get Mode, A Get Language Info, B Get Platform Info.
- Display Digits: 1 Float, 2 Float1 … 9 Float8, A Float9, then B Float10, C Float11, D Float12, then E Fix0 … Q Fix12 (Fix3 is H, Fix12 is Q; I saw H to Q and 1 to A directly).
- Angle: 1 Radian, 2 Degree, 3 Gradian.
- Exponential Format: 1 Normal, 2 Scientific, 3 Engineering.
- Real or Complex: 1 Real, 2 Rectangular, 3 Polar.
- Auto or Approx: 1 Auto, 2 Approximate, 3 Exact.
- Vector Format: 1 Rectangular, 2 Cylindrical, 3 Spherical.
- Base: 1 Decimal, 2 Hex, 3 Binary.
- Unit System: 1 SI, 2 Eng/US.

### Algebra > 8 Polynomial Tools (T2-6-*)
8 items only: 1 Find Roots of Polynomial…, 2 Real Roots, 3 Complex Roots, 4 Remainder, 5 Quotient, 6 Greatest Common Divisor, 7 Coefficients, 8 Degree. Pressing Down 12 times wrapped round to item 5, with no scroll arrow, so nothing follows 8.

### Finance Solver (T2-7-*)
- Open: Finance (menu 8) > 1 Finance Solver. Fields seen: N, I(%), PV, Pmt, FV (default 0 each), PpY, CpY (default 1); I did not scroll further, so I did not see a PmtAt field.
- N=10, I=5, PV=−1000, Pmt=0, cursor on FV, Enter gives FV = 1628.8946267774 and the status "Finance Solver info stored into tvm.n, tvm.i, tvm.pv, tvm.pmt, ...".
- **Changing PpY changes CpY**: with CpY at 1, setting PpY to 4 made CpY show 4 (PpY and CpY stay equal). Solving N with PpY=CpY=4 gave 39.275577077031.
- After solving, the Var list holds (autocomplete after `tvm.`): `cpy, fv, i, n, pmt, pmtat, ppy, pv`. Values read back: tvm.n = 39.275577 (after the solve for N), tvm.i = 5, tvm.pmt = 0., tvm.pmtat = 0, tvm.cpy = 4, tvm.ppy = 4, tvm.pv = −1000. I did not re-read tvm.fv as text, the solver showed 1628.8946.
- Note: after `tvm.` the autocomplete swallows typed names: pick from the list with Down and Return instead.

### Calculus > D Differential Equation Solver (T2-8-*)
- Dialog "Differential Equation Solver": Equation (example `y' = 2y`), Independent Var, Dependent Var, Condition (Optional), Condition (Optional) (example `y(0) = 1`). There is a scrollbar; I saw nothing else below.
- With `y'=2y`, `x`, `y`, `y(0)=1` it pastes `deSolve(y'=2·y and y(0)=1,x,y)` and gives `y=e^(2·x)`. Return once goes to OK, the second Return pastes and evaluates.

## Which parts were run
- Part 1: all 13 templates run for items a, c and d (some d items incomplete as noted). Item b (linear text) **not obtained**.
- Part 2: all eight items run. The Insert tail is in screenshots only, not transcribed.
