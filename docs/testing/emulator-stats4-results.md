# Emulator stats results (check 6, run 5) - PARTIAL

Document5 (Handheld). Settings: Radian, Automatic, Real, Float 8, CAS On (checked in Document Settings first). Data on Calculator page 1.1: xs, ys, d1, d2, cat as in the brief (all stored and echoed correctly). Pages added with ctrl+i then 5 (Add Data & Statistics).
Shots are cropped to the handheld screen in pages-shots-6/.

## R5-G1 drag a point
Settings: as above. Keys: scatter of xs (x axis) and ys (y axis) on one page; dragged the 4th point from (4, 7.8) to a new place with the mouse. Then, on a second page, a dot plot of d1; dragged the dot at 7 to the right by the mouse.
Observed:
- Scatter drag: BOTH coordinates changed. Lists on page 1.1 after: xs = {1,2,3,4.435,5,6,7,8}, ys = {2.1,3.9,6.2,9.776,10.1,12.2,13.8,16.1}. Values show 3 decimal places (4.435, 9.776); I did not check whether more digits are stored.
- Dot plot drag: d1 after = {2,4,4,4.536,5,5,7.536,9}. The dragged dot (7) moved to 7.536, and a SECOND dot (a 4 that was already highlighted/selected from the page's first view) moved by the same +0.536. So dragging a selected point moves every selected point; I did not intend that, so this is what happened, not a designed test.
- The scatter page showed the 4th and 7th points highlighted after the dot drag: selection looked shared by row across plots on the same Problem (observed once).
- Whether other plots update: the scatter page after the dot drag still showed xs/ys as in the first drag (they use different lists), so no cross-update was expected or seen. Plots using the same list were not made.
Shots: R5-G1-scatter-before-drag, -scatter-after-drag, -lists-after-scatter-drag, -dotplot-before-drag, -dotplot-after-drag, -lists-after-dot-drag, -scatter-page-after-dot-drag.
Differs from CASSim? Not compared.

## R5-G2 context menus (right-click), observed
Settings: as above. d1 plotted as box plot and as histogram on page 1.2 (changed with Menu 1 Plot Type); xs/ys scatter with Menu 4 Analyze, 6 Regression, 1 Show Linear (mx+b) on page 1.3.
- Box plot (right-click on the box; a "Q3: 6.268" label appeared while the pointer was there): 1 Dot Plot, 2 Histogram, 3 Normal Probability Plot, 4 Extend Box Plot Whiskers, 5 Zoom ▶, 6 Color ▶.
  - 5 Zoom: 1 Window Settings..., 2 Zoom - Data, 3 Zoom - In, 4 Zoom - Out.
  - 6 Color: 1 Line Color (grey), 2 Fill Color, 3 Text Color (grey).
- Histogram bar: 1 Dot Plot, 2 Box Plot, 3 Normal Probability Plot, 4 Scale ▶, 5 Bin Settings ▶, 6 Zoom ▶, 7 Color ▶.
  - 4 Scale: 1 Percent, 2 Density. 5 Bin Settings: 1 Equal Bin Width, 2 Variable Bin Width. 6 Zoom: same four items as the box plot. 7 Color: same as the box plot (Fill Color only enabled).
- Regression line, and the equation label (same list for both): 1 Remove Regression, 2 Shade Under Function, 3 Show Residual Squares, 4 Show Residual Plot, 5 Graph Trace, 6 Color ▶ (1 Line Color enabled, 2 Fill Color grey, 3 Text Color grey).
- The regression itself showed y = 1.99209·x+0.199255 and r² = 0.995402 for the dragged data (xs/ys as changed in G1). Several points were drawn selected (light fill) because earlier drags left them selected.
- Analyze menu (Menu 4), seen on the way: 1 Remove (grey), 2 Add Movable Line, 3 Lock Intercept at Zero (grey), 4 Plot Function, 5 Shade Under Function (grey), 6 Regression ▶, 7 Residuals ▶ (grey), 8 Plot Value, 9 Show Normal PDF (grey), A Graph Trace. Regression list (first ten): 1 Show Linear (mx+b), 2 Show Linear (a+bx), 3 Show Median-Median, 4 Quadratic, 5 Cubic, 6 Quartic, 7 Power, 8 Exponential, 9 Logarithmic, A Sinusoidal, then a down arrow (more items not seen).
Shots: R5-G2-boxplot-context/-zoom-sub/-color-sub, -histogram-before-menu/-context/-binsettings-sub/-zoom-sub/-color-sub/-scale-sub, -regression-shown/-line-context/-label-context/-color-sub, -analyze-menu, -regression-list.
Differs from CASSim? Not compared.

## R5-I2 stat tests from the sheet (page 1.4, already a split page with the xs/ys scatter on the right)
Run from Menu 4 Statistics > 4 Stat Tests / 3 Confidence Intervals. Data are the drag-changed lists (d1 = {2,4,4,4.536,5,5,7.536,9}); d2 = {2,4,4,4,5,5,7,30}. Dialog drop-downs list 'cat, 'd1, 'd2, 'xs, 'ys.
- Stat Tests list (first ten): 1 z Test..., 2 t Test..., 3 2-Sample z Test..., 4 2-Sample t Test..., 5 1-Prop z Test..., 6 2-Prop z Test..., 7 χ² GOF..., 8 χ² 2-way Test..., 9 2-Sample F Test..., A Linear Reg t Test..., then a down arrow (more not seen).
- Confidence Intervals list: 1 z Interval..., 2 t Interval..., 3 2-Sample z Interval..., 4 2-Sample t Interval..., 5 1-Prop z Interval..., 6 2-Prop z Interval..., 7 Linear Reg t Intervals..., 8 Multiple Reg Intervals....
- t Test: first a box "t Test, Data Input Method: Data" (OK/Cancel; other method not opened). Dialog defaults: μ0 empty; List a[]; Frequency List 1; Alternate Hyp Ha: μ ≠ μ0 (options μ > μ0, μ ≠ μ0, μ < μ0); 1st Result Column b[]; Draw: Shade P Value unticked. I set μ0 = 4, List 'd1, Ha μ > μ0, Shade ticked. Result: the page gained a third pane (shaded t density curve, right tail shaded) with "t = 1.4661" and "PVal = 0.0930"; the results sit in a sheet column (E1 = "t Test", then rows including 1.4661067, 0.09302381, df 7.).
- 2-Sample t Interval: Data Input Method box first (default Data). Dialog fields: List 1 (default e[]), List 2 (blank), Frequency 1 (1), Frequency 2 (1), C Level (0.95), Pooled (No), 1st Result Column (f[]); the dialog scrolls (the mouse wheel scrolled it). I set List 1 'd1, List 2 'd2. Result: new sheet column G (formula =tInterval_...), rows with a title "2-Samp...", Lower -10.194..., Upper 5.21281..., Diff -2.491, and further rows (7.70381... seen); no new pane was made.
- 1-Prop z Test: fields P0 (empty), Successes x (empty), n (empty), Alternate Hyp (default Ha: prop ≠ p0; options prop > p0, prop ≠ p0, prop < p0), 1st Result Column h[], Draw: Shade P Value (unticked). I set 0.5, 30, 50, prop > p0, Shade ticked. Result: a fourth pane: shaded z density curve with "z = 1.4142" and "PVal = 0.0786"; the page is now a 2 by 2 layout (sheet top left, scatter top right, z curve bottom left, t curve bottom right). Results in sheet column I (I1 = "1-Prop z Test").
- Linear Reg t Test: fields X List (default i[]), Y List (blank), Save RegEqn to (f1), Frequency List (1), Alternate Hyp (Ha: β & ρ ≠ 0), 1st Result Column (j[]); no Draw option. I set 'xs and 'ys. Result: new sheet column K (formula =LinRegtT..., K1 = "Linear R..."); no new pane. The result values were not read (column cut off in the half-width sheet).
Result values after the first row (Lower, Upper etc.) are cut off by the narrow split sheet; only those I could read on screen are given.
Shots: R5-I2-stat-tests-list, -t-test-input-method/-dialog-defaults/-list-dropdown/-ha-dropdown/-dialog-filled/-result-split, -conf-intervals-list, -2samp-t-int-input-method/-dialog-defaults/-dialog-scrolled/-result, -1prop-z-dialog-defaults/-ha-dropdown/-dialog-filled/-result-4-panes, -linreg-t-dialog-defaults/-dialog-filled/-result.
Differs from CASSim? Not compared.

## Run / not run / also seen
Run: R5-G1, R5-G2, R5-I2 (all four tests, in Handheld view only so far).
Not run: the F rows (rest of F4, F1, F22). Reason: time in this session.
Also seen, not covered: the Data Input Method "Stats" option, the rest of the stat-test lists, the values in the intervals' result columns.
