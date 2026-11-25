# Emulator stats 5 results (Run 6, Handheld view)

Document8 (new document). Document Settings on opening: Float 8, Radian, Normal, Rectangular, Auto, CAS On (inherited, not the defaults I expected; checked in the dialog). Float 12 set later for S1.

## S1 – drag a scatter point with nothing selected; Float 12; show xs
Setup (Calculator page 1.1): `xs:={1,2,3,4,5,6}`, `ys:={2,3,5,4,6,8}`. Then Data & Statistics page 1.2 added with ctrl+I, 5.
Observed:
1. A fresh Data & Statistics page, with lists xs and ys defined, opened already showing a plot of `xs` (a "Caption: xs" line, points labelled 1–6 as case numbers, "Click to add variable" on both axes). I did not choose xs. Not captured as its own screenshot (half-scale only, not saved).
2. Clicking the left axis "Click to add variable" lists `xs` and `ys` (with list icons). I chose ys, then chose xs on the bottom axis: scatter of ys against xs, axes 0.5..5.5 (x) and 2.0..8.0 (y). Screenshot: R6-S1-hh-scatter-before-drag.png.
3. With nothing selected I dragged the point (3,5) straight up with the mouse. The point moved and showed a ring highlight. Screenshot: R6-S1-hh-scatter-after-drag.png.
4. On page 1.1 `ys` then gave `{2,3,6.949,4,6,8}` (Float 8). The list variable itself changed, not just the picture. Screenshot: R6-S1-hh-ys-float8.png.
5. After setting Float 12 in Document Settings, `ys` still gave `{2,3,6.949,4,6,8}` and `xs` gave `{1,2,3,4,5,6}`. Screenshot: R6-S1-hh-ys-float12.png. (So the dragged value is shown as exactly 6.949 at Float 12; I did not check further digits by other means.)
Differs from CASSim or from this file's expectation? Not compared in this run.

## S2 – dialogs and results (Calculator page 1.1, Document8, Float 12)
Menu path: menu, 6 Statistics ▶. Data used for the Linear Reg test: `xs={1,2,3,4,5,6}`, `ys={2,3,6.949,4,6,8}` (ys as left by the S1 drag).

### t Test (menu 6, 7, 2)
- First dialog "t Test": field "Data Input Method:" drop-down with `Data` and `Stats` (default Data). Screenshot R6-S2-hh-ttest-input-method.png.
- Stats dialog fields, in order: μ0, x̄, Sx, n, "Alternate Hyp:" (default `Ha: μ ≠ μ0`). Screenshot R6-S2-hh-ttest-stats-fields.png.
- Entered μ0 5, x̄ 5.4, Sx 1.2, n 10, OK. History echo reads `tTest 5,5.4,1.2,10,0: stat.results`. Result list: "Title" "t Test"; "Alternate Hyp" "μ ≠ μ0"; "t" 1.05409255339; "PVal" 0.319315576017; "df" 9.; "x̄" 5.4; "sx := Sn-1x" 1.2; "n" 10. (Screenshot of the bottom of the result: R6-S2-hh-ttest-result-bottom.png.)

### 2-Sample t Interval (menu 6, 6, 4)
- Stats dialog fields, in order (the dialog scrolls): x̄1, Sx1, n1, x̄2, Sx2, n2, C Level (default 0.95), Pooled (default No). Screenshots R6-S2-hh-2samp-t-int-fields-top.png and R6-S2-hh-2samp-t-int-pooled-field-scaled6.jpg (0.6-scale).
- Entered 5.4, 1.2, 10, 4.8, 1.5, 12, 0.95, Pooled No. Result: "Title" "2-Sample t Interval"; "CLower" -0.601090871756; "CUpper" 1.80109087176; "x̄Diff" 0.6; "ME" 1.20109087176; "df" 19.9803265276; x̄1 5.4; x̄2 4.8; sx1 1.2; sx2 1.5; n1 10.; n2 12. (The "pooled" and "sp" rows, if any, were below the part I viewed: not seen.) Screenshots R6-S2-hh-2samp-t-int-result-bottom.png, R6-S2-hh-2samp-t-int-result-top-scaled6.jpg.

### Linear Reg t Test (menu 6, 7, A)
- Dialog fields, in order: X List, Y List, "Save RegEqn to:" (default `f1`), "Frequency List:" (default `1`), "Alternate Hyp:" (default `Ha: β & ρ ≠ 0`). Screenshot R6-S2-hh-linreg-t-test-dialog.png.
- Entered xs, ys, OK. Result: "Title" "Linear Reg t Test"; "Alternate Hyp" "β & ρ ≠ 0"; "RegEqn" "a+b·x"; "t" 2.83638252595; "PVal" 0.047039689028; "df" 4.; "a" 1.3864; "b" 1.03002857143; "s" 1.51915992293; "SESlope" 0.363148680407; "r²" 0.667913811739; "r" 0.817259941352; "Resid" "{...}". Screenshots R6-S2-hh-linreg-t-test-result-bottom.png, R6-S2-hh-linreg-t-test-result-top-scaled6.jpg (0.6-scale).
Differs from CASSim or from this file's expectation? Not compared in this run.

## S3 – menus scrolled to the end (Calculator, menu 6 Statistics ▶)
Statistics submenu: 1 Stat Calculations ▶, 2 Stat Results, 3 List Math ▶, 4 List Operations ▶, 5 Distributions ▶, 6 Confidence Intervals ▶, 7 Stat Tests ▶ (the 7th label looked like "Stat Test" in one screenshot and "Stat Tests" in another where it was partly covered). Screenshot R6-S3-hh-statistics-menu.png.
- Stat Tests ▶ (7): 1 z Test… 2 t Test… 3 2-Sample z Test… 4 2-Sample t Test… 5 1-Prop z Test… 6 2-Prop z Test… 7 χ² GOF… 8 χ² 2-way Test… 9 2-Sample F Test… A Linear Reg t Test… B Multiple Reg Tests… C ANOVA… D ANOVA 2-Way… (end; Up from item 1 wrapped to D). Screenshots R6-S3-hh-stat-tests-top.png, R6-S3-hh-stat-tests-end.png.
- Distributions ▶ (5): 1 Normal Pdf… 2 Normal Cdf… 3 Inverse Normal… 4 t Pdf… 5 t Cdf… 6 Inverse t… 7 χ² Pdf… 8 χ² Cdf… 9 Inverse χ²… A Binomial Pdf… B Binomial Cdf… C Inverse Binomial… D Inverse Binomial N… E F Pdf… F F Cdf… G Inverse F… H Geometric Pdf… I Geometric Cdf… J Poisson Pdf… K Poisson Cdf… (end). Screenshots R6-S3-hh-distributions-top-scaled6.jpg (0.6-scale), R6-S3-hh-distributions-end.png.
- Stat Calculations ▶ (1) – the "Regression" items live here: 1 One-Variable Statistics… 2 Two-Variable Statistics… 3 Linear Regression (mx+b)… 4 Linear Regression (a+bx)… 5 Median-Median Line… 6 Quadratic Regression… 7 Cubic Regression… 8 Quartic Regression… 9 Power Regression… A Exponential Regression… B Logarithmic Regression… C Sinusoidal Regression… D Logistic Regression (d=0)… E Logistic Regression (d≠0)… F Multiple Linear Regression… G Correlation Matrix (end). Screenshots R6-S3-hh-stat-calc-top-scaled6.jpg (0.6-scale), R6-S3-hh-stat-calc-end.png.
- Confidence Intervals ▶ (6): 1 z Interval… 2 t Interval… 3 2-Sample z Interval… 4 2-Sample t Interval… 5 1-Prop z Interval… 6 2-Prop z Interval… 7 Linear Reg t Intervals… 8 Multiple Reg Intervals… (8 items, no scroll arrow seen). Screenshot R6-S3-hh-conf-intervals-menu.png.
Differs from CASSim or from this file's expectation? Not compared in this run.

## S4 – Fill and ctrl+Z (Lists & Spreadsheet page 1.2, Document8, Handheld)
Setup: A1:A4 = 1, 2, 3, 4 (typed with newlines; half-scale screenshot R6-S4-hh-column-a-values-half.jpg). F1 typed `=a1+1`, Return: F1 shows 2 and its formula line reads `=a1+1`.
Keys: click F1, shift+Down ×3 (selection F1:F4, footer "F1:F4"), menu, 3, 3.
Data menu (spreadsheet) as seen with F1:F4 selected: 1 Generate Sequence, 2 Data Capture ▶ (greyed), 3 Fill (highlighted), 4 Clear Data (greyed), 5 Random ▶ (greyed), 6 List Math ▶ (greyed), 7 List Operations ▶ (greyed), 8 Summary Plot, 9 Quick Graph (greyed); in the top-level menu "2 Insert" and "4 Statistics" appeared greyed and "5 Table" not greyed. Screenshot R6-S4-hh-data-menu-fill-selected.png. (Whether the grey items really were disabled, or just dim styling for this selection, I did not test.)
After the second `3` (Fill): the selection became a dotted-outline box; Down ×3 extended the footer range to F1:F7 (half-scale R6-S4-hh-fill-range-extended-down3-half.jpg). Return: the range stayed F1:F7.
Observed after Return: F1 = 2; F2, F3, F4 blank; F5 shows a small underscore `_`; F6, F7 blank. Formula line for F2 empty. Screenshots R6-S4-hh-after-fill-return.png, R6-S4-hh-after-fill-F2.png. So Fill did NOT visibly produce 3, 4, 5 in F2:F4 in this run.
ctrl+Z once: F5's underscore disappeared and the selection returned to F1:F4 (footer "F1:F4"); F1 stayed 2. Screenshot R6-S4-hh-after-ctrl-z.png.
Differs from CASSim or from this file's expectation? Not compared in this run. (Possible cause of the blank cells, such as my key sequence, is not established.)

### S4 re-run (as the brief says: F1 ALONE selected) – Document9, page 1.2, Handheld, Float 8
My first S4 run above selected F1:F4 before Fill, which is not what the brief says; the blank F2:F4 there is therefore not a valid result for the brief's steps.
Keys: A1:A4 = 1,2,3,4; F1 `=a1+1` (shows 2); click F1 only; menu, 3, 3; Down ×3; Return.
Observed: after the second `3` the dotted fill box appeared below F1 and grew by one row per Down (half-scale R6-S4b-hh-fill-range-dotted-half.jpg, shown after the Downs). After Return: F1 = 2, F2 = 3, F3 = 4, F4 = 5, with F1:F4 selected (footer "F1:F4"). Screenshot R6-S4b-hh-fill-single-cell-after-return.png. Clicking F3 showed its formula line as `=a3+1` (half-scale R6-S4b-hh-F3-formula-half.jpg), i.e. the formula was filled down with relative references.
ctrl+Z (one press): F2:F4 were removed in one step; F1 stayed 2 with formula `=a1+1`. Screenshot R6-S4b-hh-after-ctrl-z.png.
Differs from CASSim or from this file's expectation? Not compared in this run.

## S5 – Insert Cell / Row / Column and ctrl+Z (Lists & Spreadsheet page 1.2, Handheld)
Starting state: A1:A4 = 1, 2, 3, 4.
- With the range F1:F4 selected, menu 1 Actions ▶ showed: 1 Move Column (greyed), 2 Resize ▶ (greyed), 3 Select ▶ (greyed), 4 Go To (Ctrl+G), 5 Recalculate (Ctrl+R), 6 Sort. Screenshot R6-S5-hh-actions-menu-range-selected.png. In the same state menu 2 Insert ▶ was greyed: its items 1 Insert Cell, 2 Insert Row, 3 Insert Column all looked greyed (R6-S5-hh-insert-menu-range-greyed.png). No Delete Column / Delete Row item was seen in menus 1 or 2.
- With a single cell selected (F2), menu 2 Insert ▶ showed 1 Insert Cell, 2 Insert Row, 3 Insert Column in normal (not grey) text (R6-S5-hh-insert-menu-single-cell.png). Insert Cell on the empty F2 showed no visible change.
- Insert Cell on A2: A2 became blank and the old A2:A4 values 2, 3, 4 moved down to A3:A5 (A1 stayed 1). Screenshot R6-S5-hh-after-insert-cell-A2.png.
- Insert Column (menu 2, 3) with A2 selected: a new blank column A appeared and the old column A (1, blank, 2, 3, 4) moved to B. Screenshot R6-S5-hh-after-insert-column.png. ctrl+Z restored it (column A shows 1, blank, 2, 3, 4; half-scale R6-S5-hh-after-ctrl-z-insert-column-half.jpg).
- Insert Row (menu 2, 2) with A2 selected: a new blank row 2 appeared; the earlier blank cell and the values moved down (A1 1, A2 blank, A3 blank, A4 2, A5 3). Screenshot R6-S5-hh-after-insert-row.png. ctrl+Z restored the previous layout (A1 1, A2 blank, A3 2, A4 3, A5 4; half-scale R6-S5-hh-after-ctrl-z-insert-row-half.jpg).
Differs from CASSim or from this file's expectation? Not compared in this run.

NOT run in S5: Delete Column (no menu item found by me; right-click not tried), E7 Cancel on Conflict Detected, E11 whole-column copy/paste.

## S6 – Summary Plot (Document9, Handheld, Float 8, Radian, Normal, Rectangular, Auto, CAS On)
Document9 was a fresh blank document that opened with Float 12 inherited; I set Float 8 in Document Settings first.
Setup (Calculator page 1.1): `cat:={"a","b","c"}` (the echoed line looked as if it had a stray trailing quote mark after the closing brace; not investigated) and `fr:={3,5,2}`. Then Lists & Spreadsheet page 1.2 (ctrl+I, 4).
Keys: menu, 3 (Data), 8 (Summary Plot) with A1 selected on an empty sheet.
Observed dialog "Summary Plot": "X List:" (default `cat`), "Summary List:" (default `cat`), "Display On:" (default `Split Page`). The Summary List drop-down offered `cat` and `fr`; I chose `fr` (half-scale R6-S6-hh-summary-list-fr-half.jpg). Screenshot of the dialog: R6-S6-hh-summary-plot-dialog.png.
Clicked OK. Observed: the page stayed a plain spreadsheet with an empty sheet; no plot or split view appeared in the Handheld screen, the page tabs still read 1.1 and 1.2, and pressing the keypad tab key only drew a focus border round the spreadsheet. Screenshot R6-S6-hh-after-ok-spreadsheet-only.png. I did not find where (or whether) a summary plot was created, and I did not open a Data & Statistics page or its Shade pane menu (H14).
Differs from CASSim or from this file's expectation? Not compared in this run.

## Closing lists (this file)
### Run on the emulator (Handheld view, Document8)
- S1 (drag, Float 12, show xs/ys), S2 (t Test Stats dialog and result, 2-Sample t Interval Stats dialog and result, Linear Reg t Test dialog and result; Data Input Method drop-down), S3 (Stat Tests, Distributions, Stat Calculations incl. regressions, Confidence Intervals scrolled to the end), S4 (Fill, ctrl+Z), S5 (Insert Cell, Insert Column, Insert Row, ctrl+Z; partial), S6 (dialog only; Document9).
### Not run, with reason
- S5: Delete Column, E7 Conflict Detected Cancel, E11 whole-column copy/paste (not reached).
- S6: the Summary Plot dialog was run, but no resulting plot was seen, and the Shade pane Menu (H14) was not reached. S7 (F1 List Order, rest of F4, F22): not reached.
- S2: the rows of the 2-Sample t Interval result below n2 (if any) were not seen; the t Test dialog in Data mode (list fields) was not opened; Linear Reg t Test result `Resid` list not expanded.
- All screenshots are Handheld view; no Computer view captures this file.
### Also seen, not covered
- A fresh Data & Statistics page with defined lists auto-displayed `xs` (S1 step 1) without my choosing it; not investigated further.
- The first S4 run (F1:F4 selected) gave blank F2:F4 and `_` in F5; not explained, superseded by the re-run.
