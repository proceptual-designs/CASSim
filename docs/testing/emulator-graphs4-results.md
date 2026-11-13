# Graphs, check 6 run 3 (emulator-graphs4-results.md)
Settings for the document: Float 8, Radian, Real, Automatic (checked in Document Settings first). Document13, page 1.2 Graphs. Screenshots in pages-shots-6/ (names start G-). Observations only. This file is partial: see the run / not-run list at the end.

### D5: entry line with f1, f2, f3
Keys: new Graphs page opens with the entry line `f1(x)=`; typed `x^2`, Return; then `sin(x)`, Return (nothing was entered: after Return the entry line closes and the keys go to the graph); ctrl+G; Down; Up.
Observed: after Return the entry line is hidden and the new graph is drawn thick and then thin; its label `f1(x)=x²` is drawn by the curve. ctrl+G reopens the entry line on the first EMPTY slot (`f2(x)=`, tick box empty); Down moves to the next slot (`f3(x)=`) and Up from f2 goes to f1, which shows its ticked tick box and its text, with the cursor at the end. Typing there edits f1 in place: typing `sin(x)` at the end of f1 changed it to `f1(x)=x²·sin(x)` (not a new f2). Moving Up from f3 to f2 then typing `sin(x)` and Return created `f2(x)=sin(x)`, drawn red.
Screenshot: pages-shots-6/G-D5a-f1-graph-label.png, G-D5b-ctrlG-opens-f2.png, G-D5c-Down-to-f3.png, G-D5d-ctrlG-Up-f1-ticked.png, G-D5e-Up-edit-appends-f1.png, G-D5f-ctrlG-f2-empty.png, G-D5g-Down-f3-entry.png
Differs from CASSim or from this file's expectation? not compared.

### D10: graph labels
Keys: f3 typed as `x^3`, Right, `-3x^2`, Right, `+2x-5+sin(x)`, Return.
Observed: labels are drawn beside each curve in the curve's colour (`f1(x)=…` blue, `f2(x)=sin(x)` red, `f3` black). The long f3 label `f3(x)=x³−3·x²+2·x−5` is clipped at the right edge of the screen; the `+sin(x)` part is not shown. The label of f1 also runs to the screen edge and meets the axis end label. Drag of a label was not tried.
Screenshot: pages-shots-6/G-D10-long-label-clipped.png, G-D10b-three-graphs-labels.png
Differs from CASSim or from this file's expectation? not compared.

### D11: Graph Trace (Menu > 5 Trace > 1 Graph Trace)
Keys: Menu 5 opens the Trace sub-menu (1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▸, 5 Geometry Trace, 6 Erase Geometry Trace greyed out); `1`; Right; Up; typed `2`, Return; Return; Escape.
Observed: Trace starts on f1 at x = 0 and shows `f1: (0, 0)`. Right moves by 0.3 (`f1: (0.3, 0.027)`). Up goes from f1 to f3 (`f3: (0.3, −4.35)`), i.e. the order wraps from the first graph to the last. Typing `2` then Return moves the trace point to x = 2 (`f3: (2, −4.09)`). Return on a trace point drops a point with a coordinate label `(2, −4.09)` that stays after the trace is left. Escape leaves Trace; the dropped point and its label remain on the page.
Not run: Left/Right at the screen edge, Trace Step dialog, Trace All.
Screenshot: pages-shots-6/G-D11a-menu-trace.png, G-D11b-trace-start.png, G-D11c-trace-right.png, G-D11d-trace-up.png, G-D11e-type-2-enter.png, G-D11f-enter-drops-point.png, G-D11g-esc-after-drop.png
Differs from CASSim or from this file's expectation? not compared.

### D12: discontinuities (new Graphs page 1.3, same Problem, so the first graph here is f4; earlier graphs stay drawn)
Keys: typed the function, Return (each new function opened with ctrl+G, which lands on the first empty slot).
Observed:
- `1/x` (f4): two separate branches, no line across x = 0; the branches run off the top and bottom of the window. Typing `/` in the graph entry line makes a stacked fraction template with the cursor in the denominator (differs from the Calculator page, where `/` stays linear). A shown `1/x` in a ctrl+G edit had the cursor inside the fraction; ctrl+A then BackSpace emptied the line without the `f4(x)=` prefix, and typing then Return advanced to the next slot without redefining f4 (f4 stayed `1/x`).
- `tan(x)` (f5): branches drawn separately, no vertical lines across the asymptotes.
- `floor(x)` (f6): horizontal steps only; no vertical joins and no circles at the ends of the steps.
- `abs(x)` typed then Right and Escape: the graph f7 `|x|` was created, so Escape in the entry line keeps the typed function.
- `ln(x)` (f8): drawn for x > 0 only, ends at the y-axis with no end marker.
- `sqrt(4-x^2)` (f9; typed `sqrt(` becomes √): upper half circle from x = −2 to 2, no end markers.
Not run: `1/(x-1)^2`, `abs(x)/x`, `sqrt(x)` (the `1/(x-1)^2` entry was lost in the ctrl+A/BackSpace mix-up above).
Screenshot: pages-shots-6/G-D12a-one-over-x.png, G-D12b-ctrlG-Up-edit-f4-fraction.png, G-D12c-cleared-line.png, G-D12d-tan.png, G-D12e-floor.png, G-D12f-abs-after-Escape.png, G-D12g-ln.png, G-D12h-sqrt-4-minus-x2.png
Differs from CASSim or from this file's expectation? not compared.

## Run / not run (Part D, graphs4, so far)
Run: D5, D10 (partial), D11 (partial: Graph Trace, typed x, drop point, Esc), D12 (6 of 8 functions).
Not run: D1–D4, D6–D9, D13, D18, D22, D23, D29, D31–D33, rest of D11 and D12. Reason: this session stopped here; nothing was blocked technically.
Also seen: a new Graphs page in the same Problem continues the function numbering (f4 after f1–f3), and f-names are shared with the Calculator page.

## Addendum: D13 (new document Document14, page 1.2; Document Settings checked: Float 8, Radian, Real, Auto)
### D13: restricted domains and the piecewise template
Keys: `x^2`, Right, `|x>0`, Return (f1); ctrl+G, `x^2`, Right, `|-1<x<2`, Return (f2); ctrl+G, open the templates palette, move to the piecewise icon and press Return (a mouse click only moves the highlight in the palette; Return inserts), then `x+1`, Tab, `x<0`, Tab, `x^2`, Right, Tab, `x>=0`, Return.
Observed: a restriction typed with `|` is stored as a one-piece piecewise and the label reads `f1(x)={x², x>0` (and `{x², −1<x<2`). The graph starts at the origin and ends at the window edge (or at x = 2) with no open or closed circles drawn. The piecewise template appears with two rows, each a value box and a condition box, plus a third greyed box; Tab moves value → condition → next row. `>=` is shown as `≥`. The two-piece graph `f3` is drawn as one thick curve with no circle at x = 0, and the label shows `{x+1, x<0` over `{x², x≥0`.
Screenshot: pages-shots-6/G-D13a-restrict-x-gt-0.png, G-D13b-restrict-neg1-x-2.png, G-D13c-template-palette.png, G-D13d-piecewise-empty.png, G-D13e-piecewise-filled.png, G-D13f-piecewise-graph.png
Differs from CASSim or from this file's expectation? not compared.
Run now also: D13. Still not run: D1–D4, D6–D9, D18, D22, D23, D29, D31–D33.

## Addendum: D1 menus (new document Document15, Graphs page 1.2, f1(x)=x²; Document Settings checked: Float 8, Radian, Real, Auto)
Menu opened by clicking the menu key; item digits/letters open and select; Left closes one level.
### D1: menu lists (text as shown)
- Menu: 1 Actions, 2 View, 3 Graph Entry/Edit, 4 Window / Zoom, 5 Trace, 6 Analyze Graph, 7 Table, 8 Geometry, 9 Settings…
- Actions: 1 Pointer, 2 Select ▸, 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw (the list scrolls; Up from the top wraps to C).
- View: 1 Graphing (greyed), 2 Plane Geometry, 3 3D Graphing, 4 Hide Analytic Window (greyed), 5 Hide Axes, 6 Grid ▸, 7 Show Entry Line (Ctrl+G), 8 Hide Axes End Values, 9 Hide Object Selection Guides. Grid ▸: 1 No Grid (greyed, current), 2 Dot Grid, 3 Lined Grid.
- Graph Entry/Edit: 1 Function, 2 Relation, 3 Equation Templates ▸, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▸, 8 Diff Eq. Equation Templates ▸: 1 Line ▸, 2 Parabola ▸, 3 Circle ▸, 4 Ellipse ▸, 5 Hyperbola ▸, 6 Conic ▸. Sequence ▸: 1 Sequence, 2 Custom.
- Window / Zoom: 1 Window Settings…, 2 Zoom – Box, 3 Zoom – In, 4 Zoom – Out, 5 Zoom – Standard, 6 Zoom – Quadrant 1, 7 Zoom – User, 8 Zoom – Trig, 9 Zoom – Data, A Zoom – Fit, B Zoom – Square, C Zoom – Decimal (Up from the top wraps to C).
- Trace: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▸, 5 Geometry Trace, 6 Erase Geometry Trace (greyed). Path Plot ▸: 1 Function, 2 Parametric, 3 Polar, 4 Path Setup…
- Analyze Graph: 1 Zero, 2 Minimum, 3 Maximum, 4 Intersection, 5 Inflection, 6 dy/dx, 7 Integral, 8 Bounded Area, 9 Analyze Conics ▸. Analyze Conics ▸: 1 Center, 2 Vertices, 3 Foci, 4 Axes of Symmetry, 5 Directrix, 6 Asymptotes, 7 Radius, 8 Eccentricity, 9 Latus Rectum.
- Geometry: 1 Points & Lines ▸, 2 Shapes ▸, 3 Measurement ▸, 4 Construction ▸, 5 Transformation ▸. Points & Lines ▸ (Up from the top wraps to the end): 1 Point (p), 2 Point On, 3 Point by Coordinates (p), 4 Intersection Point(s), 5 Line, 6 Segment, 7 Ray, 8 Tangent, 9 Vector, A Circle arc. Transformation ▸: 1 Symmetry, 2 Reflection, 3 Translation, 4 Rotation, 5 Dilation.
- Not opened here: Actions > 2 Select ▸ contents.
Screenshot: pages-shots-6/G-D1a-actions-menu.png, G-D1b-view-menu.png, G-D1c-window-zoom-top.png, G-D1d-window-zoom-end.png, G-D1e-view-grid.png, G-D1f-graph-entry-menu.png, G-D1g-equation-templates.png, G-D1h-sequence-submenu.png, G-D1i-trace-pathplot.png, G-D1j-analyze-menu.png, G-D1k-analyze-conics.png, G-D1l-geometry-menu.png, G-D1m-points-lines-end.png, G-D1n-transformation.png, G-D1o-actions-end.png
Differs from CASSim or from this file's expectation? not compared.
Run now also: D1 (except Actions > Select).

### D8: Zoom windows (document Document15, f1(x)=x²; Window Settings read from Menu > 4 Window / Zoom > 1)
- Standard window: XMin −10, XMax 10, XScale Auto, YMin −6.6666666666667, YMax 6.6666666666667, YScale Auto.
- Zoom – Fit (Menu 4 A) from Standard: x range unchanged; YMin −10.0012137898067, YMax 110.0197745302515 (the graph fills the window, the vertical axis end value shows 110.02).
- Zoom – Box (Menu 4 2): the prompt `1st corner?` shows beside a magnifier pointer; Return fixes it; arrow keys (5 Right, 5 Down) move the pointer; the prompt becomes `2nd corner?`; Return applies. Window afterwards: XMin 1.3836477987421, XMax 2.0125786163522, YMin 1.7610062893082, YMax 2.3899371069182 (same aspect ratio as the screen).
- Zoom – Out (Menu 4 4) from Standard: prompt `Center?`; Return at the pointer's default position gave XMin −17.987421383648, XMax 22.012578616352, YMin −11.572327044025, YMax 15.094339622642 (the window is scaled up by 2 about the chosen point, which was not the origin).
- Zoom – User (Menu 4 7): after the Zoom – Out above it showed no prompt and the window did not change (it appears to need a window set with the user window dialog first; not investigated).
Not run: Zoom – Data with a scatter plot of `xs`, `ys`.
Screenshot: pages-shots-6/G-D8a-window-standard.png, G-D8b-zoomfit-graph.png, G-D8c-window-after-fit.png, G-D8d-box-1st-corner.png, G-D8e-box-2nd-corner.png, G-D8f-box-result.png, G-D8g-window-after-box.png, G-D8h-out-center-prompt.png, G-D8i-out-result.png, G-D8j-window-after-out.png, G-D8k-zoom-user.png
Differs from CASSim or from this file's expectation? not compared.
Run now also: D8 (except Zoom – Data, Zoom – User effect).

### D2: context menus (right click) on the Graphs page, Standard window, f1(x)=x²
- Empty space: 1 Recent ▸, 2 Hide/Show ▸, 3 Select ▸, 4 Window / Zoom ▸, 5 Text, 6 Delete all, 7 Erase Geometry Trace (greyed), 8 Pin.
- An axis: 1 Recent ▸, 2 Attributes, 3 Hide/Show ▸, 4 Window / Zoom ▸, 5 Pin, 6 Color ▸, 7 Conditions…. A tooltip `axes` appears beside the pointer.
- The graph of f1: 1 Recent ▸, 2 Label (greyed), 3 Attributes, 4 Hide, 5 Delete, 6 Edit Relation, 7 Trace ▸, 8 Analyze Graph ▸, 9 Table ▸, A Pin, B Color ▸, C Conditions… (list scrolls; arrow at the bottom). A tooltip `multi-select` appears beside the pointer.
- The graph label: 1 Group (greyed), 2 Delete, 3 Pin, 4 Color ▸, 5 Conditions…. The tooltip `multi-select` with a small `tab` key badge appears.
Not run: context menu on a point and on the entry line.
Note: the Escape key closes each menu. Click and Escape were sent from the status bar focus.
Screenshot: pages-shots-6/G-D2a-context-empty.png, G-D2b-context-axis.png, G-D2c-context-graph.png, G-D2d-context-label.png
Differs from CASSim or from this file's expectation? not compared.

Process note: `computer_open_application` for the emulator created a new empty document each time it was needed (Document14, 15, 16 appeared). Context menus recorded once on a spreadsheet page by mistake were discarded (Document16 is an empty spare).
Run now also: D2 (empty space, axis, graph, label).

### D9: pan and rescale (Standard window, f1(x)=x²)
- Drag starting on the graph label area (top right, near f1's label): no pan; a rubber-band selection box formed and the label was highlighted, with the tooltip `multi-select` shown. The window did not change (Window Settings still −10..10, −6.6666666666667..6.6666666666667).
- Drag along the x axis from near its right end (leftwards, 100 px): both axes were rescaled about the origin, window −15.7..15.7 by −10.47..10.47 (the x end values `−15.7` and `15.7` shown), i.e. the view zoomed out; an `axes` tooltip showed during the drag.
- Arrow keys (3 Right, 2 Up) with nothing selected, after a click on empty space: the window did not change.
- Drag on empty space far from any object (from lower left, 100 px left and 40 px up): the view pans with the pointer. Window afterwards: XMin −7.3584905660377, XMax 12.6415094339623, YMin −7.7358490566038, YMax 5.5974842767296 (width and height unchanged).
Screenshot: pages-shots-6/G-D9a-drag-near-label.png, G-D9b-window-standard-again.png, G-D9c-drag-axis-end.png, G-D9d-arrows-nothing-selected.png, G-D9e-pan-drag.png, G-D9f-window-after-pan.png
Differs from CASSim or from this file's expectation? not compared.
Run now also: D9.

## Run / not run (Part D, graphs4, updated)
Run: D1 (except Actions > Select), D2 (except point and entry line), D5, D8 (except Zoom – Data), D9, D10 (partial), D11 (partial), D12 (6 of 8), D13.
Not run: D3, D6, D7, D18, D22, D23, D29, D31–D33; rest of D11 and D12; Zoom – Data.
Reason: stopped for this session; nothing blocked technically.

### D4: keys and mouse on the Graphs page (new document Document17; Document Settings checked: Float 8, Radian, Real, Auto; f1(x)=x², f2(x)=sin(x))
Observed:
- Tab with nothing selected: opens the entry line on the first empty slot (`f3(x)=`). A second Tab moves focus to the attributes button at the right of the entry line (the button is highlighted). shift+Tab returns to the entry field. Right in the entry field does nothing; ctrl+Right moves focus to the attributes button again. Esc closes the entry line.
- A click on the graph of f1: the graph is drawn thick and a tooltip `graph f1` appears; clicking selects it.
- The keyboard Delete key (sent as `Delete`) did nothing on a selected graph; BackSpace (the handheld's del key) deleted f1 and its label (only f2 stayed). ctrl+Z restored f1 and its label. Esc after a click deselects the graph.
- ctrl+Z straight after the Delete key (which did nothing) removed the selection highlight only.
- Double click on the graph: opens the entry line on `f1(x)=x²`, tick box ticked and highlighted, cursor at the end.
- Mouse wheel scroll up over the graph: no zoom or pan; a tooltip `text` appeared near the pointer.
- Return on a selected graph, Enter variants, ctrl+Left/Down and arrow keys with a selected graph: not run in this pass.
Screenshot: pages-shots-6/G-D5h-f1-f2-document17.png, G-D4a-tab-opens-entry-f3.png, G-D4b-tab-again-attr-button.png, G-D4c-shifttab-back-to-field.png, G-D4d-right-in-entry.png, G-D4e-ctrl-right-in-entry.png, G-D4f-esc-closes-entry.png, G-D4g-click-graph-selects.png, G-D4h-Delete-key-no-effect.png, G-D4i-ctrlz-after-select.png, G-D4j-double-click-graph.png, G-D4k-wheel-up.png, G-D4l-backspace-deletes-graph.png, G-D4m-ctrlz-restores.png, G-D4n-select-then-esc.png
Differs from CASSim or from this file's expectation? not compared.
Run now also: D4 (part).
