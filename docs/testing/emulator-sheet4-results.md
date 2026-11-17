# Emulator check 6, run 4: part S (statistics from the sheet; choices Claude Code guessed) and the E leftovers

Observations only. Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view. Document: new Handheld-size document, Radian, Automatic, Real, Float 8 (set in Document Settings; the new document had inherited Degree). Page 1.1 Calculator: `xs:={1,…,8}`, `ys:={2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1}`, `d1:={2,4,4,4,5,5,7,9}`, `cat:={"a","b","a","c","b","a","c","a"}`. Page 1.2 Lists & Spreadsheet: columns A to D named `xs`, `ys`, `d1`, `cat` (typing the name of an existing list in the grey name cell linked the column to it; the data showed at once).

## S1: One-Variable Statistics on `d1`, 1st Result Column `f[]`
Settings: as above.
Keys: Menu 4 (Statistics), 1 (Stat Calculations), 1 (One-Variable Statistics…); Num of Lists dialog (default 1, with up and down arrows), OK; then the main dialog; typed `d1` in X1 List, Tab ×4, `f[]` in 1st Result Column, Return. Then clicked F1, G1, G2 and the `=` row cells of F and G.
Observed:
- Dialog "One-Variable Statistics" first asks "Num of Lists:" (default 1). Then the fields: X1 List (default `d[]`, the column the cursor was in), Frequency List (default `1`), Category List (empty), Include Categories (empty), 1st Result Column (default `e[]`, the next free column).
- After OK a dialog "Conflict Detected" appeared: "OneVar d1,1." and "d1 : Cell or Variable?" with a drop-down whose options are "Cell Reference" (default) and "Variable Reference". It came because `d1` names both a list and the cell D1. I chose Variable Reference and OK.
- The results fill F and G: F1 "Title", F2 x̄, F3 Σx, F4 Σx², F5 `sx := sₙ₋₁`…; G1 "One-Variable Statistics", G2 5., G3 40., G4 232., G5 2.13808…
- The `=` row of G holds one formula: `=OneVar('d1,1): CopyVar Stat., Stat…` (the bar is cut off). The `=` row of F is empty. F1's edit bar reads `="Title"` and G1's reads `="One-Variable Statistics"`; G2's reads `=5.` So the labels are plain strings, the values are plain numbers shown by the one formula in the `=` row of the first value column (the label column has no formula).
Screenshot: pages-shots-6/S1a-onevar-dialog-defaults.png, S1b-onevar-dialog-filled.png, S1c-conflict-cell-or-variable.png, S1d-conflict-options.png, S1e-result-columns-F-G.png, S1f-G-equals-row.png, S1g-F-equals-row-empty.png, S1h-F1-title.png, S1i-G2-value.png
Differs from CASSim or from this file's expectation? Probably: the Conflict Detected dialog for a column name that is also a cell reference; the Num of Lists step; and the single formula in the `=` row of the value column only.

## S2: Linear Regression (mx+b) on `xs`, `ys` to `i[]`, Save RegEqn to `f1`
Keys: Menu 4, 1, 3. Pressing Return with the Y List empty gave an error first; then typed `xs` in X List, Tab, `ys`, Tab ×5, `i[]`, Return. On the Calculator: `f1(x)`, `f1(2)`, `xs[1]:=0`, `f1(x)`.
Observed:
- The dialog has X List (default `g[]`, the current column), Y List (empty), Save RegEqn to (default `f1`), Frequency List (default `1`), Category List (empty), Include Categories (empty), 1st Result Column (default `h[]`). Return with Y List empty: "Input Error: Required field is empty! Field # 2: Y List:" with OK.
- Results in I (labels) and J (values): Title "Linear Regression (mx+b)", RegEqn m*x+b, m 1.997619, b 0.03571…, r² 0.99883… (the `=` row of J reads `=LinRegM…`).
- On the Calculator `f1(x)` gave 1.997619·x+0.03571429 and `f1(2)` 4.0309524, so `f1` exists after the sheet run. `xs[1]:=0` returned 0, and then `f1(x)` gave 1.8210526·x+1.0578947: `f1` follows the data.
Screenshot: pages-shots-6/S2a-linreg-dialog-defaults.png, S2b-linreg-required-field-error.png, S2c-linreg-dialog-filled.png, S2d-linreg-results-columns.png, S2e-f1-follows-data.png
Differs? not known: CASSim should keep `f1` live (recomputed when the data changes).

## S3: `stat.` variables left by the sheet runs
Keys: on the Calculator `stat.results`, `stat.m`, `stat.regeqn(x)`; `stat.` and the variable list. (Typing `stat.x̄` pasted with spaces gave a Syntax error; recorded as seen.)
Observed (after S1 and S2, and after `xs[1]:=0` recalculated the regression):
- `stat.results` is the Linear Regression list: Title "Linear Regression (mx+b)", RegEqn "m·x+b", m 1.8210526, b 1.0578947, r² 0.98570938, r 0.99282898, Resid "{…}" (these are the values after `xs[1]:=0`, so the stat variables follow the data too).
- `stat.m` → 1.8210526; `stat.RegEqn(x)` → 1.8210526·x+1.0578947.
- The `stat.` list shows: b, freqreg, m, r, r², regeqn, resid, results, stat, values, xreg, yreg… (no x̄ or other One-Variable names: the regression run replaced the One-Variable ones).
Screenshot: pages-shots-6/S3a-stat-results-after-sheet-runs.png, S3b-stat-variable-list.png, S3c-stat-m.png, S3d-stat-regeqn-x.png
Differs? not known: only the last stat run's names exist; the values refresh when the data change.

## S4: Quadratic, Exponential and Logistic (d=0) regressions on `xs`, `ys`
Keys: Menu 4, 1, then 6 (Quadratic Regression…), A (Exponential Regression…), and Down to D (Logistic Regression (d=0)…) then Return; each with X List `xs`, Y List `ys`, the other fields left, Return.
Observed:
- The Statistics > Stat Calculations list: 1 One-Variable Statistics…, 2 Two-Variable Statistics…, 3 Linear Regression (mx+b)…, 4 Linear Regression (a+bx)…, 5 Median-Median Line…, 6 Quadratic Regression…, 7 Cubic Regression…, 8 Quartic Regression…, 9 Power Regression…, A Exponential Regression…, B Logarithmic Regression…, C Sinusoidal Regression…, D Logistic Regression (d=0)… (more below).
- Each regression dialog has the same seven fields: X List (default the current column, such as `j[]`, `l[]`, `n[]`), Y List (empty), Save RegEqn to, Frequency List (`1`), Category List, Include Categories, 1st Result Column.
- Save RegEqn to defaults to the next free function: Linear `f1`, Quadratic `f2`, Exponential `f3`, Logistic `f4` (each run takes the next one). 1st Result Column defaults to the next free column: `h[]` (Linear, I then used `i[]`), `k[]` (Quadratic), `m[]` (Exponential), `o[]` (Logistic).
- Result columns (a label column and a value column, one formula in the value column's `=` row: `=QuadRe…`, `=ExpReg(`, `=Logistic(`):
  - Quadratic: Title "Quadratic Regression", RegEqn a*x^2+b…, a 0.07146…, b 1.23806…, c 1.795098, R² (0.99485…), Resid (a list).
  - Exponential: Title "Exponential Regression", RegEqn a*b^x, a 2.48298…, b 1.29040…, r² 0.96322…, r 0.98143…, Resid, ResidTrans (each a list).
  - Logistic (d=0): Title "Logistic Regression (d=0)", RegEqn c/(1+a*ⅇ^(−b*x)), a 8.99375…, b 0.42778…, c 20.5517… (then Resid).
Screenshot: pages-shots-6/S4a-quadreg-dialog-defaults.png, S4b-quadreg-dialog-filled.png, S4c-quadreg-results-columns.png, S4d-expreg-dialog-defaults.png, S4e-expreg-dialog-filled.png, S4f-expreg-results-columns.png, S4g-regression-menu-list-end.png, S4h-logistic-dialog-defaults.png, S4i-logistic-dialog-filled.png, S4j-logistic-results-columns.png, S4k-expreg-labels-rows-6-8.png
Differs? not known: CASSim should offer the next free fN and column by default and lay out the labels in this order.

## S5: One-Variable Statistics with Num of Lists 2 (X1 `a[]`, X2 `c[]`)
Keys: Menu 4, 1, 1; Num of Lists `2`, Return; X1 List `a[]`, Tab, X2 List `c[]`, Tab, 1st Result Column `r[]`, Return.
Observed:
- With 2 lists the dialog has only three fields: X1 List, X2 List and 1st Result Column (no Frequency, Category or Include Categories). The defaults were X1 `o[]` (the current column), X2 empty, 1st Result Column `p[]`.
- First run with the default `p[]`: Return gave a "Data Loss" dialog ("This operation may overwrite data in the current column(s). Do you wish to proceed?" with OK and Cancel), because `p[]` held the Logistic results. I chose Cancel and the sheet came back unchanged (so this is also an S7 observation: Data Loss comes first when the result column already holds data).
- With `r[]` (empty) the results went straight in: column R holds the labels (Title, x̄, Σx, Σx², sx := sₙ₋₁…, n, MinX, Q₁X, MedianX…, Q₃X…), column S the values for X1 (x̄ 4.375, Σx 35., Σx² 203., sx 2.66926…, n 8.) and column T the values for X2 (x̄ 5., Σx 40., Σx² 232., sx 2.13808…). Each value column has its own `=OneVar(` formula in its `=` row and the label column has none. (x̄ 4.375 for `xs` reflects the earlier `xs[1]:=0`.)
Screenshot: pages-shots-6/S5a-onevar-two-lists-dialog.png, S5b-onevar-two-lists-filled.png, S5c-data-loss-dialog.png, S5d-two-lists-results-S-T.png, S5e-two-lists-T-column.png
Differs? not known: CASSim should lay the two sets out as one shared label column plus two value columns.

## S6: editing the result columns of S1
Keys: clicked G2 (a value cell) and typed `7`, Return; then clicked F3 (a label cell, "Σx"), Del; then Esc and ctrl+Z.
Observed:
- Typing `7` in G2 then Return gave the dialog "Data Loss: This operation may overwrite data in the current column(s). Do you wish to proceed?" with OK and Cancel (the edit bar showed `7`). OK: G2 became 7, and the rest of column G (G1, G3 and below) became empty, and the `=` row formula of G is gone. The label column F was untouched.
- Del on the label cell F3: the cell became empty at once with no dialog (the other labels stayed).
- Esc then ctrl+Z: F3 came back as `="Σx"` (undo restored the label; Esc had nothing to cancel).
Screenshot: pages-shots-6/S6a-type-7-in-value-cell-data-loss.png, S6b-after-OK-column-cleared.png, S6c-del-on-label-cell.png, S6d-esc-ctrlz-label-restored.png
Differs? not known: CASSim should ask Data Loss before an edit in a value column of a stat result (and drop the whole column's results), but let a label cell be cleared without asking.

## S7: One-Variable into a result column that already holds data
Keys: Menu 4, 1, 1 (Num of Lists 1), X1 `d1`, 1st Result Column `f[]` again; Return.
Observed: first "Conflict Detected" (d1 is a cell or a variable), then after choosing Variable Reference and OK, "Data Loss" with the same text, then OK wrote the results over the columns again (G1 `="One-Variable Statistics"`, G2 5., G3 40.…, and F3 "Σx" refilled). So the order is Conflict first, then Data Loss, then the write.
Screenshot: pages-shots-6/S7a-rerun-conflict-first.png, S7b-rerun-data-loss.png, S7c-rerun-result.png
Differs? not known.

## S8: a gap in the data
Keys: in column V (the first free column), typed 1, 2, Down once to skip a cell, 4, 5 (so V3 is empty); One-Variable on `v[]` with 1st Result Column `x[]`.
Observed: the empty cell shows as `_` (a void) once the column holds data. The results (columns X, Y): x̄ 3., Σx 12., Σx² 46., sx 1.82574…, σx 1.58113… That is the mean and sums of 1, 2, 4, 5: the gap is left out (n = 4).
Screenshot: pages-shots-6/S8a-gap-column-V.png, S8b-gap-onevar-dialog.png, S8c-gap-onevar-results.png
Differs? not known: CASSim should skip a void cell in statistics.

## S9: One-Variable with a category list
Keys: sheet: Menu 4, 1, 1, Num of Lists 1, X1 List `c[]`, Frequency `1`, Category List `d[]`, Include Categories typed as `{`, `"a`, `"}` in three chunks, then OK by click (Return only selected the field's text). Calculator: `OneVar d1,1,cat,{"a"}` and then `stat.n`.
Observed:
- The three chunks gave `{"a"}` in the Include Categories field this time (no doubled quotes).
- Result column default was `x[]` (already used by S8), so a "Data Loss" dialog came first (OK chosen). Then a dialog "Syntax Error: Syntax error during insertion." with OK, and the sheet showed no new results: the category run from the sheet fails again with this exact error.
- Calculator: `OneVar d1,1,cat,{"a"}` ran: the history showed `OneVar d1,1,cat,{"a"}` and "Done". (A first attempt where `{` was pasted as part of a 17-character string left an empty template and gave "Error: Dimension Error"; typing `OneVar d1,1,cat,` then `{` then `"a` then Right worked.)
- After it, `stat.n` → 4. and `stat.SSX` → 26. (the four "a" values 2, 4, 5, 9 of `d1`, mean 5). The `stat.` list after a OneVar run: maxX, medianX, minX, n, Q₁X, Q₃X, results, SSX, stat, sx, values, x̄ and more (scrolled).
Screenshot: pages-shots-6/S9a-category-dialog-filled.png, S9b-category-default-column-data-loss.png, S9c-category-syntax-error-during-insertion.png, S9d-calculator-onevar-error-mangled-entry.png, S9e-calculator-onevar-category-done.png, S9f-stat-variable-list-onevar.png, S9g-stat-n-and-ssx.png
Differs? yes: the sheet's category run fails with "Syntax error during insertion" whereas the Calculator route works; CASSim should use the Calculator route's behaviour.

## S10: Distributions and Stat Tests run from a sheet
Keys: clicked an empty cell (Z2), Menu 4 (Statistics), 2 (Distributions), B (Binomial Cdf…): fields Num Trials n `10`, Prob Success p `0.5`, Lower Bound `0`, Upper Bound `5`, click OK; then Return. Later Menu 4, 4 (Stat Tests), 5 (1-Prop z Test…): P0 `0.5`, Successes x `12`, n `20`, Alternate Hyp default, 1st Result Column, Draw: Shade P Value.
Observed:
- Menu 4 submenu: 1 Stat Calculations, 2 Distributions, 3 Confidence Intervals, 4 Stat Tests. The Distributions list starts Normal Pdf, Normal Cdf, Inverse Normal, t Pdf, t Cdf, Inverse t, χ² Pdf, χ² Cdf, Inverse χ², Binomial Pdf, Binomial Cdf… The Stat Tests list: 1 z Test, 2 t Test, 3 2-Sample z Test, 4 2-Sample t Test, 5 1-Prop z Test, 6 2-Prop z Test, 7 χ² GOF, 8 χ² 2-way Test, 9 2-Sample F Test, A Linear Reg t Test (more below). While a cell is in edit mode (a typed digit in its entry line) the Stat Calculations, Confidence Intervals and Stat Tests items are greyed out; Esc clears it.
- Distributions do not make a result column: after OK the dialog's formula `=binomCdf(10,0.5,0,5)` was placed into the entry line of the selected cell (Z2) and stayed in edit mode. Argument order is n, p, lower, upper. Return stored it: Z2 showed 0.62304… (0.623046875), so it is an ordinary cell formula.
- 1-Prop z Test dialog fields: P0, Successes x, n, Alternate Hyp (drop-down, default `Ha: prop ≠ p0`), 1st Result Column (default `a[]`), Draw: Shade P Value (check box), OK, Cancel. Tab order P0 → x → n → Alternate Hyp → 1st Result Column → Shade P Value.
- With the default `a[]` already holding data: "Data Loss" (Cancel closes the whole dialog and nothing is written).
- Typing `pz[]` as the result column gave "Syntax Error: Cannot accept change: Invalid input." (a multi-letter column name is not accepted there; a single letter is). With `w[]` (Data Loss, OK) the results filled TWO columns, W (labels) and X (values), overwriting what X held (the earlier One-Variable values). X's `=` row held `=zTest_1Prop(0.5,12,20,…)`. Labels/values: Alternate Hyp `prop ≠ p0`, z 0.89442…, PVal 0.37109…, p̂ 0.6, n 20.
- Shade P Value ticked: after OK the page split into two panes: the sheet (narrow, left) and a plot at the right showing a standard normal curve (axis `z`, vertical axis `Density`) with both tails shaded outside about ±0.89, and the text `z = 0.8944` and `PVal = 0.3711` at the top.
- A second try straight after a dialog sometimes leaves the menu half open: the digit keys then went into the cell. Waiting a second between the menu key and each digit fixed it.
Screenshot: pages-shots-6/S10a-distributions-menu.png, S10b-binomcdf-dialog.png, S10c-binomcdf-filled.png, S10d-binomcdf-entry-line.png, S10e-binomcdf-result.png, S10f-stattests-menu.png, S10g-1propz-dialog.png, S10h-1propz-dataloss.png, S10i-1propz-syntaxerror-pz.png, S10j-1propz-results-in-wx.png, S10k-1propz-shade-split.png
Differs? not known: CASSim distributions from a sheet should write a formula into the selected cell; tests should write label + value columns and the shade option should split the page with a plot.

## S11: void cells in column formulas and cell formulas
Keys: new Lists & Spreadsheet page (ctrl+i 4). Column A named `u` (click a data cell, Up to row 1, Up again goes to the `=` row, so from row 2 it is Up 3 times to the name cell; Up twice from row 2 put my `p` into the `=` row as `=p` and gave Data Loss), data 1, 2, void, 4 (Down skips a cell), later A1 5, A2 1, A3 8, A4 7, A5 4. Column formulas typed in the `=` row of B, C, D: `=u*2`, `=u+1`, `=u*3`; cell formulas `=a1+1`, `=a2+1` in column E.
Observed:
- A skipped cell shows a small underscore `_` (void) in the cell, and the entry bar of that cell shows `_`. Delete on a filled cell also makes it `_`.
- Typing a list name that is also a variable in a formula gives "Conflict Detected" with the text `u : Column or Variable?` and a drop-down (Column Reference / Variable Reference), then OK. The drop-down's first line (Column Reference) is shown greyed as a default but the choice must be clicked to apply.
- Chosen Column Reference: the formula is stored as `=u[]*2` (the entry bar draws `u[ ]·2` with an empty bracket box), but the B and C columns stayed completely blank, even after the voids were filled (nothing computed, no error). This also happened for `=u+1`.
- Chosen Variable Reference (D): the formula is stored as `='u*3` (an apostrophe before the name) and D shows 15, 3, 24, 21, 12 for A = 5, 1, 8, 7, 4.
- Voids: after Delete on A1 and A4, D1 and D4 show `_` and the other D cells still compute (3, 24, 12). So a void in the input gives a void in that output row only.
- Cell formulas (column E): `=a1+1` with A1 void shows `_`; `=a2+1` with A2 = 1 shows 2. A void is not treated as 0.
Screenshot: pages-shots-6/S11a-conflict-column-or-variable.png, S11b-column-reference-formula-blank.png, S11c-conflict-dropdown.png, S11d-variable-reference-chosen.png, S11e-variable-ref-result.png, S11f-void-propagates.png, S11g-void-in-cell-formula.png
Differs? not known: CASSim should propagate void per row in column formulas and cell formulas (void in, void out); the Column Reference blank result looks like an emulator quirk worth noting.

## S12: Actions / Insert / Data menus, Fill, Delete Cells, Delete Row, column menu
Keys: Menu 1, 2, 3 on a sheet; right-click on a cell range, on a row number and on a column letter; Fill from Menu 3 3 and from the cell context menu 4; Delete Cells (context 5); Delete Row (row context 6).
Observed:
- Menu 1 Actions: 1 Move Column, 2 Resize ▸, 3 Select ▸, 4 Go To (Ctrl+G), 5 Recalculate (Ctrl+R), 6 Sort (greyed on an empty cell). Recalculate did not make the blank `u[]` formula columns of S11 compute.
- Menu 2 Insert: 1 Insert Cell (greyed on an empty cell), 2 Insert Row, 3 Insert Column.
- Menu 3 Data: 1 Generate Sequence, 2 Data Capture ▸, 3 Fill, 4 Clear Data (greyed on an empty cell), 5 Random ▸, 6 List Math ▸, 7 List Operations ▸, 8 Summary Plot, 9 Quick Graph (greyed on an empty cell).
- Right-click on a cell or range: 1 Cut, 2 Copy, 3 Paste, 4 Fill, 5 Delete Cells, 6 Sort, 7 Color ▸. Right-click on a row number: 1 Cut, 2 Copy, 3 Paste, 4 Resize Row, 5 Insert Row, 6 Delete Row, 7 Color ▸. Right-click on a column letter: 1 Cut (greyed), 2 Paste, 3 Variables ▸, 4 Resize ▸, 5 Summary Plot, 6 Quick Graph (greyed), 7 Color ▸ (no Delete Column and no Copy shown there).
- Fill: with G3 = 7 and G3:G5 selected, Fill from Menu 3 3 and from the context menu (then also Return) showed no change at all (G4, G5 stayed empty, selection stayed G3:G5, no dialog, no prompt in the entry bar). With an empty selection also nothing. I could not find what Fill needs; marked not understood.
- Delete Cells on a single cell G3 (G1..G4 = 1,2,3,4 in rows 2-5, deleted the cell holding 2): no dialog, the cells below moved up (3 then 4), the last cell became empty, selection stayed on the same cell.
- Delete Row on row 3: no dialog, the whole row went from every column, the rows below moved up (D3 became `_` and its entry bar showed `=_`; G3 became 4).
Screenshot: pages-shots-6/S12a-actions-menu.png, S12b-insert-menu.png, S12c-data-menu.png, S12d-cell-context-menu.png, S12e-fill-no-effect.png, S12f-delete-cells-before.png, S12g-delete-cells-after.png, S12h-row-context-menu.png, S12i-after-delete-row.png, S12j-column-header-context-menu.png
Differs? not known: CASSim should shift cells up on Delete Cells and Delete Row without a dialog; Fill behaviour still to establish.

## S13: assigning an element of a list or variable (Calculator)
Keys: `new1[1]:=4`, `k:=5`, `k[1]:=2`, `xs[1]:={1,2}` (xs already `{0,2,3,4,5,6,7,8}`), then `new1`.
Observed:
- `new1[1]:=4` where new1 did not exist: returned 4 and created the list: `new1` → {4}.
- `k:=5` → 5 (k a plain number). `k[1]:=2` → "Error: Dimension error".
- `xs[1]:={1,2}` (a list into one element) → "Error: Domain error"; xs unchanged (`xs` → {0,2,3,4,5,6,7,8}).
Screenshot: pages-shots-6/S13a-new1-k-assign.png, S13b-xs-domain-error.png, S13c-new1-created.png
Differs? not known: CASSim should create a list on first `name[1]:=x`, Dimension error for an element of a non-list, Domain error for a list into an element.

## S14: naming a column with a name that is already a number variable
Keys: with `k:=5` stored, clicked an empty column's name cell (F), typed `k`, Return.
Observed: "Syntax Error: Cannot accept change: Invalid input." with OK; the name cell stayed in edit mode showing `k` until OK and Esc. (Naming column A `p` or `u` when those were free was accepted; a name already holding a non-list value is refused.)
Screenshot: pages-shots-6/S14-name-column-k-syntax-error.png
Differs? not known.

## S15: `=5` in the `=` row of an empty column
Keys: clicked the `=` row cell of column F, typed `=5`, Return, then Down repeatedly.
Observed: every row of F shows 5, including rows far below the other columns' data: rows 1–5, 7, 13–17 and 18 all show 5 (I stopped at row 18; it does not stop at the longest column). The entry bar of any F cell shows `=5`.
Screenshot: pages-shots-6/S15a-equals-5-column.png, S15b-equals-5-at-row-17.png
Differs? not known: the length of a constant formula column was not established (at least 18 rows).

## S16: Return and typing on a filled cell
Keys: selected F17 (a formula-column cell showing 5): Return; then typed `9`, Return.
Observed: Return on a filled cell enters edit mode with the whole content selected (`=5` highlighted, the entry bar shows `=5`). Typing `9` replaced it and Return gave "Data Loss: This operation may overwrite data in the current column(s). Do you wish to proceed?" with OK and Cancel; Cancel restored `=5` in the cell and left the column untouched.
Screenshot: pages-shots-6/S16a-return-on-filled-cell.png, S16b-type-over-formula-cell-data-loss.png
Differs? not known.

## S17: Sort and undo (sort, insert row, delete row)
Keys: G2:G5 = 1, 4, 3, 2 selected (shift+Down), right-click → 6 Sort; then ctrl+Z. Menu 2 2 (Insert Row) on G3, ctrl+Z. Right-click row number 3 → 6 Delete Row, ctrl+Z.
Observed:
- Sort dialog: title "Sort"; `Range:` g2:g5 (not editable, lower case names); `Sort By:` drop-down (g); `Sort:` drop-down (Ascending); OK, Cancel. OK sorted the range 1, 2, 3, 4 in place.
- One ctrl+Z restored 1, 4, 3, 2.
- Insert Row on G3 inserted an empty row across all columns (D's void and D's values moved down, G's 4, 3, 2 moved down; the constant F column stayed 5 all the way). One ctrl+Z removed it again.
- Delete Row on row 3 removed the row everywhere (D3 became 12 etc.); one ctrl+Z put the row back (D3 `_`, G3 4).
Screenshot: pages-shots-6/S17a-sort-dialog.png, S17b-after-sort.png, S17c-undo-sort.png, S17d-insert-row.png, S17e-undo-insert-row.png, S17f-delete-row.png, S17g-undo-delete-row.png
Differs? not known: each of sort / insert row / delete row is one undo step in the sheet.

## Run / not run / also seen (Part S, this file)
Run: S1–S17 (the S11–S20 "guessed choices" were reduced to what is written above).
Not run (with reason): S18–S20 as separate rows (their content was folded into S11–S17: void formulas, Delete Cells/Row, Fill, `k` naming, `=5`, Return over filled cell, undo after sort/insert/delete); Fill's real behaviour (nothing happened in 4 tries); Delete Column and Insert Column (not tried: no Delete Column in the column's context menu; Insert Column only listed); E4 rest, E7 `=d1+qq` Cancel, E11 column copy/paste: not reached yet (next block in this file if time).
Also seen: Menu 4 Statistics submenu layout; Distributions and Stat Tests lists; Shade P Value splits the page; sheet column header context menu has no Delete Column; Delete Cells/Row never ask a dialog; naming a column with an existing list name `u`: formulas using it raise "Column or Variable?" conflict.

## Next Cowork run: inference dialogs

- **Simulator-verified:** S10's 1-Prop z Test result layout, `a[]` default, Data Loss prompt, and checked two-sided Shade P Value plot (normal curve, both tails, `z` and `PVal` labels); the check 5 corpus cases for `tInterval`, `tInterval_2Samp`, `LinRegtTest`, `LinRegtIntervals`, `χ²GOF` and `FTest_2Samp` (`corpus/seed/035_check5_catalog.yaml`).
- **Hand-verified only:** other added interval and test calculations and dialogs. Their mathematical results are covered by unit tests; their Nspire wording, defaults, and exact result layouts have not been captured.
- **Investigate:** capture the other Confidence Interval and Stat Test dialogs (field order, defaults, result-column defaults, formulas and labels); test Shade P Value for `<` and `>` alternatives and identify which procedures offer it; confirm whether plots update when source data changes and how the split behaves after save/reload.
