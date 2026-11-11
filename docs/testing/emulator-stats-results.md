# Emulator check 4: Data & Statistics results (Part F)

Run on the TI-Nspire CX CAS Premium Teacher Software 6.0.3.374 (CX II-T CAS handheld view), Handheld-page-size document (Document14), 250% zoom, 2026-11-12.
Observations only. Screenshots are in `pages-shots/` (cropped to the handheld screen).

**Settings:** Radian (RAD in the title bar), Automatic, Real, Float 8, Exponential Normal, CAS On (the new document already had these; checked in Document Settings, OK pressed). Page 1.1 Calculator holds `xs`, `ys`, `d1`, `d2`, `cat`; page 1.2 Lists & Spreadsheet has columns A to E named `xs`, `ys`, `d1`, `d2`, `cat` (linked); page 1.3 is the Data & Statistics page used for every row below. Shared data was not edited after the setup.

**Typing note for the shared data (a finding):** typing a string list on the Calculator page with a typed `"` does NOT close a string: the editor stays in string mode, so `cat:={"a","b",...}` typed straight through gave `dim(cat)` = 1 (one string `a","b",...`), and the linked spreadsheet column showed that single string in row 1. Closing each string with the **Right arrow** (`"a`, Right, `,"b`, Right ...) gave `dim(cat)` = 8 and a column `a b a c b a c a`. The last `"` typed by hand is also auto-paired. The data used for every row is the correct 8-element `cat`.

## Rows

### F1: Menu tree (Data & Statistics, menu key at (366,379))
Settings: as above.
Keys: mouse: menu key; then jump keys 1 to 6, Left to go back; mouse wheel and arrow clicks tried on the Plot Properties list.
Observed (number, label, `▶` submenu, grey = greyed):
- Top level on the first screen (no variable on an axis): `1 Plot Type ▶` (grey), `2 Plot Properties ▶`, `3 Actions ▶`, `4 Analyze ▶` (grey), `5 Window/Zoom ▶` (grey), `6 Settings…`. Once a variable is on an axis, items 1, 4 and 5 are enabled (screenshot with a histogram shows all six enabled).
- `1 Plot Type ▶`: 1 Dot Plot, 2 Box Plot, 3 Histogram, 4 Normal Probability Plot, 5 Scatter Plot, 6 XY Line Plot, 7 Dot Chart, 8 Bar Chart, 9 Pie Chart. A separator line sits after 4 and after 6. Which are grey depends on the variables (rows F6 to F8); the current plot type is also drawn grey.
- `2 Plot Properties ▶` (the list is longer than the screen: an up arrow and a down arrow are drawn; it contains) 1 Connect Data Points, `2 Histogram Properties ▶` (`1 Histogram Scale ▶` with 1 Frequency, 2 Percent, 3 Density; `2 Bin Settings ▶` with 1 Equal Bin Width, 2 Variable Bin Width), 3 Extend Box Plot Whiskers (the label becomes `Show Box Plot Outliers` after use), 4 Show All Labels, 5 Add X Variable, 6 Add X Summary List, 7 Remove X Variable, 8 Add Y Variable, 9 Add Y Summary List, A Remove Y Variable, B Force Categorical X (the label read `Force Numeric X` in the first-screen state, where x was the categorical `cat`), C Force Numeric Y, D Split Categories by Variable, E Remove Split Variable, F Clear All. Items 1 to 4 are grey unless the plot type fits (1 for a scatter/XY or histogram; 2 for a histogram; 3 for a box plot). With a box plot the visible list starts at item 3; with a histogram it starts at item 1. Items 6, 9 and A, E are grey in the states seen. The up arrow of a scrolled list is clicked or Up pressed past the first enabled item wraps to the last item (`F Clear All`).
- `3 Actions ▶`: 1 Remove (grey), 2 Hide Text (grey), 3 Insert Text, 4 Insert Slider, 5 Select All Points, 6 Select Image (grey), `7 Sort ▶` (drawn grey, not opened).
- `4 Analyze ▶`: 1 Remove (becomes `Hide Linear (mx+b)` after a regression, `Remove Plotted Function` after Plot Function; grey on a bare plot), 2 Add Movable Line, 3 Lock Intercept at Zero (grey until a movable line or function exists), 4 Plot Function, 5 Shade Under Function (grey until a function is plotted), `6 Regression ▶`, `7 Residuals ▶` (grey until a regression is shown), 8 Plot Value, 9 Show Normal PDF (enabled only on a histogram), A Graph Trace.
  - `6 Regression ▶`: 1 Show Linear (mx+b), 2 Show Linear (a+bx), 3 Show Median-Median, 4 Show Quadratic, 5 Show Cubic, 6 Show Quartic, 7 Show Power, 8 Show Exponential, 9 Show Logarithmic, A Show Sinusoidal, B Show Logistic (d=0), C Show Logistic (d≠0) (12 items; the list scrolls and Up from item 1 wraps to C).
  - `7 Residuals ▶`: 1 Show Residual Squares, 2 Show Residual Plot (the labels become Hide Residual Squares and Hide Residual Plot).
- `5 Window/Zoom ▶` (seen with a histogram): 1 Window Settings…, 2 Zoom – Data, 3 Zoom – In, 4 Zoom – Out.
- `6 Settings…`: a dialog (row F19).
Screenshot: pages-shots/F1-menu-top.png, F1-menu-top-histogram.png, F6-plot-type-menu-d1.png, F1-plot-properties-menu-top.png, F1-plot-properties-menu-bottom.png, F10-plot-properties-menu.png, F9-plot-properties-menu-box.png, F1-actions-menu.png, F13-analyze-menu-histogram.png, F13-analyze-menu-with-function.png, F14-regression-submenu-top.png, F14-regression-submenu-bottom.png, F15-residuals-submenu.png, F1-window-zoom-menu.png, F10-histogram-properties-submenu.png, F10-histogram-scale-submenu.png, F10-bin-settings-submenu.png
Differs from CASSim? not known (CASSim comparison not done here).

### F2: Context menus (partial: right click)
Settings: as above.
Keys: mouse: right click.
Observed:
- Empty plot space: `1 Zoom ▶`, `2 Connect Data Points`.
- A data point (a tooltip `(2, 3.9)` appears with it): `1 Zoom ▶`, `2 Connect Data Points`, `3 Color ▶`.
- The x-axis label (a variable name): `1 Force Categorical X`, `2 Remove X Variable`, `3 Zoom ▶`.
Not run: an axis label with no variable, a box plot, a histogram bar, the regression line, the equation label, the `Zoom ▶` and `Color ▶` submenus.
Screenshot: pages-shots/F2-context-empty-space.png, F2-context-x-axis-label.png, F2-context-point.png
Differs from CASSim? not known.

### F3/F5: First screen with the lists defined, and the variable picker
Settings: as above.
Keys: mouse: new page with ctrl+i then 5; click "Click to add variable" on each axis.
Observed: a fresh page with the lists defined shows **8 scattered blue dots, each with a grey letter label (`a`, `b`, `c`), the caption `Caption: cat` at the top left, and the text `Click to add variable` on both axes**. The dots are laid out freely (no axes yet). The dots are labelled by the last list column in the Problem (`cat`). Clicking an axis label opens a drop-down listing the variables with a list icon (`{···}`), in alphabetical order: `cat`, `d1`, `d2`, `xs`, `ys` (the first item is highlighted; Down then Return picks). After a regression is shown the list also contains `stat.freqreg`, `stat.resid`, `stat.xreg`, `stat.yreg` between `d2` and `xs`.
Screenshot: pages-shots/F5-first-screen.png, F5-xpicker.png, F5-ypicker.png
Differs from CASSim? not known.

### F6: One numeric variable (`d1`) on x: each plot type
Settings: as above.
Keys: x axis picker `d1`; Menu > 1 Plot Type > 1 to 4.
Observed: default is a **Dot Plot**: dots stacked above an axis labelled 2 to 9 in steps of 1 (three dots over 4, two over 5, one each over 2, 7, 9). Plot Type menu then: 1 Dot Plot (grey, current), 2 Box Plot, 3 Histogram, 4 Normal Probability Plot enabled; 5 Scatter Plot, 6 XY Line Plot, 7 Dot Chart, 8 Bar Chart, 9 Pie Chart all grey. Box plot: box 4 to 6 with a median line at 4.5, whiskers 2 and 9. Histogram: bars of width 1, y axis labelled `Frequency`, x axis 2 to 11. Normal probability plot: y axis `Expected z`, a fitted line labelled **`y = (x-5)/2.1380899`** (drawn as a stacked fraction), x axis 2 to 9.
Screenshot: pages-shots/F6-dotplot-d1.png, F6-plot-type-menu-d1.png, F6-box-plot-d1.png, F6-histogram-d1.png, F6-normal-prob-plot-d1.png
Differs from CASSim? not known.

### F7: Two numeric variables (`xs`, `ys`)
Keys: x `xs`, then Menu > 2 Plot Properties > 8 Add Y Variable > `ys` (a y variable picked from the y-axis label also works).
Observed: **Scatter Plot** with x axis 1 to 8 (labels every 1) and y axis labelled 4, 10, 16 (every 6, with minor ticks). Plot Type menu: 1 to 4 grey, 5 Scatter Plot grey (current), **6 XY Line Plot enabled**, 7 to 9 grey. XY Line joins the points with straight segments (that capture was hidden behind a pop-up and is not saved).
Screenshot: pages-shots/F7-scatter-xs-ys.png, F7-plot-type-menu.png
Differs from CASSim? not known.

### F8: Categorical `cat` on x
Keys: x picker `cat`; Plot Type 7, 8, 9.
Observed: **Dot Chart** is the default: dots stacked per category `a` (4, blue), `b` (2, orange), `c` (2, green), category names under the axis. Plot Type menu with `cat`: 1 to 6 grey, 7 Dot Chart (current, grey), 8 Bar Chart, 9 Pie Chart enabled. **Bar Chart**: y axis `Frequency` 0 to 4 (labels 0, 2, 4), bars coloured per category; hovering a bar shows a tooltip with two lines `a` and `4 cases (50.0%)`. **Pie Chart**: halves and quarters coloured as the bars, category names drawn outside the slices; the tooltip format is `b` / `2 cases (25.0%)` (the tooltip lagged behind the mouse by one move, so the slice it named was not checked).
Screenshot: pages-shots/F8-dot-chart-cat.png, F8-plot-type-menu.png, F8-bar-chart.png, F8-bar-hover.png, F8-pie-chart.png, F8-pie-hover.png
Differs from CASSim? not known.

### F9: Box plot of `d2`
Keys: x picker `d2`; Plot Type 2; Plot Properties 3; mouse hover.
Observed: **the outlier 30 is a separate dot by default**; the box is 4 to 6, median line at 4.5, whiskers 2 to 7. x axis 0 to 32 in steps of 4. Hover tooltips (they appear after a second small mouse move and can lag): `Q₁: 4`, `Median: 4.5`, `Q₃: 6`, and a bare `7` at the end of the upper whisker. (The tooltip for the outlier itself was not captured.) With `d1`, `Q₁: 4` and `Median: 4.5` were seen on the same plot style. Plot Properties > `3 Extend Box Plot Whiskers` draws the upper whisker to 30 and removes the separate dot; the menu item then reads `3 Show Box Plot Outliers`.
Screenshot: pages-shots/F9-box-plot-d2.png, F9-hover-q1.png, F9-hover-q3.png, F9-hover-whisker-end.png, F9-hover-median.png, F9-extended-whiskers.png, F9-show-outliers-menu.png, F9-plot-properties-menu-box.png, F9-plot-properties-dotplot-d2.png
Differs from CASSim? the values match those pinned for `d1` (Q1 4, median 4.5, Q3 6).

### F10: Histogram of `d1`: Histogram Properties
Keys: Plot Type 3; Menu > 2 Plot Properties > 2 Histogram Properties > 1 or 2.
Observed: `Histogram Properties ▶` has `1 Histogram Scale ▶` (1 Frequency (grey, current), 2 Percent, 3 Density) and `2 Bin Settings ▶` (1 Equal Bin Width, 2 Variable Bin Width). **Equal Bin Width Settings** dialog: `Width:` 1 (selected), `Alignment:` 1, buttons OK and Cancel (defaults for `d1`). Bars: [2,3) 1, [4,5) 3, [5,6) 2, [7,8) 1, [9,10) 1. **Hovering the tall bar shows `[4.000, 5.000) 3 points`**, so the value 4 is in [4,5): left-closed bins. Clicking a bar selects it (light blue fill, thick outline).
Screenshot: pages-shots/F10-histogram-properties-submenu.png, F10-histogram-scale-submenu.png, F10-bin-settings-submenu.png, F10-equal-bin-width-dialog.png, F10-hist-bar-tooltip.png, F17-hist-bar-selected.png
Differs from CASSim? not known.

### F11: Two box plots (partial)
Keys: box plot of `d1`; Menu > 2 Plot Properties > 5 Add X Variable > `d2`.
Observed: the picker for Add X Variable lists `cat`, `d1`, `d2`, `stat.freqreg`, `stat.resid`, `stat.xreg`, `stat.yreg`, `xs`, `ys` (the stat lists exist because a regression had been shown). With `d2` added the page shows **two stacked box plots on a shared x axis (0 to 32)**, the left axis labelled `d1` (top) and `d2` (bottom), and a legend at the bottom of the plot `● d1 ● d2`. Plot Properties then: 3 Extend Box Plot Whiskers, 4 Show All Labels (grey), 5, 7, 8 enabled; 6, 9, A grey; B Force Categorical X grey. The "split `d1` by `cat`" route (Plot Properties > D Split Categories by Variable) was pressed but the capture was hidden behind a pop-up: not recorded.
Screenshot: pages-shots/F11-two-box-plots.png, F11-plot-properties-two-x.png
Differs from CASSim? not known.

### F13: Analyze menu items on the scatter plot (partial)
Observed:
- **Add Movable Line**: a thick line appears with the label **`m1(x):=2.5·x-2.15`** (the name `m1` bold). The first line had slope 2.5 and intercept -2.15. Dragging the middle of the line moved it parallel (the label changed to `m1(x):=2.5·x-0.272353`; the slope stayed 2.5). Clicking empty space deselects it and the label disappears; the line stays (drawn thin). Rotating by dragging an end was not tested.
- **Plot Function**: a small box `f1(x) :=` appears in the middle of the plot; typed `2*x`, Return gave a thick line and the label `f1(x):=2·x` (name bold). Analyze item 1 then reads `Remove Plotted Function`, items 3 and 5 are enabled.
- **Plot Value**: box `v1 :=` ; typed `mean(xs)`, Return: a **vertical thick line at x = 4.5** and the label `v1 := mean(xs)` with `=4.5` under it (`xs` bold).
- Lock Intercept at Zero, Shade Under Function, Show Normal PDF, Graph Trace and Add Movable Line rotation were not run (menu only).
Screenshot: pages-shots/F13-movable-line-label.png, F13-movable-line-dragged.png, F13-plot-function-entry.png, F13-plot-value-entry.png, F13-plot-value-result.png, F13-analyze-menu-with-function.png
Differs from CASSim? not known.

### F14: Regression > Show Linear (mx+b) on `xs`, `ys`
Observed: the line is drawn and the label (two lines) reads **`y = 1.99762·x+0.035714`** and **`r² = 0.998839`** (6 significant digits: the page's Display Digits is Float 6, see F19). The Problem then holds four lists `stat.freqreg`, `stat.resid`, `stat.xreg`, `stat.yreg` (seen in the variable picker). `stat.results` was not looked up on a Calculator page. The Analyze item 1 reads `Hide Linear (mx+b)` afterwards. A second regression was not added; Remove was not run.
Screenshot: pages-shots/F14-linear-mxb-label.png
Differs from CASSim? not known.

### F15: Residuals
Observed: **Show Residual Squares** adds a line `Sum of squares = 0.1947619` between the equation and `r²` (the squares themselves are tiny at this scale). **Show Residual Plot** splits the page: the scatter plot above, a **second plot below sharing the x axis**, y axis labelled `Residual` (-0.20 to 0.20). The labels of the main plot overlap the x axis labels and the residual plot.
Screenshot: pages-shots/F15-residual-squares-label.png, F15-residual-plot-layout.png, F15-residuals-submenu.png
Differs from CASSim? not known.

### F16: Window/Zoom (partial)
Observed: Window Settings… for the histogram of `d1`: a dialog with three fields **`XMin` 1.5, `XMax` 11.5, `YMax` 3.45** (no YMin for a histogram), OK and Cancel. Automatic axes seen: `d1` dot plot 2 to 9 labelled every 1; `d2` dot plot and box plot 0 to 32 labelled every 4; `xs` 1 to 8 every 1; `ys` labelled 4, 10, 16 (every 6). Zoom – Data, Zoom – In, Zoom – Out, the scatter plot's Window Settings and the axis drag were not run.
Screenshot: pages-shots/F16-window-settings-hist-d1.png
Differs from CASSim? not known.

### F17: Points (partial)
Observed: hovering or right-clicking a data point shows a tooltip `(2, 3.9)` (x, y in the plot). Clicking the histogram bar [4,5) (the rows where `d1` = 4, rows 2 to 4) **selected rows 2, 3 and 4 in every later plot of the same Problem**: they were drawn thick-outlined with a light fill in the scatter plot, the residual plot and the box plot. The selection did not show in the spreadsheet in this run (the sheet was not looked at while selected). Dragging a point and shift+click were not run.
Screenshot: pages-shots/F17-hist-bar-selected.png, F14-linear-mxb-label.png (selected points 2 to 4)
Differs from CASSim? not known.

### F19: Settings
Observed: dialog `Data & Statistics Settings` with `Display Digits:` a drop-down showing **Float 6** (not Float 8 as the document), and a ticked check box `Diagnostics`; buttons OK and Cancel.
Screenshot: pages-shots/F19-settings-dialog.png
Differs from CASSim? not known.

## Lists

**Run on the emulator:** F1 (menus listed above; the Actions item 7 Sort and the Window/Zoom list of a scatter plot not opened), F2 (three objects), F3/F5, F6, F7, F8, F9, F10, F11 (two box plots only), F13 (Add Movable Line, Plot Function, Plot Value), F14, F15, F16 (histogram Window Settings only), F17 (tooltip and selection link), F19, plus the setup finding about typing strings.

**Not run (reason):**
- F4 keys and mouse (arrows, Tab, Esc, Del, ctrl+arrows, drag, wheel): time.
- F12 Summary List: needs two extra lists on the Calculator page: time.
- F11 split `d1` by `cat`: capture hidden by a pop-up; not repeated.
- F13 Lock Intercept at Zero, Shade Under Function, Show Normal PDF, Graph Trace, movable-line rotation: time.
- F16 Zoom – Data, In, Out, Window Settings for scatter/box/dot plots, axis drag: time.
- F17 drag a point, shift+click, spreadsheet selection check: time.
- F18 live link (editing a value or deleting a list): the task says not to type test entries into the list-linked shared columns.
- F20 Connect Data Points (menu item seen, effect not run), Force Categorical X (item seen), Add Y Variable (used in F7), Remove variable (used to build F8): the effect of Connect Data Points and Force Categorical X was not captured.
- F21 Insert Text, Insert Slider, Select All Points: labels seen in the Actions menu only, no prompt captured.
- F22 Quick Graph: depends on E14, which was not part of this run.
- F2 other objects (box plot, histogram bar, regression line, equation label) and the Zoom and Color submenus: time.

**Also seen, not covered:**
- Strings in a list typed with `"` do not close until Right is pressed (see top of this file).
- Hover tooltips lag one mouse move; the first move often shows the previous tooltip.
- Plot Properties numbering changes with the plot type (the list starts at item 1, 2 or 3).
- A selection made in one plot carries to the other plots of the Problem.
- The XY Line Plot capture and the box plot of `d1` hover on the whiskers were hidden by the Claude window and are not saved.
