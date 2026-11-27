# Emulator sheet 7 results (run 7, Part C sheet rows)

TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, keypad + side screen at 250%.
Document Settings: Radian, Automatic, Real, Float 8 (set Real midway through Problem 11; checked).
Observations only. Shots in `pages-shots-7/`.

Data used: page 11.5 Lists & Spreadsheet, `xs` = {1,2,3,4,5,6,7,8} (column A), `ys` = {2,4,5,4,5,7,8,9} (column B).
Column names are typed into the grey name cell (the letter row: click a data cell, Up twice).
Typing a name in the "=" row instead makes a column formula (`=xs` filled the column with xs); ctrl+Z undid it.

## R7-C7 New Data & Statistics page when lists exist
Page 11.6 added with ctrl+I, 5 while `xs` and `ys` both exist. The page opens with a caption "Caption: xs"
and eight unlabelled-axis points, each labelled with its value (1 to 8), scattered over the page (the
"Click to add variable" boxes on both axes are still empty). So it shows the FIRST list (`xs`, the first
column on the sheet), not `ys`. No variable is put on an axis. The point labels 1 to 8 equal both the xs values and the
case numbers (xs = {1..8}), so this run cannot say which they are; run 6 reported case numbers. (Clicking the bottom box
afterwards put `xs` on the x axis as a dot plot at 1 to 8.)
Second look (later, with lists `cat`, `fr`, `xs`, `ys` and `stat2.resid` all present): a new Data & Statistics page opened with the caption
`cat`, the alphabetically first list (the lists were created in the order xs, ys, cat, fr, so it is not the first or the newest created).
The page showed seven dots, only three of them labelled (a, b, c); I did not work out the other four. The variable list offered on the axes is
alphabetical: cat, fr, stat2.resid, xs, ys. (R7-C6 uses this page; shots R7-C6-ds-newpage.png, R7-C6-ds-varlist.png.)
Shot: R7-C7-newds.png

## R7-C8 Menu > Statistics > Stat Calculations, to the end
Sheet menu: 1 Actions, 2 Insert, 3 Data, 4 Statistics, 5 Table. Statistics submenu: 1 Stat Calculations,
2 Distributions, 3 Confidence Intervals, 4 Stat Tests.
Stat Calculations items, in order:
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
Up from item 1 wraps to F, which is the last item (nothing after it).
Shots: R7-C8-statcalc-top.png, R7-C8-statcalc-end.png

## R7-C2 Tests on xs, ys (sheet page 11.5, cursor in D1)
Sheet cells truncate long values ("-3.5641...", "2-Samp..."), so every row was read from `stat.results`
on a Calculator page (typed `stat.` then Down to `results` then Return; stat.results shows a two-column
matrix of the rows below). Autocomplete list after `stat.` for this test: clower, cupper, df, me, n1, n2,
results, stat, sx1, sx2, values, x̄1 ... (TI text, do not reuse; names only).

### 2-Sample t Interval (Menu > Statistics > Confidence Intervals > 4)
Intervals submenu: 1 z Interval, 2 t Interval, 3 2-Sample z Interval, 4 2-Sample t Interval, 5 1-Prop z Interval,
6 2-Prop z Interval, 7 Linear Reg t Intervals, 8 Multiple Reg Intervals.
First dialog: Data Input Method: Data (OK). Second dialog, defaults: List 1 `d[]` (the cursor's column D),
List 2 empty, Frequency 1: 1, Frequency 2: 1, C Level 0.95, Pooled No, 1st Result Column `e[]` (next column
after the cursor column). Entered List 1 `xs`, List 2 `ys`.
Results written to columns E (labels) and F (values), starting at row 1, plus a header cell `=tInterval_2Sample...`
in F's formula row. Rows in order (label, value):
Title "2-Sample t Interval"; CLower -3.5641118; CUpper 1.5641118; x̄Diff -1.; ME 2.5641118; df 13.965087;
x̄1 4.5; x̄2 5.5; sx1 2.4494897; sx2 2.3299295; n1 8.; n2 8.
Shots: R7-C2-2sampt-int-dialog.png, ...-dialog-resultcol.png, ...-results-top.png, ...-results-bottom.png

### Linear Reg t Test (Menu > Statistics > Stat Tests > A), cursor in H1
Stat Tests submenu (first ten of the list seen): 1 z Test, 2 t Test, 3 2-Sample z Test, 4 2-Sample t Test,
5 1-Prop z Test, 6 2-Prop z Test, 7 χ² GOF, 8 χ² 2-way Test, 9 2-Sample F Test, A Linear Reg t Test (more below the arrow, not scrolled).
Dialog defaults: X List `h[]` (cursor column), Y List empty, Save RegEqn to `f1`, Frequency List 1,
Alternate Hyp "Ha: β & ρ ≠ 0", 1st Result Column `i[]`. Entered X `xs`, Y `ys`.
Results in columns I (labels) and J (values). Rows in order:
Title "Linear Reg t Test"; Alternate Hyp "β & ρ ≠ 0"; RegEqn "a+b*x"; t 7.5498344352708 (status bar value of J4;
the sheet cell shows 7.54983...); PVal 0.00028018; df 6.; a 1.4285714; b 0.9047619; s 0.77664316;
SEslope 0.11983864; r² 0.9047619; r 0.95118973; Resid "{...}" (a list, shown as {...} in the matrix).
Reading note: a selected sheet cell shows its full value in the bottom status bar and a tooltip.
Shots: R7-C2-linregt-dialog.png, ...-sheet.png, ...-results-bottom.png, ...-J2.png, ...-J4.png

### 2-Sample t Test (Menu > Statistics > Stat Tests > 4), cursor in L1
Dialog defaults: List 1 `l[]` (cursor column), List 2 empty, Frequency 1: 1, Frequency 2: 1,
Alternate Hyp "Ha: μ1 ≠ μ2", Pooled No, 1st Result Column `m[]`. Entered List 1 `xs`, List 2 `ys`.
Results in columns M (labels) and N (values), rows 1 to 11 (full values read from the status bar):
Title "2-Sample t Test"; Alternate Hyp "μ1 ≠ μ2"; t -0.83666002653408; PVal 0.41687122447454;
df 13.965087281795; x̄1 4.5; x̄2 5.5; sx1 2.4494897427832; sx2 2.3299294900429; n1 8.; n2 8.
(No sp row with Pooled No.) Row 12 empty.
Shots: R7-C2-2sampt-test-dialog-resultcol.png, ...-sheet-top.png, ...-rows6-10.png, ...-rows8-12.png

### 2-Sample z Test (Menu > Statistics > Stat Tests > 3), cursor in P1
Dialog fields in order: σ1 (empty), σ2 (empty), List 1 `p[]` (cursor column), List 2 empty, Frequency 1: 1,
Frequency 2: 1, Alternate Hyp "Ha: μ1 ≠ μ2", 1st Result Column `q[]`, Draw: [ ] Shade P Value (unchecked).
Entered σ1 `2`, σ2 `4`, List 1 `xs`, List 2 `ys`, Shade P Value left unchecked.
Results in columns Q (labels) and R (values), rows 1 to 12 (full values from the status bar):
Title "2-Sample z Test"; Alternate Hyp "μ1 ≠ μ2"; z -0.63245553203368; PVal 0.52708913025021;
x̄1 4.5; x̄2 5.5; sx1 2.4494897427832; sx2 2.3299294900429; n1 8.; n2 8.; σ1 2.; σ2 4.
Row 13 empty. (σ1 and σ2 are the last two rows, after n2; not before the means.)
Shots: R7-C2-2sampz-test-dialog.png, ...-dialog-resultcol.png, ...-sheet-top.png, ...-rows9-13.png

## R7-C3 t Test with the cursor in column A and column B holding data
New sheet page (11.6 after the Problem renumbered; tabs 11.4, 11.5, 11.6). Column B was named `ys`, column A empty,
cursor in A1. Menu > Statistics > Stat Tests > 2 t Test, Data Input Method Data, OK.
Dialog as first shown: μ0 (empty), List `a[]`, Frequency List 1, Alternate Hyp "Ha: μ ≠ μ0",
**1st Result Column `b[]`** (column B was holding `ys` at that moment), Draw: [ ] Shade P Value.
So the default is the column after the cursor column, whether or not it holds data. Matches the CASSim note (`b[]`).
Then I entered μ0 `3`, List `ys`, and pressed OK without re-reading the dialog. No "Conflict Detected" dialog appeared.
The results were written in columns C (labels) and D (values), not B; the header formula cell of D reads `=tTest(3,y...`.
I did not look at the 1st Result Column box after changing the List, so I cannot say whether it moved from `b[]`
to `c[]` when the list changed or the test skipped the occupied column. (To check: change List and re-read the box.)
Results: Title "t Test"; Alternate Hyp "μ ≠ μ0"; t 3.03488... ; PVal 0.01898... ; df 7.; x̄ 5.5 (n = 8 values of ys).
Side note: naming column B `ys` on this new sheet bound it to the EXISTING list `ys` from page 11.5 (same Problem), so it showed
the 8 stored values {2,4,5,4,5,7,8,9} instead of an empty column; the five values I typed were the same numbers.
Shots: R7-C3-ttest-dialog.png, R7-C3-ttest-result-placement.png

## R7-C4 Four panes, one more test with Shade P Value, then ctrl+Z
Setup: new sheet page; doc key > 5 Page Layout > 1 Select Layout; "Use + or - to choose a layout" appears; each press of the
keypad + steps on: (start) sheet left and one pane right; 1 sheet top, one pane below; 2 sheet top-left, two panes below;
3 sheet top-left, one pane top-right, one full-width pane below; 4 sheet top-left, one pane bottom-left, one tall pane right;
5 sheet left, two stacked panes right; 6 **the 2x2 layout with four panes** (sheet top-left, three "Press menu" panes);
7 the sheet alone full page. The keypad minus steps back. Return accepts. Menu > Statistics > Stat Tests > 2 t Test, Data Input Method Data;
dialog Draw: [ ] Shade P Value is unchecked by default EVERY time (it is not remembered); Tab to it and press space to check it.
Used `xs` (values now include my dragged points from R7-C1), μ0 3, 4, 5, 6, 7 in turn; 1st Result Column was the column after the cursor.
- Test 1 (μ0 3): the shade went into the top-right pane (t = 1.5244, PVal = 0.1712); sheet results in B, C.
- Test 2 (μ0 4): the shade went into the bottom-right pane (t = 1.4546, PVal = 0.1891); results in D, E.
- Test 3 (μ0 5): the shade went into the bottom-left pane (t = 1.3848, PVal = 0.2087); results in F, G. Panes now: sheet + 3 shades, all four used.
- Test 4 (μ0 6, the "one more"): **no pane was replaced.** The emulator inserted a NEW PAGE straight after the 2x2 page (it became 11.7, the
  old 11.7 and later pages moved up by one) containing a single full-page shade plot (t = 1.3149, PVal = 0.2300). The 2x2 page kept its three
  shades unchanged. CASSim "replaces the newest pane": that is NOT what the emulator does.
- Test 5 (μ0 7, repeated to check): same again, a new page 11.7 with its own full-page shade (t = 1.2451, PVal = 0.2532); the sheet results went to I, J.
ctrl+Z:
- First time (test 4): one ctrl+Z pressed while on the new shade page (nothing visible changed), then the sheet page: ctrl+Z there switched the view
  to the new shade page. Back on the 2x2 page the sheet's results for test 4 (H, I) were gone, and the three panes were unchanged.
  The new shade page was still there.
- Second time (test 5), step by step: ctrl+Z on the sheet page: the view jumped to the new shade page 11.7, the sheet's results (I, J) were still there.
  A second ctrl+Z on the shade page: the view stayed on the shade page; back on the sheet the results in I, J were gone (H1 empty again).
  The shade page 11.7 was still there after both presses.
So ctrl+Z does not remove the shaded pane or page. It removes the test's results from the sheet, and needs two presses (the first just moves to the shade page).
Shots: R7-C4-layout-2x2.png, ...-dialog-shade-checked.png, ...-shade1.png, ...-shade2.png, ...-shade3-full.png, ...-dialog2-defaults.png,
...-shade4-newpage.png, ...-run2-newpage.png, ...-run2-dialog.png, ...-run2-sheet-before-undo.png, ...-run2-sheet-after-undo1.png, ...-run2-sheet-after-undo2.png

## R7-C5 Delete, Insert Cell, Conflict, column copy and paste
Done on sheet page 11.5 (xs col A, ys col B, results tables from the C2 tests; some data rows had been dragged in R7-C1).
Sheet menus: 1 Actions (1 Move Column, 2 Resize >, 3 Select >, 4 Go To Ctrl+G, 5 Recalculate Ctrl+R, 6 Sort greyed),
2 Insert (1 Insert Cell, 2 Insert Row, 3 Insert Column), 3 Data, 4 Statistics, 5 Table (only 1 Switch to Table Ctrl+T).
Delete Row / Delete Column are NOT in the Menu; they are in the context menu (click the on-screen ctrl key, then the menu key) of a selected
row or column header.
- **Cell context menu** (ctrl+menu on a results cell, F3): 1 Cut, 2 Copy, 3 Paste, **4 Insert Cell (greyed in a results column)**, 5 Delete Cell,
  6 Fill, 7 Variables >, 8 Resize >, 9 Summary Plot, A Quick Graph (greyed), B Color >. CASSim's note (Insert Cell grey in a results column) holds.
- **Row header menu** (click the row number 4, then ctrl+menu): 1 Cut, 2 Copy, 3 Paste, 4 Resize Row, 5 Insert Row, 6 Delete Row, 7 Color >.
- **Delete Row through a results table**: row 4 (label x̄Diff, value -103.475 at the time) deleted with 6. The whole sheet row went: the label column E
  now reads CUpper, ME, df, x̄1, x̄2 (x̄Diff gone) and the values in F were recomputed on the shorter lists and no longer line up with the
  labels (ME -118.25..., df 268.995..., x̄1 6.25988..., x̄2 27.8; CUpper 150.738...). The values are formulas of the list columns, so the lists
  losing a row changed every figure. The cursor ended in C4.
- **Column header menu** (click the letter F, then ctrl+menu): 1 Cut, 2 Copy, 3 Paste, 4 Insert Column, 5 Delete Column, 6 Move Column,
  7 Resize >, 8 Data >, 9 Color >.
- **Delete Column** on F (the results value column): F became empty; the label column E stayed. Columns to its right shifted left.
- **Insert Cell on a data cell** (A8 = 105.33 selected, Menu > Insert > 1): A8 became an empty cell shown as "_" and 105.33 moved down to A9; column B did
  not move, so the lists had different lengths. A dialog opened: "Syntax Error in Column: j", then a "Dimension mismatch" message, from the Linear Reg t Test
  column J that uses xs and ys (TI text, do not reuse). OK dismissed it. ctrl+Z undid the insert (A8 = 105.33 again).
- **Conflict Detected**: NOT seen. What I did see: with the t Test dialog's 1st Result Column set to `a[]` (column A holds `xs`) and OK, the dialog
  "Data Loss": "This operation may overwrite data in the current column(s). Do you wish to proceed?" with OK and Cancel (TI text, do not reuse).
  Cancel closed it and the test dialog; nothing ran and the sheet was unchanged. The same "Data Loss" dialog came from pasting a column onto the occupied
  column B (Cancel left B unchanged). Naming column C `f1` (an existing function) gave "Syntax Error: Cannot accept change: Invalid input." (TI text), no conflict dialog.
- **Whole-column copy and paste**: click column A's name cell, Up until the whole column A is highlighted (header selected), ctrl+C, Right twice
  (column C header selected), ctrl+V: column C filled with the values of A, with no name and no formula (the header stays blank, `xs` is not carried).
Shots: R7-C5-* in pages-shots-7 (insertcell-error, insertcell-result-A8, insertcell-result-A9, insert-menu, actions-menu, cell-menu-results,
rowheader-menu, deleterow-result, colheader-menu, deletecolumn-result, dataloss-dialog, dataloss-resultcol-a, dataloss-after-cancel,
paste-over-B-dataloss, colcopy-paste-C, name-f1-syntax, colA-selected)


## Rows run / not run / also seen
### Run
R7-C1 to R7-C9 (Part C), with shots in pages-shots-7/.
### Not run, with reason
- R7-C5 Insert Row: not reached.
- "Conflict Detected" dialog: not reproduced (a "Data Loss" dialog appeared instead).
- R7-C9: box plot Window/Zoom and the Sort submenu on a categorical plot; ctrl+Z after Quick Graph.
- Not run, F4: ctrl+arrow keys on a selected point and a click-drag of a point on this page (done in C1).
### Also seen, not covered
- The stat variable autocomplete list (cat, fr, stat2.resid, xs, ys).
- Delete Row through a results table removes the whole sheet row and the recomputed values no longer line up.
- Insert Cell leaves lists different lengths (Dimension mismatch).
- Up arrow on a selected scatter point after Right gave no visible y change.
