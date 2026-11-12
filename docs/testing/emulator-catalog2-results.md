# Emulator check 5, Part C: Catalog sweep (partial)

CX II-T CAS handheld view, 6.0.3.374. Settings as in Part D (Radian, Automatic, Real, Float 8). Opened from a Calculator page with the Catalog key (the key at the right end of the third letter row, shown as a book icon; the key under `esc` is Scratchpad, not Catalog).
Screenshots: not saved for this part.

### C1 Catalog tabs
Observed: six tabs across the top, each with an icon; the Catalog remembers the last tab used (it opened on tab 6).
- 1 Commands (book icon; alphabetical list, first rows `ANOVA2way`, `Ans`, `approx(`, `approxFraction(` with a ▶ marker, `approxRational(`, `arccos(`, `arccosh(`; wizard-capable entries show a wand icon; a `Wizards On` checkbox (off by default) sits below the list)
- 2 Math functions (∫Σ icon; tree of groups, see below)
- 3 Symbols/units (°C/°F icon; `Conversion Symbol (▶)`, then groups Constants, Length, Area, Volume, Time, Velocity, ...)
- 4 Symbols (∞β° icon; grid of symbols: punctuation, brackets, x̄ ȳ Σ μ σ, superscript 2 and -1, p̂ ŷ c n Δ μ, then Greek capitals and small letters; the bottom text box shows the name of the selected symbol, e.g. `Greek small letter lambda`)
- 5 Math templates (grid of template icons: fraction, exponent, square root, nth root, e^, log, piecewise 2-case, piecewise n-case, system 2, system 3, absolute value, then row 2: ∘'" angle (DMS), 2x2 matrix, 1x2 matrix, 2x1 matrix, 3x3 matrix, Σ, Π, first/second/nth derivative, definite integral, then indefinite integral, limit, and a box template; the text box shows the name of the selected one, e.g. `fraction`)
- 6 Libraries (list: Current Problem, gm_data, gm_fin, gm_mat, gm_net, linalg, linalgcas, ... more below)
Wizards On: unchecked by default.

### C1 Tab 2 tree (Math functions)
Top-level groups in order: Number, Angle, List, Matrix, Vector, Algebra, Trigonometry, Hyperbolic, Calculus, Probability, Statistics, Finance, Test, Base, Functions & Programs (list wraps from the last back to the first).
- Number (opens expanded): Convert to Decimal, Approximate to Fraction, Factor, Least Common Multiple, Greatest Common Divisor, Remainder, Fraction Tools ▶, Number Tools ▶, Complex Number Tools ▶.
- Algebra: Solve, Factor, Expand, Zeros, Complete The Square, Numerical Solve, Solve System of Equations ▶, Polynomial Tools ▶, Fraction Tools ▶, Convert Expression ▶, Trigonometry ▶, Complex ▶, Extract ▶.
- Syntax hints (bottom box) seen: Remainder `remain(Expr1, Expr2)`; Factor (under Number) `factor(Expr [,Var])`; Solve `solve(Equation, Var)`; Arccosh (tab 1) `arccosh(Expr)`. Group rows show only the group name in the box.

### C4 Wizards (Catalog tab 1, Wizards On checked; the checkbox is off by default)
Keys: Catalog key, tick Wizards On, press a letter to jump (typing several letters uses only the last: `normC` jumped to `ceiling(`), Down to the entry, Return.
Observed: wizard-capable entries show a wand icon at the right of the row (seen on MultReg, MultRegIntervals, MultRegTests, χ²2way, chi22way, invBinom, invBinomN, invχ², invChi2, invF, invNorm, invt, normCdf). A non-wizard entry (e.g. `ceiling(`, `nand`) pastes its name into the entry line; the bottom box shows the syntax of the selected entry (e.g. `nand` shows `BooleanExpr1 nand BooleanExpr2`, `nfMin(` shows `nfMin(Expr, Var)`, `∫(` shows `∫(Expr, Var[, Lower, Upper])`, `invt(` shows `invt(Area, df)`, `irr(` shows `irr(CF0, CFList[,CFFreq])`, `invChi2(` shows `invChi2(Area, df)`, `normCdf(` shows `normCdf(lowBound, upBound[,μ[,σ]])`).
- normCdf: dialog "Normal Cdf" with fields Lower Bound (default `-∞`), Upper Bound (empty), μ (`0`), σ (`1`), OK, Cancel; each field has a ▶ drop-down. Entered -1, Tab, 1, Tab (focus moves to μ), Return. History line: `normCdf(-1,1,0,1)` result `0.68268948`.
- invt: dialog "Inverse t" with Area and "Deg of Freedom, df" fields. OK with df empty gives "Input Error / Required field is empty! / Field # 2: / Deg of Freedom, df:" (clicking OK with the mouse did nothing here; Return after a status-bar click worked). With Area `.9`, df `5`: history `invt(0.9,5)` result `1.475884`.
- invNorm: dialog "Inverse Normal" with Area (empty), μ (`0`), σ (`1`), OK, Cancel. Area `.95`, Tab, Tab, Return: history `invNorm(0.95,0,1)` result `1.6448536`.
- binomPdf: dialog "Binomial Pdf" with Num Trials, n; Prob Success, p; X Value (greyed hint `(optional)`). n `10`, p `.5`, X blank: history `binomPdf(10,0.5)` and a list result `{0.00097656,0.00976563,0.04394531,0.117▶` (long list, truncated with ▶ at the screen edge). A second Return on the empty entry line repeated the same line. `binomCdf(` also has a wand icon (dialog not opened).
- OneVar: first dialog "One-Variable Statistics" with `Num of Lists:` spinner (default 1, up/down arrows), OK, Cancel. Second dialog: X1 List (empty), Frequency List (`1`), Category List (empty), Include Categories (empty), each with a ▶ drop-down; Tab moves down the fields, shift+Tab up. With X1 `d1`, the result is a list-style block with rows (name, value): ... `"sx := Sn-1x"` 2.1380899, `"σx := σnx"` 2., `"n"` 8., `"MinX"` 2., `"Q₁X"` 4., `"MedianX"` 4.5, `"Q₃X"` 6., `"MaxX"` 9., `"SSX := Σ(x-x̄)²"` 32. (rows above `sx` not read; values use decimal points here).
- Catalog letter-jump lands one or two rows off from where you expect (after `o` the selection sat on `or`/`ord`), so check the selected row's hint box before pressing Return.
- LinRegMx and polyRoots wizards: not run (deSolve: see the Calculus notes above).

### C1 Tab 2 tree, more groups (Wizards On checked)
- Top-level groups, full order: Number, Angle, List, Matrix, Vector, Algebra, Trigonometry, Hyperbolic, Calculus, Probability, Statistics, Finance, Test, Base, Functions & Programs, String, Math Operators (the list wraps from Math Operators back to Number; earlier note that it ended at Functions & Programs was wrong).
- Calculus: Derivative (hint `derivative`), Derivative at a Point (wand), Integral, Limit, Sum, Product, Function Minimum (`fMin(Expr, Var)`), Function Maximum, Tangent Line, Normal Line, Arc Length, Series ▶, Differential Equation Solver (wand; `deSolve(1stOr2ndODE, Var, depVar)`), Implicit Differentiation, Numerical Calculations ▶.
- Probability: Factorial (!) (`Expr!`), Number of Permutations, Number of Combinations, Random ▶, Distributions ▶.
  - Random: Number (`rand([#Trials])`), Integer, Binomial, Normal, Sample, Seed.
  - Distributions (all wand icons): Normal Pdf (`normPdf(XVal[,μ[,σ]])`), Normal Cdf, Inverse Normal, t Pdf, t Cdf, Inverse t, χ² Pdf (`χ²Pdf(XVal, df)`), χ² Cdf, Inverse χ², Binomial Pdf, Binomial Cdf, Inverse Binomial, Inverse Binomial N (`invBinomN(CumulativeProb, Prob,` ...), F Pdf, F Cdf, Inverse F, Geometric Pdf, Geometric Cdf, Poisson Pdf (`poissPdf(λ, XVal)`), Poisson Cdf.
- Number of Combinations hint `nCr(Expr1, Expr2)`. See the Statistics and Finance section below.
- Test, Base, Functions & Programs, String, Math Operators: see the section below.
- deSolve wizard: dialog "Differential Equation Solver": Equation (hint line `Example: y' = 2y`), Independent Var, Dependent Var, Condition (Optional), Condition (Optional) (hint `Example: y(0) = 1`), scrolls, OK / Cancel. Filled `y'=2*y`, `x`, `y`, `y(0)=1`, OK: the entry line receives `deSolve(y'=2·y and y(0)=1,x,y)` (conditions joined with `and`) and it is NOT evaluated until Return is pressed; result `y=ⅇ^(2·x)`.
- A caution for the builder: after open_application the software opened an extra blank document (Document3, page 1.1 "Press menu"); the original Document1 was kept as the first tab at the bottom.

### C1 Tab 2 tree: Statistics and Finance (Wizards On; wand = wizard icon)
- Statistics sub-groups: Stat Calculations ▶, List Math ▶, List Operations ▶, Distributions ▶ (same Distributions list as under Probability, not re-read), Confidence Intervals ▶, Stat Tests ▶.
- Stat Calculations (all wands): One-Variable Statistics (hint `OneVar [1,]X[,[Freq][,Category,Include]]`), Two-Variable Statistics, Linear Regression (mx+b), Linear Regression (a+bx), Median-Median Line, Quadratic Regression (`QuadReg X,Y[,[Freq][,Category,Include]]`), Cubic Regression, Quartic Regression, Power Regression, Exponential Regression, Logarithmic Regression, Sinusoidal Regression (`SinReg`), Logistic Regression (d=0), Logistic Regression (d≠0), Multiple Linear Regression; then Correlation Matrix (no wand).
- List Math: Minimum, Maximum, Mean, Median, Sum of Elements, Product of Elements (`product(List[,Start[,End]])`), Sample Standard Deviation, Sample Variance, Population Standard Deviation, Population Variance.
- Confidence Intervals (wands): z Interval (`zInterval σ,List[,Freq[,CLevel]]`), t Interval, 2-Sample z Interval, 2-Sample t Interval, 1-Prop z Interval, 2-Prop z Interval (`zInterval_2Prop x1,n1,x2,n2[,CLevel]`), Linear Reg t Intervals, Multiple Reg Intervals.
- Stat Tests (wands): z Test (`zTest μ0,σ,List[,Freq[,Hypoth]]`), t Test, 2-Sample z Test, 2-Sample t Test, 1-Prop z Test, 2-Prop z Test (`zTest_2Prop x1,n1,x2,n2[,Hypoth]`), χ² GOF, χ² 2-way Test, 2-Sample F Test, Linear Reg t Test, Multiple Reg Tests, ANOVA (`ANOVA List1,List2[,...[,List20]][,Flag]`), ANOVA 2-Way.
- Finance sub-groups: TVM Functions ▶, Amortization ▶, Cash Flows ▶, Interest Conversion ▶, Days Between Dates ▶ (contents not opened).
- List Operations sub-group not opened.

### C1 Tab 2 tree: Angle, List, Matrix, Vector, Hyperbolic (sweep with Right then Down; a few rows between the zoomed views may be unseen)
- Angle: Degrees (hint `Expr°`), Radians, Gradians, Minutes, Seconds, Degrees Minutes Seconds (`dd°mm'ss.ss"`), Polar to Rectangular x, Polar to Rectangular y, Rectangular to Polar r, Rectangular to Polar θ, Angle Input (`angle(Expr)`), Convert to DMS, Convert to Decimal Degrees, Convert to Gradians, Convert to Radians.
- List: Math ▶; Operations (Sort Ascending, Sort Descending, Cumulative Sum List, Fill, Sequence (`seq(Expr, Var, Low, High[,Step])`), Difference List, Augment, Convert List to Matrix, Convert Matrix to List, Left (`left(List[,Num])`), Mid, Right); Logic (If, Count, CountIf (`countIf(List, Criteria), where`), SumIf, Frequency).
- Matrix: Create ▶ (not opened); Transpose; Determinant (`det(squareMatrix[,Tol])`); Row-Echelon Form; Reduced Row-Echelon Form; Simultaneous; Norms (Norm, Row `rowNorm(Matrix)`, Column); Dimensions (Matrix, Row, Column); Row Operations (Swap Rows `rowSwap(Matrix, rIndex1, rIndex2)`, Row Add, Multiply Row, Multiply Row & Add); Element Operations (Dot Add, Dot Subtract `Matrix1 .- Matrix2`, Dot Multiply, Dot Divide, Dot Power); Advanced (Trace `trace(squareMatrix)`, Eigenvalues, Eigenvectors, LU Decomposition, QR Decomposition `QR Matrix, qMatrix, rMatrix[,Tol]`, Characteristic Polynomial).
- Vector: Unit Vector, Cross Product, Dot Product (`dotP(List1,List2)`), Convert to Polar, Convert to Rectangular, Convert to Cylindrical, Convert to Spherical (`Vector ▶Sphere`).
- Hyperbolic: Hyperbolic Sine, Cosine, Tangent, Cosecant, Secant, Cotangent, then Inverse Hyperbolic Sine (`sinh⁻¹(Expr)`), Cosine, Tangent, Cosecant, Secant, Cotangent.

### C1 Tab 2 tree: Test, Base, Functions & Programs, String, Math Operators (sweep; some rows may be unseen)
- Test: Equal To, Not Equal To (`Expr1 ≠ Expr2`), Less Than, Less Than or Equal To, Greater Than, Greater Than or Equal To, and (`BooleanExpr1 and BooleanExpr2`), nand, nor, not, or, xor (`BooleanExpr1 xor BooleanExpr2`).
- Base: Convert to Base 2, Convert to Base 10 (`Integer ▶Base10`), Convert to Base 16, and, nand, nor, not (`not BooleanExpr`), or, xor, ⇒, ⇔, (−) 2's complement (`−Expr`), Shift, Rotate.
- Functions & Programs: Func...EndFunc, Prgm ... EndPrgm, Local (`Local Var1[,Var2][,Var3]...`), Control (If, If...Then...EndIf (`If BooleanExpr Then`), If...Then...Else...EndIf, ElseIf...Then, For...EndFor, While...EndWhile, Loop...EndLoop, Try...Else...EndTry, ClrErr, PassErr, errCode, warnCodes, Wait (`Wait timeInSeconds`)), Transfer (Return, Cycle, Exit, Lbl, Go to Lbl (`Goto labelName`), ...); rows before `Func...EndFunc` and after `Go to Lbl` not read.
- String: Convert to String, Convert to Expression, String Dimension, Concatenate, Left, Mid (`mid(sourceList, Start[,Count])`), Right, Position in String, String Format, Character, Numeric Code (`ord(String)`).
- Math Operators (symbol rows, name shown only as a symbol; hint text for some): →, :=, _, ▶, °, ʳ, ᵍ, ′, ∠, = (`Expr1 = Expr2`), ≠, <, ≤, >, ≥ (`Expr1 ≥ Expr2`) and more not seen.

## C1 (more): tab 2 Matrix, Vector, Algebra groups (read by stepping the highlight down four rows per screenful; rows can be missing between screens)
Settings: Radian, Automatic, Real, Float 8; Catalog opened with the Catalog key (about (382,480)) on a Calculator page; Wizards On ticked.
- List (part): ... Sequence, Difference List, Augment, Convert List to Matrix, Convert Matrix to List, Mid, Right, then sub-group Logic: If, Count, SumIf, Frequency.
- Matrix: sub-group `Create` (did not expand with Right in this pass), Transpose, Determinant, Row-Echelon Form, Reduced Row-Echelon Form, Simultaneous; sub-group Norms: Norm, Row, Column; sub-group Dimensions: Matrix, Row, Column; sub-group Row Operations: Swap Rows, Row Add, Multiply Row, Multiply Row & Add; sub-group Element Operations: Dot Add, Dot Subtract, Dot Multiply, Dot Divide, Dot Power; sub-group Advanced: Trace, Eigenvalues, Eigenvectors, LU Decomposition, QR Decomposition, Characteristic Polynomial.
- Vector: Unit Vector, Cross Product, Dot Product, Convert to Polar, Convert to Rectangular, Convert to Cylindrical, Convert to Spherical.
- Algebra: Solve, Factor, Expand, Zeros, Complete The Square, Numerical Solve, then collapsed sub-groups Solve System of Equations, Polynomial Tools, Fraction Tools, Convert Expression, Trigonometry, Complex, Extract. Expanded in this pass: Convert Expression: Convert to ln, Convert to logbase, Convert to exp, Convert to sin, Convert to cos; Trigonometry: Expand, Collect; Complex: Solve, Factor, Zeros; Extract: Left, Right (more below not seen). Solve System of Equations, Polynomial Tools and Fraction Tools contents not read.
- Hyperbolic (top level, follows Algebra and a collapsed Trigonometry group): Hyperbolic Sine, Hyperbolic Cosine, Hyperbolic Tangent, Hyperbolic Cosecant, Hyperbolic Secant, Hyperbolic Cotangent (more below not seen).
- A top-level `Trigonometry` group sits between Algebra and Hyperbolic and was not opened.
Screenshot: zooms only, not saved as PNG.

## C4 (rest): wizards for polyRoots, binomCdf, LinRegMx (and PowerReg)
Settings: Radian, Automatic, Real, Float 8; Calculator page 2.3; Wizards On ticked; reached from Catalog tab 1 (Commands, alphabetical) by typing the first letter then Down, checking the hint pane before Return.
- `polyRoots(` (hint pane `polyRoots(Poly, Var)`): first dialog `Find Roots of a Polynomial`: Degree (spinner, default 2), Roots (drop-down, default Real), OK, Cancel. Second dialog `Roots of a Polynomial` with the line `a₂x² + a₁x + a₀ = 0` and fields a₂, a₁, a₀ (each with a drop-down arrow). Entered 1, -3, 2 (Tab between): it pasted `polyRoots(x²-3·x+2,x)` into the entry line (not run); Return then gave `{1,2}`.
- `binomCdf(` (hint pane `binomCdf(n, p)`): dialog `Binomial Cdf`: Num Trials, n (empty); Prob Success, p (empty); Lower Bound (default 0); Upper Bound (empty); OK, Cancel. Entered 10, 0.5, 4: it pasted and evaluated at once `binomCdf(10,0.5,0,4)` = 0.37695313 (the dialog's Return ran the entry; one more Return was not needed).
- `LinRegMx` (hint pane `LinRegMx X, Y[,[Freq][,Category, Include]]`): dialog `Linear Regression (mx+b)`: X List (empty), Y List (empty), Save RegEqn to (`f5`, the next free graph function), Frequency List (`1`), Category List, Include Categories, OK, Cancel. Entered `{1,2,3,4}` and `{2,4,5,8}`: the entry line became `LinRegMx {1,2,3,4},{2,4,5,8},1: CopyVar stat.RegEqn,f5` and it ran at once, printing a matrix: "Title" "Linear Regression (mx+b)"; "RegEqn" "m·x+b"; "m" 1.9; "b" 0.; "r²" 0.96266667; "r" 0.98115578; "Resid" "{...}" (the residual list is a string shown cut off). The regression equation was saved into f5.
- `PowerReg` (opened by mistake, hint pane `PowerReg X,Y[,[Freq][,Category,Include]]`): dialog `Power Regression` with the same six fields as LinRegMx and `Save RegEqn to: f5`.
- Hint panes copied while passing: `P▶Rx(rExpr, θExpr)`, `polyGcd(Expr1, Expr2)`, `lim(Expr, Var, Value [,Direction])`, `LinRegtIntervals X,Y[,Freq[,0[,CLev]]]`, `Lbl labelName`, `∏(Expr, Var, Low, High)`, `bal(NPmt, N, I, PV, [Pmt], [FV], [PpY], [CpY], [` (cut off), `binomPdf(` and `ceiling(` entries listed, wand icons beside `binomCdf`, `binomPdf`, `poissCdf`, `poissPdf`, `polyRoots`, `PowerReg`, `LinRegMx`, `LinRegBx`, `LinRegtIntervals`, `OneVar`, `invNorm`, `invt`.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The regression wizards write the regression equation to a graph function (`f5` here) via CopyVar, and they run on OK.

## C3: Reference Guide examples (CAS guide 3.2, PDF pages read as images)
Settings for all rows: Radian, Automatic, Real, Float 8 (Document Settings as in the other files). One Calculator page, Problem 2, page after 2.3. The emulator prints Float 8 where the guide prints Float 6, so "matches" means same value and form, not the same digit count. Screenshots: half-scale JPEG zooms of the handheld screen in `pages-shots-5/` named `c3-NN-<commands>.jpg` (NN is the order of the batches; each file shows the rows for the commands in its name; a few of the early rows, such as the Ans/and/avgRC reads, have no image). The guide examples are the first one printed on the page.

| Command | Typed | Displayed | Matches the guide? |
|---|---|---|---|
| iPart | `iPart(-1.234)` | -1. | yes |
| iPart (list) | `iPart({3/2,-2.3,7.003})` | Automatic mode: `{1,-2.,7.}`. Approximate mode: `{1.,-2.,7.}` (c3-15-ipart-approximate-mode.jpg) | the guide prints `{1.,-2.,7.}`, so the guide example was made in Approximate mode. The result depends on the Calculation Mode: Automatic keeps the exact 3/2 as an exact 1; Approximate gives 1. |
| isPrime | `isPrime(5)`, `isPrime(6)` | true, false | yes |
| tanh | `tanh(1.2)` | 0.83365461 | yes (guide 0.833655) |
| left | `left("Hello",2)` | "He" | yes. The `left({1,3,-2,4},3)` example gave `{1,3,-2}`, yes |
| right | `right("Hello",2)`; `right({1,3,-2,4},3)` | "lo"; `{3,-2,4}` | yes |
| remain (4.5 guide p.128 area) | `remain(7,3)` | 1 | yes (in this build's Catalog it ran) |
| RandSeed | `RandSeed 1` | Done | yes |
| randBin | `RandSeed 1` then `randBin(10,0.5,3)` | `{6,6,3}` | no printed example for this seed. First three values recorded |
| randBin (guide) | `RandSeed 1147`, `randBin(80,.5,3)` | `{44,34,47}` | differs from the printed guide value `{47.,41.,46.}`. Documented as observed: this build gives `{44,34,47}` for `RandSeed 1147`. Simon's view: the guide's printed value may itself be wrong, so treat the emulator's sequence as the behaviour to match, not the guide's |
| randNorm | `RandSeed 1` then `randNorm(0,1,3)` | `{0.62742879,-0.17147098,-0.55931652}` | no printed example for this seed. First three values recorded |
| randNorm (guide) | `RandSeed 1147`, `randNorm(0,1)`, `randNorm(3,4.5)` | 0.49254098; -3.5435597 | yes (guide 0.492541, -3.54356) |
| randPoly | `RandSeed 1147`, `randPoly(x,5)` | `-2·x⁵+3·x⁴-6·x³+4·x-6` | yes |
| randMat | `RandSeed 1147`, `randMat(3,3)` | `[[8,-3,6],[-2,3,-6],[0,4,-6]]` | yes |
| nand | `3 nand 4` | -1 | yes |
| nor | `3 nor 4` | -8 | yes |
| mod | `mod(-7,3)` | 2 | yes |
| nPr | `nPr(z,3)` | `z·(z-2)·(z-1)` | yes |
| ord | `ord("hello")` | 104 | yes |
| mid | `mid("Hello there",2)` | "ello there" | yes |
| tangentLine | `tangentLine(x²,x,1)` | `2·x-1` | yes |
| normalLine | `normalLine(x²,x,1)` | `3/2-x/2` | yes |
| norm | `norm([1,2;3,4])` | √30 | yes |
| sech | `sech(3)` | 1/cosh(3) (seen scrolled) | yes |
| csch | `csch(3)` | 1/sinh(3) | yes |
| coth | `coth(1.2)` | 1.1995375 | yes (guide 1.19954) |
| cot⁻¹ | `arccot(1)` | π/4 | yes (Radian) |
| sec⁻¹ | `arcsec({1,2,5})` | `{0,π/3,cos⁻¹(1/5)}` | yes |
| SortA / SortD | `{2,1,4,3}→list1`, `SortA list1`, `list1`, `SortD list1`, `list1` | `{1,2,3,4}`; `{4,3,2,1}` | yes |
| Define | `Define g(x,y)=2*x-3*y`, `g(1,2)` | Done; -4 | yes |
| DelVar | `2→a`, `DelVar a`, `a+2` | 2; Done; `a+2` | yes |
| ClearAZ | `5→b`, `ClearAZ`, `b` | 5; Done; `b` | yes |
| format | `format(1.234567,"f3")` | "1.235" | yes |
| or / and | `3 or 4`; `3 and 4`; `{1,2,3} or {3,2,1}` | 7; 0; `{3,2,3}` | yes |
| not | `not(2>=3)`; `not(x<2)` | true; `x≥2` | yes |
| mRow | `mRow(-1/3,[1,2;3,4],2)` | `[[1,2],[-1,-4/3]]` | yes |
| mRowAdd | `mRowAdd(-3,[1,2;3,4],1,2)` | `[[1,2],[0,-2]]` | yes |
| median (matrix) | `median([.2,0;1,-.3;.4,-.5])` | `[0.4,-0.3]` | yes |
| tan⁻¹ (list) | `arctan({0,.2,.5})` | `{0,0.19739556,0.46364761}` | yes (guide 0.197396, 0.463648) |
| randInt | `RandSeed 1147`, `randInt(3,10,4)` | `{4,8,6,4}` | guide example has no seed (prints `{8.,9.,4.,4.}`), so no comparison |
| solve | `solve(a*x^2+b*x+c=0,x)` | `x=(√(b²-4·a·c)-b)/(2·a) or x=-(√(b²-4·a·c)+b)/(2·a)` | yes |

Typing note: typing the opening `"` also inserts the closing one, so a typed closing `"` ends up inside the string; type the text, press Right, then continue.

C3 commands whose guide pages were read but not typed in, and commands whose guide page prints no example (syntax and output-variable tables only): ANOVA, ANOVA2way, χ²GOF, χ²Pdf, CubicReg, ExpReg, FCdf, FPdf, FTest_2Samp, geomCdf, invChi2, invF, invNorm, invt, LinRegBx, LinRegMx, LinRegtIntervals, LinRegtTest, LnReg, Logistic, LogisticD, MedMed, MultReg, MultRegIntervals, MultRegTests, OneVar, PowerReg, SinReg, tInterval, tInterval_2Samp. Pages with examples read but not typed in: and (Hex/Bin base), Ans, avgRC, bal, csc⁻¹, csch⁻¹, coth⁻¹, Define h(x)=when, frequency, Fill, irr, isVoid, nor (Bin/Hex), not, or, P▶Rx, P▶Ry, piecewise, poissCdf, randInt, randSamp, Return, RequestStr, rref, sec, sech⁻¹, solve, tan⁻¹, tmpCnv, Δtmpcnv, median, mRow, mRowAdd, xor, subMat. The rest of Group 1, Group 2 and Group 3 were not opened. Programming commands are skipped as the brief says.

## C3 (no printed example): commands run on my own data and checked against scipy
These commands print no example in the guide, so the syntax was guessed from the Catalog hint lines and the data are mine. Settings: Radian, Automatic, Real, Float 8. Data: `lx={1,2,3,4,5,6}`, `ly={2.1,3.9,6.2,7.8,10.1,12.2}` (typed with `→lx`, `→ly`). Each command was followed by `stat.results`. Screenshots: half-scale JPEG zooms in `pages-shots-5/` named `c3n-NN-<command>-statlist.jpg` (the `stat.` drop-down) and `c3n-NN-<command>-results.jpg` (the results matrix; `-upper`/`-lower` when it had to be scrolled). "scipy" values were computed in Python (scipy.stats, numpy, scipy.optimize) on the same data.

Entry note: the `stat.` drop-down lists the variables of the last command in alphabetical order. Typing letters does not filter it; pick `results` with Down presses (its position varies, so look at the list first) then Return, Return. A previous scroll of the history can leave the word `Done` in the entry line: press Escape, ctrl+a, BackSpace first.

| Command | Typed | Displayed (stat.results) | scipy / by hand | Matches? |
|---|---|---|---|---|
| LinRegBx | `LinRegBx lx,ly,1` | "Linear Regression (a+bx)", RegEqn "a+b·x", a -0.02, b 2.02, r² 0.99821067, r 0.99910493, Resid "{...}" | linregress: -0.02, 2.02, r² 0.9982106661, r 0.9991049324 | yes |
| ExpReg | `ExpReg lx,ly,1` | "Exponential Regression", RegEqn "a·b^x", a 1.8424299, b 1.404215, r² 0.94591132, r 0.97257973, Resid, ResidTrans | ln y on x: a 1.8424299, b 1.4042150, r² 0.9459113, r 0.9725797 (r is for the transformed data) | yes |
| PowerReg | `PowerReg lx,ly,1` | "Power Regression", RegEqn "a·x^b", a 2.0537749, b 0.98453167, r² 0.99810754, r 0.99905332 | ln-ln: 2.0537749, 0.9845317, 0.9981075, 0.9990533 | yes |
| LnReg | `LnReg lx,ly,1` | "Logarithmic Regression", RegEqn "a+b·ln(x)", a 1.0271695, b 5.4925677, r² 0.92589586, r 0.96223483 | 1.0271695, 5.4925677, 0.9258959, 0.9622348 | yes |
| CubicReg | `CubicReg lx,ly,1` | "Cubic Regression", RegEqn "a·x^3+b·x^2+c·x+d", a 0.00648148, b -0.04126984, c 2.037963, d 0.06666667, R² 0.99862316 | polyfit deg 3: 0.00648148, -0.04126984, 2.03796296, 0.06666667; R² 0.9986232 | yes |
| MedMed | `MedMed lx,ly,1` | "Median-Median Line", RegEqn "m·x+b", m 2.0375, b -0.08125 | by hand (thirds {1,2},{3,4},{5,6}): m 2.0375, b -0.08125 | yes |
| tInterval | `tInterval ly,1,.95` | "t Interval", CLower 3.0805522, CUpper 11.019448, x̄ 7.05, ME 3.9694478, df 5., sx := Sn-1x 3.7824595, n 6. | t interval: 3.0805522, 11.0194478, ME 3.9694478, s 3.7824595 | yes |
| tInterval_2Samp | `tInterval_2Samp lx,ly,1,1,.95,0` | "2-Sample t Interval", CLower -7.5890631, CUpper 0.4890631, x̄Diff -3.55, ME 4.0390631, df 7.3082162, x̄1 3.5, x̄2 7.05, sx1 1.8708287, sx2 3.7824595, n1 6., n2 6. | Welch: CI -7.5890631, 0.4890631, df 7.3082162 | yes (Pooled=0 gave Welch df) |
| LinRegtTest | `LinRegtTest lx,ly,1,0` | "Linear Reg t Test", Alternate Hyp "β & ρ ≠ 0", RegEqn, t 47.238425, PVal 0.0000012, df 4., a -0.02, b 2.02, s 0.17888544, SESlope 0.0427618, r² 0.99821067, r 0.99910493, Resid | t 47.2384245, p 1.20136e-06, s 0.1788854, SE 0.0427618 | yes (PVal is shown to 7 places, 0.0000012) |
| LinRegtIntervals | `LinRegtIntervals lx,ly,1,0,.95` | "Linear Reg t Interval", RegEqn, CLower 1.9012742, CUpper 2.1387258, b 2.02, ME 0.11872579, df 4., s 0.17888544, SESlope 0.0427618, a, r², r, Resid | t(.975,4)·0.0427618 = 0.1187258 | yes |
| MultReg | `MultReg ly,lx,{1,0,2,1,3,0}` | "Multiple Linear Regression", RegEqn "b0+b1·x1+b2·x2+...", b0 -0.0484375, b1 2.0171875, b2 0.0328125, ŷList, Resid, R² 0.99831158 | lstsq: -0.0484375, 2.0171875, 0.0328125, R² 0.9983116 | yes |
| SinReg | `SinReg px,py` with `px={0..9}`, `py={3.6,4.7,5,4.4,3.1,1.8,1,1.2,2.3,3.6}` | "Sinusoidal Regression", RegEqn "a·sin(b·x+c)+d", a 2.0226616, b 0.70049891, c 0.29267705, d 3.0078249 | curve_fit: 2.0226616, 0.7004989, 0.2926771, 3.0078249 | yes (radians) |
| Logistic | `Logistic qx,qy` with `qx={1..8}`, `qy={1,1.98,3.55,5.51,7.32,8.59,9.31,9.68}` | "Logistic Regression (d=0)", RegEqn "c/(1+a·ⅇ^(-b·x))", a 20.088093, b 0.80115816, c 9.9986785 | curve_fit: 20.0880933, 0.8011582, 9.9986785 | yes |
| χ²GOF | `χ²GOF {10,20,30},{20,20,20},2` | "χ² GOF", χ² 10., PVal 0.00673795, df 2., CompList "{...}" | chisquare: 10, p 0.006737947 | yes (typed χ² works) |
| FTest_2Samp | `FTest_2Samp lx,ly,1,1,0` | PVal 0.14844134 (F in the top rows, not read), dfNumer 5., dfDenom 5., sx1 1.8708287, sx2 3.7824595, x̄1 3.5, x̄2 7.05, n1 6., n2 6. | F 0.2446355, two-sided p 0.1484413 | yes (F row scrolled off, not read) |
| ANOVA | `ANOVA {1,2,3},{2,4,6},{5,6,7}` | "ANOVA", F 6., PVal 0.03703704, df 2., SS 24., MS 12., dfError 6., SSError 12., MSError 2., sp 1.4142136, CLowerList, CUpperList, x̄List | f_oneway: F 6.0, p 0.0370370 | yes |
| FCdf | `FCdf(0,2,5,8)` | 0.81700226 | f.cdf(2,5,8) 0.8170023 | yes |
| FPdf | `FPdf(1.5,5,8)` | 0.27809797 | f.pdf 0.2780980 | yes |
| invF | `invF(.95,5,8)` | 3.6874987 | f.ppf 3.6874987 | yes |
| invChi2 | `invChi2(.95,3)` | 7.8147279 (shown as invχ²) | chi2.ppf 7.8147279 | yes |
| geomCdf | `geomCdf(.2,3)` | 0.488 | 1-0.8³ = 0.488 | yes |
| invt | `invt(.975,5)` | 2.5705818 | t.ppf 2.5705818 | yes |
| invNorm | `invNorm(.975)` | 1.959964 | norm.ppf 1.959964 | yes |

Not run: ANOVA2way, MultRegIntervals, MultRegTests, LogisticD (need a matrix or a longer data set), χ²Pdf, and the F row of FTest_2Samp (scrolled off). Those are not tested against scipy.

## Run
C3 (the guide examples above, and the no-example commands run on my own data and compared with scipy, plus randBin/randNorm first three values for RandSeed 1), C4 (normCdf, invt, invNorm, binomPdf, OneVar wizards), C1 (more groups, deSolve wizard), C1 (tab list, tab 2 top-level groups, Number and Algebra items), a few syntax hints.

## Not run
C1 tabs 3 and 6 in full; the other groups' contents (Angle through Functions & Programs); sub-groups under Algebra; C2 syntax hints for groups 1 to 3 beyond the four above; C3 ANOVA2way, MultRegIntervals, MultRegTests, LogisticD, χ²Pdf and Groups 1 to 3 beyond the rows above; (C4 `binomCdf`, `LinRegMx`, `polyRoots` now done in the C4 (rest) section). C3 partly run: the examples are pictures in the PDF, so each page was opened as an image; about 30 commands typed in, the rest not typed. Reason: time in this session.

## Also seen, not covered
Catalog opened on tab 6 (last-used) rather than tab 1. The Commands tab list has a scroll bar covering the whole alphabet.
