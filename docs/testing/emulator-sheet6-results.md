# RUN 6 Part C data-page rows: Lists & Spreadsheet (R6-C7 so far)
Captured 2026-11-25 on TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Document2, page 4.2 (Lists & Spreadsheet, Handheld page size). Observations only. Settings in this Problem: RAD (Document Settings were set in Problem 3; not re-opened in Problem 4).

## R6-C7 Fill
- Steps: F1 typed `=a1+1`, Return; F1 selected; Menu 3 (Data) then 3 (Fill); the Fill selection started as a dotted outline from F1; Down pressed 3 times (outline grows to F1:F4); Return.
- Result: Fill WORKS this time. F1:F4 all filled and selected (name box shows F1:F4). Formulas are relative: F3 shows `=a3+1` in the formula bar. A1:A4 are empty, so the cells display `_` (undefined). Shots R6-C7-fill-range-selecting.png, R6-C7-fill-done.png, R6-C7-f3-formula.png.
- ctrl+Z: removes the fill. F2:F4 go empty again, F1 keeps `=a1+1`. Shot R6-C7-after-ctrlz.png.
- Run 5 showed nothing in five tries; here the dotted outline was drawn straight after the second menu digit (no extra step).

## Setup (page 4.2, Lists & Spreadsheet)
Other documents (Document1, 3, 4, 5) were closed at Simon's request (Document1 asked to save: answered No). Columns named by typing the variable name in the grey name cell: A `xs`, B `ys`, C `d1`, D `d2`, E `cat` (linked to the lists defined on page 4.1; the values show straight away). Shot R6-C7-sheet-columns.png.

## R6-C2 t Test, sheet full width (no split) — t Test only so far
`Menu 4 (Statistics) > 4 Stat Tests > 2 t Test…`, Data Input Method Data, μ0 4, List d1[], Frequency List 1, Alt Hyp `Ha: μ ≠ μ0`, no Shade. Results go into two columns, labels in F and values in G, formula in G`=tTest(4,d…`:
- F1 "Title" G1 "t Test"; F2 "Alternate…" (cut off) G2 "μ ≠ μ0"; F3 "t" G3 1.32287…; F4 "PVal" G4 0.22745…; F5 "df" G5 7.; F6 "x̄" G6 5.; F7 "sx := sn-…" G7 2.13808…; F8 "n" G8 8.
- Eight rows, one result per row. Long labels and numbers are cut with "…" at the default column width. Formula bar for G8 shows `=8.` and for G1 `="t Test"`.
- Shots R6-C2-ttest-rows-top.png, R6-C2-ttest-rows-bottom.png.
- 2-Sample t Interval and Linear Reg t Test not run in the sheet.

## R6-C3 Data Input Method (partial)
- t Test opens a first dialog "Data Input Method" with a drop-down showing `Data` and OK / Cancel (shot R6-C3-ttest-method-dialog.png). Then the t Test dialog (see C4). The Stats option was not opened, nor the two-sample dialogs.

## R6-C4 1st Result Column default (partial: cursor in column E, not A)
- Cursor in E (named `cat`, holding data), column F holding a formula in F1 (`=a1+1` from C7). t Test dialog defaults: μ0 empty; List `e[]` (the cursor's column); Frequency List `1`; Alternate Hyp `Ha: μ ≠ μ0`; 1st Result Column `f[]` (the column AFTER the cursor, although F holds data); Draw Shade P Value unticked. Shot R6-C4-ttest-dialog-defaults.png.
- OK then shows a warning dialog titled "Data Loss" ("This operation may overwrite data in the current column(s)…", TI text, do not reuse) with OK and Cancel. After OK the results overwrote F and G. Shot R6-C4-data-loss-dialog.png.
- CASSim note ("column after the cursor, even if it holds data") CONFIRMED for the case run. The brief's case (cursor in A, B holding data) was not run separately.

## R6-C6 Stat Tests (partial)
- Stat Tests list: 1 z Test…, 2 t Test…, 3 2-Sample z Test…, 4 2-Sample t Test…, 5 1-Prop z Test…, 6 2-Prop z Test…, 7 χ² GOF…, 8 χ² 2-way Test…, 9 2-Sample F Test…, A Linear Reg t Test…, then B Multiple Reg Tests…, C ANOVA…, D ANOVA 2-Way… (D is the last). Shot R6-C6-stat-tests-end.png.
- Regression and Distributions lists not scrolled.

## R6-C3 Stats boxes (all four run)
Every test opens first a small "Data Input Method" dialog with a drop-down `Data` / `Stats` (shot R6-C3-method-dropdown.png); the choice is remembered only per test (2-Sample z Test and 2-Sample t Test each opened on Data). With Stats, the fields are (all empty by default unless shown):
- **t Test (Stats)**: μ0, x̄, Sx, n, Alternate Hyp `Ha: μ ≠ μ0`, 1st Result Column `h[]` (cursor was in G), then Draw Shade P Value below (scrolled). Shot R6-C3-ttest-stats-fields.png.
- **2-Sample z Test (Stats)**: σ1, σ2, x̄1, n1, x̄2, n2, Alternate Hyp `Ha: μ1 ≠ μ2`, 1st Result Column `h[]`, Draw: Shade P Value (unticked). Shots R6-C3-2zt-stats-top.png and -bottom.png.
- **2-Sample t Test (Stats)**: x̄1, Sx1, n1, x̄2, Sx2, n2, Alternate Hyp `Ha: μ1 ≠ μ2`, Pooled `No`, 1st Result Column `h[]`, Draw: Shade P Value. Shots R6-C3-2sampt-stats-top.png and -bottom.png.
- **2-Sample t Interval (Stats)**: x̄1, Sx1, n1, x̄2, Sx2, n2, C Level `0.95`, Pooled `No`, 1st Result Column `h[]`. Shots R6-C3-2sampint-stats-top.png and -bottom.png.
- CASSim note ("offers only Data for the two-sample ones") CONTRADICTED: the device offers Stats for all four. The dialog needs Tab (or scrolling) to see the lower fields; the list scrolls inside the dialog.
- Escape in the fields dialog goes back to the Data Input Method dialog, not out; Cancel there closes it.

## R6-C6 Stat Tests and Confidence Intervals (partial)
- Stat Tests list: 1 z Test…, 2 t Test…, 3 2-Sample z Test…, 4 2-Sample t Test…, 5 1-Prop z Test…, 6 2-Prop z Test…, 7 χ² GOF…, 8 χ² 2-way Test…, 9 2-Sample F Test…, A Linear Reg t Test…, B Multiple Reg Tests…, C ANOVA…, D ANOVA 2-Way… (D last). Shot R6-C6-stat-tests-end.png.
- Confidence Intervals list: 1 z Interval…, 2 t Interval…, 3 2-Sample z Interval…, 4 2-Sample t Interval…, 5 1-Prop z Interval…, 6 2-Prop z Interval…, 7 Linear Reg t Intervals…, 8 Multiple Reg Intervals… (8 last). Shot R6-C6-conf-intervals-list.png.
- Regression and Distributions lists not scrolled.

## R6-C8 Insert Row / Insert Column (partial)
- Insert menu (Menu 3... Actions 2 Insert): 1 Insert Cell is greyed with the cursor in a results column (G8); 2 Insert Row; 3 Insert Column. Shot: R6-C8-insert-menu.png.
- Insert Row (cursor row 8): a blank row appears at row 8. The t Test results in F and G did NOT shift down with the data (they stay where they were). ctrl+Z removes the row. Shots: R6-C8-insert-row.png, R6-C8-insert-row-undo.png.
- Insert Column: a new empty column appears (G, left of the cell cursor column). ctrl+Z removes it. Shots: R6-C8-insert-col.png, R6-C8-insert-col-undo.png.

## R6-C9 Summary Plot
- Menu 3 Data, 8 Summary Plot: dialog has X List, Summary List, Display On (Split Page). X List drop-down lists cat, d1, d2, xs, ys. Shots: R6-C9-data-menu.png, R6-C9-dialog.png, R6-C9-xlist-dropdown.png.
- X List xs (numeric), Summary List ys: draws a HISTOGRAM with xs on the x axis (1..9), bars heights equal ys (2,4,6,8,10,12,14,16 rising), y axis labelled ys. Confirms CASSim (numeric X list gives a histogram weighted by the summary list). Shot: R6-C9-xs-ys-histogram.png.
- X List cat with a frequency list: NOT run.

## RUN 6 Part C: lists
Run: R6-C2 (t Test only); R6-C3 (all four Stats boxes); R6-C4 (partial, cursor in E); R6-C6 (partial: Stat Tests, Confidence Intervals); R6-C7; R6-C8 (Insert Row, Insert Column only); R6-C9 (xs/ys histogram only).
Not run: C1, C5, C10 (need a Data & Statistics page); C2 (2-Sample t Interval, Linear Reg t Test); C4 exact case (cursor in A, B holding data); C6 Regression and Distributions lists; C8 Delete Column, Insert Cell on a data cell, Conflict Detected Cancel, whole-column copy/paste; C9 cat with a frequency list.
Also seen, not covered: Insert Cell is greyed in a results column; Insert Row does not move the results cells.
