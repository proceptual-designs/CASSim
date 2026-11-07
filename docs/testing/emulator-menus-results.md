# Emulator check: Nspire menus, keypad keys and dialogs (results)

Run on TI-Nspire CX CAS Premium Teacher Software, Handheld-page-size document (keypad + side screen layout), 2026-11-08.

**Settings used (Document Settings, checked then OK'd):** Display Digits Float 8, Angle Radian, Exponential Format Normal, Real or Complex Real, Calculation Mode Auto, CAS Mode On. The new document already had these values, so nothing needed changing.

**Method notes (read these first)**
- Screenshots are in `menu-shots/`, named `M<part>-...png`, each cropped to the handheld screen. Screenshots are named by part and item (e.g. `M1-3-algebra.png` = Part 1, menu 3).
- Pressing the digit or letter shown beside a menu item jumps to and opens it. This worked for every menu tried, including letters A to K in long lists (letters only, no `0`). Left arrow closes one submenu level.
- `▶` below means the item has a submenu. "(grey)" means the item was greyed out.
- Menu lists longer than the screen show a down-arrow. **That arrow is not reliable**: small submenus near the bottom of the screen (Algebra > Convert Expression, Algebra > Trigonometry, Calculus > Series) show it even when they have no more items. I checked those by arrow-key wrap-around (Convert Expression has exactly 5 items, Trigonometry 2, Series 3).
- Typing a letter in a Catalog list jumps to the first entry for that letter. Typing several letters does **not** filter; only the last letter counts.
- In the command dialogs, Return in a text field commits the field (selects the text) and a second Return presses OK. In several places a single Return was not enough.
- I did not compare against CASSim's source (`src/cassim/profiles/nspire_menus.py` is not in the repo checkout I could see; only `nspire.py` is in `profiles/`). "Differs from CASSim?" entries below are therefore mostly "not compared"; the raw device facts are the deliverable.
- Not run / not completed: see the list at the end.

---

## Part 1. Calculator Menu tree

Top-level `menu` key: **9 items only** (no "A Recent" or any tenth item; the menu ends at 9 and no scroll arrow shows). Screenshot: `M1-top.png`.

```
1 Actions ▶
2 Number ▶
3 Algebra ▶
4 Calculus ▶
5 Probability ▶
6 Statistics ▶
7 Matrix & Vector ▶
8 Finance ▶
9 Functions & Programs ▶
```

### 1 Actions (`M1-1-actions.png`)
```
1 Define
2 Recall Definition
3 Delete Variable
4 Clear a-z...
5 Clear History
-------------------------   (separator)
6 Insert Comment
-------------------------   (separator)
7 Library ▶     (M1-1-7-library.png)
    1 Refresh Libraries
    2 Insert "\" character
    3 Create Library Shortcut
    4 Define LibPriv
    5 Define LibPub (Show in Catalog)
8 Lock ▶        (M1-1-8-lock.png)
    1 Lock Variable
    2 Unlock Variable
    3 Get Lock Info
```

### 2 Number (`M1-2-number.png`)
```
1 Convert to Decimal
2 Approximate to Fraction
3 Factor
4 Least Common Multiple
5 Greatest Common Divisor
6 Remainder
7 Fraction Tools ▶   (M1-2-7-fraction-tools.png)
    1 Proper Fraction
    2 Get Numerator
    3 Get Denominator
    4 Common Denominator
8 Number Tools ▶     (M1-2-8-number-tools.png)
    1 Round
    2 Integer Part
    3 Fractional Part
    4 Sign
    5 Mod
    6 Floor
    7 Ceiling
9 Complex Number Tools ▶   (M1-2-9-complex-number-tools.png)
    1 Complex Conjugate
    2 Real Part
    3 Imaginary Part
    4 Polar Angle
    5 Magnitude
    6 Convert to Polar
    7 Convert to Rectangular
```
Note: there is **no "getNum/getDenom" by that name**; the items are "Get Numerator" and "Get Denominator" under Number > Fraction Tools (and again under Algebra > Fraction Tools).

### 3 Algebra (`M1-3-algebra.png`, tail `M1-3-algebra-tail.png`)
```
1 Solve
2 Factor
3 Expand
4 Zeros
5 Complete the Square
6 Numerical Solve
7 Solve System of Equations ▶   (M1-3-7-solve-system.png)
    1 Solve System of Equations...
    2 Solve System of Linear Equations...
8 Polynomial Tools ▶   (M1-3-8-polynomial-tools.png)
    1 Find Roots of Polynomial...
    2 Real Roots of Polynomial
    3 Complex Roots of Polynomial
    4 Remainder of Polynomial
    5 Quotient of Polynomial
    6 Greatest Common Divisor
    7 Coefficients of Polynomial
    8 Degree of Polynomial      (list reached the bottom of my screenshot at 8; I did not confirm whether more follow)
9 Fraction Tools ▶   (M1-3-9-fraction-tools.png)
    1 Proper Fraction
    2 Get Numerator
    3 Get Denominator
    4 Common Denominator
A Convert Expression ▶   (M1-3-A-convert-expression.png)
    1 Convert to ln
    2 Convert to logbase
    3 Convert to exp
    4 Convert to sin
    5 Convert to cos
B Trigonometry ▶   (M1-3-B-trigonometry.png)
    1 Expand
    2 Collect
C Complex ▶   (M1-3-C-complex.png)
    1 Solve
    2 Factor
    3 Zeros
D Extract ▶   (M1-3-D-extract.png)
    1 Left
    2 Right
```
**Settled:** Algebra has Solve (1), Factor (2), Expand (3), Zeros (4), Complete the Square (5), Numerical Solve (6), Solve System of Equations (7), Polynomial Tools (8), Fraction Tools (9), Convert Expression (A). It also has Trigonometry (B), Complex (C), Extract (D). "Complete the Square" is a plain item at 5, not under a submenu.

### 4 Calculus (`M1-4-calculus.png`, tail `M1-4-calculus-tail.png`)
```
1 Derivative
2 Derivative at a Point...
3 Integral
4 Limit
5 Sum
6 Product
7 Function Minimum
8 Function Maximum
9 Tangent Line
A Normal Line
B Arc Length
C Series ▶   (M1-4-C-series.png)
    1 Taylor Polynomial
    2 Generalized Series
    3 Dominant Term
D Differential Equation Solver...
E Implicit Differentiation
F Numerical Calculations ▶   (M1-4-F-numerical-calculations.png)
    1 Numerical Derivative at a Point
    2 Central Difference Quotient with Step
    3 Numerical Integral
    4 Numerical Function Minimum
    5 Numerical Function Maximum
```
There is no Calculus > "Numerical Derivative" submenu; numerical derivative items are under F Numerical Calculations. **Arc Length exists (B).**

### 5 Probability (`M1-5-probability.png`)
```
1 Factorial (!)
2 Permutations
3 Combinations
4 Random ▶   (M1-5-4-random.png)
    1 Number
    2 Integer
    3 Binomial
    4 Normal
    5 Sample
    6 Seed
5 Distributions ▶   (M1-5-5-distributions.png, tail M1-6-5-distributions-tail.png)
    1 Normal Pdf...
    2 Normal Cdf...
    3 Inverse Normal...
    4 t Pdf...
    5 t Cdf...
    6 Inverse t...
    7 χ² Pdf...
    8 χ² Cdf...
    9 Inverse χ²...
    A Binomial Pdf...
    B Binomial Cdf...
    C Inverse Binomial...
    D Inverse Binomial N...
    E F Pdf...
    F F Cdf...
    G Inverse F...
    H Geometric Pdf...
    I Geometric Cdf...
    J Poisson Pdf...
    K Poisson Cdf...
```
The Statistics > Distributions submenu is the **same list, same letters** (`M1-6-5-distributions.png`).
"Random Sample" exists as Probability > Random > **5 Sample**.

### 6 Statistics (`M1-6-statistics.png`)
```
1 Stat Calculations ▶
2 Stat Results            (no arrow)
3 List Math ▶
4 List Operations ▶
5 Distributions ▶         (same 20 items as Probability > Distributions)
6 Confidence Intervals ▶
7 Stat Tests ▶
```
**6.1 Stat Calculations** (`M1-6-1-stat-calculations.png`, tail `M1-6-1-stat-calculations-tail.png`):
```
1 One-Variable Statistics...
2 Two-Variable Statistics...
3 Linear Regression (mx+b)...
4 Linear Regression (a+bx)...
5 Median-Median Line...
6 Quadratic Regression...
7 Cubic Regression...
8 Quartic Regression...
9 Power Regression...
A Exponential Regression...
B Logarithmic Regression...
C Sinusoidal Regression...
D Logistic Regression (d=0)...
E Logistic Regression (d≠0)...
F Multiple Linear Regression...
G Correlation Matrix
```
(item G shows no `...` in the screenshot)

**6.3 List Math** (`M1-6-3-list-math.png`, tail `M1-6-3-list-math-tail.png`):
```
1 Minimum
2 Maximum
3 Mean
4 Median
5 Sum of Elements
6 Product of Elements
7 Sample Standard Deviation
8 Sample Variance
9 Population Standard Deviation
A Population Variance
```
**6.4 List Operations** (`M1-6-4-list-operations.png`, tail `M1-6-4-list-operations-tail.png`):
```
1 Sort Ascending
2 Sort Descending
3 Cumulative Sum List
4 Fill
5 Sequence
6 Difference List
7 Augment
8 Convert List to Matrix
9 Convert Matrix to List
A Left
B Mid
C Right
```
**6.6 Confidence Intervals** (`M1-6-6-confidence-intervals.png`):
```
1 z Interval...
2 t Interval...
3 2-Sample z Interval...
4 2-Sample t Interval...
5 1-Prop z Interval...
6 2-Prop z Interval...
7 Linear Reg t Intervals...
8 Multiple Reg Intervals...
```
**6.7 Stat Tests** (`M1-6-7-stat-tests.png`, tail `M1-6-7-stat-tests-tail.png`):
```
1 z Test...
2 t Test...
3 2-Sample z Test...
4 2-Sample t Test...
5 1-Prop z Test...
6 2-Prop z Test...
7 χ² GOF...
8 χ² 2-way Test...
9 2-Sample F Test...
A Linear Reg t Test...
B Multiple Reg Tests...
C ANOVA...
D ANOVA 2-Way...
```
Existing in the device but possibly missing in CASSim: Fill, Sequence, Difference List (List Operations 4, 5, 6); Random Sample (Probability > Random > 5).

### 7 Matrix & Vector (`M1-7-matrix-vector.png`, tail `M1-7-matrix-tail.png`)
```
1 Create ▶   (M1-7-1-create.png, tail M1-7-1-create-tail.png)
    1 Matrix...
    2 Zero Matrix
    3 Identity
    4 Diagonal
    5 Random Matrix
    6 Fill
    7 Submatrix
    8 Augment
    9 Column Augment
    A Construct Matrix
2 Transpose
3 Determinant
4 Row-Echelon Form
5 Reduced Row-Echelon Form
6 Simultaneous
7 Norms ▶   (M1-7-7-norms.png)
    1 Norm
    2 Row
    3 Column
8 Dimensions ▶   (M1-7-8-dimensions.png)
    1 Matrix
    2 Row
    3 Column
9 Row Operations ▶   (M1-7-9-row-operations.png)
    1 Swap Rows
    2 Row Add
    3 Multiply Row
    4 Multiply Row & Add
A Element Operations ▶   (M1-7-A-element-operations.png)
    1 Dot Add
    2 Dot Subtract
    3 Dot Multiply
    4 Dot Divide
    5 Dot Power
B Advanced ▶   (M1-7-B-advanced.png)
    1 Trace
    2 LU Decomposition
    3 QR Decomposition
    4 Eigenvalues
    5 Eigenvectors
    6 Characteristic Polynomial
C Vector ▶   (M1-7-C-vector.png)
    1 Unit Vector
    2 Cross Product
    3 Dot Product
    4 Convert to Polar
    5 Convert to Rectangular
    6 Convert to Cylindrical
    7 Convert to Spherical
```
There is **no submenu called "Decompositions"**: LU and QR decomposition are under B Advanced, together with Trace, Eigenvalues, Eigenvectors, Characteristic Polynomial. Fill and Submatrix exist under Create.

### 8 Finance (`M1-8-finance.png`)
```
1 Finance Solver...
2 TVM Functions ▶   (M1-8-2-tvm-functions.png)
    1 Number of Periods
    2 Interest Rate per Year
    3 Present Value
    4 Payment Amount
    5 Future Value
3 Amortization ▶   (M1-8-3-amortization.png)
    1 Amortization Table
    2 Balance
    3 Interest Paid
    4 Principal Paid
4 Cash Flows ▶   (M1-8-4-cash-flows.png)
    1 Net Present Value
    2 Internal Rate of Return
    3 Modified Internal Rate of Return
5 Interest Conversion ▶   (M1-8-5-interest-conversion.png)
    1 Nominal Interest Rate
    2 Effective Interest Rate
6 Days between Dates ▶   (M1-8-6-days-between-dates.png)
    1 Month Day Format
    2 Day Month Format
```

### 9 Functions & Programs (`M1-9-functions-programs.png`)
```
1 Program Editor ▶   (M1-9-1-program-editor.png)
    1 New...
    2 Open...
    3 Import...
    4 View...
2 Func...EndFunc
3 Prgm...EndPrgm
4 Local
5 Control ▶   (M1-9-5-control.png, tail M1-9-5-control-tail.png)
    1 If
    2 If...Then...EndIf
    3 If...Then...Else...EndIf
    4 ElseIf...Then
    5 For...EndFor
    6 While...EndWhile
    7 Loop...EndLoop
    8 Try...Else...EndTry
    9 ClrErr
    A PassErr
    B errCode
    C warnCodes
    D Wait
6 Transfer ▶   (M1-9-6-transfer.png)
    1 Return
    2 Cycle
    3 Exit
    4 Lbl
    5 GoTo Lbl
    6 Stop
7 I/O ▶   (M1-9-7-io.png)
    1 Disp
    2 DispAt
    3 Request
    4 RequestStr
    5 Text
    6 getKey
    ------ separator
    7 Get
    8 GetStr
    9 Send
    ------ separator
    A RefreshProbeVars
8 Mode ▶   (M1-9-8-mode.png)
    1 Display Digits ▶
    2 Angle ▶
    3 Exponential Format ▶
    4 Real or Complex ▶
    5 Auto or Approx ▶
    6 Vector Format ▶
    7 Base ▶
    8 Unit System ▶
    9 Get Mode
    A Get Language Info
    B Get Platform Info     (the Mode sub-submenus were not opened)
9 Add New Line
```

### Answers to the specific questions in Part 1
- Algebra has Complete the Square (5), Zeros (4), Factor (2), Expand (3), Numerical Solve (6), Polynomial Tools (8), Fraction Tools (9), Convert Expression (A). Numbers are as listed above.
- Exists on the device: Recall Definition (Actions 2), Clear History (Actions 5), Insert Comment (Actions 6), Approximate to Fraction (Number 2), Get Numerator / Get Denominator (Fraction Tools, under Number and under Algebra), Arc Length (Calculus B), Random Sample (Probability > Random > 5 Sample), Fill (List Operations 4, Matrix Create 6), Difference List (List Operations 6).
- The Catalog also has `getNum(`/`getDenom(`? Not checked.

---

## Part 2. Other menus: contents and order

### Doc menu (`doc` key) (`M2-doc-menu.png`)
Items 1 to 9:
```
1 File ▶     (M2-doc-file.png)
    1 New Document   (Ctrl+N)
    2 Open Document  (Ctrl+O)
    3 Close          (Ctrl+W)
    4 Save           (Ctrl+S)
    5 Save As...
    6 Send           (grey)
    7 View copyright information
2 Edit ▶     (M2-doc-edit.png)
    1 Undo (Ctrl+Z)
    2 Redo (Ctrl+Y)   (grey)
    3 Cut (Ctrl+X)    (grey)
    4 Copy (Ctrl+C)   (grey)
    5 Paste (Ctrl+V)
    6 Delete
    7 Color ▶         (grey)
3 View ▶     (M2-doc-view.png)
    1 Back (Ctrl+◀)      (grey)
    2 Forward (Ctrl+▶)   (grey)
    3 Page Sorter (Ctrl+▲)
4 Insert ▶   (M2-doc-insert.png)
    1 Problem
    2 Page (Ctrl+I)
    3 Calculator
    4 Graphs
    5 Geometry
    6 Lists & Spreadsheet
    7 Data & Statistics
    8 Notes
    9 Vernier DataQuest™
    A Widget
    (a down-arrow shows; I did not scroll to see whether more follow, e.g. Python, Program Editor)
5 Page Layout ▶   (M2-doc-pagelayout.png)
    1 Custom Split
    2 Select Layout ▶
    3 Select App (Ctrl+K)
    4 Swap Applications   (grey)
    5 Delete Application
    6 Delete Page
    7 Group (Ctrl+4)      (grey)
    8 Ungroup (Ctrl+6)    (grey)
6 Refresh Libraries
7 Settings & Status ▶   (M2-doc-settings-status.png)
    1 Change Language...
    2 Document Settings...
    3 Handheld Setup...
    4 Status...
    5 Login...
    6 Restore Factory Defaults...
8 Login...
9 Press-to-Test ▶   (M2-doc-presstotest.png)
    1 Exit Press-to-Test       (grey)
    2 Transfer Press-to-Test   (grey)
    3 Help
```
Routes: Insert > 1 Problem; Insert > 3 Calculator; Settings & Status = 7, Document Settings = 7 then 2 (the title label on the screen reads "Documents"). Screenshot of Document Settings: `M0-document-settings.png`.

### Trig menu (`trig` key) (`M2-trig-menu.png`)
A grid (not a list): 2 rows × 6 columns.
- Row 1: `sin  cos  tan  csc  sec  cot`
- Row 2: `sin⁻¹  cos⁻¹  tan⁻¹  csc⁻¹  sec⁻¹  cot⁻¹`
The highlight opened on `cos` (last used). No hyperbolic row.

### Templates menu (templates key) (`M2-templates-palette.png`)
An **icon grid** (not a list): 3 rows, 11 + 11 + 3 icons. Reading left to right, top to bottom, going by icon shape and the order recorded in the `vce-cas-solver` skill (I did not hover to see names; the Catalog "Math Expression Templates" tab names the first one "fraction"):
- Row 1: fraction, power `□^□`, square root, nth root, `e^□`, log with base, 2-piece piecewise, N-piece piecewise, 2-equation system, N-equation system, absolute value.
- Row 2: degrees-minutes-seconds (`° ' "`), 2×2 matrix, 1×2 matrix, 2×1 matrix, m×n matrix, Σ, Π, d/dx, d²/dx², dⁿ/dxⁿ, definite integral.
- Row 3: indefinite integral, limit, subscript box.
The highlight started on the m×n matrix icon (last used). The same 3-row grid appears under Catalog tab 5.

### Catalog (book key) (`M2-catalog-*.png`)
The book key is the **second** key right of the 9 key (the first is the templates key). The Catalog opens in the tab last used.
Six tabs along the top:
1. **Catalog** (list of commands, alphabetical; hint pane below; "Wizards On" checkbox)  `M2-catalog-tab1-catalog.png`
2. **Math functions by category**: Number, Angle, List, Matrix, Vector, ... (collapsible tree)  `M2-catalog-tab2-math-functions.png`
3. **Units**: Conversion Assistant, Conversion Symbol (▶), Constants, Length, Area, ...  `M2-catalog-tab3-units.png`
4. **Symbols** (11-column grid, scrolls; see the shots `M2-catalog-tab4-symbols-a.png` and `M2-catalog-symbols-b..g.png`)
5. **Math Expression Templates** (same 3-row icon grid as the templates key)  `M2-catalog-tab5-templates.png`
6. **Library**: Current Problem, gm_data, gm_fin, gm_mat, gm_net (tree)  `M2-catalog-tab6-library.png`

Pressing a digit 1 to 6 while the Catalog is open switches to that tab.

Catalog tab 1 entries: first entries are `abs(`, `amortTbl(`, `and`, `angle(`, `ANOVA`, ... (`M2-catalog-first-entries.png`). Last entries are `⇔`, `e^(`, `10^(`, `^2`, `^-1` (`M2-catalog-last-entries.png`). Symbols and Greek letters sort around `Δ`, `E`, `Π`, `Σ`... in unexpected places (for example `ΔtmpCnv(` sits at the start of the t group, `∫(` after `intDiv(`, `Σ(` between `subMat(` and `sum(`, `Π(` after `rref`... before `prodSeq(`).
**Does typing a letter jump?** Yes, it jumps to the first entry with that letter (e.g. `s` goes to `sec(`) (`M2-catalog-letter-jump-s.png`). Typing several letters does not narrow the list; each letter jumps again, so `solve` ends on the `e` group.
The hint pane shows each overload on its own line (see Part 5). The button left of "Wizards On" toggles a larger list with a one-line hint.

**Symbols tab (tab 4), re-captured 2026-11-08.** The grid is 11 columns wide. The blue button under the grid toggles a taller view (about 5 rows) with the name of the highlighted symbol in a field below. Rows were read cell by cell. Rows 1 to 3 have their names confirmed from that field; the rest are read from enlarged screenshots (`M2-symbols-grid-01.png` to `-13.png`, in order down the grid). Down-arrow reaches the end at the row ending `„`.

Rows 1 to 3 (name shown by the device in brackets):
```
R1  π (Greek small letter pi)   e (natural number e)   i (imaginary square root of minus one)
    ᴇ (scientific notation exponent)   ∞ (infinity)   θ (Greek small letter theta)
    → (rightwards arrow, sto operator)   _ (underscore)   ▶ (black right pointing triangle, conversion)
    ° (degree sign)   ʳ (superscript small r, radians)
R2  ᵍ (superscript small g, grads)   ' (apostrophe)   ∠ (angle)   = (equals sign)   ≠ (not equal to)
    < (less than sign)   ≤ (less than or equal to)   > (greater than sign)   ≥ (greater than or equal to)
    (−) (negate (-) sign)   + (plus sign)
R3  − (minus sign)   * (asterisk, multiplication sign)   · (middle dot, multiplication sign)
    × (multiplication sign)   / (slash, division sign)   ÷ (division sign)
    ^ (circumflex, exponent operator)   ± (plus minus sign)   ᵀ (superscript capital T, matrix transpose)
    √ (square root)   ∏ (n-ary product)
```
Rows 4 to 7 (glyphs read from screenshots; only Σ in R4 was name-confirmed, as "n-ary summation"):
```
R4  ∑  d  ∫  !  ©  @  #  $  %  &  |
R5  "  :  ;  ,  .  ?  (  )  {  }  [
R6  ]  x̄  ȳ  Σ  μ  σ  F  χ  ²  ⁻¹  ₁          (stat-style symbols; ² and ⁻¹ are raised, ₁ is lowered)
R7  ₂  ₃  p̂  ŷ  c  n  Δ  µ  Ω  Α  Β          (c and n italic; the last two are Greek capital alpha, beta)
```
Greek capitals, then Greek small letters, then arrows and shapes:
```
R8   Γ Δ Ε Ζ Η Θ Ι Κ Λ Μ Ν
R9   Ξ Ο Π Ρ Σ Τ Υ Φ Χ Ψ Ω
R10  α β γ δ ε ζ η θ ι κ λ
R11  μ ν ξ ο π ρ σ τ υ φ χ
R12  ψ ω ← ↑ → ↓ ↔ ↕ ↦ ↵ ⇐
R13  ⇒ ⇔ ⇥ ⇧ ⌐(TI step icon, named "TI step") ◿ ▪ □ ▲ △ ▴
R14  ▶ ▸ ▼ ▾ ◀ ◂ ◆ ☺ ★ ✓ (a slash-like mark)
R15  $ ¢ £ € ¥ ¤ ∀ ∃ ∄ ∅ ∆
R16  ∇ ∈ ∉ ∊ ∋ ∌ ∍ ▮ ∂ ∓ ·
R17  · ∝ ∟ ∠ ∡ (named "measured angle") ∣ ∤ ∥ ∦ ∧ ∨
R18  ∩ ∪ ∴ ∵ ≃ ≅ ≈ ≟ ≡ ≢ ⊂
R19  ⊆ ⊙ ⊥ ¼ ½ ¾ ¿ ¬ ℂ ℕ ℙ
R20  ℚ ℝ ℤ ℎ  then five small TI icons (wrench, and other calculator-feature icons) and two half-filled circles ◑ ◐
R21  0 1 2 3 4 5 6 7 8 9 (blank)
R22  A B C D E F G H I J K
R23  L M N O P Q R S T U V
R24  W X Y Z a b c d e f g
R25  h i j k l m n o p q r
R26  s t u v w x y z À Á Â
```
After that come the accented Latin letters, in Unicode order and 11 per row (À to ſ, including the Latin Extended-A block Ā ā Ă ă Ą ą Ć ć ... Ž ž ſ), then Ǻ ǻ Ǽ ǽ Ǿ ǿ, superscripts ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁺ ⁻ ⁻¹ ⁽ ⁾ ⁿ, subscripts ₀ to ₉ and ₊ ₋ ₍ ₎, and a final block of punctuation (` \ • ‣ … ~ ¡ ¦ § ¨ ´ ¯ ® ™ ¶ ¸ « » ‹ › ‚ „ and a few dashes and quotes). The last three rows are small in the screenshots and are the least certain part of this transcription. Names for rows 13 to 26 beyond those quoted above were not individually read.

Notes: the first four rows are the commonly used ones. `e` and `i` here are the Euler constant and the imaginary unit (shown italic), as in the π▸ menu. The scientific-notation exponent is `ᴇ`, shown as a small capital E.

### Variables menu (`var` key) (`M2-var-menu.png`)
With `a:=1`, `f(x):=x^2`, `l:={1,2}` defined: a small popup lists **a, f, l**, each with a type icon (number, function, list). Functions and variables are **mixed**, in **alphabetical order** by name. No numbers or letters are shown beside the items.

### Relations menu (ctrl+=) (`M2-relations-menu.png`)
- Clicking the on-screen ctrl key then the `=` key opens a small grid: row 1 `>  <  ≠`; row 2 `≥  ≤  |`.
- Using the physical-keyboard chord `ctrl+=` (through the automation key tool) did **not** open the menu; it inserted `≠` straight onto the entry line (`Ans≠`). Probably a keyboard mapping (one of the keyboard shortcuts for ≠), not the on-screen key.

### Punctuation menu (?!▸ key) (`M2-punctuation-menu.png`)
Grid, 6 per row:
- Row 1: `? ! $ ° ' %`
- Row 2: `" : ; _ \` and a blank cell.

### Symbols menu (π▸ key) (`M2-symbols-menu.png`)
Grid, 5 per row:
- Row 1: `π  i  ∞  e  θ` (the `i` and `e` are bold italic, the imaginary unit and Euler's number)
- Row 2: `°  r  g  '` and a blank cell (degree, radian, gradian, prime).

---

## Part 3. Keys whose effect we are unsure of

All run on the Calculator page by clicking the on-screen keys (ctrl, shift then the key).

| Key | Observed | Screenshot |
|---|---|---|
| ctrl+del | Clears the whole entry line (cursor was in the middle of `abc+12`; the whole line went). It did not clear once, in a run right after I had pressed shift+⏎ (shift was probably still armed); repeated later uses always cleared. | `M3-ctrl-del.png` |
| touchpad centre click | With `5+3` typed: no visible change (no evaluation). | `M3-touchpad-click.png` |
| ⏎ key (bottom right of keypad) | With `5+3` typed: no visible change on the Calculator page (did not evaluate). | `M3-enter-key.png` |
| shift+⏎ | No visible change. | `M3-shift-enter-key.png` |
| π▸ | Opens the Symbols menu (Part 2). | `M2-symbols-menu.png` |
| shift+π▸ | Nothing visible (no menu, nothing inserted). | `M3-shift-pi-key.png` |
| ctrl+^ | Inserts the **nth-root template** `ⁿ√□`; the first slot is the index (I typed 3 and it went to the index, giving `³√□`). | `M3-ctrl-caret-nthroot.png` |
| ctrl+× | Inserts a **pair of string quotes**, cursor between them (typed `hi` gives `"hi"`). | `M3-ctrl-times-quote.png` |
| ctrl+10ˣ | Inserts the **log with base template** `log□(□)` (base slot first). | `M3-ctrl-10x-log.png` |
| ctrl+esc | With `12` just typed on an empty line, the line became empty. This is consistent with undo of the typing; I did not test undo after Enter. | `M3-ctrl-esc.png` |
| shift then a letter | Shift then `B` key gave a capital italic `B`. After it, the title bar showed a **CAPS** indicator which stayed on in later screenshots (not understood: the indicator did not change what I typed with the computer keyboard). | `M3-shift-letter.png` |
| ctrl+( | Inserts a **square-bracket pair** `[□]`. | `M3-ctrl-paren-open.png` |
| ctrl+) | Inserts a **brace pair** `{□}`. | `M3-ctrl-paren-close.png` |

The Scratchpad key (the notepad key to the left of the touchpad, labelled `save`) opens the Scratchpad (Calculator and Graphs tabs): `M3-scratchpad-key.png`. This is not the Catalog.

---

## Part 4. Command dialogs: fields, order and what gets pasted

Settings: Radian, Auto, Real, Float 8. Data for statistics: `x:={1,2,3,4,5}`, `y:={2,4,5,4,5}` (not `{1,2,3,4,5}` for y, to avoid a perfect fit). `a:=1`, `f(x):=x^2`, `l:={1,2}` were also defined.

**Summary of behaviour:** the statistics, regression and distribution dialogs **fire and run on OK** and show the result straight away. The Derivative at a Point, Solve System of Equations and Matrix dialogs **only paste a template** (you fill in and press Return). Find Roots of Polynomial pasted a ready command (the cursor is at the end); Return then runs it.

### 4.1 Calculus > Derivative at a Point... (`4.2`)
Settings: as above.
Observed: Dialog "Derivative at a Point": `Variable:` x (default, selected), `Value:` (blank), `Derivative:` drop-down with `1st Derivative` (default), `2nd Derivative`, `nth Derivative`; OK, Cancel.
Pasted text: the **d/dx template with an empty box**: `d/dx(□)|x=2` (value 2 entered). On the entry line the box is selected; I typed `f(x)` and Return, giving 4. Not run by OK.
Screenshots: `M4-1-deriv-point-dialog.png`, `M4-1-deriv-point-dropdown.png`, `M4-1-deriv-point-pasted.png`, `M4-1-deriv-point-result.png`.

### 4.1b Calculus > Numerical Calculations > Numerical Derivative at a Point (`4 F 1`) (re-checked 2026-11-08)
Observed: **no dialog**. It pastes the bare text `nDerivative(` on the entry line with the cursor inside the bracket (the closing bracket is added when typing).
**Catalog syntax hint (verbatim):** `nDerivative(Expr, Var=Value [,Order])` and `nDerivative(Expr, Var [,Order])|Var=Value`.
The first attempt in this file failed because I typed the arguments as `Expr,Var,Value` (comma form). The device **returns that form unevaluated**, as it did for `nDerivative(t^2,t,3)` (shown back unchanged). The correct form is `Var=Value`:
- `nDerivative(t^2,t=3)` gives **6**.
- `nDerivative(abs(t),t=0)` gives **undef**.
Another oddity: `nDerivative(f(x),x,2)` with `x` already holding the list `{1,2,3,4,5}` returned the list `{2,2,2,2,2}` (not an error). I did not work out why; `x` held a list at that point, so treat that result as an artefact of my setup.
Screenshots: `M4-1-nderivative-pasted.png`, `M4-1-nderivative-hint.png` (the Catalog hint), `M4-1-nderivative-result-fixed.png` (the unevaluated comma-form lines, then `t=3` giving 6 and `abs(t)` giving undef).
Differs from CASSim? not compared; CASSim should accept the `Var=Value` form.

### 4.2 Algebra > Solve System of Equations > Solve System of Equations...
Observed: Dialog "Solve a System of Equations": `Number of equations:` (spinner, default 2), `Variables:` x,y (default), hint text "Enter variable names separated by commas"; OK, Cancel. It asks for the number of equations and the variables first; there is no separate grid dialog.
Pasted text: `solve(` + the **2-row system template (brace with two empty rows)** + `,{x,y})`; i.e. `solve({[ ][ ]},{x,y})` with a brace template, not a `solve({..},{..})` text. Entered `x+y=3` (Tab) `x-y=1`, Return, got `x=2 and y=1`.
Not run by OK. The second item 7.2 "Solve System of Linear Equations..." was not opened.
Screenshots: `M4-2-solve-system-dialog.png`, `M4-2-solve-system-pasted.png`, `M4-2-solve-system-result.png`.

### 4.3 Algebra > Polynomial Tools > Find Roots of Polynomial...
Observed: **two dialogs**. (1) "Find Roots of a Polynomial": `Degree:` spinner (default 2), `Roots:` drop-down (Real by default; other options not opened); OK, Cancel. (2) "Roots of a Polynomial": the line `a₂x² + a₁x + a₀ = 0`, then fields `a₂=`, `a₁=`, `a₀=`, each with a drop-down arrow; OK, Cancel.
Pasted text (after entering 1, -3, 2): `polyRoots(x^2-3·x+2,x)` (shown as x²−3·x+2) on the entry line; Return gave `{1,2}`.
Screenshots: `M4-3-polyroots-dialog1.png`, `M4-3-polyroots-dialog2.png`, `M4-3-polyroots-pasted.png`, `M4-3-polyroots-result.png`.

### 4.4 Matrix & Vector > Create > Matrix...
Observed: Dialog "Create a Matrix": `Number of rows:` (default 2), `Number of columns:` (default 2), both spinners; OK, Cancel.
Pasted: an **empty 2×2 matrix template** (square brackets with four empty dotted boxes), nothing else (no command name, no variable).
Screenshots: `M4-4-matrix-dialog.png`, `M4-4-matrix-template.png`.

### 4.5 Statistics > Stat Calculations > One-Variable Statistics... and Two-Variable Statistics...
**One-Variable:** two dialogs. (1) "One-Variable Statistics": `Num of Lists:` spinner (default 1). (2) fields `X1 List:`, `Frequency List:` (default `1`), `Category List:`, `Include Categories:` (each with a drop-down arrow); OK, Cancel. There are **no** "1st Result Column" or "Show on the page" fields on the Calculator page (those belong to the spreadsheet).
Pasted text: `OneVar x,1: stat.results`. It **ran on OK** and `stat.results` was **shown at once** (no extra Enter): Title "One-Variable Statistics", x̄ 3., Σx 15., Σx² 55., sx := Sn-1X 1.5811388, σx := σnX 1.4142136, n 5., MinX 1., Q₁X 1.5, MedianX 3., Q₃X 4.5, MaxX 5., SSX := Σ(x−x̄)² 10. (the display shows a trailing decimal point on whole numbers).
**Two-Variable:** **no** Num of Lists step; the dialog opens straight onto `X List:`, `Y List:`, `Frequency List:` (blank), `Category List:`, `Include Categories:`. With X List empty, OK gives a dialog "Input Error / Required field is empty! / Field # 1: / X List:". Pasted and run on OK: `TwoVar x,y,1: stat.results`; result table starts Title "Two-Variable Statistics", x̄ 3., Σx 15., Σx² 55., sx 1.5811388, σx 1.4142136, n 5., ȳ 4., Σy 20., Σy² 86., ... (the rest scrolls).
Screenshots: `M4-5-onevar-dialog1.png`, `M4-5-onevar-dialog2.png`, `M4-5-onevar-header.png`, `M4-5-onevar-result.png`, `M4-5-twovar-error.png`, `M4-5-twovar-dialog.png`, `M4-5-twovar-header.png`, `M4-5-twovar-result.png`.

### 4.6 Regressions
**Linear Regression (mx+b)...:** fields `X List:`, `Y List:`, `Save RegEqn to:` (default `f1`), `Frequency List:` (default `1`), `Category List:`, `Include Categories:`. Pasted and run on OK: `LinRegMx x,y,1: CopyVar stat.RegEqn,f1: stat.results` (the line is cut off at the right edge of the screen after `...stat.RegEqn,f1: sta`). Result shown at once: Title "Linear Regression (mx+b)", RegEqn "m·x+b", m 0.6, b 2.2, r² 0.6, r 0.77459667, Resid "{...}".
**Quadratic Regression...:** same six fields, `Save RegEqn to:` default `f2`. Pasted and run: `QuadReg x,y,1: CopyVar stat.RegEqn,f2: stat.results`. Result: Title "Quadratic Regression", RegEqn "a·x^2+b·x+c", a −0.28571429, b 2.3142857, c 0.2, R² 0.79047619, Resid "{...}".
Screenshots: `M4-6-linreg-dialog.png`, `M4-6-linreg-result.png`, `M4-6-quadreg-dialog.png`, `M4-6-quadreg-result.png`.

### 4.7 Finance > Finance Solver...
Observed: a window "Finance Solver" (not a small dialog) with fields in order: `N:` 0., `I(%):` 0., `PV:` 0., `Pmt:` 0., `FV:` 0., `PpY:` 1 (spinner), `CpY:` 1 (spinner), `PmtAt:` END (drop-down). The first five have a drop-down arrow. The footer reads "Press ENTER to calculate" plus the name of the highlighted field (for example "Number of Payments, N", "Edit Payments / Yr, PpY", "Set Annuity, PmtAt").
How it solves: fill the known fields, Tab to the unknown field, press Return; the unknown field is boxed and filled, the footer reads "Finance Solver info stored into tvm.n, tvm.i, tvm.pv, tvm.pmt, ...". Test: N 12, I 6, PV 10000, FV 0, PpY 12, CpY 12, solve for Pmt gave −860.6642970… (the field shows more digits than fit). I typed PpY and CpY separately (both 12); I did not test whether changing one changes the other.
Escape closes it and **pastes nothing** onto the page.
Screenshots: `M4-7-finance-solver-top.png`, `M4-7-finance-solver-ppy.png`, `M4-7-finance-solver-cpy-pmtat.png`, `M4-7-finance-solver-solved.png`.

### 4.8 Distributions (all dialogs fire on OK and return the number; no Return needed)
| Item | Fields in order and defaults | Pasted/evaluated line | Result |
|---|---|---|---|
| Normal Pdf | `X Value:` (blank), `μ:` 0, `σ:` 1 | `normPdf(0,0,1)` | 0.39894228 |
| Normal Cdf | `Lower Bound:` **`−∞`** (the symbol, selected), `Upper Bound:` (blank), `μ:` 0, `σ:` 1 | `normCdf(−∞,1.96,0,1)` | 0.97500217 |
| Inverse Normal | `Area:` (blank), `μ:` 0, `σ:` 1 | `invNorm(0.975,0,1)` | 1.959964 |
| Binomial Pdf | `Num Trials, n:`, `Prob Success, p:`, `X Value:` shown as "(optional)" | `binomPdf(10,0.5,5)` | 0.24609375 |
| Binomial Cdf | `Num Trials, n:`, `Prob Success, p:`, `Lower Bound:` 0, `Upper Bound:` | `binomCdf(10,0.5,0,5)` (four arguments) | 0.62304688 |
| Inverse Binomial (item C) | dialog titled **"Num Successes"**: `Cumulative Prob:`, `Num Trials, n:`, `Prob Success, p:`, `Display Result:` ☐ `Matrix Form`; OK, Cancel | not run | not run |
| Poisson Pdf | `λ:`, `X Value:` | `poissPdf(3,2)` | 0.22404181 |
| Poisson Cdf | `λ:`, `Lower Bound:` 0, `Upper Bound:` | `poissCdf(3,0,2)` | 0.42319008 |
| Geometric Pdf | `Prob Success, p:`, `X Value:` | `geomPdf(0.3,2)` | 0.21 |
| Geometric Cdf | `Prob Success, p:`, `Lower Bound:` 1, `Upper Bound:` | `geomCdf(0.3,1,2)` | 0.51 |

Optional: only the Binomial Pdf `X Value` is marked "(optional)" (blank gives the whole list; not tested). The default Lower Bound of Normal Cdf is the symbol `−∞`, not `−9E999`. Not opened: Inverse Binomial N (D), t, χ², F distributions.
Screenshots: `M4-8-normpdf-dialog.png`, `M4-8-normpdf-result.png`, `M4-8-normcdf-dialog.png`, `M4-8-normcdf-result.png`, `M4-8-invnorm-result.png`, `M4-8-binompdf-dialog.png`, `M4-8-binomcdf-dialog.png`, `M4-8-binom-results.png`, `M4-8-invbinom-dialog.png`, `M4-8-poisspdf-dialog.png`, `M4-8-poisscdf-dialog.png`, `M4-8-poisson-results.png`, `M4-8-geompdf-dialog.png`, `M4-8-geomcdf-dialog.png`, `M4-8-geom-results.png`.

---

## Part 5. Syntax hints (Catalog tab 1, hint pane, verbatim)

Read from small screenshots; the hint pane shows only three lines and cuts long lines, so some are cut off (marked …). Several entries have more overloads than the pane shows.

| Name | Hint(s) |
|---|---|
| solve | `solve(Equation,Var)`; `solve(Equation,Var=Guess)`; `solve(Inequality,Var)` …. Separate entry `solve( system`: `solve(SystemOfEqns, VarOrGuess1, VarOrGuess2 [,...])`; `solve(Eqn1 and Eqn2 [and …` |
| nSolve | `nSolve(Equation,Var[=Guess])`; `nSolve(Equation,Var[=Guess],lowBound)`; `nSolve(Equation,Var[=Guess],lowBound,up…` (cut off) |
| factor | `factor(Expr[,Var])`; `factor(List[,Var])`; `factor(Matrix[,Var])` |
| expand | `expand(Expr [,Var])`; `expand(List[,Var])`; `expand(Matrix [,Var])` |
| zeros | `zeros(Expr,Var)`; `zeros(Expr,Var=Guess)`; `zeros({Expr1,Expr2},{VarOrGuess1,VarOrG…` |
| cSolve | `cSolve(Equation,Var)`; `cSolve(Equation,Var=Guess)`; `cSolve(Inequality,Var)` … |
| d (derivative, italic d) | `d(Expr,Var[,Order])`; `d(List,Var[,Order])`; `d(Matrix,Var[,Order])` |
| ∫ | `∫(Expr, Var[, Lower, Upper])`; `∫(Expr, Var[, Constant])` |
| limit (and `lim(`, adjacent entries, same hint) | `limit(Expr, Var, Value [,Direction])`; `limit(List, Var, Value [,Direction])`; `limit(Matrix, Var, Value [,Direction])` |
| sum | `sum(List[,Start[,End]])`; `sum(Matrix [,Start[,End]])` |
| Σ | `Σ(Expr, Var, Low, High)` |
| normCdf | `normCdf(lowBound,upBound[,μ[,σ]])`; `For P(X≤upBound), set lowBound=−∞` |
| invNorm | `invNorm(Area[,μ[,σ]])` |
| binomPdf | `binomPdf(n,p [,XVal])` |
| binomCdf | `binomCdf(n,p)`; `binomCdf(n,p,lowBound,upBound)`; `binomCdf(n,p,upBound), for …` |
| poissPdf | `poissPdf(λ,XVal)` |
| poissCdf | `poissCdf(λ,lowBound,upBound)`; `poissCdf(λ,upBound), for P(0≤X≤upBound)` |
| geomPdf | `geomPdf(p,XVal)` |
| mean | `mean(List[, freqList])`; `mean(Matrix [, freqMatrix])` |
| median | `median(List[, freqList])`; `median(Matrix [, freqMatrix])` |
| stdDevSamp | **The device name is `stDevSamp`** (capital D): `stDevSamp(List[,freqList])`; `stDevSamp(Matrix[,freqMatrix])` |
| stdDevPop | **The device name is `stDevPop`**: `stDevPop(List[,freqList])`; `stDevPop(Matrix[,freqMatrix])` |
| quartile | **Not in the Catalog**: the q group is `QR`, `QuadReg`, `QuartReg` (I did not find a `quartile(`) |
| seq | `seq(Expr,Var,Low,High[,Step])` (neighbours: `seqn(`, `seqGen(`) |
| rand | `rand([#Trials])` |
| randInt | `randInt(lowBound,upBound[,#Trials])` |
| randNorm | `randNorm(μ,σ[,#Trials])` |
| det | `det(squareMatrix[,Tol])` |
| identity | `identity(Integer)` |
| augment | `augment(List1,List2)`; `augment(Matrix1,Matrix2)` |
| simult | `simult(coeffMatrix, constVector[,Tol])` |
| polyRoots | `polyRoots(Poly,Var)`; `polyRoots(ListOfCoeffs)` |
| tvmN | `tvmN(I,PV,Pmt,FV,[PpY],[CpY],[PmtAt])` |
| tvmI | `tvmI(N,PV,Pmt,FV,[PpY],[CpY],[PmtAt])` |
| tvmPV | `tvmPV(N,I,Pmt,FV,[PpY],[CpY],[PmtAt])` |
| tvmPmt | `tvmPmt(N,I,PV,FV,[PpY],[CpY],[PmtAt])` |
| tvmFV | `tvmFV(N,I,PV,Pmt,[PpY],[CpY],[PmtAt])` |

Extra entries seen that CASSim may lack: `linSolve(` (`linSolve(SystemOfLinearEqns, Var1, Var2, ...)`), `avgRC(Expr, Var[=Value] [,Step])`, `centralDiff(Expr, Var[=Value] [,Step])` (also `(Expr, Var[,Step])|Var=Value`, `(Expr, Var[=Value], List)`), `invBinomN(CumulativeProb, Prob, NumSuccess, OutputForm)`, `invχ²(Area, df)`, `invChi2(Area, df)`, `cFactor(Expr [,Var])`, `polyCoeffs(Poly[,Var])`, `ceiling(Expr)`, `bal(NPmt, N, I, PV, [Pmt], [FV], [PpY], [CpY], [PmtAt], [roundValue])`, `QR Matrix, qMatrix, rMatrix [,Tol]`, `CubicReg X, Y [,[Freq] [,Category, Include]]`. The `∫(`, `d(`, `lim(`/`limit(` and `solve( system` entries are separate Catalog entries.
Screenshots: `M5-*.png` (one per hint above).

---

## What was run and what was not
**Run:** Part 1 (full tree, every submenu opened except Mode > sub-submenus and the 8th+ items of Algebra > Polynomial Tools); Part 2 (Doc, Trig, Templates, Catalog tabs 1 to 6, Var, Relations, Punctuation, Symbols); Part 3 (all keys except that ctrl+esc was only tested on typed text); Part 4 items 1 to 8 (see exceptions below); Part 5 (all listed names except where marked).
**Not done or inconclusive:** (`nDerivative` and the Symbols grid were re-done on 2026-11-08, see 4.1b and Part 2.)
- Solve System of **Linear** Equations (Algebra 7.2) not opened. Inverse Binomial (and Inverse Binomial N) not run, only the dialog seen. t, χ², F distributions not opened.
- The Insert menu in the Doc menu was not scrolled past `A Widget`.
- Catalog hints for `getNum` and `getDenom` not captured. The `nDerivative` hint is now in 4.1b.
- Nothing was compared with CASSim's code, so "Differs from CASSim?" is largely unanswered.
- Some Part 1 submenus were captured at the bottom of the screen edge: Polynomial Tools (ended at item 8 in the view) and Mode (B last visible) may have further items.
