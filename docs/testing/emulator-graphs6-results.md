# Emulator check 6, run 6: Graphs (R6-D rows)

Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374. Observations only. Not compared with CASSim in this run.
Settings for every new document: Radian, Float 8 (set by hand: the new document came up in Fix 4), Automatic, Real. Handheld page size, Keypad + SideScreen, zoom 250%.
Screenshots: pages-shots-6/R6-*.png. "hh" = Handheld view.

## R6-D1 (hh): dragging an axis on a tick mark

Settings: Document2 (new, Handheld page size), Radian, Float 8, Automatic, Real. Graphs page 1.1, no functions. Menu 4 Window / Zoom ▶ 5 Zoom – Standard, then menu 4 1 Window Settings… read after each drag. Window Settings dialog closed with the Cancel button each time. Drags: the left mouse button dragged 50 screen pixels along the axis, starting on a tick mark.
Keys and observed:
| Step | XMin | XMax | XScale | YMin | YMax | YScale |
|---|---|---|---|---|---|---|
| Before (after Zoom – Standard) | -10 | 10 | Auto | -6.6666666666667 | 6.6666666666667 | Auto |
| x axis tick dragged 50 px outward (to the right) | -8.5945945945946 | 8.5945945945946 | Auto | -5.7297297297297 | 5.7297297297297 | Auto |
| x axis tick dragged 50 px back inward | -9.6951219512194 | 9.6951219512194 | Auto | -6.4634146341463 | 6.4634146341463 | Auto |
| y axis tick dragged 50 px outward (downward) | -6.7183098591549 | 6.7183098591549 | Auto | -4.4788732394366 | 4.4788732394366 | Auto |
| y axis tick dragged 50 px back inward | -9.54 | 9.54 | Auto | -6.36 | 6.36 | Auto |
So in the Handheld view a drag on either axis rescaled both axes together about the origin (the window stayed symmetric about 0), not a pan. An outward drag shrank the range (zoom in) and an inward drag grew it. The x and y ranges kept the ratio of the first window (x range : y range = 3 : 2 each time). The scale stayed Auto and the tick labels changed (0.5 spacing after the outward drags, 1 after the first inward drag). Two small captions ("text" with a tab icon, then "axes") appeared on the graph during the drags and disappeared later; they look like hover captions. The y drag was started at a tick below the origin.
Screenshots: R6-D1-hh-window-settings-before.png; R6-D1-hh-after-drag-x-out-50px-graph.png and R6-D1-hh-window-settings-after-x-out.png; R6-D1-hh-after-drag-x-in-50px-graph.png and R6-D1-hh-window-settings-after-x-in.png; R6-D1-hh-after-drag-y-out-50px-graph.png and R6-D1-hh-window-settings-after-y-out.png; R6-D1-hh-after-drag-y-in-50px-graph.png and R6-D1-hh-window-settings-after-y-in.png
Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-D2 (hh): Graph Trace steps on `f1(x)=x^2`

Settings: Document2, Radian, Float 8, Automatic, Real. Zoom – Standard (window -10 to 10, -6.67 to 6.67 shown). Entry bar shown with ctrl+G; typed `x^2` in `f1(x)=`, Return.
Menus: menu 5 Trace ▶: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▶, 5 Geometry Trace, 6 Erase Geometry Trace (greyed). Menu 5 3 Trace Step… opens a dialog with one field "Trace Step" showing Automatic; its drop-down arrow lists two items: Automatic, Enter Value…. No number is shown for Automatic. Dialog closed with Cancel.
Keys: menu 5 1 Graph Trace (the trace began on f1 at x = 0), then Right 1 time, Right 1 more time (2 in all), Right 8 more (10 in all), then Left 10 times.
Observed (readout bottom right "f1: (x , y)"):
| After | x | y |
|---|---|---|
| start | 0 | 0 |
| Right ×1 | 0.3 | 0.09 |
| Right ×2 | 0.6 | 0.36 |
| Right ×10 | 3 | 9 |
| Left ×10 | 0 | 0 (a "zero" label appears beside the point) |
So the Automatic step moved x by 0.3 per press (the displayed values, 3 decimals not shown), and 10 presses gave exactly 3. During the Right ×10 the window scrolled up: the y axis range became about -3 to 10.33 (the label at the top reads 10.33) while x stayed -10 to 10; the window did not scroll back with the Left presses (still 10.33 at the end).
Screenshots: pages-shots-6/R6-D2-hh-trace-menu-zoom.jpg (zoomed; the menu was open at half scale), R6-D2-hh-trace-step-dialog-automatic.png, R6-D2-hh-trace-start-x0.png, R6-D2-hh-trace-right1.png, R6-D2-hh-trace-right2.png, R6-D2-hh-trace-right10.png, R6-D2-hh-trace-left10-back-to-zero.png
Slip: a first attempt typed `x^2` into the still-open Window Settings dialog (XMin showed `45x^2`, an "Invalid value(s)" error); both closed without applying (OK on the error, then Cancel). The window was then reset with Zoom – Standard.
Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-D3 (hh), part 1: Zoom – Fit with `x^2` alone

Settings: Document2, Radian, Float 8, Automatic, Real. Only `f1(x)=x^2` on the page.
Keys: menu 4 1 Window Settings…, typed `0.3`, Tab, `8.7`, OK (y range left as it was: -3 to 10.333333333333); then menu 4 A Zoom – Fit; then menu 4 1 to read the values (dialog closed with Cancel after).
Observed (Window Settings after Zoom – Fit): XMin 0.3, XMax 8.7, XScale Auto, YMin -7.4706981642471, YMax 83.2576798067181, YScale Auto. So Fit left x as set and only changed y. The y range is the function's range on [0.3, 8.7] (0.09 to 75.69) with about 10% of its length added at each end (75.6 × 0.1 = 7.56). The graph is drawn with the curve rising from the bottom left to the top right; the labels 83.26 (top) and 0.3, 8.7 are on the screen.
Screenshots: pages-shots-6/R6-D3-hh-fit-x2-alone-graph.png, R6-D3-hh-fit-x2-alone-window-settings.png
Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-D3 part 2: Zoom – Fit with the scatter alone, and with x^2 plus the scatter (Handheld)

Data: `xs:={1,2,3,4,5,6,7,8}`, `ys:={2,3,5,8,9,12,14,16}` (defined on page 1.2). Page 1.1: scatter s1 `xs`,`ys`; f1 `x^2` hidden (Actions, Hide/Show).

### Scatter alone, first attempt (uninformative)
- Settings: window left at x 0.3 to 8.7 from the D3 part 1 run, then Zoom – Fit (menu 4 `a`).
- Observed: window settings screenshot only. The data x range 1..8 plus 10% padding is exactly 0.3..8.7, so Fit could not be told apart from "no change". Redone below from a different window.
- Screenshot: `R6-D3-hh-fit-scatter-alone-from-x0.3-8.7-window-settings.png`
- Differs from CASSim or from this file's expectation? Not compared in this run.

### Scatter alone, from window x -5..20, y -3..30
- Settings: Window Settings typed XMin -5, XMax 20, YMin -3, YMax 30, then Zoom – Fit.
- Observed: XMin 0.3, XMax 8.7, YMin 0.6, YMax 17.4. So x = data range 1..8 padded 10% each side (0.7 of 7), y = data range 2..16 padded 10% (1.4 of 14).
- Screenshots: `R6-D3-hh-fit-scatter-alone-from-x-5-20-graph.png`, `R6-D3-hh-fit-scatter-alone-from-x-5-20-window-settings.png`
- Differs from CASSim or from this file's expectation? Not compared in this run.

### f2 `x^2` (red) plus the scatter, from window x -5..20, y -3..30
- Settings: f2 added with menu 3 1 (drawn red; f1 hidden), Window Settings typed as above, then Zoom – Fit.
- Observed: XMin -7.5, XMax 22.5, XScale Auto, YMin -40.0038784663631, YMax 440.0445287900329, YScale Auto. The x window is the old window -5..20 widened by 10% each side (2.5), not the scatter's 0.3..8.7. The y range is set by the parabola over that x range (about 0 to 400 plus padding), so the scatter points sit near the bottom of the screen.
- My reading of the x range is a guess from the numbers (25 wide, 10% each side); not tested with another window.
- Screenshots: `R6-D3-hh-fit-x2-and-scatter-graph.png`, `R6-D3-hh-fit-x2-and-scatter-window-settings.png`; also `R6-D3-hh-scatter-entry-with-f1-before-fit.png` (taken earlier, not described here).
- Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-D4: Graph Entry/Edit, each type opened (Handheld)

Settings: Float 8, Radian, page 1.1 Graphs (Document2). Each entry was opened with menu 3 then the item number; the entry bar shows only the new empty entry, nothing typed. Entries accumulate on the page; I did not delete them between types.

Graph Entry/Edit menu (menu 3): 1 Function, 2 Relation, 3 Equation Templates ▶, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▶, 8 Diff Eq. Sequence submenu (menu 3 7): 1 Sequence, 2 Custom. (Equation Templates ▶ not opened in this run.) Main Graphs menu seen alongside: 1 Actions ▶, 2 View ▶, 3 Graph Entry/Edit ▶, 4 Window / Zoom ▶, 5 Trace ▶, 6 Analyze Graph ▶, 7 Table ▶, 8 Geometry ▶, 9 Settings ▶ (labels cut off at the menu edge on screen: "Graph Entry/E", "Window / Zoo", "Analyze Grap"; Settings label cut).

| Type | Keys | Entry line as shown | Defaults seen |
|---|---|---|---|
| Relation | menu 3 2 | `rel1(x,y)` then an empty entry field with a list icon at the right | none; no range fields |
| Parametric | menu 3 4 | `x1(t)=` / `y1(t)=` / `0≤t≤6.28 tstep=0.13` | t from 0 to 6.28, tstep 0.13 |
| Polar | menu 3 5 | `r1(θ)=` / `0≤θ≤6.28 θstep=0.13` | θ from 0 to 6.28, θstep 0.13 |
| Scatter Plot | menu 3 6 | `s2 {x ← | y ←` (the first scatter on the page was s1; this one is s2) | blank x and y |
| Sequence | menu 3 7 1 | `u1(n)=` / `Initial Terms:=` / `1≤n≤99 nstep=1` | n from 1 to 99, nstep 1 |
| Sequence, Custom | menu 3 7 2 | `p1 {x ← | y ←` / `1≤n≤99 nstep=1` | n from 1 to 99, nstep 1 |
| Diff Eq | menu 3 8 | label `d1:`, ticked checkbox, `y1' =` input box with `...` at the right, then `(x0,y10): ( <x> , <y> )` with a magnifier icon | `<x>` and `<y>` placeholders greyed |

Screenshots (all `pages-shots-6/`, .png): `R6-D4-hh-relation-entry`, `R6-D4-hh-parametric-entry`, `R6-D4-hh-polar-entry`, `R6-D4-hh-scatter-plot-entry-s2`, `R6-D4-hh-sequence-submenu`, `R6-D4-hh-sequence-entry-u1`, `R6-D4-hh-sequence-custom-entry-p1`, `R6-D4-hh-diff-eq-entry-d1`.

Differs from CASSim or from this file's expectation? Not compared in this run.
Not done for D4: typing into any of these entries; the Computer view; Equation Templates ▶ submenu; the `...` button and magnifier in the Diff Eq entry.

## R6-D6 and D5 (colours): Actions leaves, Conditional Attributes, Table > Edit Table Settings (Handheld)

Settings: Float 8, Radian, page 1.1 (Document2): f1 `x^2` hidden, f2 `x^2` red, scatter s1 `xs`,`ys`, window x -7.5..22.5, y -40.0038784663631..440.0445287900329. Several empty entries from D4 are also on the page. All Handheld view only.

### Actions menu (menu 1), full list
1 Pointer, 2 Select ▶, 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw. Separator lines are drawn under 3 Hide/Show, under 6 Delete all and above C MathDraw. The list scrolls (▼ at the bottom of the first view, ▲ after pressing Up, which wrapped to C MathDraw).
Screenshots: `R6-D6-hh-actions-menu-top.png`, `R6-D6-hh-actions-menu-bottom.png`.

### 4 Attributes on the f2 curve
- Keys: menu 1 4, then click the red curve. Panel title "graph f2" with an icon column; Down moves through the rows, the yellow caption names each:
  1. Line weight: "(1/3) Line weight is thin"
  2. Line style: "(1/3) Line style is continuous"
  3. Label style: "(3/5) label style"
  4. Label parameters: caption begins ") Label parameters: Show names" (start of caption cut off in the zoom)
  5. Graph continuity: "(1/2) Graph is continuous"
- Down on row 5 stayed on row 5 (no wrap, three presses). No colour row was in this list. I did not press Left/Right to change a value.
- Screenshots: `R6-D6-hh-attributes-tool-active.png`, `R6-D6-hh-attributes-f2-line-weight.png`, `...-line-style-zoom.jpg`, `...-label-style-zoom.jpg`, `...-label-parameters-zoom.jpg`, `...-graph-continuity-zoom.jpg` (zoom captures, not full-size).

### 5 Set Conditions on f2 (dialog "Conditional Attributes")
- Keys: menu 1 5, click the f2 curve. While the tool was active the curve drew thick and a ghost label `f1: (0,0)` appeared near the origin.
- Dialog fields: Show When (empty, focused), Line Color `<Enter expression>`, Fill Color `<Enter expression>`, buttons Colors…, OK, Cancel.
- Colors… opens "Conditional Color" with the text "The value of the expression determines the object color." (TI text, do not reuse) and 15 numbered swatches in 3 rows of 5, then OK:
  - row 1: 1 navy, 2 blue, 3 light blue, 4 green, 5 brown
  - row 2: 6 magenta, 7 red, 8 orange, 9 yellow, 10 white
  - row 3: 11 very light grey, 12 light grey, 13 mid grey, 14 dark grey, 15 black
  (colour names are my reading of the swatches.)
- I clicked OK on the colour list and Cancel on Conditional Attributes; nothing was entered.
- Screenshots: `R6-D6-hh-set-conditions-dialog-f2.png`, `R6-D6-hh-conditional-color-list-1-to-15.png`.
- This also gives the D5 colour numbering 1 to 15 for conditional colours. D5 itself (defining f1 to f15 and looking at the colours of f8 to f15) was NOT run.

### 8 Coordinates and Equations
- Keys: menu 1 8; tool icon `y=∫(x)` shown at the top left. Clicked the f2 curve, a scatter point and a blank area: no visible change in any case (f2 already shows its equation label). Not investigated further.
- Screenshot: `R6-D6-hh-coordinates-equations-tool-active.png`.

### 9 Calculate
- Keys: menu 1 9; tool icon `a+b` at the top left. Clicked the f2 curve: no visible change. Not investigated further.
- Screenshot: `R6-D6-hh-calculate-tool-active.png`.

### A Redefine
- Keys: menu 1 A; a tool icon appeared at the top left. Clicked the f2 curve: no visible change. Screenshot is half scale only: `R6-D6-hh-redefine-tool-after-click-half.jpg`.

### Not run: 2 Select ▶, 3 Hide/Show (used earlier in D3 setup, not recorded as a row), 6 Delete all, 7 Text, B Insert Slider, C MathDraw.

### Table (menu 7)
- Graphs menu 7 Table: 1 Split-screen Table (Ctrl+T), 2 Remove Table (Ctrl+T), greyed until a table is showing.
- After Split-screen Table: graph on the left, table on the right with columns `x` and `f1(x):=` / `x^2` (f1 is hidden but still listed), the visible rows `1.`/`1.`, `2.`/`4.`, `3.`/`9.`, `4.`/`16.`, `5.`/`25.`. The scroll bar thumb sat in the middle, so there are rows above row 1; the entry line at the bottom shows `1.`.
- Menu key while the table pane has focus gives a different menu: 1 Actions ▶, 2 Table ▶. Table ▶: 1 Remove Table (Ctrl+T), 2 Delete Column, 3 Choose…, 4 Edit Expression, 5 Edit Table Settings….
- 5 Edit Table Settings… (dialog titled "Table"): Table Start `0.` (selected), Table Step `1.0`, Independent `Auto` ▶, Dependent `Auto` ▶, OK, Cancel. Cancelled. Removed the table with ctrl+T.
- Screenshots: `R6-D6-hh-table-menu-before-split.png`, `R6-D6-hh-split-screen-table-f1.png`, `R6-D6-hh-table-pane-menu.png`, `R6-D6-hh-table-submenu.png`, `R6-D6-hh-edit-table-settings-dialog.png`.
- Note: the Table Start in the dialog is 0. but the first visible row was 1.; I did not scroll up to check the first row.

Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-D5: f1 to f15 and their colours (Handheld)

Settings: Float 8, Radian, page 1.1 (Document2), window x -7.5..22.5, y -40.0038784663631..440.0445287900329. Existing: f1 `x^2` (hidden), f2 `x^2` (red), scatter s1.
Keys per function: menu 3 1 (Function), type the expression, Return. After Return the entry bar closes, so each function needs menu 3 1 again. Each new function takes the next free number.
Entered: f3 `x+3`; f4 `100`; f5 `125`; f6 `150`; f7 `175`; f8 `200`; f9 `225`; f10 `250`; f11 `275`; f12 `300`; f13 `325`; f14 `350`; f15 `375` (constants chosen so the horizontal lines separate).

Colours seen (by eye from the screenshot, my colour names):
| Function | Colour |
|---|---|
| f1 | not seen (hidden in this run) |
| f2 | red |
| f3 | black |
| f4 | magenta |
| f5 | green |
| f6 | orange |
| f7 | brown |
| f8 | blue |
| f9 | red |
| f10 | black |
| f11 | magenta |
| f12 | green |
| f13 | orange |
| f14 | brown |
| f15 | blue |

So from f2 the colours repeat in a cycle of 7: red, black, magenta, green, orange, brown, blue. That f1 is blue is NOT observed; it would follow from the cycle only. The labels on the right of the graph are drawn in the same colour as their line (`f15(x)=375` blue ... `f5(x)=125` green); f2 `x^2` and f3 `x+3` labels also seen.
No limit or error appeared at f15; f16 was not tried.
Screenshots: `R6-D5-hh-f2-to-f15-colours.png` (full), `R6-D5-hh-f3-black-scaled0.6.jpg`, `R6-D5-hh-f4-to-f7-scaled0.6.jpg`, `R6-D5-hh-f8-to-f11-scaled0.6.jpg` (scaled 0.6, not full size).
Differs from CASSim or from this file's expectation? Not compared in this run.
Not done for D5: the Computer view; the colour of f1; the colours of the 15 numbered swatches vs these line colours (the swatch list is in D6).

## R6-D7: `nInt` graph draw time (Handheld)

Settings: Float 8, Radian, Document2. New Graphs page added with ctrl+i then 2 (Add Graphs); it became page 1.2 (the earlier Calculator page moved to 1.3). Window -10..10, y top 6.67, bottom -6.67.
Add-page menu (ctrl+i): 1 Add Calculator, 2 Add Graphs, 3 Add Geometry, 4 Add Lists & Spreadsheet, 5 Add Data & Statistics, 6 Add Notes, 7 Add Vernier DataQuest™, 8 Add Widget, 9 Add Program Editor ▶, A Add Python ▶.
First entry on the new Graphs page was labelled `f16(x)=` (numbering continued from f1 to f15 defined on page 1.1 in D5), not `f1`.
Keys: typed `nInt(sin(`, `t^2`, Right, `),t,0,x)` then Return. Entry shown as `f16(x)=nInt(sin(t²),t,0,x)`.

Observed:
- Screenshot straight after Return (call latency only): no curve yet, entry still shown.
- Next screenshot, 3 s wait plus call latency later: the full red curve is drawn (flat near 0 for x<0 on the left, rising to about 1 near x=1 then oscillating, with the label `f16(x)=nInt(sin(t²),t,0,x)`). So draw time is somewhere above 0 and roughly 3 to 5 s by this method; the clock was not precise, no stopwatch. The 5 s and 15 s screenshots were identical to the 3 s one.
- Redraw: Zoom – Standard (menu 4 5) on this page, then a click on page tab 1.1 at once. The first screenshot after the click still showed page 1.2 mid-draw: only a sparse set of red dots across x about 1 to 10 and none on the left half, so the curve is drawn progressively as separate points. The next screenshot (after clicking tab 1.2 again) showed page 1.1 (the tab click had applied late), and a screenshot 3 s later showed page 1.2 fully drawn.
- Whether the page can be left while it draws: a switch to 1.1 did happen and 1.2 was complete on return, but the screenshot timing does not show whether the draw was still running when the page changed. Not conclusive.

Screenshots (all scaled, not full size; `pages-shots-6/`): `R6-D7-hh-add-page-menu-scaled0.5.jpg`, `R6-D7-hh-new-graphs-page-f16-entry-scaled0.6.jpg`, `R6-D7-hh-nint-typed-before-return-scaled0.5.jpg`, `R6-D7-hh-nint-just-after-return-scaled0.4.jpg`, `R6-D7-hh-nint-drawn-3s-later-scaled0.4.jpg`, `R6-D7-hh-nint-redraw-after-zoom-standard-scaled0.4.jpg`, `R6-D7-hh-leave-page-click-1.1-scaled0.4.jpg`, `R6-D7-hh-back-on-1.2-drawn-scaled0.4.jpg`.
Differs from CASSim or from this file's expectation? Not compared in this run.

## Run on the emulator in this file (Handheld view only)
- R6-D1 (Handheld): axis drags x out/in and y out/in with Window Settings after each.
- R6-D2 (Handheld): Trace Right 1/2/10 and Left back; Trace Step Automatic.
- R6-D3: Zoom – Fit with `x^2` alone, scatter alone, and both together.
- R6-D4: each Graph Entry/Edit type opened (empty entry lines only).
- R6-D5: f2 to f15 colours (f1 not seen).
- R6-D6: Actions menu list, Attributes, Set Conditions (and its colour list), Coordinates and Equations, Calculate, Redefine (tool active only), Table menu and Edit Table Settings.
- R6-D7: `nInt` graph draw time (rough, by screenshots).

## Not run on the emulator
- R6-D1 Computer view (needs a Computer-page-size document).
- D4: typing into the entries; Equation Templates ▶; Computer view.
- D5: colour of f1; f16 and beyond.
- D6: Actions 2 Select ▶, 6 Delete all, 7 Text, B Insert Slider, C MathDraw; any effect of Coordinates and Equations, Calculate or Redefine (clicks gave no visible change); changing an attribute value with Left/Right.
- D7: a clean timing (no stopwatch) and a proof of leaving the page mid-draw.

## Also seen, not covered by a row
- Function numbering continues across pages in a Problem: a new Graphs page started at `f16`.
- Enter in the graph entry bar closes the bar; ctrl+G brings it back; the entry bar defaults to a blank scatter slot (s2) after a scatter exists.
- With the table pane focused, the menu key gives a short menu (1 Actions ▶, 2 Table ▶) instead of the Graphs menu.
- The Add-page menu list (see D7).
- Zoom – Fit with the scatter alone pads each axis 10% beyond the data range.


---
# RUN 6 per brief of 2026-11-23 (rows R6-A1 to R6-A14)

The sections above are from an earlier run that used the same file name and the old labels R6-D1 to R6-D7. They are kept as they were. Everything below is the run 6 brief's own Part A, written 2026-11-25.

Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, Keypad + SideScreen at 250%. Computer-use capture.
Settings (Document2, new): Document Settings opened on arrival. It came up Float 8, Radian, Normal, Rectangular, Auto, CAS On (Real or Complex was inherited as Rectangular, not the default). I changed Real or Complex to Real. Final: Float 8, Radian, Normal, Real, Auto, CAS On.
Page 1.1 Calculator (empty), page 1.2 Graphs. Functions: f1(x)=x^2, f2(x)=2*sin(x), f3(x)=x+1 (typed, Return).
Screenshots: pages-shots-6/R6-A*-hh-*.png. "hh" = Handheld view. Cropped to the handheld screen unless noted.

### R6-A1 (hh): drag an axis on a tick mark, 50 px out then 50 px in
Settings: as above. Graphs page 1.2, no functions yet. Menu 4 Window/Zoom > 5 Zoom – Standard, then Menu 4 1 Window Settings read after each drag, closed with Cancel.
Keys: mouse, left button dragged 50 screen pixels along the axis, starting on a tick mark (x axis: the tick at x=1; y axis: the tick at y=1, then a tick on the axis further out).
Observed:
| Step | XMin | XMax | XScale | YMin | YMax | YScale |
|---|---|---|---|---|---|---|
| After Zoom – Standard | -10 | 10 | Auto | -6.6666666666667 | 6.6666666666667 | Auto |
| x axis tick dragged 50 px outward (away from the origin) | -4.1842105263158 | 4.1842105263158 | Auto | -2.7894736842106 | 2.7894736842106 | Auto |
| x axis tick dragged 50 px inward (back toward the origin) | -8.8333333333334 | 8.8333333333334 | Auto | -5.8888888888889 | 5.8888888888889 | Auto |
| y axis tick dragged 50 px outward | -4.1842105263157 | 4.1842105263157 | Auto | -2.7894736842105 | 2.7894736842105 | Auto |
| y axis tick dragged 50 px inward | -7.9499999999999 | 7.9499999999999 | Auto | -5.2999999999999 | 5.2999999999999 | Auto |
Reading: a drag on EITHER axis changes BOTH x and y. It is a rescale about the origin, not a pan: the window stays centred on (0,0), and the ratio YMax/XMax stays 2/3 (the aspect of the plot area). Dragging a tick away from the origin makes the window smaller (zoom in); dragging it toward the origin makes it larger. The factor looks like the distance from the origin before the drag divided by the distance after it. Not checked at a start point off a tick or with a window that is not centred on the origin. The word "axes" appeared next to the axis while it was dragged. The last two values show a float tail of ...99999 (e.g. 7.9499999999999).
Screenshots: R6-A1-hh-window-standard-baseline.png, R6-A1-hh-x-axis-out-50px-window.png, R6-A1-hh-x-axis-in-50px-window.png, R6-A1-hh-y-axis-out-50px-window.png, R6-A1-hh-y-axis-in-50px-window.png (each shows the Window Settings dialog).
Computer view: NOT RUN (it needs a Computer-page-size document; see "Not run").
Differs from CASSim or from this file's expectation? Not compared in this run. The brief notes that run 5 saw the two views disagree.

### R6-A2 (hh): Graph Trace across three graphs
Settings: as above. f1, f2, f3 graphed in window x -7.95..7.95, y -5.3..5.3. Menu 5 Trace > 1 Graph Trace.
Trace submenu as shown: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▶, 5 Geometry Trace, 6 Erase Geometry Trace (grey).
Keys: keyboard arrows. Trace started on f1 at (0,0).
Observed (trace label at the bottom right, x at 0 throughout):
| Press | Trace is on | Label |
|---|---|---|
| (start) | f1 | f1: (0, 0) |
| Up once | f2 | f2: (0, 0) |
| Down (1st) | f1 | f1: (0, 0) |
| Down (2nd) | f3 | f3: (0, 1) |
| Down (3rd) | f2 | f2: (0, 0) |
So Down went f1 → f3 → f2 here, and Up from f1 went to f2, NOT to f3. A yellow tag appeared at the point: "zero" on f1 and f2 at (0,0), "y-intercept" on f3 at (0,1). All three of f1, f2 and f3 were at or near the point (0,0) or (0,1), so the order may depend on where the graphs sit at that x. I did not repeat it at another x.
Screenshots: R6-A2-hh-trace-submenu.png (half-scale full-window screenshot, not cropped), R6-A2-hh-trace-start-f1.png, R6-A2-hh-trace-up-once-f2.png, R6-A2-hh-trace-down1-f1.png, R6-A2-hh-trace-down2-f3.png, R6-A2-hh-trace-down3-f2.png.
Differs from CASSim? CASSim: "Up from f1 goes to f3, Down goes f1 → f2 → f3 → f1". Observed: Up from f1 goes to f2, and Down goes f2 → f1 → f3 → f2. CONTRADICTS CASSim at this x. (f1 and f2 are tied at y=0 here, so a second reading at another x would settle the rule.)

### R6-A3 (hh): Enter at a traced point, then Esc
Keys: from the trace on f2 (0,0): Right three times, then Return, then Escape.
Observed: after Right ×3 the trace was on f2 at (0.3, 0.591). Return left a black label near the point reading "(0.3, 0.591)" (round brackets, a comma and a space, no f2 prefix, no "x=" or "y="), and the trace marker stayed (still in trace mode, bottom-right label still f2: (0.3, 0.591)). Escape ended the trace: the bottom-right label went away and a small black dot stayed at the point, with the black label "(0.3, 0.591)" still drawn beside it.
Screenshots: R6-A3-hh-trace-right3-before-enter.png, R6-A3-hh-trace-after-enter-label.png, R6-A3-hh-trace-after-esc-point-stays.png.
Differs from CASSim? CASSim: not built. Observed behaviour is above.

### R6-A4 (hh): Zoom – Fit three ways
Settings: as above. Page 1.1 Calculator: `xs:={1,2,3,4,5,6,7,8}`, `ys:={2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1}` (shot: R6-A4-hh-setup-xs-ys-lists-page-1.1.png). New Graphs page (it came up as f4 because function numbering continues across pages: `x^2` was f4(x)). Scatter entered with Menu 3 Graph Entry/Edit > 6 Scatter Plot, X `xs`, Y `ys` (Tab between the fields).
Graph Entry/Edit submenu seen: 1 Function, 2 Relation, 3 Equation Templates ▶, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▶, 8 Diff Eq. The scatter entry line opened as `s1` with two empty fields `x←` and `y←` (an empty check box to the left).
Keys: Menu 4 Window / Zoom > A Zoom – Fit, then Menu 4 1 Window Settings to read, Cancel.
Observed:
| Case | Window before | XMin | XMax | YMin | YMax |
|---|---|---|---|---|---|
| `x^2` alone | x 0.3 to 8.7, y standard (−6.67 to 6.67) | 0.3 | 8.7 | -7.4706981642471 | 83.2576798067181 |
| scatter `xs`,`ys` alone | standard | 0.3 | 8.7 | 0.7 | 17.5 |
| both together (f4 and s1 on the page) | x 0.3 to 8.7 (the case-1 result) | -0.54 | 9.54 | -7.4706981642471 | 83.2576798067181 |
Reading: Fit keeps the x window for a function alone and pads the sampled y range by 10% of the range on each side: x² over 0.3..8.7 is 0.09 to 75.69 (range 75.6), 0.09−7.56 = −7.47, 75.69+7.56 = 83.26. For the scatter alone Fit CHANGES x: it set x to the data range padded by 10% (xs 1..8, range 7, pad 0.7 gives 0.3..8.7) and y to the data range padded by 10% (ys 2.1..16.1, range 14, pad 1.4 gives 0.7..17.5), whatever the window was before. With both, y was the function's fitted y (the scatter fits inside it) and x was -0.54..9.54, which is the 0.3..8.7 window padded again by 10% of its width (8.4 wide, 0.84 each side). I did not run the both case from a different starting x window, so whether the x pad comes from the scatter, from the previous window, or from the union is not settled.
Screenshots: R6-A4-hh-fit-x2-alone-before.png, -after-graph.png, -window.png; R6-A4-hh-fit-scatter-alone-graph.png, -window.png; R6-A4-hh-fit-both-after-graph.png, -window.png; R6-A4-hh-graph-entry-submenu-scatter.png (half-scale full window), R6-A4-hh-scatter-entry-empty.png.
Differs from CASSim? CASSim: "Fit keeps x and pads the sampled y range by 10%; the scatter case is not built." Confirmed for a function alone; the scatter case is now observed as above (Fit sets x as well as y, 10% pad each side).

### R6-A5 (hh): Zoom – Square
Zoom menu in full (scrolled to its end): 1 Window Settings…, 2 Zoom – Box, 3 Zoom – In, 4 Zoom – Out, 5 Zoom – Standard, 6 Zoom – Quadrant 1, 7 Zoom – User, 8 Zoom – Trig, 9 Zoom – Data, A Zoom – Fit, B Zoom – Square, C Zoom – Decimal. (Shot: R6-A5-hh-zoom-menu-scrolled-end.png, half-scale full window.)
Keys: Menu 4 5 (Standard), Menu 4 B, read Window Settings. Then Window Settings typed XMin 0, XMax 10, YMin 0, YMax 2, OK; Menu 4 B; read again.
Observed:
| Start | After Zoom – Square |
|---|---|
| Standard: x -10..10, y -6.6666666666667..6.6666666666667 | unchanged: x -10..10, y -6.6666666666667..6.6666666666667 |
| x 0..10, y 0..2 | XMin 0, XMax 10, YMin 0, YMax 6.6666666666667 |
Reading: Square keeps x and rescales y so the y range is 2/3 of the x range (the plot area aspect). From y 0..2 it kept YMin = 0 and moved YMax; so the scaling is about y = 0 (the x axis, which here is also YMin). It cannot be told apart from "keeps YMin" with this start. A start with the x axis inside the window (say y −1..3) would settle it; not run.
Screenshots: R6-A5-hh-square-from-standard-window.png, R6-A5-hh-window-x0-10-y0-2-typed.png, R6-A5-hh-square-from-x0-10-y0-2-graph.png, R6-A5-hh-square-from-x0-10-y0-2-window.png.
Differs from CASSim? CASSim (inferred): "keeps x and scales y about the x axis". Consistent with what was seen (not separable from keeping YMin).

### R6-A6 (hh): Zoom – In, Zoom – Out, the zoom pointer and its arrow step
Settings: as above. Graphs page with the scatter; each trial started from Zoom – Standard (x -10..10, y -6.6666666666667..6.6666666666667), then Menu 4 3 (Zoom – In) or Menu 4 4 (Zoom – Out), then the window read with Menu 4 1.
What the screen shows: Zoom – In shows a magnifier pointer with a yellow tag "Center?" beside it. The pointer STARTS where the mouse cursor last was over the graph (after Menu 4 3 it sat at the lower right where my last click had been), and it FOLLOWS the mouse. I could not put it on exactly (3,2) with the arrow keys alone, so I put the mouse at one screen point (1100,400) and read what graph point that was from the result. The brief's "(3, 2)" was therefore NOT used; the picked point was (2.7673, 2.2642).
Observed:
| Trial | XMin | XMax | YMin | YMax |
|---|---|---|---|---|
| Zoom – In, mouse at the point, Return | -2.2327044025157 | 7.7672955974843 | -1.0691823899371 | 5.5974842767296 |
| Zoom – In, the same point, by a click (no Return) | -2.2327044025157 | 7.7672955974843 | -1.0691823899371 | 5.5974842767296 |
| Zoom – In, the point then Right ×10, Return | -0.9748427672956 | 9.0251572327044 | -1.0691823899371 | 5.5974842767296 |
| Zoom – In, the point then Up ×10, Return | -2.2327044025157 | 7.7672955974843 | 0.188679245283 | 6.8553459119497 |
| Zoom – Out, the same point, Return | -17.232704402516 | 22.767295597484 | -11.069182389937 | 15.59748427673 |
Reading:
- Zoom – In halves both ranges (20 to 10 wide, 13.33 to 6.67 high) and puts the picked point at the CENTRE of the new window (centre x 2.7673, y 2.2642). Zoom – Out doubles both ranges (to 40 and 26.67) about the same point as the centre. Same factor 2 each time.
- A click on the graph in Zoom – In does the zoom at once; Return is not needed after a click.
- Arrow step of the pointer: Right ×10 moved the picked x by 1.2579 units, Up ×10 moved the picked y by 1.2578 units, so one press moves 0.12579 units on a 20-wide window = 1/159 of the plot width, the same distance in x and y. In handheld screen pixels that is 2 px per press (the plot is about 318 px wide). Earlier test: 5 Right and 3 Up moved the picked point by about (0.63, 0.38) units, consistent. Not checked: whether the step depends on the window width (it is a screen step, so it should scale with the units per pixel), or on holding a key down.
Screenshots: R6-A6-hh-zoom-in-pointer-center-prompt.png, R6-A6-hh-zoom-in-pointer-after-5right-3up.png, R6-A6-hh-zoom-in-after-enter-graph.png, R6-A6-hh-zoom-in-after-5right-3up-window.png, R6-A6-hh-zoom-in-no-key-window.png, R6-A6-hh-zoom-in-10right-window.png, R6-A6-hh-zoom-in-10up-window.png, R6-A6-hh-zoom-in-by-click-window.png, R6-A6-hh-zoom-out-window.png.
Differs from CASSim? CASSim: "halves or doubles the window about the chosen point": CONFIRMED (the chosen point becomes the centre). CASSim: "arrow step 1/80 of the plot": CONTRADICTED, it is about 1/159 of the plot width (2 handheld px), half of CASSim's step.

### R6-A7 (hh): Zoom – User after a Window Settings change, then after a Zoom – Box
Settings: as above. Graphs page with the scatter. Keys: Menu 4 5 (Standard); Menu 4 1, typed XMin -5, XMax 5, YMin -3, YMax 3, OK; Menu 4 3 (Zoom – In) and a click on the graph; Menu 4 7 (Zoom – User); then Menu 4 2 (Zoom – Box), a click for the first corner and a click for the second corner; Menu 4 7 again. The window was read with Menu 4 1 after each step.
Observed:
| Step | XMin | XMax | YMin | YMax |
|---|---|---|---|---|
| Window Settings typed and OK | -5 | 5 | -3 | 3 |
| After Zoom – In (click) | -1.1163522012579 | 3.8836477987421 | -0.4811320754717 | 2.5188679245283 |
| After Zoom – User | -1.1163522012579 | 3.8836477987421 | -0.4811320754717 | 2.5188679245283 |
| After Zoom – Box (two clicks) | 0.7389937106918 | 2.0754716981132 | 1.0471698113208 | 1.938679245283 |
| After Zoom – User | 0.7389937106918 | 2.0754716981132 | 1.0471698113208 | 1.938679245283 |
Reading: in both runs Zoom – User left the window exactly as it was; it did not go back to the typed window (-5..5, -3..3) and did not go back to the window before the box. I saw no message, no dialog and no pointer after pressing 7. So here Zoom – User behaves as a no-op, or it returns to a window that I never set in a way it recognises. Not tried: Zoom – User straight after opening the document, after a drag of the axes, or after Zoom – Standard (with the page's first window recorded some other way). Zoom – Box showed a yellow tag "2nd corner?" after the first click and a dotted rectangle that followed the mouse.
Screenshots: R6-A7-hh-window-settings-typed-x-5-5-y-3-3.png, R6-A7-hh-after-zoom-in-window.png, R6-A7-hh-zoom-user-after-zoom-in-window.png, R6-A7-hh-zoom-box-2nd-corner-prompt.png, R6-A7-hh-after-zoom-box-window.png, R6-A7-hh-zoom-user-after-zoom-box-window.png.
Differs from CASSim? The brief asks "which window User returns to": it returned to NO different window in these two cases (no change).

## R6-A8 Analyze Graph tools (Zero, Minimum, Intersection, dy/dx)

Settings: Radian, Automatic, Real, Float 8, Handheld. Page 1.4 of Document2: f5(x)=x², f6(x)=x+1, f8(x)=x²+1 visible (f7 hidden), Standard window.
Keys: Menu, 6 (Analyze Graph), then 1 Zero / 2 Minimum / 4 Intersection / 6 dy/dx. Bounds were set by mouse click, so they are approximate, not exact integers.

| Tool | Prompts seen, in order (verbatim) | Result |
|---|---|---|
| Zero on f8 (x²+1, no zero) | "graph?" then "lower bound?" then "upper bound?" | Error dialog "No zero found within the specified bounds", button OK. No point drawn. |
| Minimum on f5 (bounds about 0.94 and 3.0) | "graph?", "lower bound?", "upper bound?" | Yellow tag "minimum" appears, then a label "(0.943, 0.89)" at the LEFT BOUND (not at the vertex x=0, which is outside the bounds). Tab hint "label [tab]". |
| Intersection of f5 and f6 (bounds about 0.94 and 1.9) | "graph?", "2nd graph?", "lower bound?", "upper bound?" | Yellow tag "intersection", label "(1.62, 2.62)" |
| dy/dx on f5 at x=2 | "graph?", then "position?" (typed 2, Return) | Label "4" at the point on f5 |

Observed: while a tool waits for a graph, the hovered graph is drawn bold and a tag "graph f5" or "graph f6" with a [tab] hint follows the pointer. The Minimum label is the point found on the bound, to three significant figures after rounding display (0.943, 0.89).

Screenshots: pages-shots-6/R6-A8-hh-*.png (19 files).

Differs from CASSim? To check against the CASSim notes (not read in this run). Items for the reader: (1) Zero with no root gives an Error dialog with that exact text; (2) Minimum on a monotone stretch returns the bound point rather than "none"; (3) prompts are "graph?", "2nd graph?", "lower bound?", "upper bound?", "position?"; (4) labels show 3 significant figures ((1.62, 2.62), (0.943, 0.89)).
(TI text, do not reuse): the error message text above.

## R6-A9 Domain restriction and piecewise template

Settings: Radian, Automatic, Real, Float 8, Handheld. New Graphs page 1.5 of Document2.
Keys: ctrl+i, 2; typed `x^2`, Right (leave exponent), `|x>0`, Return. Then templates key (the key with the bracket icon at the right of the keypad, second row), chose the first piecewise icon, Return, typed `x+1`, Tab, `x<0`, Tab, `x^2`, Return.

Observed:
- Domain restriction: the entry bar showed `f9(x)=x²|x>0` while typing; after Return the label drawn on the graph is `f9(x)={x², x>0` (a brace with one row). The curve is drawn only for x>0, starting at the origin; nothing for x<0. The new page took the next free name, f9 (names run on across pages of the document: f4 to f8 were already used on other pages). The entry bar was hidden when the page opened; ctrl+g showed it.
- Piecewise template (two pieces): the template inserted is a brace with two rows and fields [expr1, cond1] and [expr2, cond2], where cond2 is drawn grey (optional). Tab moves field to field. With cond2 left empty the graph label reads `f10(x)={x+1, x<0 ; x², Else`, i.e. the second row is labelled "Else". Drawn: the line x+1 for x<0 and the parabola x² for x≥0, joined at x=0 (the line reaches 1 at x=0, the parabola starts at 0, so there is a visible jump; no marker for it).
- New function f10 was started as `f10(x)=` in the entry bar.

Screenshots: pages-shots-6/R6-A9-hh-*.png (6 files).

Differs from CASSim? For the reader to check: (1) domain restriction label has the brace form `{x², x>0`; (2) piecewise default second row is labelled "Else"; (3) new graph pages continue the function numbering (f9, f10).

## R6-A10 Where functions are drawn (domain edges)

Settings: Radian, Automatic, Real, Float 8, Handheld. New Graphs page 1.6 of Document2, Standard window. Each function typed in the entry bar (ctrl+g opens a new line), Return.

| Typed | Label shown | Drawn where | Message |
|---|---|---|---|
| `x^(1/3)` | f11(x)=x^(1/3) (fraction shown as a superscript 1 over 3) | Both sides of the y-axis: real cube root, negative branch below the axis for x<0, vertical tangent at the origin | none |
| `sqrt(x)` | f12(x)=√x | x ≥ 0 only, starts at the origin | none |
| `ln(x)` | f13(x)=ln(x) | x > 0 only, falls off the bottom of the screen near the y-axis | none |
| `1/sqrt(4-x^2` Right `)` | f14(x)=1/√(4−x²), drawn as a stacked fraction | Only between about x=−2 and x=2: a U shape with minimum 0.5 at x=0 and walls rising off the top near x=±2 | none |

Observed: no error or warning for any of the four; points outside the domain are simply not plotted. Function names continued from the earlier pages (f11 to f14).
`^` trap: `x^(1/3)` typed in one go gave the right power because the parentheses stay inside the exponent. For f14 the `^2` was left with Right before the closing `)`.

Screenshots: pages-shots-6/R6-A10-hh-*.png (5 files). The last one shows all four.

Differs from CASSim? For the reader to check: the real cube root is drawn for x<0 (x^(1/3) is not restricted to x≥0), and no domain message is shown.

## R6-A11 Colours of f1 to f10

Settings: Radian, Automatic, Real, Float 8, Handheld. New Problem (page 2.1, Graphs), Standard window. Entered ten parallel lines in order: f1=x-5, f2=x-4, f3=x-3, f4=x-2, f5=x-1, f6=x, f7=x+1, f8=x+2, f9=x+3, f10=x+4 (ctrl+g then type then Return for each).

| Function | Colour (as drawn) |
|---|---|
| f1 | blue |
| f2 | red |
| f3 | black |
| f4 | magenta |
| f5 | green |
| f6 | orange |
| f7 | brown |
| f8 | blue |
| f9 | red |
| f10 | black |

Observed: the cycle has length 7 and starts again with blue after brown. The latest entered function is drawn thick (selected) until the next entry. Labels of the top lines overlap on screen, so the colours of f8 to f10 were read from the lines themselves (the three lines above f7: blue, red, thick black). Cross-check from page 1.4 and later pages in Document2: f8 blue, f9 red, f10 black, f11 magenta, f12 green, f13 orange, f14 brown, the same cycle.

Screenshots: pages-shots-6/R6-A11-hh-f1-to-f4-colours.png, ...-f1-to-f7-colours.png, ...-f1-to-f10-colours.png.

Differs from CASSim? CASSim says the colours repeat after 7 with f8 blue and f9 red: CONFIRMED. f10 is black (same as f3).

## R6-A12 Graph Entry/Edit types and their entry lines

Settings: Radian, Automatic, Real, Float 8, Handheld. Page 2.1 (Graphs). Keys: Menu, 3 (Graph Entry/Edit), then the number below.

Submenu, in order (verbatim): 1 Function, 2 Relation, 3 Equation Templates ▸, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▸, 8 Diff Eq.
- 7 Sequence ▸ has: 1 Sequence, 2 Custom.
- 3 Equation Templates ▸ has (each with its own ▸): 1 Line, 2 Parabola, 3 Circle, 4 Ellipse, 5 Hyperbola, 6 Conic. (Inner leaves not opened in this run.)

| Type | Entry line as shown on opening |
|---|---|
| Relation | `rel1(x,y)` then a second blank input line below it |
| Parametric | `x1(t)=` / `y1(t)=` / `0≤t≤6.28  tstep=0.13` |
| Polar | `r1(θ)=` / `0≤θ≤6.28  θstep=0.13` |
| Scatter Plot | `s1` with `x←` and `y←` (seen in A4) |
| Sequence | `u1(n)=` / `Initial Terms:=` / `1≤n≤99  nstep=1` |
| Sequence, Custom | `p1` then `x←` / `y←` / `1≤n≤99  nstep=1` |
| Diff Eq | `y1' =` input box (checkbox, "..." button), under it `(x0,y10):  (<x>, <y>)` with grey placeholders and a small magnifier icon. A label `d1:` is cut off at the left edge. |

Observed: each new entry line starts with an empty checkbox. Parametric and Polar defaults are 0 to 6.28 (2π, two decimals), step 0.13. Sequence defaults n 1 to 99, step 1.

Screenshots: pages-shots-6/R6-A12-hh-*.png (9 files; Scatter Plot is in the A4 set).

Differs from CASSim? To check against CASSim: Parametric/Polar defaults, Sequence defaults, the Diff Eq `(x0,y10)` placeholder line.

## R6-A13 Actions leaves, ctrl+T and Table settings

Settings: Radian, Automatic, Real, Float 8, Handheld. Page 2.1 (Graphs), ten lines f1 to f10, Standard window. A leaf is picked with Menu, 1 (Actions), then its number or letter. Mouse clicks on a drawn line (f5) were used to choose the graph.

Actions submenu as drawn (labels cut off at the right of the handheld screen, a scroll arrow at the foot): 1 Pointer, 2 Select, 3 Hide/Show, 4 Attributes, 5 Set Conditi…, 6 Delete all, 7 Text, 8 Coordinate…, 9 Calculate, A Redefine.

| Leaf | What appears |
|---|---|
| 3 Hide/Show | A blue eye icon at the top-left of the graph area. No text prompt. (The click that I tried on a line did not visibly change anything; not confirmed.) |
| 4 Attributes | An attribute-grid icon at the top-left. After clicking f5 a tag "graph f5 [tab]" and a vertical attribute palette open beside the pointer. Items, as the yellow tip reads for each (Down arrow steps): "(1/3) Line weight is thin", "(1/3) Line style is continuous", "(3/5) label style", "(1/2) Label parameters: Show names", "(1/2) Graph is continuous". Escape closes the palette; the Attributes mode stays active. |
| 5 Set Conditions | After clicking f5, dialog titled "Conditional Attributes" with fields "Show When:" (focused, empty), "Line Color:" and "Fill Color:" (both showing the grey text "<Enter expression>"), a "Colors..." button, then OK and Cancel. Cancel used. |
| 6 Delete all | Not run (it would delete the page's work). |
| 8 Coordinates and Equations | An icon "y=f(x)" at the top-left. Clicking f5 (twice) showed no label in this run. |
| 9 Calculate | An "a+b" icon at the top-left. No prompt text. Not applied to anything (it needs a text or number object). |
| A Redefine | A small point-and-arrow icon at the top-left. Clicking f5 showed nothing. |
| 7 Text, 1 Pointer, 2 Select | Not run. |

ctrl+T (table):
- Opens a split screen: graph on the left (labels now drawn at the left of the plot), table on the right. Columns "x" and "f1(x):=" with its expression "x-5" under the heading and a dropdown arrow. The cursor sits on the f1 cell of the row x=1 (value -4.); the rows above it exist: scrolling up with Up showed x=0. (-5.), then x=-1. (-6.), x=-2. (-7.). So the table can be scrolled to negative x even though the Table Start is 0.
- Menu, 2 Table shows: 1 Remove Table (Ctrl+T), 2 Delete Column, 3 Choose..., 4 Edit Expression, 5 Edit Table Settings...
- Edit Table Settings dialog "Table": "Table Start:" 0. (selected), "Table Step:" 1.0, "Independent:" Auto (drop-down), "Dependent:" Auto (drop-down), OK, Cancel. Cancel used.
- ctrl+T again removes the table pane and the full graph comes back at once, window unchanged.

Screenshots: pages-shots-6/R6-A13-hh-*.png (15 files).
(TI text, do not reuse): the dialog titles and field names above are TI's wording.

Differs from CASSim? To check against CASSim: table first x (0, step 1.0), the five attribute items and their yellow tips, the Conditional Attributes fields, and that ctrl+T closes the pane without changing the window.

## R6-A14 nInt(sin(t²),t,0,x) draw time

Settings: Radian, Automatic, Real, Float 8, Handheld. New Graphs page 2.2, Standard window. Typed `nInt(sin(t^2`, Right (leave the exponent), `),t,0,x)`, Return. (The function took the next free name f11, not f4; the expression is the one in the brief.) Entry bar showed `f11(x)=nInt(sin(t²),t,0,x)`.

Observed:
- After Return the curve is built up in passes: the first pass puts widely spaced dots (about 10 to 20 dots across the screen), then each pass adds points. It looked like dots at about 1 s and still sparse dots at about 2 s after Return (screenshot times are approximate, each zoom takes about 1 s).
- Fully drawn as a smooth line about 5 to 6 s after Return (a Fresnel-type curve: oscillations that settle to about 0.63 for x>0 and about -0.63 for x<0; the display shows about 0.6 on the right and -0.6 on the left; read from the picture, not measured).
- Zoom out (Menu, 4, 4, click on the origin) restarted the drawing: after the click only 4 or 5 dots were present; complete after about 2 s on return.
- Leaving the page while it draws: a click on the 2.1 tab straight after the zoom-out worked at once (page 2.1 showed); no wait, no message. Returning to 2.2 two seconds later showed the curve already fully drawn, and it stayed the same 5 s later.

Screenshots: pages-shots-6/R6-A14-hh-*.png (7 files).

Differs from CASSim? To check: whether CASSim draws progressively, and that the page can be left at any time.

## RUN 6 Part A: lists (rows R6-A1 to R6-A14)

**Run on the emulator:** R6-A1 (Handheld view only), A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13 (see the table for the leaves actually opened), A14.

**Not run (with the reason):**
- R6-A1 Computer view: needs a Computer-page-size document; not made in this run.
- R6-A8: Zero was tried only on f8 (no root, error), not on a function with a root; Maximum, Inflection, Bounded Area, Integral and Analyze Conics were not opened.
- R6-A12: the inner leaves of Equation Templates (Line, Parabola, Circle, Ellipse, Hyperbola, Conic) were not opened; Scatter Plot is in A4.
- R6-A13: 1 Pointer, 2 Select, 6 Delete all and 7 Text were not run; Hide/Show, Coordinates and Equations, Calculate and Redefine only showed their mode icon (clicking f5 gave no visible effect).
- Part A was interrupted several times when other windows (File Explorer, a terminal) came in front of the emulator; the rows above were redone or finished afterwards.

**Also seen, not covered:**
- Documents 1 and 3 and 4 are not mine. Function names continue across the pages of a Problem (f9, f10 ... f14) and restart in a new Problem (f1 on page 2.1).
- The Actions menu labels are truncated at the right edge on the Handheld screen.
- Table: the rows above Table Start (x<0) can be scrolled to.
