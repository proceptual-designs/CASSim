# Emulator check 4: Lists & Spreadsheet results (Part E)

Software: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view, 250% zoom.
Document13, page 1.2. Settings: Radian, Automatic, Real, Float 8.
Observations only. This part was **not run exhaustively**: see the three lists at the end.
Document13 was reused, not a fresh document (shared data from the Calculator page 1.1 was needed).

## Recorded items

### E-link: columns linked to variables
Settings: Radian, Auto, Real, Float 8.
Keys: columns A to D named `xs`, `ys`, `d1`, `d2` (name cell, then values), column E used for cell-entry tests.
Observed: naming a column with an existing list name links the column to that variable. The data shows the list values.
Differs from CASSim? not known. (Detail beyond this was not written down at the time.)

### E-onevar: live One-Variable results
Keys: One-Variable Statistics on `d1`, results placed in columns F and G; then `d1[2]` changed to 10 from the sheet.
Observed: the result cells are live formulas. After the change the results updated (x̄ = 5.75, Σx = 46).
Differs from CASSim? not known.

### E-formula: formula column
Keys: `=xs^2` in the formula cell (row above row 1) of column H. Then typed 99 into H3.
Observed: the column fills with the squares. Typing a value into a cell of the formula column raises a **Data Loss** dialog (OK / Cancel). Cancel restores the formula column. A Conflict Detected dialog was also seen when an entry clashed with a linked variable (wording not recorded exactly).
Screenshot: none saved.
Differs from CASSim? not known.

### E9: shared list sync with the Calculator page
Keys: on Calculator page 1.1 `xs[2]:=20`, Return; back to page 1.2.
Observed: A2 now shows 20 at once. `d1` row 2 shows 10 (earlier change to `d1[2]`). The list and the column are the same object.
Screenshot: pages-shots/E9-shared-list-sync.png
Differs from CASSim? not known.

### E20: cell errors (partial, partly accidental)
Keys: with the cursor in the xs column (a linked column; navigation went astray, so the cells were A1 and A2 and not the planned column I) typed `=1/0` in A1, then `=zzq` in A2. `=a1+"x"` raised a **Syntax Error** dialog (title Syntax Error, message Syntax, with the cell name in the dialog; the earlier note recorded "Syntax Error in Cell: e9" for a similar entry).
Observed:
- `=1/0` in a cell shows **#UNDEF**.
- `=zzq` (undefined name) is stored and shown as the text `zzq`, left-aligned (not right-aligned like a number). The bottom bar shows `=zzq` in italics.
- Entries typed as `sqrt(2)`, `2^0.5` and `pi` without a leading `=` are stored as left-aligned text. Only a leading `=` makes a formula.
Side effect: xs[1] and xs[2] of Document13 were overwritten by these tests. The document is unsaved and the damage is limited to the emulator document.
Screenshot: pages-shots/E20-cell-errors.png
Differs from CASSim? not known.

### E1: Lists & Spreadsheet Menu (labels, numbers, greyed items; the cell K7 was selected)
Top level: 1 Actions, 2 Insert, 3 Data, 4 Statistics, 5 Table (all with `▶`).
- 1 Actions: 1 Move Column, 2 Resize ▶, 3 Select ▶, 4 Go To (Ctrl+G), 5 Recalculate (Ctrl+R), 6 Sort (greyed with K7 selected).
- 1 Actions > 2 Resize: 1 Resize Column Width, 2 Maximize Column Width, 3 Minimize Column Width, 4 Resize Row Height (greyed).
- 1 Actions > 3 Select: 1 Select Row, 2 Select Column, 3 Select Formula Range (greyed).
- 2 Insert: 1 Insert Cell (greyed), 2 Insert Row, 3 Insert Column.
- 3 Data: 1 Generate Sequence, 2 Data Capture ▶, 3 Fill, 4 Clear Data (greyed), 5 Random ▶, 6 List Math ▶, 7 List Operations ▶, 8 Summary Plot, 9 Quick Graph (greyed).
- 3 Data > 2 Data Capture: 1 Automatic, 2 Manual.
- 3 Data > 5 Random: 1 Number, 2 Integer, 3 Binomial, 4 Normal, 5 Sample.
- 3 Data > 6 List Math: 1 Minimum, 2 Maximum, 3 Mean, 4 Median, 5 Sum of Elements, 6 Product of Elements, 7 Sample Standard Deviation, 8 Sample Variance, 9 Population Standard Deviation, A Population Variance (the pane was partly hidden; more rows may follow, not checked).
- 3 Data > 7 List Operations: 1 Cumulative Sum List, 2 Difference List, 3 Augment, 4 Convert Matrix to List (greyed), 5 Left, 6 Mid, 7 Right.
- 4 Statistics: 1 Stat Calculations ▶, 2 Distributions ▶, 3 Confidence Intervals ▶, 4 Stat Tests ▶.
- 5 Table: 1 Switch to Table (Ctrl+T).
Not opened: Distributions, Confidence Intervals and Stat Tests submenus, Data Capture dialogs, Generate Sequence dialog.
Screenshot: pages-shots/E15-sheet-menu.png, E1-actions-menu.png, E13-resize-menu.png, E1-select-menu.png, E1-insert-menu.png, E1-data-menu.png, E1-data-capture.png, E1-random-menu.png, E1-listmath-menu.png, E1-listops-menu.png, E17-statistics-submenu.png, E19-table-menu.png
Differs from CASSim? not known.

### E15: Stat Calculations and Linear Regression (mx+b)
Stat Calculations (15 items, 10 rows show, arrows signal more, Down on the last wraps): 1 One-Variable Statistics…, 2 Two-Variable Statistics…, 3 Linear Regression (mx+b)…, 4 Linear Regression (a+bx)…, 5 Median-Median Line…, 6 Quadratic Regression…, 7 Cubic Regression…, 8 Quartic Regression…, 9 Power Regression…, A Exponential Regression…, B Logarithmic Regression…, C Sinusoidal Regression…, D Logistic Regression (d=0)…, E Logistic Regression (d≠0)… (second part of the label hidden), F Multiple Linear Regression…
Linear Regression (mx+b) dialog, in order: X List (preselected: `a[]`, from the selected cell's column), Y List (empty), Save RegEqn to (`f1`), Frequency List (`1`), Category List (empty), Include Categories (empty), 1st Result Column (default **`b[]`**, the column after the X list: it would overwrite column B, so I typed `j[]`). Buttons OK, Cancel.
Result with `a[]`, `b[]`, 1st Result Column `j[]`: column J holds labels (Title, RegEqn, m, b, r², r, Resid) and column K the values. The formula cell of K shows `=LinRegMx(a[],b[],1): CopyVar stat.results,...` (cut off). K1 is `="Linear Regression (mx+b)"`, K2 `m*x+b`. K7 (Resid) holds a quoted string of the residual list, not a list. A selected cell shows a yellow tooltip with the full text. (The numbers are for data that I had overwritten, so they are not the intended xs, ys values.)
Not run: One-Variable and Two-Variable dialogs again, what happens when the data change (One-Variable was seen live in the first pass).
Screenshot: pages-shots/E15-stat-calcs-top.png, E15-stat-calcs-scrolled.png, E15-linreg-dialog.png, E15-linreg-dialog-scrolled.png, E15-linreg-results.png, E15-linreg-formula.png, E15-resid-tooltip.png
Differs from CASSim? not known.

### E10: Go To
Ctrl+G opens a small dialog titled **Go To** with one text field and OK and Cancel. What it accepts was not tested.
Screenshot: pages-shots/E10-goto-dialog.png

### E19: function table
Ctrl+T on the sheet switches the page to a function table view: an empty table with a function drop-down at the top right (list: `f1`, `stat.regeqn`, `stat.stat`, `stat1.stat`, `stat2.regeqn`, `stat2.stat`), a first column of numbered rows and an empty edit bar. Escape closes the drop-down. Ctrl+T again returns to the sheet. Typing while in the table view enters text in its edit bar (a stray `2` went there).
Screenshot: pages-shots/E19-table-dropdown.png, E19-table-view.png, E19-back-to-sheet.png
Differs from CASSim? not known.

## Run
E-link, E-onevar, E-formula (column formula, Data Loss, Cancel), E1 (menu labels, numbers and greyed items, except the three Stat submenus), E9, E10 (Go To dialog only), E15 (Linear Regression mx+b), E19, E20 (partial).

## Not run
E1 Distributions, Confidence Intervals and Stat Tests submenus; the Generate Sequence and Data Capture dialogs; E2 to E4 (context menus); E6 (formula references); E7 (invalid names); E10 (keys other than Ctrl+G); E11 to E14 (editing and resizing); E15 Two-Variable and the other regressions; E16 (frequency and category); E17 (the dialogs); E18; E21 (void cells); E22 to E24.

## Also seen, not covered
- One-Variable results are live formulas; editing the source list re-computes them.
- The Claude window repeatedly took focus, so some menu captures were partly hidden.
