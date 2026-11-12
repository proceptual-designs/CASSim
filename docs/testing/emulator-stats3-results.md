# Emulator check 6, Part F: Data & Statistics (observations only)

Note for Claude Code (from Simon): captures record behaviour, not look. Do not copy cursor shapes; CASSim should use conventional touch interactions (tap, long-press, swipe, drag handles, on-screen menus), treating key chords and right-click as the function reached.

Settings: Radian / Automatic / Real / Float 8 (title bar RAD). Document2, Problem 1. New Data & Statistics pages added with ctrl+i, 5: page 1.5 (xs vs ys scatter) and page 1.6 (dot plot of d2). Page 1.3 is the earlier split page with a Summary Plot bar chart of d1 by cat. Screenshots in `pages-shots-6/`. Each entry: Differs from CASSim or from this file's expectation? Not compared yet.

### F0 New Data & Statistics page
Keys: ctrl+i, 5. Observed: the new page opened already plotting points with the caption `Caption: cat` (points labelled a, b, c), x and y axes both "Click to add variable". Clicking the x label lists `cat, d1, d2, qq, xs, ys` (after a regression the list also has `stat.freqreg, stat.resid, stat.xreg, stat.yreg`). Choosing `xs` made a dot plot; choosing `ys` for y gave the scatter. Screenshots: F0-new-data-stats-page-caption-cat.png, F0-xaxis-variable-list-with-stat-vars.png, F4-0-scatter-xs-ys-start.png.

### F4 Keys and mouse on the scatter (xs, ys)
- Tab (1st): no visible change. Tab (2nd): x label boxed and its variable list opens. Tab again: y label boxed and its list opens. Next Tab: nothing visible. Esc closes a list. Screenshots F4-a, F4-b, F4-d.
- Inside a variable list, Up on the first item (`cat`) wraps to the last (`ys`) (F4-c).
- Del with nothing selected: no change (F4-e).
- Click on a point: point gets a thick ring (selected) (F4-f). Right arrow with it selected: coordinate label `(4, 7.8)` appears (F4-g). ctrl+Right afterwards: label reads `(4.031, 7.8)` (F4-h); I did not check the xs list afterwards, so whether xs[4] changed is not confirmed.
- ctrl+Up: opens the page sorter ("*Unsaved Document", Problem 1 thumbnails); Return opens the highlighted page again (F4-i, F4-j).
- Drag on empty plot space: no change (F4-k). Mouse wheel over the plot: no change (F4-l).
- Drag along the x axis: the x window pans (axis became 2.5 to 8.5 from about 0.5 to 8.5; points 1 and 2 left the screen) (F4-m). Drag at the y axis (two attempts at x 700 and 690): no change (F4-n); not confirmed that the pointer was on the axis.
Not run: arrow keys with nothing selected, Esc on a selected point, ctrl+Left/Down, Del on a selected point.

### F2 Menus and context menus
- Menu (top level): 1 Plot Type ▶, 2 Plot Properties ▶, 3 Actions ▶, 4 Analyze ▶, 5 Window/Zoom ▶, 6 Settings…
- Analyze (scatter): 1 Remove (grey), 2 Add Movable Line, 3 Lock Intercept at Zero (grey), 4 Plot Function, 5 Shade Under Function (grey), 6 Regression ▶, 7 Residuals ▶ (grey), 8 Plot Value, 9 Show Normal PDF (grey), A Graph Trace. Screenshot F2-analyze-menu-items.png.
- Analyze > 6 Regression: 1 Show Linear (mx+b), 2 Show Linear (a+bx), 3 Show Median-Median, 4 Show Quadratic, 5 Show Cubic, 6 Show Quartic, 7 Show Power, 8 Show Exponential, 9 Show Logarithmic, A Show Sinusoidal, more below (down arrow; not scrolled). F2-analyze-regression-submenu.png.
- Show Linear (mx+b) result: line drawn, label `y = 1.99815·x+0.025584…` and `r² = 0.998652`. F2-linear-regression-line-and-label.png.
- Right-click on the regression line: 1 Remove Regression, 2 Shade Under Function, 3 Show Residual Squares, 4 Show Residual Plot, 5 Graph Trace, 6 Color ▶. F2-regression-line-context-menu.png. Color ▶: 1 Line Color, 2 Fill Color (grey), 3 Text Color (grey). F2-regression-line-color-submenu.png. Line Color opens a grid titled "Line Color", 5 columns x 3 rows: row 1 dark blue, blue, brown, red, magenta; row 2 green, light blue, orange, yellow, white; row 3 four greys light to dark then black (black selected). F2-regression-line-color-grid.png.
- Right-click on the equation label: the same six-item list as the line (F2-equation-label-context-menu.png).
- Right-click on empty plot space: 1 Zoom ▶, 2 Connect Data Points (F2-empty-space-context-menu.png).
- Actions (scatter): 1 Hide/Remove item (label shows "Hide Linear (mx+b)" while the regression is shown), 2 Hide Text (grey), 3 Insert Text, 4 Insert Slider, 5 Select All Points, 6 Select Image (grey), 7 Sort ▶ (grey). F1-actions-menu-sort-grey-on-scatter.png.

### F1 Sort
On the Summary Plot bar chart (page 1.3, d1 by cat), Actions has 7 Sort ▶ enabled with 1 List Order, 2 Value Order, 3 Alpha Order. Value Order: bars reordered a (20), c (11), b (9). Alpha Order: a, b, c. List Order not run. Screenshots F1-actions-menu-sort-live-on-bar-chart.png, F1-sort-submenu-list-value-alpha.png, F1-sort-value-order-a-c-b.png, F1-sort-alpha-order-a-b-c.png.

### F13 Movable line
Analyze > 2 Add Movable Line on the scatter (regression removed): line with label `m1(x):=3.19061·x−8.15829`. Dragging near the upper end downward rotated it: label `m1(x):=2.50959·x−6.26753`. Screenshots F13-movable-line-added.png, F13-movable-line-rotated-by-drag.png.

### F16 Dot plot of d2 (page 1.6)
- Window/Zoom: 1 Window Settings…, 2 Zoom – Data, 3 Zoom – In, 4 Zoom – Out.
- Window Settings dialog for a dot plot has only XMin and XMax: -0.8 and 32.8 at first.
- Zoom – In: a magnifier icon shows at the top left and the item is grey in the menu while the mode is active; a click on the plot zoomed by 2 about the click: XMin 5.7959731543624, XMax 22.5959731543624.
- Zoom – Out with a click at the same place: back to -0.8 / 32.8.
- Zoom – Data: no visible change, -0.8 / 32.8.
Screenshots F16-*.png.

### F17 Shift+click and selection
On the scatter with the regression removed: click one point, shift+click a second: both show the thick ring (xs = 4 and 6). While the regression line was shown, clicking on a point that lies on the line selected nothing visible (F17-click-on-point-selects-line-not-point.png). On page 1.3 the bar chart (d1 by cat) showed parts of bars a and c highlighted (the selected cases) (F17-selection-shows-in-bar-chart-on-1.3.png). Spreadsheet highlight not checked.

---

## Lists for Part F (check 6)

### Run
F0 (new page), F4 (Tab, Esc, Del, arrows on a selected point, ctrl+arrows, page sorter, point click, drags, wheel), F2 (Analyze, Regression, line/label/empty-space context menus, Color), F1 Sort (value and alpha on the bar chart), F13 rotate movable line, F16 dot plot, F17 shift+click.

### Not run (with reason)
F4: arrow keys with nothing selected, Esc and Del on a selected point, ctrl+Left/Down; y-axis drag not confirmed. F1: List Order. F2: other Regression submenu items, histogram bar and box plot context menus (done in check 5). F17: spreadsheet highlight check; whether xs changed after ctrl+Right. F22: Quick Graph with two columns. F11, F12, F18, F20, F21: done in check 5 and not repeated. Reason: stopped at this point for hand-back.

### Also seen, not covered
Pointer shows a magnifier while Zoom – In is active; the on-screen ctrl and number keys can show red after key chords (not investigated); new D&S pages start with the last cat column as a caption plot; a regression adds `stat.freqreg, stat.resid, stat.xreg, stat.yreg` to the variable lists.
