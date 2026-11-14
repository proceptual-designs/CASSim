# Calculator leftovers, check 6 run 4 (emulator-calc5-results.md)
Settings: Float 8, Radian, Real, Automatic (checked in Document Settings first), in a new Handheld-page-size document (all earlier test documents had been closed without saving). Screenshots in pages-shots-6/ (names start R4-). Observations only. This file is partial: see the lists at the end.

### C2: depth at which recursion stops
Keys: `f(n):=when(n=0,0,f(n-1))` then `f(n)` for growing n; Escape closed each error dialog.
Observed: the definition gives `Done`. `f(50)`, `f(200)`, `f(240)`, `f(250)`, `f(251)`, `f(252)`, `f(253)`, `f(254)` all give `0`. `f(255)`, `f(260)`, `f(265)`, `f(275)`, `f(350)`, `f(500)` and `f(1000)` fail: an Error dialog with the text `Recursion too deep` and buttons View, Edit, Cancel appears, and the history row shows `"Error: Recursion too deep"`. So the limit is between n = 254 (works) and n = 255 (fails) for this function.
Screenshot: pages-shots-6/R4-C2a-recursion-f200-ok.png, R4-C2b-recursion-f1000-dialog.png, R4-C2c-recursion-f275-f240.png, R4-C2d-recursion-f254-ok.png, R4-C2e-recursion-f255-dialog.png
Differs from CASSim or from this file's expectation? yes (CASSim stops at depth 50; the simulator allows n = 254).

### B13 and B12: Real (not Rectangular) in Degree mode
Settings: Float 8, Degree, Real, Automatic (changed in Document Settings in this document; title bar shows DEG).
Keys: `(3+4@i)@>Polar`, Return.
Observed: `(3+4ⅈ)▶Polar` gives `(5∠90−tan⁻¹(3/4))`. `3+4ⅈ` is accepted in Real mode here (no error); the Rectangular setting is not needed to type ⅈ.
Screenshot: pages-shots-6/R4-B13-polar-degree-real.png
Differs from CASSim or from this file's expectation? same as the value already in simulator-todo B12.

### D17 and D2: calculus and `sin(1)+1` in Degree mode (Degree, Auto, Real, Float 8)
Keys: `derivative(sin(x),x)`; `integral(sin(x),x,0,90)`; `sin(1)+1`; `derivative(sin(x),x)|x=90`; each then Return.
Observed:
- `d/dx(sin(x))` → `π·cos(x)/180` (the derivative of the degree-mode sine carries the π/180 factor).
- `∫₀⁹⁰ sin(x) dx` → `180/π`.
- `sin(1)+1` → `sin(1)+1` (not rewritten).
- `d/dx(sin(x))|x=90` → `0`.
Screenshot: pages-shots-6/R4-D17a-derivative-sin-degree.png, R4-D17b-integral-sin-0-90-degree.png, R4-D2-sin1-plus1-degree.png, R4-D17c-derivative-at-90-degree.png
Differs from CASSim or from this file's expectation? yes for D17 (CASSim treats trig as radians in calculus); D2 matches the simulator-todo "Simulator" column.

### D19: `tvm*` and `amortTbl` with PmtAt 1 and a non-default round (Degree, Auto, Real, Float 8 in this document)
Keys: `tvmFV(12,5,0,-100,0,12,12,0)` (8 arguments, my first try), then `tvmFV(12,5,0,-100,12,12,0)`, `…,12,12,1)`, `tvmPmt(12,5,5000,0,12,12,1)`, `amortTbl(3,12,5,5000,,0,12,12,1)`, `amortTbl(3,12,5,5000,,0,12,12,0,4)`.
Observed:
- 8 arguments to `tvmFV`: Error dialog `Too many arguments`, long text `The function or command contains an excessive number of arguments and cannot be evaluated.` (TI text, do not reuse), button OK; the line stays on the entry line for editing. (`amortTbl` with one argument too many gave the same dialog.)
- `tvmFV(12,5,0,-100,12,12,0)` → `1227.8855` (payment at the end of the period).
- `tvmFV(12,5,0,-100,12,12,1)` → `1233.0017` (payment at the start; equals 1227.8855·(1+0.05/12)).
- `tvmPmt(12,5,5000,0,12,12,1)` → `-426.26132`.
- `amortTbl(3,12,5,5000,,0,12,12,1)` (empty Pmt argument) → a 4×4 matrix `[0 0. 0. 5000.; 1 0. −426.26 4573.74; 2 −19.06 −407.2 4166.54; 3 −17.36 −408.9 3757.64]` (first column the payment number; no interest in payment 1; values rounded to 2 places).
- `amortTbl(3,12,5,5000,,0,12,12,0,4)` (PmtAt 0, round 4) → `[0 0. 0. 5000.; 1 −20.8333 −407.2041 4592.7959; 2 −19.1366 −408.9008 4183.8951; 3 −17.4329 −410.6045 3773.2906]` (values rounded to 4 places).
Screenshot: pages-shots-6/R4-D19a-tvmFV-too-many-args.png, R4-D19b-tvmFV-end.png, R4-D19c-tvmFV-begin.png, R4-D19d-tvmPmt-begin.png, R4-D19e-amortTbl-PmtAt1.png, R4-D19f-amortTbl-round4.png
Differs from CASSim or from this file's expectation? CASSim's annuity-due formula agrees with the tvmFV ratio; amortTbl with PmtAt 1 to be compared.

### D25 — MedMed group sizes (n = 7, 8, 10)
Settings: Degree, Automatic, Real, Float 8.
Keys: `xs:={1,…,8}`, `ys:={2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1}`; `MedMed xs,ys`, then `stat.results`. Repeated with the first 7 points (`x7`,`y7`) and with `x10:=seq(k,k,1,10)`, `y10:=seq(k^2,k,1,10)`.
Observed:
- n = 8 (ys above) → m 1.98, b −0.02666667.
- n = 7 (first 7 points, ys ends 13.8) → m 2., b −0.06666667.
- n = 10 (y = k², exact squares 1…100) → m 11., b −22. Result lists Title "Median−Median Line", RegEqn "m·x+b", m, b, Resid (list).
- No r or r² rows in the MedMed results (only Title, RegEqn, m, b, Resid).
Screenshot: pages-shots-6/R4-D25a-medmed-n8.png, R4-D25b-medmed-n7.png, R4-D25c-define-x10-y10.png, R4-D25d-medmed-n10.png
Differs from CASSim or from this file's expectation? Compare CASSim's three-group split for n = 7, 8, 10 against these m, b values (n = 10 gives 11, −22).

### D27 — r and r² on transformed fits (first data)
Settings: Degree, Automatic, Real, Float 8. Data: `xs`={1..8}, `ys`={2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1} (near-linear).
Keys: `ExpReg xs,ys` then `stat.results`; `PowerReg xs,ys` then `stat.results`.
Observed:
- ExpReg: RegEqn "a·b^x", a 2.2253902, b 1.3128637, r² 0.92465993, r 0.9615924, plus Resid and ResidTrans lists.
- PowerReg: RegEqn "a·x^b", a 2.0522894, b 0.98517582, r² 0.99872502, r 0.99936231, plus Resid and ResidTrans lists.
- r and r² are reported for the straightened (transformed) fit, not for the original-scale curve; a ResidTrans row appears beside Resid.
Screenshot: pages-shots-6/R4-D27a-expreg-linear-data.png, R4-D27b-powerreg-linear-data.png
Differs from CASSim or from this file's expectation? CASSim should report r, r² of the transformed line and offer both residual lists.

### D26 — Logistic regression on noisy data
Settings: Degree, Automatic, Real, Float 8.
Keys: `xl:=seq(k,k,1,10)`, `yl:={1.2,1.9,3.1,5.2,7.9,10.6,12.5,13.3,13.8,14.1}`; `Logistic xl,yl`, then `stat.results`.
Observed: Title "Logistic Regression (d=0)", RegEqn "c/(1+a·ⅇ^(−b·x))", a 33.107433, b 0.74461186, c 14.457285, Resid (list). No r or r² rows. Converged without an error on this data (first-guess and stopping rule are not visible to the user).
Screenshot: pages-shots-6/R4-D26a-logistic-noisy.png
Differs from CASSim or from this file's expectation? CASSim should return a, b, c of the c/(1+a·ⅇ^(−b·x)) form with the title showing (d=0), and no r.

### Item 8 — units `_c` and `_g` (Automatic mode)
Settings: Degree, Automatic, Real, Float 8.
Keys: `5_c`, `5_g`, `5_c+3_g`.
Observed:
- `5·_c` → 1.4989623ᴇ9·_m/_s (speed-of-light constant used as a unit-bearing value, shown with a decimal because of the large value).
- `5·_g` → 49.03325·_m/_s² (standard gravity).
- `5·_c+3·_g` → "Error: Inconsistent units" (a dialog "Inconsistent units" with OK first; after OK the history shows the error text as the result).
Screenshot: pages-shots-6/R4-B8-units-c-g-mixed.png
Differs from CASSim or from this file's expectation? CASSim should treat `_c`, `_g` as constants with units and raise "Inconsistent units" on mixed dimensions. Exact-mode behaviour not run yet.

### H1 l — undo depth (typing 30 characters, then ctrl+Z repeatedly)
Settings: Degree, Automatic, Real, Float 8. Computer keyboard ctrl+Z / ctrl+Y (keypad not tried).
Keys: new empty entry line; typed `1+2+3+4+5+6+7+8` and `+9+1+2+3+4+5+6+` (30 characters). The entry showed `Ans+2+3+4+5+6+7+8+9+1+2+3+4+5+6+` (the leading `1` did not remain and `Ans` was inserted because the line began with an operator after the first character was removed; recorded as seen, not a test of undo).
Observed:
- After 10 ctrl+Z the entry read `Ans+2+3+4+5+6+7+8+9+1+2+` (8 characters removed by 10 presses).
- After 20: `Ans+2+3+4+5+6`; after 30: `Ans+2`.
- After 35 presses (5 more) the page showed the blank "Press menu" screen (the Calculator application on the page itself was undone), and 10 and 30 more presses changed nothing. So undo is not limited to the entry line: it keeps going past the typing, past the page's content, to the point where the page was created. Roughly 35 presses covered this whole page.
- ctrl+Y once: an empty Calculator page returned with the cursor on the entry line. Twice: `Ans+`. After 10 more: `Ans+2+3+4+5+`. Redo restores typing in small steps, similar in size to undo.
- Caveat: the document had no earlier history lines visible above the entry in these screenshots (it appears to be a fresh document), so the question whether undo crosses earlier history pairs was not decided here.
Screenshot: pages-shots-6/R4-H1l-undo10.png, R4-H1l-undo20.png, R4-H1l-undo30.png, R4-H1l-undo35-blank-page.png, R4-H1l-redo1.png, R4-H1l-redo2.png, R4-H1l-redo12.png
Differs from CASSim or from this file's expectation? CASSim should keep a deep undo stack (not a small fixed count) and expect undo to step back through typing in groups of fewer than one character per press on average (grouping), and redo to mirror it.
