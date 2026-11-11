# Emulator check 4, parts A and B: name styling and Calculator leftovers (results)

Run on the TI-Nspire CX CAS Premium Teacher Software 6.0.3.374 (CX II-T CAS handheld view), Handheld-page-size document, 2026-11-12.
Observations only. Screenshots are in `pages-shots/` (cropped to the handheld screen; the emulator zoom was set to 250% so bold and italic can be told apart).

**Settings used for every row:** Radian, Exponential Format Normal, Real (the document opened as Rectangular; changed to Real), Auto calculation mode, Float 8, CAS On. One Problem and one page (1.1) held all of Part A rows, so variables carried between rows (stated per row where it matters).

**Important method note.** The handheld draws a name differently *on the live entry line* and *in the history after Return*. Every row below gives both. Bold against regular was judged on 250% crops; nothing here was judged on 100%.

## Part A summary: the rules (device behaviour)

1. **Catalog names are upright and regular** (`solve`, `sin`, `expand`, `Define`, `DelVar`, `Lock`, `Unlock`, `OneVar`, `tvmPmt`, `Disp`, `Local`, `If`, `when`, `ans`, and the word operators `and`, `or`, `not`, `xor`), on the entry line and in the history. Units `_m` and the constant `_c` are upright regular too.
2. **A name with no definition is italic and regular** (`x`, `a`, `b`, `d`, `h(2)`, `eq` before it is defined, and `tvm.pmt` when nothing has set it), on the entry line and in the history.
3. **A name that has a definition in the Problem is BOLD upright on the live entry line**: number, expression, equation, list, matrix, string, a function (with or without brackets, and as `f(a)` where `a` is undefined), a locked variable, and `stat.results` once `OneVar` has run. A bold name keeps its bold inside every template slot on the entry line (fraction numerator and denominator, exponent, root, integral body).
4. **In the history after Return, user names are italic regular again, even ones that are defined** (the stored `a`, `b`, `f`, `g`, `c`, `eq`, `l`, `m`, `s` all show italic in the input column and in the result column). So bold exists only while the line is being edited. **This contradicts the file's expectation** that defined names are bold everywhere; it matches the "bold on the entry line" seen in the history run.
5. **Case is not corrected while typing; it is corrected on Return.** `define k(x)=x`, `SOLVE(x=1,x)`, `Sin(x)` stay as typed on the entry line; the history then shows `Define`, `solve`, `sin`.
6. **Constants.** After Return `ⅇ` is bold upright, `ⅈ` is bold italic, `π` is upright regular. On the entry line they are still the typed ASCII text (`@e^2`, `@i`, `pi`, `2@E3`).

Exceptions met: `_km` is italic (`_m` is upright) in `2_km▶_m`; the result word `Done` is italic; error text appears as a quoted upright string (`"Error: Argument Error"`).

## Rows

### A1: Catalog functions and their arguments
Settings: as above.
Keys: computer keyboard: `solve(x^2=4,x)` (Right to leave the exponent), `sin(x)`, `expand((a+b)^2)`.
Observed: entry line and history: `solve`, `sin`, `expand` upright regular; `x`, `a`, `b` italic regular. Results: `x=-2 or x=2`, `sin(x)`, `a²+2·a·b+b²` (the multiplication dot is drawn; `a` and `b` italic).
Screenshot: pages-shots/A1-solve-result.png, pages-shots/A1-sin-expand-result.png
Differs from this file's expectation? no.

### A2: Define typed in full (the Menu > Actions > Define route was NOT run)
Settings: as above.
Keys: computer keyboard: `Define f(x)=x` then `^2`, Right; Return; then `f(3)`.
Observed: `Define` upright regular. Before Return `f` and the parameter `x` are italic regular (undefined). After Return the history row shows `Define f(x)=x²` with `f` and `x` italic, result `Done` (italic). `f(3)` shows `f` italic in the history, result `9`.
Screenshot: pages-shots/A2-define-entry.png, pages-shots/A2-define-result-f3.png
Differs? yes: `f` is not bold in the history after it is defined (bold only on the entry line, see A7).

### A3: wrong case
Keys: computer keyboard: `define k(x)=x`, `SOLVE(x=1,x)`, `Sin(x)`.
Observed: entry line keeps the typed case (`define`, `SOLVE`, `Sin`, upright regular). On Return the history shows `Define k(x)=x`, `solve(x=1,x)`, `sin(x)`, styled exactly as in A1. The result column of these rows was hidden behind an application overlay in the capture, so the result text is not recorded.
Screenshot: pages-shots/A3-define-lowercase-entry.png, A3-SOLVE-entry.png, A3-Sin-entry.png, A3-case-corrected-history.png
Differs? not known (no expectation about when).

### A4: a undefined, then defined
Keys: computer keyboard: `a`, `a:=3`, `a`, `a+b`, `2a`.
Observed: undefined `a` is italic (entry line and history). After `a:=3`, typing `a` shows **bold** `a` on the entry line. After Return the history shows `a` italic again, result `3`. `a+b` result `b+3`, `2a` shown `2·a` result `6`. The first history line (`a` → `a`) did **not** change after `a` was defined.
Screenshot: pages-shots/A4-a-defined-entry-bold.png, pages-shots/A4-history-after.png
Differs? yes (history italic, not bold).

### A5: DelVar
Keys: `DelVar a`, `a`.
Observed: while `a` is still defined, the text `a` in `DelVar a` is bold on the entry line; `DelVar` is upright regular. After Return result `Done`; typing `a` again is italic regular; Return gives `a`. No earlier history line changed. In the history `DelVar a` shows `a` italic.
Screenshot: pages-shots/A5-DelVar-entry.png, A5-a-after-delvar-entry.png, A5-history.png
Differs? no.

### A6: every kind of definition
Keys: `g:=x+1`, `eq:=x+y=3`, `l:={1,2,3}`, `m:=[1,2;3,4]`, `s:="hi"`, then each name alone, then `g+l`.
Observed: `g`, `eq`, `l`, `m`, `s` are all bold on the entry line; `g+l` shows `g+l` bold. In the history all of them are italic (input side and result side). (The list name `l` is drawn like a bold `1` in this serif face at the entry line; read from the screenshot.)
Screenshot: pages-shots/A6-g-entry.png, A6-eq-entry.png, A6-list-entry.png, A6-matrix-entry.png, A6-string-entry.png, A6-g-plus-l-entry.png, A6-history.png
Differs? yes (history italic).

### A7: functions
Keys: `f(x):=x^2` (Right), `f(2)`, `f`, `f(a)`, `h(2)`.
Observed: defined `f` is bold on the entry line in `f(2)`, in `f` alone and in `f(a)` (`a` italic, undefined); undefined `h(2)` is italic. History: `f(2)` → `4` with `f` italic; typing `f` alone and pressing Return gave the result string `"Error: Argument Error"`. `h(2)` echoed as `h(2)`.
Screenshot: pages-shots/A7-f2-entry.png, A7-f-entry.png, A7-fa-entry.png, A7-h2-undefined-entry.png, A7-history.png
Differs? yes (history italic). Also note: bare `f` gives an Argument Error string, not an echo.

### A8: store with an arrow
Keys: computer keyboard `5=:b`, then `b`.
Observed: `5=:b` is displayed `5→b` in the history; `b` is bold on the entry line afterwards, italic in the history; result `5`. Same as `:=`.
Screenshot: pages-shots/A8-b-entry.png
Differs? no.

### A9: Ans
Keys: `x^2+1` (Right), `ans`, `ans+1`.
Observed: the entry line shows the plain upright regular text `ans`. After Return the history shows the *value* (`x²+1`, then `x²+1+1`), not the word `ans`.
Screenshot: pages-shots/A9-ans-entry.png, A9-ans-plus1-entry.png, A9-history.png
Differs? not known.

### A10: system variables
Keys: `tvmPmt(60,6,10000,0,12,12)`, `tvm.pmt`, `OneVar {1,2,3}`, `stat.` (choose `results` from the drop-down by clicking), Return.
Observed: `tvmPmt(...)` result `-193.32802`; `tvmPmt` upright. `tvm.pmt` is **not set** by `tvmPmt()` (only by the Finance Solver): it is italic and echoes `tvm.pmt`. `stat.results` after `OneVar` is **bold** on the entry line, result a column of labelled rows (`"SX := Sn-1X"` 1., `"σX := σnX"` 0.81649658, `"n"` 3., MinX 1., Q1X 1., MedianX 2., Q3X 3., MaxX 3., SSX 2., and rows above it). **`stat.x̄` was not run.** A typed `stat.res`+`ults` was swallowed by the drop-down and Return gave a `Syntax` error dialog (OK = Return), consistent with the skill's note.
Screenshot: pages-shots/A10-tvm-dropdown.png, A10-tvm-history.png, A10-stat-results-entry.png, A10-onevar-result.png
Differs? no.

### A11: word operators
Keys: `x>1 and x<3`, `not true`, `a or b`, `when(x>0,1,2)`, `2 xor 3`.
Observed: `and`, `not`, `or`, `xor`, `when` upright regular. `x>1 and x<3` echoes; `not true` shown as typed in the capture (result column hidden by the overlay); `a or b` gave an error string beginning `"Error: Argument must ...` (b was 5 and so a number, not a Boolean; the rest of the message was hidden); `when(x>0,1,2)` result is a piecewise `{1, x>0; 2, x≤0}`; `2 xor 3` echoed with the result column hidden. In `a or b`, `a` was italic and `b` (defined) bold on the entry line.
Screenshot: pages-shots/A11-and-entry.png, A11-not-entry.png, A11-or-entry.png, A11-xor-entry.png, A11-when-entry.png (see A12), A11-history.png
Differs? not known.

### A12: units and constants
Keys: `3_m`, `_c`, `2_km@>_m`.
Observed: `_m` upright regular. `3_m` is drawn `3· _m`, result `3.· _m` (a decimal point appears, in Auto mode). `_c` result `2.9979246ᴇ8· _m/_s` (drawn as a fraction of units). `2_km@>_m`: on the entry line `km` is italic and `@>` is literal text; in the history `_km` is italic, `▶` and `_m` upright, result `2000.· _m`.
Screenshot: pages-shots/A12-unit-entry.png, A12-const-entry.png, A12-convert-entry.png, A12-when-entry.png, A12-history.png
Differs? not known; the `3.·` decimal point is worth a CASSim case.

### A13: constants
Keys: `@e^2` (Right), `@i`, `pi`, `2@E3`.
Observed: entry line shows the typed ASCII (`@e²`, `@i`, `pi`, `2@E3`) in upright/italic regular. After Return: `ⅇ²` bold upright (top row partly cut off in the crop), `ⅈ` bold italic, `π` upright regular, `2@E3` becomes `2000.`.
Screenshot: pages-shots/A13-e-entry.png, A13-i-entry.png, A13-pi-entry.png, A13-EE-entry.png, A13-history.png
Differs? no (matches the menus run's bold `ⅇ`, bold italic `ⅈ`).

### A14: library call: NOT RUN
No library was opened (the Catalog Library tab was not checked in this session).

### A15: Lock
Keys: `Lock b`, `b`, `Unlock b`.
Observed: a locked `b` is bold on the entry line, the same as an unlocked defined name. No style change. History: `Lock b`, `Unlock b` show `b` italic; result `Done` (italic). The result column of the lock row was hidden by the overlay in one crop; `Done` seen on the next.
Screenshot: pages-shots/A15-locked-b-entry.png, A15-history.png
Differs? no change for a locked variable.

### A16: command keywords (typed, not pasted from Menu > Functions & Programs)
Keys: `Disp 5`, `Local t`, `If` typed, then cleared (not run).
Observed: `Disp`, `Local`, `If` upright regular; `t` italic.
Screenshot: pages-shots/A16-Disp-entry.png, A16-Local-entry.png, A16-If-entry.png
Differs? not known.

### A17: the lists themselves (var key only; Catalog tab 1 NOT opened)
Keys: var key.
Observed: the Variables drop-down lists `b, c, eq, f, g, k, l, m, s, stat.maxx, stat.medianx, stat.minx, …` in a plain upright regular face with a small type icon per name (number, expression, function, list, matrix, string); nothing italic or bold.
Screenshot: pages-shots/A17-var-list.png

### A18: inside templates
Keys: fraction template with `f(x)` over `k(2)`; typed (not template-palette) `2^f(x)`, `sqrt(f(x))`, `integral(f(x),x)`.
Observed: on the entry line defined names stay bold in every slot (fraction numerator and denominator, exponent, radicand, integral body), with the argument `x` italic. After Return the history draws them italic (`f(x)`, `k(2)`), and `sqrt` becomes a root, `integral` a ∫ f(x) dx template. Results: `32·x²` for `8·f(x)·f(2)` (an `8` was typed by mistake from a mis-clicked key and is recorded as such), `2^(x²)`, `|x|`, `x³/3`.
Screenshot: pages-shots/A18-fraction-entry.png, A18-exponent-entry.png, A18-root-entry.png, A18-integral-entry.png, A18-history.png, A18-fraction-history.png
Differs? no.

### A19: result containing defined and undefined names
Keys: `c:=d+1`, `c`.
Observed: `c` is bold on the entry line; history `c:=d+1` → `d+1` and `c` → `d+1`, `d` italic, `1` regular, `c` italic.
Screenshot: pages-shots/A13-c-defined-entry.png, A13-history.png

### Part A lists
**Run:** A1, A2 (typed route), A3, A4, A5, A6, A7, A8, A9, A10 (except `stat.x̄`), A11, A12, A13, A15, A16 (typed), A17 (var key only), A18, A19.
**Not run:** A2 via Menu > Actions > Define (not opened); A14 (no library checked); A17 Catalog tab 1 list; A10 `stat.x̄`; A18 root, exponent and integral were typed and not chosen from the template palette; the first history result columns in A3 and A11 were hidden by an overlay and are not transcribed.
**Also seen, not covered:** a bare function name returns `"Error: Argument Error"` (A7); `tvmPmt()` does not set `tvm.pmt` (A10); results with units show `3.·_m` with a decimal point in Auto mode (A12); `a or b` with a number gives an argument error string (A11).

## Part B: Calculator leftovers

Only items B5, B7, B8 and B9 were run in this session (see the lists at the end). Everything else in Part B is **not run**.

### B5: Recall Definition, Clear History, Insert Comment
Settings: Radian, Auto, Real, Float 8. Keys: mouse on the menu key, then number keys.
Observed, Menu > 1 Actions submenu (nothing greyed on an empty entry line, separators after 2, 5 and 6):
- 1 Define
- 2 Recall Definition
- 3 Delete Variable
- 4 Clear a–z…
- 5 Clear History
- 6 Insert Comment
- 7 Library ▶
- 8 Lock ▶

**Recall Definition** opens a small drop-down (no dialog with fields) listing the function-type names defined in the Problem (`f`, `k`, `stat.stat`). Return on `f` pastes `Define f(x)=x²` into the entry line (`f` bold, cursor inside the exponent, not evaluated). Whether it lists plain variables was not tested (the list showed only function-type items while `a`…`s`, `eq`, `l`, `m` existed).
**Clear History** has no confirmation dialog. It empties the whole history on the page; variables survive (`f(3)` afterwards gave `9`). **Ctrl+Z restores the history** (it took the undo presses for the new `f(3)` entry first; the whole history was back after 6 presses in all).
**Insert Comment** pastes `©` at the start of the entry line. After typing `hello 1+1` and Return, the history shows `©hello 1+1` as one plain upright line with **no result**, so it is not evaluated. Whether the comment line can be edited afterwards was not tested.
Screenshot: pages-shots/B5-actions-menu.png, B5-recall-dropdown.png, B5-recall-pasted.png, B5-clear-history.png, B5-undo-restores.png, B5-comment.png
Differs from CASSim? not known.

### B7: Help and About on the device
Observed:
- Doc menu (title bar word `Documents`): 1 File ▶, 2 Edit ▶, 3 View ▶, 4 Insert ▶, 5 Page Layout ▶, 6 Refresh Libraries, 7 Settings & Status ▶, 8 Login…, 9 Press-to-Test ▶.
- 7 Settings & Status ▶: 1 Change Language…, 2 Document Settings…, 3 Handheld Setup…, 4 Status…, 5 Login…, 6 Restore Factory Defaults…
- 4 Status…: dialog titled `Handheld Status` with fields Batteries (two icons, `#%` each), Version (6.0.3.374), Storage Capacity (`# MB`), Storage Available (`# MB`), a dashed separator, Network (`Not Applicable`), Login (`Not Applicable`); buttons **About** (left) and **OK** (right).
- About button: a scrollable dialog titled `About` with fields Handheld Type, a product-line and copyright block (legal text, not copied), Product ID (`Not Applicable`), Boot ROM Version (`Not Applicable`), Boot Loader Version (`Not Applicable`), a "visit the vendor site for the latest versions" line, and an **OK** button.
- 9 Press-to-Test ▶: 1 Exit Press-to-Test (grey), 2 Transfer Press-to-Test (grey), 3 Help. Help opens a scrollable dialog titled `Press-to-Test Help`, first heading "How to set-up your handheld:", then instructions that refer to key combinations at power-on; button **OK**.
- Teacher Software menu bar, Help menu (labels only): Help (F1), Online Help (F2), Download latest Guidebook, Visit (vendor site), Visit Activities Exchange, Explore Online Troubleshooting, Product Improvements…, Check for Upgrades and Notifications, Check for OS Updates (grey), Check TI-Innovator Hub…, About (the software), License Info, Sign Out.
- The Calculator page Menu (menu key) has 9 items (1 Actions … 9 Functions & Programs) and **no Help or Hints item**.
Screenshot: pages-shots/B7-doc-menu.png, B7-settings-status-menu.png, B7-status.png, B7-about.png, B7-ptt-menu.png, B7-ptt-help.png, B7-help-menu.png
Differs from CASSim? yes: the device's About is under Status (Doc > Settings & Status > Status > About), as CASSim has it now; the page Menu has no About or Help.

### B8: warning triangle (FR-CALC-007)
Settings: Radian, Auto, Real.
Keys: `real(sqrt(-1)^3)` (exponent left with Right), Return; click the triangle; then `(-8)^(1/3)`.
Observed: `real(√(-1))³` draws a yellow warning triangle at the left of the history row and gives result `0`. Clicking the triangle opens a dialog titled **Warning** with the message **Non-real calculation** and an OK button. `(-8)^(1/3)` gives `-2` with **no triangle** (drawn with a stacked fraction exponent, `(-8)^(1/3)`).
Screenshot: pages-shots/B8-real-sqrt-triangle.png, B8-warning-dialog.png, B8-cube-root.png
Differs from CASSim? not known.

### B9: error dialogs
All in Real mode, Float 8. In each case the dialog has one **OK** button. "Cursor afterwards" is where the cursor sat after pressing OK.
| Typed | Dialog title | Message | Cursor afterwards |
|---|---|---|---|
| `1+` | Error | Syntax | still at the end of the entry line (`1+`), no history line added |
| `solve(x=1)` | Error | Too few arguments / The function or command is missing one or more arguments. | still at the end of the entry line, no history line |
| `det([1,2;2,4])^-1` | (no dialog) | result `undef` | new empty entry line |
| `[1,2]+[1,2,3]` | Error | Dimension mismatch / Two or more arguments must have matching dimensions. For example [1,2]+[1,2,3] is a dimension mismatch. | history line added with the result string `"Error: Dimension mismatch"`, new empty entry line |
| `f(1,2)` (f has one argument) | Error | Too many arguments / The function or command contains an excessive number of arguments and cannot be evaluated. | history line added with the result string `"Error: Too many arguments"`, new empty entry line |
| `"a"+1` | (no dialog) | echoed as `"a"+1` with no evaluation | new empty entry line |
Note on `"a"+1`: typing the opening quote auto-inserts the closing one; typing `"a` then Right then `+1` gives the line above. Typing `"a"+1` straight through left a stray quote (`"a"+1"`).
Screenshot: pages-shots/B9-syntax.png, B9-too-few.png, B9-det-undef.png, B9-dimension.png, B9-too-many.png, B9-string-plus-1.png
Differs from CASSim? not known.

### Part B lists
**Run:** B5 (Actions menu, Recall Definition, Clear History, Insert Comment; Insert Comment editing not tested), B7, B8, B9.
**Not run (time):** B1 (history plan rows H1 to H9), B2 (editor plan rows), B3 (every row of `simulator-todo.md`), B4 (every leaf of the Calculator Menu), B6 (menu scrolling and size, including the Variables list with 15 variables).
**Also seen, not covered:** the entry line keeps the typed text after a Syntax or Too-few-arguments error but is cleared after a run-time error (Dimension mismatch, Too many arguments), which also adds a history row with the error string; a quote typed on the entry line auto-closes.

---
## Part B additions (second pass)

### B4: Calculator Menu leaves (partial). Pasted text, empty entry line, Radian/Auto/Real/Float 8
Cursor is shown inside the brackets after each paste, with the brackets empty. In three entries the mouse pointer hid one letter; those spellings are marked (?).
| Menu route | Label | Pasted |
|---|---|---|
| Number > Fraction Tools (1 Proper Fraction, 2 Get Numerator, 3 Get Denominator, 4 Common Denominator) | Get Numerator | `getNum(` |
| same | Get Denominator | `getDenom(` |
| Algebra | 5 Complete the Square | `completeSquare(` |
| Algebra > 8 Polynomial Tools (1 Find Roots of Polynomial… (dialog, not run), 2 Real Roots, 3 Complex Roots, 4 Remainder, 5 Quotient, 6 GCD, 7 Coefficients, 8 Degree; more items may follow) | Real Roots | `polyRoots(` |
| same | Complex Roots | `cPolyRoots(` |
| same | Remainder | `polyRemainder(` |
| same | Quotient | `polyQuotient(` |
| same | Greatest Common Divisor | `polyGcd(` (?) |
| same | Coefficients | `polyCoeffs(` (?) |
| same | Degree | `polyDegree(` |
| Calculus > B Arc Length | Arc Length | `arcLen(` |
| Calculus > C Series (1 Taylor Polynomial, 2 Generalized Series, 3 Dominant Term) | Generalized Series | `series(` |
| same | Dominant Term | `dominantTerm(` |
| Calculus > F Numerical Calculations (1 Numerical Derivative, 2 Central Difference Quotient, 3 Numerical Integral, 4 Numerical Function Minimum, 5 Numerical Function Maximum) | Central Difference Quotient | `centralDiff(` |
| same | Numerical Function Minimum | `nfMin(` |
| same | Numerical Function Maximum | `nfMax(` |
| Matrix & Vector (1 Create, 2 Transpose, 3 Determinant, 4 Row-Echelon Form, 5 Reduced Row-Echelon Form, 6 Simultaneous, 7 Norms, 8 Dimensions, 9 Row Operations, A Element Operations, more below) | Row-Echelon Form | `ref(` |
| same | Reduced Row-Echelon Form | `rref(` |
| Matrix & Vector > 1 Create (1 Matrix… (dialog), 2 Zero Matrix, 3 Identity, 4 Diagonal, 5 Random Matrix, 6 Fill, 7 Submatrix, 8 Augment, 9 Column Augment, A Construct Matrix) | Zero Matrix | `newMat(` |
| same | Diagonal | `diag(` |
| same | Random Matrix | `randMat(` |
| same | Fill | `Fill ` (no bracket; cursor after the space) |
| same | Column Augment | `colAugment(` |
| same | Construct Matrix | `constructMat(` |
Menus seen: Calculator Menu top level has 9 items. Number: 1 Convert to Decimal, 2 Approximate to Fraction, 3 Factor, 4 Least Common Multiple, 5 Greatest Common Divisor, 6 Remainder, 7 Fraction Tools, 8 Number Tools, 9 Complex Number Tools. Algebra: 1 Solve, 2 Factor, 3 Expand, 4 Zeros, 5 Complete the Square, 6 Numerical Solve, 7 Solve System of Equations, 8 Polynomial Tools, 9 Fraction Tools, A Convert Expression, more. Calculus: 1 Derivative, 2 Derivative at a Point…, 3 Integral, 4 Limit, 5 Sum, 6 Product, 7 Function Minimum, 8 Function Maximum, 9 Tangent Line, A Normal Line, B Arc Length, C Series, D Differential Equation Solver…, E Implicit Differentiation, F Numerical Calculations (last item). Statistics: 1 Stat Calculations, 2 Stat Results, 3 List Math, 4 List Operations, 5 Distributions, 6 Confidence Intervals, 7 Stat Tests.
Screenshot: pages-shots/B4-*.png
Differs from CASSim? not known (CASSim comparison not done here).

### B6: menu scrolling (partial)
- Stat Calculations (in Lists & Spreadsheet) shows 10 rows at once. A blue down arrow at the bottom (and an up arrow at the top once scrolled) signals more rows. It has 15 items (1 to 9, A to F). Down on the last item wraps to the first; Up on the first wraps to the last.
- Calculus shows 10 rows with the same arrows and 15 items.
- Not recorded: ctrl+1/3/7/9 in a menu, mouse wheel, arrow click, drag, Catalog tab 1, Catalog Symbols, the 15-variable Variables list.
Screenshot: pages-shots/E15-stat-calcs-top.png, E15-stat-calcs-scrolled.png, B4-calculus-menu.png, B4-calculus-menu-scrolled.png

### Part B lists (updated)
**Run:** B4 (partial: the leaves listed above), B5, B6 (partial), B7, B8, B9.
**Not run:** B1, B2, B3; B4 leaves not listed above (Actions already in B5; Statistics Sample, Multiple Linear Regression, Correlation Matrix, Fill, Difference List, Mid; Matrix Row and Column items, Trace, LU and QR Decomposition, Characteristic Polynomial; the dialog items such as Find Roots of Polynomial…); the rest of B6.
**Also seen, not covered:** none new.
