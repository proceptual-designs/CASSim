# Emulator check 5: Lists & Spreadsheet results (Part E, partial)

Software: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view, 250% zoom, Handheld page size.
Settings: Radian, Automatic, Real, Float 8 (found already set; Document Settings checked first). E22 changed them briefly (stated there) and they were put back.
Observations only. Baseline read first: `docs/testing/emulator-sheet-results.md` (check 4, from `C:\dev\CASSim\docs\testing\`).
Document1: page 1.1 Calculator holds `xs`, `ys`, `d1`, `d2`, `cat` (typed as the brief says, with the `"a`, Right trick); page 1.2 Lists & Spreadsheet has them linked to columns A to E (named `xs`, `ys`, `d1`, `d2`, `cat`). Tests below were typed in columns F to K so the linked lists stayed intact (A to E untouched).
This part was **not run in full**: see the three lists at the end. Screenshots are in `pages-shots-5/`, cropped to the handheld screen.

## E1: Statistics submenus and List Math end
Settings: Float 8, Auto, Real.
Keys: mouse on the menu key, then number keys; Left closes one level; Up on the first row wraps to the last.
Observed (labels exact, `…` as drawn):
- Menu > 4 Statistics > 2 Distributions (20 items, 10 rows show, arrows at top and bottom):
  1 Normal Pdf…, 2 Normal Cdf…, 3 Inverse Normal…, 4 t Pdf…, 5 t Cdf…, 6 Inverse t…, 7 χ² Pdf…, 8 χ² Cdf…, 9 Inverse χ²…, A Binomial Pdf…, B Binomial Cdf…, C Inverse Binomial…, D Inverse Binomial N… (label cut at the menu edge), E F Pdf…, F F Cdf…, G Inverse F…, H Geometric Pdf…, I Geometric Cdf…, J Poisson Pdf…, K Poisson Cdf….
- Menu > 4 Statistics > 3 Confidence Intervals (8 items, all show): 1 z Interval…, 2 t Interval…, 3 2-Sample z Interval…, 4 2-Sample t Interval…, 5 1-Prop z Interval…, 6 2-Prop z Interval…, 7 Linear Reg t Intervals…, 8 Multiple Reg Intervals….
- Menu > 4 Statistics > 4 Stat Tests (13 items): 1 z Test…, 2 t Test…, 3 2-Sample z Test…, 4 2-Sample t Test…, 5 1-Prop z Test…, 6 2-Prop z Test…, 7 χ² GOF…, 8 χ² 2-way Test…, 9 2-Sample F Test…, A Linear Reg t Test…, B Multiple Reg Tests…, C ANOVA…, D ANOVA 2-Way….
- Menu > 3 Data > 6 List Math, scrolled to its end: the list is 10 items and ends at **A Population Variance** (nothing follows; check 4's doubt is settled). Items: 1 Minimum, 2 Maximum, 3 Mean, 4 Median, 5 Sum of Elements, 6 Product of Elements, 7 Sample Standard Deviation, 8 Sample Variance, 9 Population Standard Deviation, A Population Variance.
No item in these three submenus was greyed (the cursor was in a data-area cell of column E).
Screenshot: pages-shots-5/E1-distributions-top.png, E1-distributions-end.png, E1-confidence-intervals.png, E1-stat-tests-top.png, E1-stat-tests-end.png, E1-listmath-end.png
Differs from CASSim or from this file's expectation? not known.

## E2: context menus (right click)
Keys: mouse right click. A right click also selects what was clicked.
Observed:
- **Data cell** (selected C2): 1 Cut, 2 Copy, 3 Paste, (rule) 4 Insert Cell, 5 Delete Cell, 6 Fill, (rule) 7 Variables ▶ (grey), 8 Resize ▶, 9 Summary Plot, A Quick Graph, B Color ▶. Up from the first row wraps to B, so B is the last item.
- **Name cell** (column D selected, bottom bar `D` and `d2` in italics): 1 Cut, 2 Paste, (rule) 3 Variables ▶, 4 Resize ▶, 5 Summary Plot, 6 Quick Graph, 7 Color ▶.
- **Formula cell** (the `=` row, column D): the list is longer than the screen (scroll bar and arrows). 1 Cut (grey), 2 Copy (grey), 3 Paste, (rule) 4 Variables ▶ (grey), 5 Symbols…, 6 Math Templates…, 7 Generate Sequence, 8 Data Capture ▶, 9 Clear Data, (rule) A Resize ▶, B Summary Plot, C Quick Graph, D Color ▶ (last; reached with Up).
- **Row number** (row 2, the whole row gets a frame): 1 Cut, 2 Copy, 3 Paste, (rule) 4 Resize Row, 5 Insert Row, 6 Delete Row, 7 Color ▶. Bottom bar shows just `2`.
Screenshot: pages-shots-5/E2-context-data-cell.png, E2-context-name-cell.png, E2-context-formula-cell-top.png, E2-context-formula-cell-end.png, E2-context-row-number.png
Differs from CASSim or from this file's expectation? not known.

## E3: first screen of a new Lists & Spreadsheet page
Observed: the page opens with cell A1 selected. Four columns (A to D) are visible, five data rows (1 to 5). Above the data are a grey letter row (the name cells, with the column letter drawn small at the left of each cell) and a grey `=` row (the formula cells), then the numbered rows. At the bottom is an edit bar with the cell name in a dark box at the left (`A1`) and two small arrows at the right. A vertical scroll bar with up and down arrows is on the right.
Approximate positions on the 320×240 screen (the handheld picture is 756×568 screen pixels at 250%, so divide by about 2.36): the page tab strip is about 0 to 28; the name row about 28 to 55; the `=` row about 55 to 82; each data row about 27 high, rows 1 to 5 filling about 82 to 218; the edit bar about 218 to 240. The row-number column is about 32 wide and each data column about 70 wide.
Screenshot: pages-shots-5/E3-first-screen.png
Differs from CASSim or from this file's expectation? not known.

## E5: cell entry in column F (Automatic mode, Float 8)
Keys: computer keyboard, a number or text then Return. Enter moves the cursor **down** one cell (not right).
Typed (TI ASCII spellings) and displayed:
| Cell | Typed | Cell shows | Alignment | Edit bar when selected |
|---|---|---|---|---|
| F1 | `5` | 5 | right | `5` |
| F2 | `1/3` | 1/3 (linear) | right | a stacked fraction (the zoom cut the edit bar, so only read at low quality) |
| F3 | `2^0.5` | 2^(0.5) | left (text) | `2` with a raised `0.5` |
| F4 | `sqrt(2)` | sqrt(2) | left (text) | `√2` drawn as a root |
| F5 | `pi` | π | left (text) | `π` |
| F6 | `"text` then Right | text (no quotes) | left | `"text"` |
| F7 | `abc` | abc | left | `abc` in italics |
| F8 | `=f1+1` | 6 | right | `=f1+1` in italics |
| F9 | `=f1:f3` | #ERR | left | `=f1:f3` |
F9 raised a dialog: title **Syntax Error in Cell: f9**, text `Syntax`, button OK. Return dismissed it, the cell kept `#ERR`.
So, as in check 4, only a leading `=` makes a formula; `sqrt(2)`, `2^0.5` and `pi` without `=` are text. New: the typed `pi` is turned into `π` and `"text"` loses its quotes in the cell.
Not run: the same entries in Approximate mode (only E22 below used Approximate).
Screenshot: pages-shots-5/E5-entries-f2-f5.png, E5-syntax-error-f9.png
Differs from CASSim or from this file's expectation? not known.

## E6: formulas (columns G and I; the brief's `$g$1` and `h1` variants were adapted)
Keys: computer keyboard.
Typed → displayed (Automatic, Float 8):
- G1 `=mean(xs)` → 9/2 (edit bar `=mean(xs)` with `xs` in bold).
- G2 `=mean(a[])` → 9/2.
- G3 `=d1[2]` → 4 (a reference to a Calculator variable works).
- G4 `=sum(a1:a4)` → 10.
- G5 `=a1*$a$2` → 2 (absolute reference accepted; **not copied down**, so copy and fill of `$` references was not tested).
- G6 `=g6` (circular) → dialog titled **Syntax Error**, text `Circular definition` (TI text, do not reuse), OK. After OK the cell stays in edit mode; Escape cancels and G6 stays empty.
Screenshot: pages-shots-5/E6-formulas-g1-g5.png, E6-circular-definition.png
Differs from CASSim or from this file's expectation? not known. Note: check 4 (E20) saw a `Syntax Error` dialog whose text was `Syntax`; this one has its own text.

## E8: column formula
Keys: cursor on the `=` row of column H, `=xs^2`, Return; then Down twice and `99` Return in H3.
Observed:
- After `=xs^2` the column fills with 1, 4, 9, 16, 25, … ; the formula cell shows `=xs^2`; a data cell of H shows `=1` in the edit bar.
- Typing `99` in H3 raises a dialog titled **Data Loss**: `This operation may overwrite data in the current column(s). Do you wish to proceed?` (TI text, do not reuse). Buttons **OK** and **Cancel**.
- **OK** (check 4 only pressed Cancel): the column formula is **removed**, the squares are cleared, and only `99` remains in H3; the `=` row of H is empty.
- ctrl+Z straight after that put the formula column back, and H3 returned to edit mode showing `99` (so ctrl+Z undid the commit, not the 99 itself). Escape left it.
Screenshot: pages-shots-5/E8-column-formula-typed.png, E8-data-loss-dialog.png, E8-after-ok.png, E8-ctrlz-restores.png
Differs from CASSim or from this file's expectation? not known.

## E20: errors in cells (column I)
Keys: computer keyboard.
Observed:
- I1 `=1/0` → **#UNDEF** (as check 4).
- I2 `=f1+"x"` (typed `=f1+"x`, Right, Return) → the cell shows `"x"+5`, left-aligned, no error dialog. (f1 holds 5.)
- I3 `=zzq` → the text `zzq`, left-aligned (as check 4).
- `=undefinedname` → **no cell is written**: a dialog titled **Syntax Error** with text `Syntax error during insertion.` (TI text, do not reuse), OK; the cell stays in edit mode with the text until Escape. This differs from `=zzq`. It was not found why (the name is long and starts with `undef`); only tested once more with the same result.
- Not run: a formula column whose list lengths differ.
Screenshot: pages-shots-5/E20-error-cells.png, E20-zzq-text-and-void.png, E20-undefinedname-syntax-error.png
Differs from CASSim or from this file's expectation? not known.

## E21: void cells
Keys: `_` typed into I4; in column J, `2` in J5, J6 left empty, `4` in J7, then K5 `=mean(j5:j7)`.
Observed: a typed `_` is shown as a small low underscore centred in the cell (a void). `=mean(j5:j7)` with J6 empty gives **3**, so the empty cell is skipped and the mean is of 2 and 4. (A void in a list vs an empty cell was not compared.)
Screenshot: pages-shots-5/E20-zzq-text-and-void.png (the void), E21-void-mean.png
Differs from CASSim or from this file's expectation? not known.

## E22: Document Settings Float 3, then Fix 2
Settings used: first Float 3 with **Calculation Mode Approximate** (Auto would keep `1/3` exact, so Approximate was set too), then Fix 2 with Approximate. Afterwards put back to Float 8, Radian, Real, Auto.
Keys: mouse on Document Settings (doc key, 7, 2); drop-downs by mouse; OK. In a Fix list the mouse wheel moves 3 items per tick, so Up/Down keys were used.
Observed with `=1/3` in K6 and other cells:
- Float 3, Approximate: K6 shows 0.333; plain typed numbers and formula results get a decimal point (`2.`, `4.`, `16.`).
- Fix 2, Approximate: K6 shows 0.33; numbers show `16.00`, `2.00`, `3.00`.
So the sheet **follows** Document Settings (display digits and Approximate mode).
Screenshot: pages-shots-5/E22-approx-float3-sheet.png, E22-fix2-sheet.png
Differs from CASSim or from this file's expectation? not known.

## E23: recalculate
Keys: `=rand()` in K7, then ctrl+R.
Observed: K7 first showed 0.94359… (tooltip `0.94359740249213`), after ctrl+R it showed 0.90831… (tooltip `0.90831886097475`). The tooltip holds 14 digits. ctrl+R also re-ran the bad formula in F9 and raised the **Syntax Error in Cell: f9** dialog again (OK to dismiss). `=randInt(1,6,5)` in a formula cell was not run.
Screenshot: pages-shots-5/E23-rand-before.png, E23-rand-after-ctrl-r.png, E23-ctrl-r-f9-error.png
Differs from CASSim or from this file's expectation? not known.

## E24: Go To limits
Keys: ctrl+G, `a2500`, Return; then ctrl+G, `a2501`, Return.
Observed: the Go To dialog (title **Go To**, one text field, OK, Cancel) accepts a cell name: `a2500` moves the cursor to row 2500 (the bottom bar shows `A2500`). `a2501` gives a dialog titled **Go To** with `Invalid reference. Please try again.` (TI text, do not reuse), OK. So the last row is **2500**. The last column was not tested.
Screenshot: pages-shots-5/E24-goto-a2500-dialog.png, E24-a2500-row.png, E24-a2501-invalid-reference.png
Differs from CASSim or from this file's expectation? not known.

## Run
E1 (Distributions, Confidence Intervals, Stat Tests, List Math end), E2 (data cell, name cell, formula cell, row number), E3, E5 (Automatic mode only), E6 (all but copy-down), E8 (OK path and ctrl+Z), E20 (partial), E21 (partial), E22, E23 (rand and ctrl+R), E24 (last row), E15 (One-Var, Two-Var, Linear Regression mx+b, live update), E16 (category list, error only), E17 (Normal Pdf, Normal Cdf with Shade area, 1-Prop z Interval, t Test). The Data menu items, Generate Sequence dialog and Quick Graph (E14) are recorded in emulator-stats2-results.md under F22.

## Not run
E2 context menu on a block of cells; E4 (keys and mouse beyond Enter moving down); E5 in Approximate mode; E6 copy-down of `$` references; E7 (invalid names, the var key, the Conflict Detected buttons); E10 (ctrl+arrows, ctrl+7, ctrl+1, Page Up and Down, `xs` in Go To); E11 to E13 (selection, insert and delete, resize); E14 (see F22 for Generate Sequence and Quick Graph; Data Capture, Random dialogs and Summary Plot not run); E15 other regressions, E16 with a working category run (the run gave a Syntax error, unsolved), E17 other distributions and tests; E18 (Sort); E20 differing list lengths; E21 void inside a list; E23 `randInt`; E24 last column. Reason: time; the rows were not attempted, none failed (E16 category run failed, recorded above).

## Also seen, not covered
- Right click on a cell scrolls the view and selects that cell before the menu opens.
- The tooltip on a selected cell shows 14 digits of a number.
- The page tab strip and the edit bar stay on screen while the sheet scrolls.
- Check 4's "Conflict Detected" and Data Loss dialogs were not seen again except Data Loss (E8).

## Addendum: E15 and E16 (Stat Calculations from the sheet)

### E15 One-Variable Statistics (Menu 4 Statistics > 1 Stat Calculations > 1)
- Settings: Radian, Automatic, Real, Float 8. Data d1 in column C (`{2,4,4,4,5,5,7,9}`), cell in column C selected.
- Keys: Menu, 4, 1, 1. First dialog "One-Variable Statistics" has only "Num of Lists:" (spinner, default 1), OK, Cancel. Second dialog fields: X1 List (preselected `c[]`, the selected column), Frequency List (`1`), Category List (empty), Include Categories (empty), 1st Result Column (default `d[]`, the next column, which would overwrite d2), OK, Cancel.
- Observed (result column `l[]`, labels in L, values in M, 13 rows): Title "One-Variable Statistics"; x̄ 5.; Σx 40.; Σx² 232.; sx := sn-1x 2.1380899352994; σx := σnx 2.; n 8.; MinX 2.; Q₁X 4.; MedianX 4.5; Q₃X 6.; MaxX 9.; SSX := Σ(x-x̄)² 32. Values show as decimals with a trailing point.
- Screenshot: E15-onevar-dialog-defaults.png (dialog only; the result columns were not saved as screenshots).
- Frequency List `{1,1,1,1,1,1,1,2}` on d1 (results U/V): x̄ 5.44444…, Σx 49., Σx² 313., sx 2.40370…

### E15 Two-Variable Statistics (Menu 4 > 1 > 2), xs, ys
- Dialog directly (no Num of Lists step): X List `a[]`, Y List (empty, must be filled), Frequency List `1`, Category List, Include Categories, 1st Result Column (default `b[]`). Used `o[]`.
- Observed (26 rows): Title "Two-Variable Statistics"; x̄ 4.5; Σx 36.; Σx² 204.; sx 2.44948…; σx 2.29128…; n 8.; ȳ 9.025; Σy 72.2; Σy² 819.4; sy 4.89598…; σy 4.57977…; Σxy 408.8; r 0.99941…; MinX 1.; Q₁X 2.5; MedianX 4.5; Q₃X 6.5; MaxX 8.; MinY 2.1; Q₁Y 5.05; MedianY 8.95; Q₃Y 13.; MaxY 16.1; SSX 42.; SSY 167.795.

### E15 Linear Regression (mx+b) (Menu 4 > 1 > 3), xs, ys
- Dialog "Linear Regression (mx+b)": X List `a[]`, Y List `b[]`, Save RegEqn to `f1`, Frequency List `1`, Category List, Include Categories, 1st Result Column (used `q[]`).
- Observed: Title "Linear Regression (mx+b)"; RegEqn `m*x+b`; m 1.997619047619; b 0.035714285714289; r² 0.99883928660114; r 0.99941947479581; Resid is a quoted string in one cell "{0.066666666666711,-0.13095238095229,0.17142857142871,-0.22619047619029,0.07619047619072,0.17857142857172,-0.21904761904728,0.08333333333372}", not a list.
- Live update: changing A1 from 1 to 0 updated the results at once (x̄ 4.375, Σx 35., Σx² 203., sx 2.66926…; m 1.8210526315789, b 1.05789…, r² 0.98570…). Restored to 1 afterwards.
- Differs from CASSim? Results are live formulas; result columns are written beside the data and overwrite whatever is there unless 1st Result Column is changed.

### E16 Category list
- Entering a Category List without Include Categories gives "Input Error: Required field is empty! Field # 4: Include Categories:" (screenshot E16-category-list-include-required-error.png).
- With Category List `cat` or `e[]` and Include Categories `{"a"}` or `"a"` and result column `x[]` or `s[]`, OK gives the dialog "Syntax Error: Syntax error during insertion." and no results were written (screenshots E16-onevar-dialog-category-filled.png, E16-category-include-syntax-error.png). Could not get a category run to complete; cause not found (not the result column, not the quote form).
- Typing `"` straight after other characters in a dialog field can swallow the text and open a variable list; type `{`, then `"a`, then `"}` as separate short chunks.

### Mechanics noted
- Clicking a cell that is already selected enters edit mode (cell shows `=value` selected); then Menu 4 > 1 shows Stat Calculations items grey and gives "Selection Error: Invalid selection for command" (screenshot E16-selection-error-after-edit-mode.png). Click a different cell first, then the target cell once.

## Addendum: E17 (Distributions, Confidence Intervals, Stat Tests run from the sheet)

Settings: Radian, Automatic, Real, Float 8. Menu 4 Statistics submenus: 1 Stat Calculations ▶, 2 Distributions ▶, 3 Confidence Intervals ▶, 4 Tests ▶ (shown as "Stat Tests").

### E17 Normal Pdf (Menu 4 > 2 > 1)
- Distributions list (first 10 of more, scroll arrow): 1 Normal Pdf…, 2 Normal Cdf…, 3 Inverse Normal…, 4 t Pdf…, 5 t Cdf…, 6 Inverse t…, 7 χ² Pdf…, 8 χ² Cdf…, 9 Inverse χ²…, A Binomial Pdf…
- Dialog "Normal Pdf": X Value (empty), μ `0`, σ `1`, Draw: checkbox "Plot pdf" (unchecked), OK, Cancel. X Value 1 gives `=normpdf(1,0,1)` written INTO THE SELECTED CELL (it overwrote the data cell D4 without any Data Loss warning); the cell shows 0.24197… and the formula is `=normpdf(1,0,1)`. D4 was then retyped as 4.
- Screenshots: E17-distributions-menu-top.png, E17-normal-pdf-dialog.png, E17-normal-pdf-result-overwrites-cell.png

### E17 Normal Cdf (Menu 4 > 2 > 2)
- Dialog "Normal Cdf": Lower Bound (default `−∞`, preselected), Upper Bound (empty), μ `0`, σ `1`, Draw: checkbox "Shade area", OK, Cancel.
- Upper 1.96 in cell Z1: cell shows 0.97500…, formula `=normcdf(−∞,1.96,0,1)` (written into the selected cell; only the single value, no label).
- With Shade area ticked (Upper 1, cell Z3): the cell shows 0.84134… (`=normcdf(…)`) and the page SPLITS: sheet on the left, a graph panel on the right with a density curve (title/function label `normPdf(x,0,1)`, y axis "Density", x axis "x", x range about −3.0 to 3.0), shaded area up to x = 1 and an "Area: .841…" label.
- Screenshots: E17-normal-cdf-dialog.png, E17-normal-cdf-result-in-cell.png, E17-normal-cdf-shade-area-split-page.png

### E17 1-Prop z Interval (Menu 4 > 3 > 5)
- Confidence Intervals list: 1 z Interval…, 2 t Interval…, 3 2-Sample z Interval…, 4 2-Sample t Interval…, 5 1-Prop z Interval…, 6 2-Prop z Interval…, 7 Linear Reg t Intervals…, 8 Multiple Reg Intervals…
- Dialog "1-Prop z Interval": Successes, x (empty); n (empty); C Level `0.95`; 1st Result Column `a[]` (default, would overwrite xs!); OK, Cancel. Used x 30, n 100, result column `v[]`.
- Because column V already held results, a "Data Loss" dialog appeared first ("This operation may overwrite data in the current column(s). Do you wish to proceed?", OK / Cancel); OK proceeded.
- Result (labels column V, values column W, 6 rows): Title "1-Prop z Interval"; CLower 0.21018…; CUpper 0.38981…; p̂ 0.3; ME 0.08981…; n 100. Values are live formulas (column header formula shows `=zInterval…`).
- Screenshots: E17-confidence-intervals-menu.png, E17-1prop-z-interval-dialog.png, E17-data-loss-on-result-column.png, E17-1prop-result-top.png, E17-1prop-result-end.png

### E17 t Test (Menu 4 > 4 > 2)
- Stat Tests list (first 10): 1 z Test…, 2 t Test…, 3 2-Sample z Test…, 4 2-Sample t Test…, 5 1-Prop z Test…, 6 2-Prop z Test…, 7 χ² GOF…, 8 χ² 2-way Test…, 9 2-Sample F Test…, A Linear Reg t Test… (more below).
- First dialog "t Test": Data Input Method drop-down (default "Data", other option Stats), OK, Cancel. Second dialog: μ0 (empty), List (preselected from the selected column, e.g. `w[]`), Frequency List `1`, Alternate Hyp drop-down "Ha: μ ≠ μ0", 1st Result Column `x[]`, Draw: checkbox "Shade P Value", OK, Cancel.
- Run on d1 (`c[]`), μ0 5, result column `s[]`: Title "t Test"; Alternate Hyp "μ ≠ μ0"; t 0.; PVal 1.; df 7.; x̄ 5.; sx := sn-1x 2.13808…; n 8. (8 rows, labels S, values T).
- Screenshots: E17-stat-tests-menu-top.png, E17-t-test-data-input-method.png, E17-t-test-dialog-defaults.png, E17-t-test-dialog-filled.png, E17-t-test-result-top.png, E17-t-test-result-end.png
