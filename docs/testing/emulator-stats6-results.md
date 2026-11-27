# Emulator stats 6 results (run 7, Part C Data & Statistics rows)

TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, keypad + side screen at 250%.
Document Settings: Radian, Automatic, Real; Float 8, changed to Float 12 for R7-C1 (see below).
Observations only. Shots in `pages-shots-7/`. Lists: `xs` = {1..8}, `ys` = {2,4,5,4,5,7,8,9} on a sheet in the same Problem.

## R7-C1 Scatter of xs, ys; window x 0..100, y 0..1000; drag a point
Page: new Data & Statistics page (it opened showing the first list `xs`, see R7-C7 in the sheet file).
Clicking the bottom "Click to add variable" box offers the lists: `stat2.resid`, `xs`, `ys` (stat2.resid came from the
Linear Reg t Test that was run earlier in the Problem). Chose `xs` for the x axis (dot plot of xs at 1 to 8), then the
left box, `ys`: a scatter plot. Auto window.
Menu (Data & Statistics): 1 Plot Type, 2 Plot Properties, 3 Actions, 4 Analyze, 5 Window/Zoom, 6 Settings...
Window/Zoom: 1 Window Settings..., 2 Zoom - Data, 3 Zoom - In, 4 Zoom - Out.
Window Settings dialog at the auto window: XMin 0.3, XMax 8.7, YMin 1.3, YMax 9.7 (fields XMin, XMax, YMin, YMax, OK, Cancel).
Entered 0, 100, 0, 1000: all eight points sit in a pile at the origin.
Drag 1: dragged the pile's top point (the point that was xs 8, ys 9) to about (40, 570). The dragged point stays selected
(drawn as a black ring with a pale centre).
Then on the sheet page, Document Settings Display Digits Float 12 (doc, 7, 2, drop-down list Float, Float 1 ... Float 12), OK.
Stored values, shown at Float 12 (status bar of the selected cell): row 8, `xs` **40.06**, `ys` **567.8**.
So the stored value is 4 significant figures here (two decimals on an x range of 100, one decimal on a y range of 1000),
not three decimals. Run 6 stored 6.949 (also 4 significant figures) on a small window. The step looks tied to the axis range
(about range/10000, giving 0.01 for x and 0.1 for y), not a fixed three places. CASSim keeps three places: it would store 40.060 and 567.800 here.
Drag 2 (with the first point still selected): dragged another point of the pile from about (7, 8) to (72, 220). Both points
moved by the same amount: row 7 became xs 72.27, ys 219.8 and row 8 became xs 105.33, ys 779.6 (row 8 had been 40.06, 567.8: the
same shift of +65.27 in x and +211.8 in y). So dragging a point while another is selected moves the whole selection, and the
stored values are the old stored value plus a rounded shift (105.33 has five significant figures; x gains hundredths).
In the plot only the (72, 220) point shows, as row 8 is now past XMax 100.
Shots: R7-C1-scatter-auto.png, R7-C1-windowsettings-default.png, R7-C1-window-0-100.png, R7-C1-dragged.png,
R7-C1-docsettings-float12.png, R7-C1-sheet-B8.png, R7-C1-sheet-A8.png, R7-C1-second-drag-plot.png, R7-C1-second-drag-sheet.png

## R7-C6 Summary Plot with X List `cat` and a frequency list
Data: new sheet page, column A `cat` = {a, b, c} (text), column B `fr` = {3, 5, 2}. Typing note: typing `"a"` in a cell gave the text `a""`;
the opening quote auto-closes, so type `"a` and Return (cell shows a).
**From the sheet** (Menu > Data: 1 Generate Sequence, 2 Data Capture >, 3 Fill, 4 Clear Data greyed, 5 Random >, 6 List Math >,
7 List Operations >, 8 Summary Plot, 9 Quick Graph). 8 Summary Plot opens a dialog: X List (default `cat`), Summary List
(default shown `cat`, I typed `fr`), Display On: Split Page, OK, Cancel. OK: the page splits and a Data & Statistics pane on the right shows a
**bar chart**: bars a = 3 (blue), b = 5 (orange), c = 2 (green), y axis 0.0, 1.5, 3.0, 4.5 labelled `fr`, x axis labelled `cat` with a, b, c;
a small table icon sits at the bottom left of the plot. So a plot DOES appear here (run 6 saw none).
**From a Data & Statistics page** (new page after the sheet; opens showing caption `cat`, see R7-C7): the bottom "Click to add variable" list offers
`cat`, `fr`, `stat2.resid`, `xs`, `ys` (alphabetical). Chose `cat`: a categorical dot plot, one dot each for a, b, c.
Menu > Plot Type with a categorical x: 1 Dot Plot, 2 Box Plot, 3 Histogram, 4 Normal Probability Plot, 5 Scatter Plot, 6 XY Line Plot all greyed,
7 Dot Chart greyed, **8 Bar Chart**, 9 Pie Chart enabled. 8 gives a bar chart with Frequency axis 0 to 1 (one case each).
Menu > Plot Properties (middle of the list, scrolled): 4 Show All Labels, 5 Add X Variable, 6 Add X Summary List (greyed), 7 Remove X Variable,
8 Add Y Variable, 9 Add Y Summary List, A Remove Y Variable (greyed), B Force Numeric X, C Force Numeric Y (greyed); more items above and below.
9 Add Y Summary List opens the list choice (`cat`, `fr`, `stat2.resid`, `xs`, `ys`); `fr` gives the same bar chart: a = 3, b = 5, c = 2,
y axis `fr` 0.0 to 4.5, x axis `cat`.
Shots: R7-C6-sheet-data.png, ...-data-menu.png, ...-summaryplot-dialog-default.png, ...-summaryplot-dialog-filled.png, ...-summaryplot-result.png,
...-ds-newpage.png, ...-ds-varlist.png, ...-ds-cat-dotplot.png, ...-ds-plottype-menu.png, ...-ds-barchart-freq.png, ...-ds-plotprops-menu.png,
...-ds-summarylist-pick.png, ...-ds-summary-result.png

## R7-C9 The Shade area pane menu (H14), F1 List Order, F4 keys, F22 Quick Graph

### H14 Menu of a Shade area pane (the 2x2 page, top-right t-test shade pane focused by a click)
Shots `R7-C9-shade-menu.png`, `-shade-plotprops.png`, `-shade-actions.png`, `-shade-analyze.png`, `-shade-window.png`.
- The pane takes focus on a click and shows the Data & Statistics menu: 1 Plot Type (greyed), 2 Plot Properties, 3 Actions, 4 Analyze, 5 Window/Zoom, 6 Settings...
- Plot Properties live: 5 Add X Variable, 8 Add Y Variable. Greyed: 6 Add X Summary List, 7 Remove X Variable, 9 Add Y Summary List, A Remove Y Variable, B Force Numeric X, C Force Numeric Y, D Split Categories by Variable.
- Actions: 1 Remove and 2 Hide Text greyed; live 3 Insert Text, 4 Insert Slider, 5 Select All Points; 6 Select Image and 7 Sort greyed.
- Analyze: greyed 1 Remove, 3 Lock Intercept at Zero, 6 Regression, 7 Residuals, 9 Show Normal PDF; live 2 Add Movable Line, 4 Plot Function, 5 Shade Under Function, 8 Plot Value, A Graph Trace.
- Window/Zoom: 1 Window Settings..., 3 Zoom - In, 4 Zoom - Out live; 2 Zoom - Data greyed.
- The shade pane is therefore a pane of the page layout that can take focus and has its own (mostly restricted) DS menu.

### F1 List Order
Shot `R7-C9-scatter-sort.png`, `-scatter-window.png`.
- Scatter plot (xs, ys), Menu > 3 Actions: 7 Sort is greyed. Its submenu still shows 1 List Order, 2 Value Order, 3 Alpha Order, all greyed. (Sort needs a categorical or single-variable plot; not reached here.)
- Window/Zoom on the scatter: 1 Window Settings..., 2 Zoom - Data, 3 Zoom - In, 4 Zoom - Out, all live.
- Box plot Window/Zoom not run.

### F4 Keys and mouse on a scatter plot (page of xs, ys; one point dragged earlier to 72.27, 219.8)
- Right with nothing selected: no change.
- Tab: focus goes to the x axis variable box, which opens a list: cat, fr, stat2.resid, xs, ys. A second Tab goes to the y axis box with the same list. Esc closes it. (`-scatter-tab-xaxis.png`)
- Del with nothing selected: no change. ctrl+Right on the last page: no change. ctrl+Up: opens the Page Sorter.
- Click on a point: the point goes hollow (selected). (`-scatter-point-click.png`)
- Then Right: the point moved, label (72.65, 219.8) shown, the pointer is the grab hand (x +0.38). Up straight after gave no visible change in y. Del on the point: nothing. Esc: leaves the grab state, label stays. (`-scatter-point-arrow.png`)
- Drag on empty plot space: no change.
- Drag on the x axis (80 px right): the window pans, x range moves to about -13 to 85. (`-scatter-axis-drag.png`)
- Mouse wheel up 3 over the plot: no change.

### F22 Quick Graph page
Shots `R7-C9-quickgraph.png`, `-quickgraph-menu.png`, `-datamenu-cell.png`.
- On a sheet, Menu > 3 Data: with a single cell selected 8 Summary Plot and 9 Quick Graph are greyed. With the column header of `ys` selected they are live (3 Fill greyed instead).
- 9 Quick Graph splits the page: sheet left, a plot pane right, with `ys` on the horizontal axis (dot plot), "Click to add variable" on the vertical axis, focus in the plot pane.
- Its Menu is the ordinary Data & Statistics menu with 1 Plot Type live (so it is the same page type, not a restricted pane).
- ctrl+Z after it not run.


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
