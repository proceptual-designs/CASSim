# Emulator check 6, run 7: Parts A and D (CAS and calculator), observations only

Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, Keypad + SideScreen at 250%. Settings used (Document1, opened fresh; already at these values when checked): Float 8, Radian, Exponential Normal, Real or Complex Rectangular, Calculation Mode Auto, CAS On. Writes go to CASSim-evidence (Simon's instruction 2026-11-27). Screenshots: `pages-shots-7/R7-<row>-<name>.png`.
How a warning is read: clicking the yellow triangle at the left of a line opens a Warning dialog (no right-click needed). Texts are marked (TI text, do not reuse).

## R7-A1 Show Warning Info
Status: partial. Run: the three stand-alone entries and K4 1.1 #8 (in both forms). Not run: the other paper entries (see the end of this section).

### R7-A1a derivative((x+1)/(x-1),x)
Keys: keyboard, typed `derivative((x+1)/(x-1),x)`, Return. Observed: triangle shown; result `-2/(x-1)²` (as a fraction, d/dx template drawn in the input). Warning text (TI text, do not reuse): "Domain of the result might be larger than the domain of the input." Screenshots: R7-A1-derivative-result.png, R7-A1-derivative-warning.png.
Differs from CASSim? Not known (CASSim gave no triangle for this one: brief says it shows none for the rest). Here the device DOES show a triangle.

### R7-A1b tCollect(dotP(...)) with the vector [5cos(t)-4cos(5t/2), 5sin(t)-4sin(5t/2)] twice
Observed: triangle shown; result `41-40·cos(3·t/2)`. Warning text (TI text, do not reuse): "Domain of the result might be larger than the domain of the input." (same text as A1a). Screenshots: R7-A1-tcollect-result.png, R7-A1-tcollect-warning.png.
Differs from CASSim? Not known; CASSim shows no triangle here.

### R7-A1c solve(x*@e^(-2y)+y^2*@e^(x)=8*@e^(4),y)
Typed with Right after each exponent. Observed: triangle shown; result `(y²·ⅇ^x-8·ⅇ⁴)·ⅇ^(2·y)=-x` (the equation is returned in a rearranged form, not solved for y). Warning text (TI text, do not reuse), scrolls: "More solutions may exist. Try specifying appropriate lower and upper bounds and/or a guess. Examples using solve(): solve(Equation, Var=Guess)|lowBound<Var<upBound; solve(Equation, Var)|lowBound<Var<upBound; solve(Equation, Var=Guess)" (the end of the scroll was not read). Screenshots: R7-A1-implicit-solve-result.png, R7-A1-implicit-solve-warning.png.
Differs from CASSim? CASSim says "Solved numerically: there may be other solutions" for a numeric solve; the device text here is a different warning ("More solutions may exist ..."), for a symbolic (unsolved) result.

### R7-A1d K4 1.1 #8: v(x):=2·x·(h-2·x)·(h-x), then solve(d/dx(v(x))=0,x)|0<x<h/2
New Problem (2.1). Typed `derivative(` for the d/dx template. Entered twice: as the conjunction `|0<x and x<h/2`, then as the original chain `|0<x<h/2`.
Observed (both): triangle shown; result `x=-h·(√3-3)/6 and h>0`. Warning text, identical for both (TI text, do not reuse): "Constraint might be ignored. Specify constraint in the form 'Variable MathTestSymbol Constant' or a conjunction of these forms, for example 'x<3 and x>-12'". Note the warning appears for the conjunction too, and for a constraint whose right-hand side is `h/2` (not a constant).
Screenshots: R7-A1-K4-1.1-8-conj-result.png, R7-A1-K4-1.1-8-conj-warning.png, R7-A1-K4-1.1-8-chained-result.png, R7-A1-K4-1.1-8-chained-warning.png.
Differs from CASSim? Not known.

### R7-A1 not run
K4 1.1 #11; K4 3.1 #3; K4 4.1 #2; K5 3.1 #3; K6 #1, #3; K7 1.1 #3-5, #9, #11, #13, #15; K7 3.1 #4; K7 4.1 #10. Reason: these need the paper definitions retyped first; not reached yet.

## R7-A2 solve with a condition
Settings: as above. Keys: keyboard, `solve(x^2` Right `=4,x)|x>0` and the two others, one Problem (3.1).
Observed: `|x>0` gives `x=2`; `|x=2` gives `x=-2 or x=2`; `|x=3` gives `x=-2 or x=2`. So an equality condition is ignored; an inequality filters.
Screenshot: R7-A2-solve-conditions.png
Differs from CASSim? No: identical to the three CASSim results.

## R7-A3 integral(1/(x^3+x+2),x,0,2)
Keys: keyboard, `integral(1/(x^3` Right `+x+2),x,0,2)`. The result is wider than the screen; it was scrolled by clicking it, pressing Up to select it, then Right 20 times.
Observed (whole result, in the device's order): `3·√7·tan⁻¹(3·√7/7)/28 + 3·√7·tan⁻¹(√7/7)/28 + ln(9/2)/8`. Input shown as the integral template with limits 0 and 2.
Screenshots: R7-A3-integral-start.png, R7-A3-integral-end.png
Differs from CASSim? Same three terms; the ORDER differs. CASSim puts the `tan⁻¹(√7/7)` term first, then `ln(9/2)/8`, then the `tan⁻¹(3·√7/7)` term. Device: tan⁻¹(3√7/7) term, tan⁻¹(√7/7) term, ln term.

## R7-A4 expand with and without the variable
Keys: `expand((x^2` Right `+a)/(b*x+c))`, then the same with `,x)`; one Problem (5.1).
Observed: without x: triangle; `a/(b·x+c) + c²/(b²·(b·x+c)) + x/b - c/b²`. Its warning (TI text, do not reuse): "Domain of the result might be larger than the domain of the input." With x: no triangle; `(a·b²+c²)/(b²·(b·x+c)) + x/b - c/b²`.
Screenshots: R7-A4-expand.png, R7-A4-expand-warning.png
Differs from CASSim? Yes. The no-variable form: CASSim gives `x²/(b·x+c)+a/(b·x+c)` (not expanded further); the device splits the quotient into `a/(b·x+c) + c²/(b²·(b·x+c)) + x/b - c/b²`. The with-x form has the same terms as CASSim in a different order (device: the fraction first, then x/b, then -c/b²; CASSim: x/b, -c/b², fraction last).

## R7-A5 trig families (one Problem, 7.1, five entries in order)
Keys: keyboard, each typed in two short chunks (a 17-character type goes through the clipboard and was dropped, which is why the first attempt in another Problem lost three entries and numbered the later ones from n1).
Observed: `solve(cos(x)=0,x)` `x=(2·n1-1)·π/2`; `solve(tan(x)=1,x)` `x=n2·π+π/4`; `solve(sin(x)=1/2,x)` `x=2·n3·π+π/6 or x=2·n3·π+5·π/6`; `zeros(sin(x),x)` `{n4·π}`; `fMax(sin(x),x)` `x=(4·n5+1)·π/2`. The n numbers count up 1..5 through the Problem; they are bold italic.
Screenshots: R7-A5-cos-tan.png, R7-A5-sin-zeros.png, R7-A5-fmax.png
Differs from CASSim? cos: yes (CASSim `n1·π+π/2`). tan, sin, zeros: no. fMax(sin): yes: the device gives `(4·n5+1)·π/2` with no `(-1)^n` condition; CASSim `(2·n5-1)·π/2 and (-1)^n5<0`.

## R7-A6 fMin(x^3,x)
Observed: `x=-∞`. Screenshot: R7-A6-fmin-cube.png. Differs from CASSim? Yes: CASSim echoes the input.

## R7-A7 constants counter (one Problem, 9.1)
Observed: `solve(2x+y+z=1 and x-y=2,x,y,z)` gives `x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1`; `deSolve(y''=-y,x,y)` gives `y=c2·cos(x)+c3·sin(x)`; `deSolve(y'=y,x,y)` gives `y=c4·ⅇ^x`. So `deSolve` shares `solve`'s `c` counter. Screenshot: R7-A7-constants.png. Differs from CASSim? No: c1; c2, c3; c4 as guessed.

## R7-A8 ln forms (one Problem, 8.1, with A6 and A9)
Observed: `ln(9/2)` gives `ln(9/2)`; `ln(4)` `2·ln(2)`; `ln(1/2)` `-ln(2)`; `ln(3)/4-ln(2)/8` `ln(9/2)/8`; `solve(100=300-295*@e^(-t/150),t)` `t=150·ln(59/40)` (typed with Right after the exponent).
Screenshots: R7-A8-ln-first4.png, R7-A8-ln-solve.png
Differs from CASSim? Entries 1-3: no. Entry 4: yes (CASSim `-ln(2)/8+ln(3)/4`; device combines to `ln(9/2)/8`). Entry 5: yes (CASSim `t=-150·ln(40/59)`; device `t=150·ln(59/40)`).

## R7-A9 invBinom edge cases
Observed: `invBinom(0.0001,10,0.5,1)` (the device shows the typed 0.0001 as `1.ᴇ-4`) gives `[0  0.00097656]`, one row. `invBinomN(0.99,0.5,0,1)` gives the 2×2 matrix `[[0,1.],[1,0.5]]`. Screenshot: R7-A9-invbinom.png.
Differs from CASSim? No: both match the guesses (the CASSim form `[0,1.;1,0.5]` is the same matrix).

## R7-A10 fMin/fMax of trig (one Problem, 10.1)
Observed: `fMin(sin(x),x)` `x=(4·n1-1)·π/2`; `fMax(cos(x),x)` `x=2·n2·π`; `fMin(cos(x)^2,x)` shown as `fMin((cos(x))²,x)` gives `x=-∞ or x=(2·n3-1)·π/2 or x=∞`. No `(-1)^n` conditions anywhere. Screenshot: R7-A10-fmin-fmax.png.
Differs from CASSim? Yes, all three (CASSim: `x=(2·n1-1)·π/2 and (-1)^n1>0`; `x=n2·π and (-1)^n2>0`; `x=n3·π/2 and (-1)^n3<0`).

## Notes on how Part A was run
A6, A8 and A9 shared one Problem (8.1) because none of them makes `c` or `n` numbers. A2 and A4 each had two or three entries in one Problem. One typed 17-character chunk went through the clipboard and was lost (A5 first attempt, A7 first attempt).

## RUN 7 Part A: lists
Run: A2, A3, A4, A5, A6, A7, A8, A9, A10; A1 partly (the three stand-alone entries and K4 1.1 #8).
Not run: A1 paper entries (K4 1.1 #11; K4 3.1 #3; K4 4.1 #2; K5 3.1 #3; K6 #1, #3; K7 1.1 #3-5, #9, #11, #13, #15; K7 3.1 #4; K7 4.1 #10), because each needs its paper's definitions retyped.
Also seen, not covered: clicking the yellow triangle opens the warning; a conjunction constraint with a non-constant bound gives the "Constraint might be ignored" warning; D parts D1 and D2 have not been started.

## Part D

Document Settings in this document: RAD, Automatic, Real (title bar RAD); Float setting not re-checked for this part.

### R7-D1 E1 Solve System of Equations (shot `R7-D1-solve-system.png`)
- Calculator Menu > 3 Algebra > 7 Solve System of Equations... offers two items: 1 Solve System of Equations... and 2 Solve System of Linear Equations....
- Item 1 dialog: "Solve a System of Equations" (TI text, do not reuse), field Number of equations (default 2, spinner), field Variables (default `x,y`), hint "Enter variable names separated by commas", OK and Cancel.
- OK pastes a template `solve({[ ] / [ ]},{x,y})` with two empty slots; I typed `x+y=3`, Down, `x-y=1`, Return.
- Result: `x=2 and y=1` (the word "and" between the two equations).

### R7-D1 E3 t Cdf and χ² Cdf (shots `R7-D1-tcdf-*.png`, `R7-D1-chi2cdf-*.png`)
- Menu > 5 Probability > 5 Distributions: 1 Normal Pdf, 2 Normal Cdf, 3 Inverse Normal, 4 t Pdf, 5 t Cdf, 6 Inverse t, 7 χ² Pdf, 8 χ² Cdf, 9 Inverse χ², A Binomial Pdf, then more below (not scrolled this run).
- t Cdf dialog: Lower Bound default `−∞`, Upper Bound empty, Deg of Freedom, df empty. OK with Upper Bound empty gives an Input Error dialog: "Required field is empty! Field # 2: Upper Bound:" (TI text, do not reuse). Return did not dismiss it; I clicked OK.
- Typing on that dialog after the error left df as 1 (my first typed values went elsewhere), so I re-entered upper 1 and df 5 with ctrl+a. Return did not submit the dialog; clicking OK did.
- Result line: `tCdf(−∞,1,5)` = `0.818391266162` (twelve digits displayed).
- χ² Cdf dialog: Lower Bound default `0`, Upper Bound empty, Deg of Freedom, df empty. With 0, 2, 3: `χ²Cdf(0,2,3)` = `0.427593295297` (twelve digits).

## Rows run / not run / also seen (Parts A and D)
### Run
- Part A: as listed earlier in this file.
- D1: E1 to a result; E3 t Cdf and χ² Cdf, one run each.
### Not run, with reason (time)
- D1: F Cdf and the Inverse dialogs (Inverse t, Inverse χ², Inverse F), E7 Mode's eight submenus, F1 safe keys, F2, F5.
- All of D2 (run 5 leftovers).
- Part B1 Computer view; Part F catalog sweep (no `emulator-catalog3-results.md`).
- Part E skipped by Simon's instruction.
### Also seen, not covered
- Results of tCdf and χ²Cdf show 12 digits although the Float setting for this document was not checked.
- Dialogs in this build do not submit on Return from a field; OK has to be clicked.
