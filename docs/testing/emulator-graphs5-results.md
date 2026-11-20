# Emulator check 6, run 5, Part 1: Graphs (results so far)

Observations only. Software: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view (Keypad + SideScreen, 250% zoom). Screenshots are in `pages-shots-6/`, named `R5-<row>-<name>.png`, cropped to the handheld screen.

Document: new Handheld-size document (Document3), then saved as `R5-test.tns`. Document Settings checked first: Display Digits Float 8, Angle Radian, Exponential Format Normal, Real or Complex Real, Calculation Mode Auto, CAS Mode On (screenshot R5-D34-settings-part1.png). Run 4's Document1 and Document2 were closed with No at the "Save Document" prompt (there was no Document3 left open).
Page 1.1 Calculator: `xs`, `ys`, `d1`, `d2`, `cat` defined (typed `xs:={1,2,3,4,5,6,7,8}` and so on; `cat` typed as `"a`, Right, `,"b`, Right ...). All five echoed correctly.
Page 1.2 Graphs: `f1(x)=x^2` typed with Right to leave the exponent, `f2(x)=sin(x)`.

Computer-use caveat: the mouse wheel and drags were sent by the computer-use tool, not by a physical mouse. The wheel did nothing (below); that matches run 4 (emulator-graphs4-results.md, "Mouse wheel scroll up over the graph: no zoom or pan"), so it may be a limit of how the wheel is delivered rather than of the emulator.

## R5-D34: mouse wheel zoom
Settings: as above, window Standard.
Keys: mouse: pointer at about (3, 2) on screen (pixel (1064,411)), one notch up, then one notch down; then pointer at the origin (951,486), one notch up and one down. Window read from Menu > 4 > 1 Window Settings.
Observed:
- Baseline Window Settings: XMin `-10`, XMax `10`, XScale `Auto`, YMin `-6.6666666666667`, YMax `6.6666666666667`, YScale `Auto`.
- After one notch in at (3, 2): unchanged (same six values). The graph did not move or rescale. A small tab-shaped hint "label" appeared next to the f1 label because the pointer was over it.
- After one notch out at (3, 2): unchanged.
- After one notch in and one out at the origin: unchanged.
- Does the point under the pointer stay fixed? Not testable: nothing changed. Zoom factor per notch: none seen.
Screenshot: pages-shots-6/R5-D34-0-baseline-window.png, R5-D34-a-wheel-in-at-3-2-graph.png, R5-D34-b-wheel-in-at-3-2-window.png, R5-D34-c-wheel-out-at-3-2-graph.png, R5-D34-d-wheel-out-at-3-2-window.png, R5-D34-e-wheel-in-out-at-origin-window.png
Differs from CASSim or from this file's expectation? Not known. The expectation (a wheel zoom about the pointer) was not seen; same as run 4.

## R5-D35: drag on empty space, drag on an axis tick label
Keys: mouse: drag on empty space from (800,640) to (850,670), i.e. 50 px right and 30 px down; then drag from the x-axis tick label `1` (1036,540) to (1086,540), 50 px right.
Observed:
- Window before: XMin -10, XMax 10, YMin -6.6666666666667, YMax 6.6666666666667.
- Window after the empty-space drag: XMin `-11.3207547169811`, XMax `8.6792452830189`, YMin `-5.8490566037736`, YMax `7.4842767295597`; scales still `Auto`. So the width stayed 20 and the height stayed 13.3333. The window moved 1.3207547 units left in x and 0.8176 units up in y: the graph followed the pointer (content moved right and down), x at 757 screen px per 20 units (0.026415 units per px; 50 px gives 1.3208 exactly). For y the shift corresponds to about 31 px, not 30 (by the same 0.026415 units per px); not explained. The axis end values on screen read `-11.32` and `8.68`, `7.48` and `-5.85`.
- Drag on the tick label `1`: the window values were identical to those after the first drag (XMin -11.3207547169811, XMax 8.6792452830189, YMin -5.8490566037736, YMax 7.4842767295597). No rescale of either axis and no pan.
- Does the graph follow the pointer one to one? Yes for the empty-space drag (x exactly; y within about 1 px). Does the axis drag rescale only that axis? Not seen: the drag on the tick label had no effect (the drag may have missed the axis hot area; only the label was tried, as the row asks).
Screenshot: R5-D35-a-after-empty-drag-graph.png, R5-D35-b-after-empty-drag-window.png, R5-D35-c-after-axis-label-drag-graph.png, R5-D35-d-after-axis-label-drag-window.png
Differs from CASSim or from this file's expectation? Not known. Empty-space drag matches emulator-graphs2-results.md (pans without changing the width).

## R5-I1: Dot Grid, Hide Axes, Hide Axes End Values, persistence
Keys: Menu > 2 View (listed below), 6 Grid > 2 Dot Grid; Hide Axes; Hide Axes End Values; ctrl+Left to page 1.1 and ctrl+Right back; ctrl+I > 2 Graphs for a second Graphs page (same Problem); Insert > Problem then Add Graphs (new Problem); ctrl+S; close; ctrl+O.
Observed:
- Menu > 2 View on a Graphs page (page 1.2), numbers and labels, grey marked:
  - 1 Graphing (grey)
  - 2 Plane Geometry
  - 3 3D Graphing
  - 4 Hide Analytic Window (grey)
  - 5 Hide Axes
  - 6 Grid ▶ : 1 No Grid (grey while no grid is set), 2 Dot Grid, 3 Lined Grid
  - 7 Show Entry Line (Ctrl+G)
  - 8 Hide Axes End Values
  - 9 Hide Object Selection Guides
- After Hide Axes the item 5 reads `Show Axes` and item 8 `Hide Axes End Values` is **grey**. So the three settings cannot be set in the order the row gives. I set them as Dot Grid, then (axes shown) Hide Axes End Values, then Hide Axes. The result: dots on a regular grid, no axes, no axis numbers or end values.
- Switch to page 1.1 and back: all three settings kept (page 1.2 looked the same).
- Second Graphs page in the same Problem (page 1.3): axes shown, end values shown (`-10`, `10`, `6.67`, `-6.67`), no grid. It did not inherit any of the three. Its first function was named `f7(x)=x^2` (f1 to f6 exist in the Problem) and drawn in a brown / dark orange.
- Graphs page in a new Problem (page 2.1): axes shown, end values shown, no grid; its function was `f1(x)=x^2` in blue (a new Problem restarts the names and colours).
- Save: ctrl+S opened "Save TI-Nspire™ Document" with "Save In: Users" (C:\Users) as the default folder. Saving `R5-test` there gave an error dialog: "This document cannot be saved because the folder is read-only: C:\Users" (screenshot R5-I1-g). I therefore saved to `C:\dev\CASSim-capture\R5-test.tns` (typed the full path in the File Name box). This is a **deviation from the row** (the default folder was not usable). The title bar then read `R5-test`.
- Closed the document (no prompt) and reopened it with ctrl+O (the Open dialog started in CASSim-capture, the last folder). It opened on page 1.1. Page 1.2: Dot Grid, hidden axes and hidden end values all kept, and the shifted window from D35 (end values not shown, so only seen from the shifted curves) was kept. Page 1.3 and page 2.1: still the defaults (axes, end values, no grid).
Screenshot: R5-I1-a-view-menu-axes-hidden-endvalues-grey.png, R5-I1-b-dotgrid-noaxes-noendvalues-set.png, R5-I1-c-page-1-1-after-switch.png, R5-I1-d-back-on-1-2-settings-kept.png, R5-I1-e-second-graphs-page-1-3-defaults.png, R5-I1-f-new-problem-graphs-page-2-1-defaults.png, R5-I1-g-save-default-folder-readonly-error.png, R5-I1-h-reopened-page-1-1.png, R5-I1-i-reopened-page-1-2-settings-kept.png, R5-I1-j-reopened-page-1-3-defaults.png, R5-I1-k-reopened-page-2-1-defaults.png
Differs from CASSim or from this file's expectation? Matches the to-do note (settings stored per Graphs page, new pages default to visible axes and no grid). New: Hide Axes End Values is grey once axes are hidden; the default save folder is read-only.

## R5-D36: default colour, label position and label colour for f1 to f6
Keys: keyboard: ctrl+G opens the entry line on the next free slot (f3 after f1 and f2); typed `x+1`, `2x`, `cos(x)`, `abs(x)`, each with Return. (With only f1 defined, ctrl+G opened f2; Down from there went to f3 and Up came back to f2.)
Observed (Standard window shifted by D35, so labels are at the right of the screen):
| Function | Default colour (in words) | Label | Label colour |
|---|---|---|---|
| f1(x)=x² | blue | `f1(x)=x²`, to the right of the curve at upper right | blue; `f1` bold, the rest regular weight |
| f2(x)=sin(x) | red | `f2(x)=sin(x)` to the right of the curve near the origin | red |
| f3(x)=x+1 | black | `f3(x)=x+1`, above and right of the line | black |
| f4(x)=2·x | magenta (pink-purple) | `f4(x)=2·x` at the top right, overlapping the f1 label | magenta |
| f5(x)=cos(x) | green (dark) | `f5(x)=cos(x)` below the curve at the bottom right | green |
| f6(x)=\|x\| | orange | `f6(x)=\|x\|` right of the line | orange |
| f7(x)=x² (page 1.3) | brown / dark orange | `f7(x)=x²` to the right of the curve | the same brown |
Each label is drawn in its graph's colour; the labels overlap when the curves are close (f1 and f4). The thick lines on the page are the selected graph or the last one entered, thin lines the rest.
Screenshot: R5-D36-f1-f6-colours-labels.png
Differs from CASSim or from this file's expectation? Not known.

## D12 (rest): 1/(x-1)^2, abs(x)/x, sqrt(x)
Settings: Radian, Automatic, Real, Float 8; each on its own new Graphs page of Problem 2 (pages 2.2, 2.3, 2.4), Standard window `-10..10`, `-6.67..6.67`, entry typed `1/(x-1)`, `^2`, Right; `abs(x)/x`; `sqrt(x)`.
Observed:
- `1/(x-1)^2` (f2, red, thick): two branches, the left rising to the top of the screen just left of x = 1 and the right one coming down from the top just right of x = 1. **No line is drawn across x = 1**: there is a gap at the top edge. The label is typeset as a stacked fraction with `(x-1)²` in the denominator.
- `abs(x)/x` (f3, black): a horizontal line at y = -1 for x < 0 and one at y = 1 for x > 0, ending at x = 0 with no vertical join and no open or closed circles; nothing is drawn at x = 0. The label is `|x|` over `x`.
- `sqrt(x)` (f4, magenta): starts at the origin and rises to the right; nothing is drawn for x < 0 and there is no end marker. The label reads `f4(x)=√x`.
Screenshot: R5-D12-a-1-over-x-minus-1-squared.png, R5-D12-b-abs-x-over-x.png, R5-D12-c-sqrt-x.png
Differs from CASSim or from this file's expectation? Not known.

## D6: `f1` back on the Calculator page, both ways
Settings: as above; Problem 2 holds f1 = x^2 (page 2.1), f2 = 1/(x-1)^2, f3 = abs(x)/x, f4 = sqrt(x); a Calculator page 2.5 was added with ctrl+I, 1.
Observed: `f1(2)` gives `4`; `f2(3)` gives `1/4` (stacked fraction); `f4(4)` gives `2`; `f1(x)` gives `x²`. Then on the Calculator `f4(x):=x^3` (typed `f4(x):=x`, `^3`, Right) gave `Done`, and back on page 2.4 the graph of f4 had changed to a cubic (label `f4(x)=x³`, magenta). So a Problem's function variables are shared in both directions.
Screenshot: R5-D6-a-f-values-on-calculator.png, R5-D6-b-calculator-redefine-f4-updates-graph.png
Differs from CASSim or from this file's expectation? No: this matches emulator-graphs2-results.md (D6, which had no PNG).

## D29: scatter plot of xs, ys with a function; Zoom - Data then Zoom - Fit
Settings: Problem 1, new Graphs page 1.4 (ctrl+I after page 1.3), Standard window. Menu 3 > 6 Scatter Plot: typed `xs`, Tab, `ys`, Return. Menu 3 > 1 Function: `x^2` (it was named `f8`, since f1 to f7 exist in Problem 1, so "f1" of the row is `f8` here). Menu 4 > 9 Zoom - Data, window read from Menu 4 > 1; then Menu 4 > A Zoom - Fit, window read the same way.
Observed:
- Scatter: only three points are visible in the Standard window, at about (1, 2.1), (2, 3.9) and (3, 6.2); the label is `(xs,ys)` in blue (not `s1`).
- After Zoom - Data: XMin `0.3`, XMax `8.7`, YMin `0.7`, YMax `17.5`, both scales `Auto`. All eight points are in view; the parabola `f8` is cut off at the top of the screen. (The x range is the data range 1 to 8 plus 0.7 each side, the y range 2.1 to 16.1 plus 1.4 each side, i.e. 10% of each range.)
- After Zoom - Fit: XMin `-0.54`, XMax `9.54`, YMin `-7.4335950025186`, YMax `82.8495450277046`, scales `Auto`. The whole parabola up to x = 9.54 and the eight points are in view, the points squashed along the bottom.
Screenshot: R5-D29-a-scatter-xs-ys-standard-window.png, R5-D29-b-after-zoom-data.png, R5-D29-c-zoom-data-window-settings.png, R5-D29-d-after-zoom-fit.png, R5-D29-e-zoom-fit-window-settings.png
Differs from CASSim or from this file's expectation? Not known.

## Not run in Part 1
The rest of D4 (double click, drag on an axis, ctrl+arrows, ctrl+Z; the wheel was done in D34), the rest of D11 (Left and Right at the screen edge, Trace Step dialog, Trace All), D32, D33, D22, D31, D23, H12 and D28 (H12 and D28 are partly in emulator-graphs3-results.md; the brief's remaining parts were not rerun).

## Lists
Run: R5-D34, R5-D35 (empty-space drag and tick-label drag), R5-I1, R5-D36, D12 (rest), D6, D29.
Not run (reason: not reached in this session, nothing was blocked): the rows under "Not run in Part 1".
Also seen, not covered: with only f1 defined, ctrl+G opened the entry line on f2 and Down went on to the empty slot f3 (Up came back to f2); a small tab-shaped `label` hint appears when the pointer rests on a graph label; the Open dialog starts in the last folder used (CASSim-capture) while the Save dialog starts in C:\Users (read-only); a second function entered on a page whose Problem already has f1 to f7 is named `f8` and drawn in the 8th colour.

## Computer view (Page Size: Computer) - Graphs rows

Document6 page 1.3 (Graphs added with ctrl+i then "2:Add Graphs"). Settings checked earlier in this document: Radian, Automatic, Real, Float 8. f1(x)=x², f2(x)=sin(x). The on-screen menu key does not open menus in this document; the right-click context menus do, and reach Trace, Analyze Graph and Table. Window values are read from the axis end labels (no Window Settings dialog, so no exact window dialog values).

### R5-D2 (Computer view) right-click menus
- Right-click on the f2 label: 1 Recent ▶, 2 Hide, 3 Delete, 4 Calculate (grey), 5 Convert to geometric (grey), 6 Pin, 7 Attach, 8 Detach (grey), 9 Color ▶, A Conditions…. The label is highlighted and shows "label" with a tab chip.
- Right-click on empty space: 1 Recent ▶, 2 Hide/Show ▶, 3 Select ▶, 4 Window / Zoom ▶, 5 Text, 6 Delete all, 7 Erase Geometry Trace (grey), 8 Pin.
- Right-click on the f2 curve: 1 Recent ▶, 2 Label (grey), 3 Attributes, 4 Hide, 5 Delete, 6 Edit Relation, 7 Trace ▶, 8 Analyze Graph ▶, 9 Table ▶, A Pin, B Color ▶, C Conditions…. Analyze Graph ▶: 1 Zero, 2 Minimum, 3 Maximum, 4 Intersection, 5 Inflection, 6 dy/dx, 7 Integral, 8 Bounded Area, 9 Analyze Conics (grey).
- Screenshot: pages-shots-6/R5-D2-computer-curve-context-menu.png (the label and empty-space menus were seen on screen but the PNG crops were bad and deleted).
- Differs? Not compared.

### R5-D34 (Computer view) mouse wheel
- Keys: wheel one notch up, then one notch down, pointer at about (1100,300).
- Observed: no zoom and no pan either way; a "label" text hint appeared near the top right of the graph (it stayed after the wheel). Window stayed x -10..10, y -6.66..6.66.
- Screenshot: pages-shots-6/R5-D34-computer-wheel-up-no-zoom.png. The zoom factor per notch cannot be given: no change.

### R5-D4 (Computer view) drags, ctrl+Z, double click
- Drag on empty space 50 px right, 30 px down: window x -10..10 became -11.14..8.86, y -6.66..6.66 became -5.96..7.35 (graph follows the pointer, both axes; one drag, whole graph moved).
- Then drag on the x axis 100 px right: x -11.14..8.86 became -13.36..6.64; y stayed -5.96..7.35 (x only moved).
- ctrl+Z: back to x -11.14..8.86 (undid the axis drag only; the first drag stayed).
- Double click on the integral label (not on the curve): label went into edit with "integral" and a tab chip.
- ctrl+Right after clicking empty space: no visible change.
- Screenshots: R5-D4-computer-drag-empty-space.png, R5-D4-computer-drag-axis.png, R5-D4-computer-ctrlz-after-drag.png.

### R5-D32 (Computer view) Analyze Graph results kept
- Brief says change f1; I analysed f2 (sin x) because f1=x² has no maximum. Deviation noted.
- Zero: right-click curve, 8 Analyze Graph, 1 Zero; prompts "lower bound?" (dotted vertical line follows the pointer), click to set, then "upper bound?"; result (0,0) marked with a dot and a label (0,0).
- Maximum (3): bounds clicked; result label (1.57,1).
- Change on the Calculator page: f2(x):=cos(x) (typed `f2(x):=cos(x)`). On the graph: f2 became cos; the two marked points were not shown at (0,0) and (1.57,1) any more; a single dot with label (0.777,0.713) appeared on the cos curve (cos 0.777 = 0.713).
- Changed again to f2(x):=2*sin(x) (typed `f2(x):=2*sin(x)`): the zero at (0,0) and a maximum labelled (1.57,2) were displayed again, so marked points follow the function and are recomputed.
- A stray "label" text appeared at the top right after my first click on the curve prompt (see D34).
- Screenshots: R5-D32-computer-zero-max-marked.png, R5-D32-computer-after-f2-changed.png.

### R5-D33 (Computer view) Integral
- Keys: right-click curve, 8 Analyze Graph, 7 Integral; typed `0` Return (lower), `2` Return (upper). f2 = cos x at that moment.
- Observed: grey shading between the curve and the x axis from x=0 to about 2 (below the axis past π/2), label near the point shows 0.909 (overlapping the stale point label), end dots on the axis at 0 and 2.
- After f2:=2*sin(x): shading remained from 0 to 2 and the label read 2.83 (overlapping "(1.57,2)").
- Screenshots: R5-D33-computer-integral-0-2.png, R5-D33-computer-after-f2-2sin.png.
- Differs? Not compared.

### R5-D11 (Computer view) Trace
- Keys: right-click the f2 curve, 7 Trace ▶. Submenu: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot, 5 Path Setup….
- 3 Trace Step…: dialog "Trace Step", one drop-down "Trace Step:" default Automatic; choices Automatic, Enter Value…; OK, Cancel. I pressed Cancel.
- 2 Trace All: thick vertical line through the graphs at x about 4.71 (the point where I had right-clicked), red dot on f2 with readout `f2: (4.71, -2)` at the bottom right of the window, an open circle on the x axis, a small trace icon at the top left of the page. Right arrow x5: readout `f2: (6, -0.559)` (a step of about 0.26 per press, Automatic).
- Right arrow x100 more: the window panned with the trace point. Axis labels became about 2.83 (left, overlapped by the f2 label) and 36.2 (right); readout `f2: (36, -1.98)`. So Right at the screen edge pans the window.
- Left at the left edge, Up and Down between graphs, Graph Trace (item 1) not run in Computer view.
- Screenshots: R5-D11-computer-trace-submenu.png, R5-D11-computer-trace-step-dialog.png, R5-D11-computer-trace-all-start.png, R5-D11-computer-trace-right-edge-pans.png.

### R5-H12 (Computer view) ctrl+T table split
- Keys: click the status bar, ctrl+T.
- Observed: page split about half and half, graph on the left, table on the right with a teal border (table focused). Columns: `x` (rows 1., 2., 3. ...), `f1(x):=` with `x^2` and `f2(x):=` with `2*sin(x)` (each with a drop-down arrow), a vertical scroll bar and a formula line at the bottom showing `1.`. Row 1 values: 1., 1.682942; row 2: 4., 1.81859…; row 3: 9., 0.28224…. First data cell selected.
- Right-click inside the table gave no context menu on screen.
- ctrl+T again: table pane closed, graph back to the full page.
- Menu in each pane and the Page Layout check: not run (no on-screen menu key in Computer view).
- Screenshot: R5-H12-computer-ctrl-t-table-split.png.

### R5-D22 (Computer view) entry-line types
- Not reachable. The Menu 3 Graph Entry/Edit list needs the on-screen menu key, which does nothing in the Computer-size document. The entry line's icon at the top right is a History Menu (tooltip "History Menu"; clicking it lists the existing functions `1:f1`, `2:f2`), not an entry-type list. The right-click menus contain no entry types. Handheld result for D22 stays in emulator-graphs2-results.md (labels seen; Equation Templates not entered).
- Screenshot: none for the History icon (seen on screen only).

### R5-D23 (Computer view) page and window right-click menus (labels only)
- Empty-space menu, item 2 Hide/Show ▶: 1 Hide Selection (grey), 2 Hide Grid (grey), 3 Show Dot Grid, 4 Show Lined Grid, 5 Show Entry Line.
- Item 3 Select ▶: 1 Region, 2 Image (grey), 3 Grid (grey).
- Item 4 Window / Zoom ▶: 1 Window Settings…, 2 Zoom - Box, 3 Zoom - In, 4 Zoom - Out, 5 Zoom - Standard, 6 Zoom - Quadrant 1, 7 Zoom - User, 8 Zoom - Trig, 9 Zoom - Data, A Zoom - Fit, B Zoom - Square, C Zoom - Decimal.
- Item 5 Text: the menu closed with no visible change (a text box probably needs a click on the page; not followed up). Items 6 Delete all and A Redefine not run (a Delete all would remove the page content).
- Screenshots: R5-D23-computer-hide-show-submenu.png, R5-D23-computer-select-submenu.png, R5-D23-computer-window-zoom-submenu.png.

### R5-D35 (Computer view) Window Settings dialog (extra)
- Window / Zoom ▶ 1 Window Settings… opens a dialog: XMin, XMax, XScale (drop-down, Auto), YMin, YMax, YScale (drop-down, Auto), OK, Cancel. At that moment (after the trace panned the window): XMin 16.2, XMax 36.2, YMin -5.958795562599, YMax 7.3534072900158. YMin/YMax show full digits (not Float 8).
- Screenshot: R5-D35-computer-window-settings-dialog.png. Pressed Cancel.

### R5-D31 (Computer view) slow function `f3(x)=nInt(sin(t^2),t,0,x)`
- Keys: ctrl+G; typed `nInt(sin(`, `t^2`, Right, `),t,0,x)`; Return. Window x about 2.83..36.2 (after the trace pan), y -5.96..7.35.
- Observed: no graph straight after Return. After about 3 s only a few dots are on screen (spaced about 110 px). After about 13 s a dense dotted line has been filled in from the left to about the middle of the page. After about 33 s the dotted line spans the whole window at a height of about 0.9 (thick, mostly dots). No busy mark or hourglass was visible in the page area in these shots. I did not leave the page while it drew.
- Screenshots: R5-D31-computer-nint-after-3s.png, R5-D31-computer-nint-after-30s.png.

## Handheld view (Page Size: Handheld) - rows captured later in the run

Settings for all rows below: Document7, Handheld page size, page 1.2 Graphs, f1(x)=x^2, f2(x)=2*sin(x), RAD / Automatic / Real / Float 8.
Values are in the screenshots; this file records only what was noted while at the screen. Nothing here is claimed as simulator-verified.

### R5-D32 handheld - Analyze Graph points are live
Keys: Menu > Analyze Graph > Zero (click curve, then bounds), then Maximum; then edited f2 to a cosine.
Observed: points stay marked after being placed; after f2 was changed the marked points moved with the new function (they follow the function definition).
Screenshots: R5-D32-zero-graph-prompt, R5-D32-zero-marked, R5-D32-zero-and-max-marked, R5-D32-after-f2-cos.
Differs from CASSim or from this file's expectation? Not compared in this pass. Computer-view result is in the section above.

### R5-D33 handheld - Integral stays live
Keys: Menu > Analyze Graph > Integral, lower bound 0, upper bound 2 on f1; then f2 changed to 2*sin(x).
Observed: bound prompt shown, shaded region and value label drawn, label updated after f2 was changed (see screenshots for the numbers).
Screenshots: R5-D33-lower-bound-prompt, R5-D33-integral-0-2, R5-D33-after-f2-2sin.
Differs? Not compared in this pass.

### R5-D11 handheld - Trace
Keys: Menu > Trace submenu; Trace Step...; Trace All.
Observed: Trace submenu listing (see screenshot); Trace Step dialog opens with Automatic as the default and an "Enter Value..." choice; Return does not close the dialog (ctrl+A, type value, click OK); with step 1, three Right presses move the trace point; at the right and left edges the window pans; Trace All with step 1 moves both traces.
Screenshots: R5-D11-trace-submenu, R5-D11-trace-step-dialog, R5-D11-trace-step-dropdown, R5-D11-trace-step-1-three-rights, R5-D11-trace-right-edge-pans, R5-D11-trace-left-pans, R5-D11-trace-all-step1-three-rights.
Differs? Not compared in this pass.

### R5-D4 handheld - drags
Keys: mouse drag on empty space, on a label, on an axis; ctrl+Z after the label drag.
Observed: drag on empty space (see screenshot); drag on a label moves the label; drag on an axis rescales; ctrl+Z after the label drag (see screenshot for the result).
Screenshots: R5-D4-drag-empty-space, R5-D4-drag-on-label-moves-label, R5-D4-ctrlz-after-label-drag, R5-D4-drag-on-axis-rescales.
Differs? Not compared in this pass.

### R5-H12 handheld - ctrl+T table split
Keys: ctrl+T on the graph page; Menu in each pane; doc > 5 Page Layout; ctrl+T again.
Observed:
- ctrl+T splits the page about half and half, graph left, table right, table pane focused.
- Menu with the table pane focused: 1 Actions >, 2 Table > only.
- Menu with the graph pane focused: the full Graphs menu 1-9.
- doc key > 5 Page Layout > : 1 Custom Split, 2 Select Layout >, 3 Select App (Ctrl+K), 4 Swap Applications, 5 Delete Application, 6 Delete Page, 7 Group (grey, Ctrl+4), 8 Ungroup (Ctrl+6). So the table pane is treated as an application in the page (Swap/Delete Application present).
- ctrl+T a second time closes the table pane and the graph fills the page again.
Screenshots: R5-H12-ctrl-t-table-split, R5-H12-menu-in-table-pane, R5-H12-page-layout-menu-with-table-split, R5-H12-ctrl-t-again-table-closed.
Differs? Not compared in this pass.

### R5-D23 handheld - Graphs Actions menu and Text
Settings: as above.
Keys: Menu > 1 Actions; Up (wraps to last item); then Menu > 1 > 7 Text, click the graph, type hello, Return.
Observed Actions list (handheld): 1 Pointer, 2 Select >, 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw. The list scrolls (down arrow at the bottom); Up from the top item wrapped to C MathDraw.
Text tool: the pointer became an I-beam and an "Ab" tool icon showed top left; clicking the graph opened a boxed entry at the click point; typed text hello appeared in italics; Return closed the box and left the text as plain italic on the graph; the Text tool stayed active afterwards (icon still shown).
Screenshots: R5-D23-actions-menu-top, R5-D23-actions-menu-bottom-mathdraw, R5-D23-text-box-typing, R5-D23-text-after-return.
Differs? Not compared in this pass. Not run in handheld: 3 Hide/Show leaves, 4 Attributes, 5 Set Conditions, 6 Delete all, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw.

### Handheld D31 / D22 rest
Not run in handheld in this pass (computer view done above).

## Hand-back lists (Part 1 Graphs)

### Run on the emulator (Handheld and/or Computer page size)
- Handheld: D34, D35, I1, D36, D12 rest, D6, D29, D32, D33, D11 (Trace submenu, Trace Step, Trace All, edge panning), D4 (empty-space, label and axis drags, ctrl+Z after label drag), H12 (ctrl+T split, Menu in each pane, Page Layout, ctrl+T again), D23 (Actions menu list and Text tool only).
- Computer page size (right-click menus): D2, D34, D4, D32, D33, D11, H12, D23 (Hide/Show, Window/Zoom, Select submenus), D35 (Window Settings dialog), D31.

### Not run (reason)
- Handheld D31 (slow nInt timing), D22 rest (Equation Templates), D28 table settings: session time ran out.
- Handheld D23 leaves: Hide/Show, Attributes, Set Conditions, Delete all, Coordinates and Equations, Calculate, Redefine, Insert Slider, MathDraw: session time ran out.
- Computer view D22: not reachable (entry-line icon is only a History Menu; Graph Entry/Edit types not found).
- Computer view H12 Page Layout: not reachable (document menu key does nothing in Computer page size).

### Also seen, not covered by the brief
- Handheld Actions menu has A Redefine, B Insert Slider, C MathDraw beyond the brief's list.
- Marked Analyze Graph points and the integral label follow later edits to the function.
- Stray "label"/"text" hint chip appears near clicked labels.
