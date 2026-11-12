# Emulator check 5: Data & Statistics results (Part F)

Run on the TI-Nspire CX CAS Premium Teacher Software 6.0.3.374 (CX II-T CAS handheld view), Handheld-page-size Document1, 250% zoom, 2026-11-12. Observations only. Screenshots are in `pages-shots-5/` (cropped or zoomed to the handheld screen).

**Settings:** Radian, Automatic, Real, Float 8 (the title bar shows RAD). Same Problem and same lists as Part E (`xs`, `ys`, `d1`, `d2`, `cat` linked to spreadsheet columns A to E). Pages: 1.1 Calculator, 1.2 spreadsheet (split with a Data & Statistics panes from E14/E17), 1.3, 1.4, 1.5 Data & Statistics pages made with ctrl+i, 5. Extra lists on the Calculator page: `v := {1,2,3}`, `c := {4,2,1}`.

**Typing note:** menu navigation is unreliable straight after clicking the menu key if a previous menu or mode is still active. Click the menu key, wait 1 s, press the digit, wait 1 s, then Right to open a submenu, then the next digit. After a submenu has been used the menu often reopens on the same item.

## Rows

### F1: Menu items not covered in check 4
- `Actions` submenu in a Data & Statistics page with a scatter plot: 1 Remove (grey), 2 Hide Text (grey), 3 Insert Text, 4 Insert Slider, 5 Select All Points, 6 Select Image (grey), `7 Sort ▶` (grey, not opened). Screenshot F21-actions-menu.png.
- `Window/Zoom ▶` on a box plot: 1 Window Settings…, 2 Zoom – Data, 3 Zoom – In, 4 Zoom – Out. The same list appears as the `Zoom ▶` item of the context menu. Screenshot F16-window-zoom-menu-box.png, F2-zoom-submenu.png.
- Plot Properties on a scatter plot (list as first seen): 1 Connect Data Points, 2 Histogram Properties ▶ (grey), 3 Extend Box Plot Whiskers (grey), 4 Show All Labels (grey), 5 Add X Variable (grey, x set), 6 Add X Summary List (grey), 7 Remove X Variable, 8 Add Y Variable (grey, y set), 9 Add Y Summary List (grey), A Remove Y Variable, then B… below (scrolls).
- Not run: Sort submenu (item 7 is grey).

### F2: Context menus (right click)
- Axis label with no variable, x axis: `1 Add Variable`, `2 Add X Variable with Summary List`. y axis: `1 Add Variable`, `2 Add Y Variable with Summary List`. Screenshot F2-context-x-axis-no-variable.png, F2-context-y-axis-no-variable.png.
- Box plot (right click on the box; a label `Q₃: 6` appears with it): `1 Dot Plot`, `2 Histogram`, `3 Normal Probability Plot`, `4 Extend Box Plot Whiskers`, `5 Zoom ▶`, `6 Color ▶`. Screenshot F2-context-box-plot.png.
- Histogram (right click on a bar): `1 Force Categorical X`, `2 Add X Variable`, `3 Remove X Variable`, `4 Zoom ▶` (Zoom ▶ is the Window Settings…/Zoom – Data/Zoom – In/Zoom – Out list). Screenshot F2-context-histogram.png, F2-zoom-submenu.png.
- `Color ▶` on the box plot: 1 Line Color (grey), 2 Fill Color, 3 Text Color (grey). Screenshot F2-color-submenu-box.png. The colour choices themselves were not opened.
- Regression line and equation label right-click: not run.

### F4: Keys and mouse on a scatter plot
Not run (time).

### F11: Split `d1` by `cat`
- Plot Properties > `D Split Categories by Variable` is GREY while only `d1` is on the x axis (dot plot) and also with `cat` already on the y axis. Screenshot F11-plot-properties-split-grey-remove-split-on.png.
- Route that worked: `d1` on x, then Plot Properties > 8 Add Y Variable > `cat`. The dot plot becomes three rows labelled a (top), b, c (bottom) with the axis title `cat` on the left, dots coloured per category (a blue, b orange, c green) on the shared x axis 2 to 9; no legend was drawn. Screenshot F11-d1-dot-plot-cat-on-y.png.
- With `cat` on y the Plot Properties list shows `E Remove Split Variable` enabled (so this is the split), `D Split…` grey, `8 Add Y Variable` and `9 Add Y Summary List` grey, `A Remove Y Variable` and `F Clear All` enabled.
- Box plot with the split (Plot Type > 2): three box plots, a (box 3 to 7, median 4.5, whiskers 2 to 9), b (box 4 to 5, median 4.5), c (box 4 to 7, median 5.5), in the same colours. Screenshot F11-split-box-plots-by-cat.png.
- `E Remove Split Variable` returns to a single plot with the y axis reading "Click to add variable" (the d1 box plot stays).

### F12: Frequency data with a summary list
- `Add X Summary List` and `Add Y Summary List` are grey on a fresh page with no variable on the axes. With `c` on x (item 5 Add X Variable, first list), item 9 `Add Y Summary List` became enabled; item 6 `Add X Summary List` stayed grey. Screenshot F12-plot-properties-y-summary-enabled.png.
- `9 Add Y Summary List` opens a variable picker (`c`, `cat`, `d1`, `d2`, `stat3.freqreg`, `stat3.resid`, `stat3.xreg`, `stat3.yreg`, `v`, `xs`, `ys`). Picked `v` (x = `c` = {4,2,1}, summary list `v` = {1,2,3}): the plot switches to a HISTOGRAM with the y axis titled `v`, x axis titled `c`, bars at [1,2) height 3, [2,3) height 2, [4,5) height 1 (x values 1,2,4 are the counts of the data c; each value is plotted with weight from v in the same row: c=1 has weight 3). A small spreadsheet icon sits at the bottom left of the page. Screenshot F12-y-summary-list-picker.png, F12-summary-list-histogram.png.
- With the x variable changed to `d1` (8 entries) and the summary list `v` (3 entries) the histogram used only the first 3 rows (bar at 2 height 1, bar at 4 height 5 = 2+3) while the x axis ran to 22.

### F13: Analyze items
- Show Normal PDF on a histogram of `d1` (Analyze item 9): a curve and the label **`8·normPdf(x,5,2.1380899)`** (n times the bin width times the pdf, with mean and sx from the data, 8 digits). Screenshot F13-normal-pdf-label-histogram.png.
- Lock Intercept at Zero on the movable line (scatter of xs, ys): the label changes from `m1(x):=2.5·x-2.15` to **`m1(x):=2.5·x`** and the line passes through the origin. The Analyze item 3 then reads **`Unlock Movable Line Intercept`**, item 1 reads **`Remove Movable Line`**. Screenshot F13-movable-line-scatter.png, F13-lock-intercept-at-zero.png, F13-analyze-menu-unlock-intercept-label.png.
- Shade Under Function (with a plotted function `f2(x):=2·x`, Analyze 5 enabled only then): a tool icon appears at the top left of the plot and a dotted vertical line follows the mouse. First click gives a vertical line, a boxed label `−∞` at the left and an x label `0.000` at the bottom; the second click fixes the upper bound and shades the area under the curve from x = 0 to the clicked x (grey fill), with the area value **`32.435`** printed in the shaded region (the upper bound was about x = 5.7). Screenshot F13-shade-under-function-first-click.png, F13-shade-under-function-result.png.
- Graph Trace (Analyze A) on the plotted function: an icon appears at the top left and a crosshair with the label **`(4.54,9.08)`** (x, y with 2 decimals) sits on the function near the mouse; **Right twice moved it to `(4.78,9.56)`** (step 0.12 in x). Esc ends the mode. Screenshot F13-graph-trace-start.png, F13-graph-trace-right-twice.png.
- Rotating the movable line by dragging an end: not run.

### F16: Window/Zoom
- Box plot of `d1`: Window Settings shows `XMin` 1.3 and `XMax` 9.7 (no y fields). Screenshot F16-box-d1-window-settings-default.png.
- Zoom – Data on that plot: unchanged (1.3, 9.7).
- Zoom – In is a MODE: a magnifier icon (+) appears at the top left; the next click on the plot zooms about the click point. After one click at the plot centre the window was XMin 3.2590604026846, XMax 7.4590604026846 (width halved, 8.4 to 4.2). Esc (twice) leaves the mode. Screenshot F16-zoom-in-mode-after-click.png, F16-box-d1-window-after-zoom-in.png.
- Zoom – Out (magnifier −) and a click: the window was 1.3 and 9.7 again (it may be that the click undid the zoom; not confirmed with another click). Screenshot F16-box-d1-window-after-zoom-out.png.
- Scatter of `xs`, `ys` (automatic): Window Settings `XMin` 0.3, `XMax` 8.7, `YMin` 0.7, `YMax` 17.5. Screenshot F16-scatter-window-settings.png.
- Histogram of `d1` (check 4): 1.5 / 11.5 / YMax 3.45. Dot plot of `d2` and an axis drag: not run.

### F17: Drag a point, spreadsheet link
- Dragging a point (xs=3 up) in the scatter plot moves it and **writes the new value into the linked list**: `ys[3]` (B3) changed from 6.2 to **9.066** (shown with 3 decimals). The Calculator list changes with it (linked). B3 was retyped to 6.2 afterwards. Screenshot F17-point-dragged.png, F17-sheet-b3-changed-to-9066.png.
- Dragging a point that sits under a text box dragged the text box instead (the text box lay over it).
- Shift+click a second point: the click tool did not apply the shift modifier; not recorded.
- Selection showing in the spreadsheet: not looked at.

### F18: Live link
- Changing `d1[8]` (C8) from 9 to 20 in the sheet moved the dot at 9 to 20 in the dot plot at once, and the x axis rescaled to 2 to 20. Screenshot F18-d1-edit-dot-plot-with-20.png. C8 was set back to 9.
- `DelVar d2` on the Calculator page: result `Done`, no message. The Data & Statistics page that plotted `d2` went back to the first screen (scattered labelled dots, caption `cat`, "Click to add variable" on both axes); the sheet column D lost its name (name cell blank) but kept its values 2, 4, 4, 4, 5, 5, 7, 30. Screenshot F18-delvar-d2-calculator.png, F18-delvar-d2-plot-reset.png, F18-delvar-d2-sheet-column.png. (`d2` is therefore not defined for the rest of this run.)

### F20: Connect Data Points and Force Categorical X
- Connect Data Points (Plot Properties item 1): the item label becomes **`Hide Connecting Lines`** afterwards; the lines were hidden behind the plotted function in the capture and not visible. Screenshot F20-connect-data-points-label-after.png.
- Force Categorical X on `xs` (scatter plot): each distinct x value becomes a category with its own colour (blue, orange, green, red, yellow, magenta, dark blue, brown) and the points are evenly spaced with the numbers as labels; the movable line, the plotted function, the shading and the line label disappeared. Plot Properties item B then reads `Force Numeric X` and brings the numeric x axis back. Screenshot F20-force-categorical-x-on-xs.png.

### F21: Actions
- Insert Text: a framed empty text box appears at the middle of the plot with the cursor in it; typing `hello` and Return puts the text in the box (the frame stays until Esc; afterwards only the text shows). Screenshot F21-insert-text-box.png, F21-text-typed.png.
- Insert Slider: dialog **Slider Settings**: Variable `v1`, Value `1`, Minimum `−5`, Maximum `5`, Step Size `Automatic` (drop-down), Style `Horizontal` (drop-down), Display Digits `Float 3`, check boxes Minimized (off), Show Variable (on), Show Scale (on); OK, Cancel. After OK a small horizontal slider panel with the label `v1 =1.`, scale labels `−5.` and `5.`, and a thumb sits on the plot. Screenshot F21-slider-settings-top.png, F21-slider-settings-bottom.png, F21-slider-on-plot.png.
- Select All Points: all points drawn with a thick outline and a lighter fill. Screenshot F21-select-all-points.png.

### F22: Quick Graph (from E14)
Data > Quick Graph is grey with a rectangle selected (A1:B8, A1:A8) and enabled only when a column NAME cell (the grey header cell) is selected (a column letter shown in the status line). With column A (`xs`) selected it added a new Data & Statistics pane to the page: the page became three panes (sheet left, the earlier normal-curve pane upper right, a new dot plot lower right with eight dots at 1 to 8, x axis `xs`, y axis "Click to add variable"); it is the same plot type and menu as a page made with ctrl+i, 5 (the menu is Plot Type / Plot Properties / Actions / Analyze / Window/Zoom / Settings…, with the right pane focused). Screenshot E14-quick-graph-one-column-three-panes.png, F1-graph-pane-*.png (menu of such a pane).
Not run: Quick Graph with two columns selected (shift+Right from the name cell did not extend the selection).

## Lists

**Run on the emulator:** F1 (Actions and Window/Zoom items), F2 (axis labels with no variable, box plot, histogram, Zoom, Color), F11 (route and layout), F12 (summary list route and plot), F13 (Show Normal PDF, Lock Intercept, Shade Under Function, Graph Trace), F16 (box plot of d1, scatter xs/ys, Zoom In/Out/Data), F17 (drag writes the list), F18 (edit a value; DelVar d2), F20, F21, F22 (one column).

**Not run (reason):**
- F4 keys and mouse (arrows, Tab, Del, ctrl+arrows, wheel, drag on empty space or axis): time.
- F2 regression line and equation label context menus; Color choices; F1 Sort submenu: time or grey.
- F13 rotating the movable line: time.
- F16 dot plot of `d2` and an axis drag: `d2` was deleted by F18, time.
- F17 shift+click and the selection check in the spreadsheet: the click tool does not apply shift; not looked at.
- F22 Quick Graph with two columns: could not select two columns.

**Also seen, not covered:**
- Plot Properties > Split Categories by Variable is grey with a numeric x only; a categorical on the y axis is the way to split.
- After a first use the menu key often reopens on the last item; keys pressed immediately are lost.
- Dragging a point changes the underlying list.
- Insert Slider default name is `v1`, and Plot Function names are `f2` here because `f1` was already a variable (saved RegEqn from E15).
