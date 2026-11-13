# Check 6, part J: categorical charts (TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view)

Observations only; nothing tidied. Captures record behaviour, not look. Settings for every row unless stated: Radian / Automatic / Real / Float 8.

## Setup note
- Data typed on the Calculator (page 1.1): `pets`, `sex` (10 strings each), `kind` (4 strings), `cnt` (5,3,1,1), `yr` (numbers 7,8,7,9,8,7,9,7,8,7). The brief's name `count` cannot be used: `count:={5,3,1,1}` gives Error "Missing (" because `count` is a built-in function name. I used `cnt`.
- Typing strings: `"dog` then Right to leave the quote; the closing `}` is added automatically. A line longer than about 9 characters typed in one go can fail; I typed in chunks.
- A new Lists & Spreadsheet page added with ctrl+i, 4 from page 1.1 is inserted straight AFTER the current page (it became 1.2; the older pages moved up). Columns A to E named `pets`, `sex`, `kind`, `cnt`, `yr` (all linked, values shown). A new Data & Statistics page (ctrl+i, 5) was added after that as 1.3. x axis: click "Click to add variable", pick from the variable list (the list shows cat, cnt, d1, kind, pets, sex, sq, stat.freqreg ... alphabetical).

## J1 - `pets` on x: default plot
- Keys: click the x axis label, choose `pets`.
- Observed: a Dot Chart. Categories along the axis in ALPHABETICAL order (bird, cat, dog, fish), not typed order (dog, cat, fish, bird). Dots stacked upwards, one per case: bird 1, cat 3, dog 5, fish 1. One colour per category (bird blue, cat orange, dog green, fish pink). x axis title `pets` in a box under the axis; y axis shows the grey "Click to add variable" only (no scale).
- Screenshot: J1-dot-chart-pets.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J2 - Plot Type > Bar Chart
- Keys: Menu (click) > 1 Plot Type > 8 Bar Chart. Plot Type list: 1 Dot Plot, 2 Box Plot, 3 Histogram, 4 Normal Probability Plot, 5 Scatter Plot, 6 XY Line Plot (all grey), 7 Dot Chart (grey: current), 8 Bar Chart, 9 Pie Chart. Analyze and Window/Zoom are grey on the dot chart.
- Observed: bars in alphabetical order, same colours, wide bars with a narrow gap (gap about one eighth of a bar width), thin dark border. y axis title `Frequency`; tick labels 0, 2, 4 with minor ticks between; faint horizontal grid lines. x title `pets`. A bar clicked shows a tooltip: `dog` and next line `5 cases (50.0%)`. A selected bar gets a pale fill and a thick border.
- Screenshot: J2-bar-chart-pets.png, J2-bar-click-label.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J3 - Plot Type > Pie Chart
- Observed: a circle with slices; the first slice (bird, alphabetical) starts at 3 o'clock and the slices run CLOCKWISE in alphabetical order (bird, cat, dog, fish; fish ends at 3 o'clock from above). Same colours as the bars. Category names are written outside the pie at each slice (no legend). Click a slice: tooltip `cat` / `3 cases (30.0%)`. Selected slices get a pale fill and a thick border. x title `pets` below; y axis shows the grey "Click to add variable".
- Screenshot: J3-pie-chart-pets.png, J3-pie-click-label.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J4 - Bar Chart: Plot Properties > Show All Labels
- Keys: Menu > 2 Plot Properties (the list opens scrolled; its visible items: 4 Show All Labels, 5 Add X Variable, 6 Add X Summary List (grey), 7 Remove X Variable, 8 Add Y Variable, 9 Add Y Summary List, A Remove Y Variable (grey), B Force Numeric X, C Force Numeric Y, more below with a scroll arrow; 1 to 3 are above, not read).
- Observed: each bar gets a rotated (vertical) label `count (percent)`: `1 (10.0%)`, `3 (30.0%)`, `5 (50.0%)`, `1 (10.0%)`; put above short bars and inside the top of the tallest bar.
- Screenshot: J4-plot-properties-menu-bar.png, J4-show-all-labels.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J5 - Bar Chart: Menu > 3 Actions > 7 Sort
- Observed: Actions menu on a bar chart: 1 Remove (grey), 2 Hide Text (grey), 3 Insert Text, 4 Insert Slider, 5 Select All Points, 6 Select Image (grey), 7 Sort (submenu enabled). Submenu: 1 List Order, 2 Value Order, 3 Alpha Order.
  - List Order: dog, cat, fish, bird (order of first appearance in the list).
  - Value Order: dog (5), cat (3), bird (1), fish (1): largest first, tie broken alphabetically (bird before fish).
  - Alpha Order: bird, cat, dog, fish.
  - Colours stay with the category when bars move.
- Screenshot: J5-actions-menu-bar.png, J5-sort-submenu.png, J5-sort-list-order.png, J5-sort-value-order.png, J5-sort-alpha-order.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J6 - Which menu items are grey on a bar chart and on a pie chart
- Keys: Menu (click) then 1 to 5, read each.
- Observed, Bar Chart: Plot Type 1 to 6 grey, 7 Dot Chart, 8 Bar Chart (current), 9 Pie Chart; Plot Properties as in J4; Actions as in J5; Analyze: everything grey (1 Remove, 2 Add Movable Line, 3 Lock Intercept at Zero, 4 Plot Function, 5 Shade Under Function, 6 Regression, 7 Residuals, 8 Plot Value, 9 Show Normal PDF) EXCEPT A Graph Trace; Window/Zoom: 1 Window Settings grey, 2 Zoom - Data enabled, 3 Zoom - In grey, 4 Zoom - Out grey.
- Observed, Pie Chart: Plot Properties: 4 Show All Labels, 5 Add X Variable grey, 6 Add X Summary List grey, 7 Remove X Variable, 8 Add Y Variable, 9 Add Y Summary List, A Remove Y Variable grey, B Force Numeric X, C Force Numeric Y grey. Analyze: same as bar (only A Graph Trace enabled). Window/Zoom: the top-level item is grey and its four sub-items are all grey (including Zoom - Data).
- Screenshot: J6-bar-analyze-menu.png, J6-bar-window-zoom-menu.png, J6-pie-plot-properties-menu.png, J6-pie-analyze-menu.png, J6-pie-window-zoom-menu.png (bar Plot Properties and Plot Type are in J4 and J2)
- Differs from CASSim or from this file's expectation? Not compared yet.

## J7 - Context (right click) menus
- Keys: right click on each item, read, Escape.
- Observed:
  - A bar: 1 Dot Chart, 2 Pie Chart, 3 Show All Labels, 4 Sort (submenu), 5 Color (submenu; not opened).
  - A pie slice: 1 Dot Chart, 2 Bar Chart, 3 Show All Labels, 4 Sort (submenu), 5 Color (submenu; not opened).
  - A category label on the axis: 1 Force Numeric X, 2 Add X Variable, 3 Remove X Variable, 4 Split Categories by Variable.
  - The axis title box `pets`: 1 Force Numeric X, 2 Remove X Variable.
  - (A first right click on a slice showed the full Menu list, but a menu from the previous step was still open, so I do not count that.)
- Screenshot: J7-context-bar.png, J7-context-pie-slice.png, J7-context-category-label.png, J7-context-x-axis-title.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J8 - Split by a second category (`sex`)
- Keys that work: right click a category label on the axis > 4 Split Categories by Variable, then pick `sex` from the variable list (list: cat, cnt, d1, kind, pets, sex, sq, stat.freqreg, ...). (Plot Properties > D Split Categories was not needed.)
- Observed:
  - Bar Chart: CLUSTERED bars (side by side, not stacked): each pet has an f bar then an m bar; colour now follows `sex` (f blue, m orange), legend box at top left titled `sex` with a square swatch per value; a zero count is drawn as a thin line (bird/m, fish/m); x title becomes `pets / sex`. Counts seen: bird f1 m0, cat f1 m2, dog f2 m3, fish f1 m0.
  - Dot Chart: same clustering; f dots are circles (blue), m dots are squares (orange), the legend shows the same shapes; stacks are side by side per category.
  - Pie Chart: not available once split: with the split on, Plot Type item 9 Pie Chart is grey in the Plot Type menu (seen on both the bar and dot chart).
  - Everything on the page looked selected (thick outlines, dots drawn on bars) right after the split until I clicked an empty part of the plot.
- Screenshot: J8-bar-split-by-sex.png, J8-dot-split-by-sex.png, J8-plot-type-menu-on-split-dot.png, J8-plot-type-menu-on-split-bar.png, J8-variable-list-for-split.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J9 - Summary table on an empty Data & Statistics page (`kind` x, `cnt` summary)
- Observed:
  - A brand-new Data & Statistics page (ctrl+i, 5) is not empty: it opens showing a case plot with the caption "Caption: cat" and dots labelled a, b, c (the first list on the sheet; a case plot of `cat`).
  - Plot Properties on that page: 6 Add X Summary List and 9 Add Y Summary List are GREY; 5 Add X Variable and 8 Add Y Variable are enabled; also listed B Force Numeric X, C Force Numeric Y, D Split Categories by Variable (all grey there). So the Plot Properties route does not work from the empty page.
  - Route that works: right click the x axis label "Click to add variable": a two-item menu `1 Add Variable`, `2 Add X Variable with Summary List`. Item 2 opens a dialog titled `Summary Plot`: X List (default `cat`, a drop-down), Summary List (default `cnt`, a drop-down), OK, Cancel. Choose X List `kind` by opening the drop-down and clicking it (typing `kind` into the field did not work: it ended up as `d1`).
  - With X List `kind`, Summary List `cnt`: the page shows a BAR CHART in the order of the list (dog, cat, fish, bird; not alphabetical), y axis title `cnt` with ticks 0.0, 1.5, 3.0, 4.5; x title `kind`; colours dog green, cat orange, fish red, bird blue (fish is red here, pink in the `pets` plot). A small table icon sits at the bottom left of the page.
  - Plot Type on a summary bar chart: 7 Dot Chart grey, 8 Bar Chart (current), 9 Pie Chart enabled. Pie: dog (first) starts at 3 o'clock and the slices run clockwise in LIST order (dog 50% lower half, then cat, fish, bird), names outside. On the summary pie, 7 Dot Chart is grey and 8 Bar Chart enabled: no dot chart for a summary plot.
  - Two missteps to note: (1) a first try typed `kind` in the dialog and gave X List `d1` with summary `cnt`, which drew a histogram-like plot with two bars (d1 values 2..5, each 5 high). (2) After removing the x variable the y axis held `cnt` as an ordinary variable; right click on the x axis then offered `1 Add Variable`, `2 Add X Summary List` (a different menu), and choosing `kind` there gave the message "Invalid Summary Plot data" on an axis `cnt` / `kind`.
- Screenshot: J9-dialog-summary-plot.png, J9-summary-bar-kind-cnt.png, J9-plot-type-menu-summary-bar.png, J9-summary-pie.png, J9-plot-type-menu-summary-pie.png, J9-context-x-axis-empty-page.png, J9-context-x-axis-y-already-set.png, J9-misstep-x-d1-histogram.png, J9-misstep-invalid-summary-plot-data.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J10 - Summary Plot from the sheet (`kind` and `cnt` columns)
- Keys: select C1:D4 (click C1, shift+Right, shift+Down x3), Menu (click) > 3 Data > 8 Summary Plot.
- Observed: Data submenu with a block selected: 1 Generate Sequence (grey), 2 Data Capture, 3 Fill, 4 Clear Data (grey), 5 Random, 6 List Math, 7 List Operations, 8 Summary Plot, 9 Quick Graph (grey). The dialog `Summary Plot`: X List `kind` (pre-filled from the first selected column), Summary List `cnt` (second column), Display On `Split Page` (drop-down: Split Page, New Page), buttons OK and Cancel. With Split Page and OK: page 1.2 becomes a split page: the sheet on the left (narrow), a Data & Statistics bar chart on the right (kind: dog 5, cat 3, fish 1, bird 1; y title `cnt`, x title `kind`; the table icon bottom left), the sheet keeps its selection C1:D4. The New Page choice was not run.
- Screenshot: J10-data-menu-block-selected.png, J10-summary-plot-dialog.png, J10-display-on-options.png, J10-result-split-page.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J11 - Quick Graph on the `pets` column
- Keys: on the split page click header A (selects the whole column), Menu > 3 Data (with a whole column selected: 3 Fill and 1 Generate Sequence swap places; 8 Summary Plot and 9 Quick Graph enabled) > 9 Quick Graph.
- Observed: the right half of the split page now holds two plots stacked: the summary bar chart (kind) above and, new, a Dot Chart of `pets` below (alphabetical: bird, cat, dog, fish; dots stacked in a packed cluster; axis title `pets`, y axis "Click to add variable"). Colours on this page: bird blue, cat orange, dog green, fish red. So Quick Graph on a text column gives a Dot Chart, placed in the next free slot of the split page (the page layout here had 3 panes: sheet left, two plots right).
- Note: selecting by clicking and shift+Down on a row header selected whole rows (status "1:10"); Quick Graph needs the column selected by clicking its header.
- Screenshot: J11-data-menu-column-selected.png, J11-quick-graph-pets-result.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## J12 - Numeric variable `yr` (values 7,7,7,7,7,8,8,8,9,9) on a new Data & Statistics page
- Settings: Radian/Automatic/Real/Float 8. New D&S page 1.3 (case plot "Caption: cat"); x axis "Click to add variable" clicked, list scrolled to `yr`.
- Keys: pick `yr`; right click the x axis title > 1 Force Categorical X; Menu (click) > 1 Plot Type; pick 8 Bar Chart; right click the axis title > 1 Force Numeric X.
- Observed: (a) default with numeric `yr`: a numeric Dot Plot, axis 6.8 to 9.0 in steps of 0.2, stacks of 5, 3, 2 dots at 7, 8, 9, all blue. (b) Force Categorical X: axis labels 7, 8, 9 (no decimals), a Dot Chart, the three categories coloured blue, orange, green, in numeric order. The axis-title menu then: 1 Force Numeric X is shown only after this; before it the menu was 1 Force Categorical X, 2 Add X Variable, 3 Remove X Variable, 4 Zoom (submenu). (c) Plot Type menu while categorical: 1 to 6 (Dot Plot ... XY Line Plot) grey, 7 Dot Chart grey (current), 8 Bar Chart and 9 Pie Chart enabled. (d) Bar Chart: bars 5, 3, 2 high, y axis `Frequency`, coloured blue, orange, green; the bar chart appears by a lerp (the dots first sit inside the outlined bars, then the bars fill, about 1 to 2 s). (e) Axis-title menu on the bar chart: 1 Force Numeric X, 2 Add X Variable, 3 Remove X Variable, 4 Split Categories by Variable. Force Numeric X from the bar chart returns to the numeric Dot Plot (a), plot type reset to Dot Plot.
- Screenshot: not saved (the zooms were viewed, not written to disk).
- Differs from CASSim or from this file's expectation? Not compared yet.

## J13 - Drag a category label along the axis of a bar chart
- Settings: as J12. New D&S page 1.3, x axis list: picked `pets` (click the x title, the variable list replaces the axis), Plot Type > 8 Bar Chart. Start order was bird, cat, dog, fish (alphabetical), colours bird blue, cat orange, dog green, fish red.
- Keys: left_click_drag from the label `bird` to the right of `fish` (the right end of the axis).
- Observed: the bars were reordered: cat, dog, fish, bird. Each bar kept its colour (cat orange, dog green, fish red, bird blue). So categories can be reordered by hand by dragging a label; the axis title lost its box outline afterwards. Reorder is a view property (the sheet column was not looked at in this row; see J15 for the list).
- Screenshot: not saved (zooms viewed only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## J14 - Drag a bar's top, a dot, a pie slice
- Keys: on the bar chart drag from the top of the `dog` bar down; switch Plot Type > 7 Dot Chart and drag the top dot of the `cat` stack to the right and up; switch to 9 Pie Chart and drag inside the `cat` slice to the upper right.
- Observed: bar chart: the bar did not change height; the `dog` bar became selected (pale green fill, thick outline) and a tooltip `dog / 5 cases (50.0%)` showed. Dot chart: the selection is kept (the five `dog` dots stay pale with thick outline); the dragged `cat` dot sprang back into its stack and is itself shown selected (pale). Pie chart: the selection is kept across plot types: `dog` slice pale with thick outline; the cat slice first showed a part-selected look (a pale wedge in the cat slice with a dashed edge, for the one selected case) and after the drag the whole `cat` slice was pale/selected. Nothing moved, no values changed in any of the three. The pie order after the hand reorder in J13 follows the new order (cat, dog, fish, bird clockwise from 3 o'clock: cat from 3 o'clock down, dog, fish, bird last).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## J15 - Live link: change `pets[1]` to "fish", add an 11th value "snake"
- Settings: as J12. Sheet on page 1.2 (split page: sheet, summary bar chart `kind`/`cnt`, Dot Chart of `pets`); bar/pie of `pets` on page 1.3 (cat and dog were still selected from J14).
- Keys: page 1.2, click a cell in column A, Up x5 to A1 (it held `="dog"`), type `"fish`, Right, Return; then Down x9 to A11 (empty), type `"snake`, Right, Return; then ctrl+Right to page 1.3 (pie), Plot Type > 8 Bar Chart.
- Observed: A1 changed to fish (the entry shows `"fish"` with quotes while editing, `fish` after Return). On the 1.2 Dot Chart the dog stack lost a dot (5 to 4) and fish gained one (1 to 2) at once; no animation seen in the zoom taken 3 s later. The summary bar chart (`kind`/`cnt`) did not change (it is a different list). After "snake" in A11: the 1.2 Dot Chart gained a fifth category `snake` (yellow) at the right end (alphabetical, last), category labels turned vertical (rotated) because of lack of room, dots squeezed small. On page 1.3 the pie then had five slices, in clockwise order from 3 o'clock: bird, cat, dog, fish, snake (the hand order from J13 (cat, dog, fish, bird) was not kept: back to alphabetical); and the bar chart (Plot Type 8) showed bird 1, cat 3, dog 4, fish 2, snake 1 in alphabetical order, snake yellow, y axis Frequency 0 to 4. Selection from J14 persists: cat and dog selected; fish bar is split: bottom part (1 case, pale, thick outline) is the selected case, the top part (red, no outline) the other. The sheet pane on 1.2 showed the selection highlight in the same way (cat, dog dots pale).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## J16 - `cat` on x and `d1` on y (categorical x, numeric y)
- Settings: as J12. Page 1.3 (bar chart of `pets` before). `cat` is {a,b,c} in groups of 4, 2, 2 cases; `d1` values: a: 2,4,5,9; b: 4,5; c: 4,7.
- Keys: click the x title, pick `cat` (bar chart of `cat` appears: a 4, b 2, c 2); right click the y axis title ("Frequency") > menu 1 Add Variable, 2 Add Y Summary List; pick 1 Add Variable, then `d1` in the list; then Menu > 1 Plot Type.
- Observed: with `d1` on y the plot became a dot plot with categorical x: vertical columns of dots above a, b, c, at heights 2,4,5,9 / 4,5 / 4,7 (y axis `d1` 3, 6, 9). Plot Type menu then: 1 Dot Plot grey (current), 2 Box Plot enabled, 3 Histogram enabled, 4 Normal Probability Plot enabled, 5 Scatter Plot grey, 6 XY Line Plot grey, 7 Dot Chart / 8 Bar Chart / 9 Pie Chart grey. Choosing 2 Box Plot gave one vertical box plot per category (a: box about 3 to 7, median 4.5, a line up to the point at 9 and a point at 2 drawn; b: box 4 to 5; c: box 4 to 7, median 5.5), coloured blue, orange, green; some case dots were still drawn selected (pale with thick outline) from earlier selection.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## J17 - A categorical list with an empty string and with a void
- Settings: as J12. Sheet on page 1.2, column A `pets` (10 values), Dot Chart of `pets` on page 1.2 and on 1.3.
- Keys: (a) empty string: click A3, type `"`, Right, Return (cell then holds `""`, the formula bar showed `"[]"` with an empty placeholder box). (b) void: click A4 (held fish), press Delete (the key named Delete in the tool). Then retyped the values (see restore).
- Observed: (a) the cell shows blank; the formula bar shows an empty string. The Dot Chart of `pets` (page 1.3, x `pets`) showed bird 1, cat 3, dog 3, fish 2, snake 1 = 10 dots for 11 cases: no category with an empty label, no extra tick, the empty-string case is simply not drawn. (b) a void cell shows `_` in the cell and `_` in the formula bar; the 1.2 Dot Chart still had the same five categories (that small chart was squashed; individual stacks could not be counted). No error message in either case. Deleting the last cell (A11, the "snake" row) with Delete removed it entirely (the cell goes blank, the `snake` category vanished from the dot chart, 4 categories again), whereas Delete on a cell in the middle of the column left a `_`.
- Restore: A1 dog, A2 cat, A3 dog, A4 fish retyped as strings (the entries now read `"cat"` in the formula bar, where the originals read `="cat"`: same display, possibly a different stored form), A11 cleared. At one point A2 was typed as "dog" by mistake (wrong row clicked) and corrected to "cat".
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## J18 - Menu > 6 Settings on a bar chart
- Keys: page 1.3, Plot Type 8 Bar Chart of `pets`; Menu (click) > 6 Settings...
- Observed: dialog `Data & Statistics Settings`: Display Digits drop-down showing `Float 6` (the document setting is Float 8, so this dialog has its own value), a checkbox `Diagnostics` ticked, buttons OK and Cancel. Same two controls as the numeric-plot dialog from check 4 (F19); no extra control for the bar chart. Cancelled.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## J19 - A percentage bar chart
- Keys: bar chart of `pets`; Menu > 2 Plot Properties, scrolled the whole list with Up/Down; right click menus from J7.
- Observed: Plot Properties on a bar chart lists: 4 Show All Labels, 5 Add X Variable, 6 Add X Summary List (grey), 7 Remove X Variable, 8 Add Y Variable, 9 Add Y Summary List, A Remove Y Variable (grey), B Force Numeric X, C Force Numeric Y (grey), D Split Categories by Variable, E Remove Split Variable (grey), F Clear All. The list starts at item 4 (the up arrow shows, but Up from 4 wraps round to F, so nothing sits above). There is no Frequency / Percent choice anywhere (not here, not in the right click menus recorded in J7). Percentages appear only as the tooltip `dog / 5 cases (50.0%)` and, with Show All Labels, as `count (percent)` labels (J4). The y axis of the bar chart is always `Frequency`.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

---
## Lists for part J (run 2)

### Run
J1 to J19. J6 and J7 done for bar and pie charts. J20 (Window Settings) could not be run: Window/Zoom > 1 Window Settings is grey on bar and pie charts (J6).

### Not run
J20 as above. Screenshots were not saved for J12 to J19 (zooms were read on screen only; the observations in the rows are the record).

### Also seen, not covered by a row
- A new Data & Statistics page opens as a case plot captioned with the first list name, not empty (J9).
- The Plot Properties summary-list items are grey until the page has no plot variables; the right click on the axis offers the summary route (J9).
- `count` is a reserved name on the Calculator (error "Missing ("); I used `cnt`.
- A new Lists & Spreadsheet page added from page 1.1 is inserted right after the current page.
- Colours of categories differ between pages: fish is pink on the `pets` page and red on the summary and quick-graph pages (J1, J9, J11).
- Selection (cases picked by clicking bars/dots/slices) is shared across the pages that use the same lists and persists across plot-type changes; a bar with some selected cases is drawn split (selected part pale with thick outline, the rest in the category colour) (J14, J15).
- Y axis title right click menu on a plot with `d1` on y: 1 Force Categorical Y, 2 Remove Y Variable, 3 Zoom (submenu); on a bar chart the y title menu is 1 Add Variable, 2 Add Y Summary List (J16).
- Plot-type changes and bar/box plot appearance are animated (lerp) for 1 to 2 s; a zoom taken at once shows the old dots inside the new bars (J12).
- Document state at the end of J: Document2, pages 1.1 Calculator, 1.2 split page (sheet, summary bar chart, `pets` dot chart; `pets` restored: dog,cat,dog,fish,cat,dog,bird,dog,cat,dog; `pets` cell entries retyped as strings), 1.3 bar chart of `pets` (manual label order not applied), then the pets/sex D&S page and summary pages, and the Problem 1 pages from part G. `Gshots.zip` and `Jshots.zip` are in pages-shots-6 (extracted; could not be deleted, please delete).
