# Emulator check 4, Part D: Graphs (TI-Nspire CX CAS Premium Teacher Software 6.0.3.374)

Observations only. Settings for every row unless stated: Document Settings Radian, Automatic, Real, Float 8; RAD in the title bar. Handheld-page-size document "Document15" (Graphs page 1.2; Calculator page 1.1 holds xs, ys, `f(x):=x^3-3·x`). Handheld view, 250% zoom. Screenshots are in pages-shots/.

Coverage was partial. See the three lists at the end.

### D1 Menu tree (Graphs page, Menu key)
Settings: as above
Keys: Menu key (366,379), then number keys; Left backs out one level.
Observed: top menu: 1 Actions ▶, 2 View ▶, 3 Graph Entry/Edit ▶, 4 Window / Zoom ▶, 5 Trace ▶, 6 Analyze Graph ▶, 7 Table ▶ (greyed while no function is plotted), 8 Geometry ▶, 9 Settings…
- 1 Actions ▶ (list longer than the screen, down arrow shown): 1 Pointer, 2 Select ▶, 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, more below (not scrolled).
- 2 View ▶: 1 Graphing (greyed, current), 2 Plane Geometry, 3 3D Graphing, 4 Hide Analytic Window (greyed), 5 Hide Axes, 6 Grid ▶, 7 Show Entry Line (Ctrl+G), 8 Hide Axes End Values, 9 Hide Object Selection Guides.
- 3 Graph Entry/Edit ▶: 1 Function, 2 Relation, 3 Equation Templates ▶, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▶, 8 Diff Eq.
- 4 Window / Zoom ▶: 1 Window Settings…, 2 Zoom – Box, 3 Zoom – In, 4 Zoom – Out, 5 Zoom – Standard, 6 Zoom – Quadrant 1, 7 Zoom – User, 8 Zoom – Trig, 9 Zoom – Data, A Zoom – Fit, more below (down arrow; not scrolled).
- 5 Trace ▶: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▶, 5 Geometry Trace, 6 Erase Geometry Trace (greyed).
- 6 Analyze Graph ▶: 1 Zero, 2 Minimum, 3 Maximum, 4 Intersection, 5 Inflection, 6 dy/dx, 7 Integral, 8 Bounded Area, 9 Analyze Conics ▶.
- 8 Geometry ▶: 1 Points & Lines ▶, 2 Shapes ▶, 3 Measurement ▶, 4 Construction ▶, 5 Transformation ▶ (5 not opened).
  - Points & Lines: 1 Point (p), 2 Point On, 3 Point by Coordinates (p), 4 Intersection Point(s), 5 Line, 6 Segment, 7 Ray, 8 Tangent, 9 Vector, A Circle arc, more below (not scrolled).
  - Shapes: 1 Circle, 2 Triangle, 3 Rectangle, 4 Polygon, 5 Regular Polygon, 6 Ellipse, 7 Parabola, 8 Hyperbola, 9 Conic by Five Points.
  - Measurement: 1 Length, 2 Area, 3 Slope, 4 Angle, 5 Directed Angle.
  - Construction: 1 Perpendicular, 2 Parallel, 3 Perpendicular Bisector, 4 Angle Bisector, 5 Midpoint, 6 Locus, 7 Compass, 8 Measurement transfer.
- 9 Settings…: dialog, see D18.
Screenshot: pages-shots/D1-menu-top.png, D1-actions-submenu.png, D1-view-submenu.png, D1-graph-entry-submenu.png, D1-window-zoom-submenu.png, D1-trace-submenu.png, D1-analyze-graph-submenu.png, D20-geometry-submenu.png, D20-geometry-points-lines.png, D20-geometry-shapes.png, D20-geometry-measurement.png, D20-geometry-construction.png
Differs from CASSim or from this file's expectation? not known (CASSim not compared in this run)

### D3 First screen
Settings: as above
Keys: Add Graphs page (ctrl+i, 2).
Observed: axes run -10 to 10 with a "1" tick label on each axis and "x" at the right end; the bottom y label reads -6.67 and the top reads 6.67. Entry line `f1(x)=` with the cursor appears at the top on a new Graphs page (empty tick box at the left, attributes icon at the right).
Screenshot: pages-shots/D3-first-screen.png
Differs from CASSim or from this file's expectation? not known

### D5/D6 Entry line and shared variable
Settings: as above
Keys: click status bar; Ctrl+G (Show Entry Line); typed `f(x)`, Return.
Observed: with `f(x):=x^3-3·x` defined on 1.1, `f1(x)=f(x)` plots the cubic (zeros near ±1.73 and 0, local max about 2 near x=-1, local min about -2 near x=1). The plot label reads `f1(x)=f(x)`. Typing `f(x)` when the entry line was not open (before Ctrl+G) put nothing on the plot.
Screenshot: pages-shots/D6-f1-equals-f-plot.png
Differs from CASSim or from this file's expectation? not known

### D7 Default Window Settings
Settings: as above
Keys: Menu 4 1.
Observed: dialog "Window Settings": XMin -10, XMax 10, XScale Auto, YMin -6.6666666666667, YMax 6.6666666666667, YScale Auto, OK and Cancel. XMin field is selected on opening.
Screenshot: pages-shots/D7-window-settings-default.png
Differs from CASSim or from this file's expectation? not known

### D8 Zoom items
Settings: as above
Keys: Menu 4 then the item number (items 1, 3, 5, 6, 8, A used).
Observed:
- Zoom – Standard (5): -10 to 10, y -6.67 to 6.67, labels "1".
- Zoom – Quadrant 1 (6): x -4 to 20, y -2.67 to 13.33 (labels -4, 20, 13.33, -2.67), so the origin is near the lower left but not at the corner.
- Zoom – Trig (8): x -2·π to 2·π, y -4.19 to 4.19, tick labels 0.5.
- Zoom – Fit (A): applied on the trig window it gave y about -275.05 to 275.12 with x unchanged (-2·π shown at the left), the curve only partly visible because the Claude window covered the right of the screen in the capture; not repeated.
- Zoom – In (3): a magnifier icon appears at the top left and a "Center?" tooltip at the pointer; Return zooms about the pointer. The new window read about x -5.63 to 4.37, y -4.72 to 1.95.
Zoom – Box (2), Zoom – Out (4), Zoom – User (7), Zoom – Data (9) not run (see list).
Screenshot: pages-shots/D8-zoom-standard.png, D8-zoom-quadrant1.png, D8-zoom-trig.png, D8-zoom-fit.png, D8-zoom-in-prompt.png, D8-zoom-in-result.png (and the same three windows on an empty plot: D8-zoom-standard-emptyplot.png, D8-zoom-quadrant1-emptyplot.png, D8-zoom-trig-emptyplot.png)
Differs from CASSim or from this file's expectation? not known

### D14 Analyze Graph prompts
Settings: as above, f1(x)=f(x) on Standard window
Keys: Menu 6 then 1, 2, 5, 6, 7 (prompts), and Zero with two clicks on the graph.
Observed:
- 1 Zero: icon "Zero" top left, prompt "lower bound?" with a dotted vertical line at the pointer; after a click the prompt reads "upper bound?"; a second click gives a point at (-1.73,0) with the coordinate label shown in a large font.
- 2 Minimum: prompt "lower bound?" (min icon).
- 5 Inflection: prompt "lower bound?" (inf icon).
- 6 dy/dx: prompt "position?" with a value label (-1.81 seen at the pointer position).
- 7 Integral: prompt "lower bound?".
- 3 Maximum, 4 Intersection, 8 Bounded Area, 9 Analyze Conics prompts not captured.
Screenshot: pages-shots/D14-zero-lower-bound-prompt.png, D14-zero-upper-bound-prompt.png, D14-zero-result.png, D14-minimum-lower-bound-prompt.png, D14-inflection-lower-bound-prompt.png, D14-dydx-position-prompt.png, D14-integral-lower-bound-prompt.png
Differs from CASSim or from this file's expectation? not known

### D17 Table (unplanned sighting)
Settings: as above
Keys: after Escape from the Zero tool, Menu 6 3, two clicks on the graph. I did not intend to open a table.
Observed: the page split into the graph (left) and a table (right) with columns x and `f1(x):=` / `f(x)`; rows showed x 1 to 5 with f1 values -2, 2, 18, 52, 110. I do not know which key opened it; Ctrl+T afterwards removed it. Not examined further, so D17 is not covered.
Screenshot: pages-shots/D17-table-split-unplanned.png
Differs from CASSim or from this file's expectation? not known

### D18 Settings dialog
Settings: as above
Keys: Menu 9.
Observed: "Graphs & Geometry Settings": Display Digits Float 3, Graphing Angle Auto, Geometry Angle Degree, Grid No Grid, checkboxes: Automatically hide plot labels (unticked), Show axes end values (ticked), Show tool tips for function manipulation (unticked), Automatically find points of interest (ticked), Force geometric triangle angles to integers (unticked); OK and Cancel; scroll bar at the right.
Screenshot: pages-shots/D18-settings-dialog-top.png, D18-settings-dialog-bottom.png
Differs from CASSim or from this file's expectation? not known

### D20 Geometry submenus
See D1 (menu lists and screenshots). Creating Point On / labels not run.

## Lists

### Run on the emulator
D1 (all top-level submenus except those named under "not opened"), D3, D5/D6 (one function), D7, D8 (items 1, 3, 5, 6, 8, A), D14 (prompt texts for Zero, Minimum, Inflection, dy/dx, Integral; one completed Zero), D18, D20 (menu lists only).

### Not run, with reasons
- D1 submenus 2 Select, 6 Grid, 3 Equation Templates, 7 Sequence, 5 Transformation, 4 Path Plot, 9 Analyze Conics, and the scrolled rest of Actions, Points & Lines and Window / Zoom: not opened for lack of time.
- D2 context menus, D4 keys and mouse, D9 pan and rescale, D10 labels, D11 Trace, D12 discontinuities, D13 restricted domains and piecewise, D15 relations and inequalities, D16 sliders, D17 table (only an unplanned sighting), D19 View items, D20 Point On and labels, D21 attributes, D22 scatter plot, D23 text and coordinates, D24 Degree mode, D25 limits and messages: not run for lack of time.
- D8 Zoom – Box, Zoom – Out, Zoom – User, Zoom – Data: not run.
- D14 prompts for Maximum, Intersection, Bounded Area, Analyze Conics: not run.

### Also seen, not covered
- The table opened by accident (D17 screenshot).
- Zoom – Fit produced a y range of about ±275 on the cubic with the trig x range; capture was partly hidden by the Claude window.
