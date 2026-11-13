# Emulator check 6, run 3: Part B, Calculator leftovers (calc4)

Handheld CX II-T CAS, Teacher Software 6.0.3.374, Keypad + SideScreen at 250%. New document (Document12), Document Settings read: Display Digits Float 8, Angle Radian, Real or Complex Real, Calculation Mode Auto, CAS Mode On. Screenshots are in `pages-shots-6/` (cropped to the handheld screen). One entry per row unless stated.

## simulator-todo.md section A. Input and parsing

### A1: `2 3`
Settings: Radian, Auto, Real, Float 8
Keys: computer keyboard: `2 3` (a space between), Return
Observed: history row `2· 3` with result `6`. No error. (A space between two numbers is read as a product.)
Screenshot: pages-shots-6/B-A1-2-space-3.png
Differs from CASSim or from this file's expectation? yes, CASSim's guess was a syntax error.

### A2: `x 3`, `(x+1)2`
Settings: as above
Keys: computer keyboard, each followed by Return
Observed: `x 3` shows `x· 3` and the result `3· x`. `(x+1)2` shows `(x+1)· 2` and the result `2·(x+1)`.
Screenshot: pages-shots-6/B-A2a-x-space-3.png, pages-shots-6/B-A2b-paren-x1-2.png
Differs from CASSim or from this file's expectation? no (products).

### A3: `sin (0)`
Settings: as above
Keys: computer keyboard `sin (0)` (a space before the bracket), Return
Observed: history row `sin(0)`, result `0` (a call to sin).
Screenshot: pages-shots-6/B-A3-sin-space-0.png
Differs from CASSim or from this file's expectation? no.

### A4: `[1 2 3]`, `[1 -2]`
Settings: as above
Keys: computer keyboard, Return after each
Observed: `[1 2 3]` is displayed `[1· 2· 3]` with result `[6]` (one element, the product). `[1 -2]` is displayed `[1−2]` with result `[-1]` (one element, the difference).
Screenshot: pages-shots-6/B-A4a-bracket-1-2-3.png, pages-shots-6/B-A4b-bracket-1-minus-2.png
Differs from CASSim or from this file's expectation? yes, CASSim guessed 3 elements and 1 element; the device gives one element each time.

### A5: `+3`
Settings: as above (Ans was `[-1]`)
Keys: computer keyboard `+3`, Return
Observed: the row shows a warning triangle at its left, input `[-1]+3` (Ans put in front), result `[2]`. No error.
Screenshot: pages-shots-6/B-A5-plus-3.png
Differs from CASSim or from this file's expectation? yes, CASSim guessed a syntax error. A line starting with an operator gets the last answer in front.

### A6: `√4`
Settings: as above
Keys: computer keyboard, the typed character `√` then `4`, Return
Observed: dialog titled `Error` with the text `Missing (`; the entry line keeps `√4` with the caret after the 4.
Screenshot: pages-shots-6/B-A6-sqrt4.png
Differs from CASSim or from this file's expectation? no.

### A7: `x²`
Settings: as above
Keys: computer keyboard, typed character `²` after `x`, then Return
Observed: the entry line shows `x` with a small raised 2; Return gives dialog `Error` / `Syntax`.
Screenshot: pages-shots-6/B-A7a-x-superscript-typed.png, pages-shots-6/B-A7b-x-superscript-return.png
Differs from CASSim or from this file's expectation? no.

### A8: `(2∠π/4+1)`
Settings: Radian, Auto, Real
Keys: computer keyboard `(2∠π/4+1)`, Return
Observed: the input is drawn with tall brackets as `(2 ∠ π/4 +1)` (a stacked fraction); the result is `2·ⅇ^(ⅈ·(π/4+1))` (ⅇ and ⅈ in bold italic), so the angle is `π/4+1`.
Screenshot: pages-shots-6/B-A8-angle-paren.png
Differs from CASSim or from this file's expectation? no.

### A9: `2+3@>Rad`, and `@>` in mid-line
Settings: Radian
Keys: computer keyboard `2+3@>Rad`, Return; then `2+3@>Rad+4`, Return
Observed: first gives input `(2+3)▶Rad`, result `5ʳ`. Second gives dialog `Error` / `Syntax`; the entry line keeps `2+3@>Rad+4` with the caret before the 4.
Screenshot: pages-shots-6/B-A9a-to-rad.png, pages-shots-6/B-A9b-to-rad-midline.png
Differs from CASSim or from this file's expectation? no for the first; the mid-line case is a syntax error.

### A10: `a!=b`
Settings: as above
Keys: computer keyboard `a!=b`, Return
Observed: input shown `a!=b`, result shown `a!=b` (echoed, no error).
Screenshot: pages-shots-6/B-A10-a-not-equal-b.png
Differs from CASSim or from this file's expectation? not known; the result does not show whether it reads `a!` then `=b`.

### A11: `lu:=1`, `text:=1`, `wait:=1`, `fill:=1`
Settings: as above
Keys: computer keyboard, Return after each
Observed: each gives dialog `Error` / `Syntax`; the caret stays just after `:=`. None was accepted.
Screenshot: pages-shots-6/B-A11a-lu.png, B-A11b-text.png, B-A11c-wait.png, B-A11d-fill.png (all in pages-shots-6/)
Differs from CASSim or from this file's expectation? no (syntax error).

### A12: `5→a→b`
Settings: as above
Keys: computer keyboard, typed `→` characters, Return
Observed: dialog `Error` / `Syntax`; the caret sits before `b`.
Screenshot: pages-shots-6/B-A12-arrow-chain.png
Differs from CASSim or from this file's expectation? no.

## simulator-todo.md section B. Numbers and display

### B1: `0.002` and `0.0009` in Float 3
Settings: Document Settings Display Digits changed to Float 3 (list is Float, Float 1 to Float 12, Fix 0 to Fix 12); other settings as above
Keys: computer keyboard `0.002`, `0.0009`, and two extra values `0.00099`, `0.001`, Return after each
Observed: `0.002` shows `0.002`; `0.0009` shows `9.ᴇ-4`; `0.00099` shows `9.9ᴇ-4`; `0.001` shows `0.001`. The change to the `ᴇ` form is below 0.001.
Screenshot: pages-shots-6/B-B1a-float3-0.002.png, B-B1b-float3-0.0009.png, B-B1c-float3-0.00099.png, B-B1d-float3-0.001.png
Differs from CASSim or from this file's expectation? no.

### B2: `0.05` and `0.009` in Fix 2
Settings: Display Digits Fix 2
Keys: computer keyboard `0.05`, `0.009`, extra `0.005`, Return after each
Observed: `0.05` shows `0.05`; `0.009` shows `9.00ᴇ-3`; `0.005` shows `5.00ᴇ-3`.
Screenshot: pages-shots-6/B-B2a-fix2-0.05.png, B-B2b-fix2-0.009.png, B-B2c-fix2-0.005.png
Differs from CASSim or from this file's expectation? no.

### B3: `1ᴇ12` in Fix 2
Settings: Fix 2
Keys: computer keyboard `1@E12`, Return; then `1@E5`, Return
Observed: the input row shows `1000000000000.` and the result `1.00ᴇ12`. `1@E5` shows input `100000.` and result `100000.00`. So 10^12 is already in `ᴇ` form and 10^5 is fixed form.
Screenshot: pages-shots-6/B-B3-fix2-1e12.png, B-B3b-fix2-1e5.png
Differs from CASSim or from this file's expectation? no for 10^12; the upper limit of the fixed form lies between 10^5 and 10^12 (not narrowed further).

### B4: `1ᴇ5` in Auto
Settings: Float 8, Radian, Auto, Real
Keys: computer keyboard `1@E5`, Return
Observed: input row `100000.`, result `100000.` (a decimal, not an exact integer).
Screenshot: pages-shots-6/B-B4-auto-1e5.png
Differs from CASSim or from this file's expectation? no (CASSim gives the decimal).

### B5: `100°` in Gradian mode
Not run in this section; see the Gradian block below (A13 and B5).

### B6: `(-8)^(1/3)` in Real mode
Settings: Float 8, Radian, Auto, Real
Keys: computer keyboard `(-8)^(1/3`, then `)`, Return (the exponent drew as a stacked 1 over 3)
Observed: result `-2`.
Screenshot: pages-shots-6/B-B6-neg8-cuberoot.png
Differs from CASSim or from this file's expectation? yes (CASSim gives a complex root; the device gives -2).

### B7: `sqrt(-1)` in Real mode
Settings: Real
Keys: computer keyboard `sqrt(-1)`, Return
Observed: dialog titled `Error`, text `Non-real result` then a longer explanation (TI text, do not reuse): says that in the Real setting √(-1) is invalid and to change the "Real or Complex" setting to RECTANGULAR or POLAR. After OK the history row shows `√(-1)` with the result text `"Error: Non-real result"` and no warning triangle.
Screenshot: pages-shots-6/B-B7-sqrt-neg1-real.png
Differs from CASSim or from this file's expectation? yes (CASSim returns ⅈ with a warning triangle).

### B8: `90▶Rad` in Degree mode
Settings: Angle Degree (title bar DEG)
Keys: computer keyboard `90@>Rad`, Return
Observed: input `90▶Rad`, result `(π/2)ʳ` (stacked fraction in brackets with a raised r).
Screenshot: pages-shots-6/B-B8-90-to-rad-degree.png
Differs from CASSim or from this file's expectation? no.

### B9: text of `x▶Polar`
Settings: Real, Radian
Keys: computer keyboard `x@>Polar`, Return
Observed: input `x▶Polar`, result `x` (nothing to convert). A complex input was not tried here (Real mode): see B12.
Screenshot: pages-shots-6/B-B9-x-to-polar.png
Differs from CASSim or from this file's expectation? not known; CASSim's guess was for a complex value.

### B10: `30▶DMS` with no minutes
Settings: Radian first, then Degree
Keys: computer keyboard `30@>DMS`, Return
Observed: in Radian the 30 is taken as radians and the result is a long exact expression starting `1718°iPart(60·fPart(5400/π))'(60·fPart(60·fPa…` (cut off at the screen edge). In Degree the result is `30°` (no minutes or seconds shown).
Screenshot: pages-shots-6/B-B10a-30-to-dms-radian.png, B-B10b-30-to-dms-degree.png
Differs from CASSim or from this file's expectation? yes (CASSim guessed `30°0'`).

### B11: name of the circular inverses
Settings: Radian
Keys: computer keyboard `arccos(1/2)`, Return; `cos(1)`
Observed: `arccos(1/2)` is displayed `cos⁻¹(1/2)` with result `π/3`. `cos(1)` stays `cos(1)`.
Screenshot: pages-shots-6/B-B11a-arccos-half.png, B-B11b-cos-1.png
Differs from CASSim or from this file's expectation? no (`cos⁻¹`).

### B14: the 30.25° conversion in Degree mode
Settings: Degree
Keys: computer keyboard `30.25@>DMS`, Return
Observed: input `(30.25)▶DMS`, result `30°15'`.
Screenshot: pages-shots-6/B-B14-30.25-to-dms.png
Differs from CASSim or from this file's expectation? not known (the source file `emulator-templates-results.md` was not opened for its expected value).

## simulator-todo.md section D (the ones run so far)

### D2: `sin(1)` in Degree, Auto, and `sin(1)+1`
Settings: Degree, Auto, Real, Float 8
Keys: computer keyboard `sin(1)`, Return; `sin(1)+1`, Return
Observed: `sin(1)` stays `sin(1)`; `sin(1)+1` stays `sin(1)+1`. Nothing is rewritten with π/180.
Screenshot: pages-shots-6/B-D2a-sin1-degree.png, B-D2b-sin1-plus-1-degree.png
Differs from CASSim or from this file's expectation? yes for the sum (CASSim prints `sin(π/180)+1`).

### A13 and B5: `100°` in Gradian mode
Settings: Angle Gradian (title bar GRAD), Float 8, Auto, Real
Keys: computer keyboard, typed `100°`, Return; then `sin(100°)`
Observed: `100°` shows input `100°`, result `1000/9` (stacked fraction). `sin(100°)` shows result `cos(100/9)` (stacked), not a number.
Screenshot: pages-shots-6/B-A13-B5-100deg-gradian.png, B-A13b-sin-100deg-gradian.png
Differs from CASSim or from this file's expectation? no for `100°` (1000/9 as guessed).

### B12: Degree-mode exact angle, `3+4ⅈ` in Polar
Settings: Angle Degree, Real or Complex Rectangular (Real or Complex list: Real, Rectangular, Polar), Float 8, Auto
Keys: computer keyboard `3+4@i@>Polar`, Return
Observed: input `(3+4·ⅈ)▶Polar`, result `(5 ∠ 90−tan⁻¹(3/4))` with the fraction stacked.
Screenshot: pages-shots-6/B-B12-B13b-degree-rect-polar-exact.png
Differs from CASSim or from this file's expectation? CASSim writes `180*tan⁻¹(4/3)/π` (the device gives `90−tan⁻¹(3/4)`, as the todo row says).

### B13: Real and Rectangular in Degree mode (Rectangular run; Real not run)
Settings: Angle Degree, Rectangular
Keys: computer keyboard `3+4@i`, `3+4@i@>Polar`, `@i@>Polar`, `3+4@i@>Polar` with ctrl+Return (approximate), `(3+4@i)@>Rect`
Observed: `3+4ⅈ` shows `3+4·ⅈ`. `▶Polar` gives `(5 ∠ 90−tan⁻¹(3/4))`. `ⅈ▶Polar` gives `(1 ∠ 90)`. With ctrl+Return the polar gives `(5. ∠ 53.130102)`. `(3+4ⅈ)▶Rect` gives `3+4·ⅈ`. Rectangular gives the same Polar results as the Polar mode row of check 4's 5.4.
Screenshot: pages-shots-6/B-B13a-degree-rect-3plus4i.png, B-B13c-degree-rect-i-polar.png, B-B13d-degree-rect-polar-approx.png, B-B13e-degree-rect-to-rect.png
Differs from CASSim or from this file's expectation? not compared yet. Real in Degree mode was not run: `3+4ⅈ` in Real mode gives a Non-real error (see B7), so only non-complex inputs would be left to test.

## simulator-todo.md section C. Variables and scope

Settings for C: Radian, Auto, Real, Float 8 (put back after the Degree and Gradian rows).

### C1: `pi:=3`
Settings: as above
Keys: computer keyboard `pi:=3`, Return
Observed: dialog `Error` with the text `Invalid variable or function name`, button OK. The entry line keeps `pi:=3` with the caret just after `pi`. No error code number shown.
Screenshot: pages-shots-6/B-C1-pi-assign.png
Differs from CASSim or from this file's expectation? yes (wording; CASSim says "Invalid variable name: that name is reserved", code -3).

### C2: runaway recursion
Settings: as above
Keys: computer keyboard `f(n):=f(n+1)`, Return, then `f(1)`, Return
Observed: after about 1 to 3 s a dialog `Error` with the text `Recursion too deep` and three buttons `View`, `Edit`, `Cancel`. The history row for `f(1)` then reads `"Error: Recursion too deep"`. (My Return pressed View, which opened a box titled `f` showing `Define f(n)=f(n+1)` with Edit and Cancel; Escape closed it.) The depth at which it stops was not measured.
Screenshot: pages-shots-6/B-C2a-recursion-dialog.png, B-C2b-recursion-history.png
Differs from CASSim or from this file's expectation? yes (CASSim: "Recursion is too deep", code -4).

### C3: `delVar nothing` (undefined)
Settings: as above
Keys: computer keyboard `delVar nothing`, Return
Observed: input `DelVar nothing`, result `Done`.
Screenshot: pages-shots-6/B-C3-delvar-nothing.png
Differs from CASSim or from this file's expectation? no.

### C4: `a:=x+1`, `x:=2`, then `a`
Settings: as above (x undefined at the start)
Keys: computer keyboard, Return after each
Observed: `a:=x+1` gives `x+1`; `x:=2` gives `2`; `a` gives `3`.
Screenshot: pages-shots-6/B-C4-a-x-plus-1.png
Differs from CASSim or from this file's expectation? yes (CASSim gives `x+1`).

### C5: `a:=5` then `a(2)`
Settings: as above
Keys: computer keyboard `a:=5`, Return; `a(2)`, Return
Observed: dialog `Error` / `Name is not a function`; history row `a(2)` with `"Error: Name is not a function"`.
Screenshot: pages-shots-6/B-C5-a-of-2.png
Differs from CASSim or from this file's expectation? yes (not read as a·2).

### C6: `derivative(x^2*sin(x),x)|x=2`
Settings: as above, `DelVar x` run first
Keys: computer keyboard (pasted as one string), Return
Observed: the input is typeset `d/dx(x²·sin(x))|x=2`; result `4·cos(2)+4·sin(2)`. The `|` is applied after the derivative.
Screenshot: pages-shots-6/B-C6-derivative-bar.png
Differs from CASSim or from this file's expectation? no.

## simulator-todo.md section D (continued)
Settings: Radian, Auto, Real, Float 8 unless stated.

### D1: error wording
Keys: computer keyboard `[1,2;2,4]^-1`, Return; recursion is under C2
Observed: `Singular matrix` dialog (`Error` / `Singular matrix`, OK); history `"Error: Singular matrix"`. "Memory" was not provoked. Recursion: `Recursion too deep` (C2). No numeric error codes are shown.
Screenshot: pages-shots-6/B-D1-singular-matrix-dialog.png
Differs from CASSim or from this file's expectation? wording only: the device has no code number on screen.

### D3: `propFrac(7/3)`
Observed: result `2+1/3` (stacked fraction).
Screenshot: pages-shots-6/B-D3-propfrac.png
Differs from CASSim or from this file's expectation? yes (CASSim gives 7/3).

### D4: `round(2.5)`
Observed: result `2.5` (not rounded to an integer).
Screenshot: pages-shots-6/B-D4-round-2.5.png
Differs from CASSim or from this file's expectation? yes (CASSim gives 3.).

### D5: `cross` of two 2-element vectors
Keys: `crossP([1,2],[3,4])`
Observed: `[0 0 -2]`.
Screenshot: pages-shots-6/B-D5-crossp-2d.png
Differs from CASSim or from this file's expectation? no.

### D6: `norm` of a matrix
Keys: `norm([1,2;3,4])`
Observed: `√30` (Frobenius).
Screenshot: pages-shots-6/B-D6-norm-matrix.png
Differs from CASSim or from this file's expectation? no.

### D7: `mean`, `median` of an empty list
Keys: typed `mean({})`, `median({})` (typing `{}` gives a list with one empty slot `{▯}`, so this was not a true empty list)
Observed: `mean({▯})` gives `undef`. `median({▯})` gives a dialog `Dimension error` (TI text, do not reuse: a list or matrix index is not valid, with an example) and the history row `"Error: Dimension error"`.
Screenshot: pages-shots-6/B-D7a-mean-empty.png, B-D7b-median-empty.png
Differs from CASSim or from this file's expectation? yes (CASSim says Domain error); a real empty list (`seq(1,n,1,0)`) was not tried.

### D8: `solve(sin(x)=1/2,x)` with no domain
Observed: `x=2·n1·π+π/6 or x=2·n1·π+5·π/6` (n1 in bold italic).
Screenshot: pages-shots-6/B-D8-solve-sin.png
Differs from CASSim or from this file's expectation? yes (CASSim echoes it).

### D9: `solve(x^2=a,x)`
Observed: `x=-√a and a≥0 or x=√a and a≥0`.
Screenshot: pages-shots-6/B-D9-solve-x2-a.png
Differs from CASSim or from this file's expectation? yes (a≥0 is added to each root). Typing `x^2=a` without Right after the 2 gave a Syntax error first (the exponent captured the rest).

### D10: `zeros` with no finite answer
Keys: `zeros(1,x)`
Observed: `{▯}` (an empty list drawn with one empty slot).
Screenshot: pages-shots-6/B-D10-zeros-none.png
Differs from CASSim or from this file's expectation? yes (CASSim echoes).

### D11: `polyRoots`
Keys: `polyRoots(x^3-3x^2+3x-1,x)`
Observed: `{1,1,1}` (multiplicity kept).
Screenshot: pages-shots-6/B-D11-polyroots.png
Differs from CASSim or from this file's expectation? no.

### D12: a system SymPy cannot solve
Keys: `solve({sin(x)=y,cos(y)=x},{x,y})`
Observed: warning triangle on the row; result `x=0.76816916 and y=0.69481969` (a numeric solution).
Screenshot: pages-shots-6/B-D12-solve-nonlinear-system.png
Differs from CASSim or from this file's expectation? yes (CASSim says Domain error).

### D13: `x:=4` then `derivative(x^2,x)`
Observed: `x:=4` gives `4`; `derivative(x^2,x)` is drawn `d/dx(x²)` with result `8`. No refusal.
Screenshot: pages-shots-6/B-D13-x-assigned-derivative.png
Differs from CASSim or from this file's expectation? no.

### D15: `nSolve` start points
Keys: `nSolve(x^3-x=0,x)`
Observed: `0.` Only this one case was run; start points are not visible.
Screenshot: pages-shots-6/B-D15-nsolve-x3-x.png
Differs from CASSim or from this file's expectation? not known.

### D16: `fMin(x^3,x)`
Observed: `x=-∞`.
Screenshot: pages-shots-6/B-D16-fmin-x3.png
Differs from CASSim or from this file's expectation? yes (CASSim echoes).

### D18: `integral(sin(x)/x,x,1,2)`
Observed: input drawn as an integral template; result `0.65932991` (decimal).
Screenshot: pages-shots-6/B-D18-integral-sinx-over-x.png
Differs from CASSim or from this file's expectation? yes (CASSim gives Si(2)-Si(1)).

### D20: `binomPdf(10,1/2,5)`
Observed: `0.24609375` (decimal).
Screenshot: pages-shots-6/B-D20-binompdf.png
Differs from CASSim or from this file's expectation? yes (CASSim gives 63/256).

### D21: `invBinom` when the area is not reached
Keys: `invBinom(1,10,1/2)`
Observed: `10`.
Screenshot: pages-shots-6/B-D21-invbinom-area-1.png
Differs from CASSim or from this file's expectation? no.

### D22: `tvmN` for an impossible loan
Keys: `tvmN(5,10000,-10,0,12,12,0)`
Observed: dialog `Error` / `Domain error` with an explanatory line (TI text, do not reuse). (A first attempt had a stray bracket from a split type and gave Syntax.)
Screenshot: pages-shots-6/B-D22-tvmn-impossible.png
Differs from CASSim or from this file's expectation? no ("Domain error").

### D28: `eigVl` order
Keys: `eigVl([2,1;1,2])`
Observed: `{3.,1.}`.
Screenshot: pages-shots-6/B-D28-eigvl.png
Differs from CASSim or from this file's expectation? no for order (largest first); the result is a decimal.

### D29: `3+"x"` and `"x"+3`
Keys: computer keyboard `3+"x` then Right (the closing quote is added by the editor), Return; `"x` Right `+3`, Return
Observed: `3+"x"` gives result `"x"+3` (no error); `"x"+3` gives `"x"+3`.
Screenshot: pages-shots-6/B-D29a-3-plus-string-x.png, B-D29b-string-x-plus-3.png
Differs from CASSim or from this file's expectation? yes (CASSim gives Error: Data type).

### D30: `{1,_,3}` and `mean({1,_,3})`
Keys: computer keyboard `{1,_,3}`, Return; `mean({1,_,3})`, Return
Observed: `{1,_,3}` stays `{1,_,3}` (a void). `mean({1,_,3})` gives `2` (the void is skipped).
Screenshot: pages-shots-6/B-D30a-list-void.png, B-D30b-mean-list-void.png
Differs from CASSim or from this file's expectation? yes (CASSim treats `_` as a variable).

### D31: `seqGen(n^2,n,u,{1,5},{},1)`
Keys: computer keyboard `seqGen(n^2`, Right, `,n,u,{1,5},{},1)`, Return (the empty `{}` is drawn `{▯}`)
Observed: result `{1,4,9,16,25}`.
Screenshot: pages-shots-6/B-D31-seqgen.png
Differs from CASSim or from this file's expectation? yes (CASSim echoes it, not built).

### D23: titles and `RegEqn` text of the regressions
Settings: Radian, Auto, Real, Float 8. Data on the Calculator page: `xs:={1,2,3,4,5,6,7,8}`, `ys:={2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1}`. Each command was run as `<Reg> xs,ys`, then `stat.results` was entered. (Typing `stat.results` letter by letter fails because of the drop-down; a string of 17 or more characters, for example `stat.results` followed by five spaces, is pasted whole and works.)
Observed (labels exactly as shown, then values):
- `MedMed`: Title `"Median−Median Line"`, RegEqn `"m·x+b"`, `"m"` 1.98, `"b"` -0.02666667, `"Resid"` `"{...}"`.
- `LnReg`: Title `"Logarithmic Regression"`, RegEqn `"a+b·ln(x)"`, `"a"` 0.19564441, `"b"` 6.6607723, `"r²"` 0.91572796, `"r"` 0.95693676, `"Resid"`, `"ResidTrans"` (both `"{...}"`).
- `CubicReg`: Title `"Cubic Regression"`, RegEqn `"a·x^3+b·x^2+c·x+d"`, a -0.0010101, b 0.01601732, c 1.9241703, d 0.12142857, `"R²"` 0.99884857, `"Resid"`.
- `QuartReg`: Title `"Quartic Regression"`, RegEqn `"a·x^4+b·x^3+c·x^2+d·x+e"`, a 0.0030303, b -0.05555556, c 0.34545455, d 1.1683261, e 0.63571429, `"R²"` 0.99894764, `"Resid"`.
- `SinReg`: Title `"Sinusoidal Regression"`, RegEqn `"a·sin(b·x+c)+d"`, a 3.1585864, b 1.4482556, c 2.9275519, d 9.0203022, `"Resid"`. No R² row.
- `Logistic`: Title `"Logistic Regression (d=0)"`, RegEqn `"c/(1+a·ⅇ^(−b·x))"`, a 10.148134, b 0.48830599, c 18.968061, `"Resid"`.
- `LogisticD`: Title `"Logistic Regression (d≠0)"`, RegEqn `"c/(1+a·ⅇ^(−b·x))+d"`, a 1.8217818, b 0.12495558, c 64.730371, d -22.745326, `"Resid"`.
In `stat.` drop-down for `MedMed`: b, freqreg, m, regeqn, resid, results, stat, values, xreg, yreg; for `LnReg`: a, b, freqreg, r, r², regeqn, resid, residtrans, results, stat, values, xreg, ...
Screenshot: pages-shots-6/B-D23a-medmed-results.png, B-D23b-lnreg-results.png, B-D23c-cubicreg-results.png, B-D23d-quartreg-results.png, B-D23e-sinreg-results.png, B-D23f-logistic-results.png, B-D23g-logisticd-results.png
Differs from CASSim or from this file's expectation? not compared yet (CASSim's wording was a guess).

### D24: `stat.values` for `OneVar`
Keys: `OneVar xs`, Return; `stat.values` (pasted)
Observed: a single column of numbers (not one row). The visible bottom of the column reads 2.4494897, 2.2912878, 8., 1., 2.5, 4.5, 6.5, 8., 42. (the top was off screen).
Screenshot: pages-shots-6/B-D24-onevar-values.png
Differs from CASSim or from this file's expectation? yes (CASSim gives one row).

### D14: `deSolve` with a second initial condition
Keys: `deSolve(y''=y and y(0)=1 and y'(0)=2,x,y)`, Return
Observed: `y=3·ⅇ^x/2 − ⅇ^(−x)/2`.
Screenshot: pages-shots-6/B-D14-desolve-y-prime-initial.png
Differs from CASSim or from this file's expectation? yes (CASSim says not supported).

### Item 4 small examples (Radian, Auto, Real, Float 8)
- `getNum(2/3)` → `2`; `getDenom(2/3)` → `3`. Screenshots: B-D14b-getNum.png, B-D14c-getDenom.png
- `completeSquare(x^2+4·x+1,x)` → `(x+2)²−3`. Screenshot: B-D14d-completeSquare.png
- `polyRoots(x^2-1,x)` → `{-1,1}`. Screenshot: B-D14e-polyRoots.png
- `cPolyRoots(x^2+1,x)` → `{−ⅈ,ⅈ}`. Screenshot: B-D14f-cPolyRoots.png
- `polyRemainder(x^2+1,x-1,x)` → `2`. Screenshot: B-D14g-polyRemainder.png
- `polyQuotient(x^2+1,x-1,x)` → `x+1`. Screenshot: B-D32a-polyQuotient.png
- `polyGcd(x^2-1,x-1)` → `x-1` (spelling `polyGcd` accepted). Screenshot: B-D32b-polyGcd.png
- `polyCoeffs(3x^2+2,x)` → `{3,0,2}` (spelling accepted; echoed `3·x²+2`). Screenshot: B-D32c-polyCoeffs.png
- `polyDegree(3x^2+2,x)` → `2`. Screenshot: B-D32d-polyDegree.png
- `arcLen(x^2,x,0,1)` → `ln(√5+2)/4 + √5/2`. Screenshot: B-D32e-arcLen.png
- `series(sin(x),x,5)` → `x − x³/6 + x⁵/120`. Screenshot: B-D32f-series.png
- `dominantTerm(x^3+x,x,ⅈ)` (typed by mistake with the point ⅈ instead of ∞; redone with ∞ below) → `-2·(x−ⅈ)`. Screenshot: B-D32g-dominantTerm-at-i.png
- `centralDiff(x^2,x)` → `2.·x` (decimal coefficient). Screenshot: B-D32h-centralDiff.png
- `nfMin(x^2-2x,x)` → `0.99999986` (numeric, not exactly 1). Screenshot: B-D32i-nfMin.png
- `nfMax(-x^2,x)` → `0.`. Screenshot: B-D32j-nfMax.png
- `dominantTerm(x^3+x,x,∞)` (typed `infinity`) → `x³`, with a warning triangle shown at the left of the entry (warning text not opened). Screenshot: B-D32k-dominantTerm-inf.png
- `newMat(2,3)` → 2×3 zero matrix. Screenshot: B-D32l-newMat.png
- `diag([1,2;3,4])` → row matrix `[1 4]`. Screenshot: B-D32m-diag.png
- `colAugment([1,2],[3,4])` → 2×2 matrix `[1 2;3 4]` (the two rows stacked, despite the name). Screenshot: B-D32n-colAugment.png
- `constructMat(i+j,i,j,2,2)` → `[2 3;3 4]`. Screenshot: B-D32o-constructMat.png
- `ref([1,2;3,4])` → `[1 4/3;0 1]`. Screenshot: B-D32p-ref.png

### Item 8: units, define, logic (Radian, Auto, Real, Float 8)
- `3_m` → `3.·_m` (decimal point added to the coefficient; the unit is kept). Screenshot: pages-shots-6/B-U1-unit-3m.png
- `3_m+2_m` → `5.·_m`. Screenshot: B-U2-unit-sum.png
- `2_km@>_m` (typed `@>`, shown ▶) → `2000.·_m`. Screenshot: B-U3-unit-convert.png
- `g:=x+1` → `x+1`; then `g` → `x+1`. Screenshot: B-U4-define-g-then-g.png
- `true or false` → `true`. Screenshot: B-U5-true-or-false.png
- `not true` → `false`. Screenshot: B-U6-not-true.png
- `2 xor 3` → `1` (bitwise on integers). Screenshot: B-U7-2-xor-3.png
Differs from CASSim? not compared; `3_m` gaining a decimal point, and `xor` acting bitwise, are the points to check.

## Run / not run (Part B)
Run: simulator-todo sections A (A1–A13), B1–B14, C1–C6, D1–D16, D18, D20–D24, D28–D31, plus item-4 examples (getNum, getDenom, completeSquare, polyRoots, cPolyRoots, polyRemainder, polyQuotient, polyGcd, polyCoeffs, polyDegree, arcLen, series, dominantTerm, centralDiff, nfMin, nfMax, newMat, diag, colAugment, constructMat, ref) and item-8 units/define/logic rows.
Not run: B13 Real-in-Degree (ⅈ errors in Real mode, not retried); D17, D19, D25–D27; sections E1–E8 and F1–F5 of simulator-todo; history plan H1 i,k,l,m, H2 c,h,j, H3 (mouse), H4 k–o, H5 d,f,h,j, H7, H8, H9; editor plan T3f, T7 templates, T8c, T9, T10c; item 4 menu leaves; item 5 Recall Definition/Insert Comment; item 6 menu scrolling; item 7 `stat.x̄`, Define from Actions, library call; `a or b` full text; A3/A11 hidden results.
Reason: time and context ran out in this session; nothing was skipped for a technical reason except B13.
Also seen: `dominantTerm(x^3+x,x,ⅈ)` was typed by mistake first (kept as B-D32g); `2 xor 3` is bitwise; `colAugment` stacked two row vectors into a 2×2.
