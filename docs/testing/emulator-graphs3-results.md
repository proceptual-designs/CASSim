# Part D results (check 6, run 2): Graphs, extra rows D26 to D28 (TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view)

Settings: Document6 (a new document), Radian (title bar shows RAD), Graphs page with `f1(x)=x^2`, Window Settings changed by Menu > 4 Window / Zoom > 1 Window Settings (XScale and YScale left on Auto; the y window stayed at its standard -6.67 to 6.67 throughout). Document Settings Automatic/Real/Float were not re-checked in this document (opened by `open_application`; the title bar shows RAD only). Tick spacing is read by eye from a zoom of the screen. No screenshots were saved for D (zooms read on screen); that is said again in each row.

## D26 - Tick marks with XScale and YScale on Auto
- Keys: Menu (click) > 4 Window / Zoom > 1 Window Settings; type XMin, Tab, XMax, Return; zoom the screen.
- Observed (x window: tick spacing on x; numbered ticks; end labels): 
  - -10 to 10: a tick at every 1; only the tick at 1 is numbered (and 1 on the y axis); end labels `-10` and `10` at the ends of the x axis.
  - -1 to 1: ticks every 0.1; the tick at `0.1` is the only numbered one; end labels `-1` and `1`.
  - -100 to 100: ticks every 10; `10` is the only numbered one; end labels `-100` and `100`.
  - 0 to 1000: very close ticks, about every 10 (about 100 across the screen, judged from the count of marks); no tick number; end labels `0` and `1000`.
  - -0.1 to 0.1: ticks every 0.01; `0.01` is the only numbered one; end labels `-0.1` and `0.1`.
  - -2π to 2π: ticks every 0.5; `0.5` is the only numbered one; end labels `-2·π` and `2·π` (shown with a centred dot, not `2π`).
  - -7 to 13: ticks every 1; `1` is the only numbered one; end labels `-7` and `13`.
  - The y axis (window left at -6.67 to 6.67 each time) keeps ticks every 1 with `1` numbered and end labels `6.67` and `-6.67`.
  - So the pattern seen: the tick spacing is a power of ten set by the window width (a tenth or a twentieth of it), one tick near the origin is numbered with the first tick value and the two end values are the only other labels.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## D27 - Graph Trace defaults
- Keys: Menu > 5 Trace > 1 Graph Trace; Right; Menu > 5 > 3 Trace Step; the Esc key on the keypad ends a trace.
- Observed: Trace menu: 1 Graph Trace, 2 Trace All, 3 Trace Step..., 4 Path Plot (submenu), 5 Geometry Trace, 6 Erase Geometry Trace (grey). Trace Step dialog: one field `Trace Step:` showing `Automatic` (with a drop-down arrow), OK and Cancel (cancelled). On the Standard window (-10 to 10) the first trace started at x = 0 on f1 (read-out bottom right `f1: (0, 0)`), and one Right press gave `f1: (0.3, 0.09)` (x step 0.3). In the next windows a new trace did NOT start at a default: it started at the x left by the previous trace (0.3 in the -100 to 100 window, then 0.6 then 0.9 in -1 to 1), and the step stayed 0.3 in every window (-100 to 100: 0.3 to 0.6; -1 to 1: 0.6 to 0.9 and 0.9 to 1.2). So the step did not follow the window width in these runs; I could not tell the rule. At the right edge in the -1 to 1 window the window panned (after x = 1.2 the x axis read -0.6 to 1.4: the window moved by 0.4).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## D28 - Table defaults and the Table pane
- Keys: ctrl+T on the Graphs page (after a click on the status bar); Menu in the table pane; 2 Table > 5 Edit Table Settings; ctrl+T again.
- Observed: ctrl+T split the page: the graph on the left (about 160 px) and a table on the right (about 160 px), the table pane focused (teal border). Columns: `x` and `f1(x):=` with a drop-down arrow and the formula `x^2` in a row under the title; the rows read x = 1., 2., 3. ... with f1 = 1., 4., 9., 16., 25. (a row above 1. was partly hidden under the header). Menu with the table focused: 1 Actions (submenu), 2 Table (submenu). Table submenu: 1 Remove Table (Ctrl+T), 2 Delete Column, 3 Choose..., 4 Edit Expression, 5 Edit Table Settings.... The dialog `Table`: Table Start `0.`, Table Step `1.0`, Independent `Auto` (drop-down: Auto, Ask), Dependent `Auto` (drop-down: Auto, Ask); buttons OK, Cancel. (The table showed 1. as its first visible row while Table Start is 0.: row 0 may have been hidden above; not checked.) The second ctrl+T removed the table and the graph went back to the full page. Not run: whether the table pane is an app in Page Layout (H12).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## D30 - How many points: `sin(50x)` and `sin(1/x)` in the standard window
- Keys: Menu > 3 Graph Entry/Edit > 1 Function; type `sin(50x)`, Return (it became f2); ctrl+G (entry line opens at f3), type `sin(1/x)`, Return (f3). Window -10 to 10 by -6.67 to 6.67; f1 = x^2 still drawn.
- Observed: `sin(50x)`: not a smooth wave: a column of vertical strokes whose height rises and falls in a repeating envelope (a beat pattern about one swell for every 1.5 units of x), all within the band y = -1 to 1, so the curve is sampled about once per pixel column and aliased. Right after Return the selected graph is drawn heavy (a solid thick red band) and goes thin when another graph is selected. `sin(1/x)`: smooth and thin for |x| above about 1 (it flattens towards 0 for large |x|); inside about |x| < 0.5 the oscillation is a solid black blob of strokes around the y axis with no clear curve; no break in the line was seen elsewhere. The f2 label has a pale grey box behind it that hides what is under it.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## D12 - Discontinuities (eight functions, each on its own new Graphs page, Standard window)
- Settings: Document7 (new document, RAD), one new Graphs page per function (ctrl+i, 2, then typed the function and Return). The function names went up with each page (f1, f2, ... f8) because the variables are shared by the Problem, so each page drew only its newest function. Radian. The newly entered graph is drawn heavy (selected) in the pictures.
- Observed:
  - `1/x`: two separate branches, no line across the break at x = 0; the branches run off the top and bottom of the screen at the y axis.
  - `tan(x)`: one separate branch per period (about six in -10 to 10), no vertical line at the asymptotes; each branch leaves the top and the bottom of the window.
  - `1/(x-1)^2`: two branches, both going up the screen on either side of x = 1; no line between them.
  - `floor(x)`: horizontal segments, each one unit wide, at integer heights; no vertical connecting lines; the segment ends carry no open or closed circles (plain flat ends); the segment for [0, 1) starts at x = 0 and sits at y = 0.
  - `abs(x)/x`: two flat lines, y = -1 for x < 0 and y = 1 for x > 0; nothing drawn at x = 0, no circles; no line joining them.
  - `ln(x)`: a single curve starting at the y axis and running down the left of the screen to the bottom edge; nothing for x ≤ 0.
  - `sqrt(x)` (typed with the √ character): a curve starting at the origin (x = 0, y = 0) going right; nothing for x < 0; no marker at the end point.
  - `sqrt(4-x^2)`: an upper semicircle-like arc from x = -2 to x = 2 (about 4 units wide) with plain ends on the x axis; no circles.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## D13 - Restricted domains (two of the three forms)
- Settings: Document7, new Graphs page for each, Standard window. Typed `x^2`, Right, `|x>0` and `x^2`, Right, `|-1<x<2`.
- Observed: the label is rewritten as a brace form: `f9(x) = { x², x>0` and `f10(x) = { x², -1<x<2` (a large left brace, the condition after a comma). `x^2|x>0`: the curve runs from the origin up to the right and off the top; the end at the origin carries no open circle (plain end). `x^2|-1<x<2`: a curve from x = -1 (height 1) down through the origin and up to x = 2 (height 4); both ends plain, no circles. The new graph is drawn heavy (selected). The piecewise template with two pieces was not run.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

---
## Lists for part D (run 2, so far)

### Run
D26, D27, D28, D30, D12, D13 (the two restricted forms; not the piecewise template). H12 in part: ctrl+T on the Graphs page splits it into graph left and table right and a second ctrl+T removes it (D28).

### Not run
D1 to D11, D14 to D25 and the piecewise template of D13 (the basic Part D rows), D29, D31, D32, D33. Editing `f1` in the entry line did not take (Up x3 then retyping left f1 as x^2), so D12 was done with one new page per function instead. Reason: I ran out of time in this session.

### Also seen, not covered by a row
- The Add-application list for a new page has the items 1 Add Calculator, 2 Add Graphs, 3 Add Geometry, 4 Add Lists & Spreadsheet, 5 Add Data & Statistics, 6 Add Notes, 7 Add Vernier DataQuest, 8 Add Widget, 9 Add Program Editor (submenu), A Add Python (submenu).
- Window / Zoom submenu: 1 Window Settings..., 2 Zoom - Box, 3 Zoom - In, 4 Zoom - Out, 5 Zoom - Standard, 6 Zoom - Quadrant 1, 7 Zoom - User, 8 Zoom - Trig, 9 Zoom - Data, A Zoom - Fit (a down arrow shows more items below).
- Window Settings dialog: XMin -10, XMax 10, XScale Auto (drop-down), YMin -6.6666666666667, YMax 6.6666666666667, YScale Auto (drop-down), OK, Cancel.
- Graphs page Menu: 1 Actions, 2 View, 3 Graph Entry/Edit, 4 Window / Zoom, 5 Trace, 6 Analyze Graph, 7 Table, 8 Geometry, 9 Settings....
- Graph entry line: after Return on a new function the line closes; ctrl+G reopens it at the next free slot (f3, f4). Up in the open entry line moves f4, f3, f2, f1; on f1 the check box is drawn with a blue frame.
- Selected graphs are drawn thick (about three times the line width); the 'graph f1' tip shows with Up/Down between graphs.

## D14 Analyze Graph prompts (run 2, Document11)
Settings: RAD, Graphs page, f2(x)=x^3-3x (f1 on page 1.1 is a mistyped x^(3-3x); f3(x)=x+1 added with ctrl+G).
Keys: Menu (clicked) 6 then item digit; Left/Right arrows move the bound, Return accepts.
Observed:
- 6 Analyze Graph submenu: 1 Zero, 2 Minimum, 3 Maximum, 4 Intersection, 5 Inflection, 6 dy/dx, 7 Integral, 8 Bounded Area, 9 Analyze Conics (submenu).
- 3 Maximum: prompt "lower bound?" (dotted vertical line), Return, prompt "upper bound?", Return; result drawn as a dot with tooltip "maximum" and label (-1, 2).
- 4 Intersection (f2 and f3 both shown): "lower bound?" then "upper bound?"; with the bounds used a dot appeared at (-0.254, 0.746) with tooltip "intersection". A further Return showed a "graph f3 [tab]" hover label on the line (not understood).
- 8 Bounded Area: "lower bound?", Return, "upper bound?" (the bound line showed the x value 0.647 in grey beside it); after the second Return a solid vertical bar at x = 0.647 with label 0.647 stayed; no shaded area or area value appeared with my key sequence. A hover label "point on [tab]" appeared first.
- 9 Analyze Conics submenu: 1 Center, 2 Vertices, 3 Foci, 4 Axes of Symmetry, 5 Directrix, 6 Asymptotes, 7 Radius, 8 Eccentricity, 9 Latus Rectum. Picking 1 with no conic on the page only changed the tool icon (top left); no prompt text.
- Menu digits pressed straight after clicking Menu are sometimes dropped; a 1 s wait between digits fixed it.
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## D15 Relations and inequalities (run 2, page 1.3)
Settings: RAD, new Graphs page. Keys: Menu 3 2 (Graph Entry/Edit > Relation) shows a rel1(x,y) entry; type, Return.
Observed:
- `y<x+1`: region below the line shaded blue, boundary a solid thick line (not dashed), label "y<x+1" in a pale box near the origin.
- `y>=x^2`: typed >= shown as ≥ ("y≥x²"); region inside the parabola shaded red with a solid red boundary; label "y≥x²".
- `x=3`: a solid black vertical line, label "x=3"; no shading.
- `x^2+y^2=4` (typed x^2, Right, +y^2, Right, =4): a magenta circle, no shading, label "x²+y²=4"; the four labels overlapped near the origin.
- Every boundary looked solid, including the strict `<`.
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## D16 Sliders (run 2, page 1.4)
Settings: RAD, new Graphs page. Keys: type `a*x^2`, Return; Return on the dialog; ctrl then Menu (on-screen keys) for the slider menu.
Observed:
- Entering `f1(x)=a*x^2` (it was labelled f4 on this page): dialog "Create Sliders", text "Create a slider for:", a checkbox row "a" (ticked), buttons OK / Cancel. Return accepts.
- The slider appears as a boxed panel at the lower left of the graph area: "a =1.", a horizontal line with a blue marker, "-5." under the left end and "5." under the right end; the box has blue round handles on both sides and a blue outline while selected. The curve updated at once.
- Up arrow with the entry line focused selected the slider; Right arrow x5 moved the whole panel to the right (about 15 px), not the value.
- ctrl+Menu on a slider: 1 Settings..., 2 Minimize, 3 Animate, 4 Delete.
- Slider Settings dialog fields in order: Variable (drop-down, "a"), Value (1), Minimum (-5), Maximum (5), Step Size (drop-down, Automatic), Style (drop-down, Horizontal; greyed text), Display Digits (drop-down, Float 3), Minimized (checkbox, off), Show Variable (checkbox, on), Show Scale (checkbox, on); OK / Cancel. The dialog scrolls (scroll bar at the right).
- 3 Animate: the value ran from 1 toward -5 and back (seen -4. then 1.) while the curve moved; during animation the slider box was not drawn while the menu was open, and the menu item read "Stop Animate". Stopping left a = -4.
- 2 Minimize: the panel became a small row "[<] [>] a =-4." (two arrow buttons, then the value); the menu item then read "Maximize".
- Menu > 1 Actions list: 1 Pointer, 2 Select (submenu), 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw.
- Actions > B Insert Slider: the same Slider Settings dialog, Variable defaulted to v1, Value 1, Minimum -5, Maximum 5.
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## D17 Table (run 2, page 1.5)
Settings: RAD, Graphs page with f(x)=x^2-2, then ctrl+T.
Observed:
- ctrl+T opens the table: the page splits into graph (left) and table (right); the table has an x column (grey) and the function column with header "f5(x):=" and its expression "x^2-2" in a second header row, a small triangle at the right of the header; cursor starts in the first function cell. The first view showed rows from 1.; pressing Up showed 0., then -1., -2., -3. : the table scrolls upward with no limit at the top (negative x values appear).
- Menu in the table pane has only 1 Actions and 2 Table. Table submenu: 1 Remove Table (Ctrl+T), 2 Delete Column, 3 Choose..., 4 Edit Expression, 5 Edit Table Settings....
- 3 Choose...: a list of every function and relation in the problem (f1..f5, rel1..rel4 and more below), not only this page's; picking f2 replaced the highlighted column's function with f2(x) = x^3-3*x.
- Right arrow from the last function column opens the same chooser straight away for a new column; picking f3 then f2 gave three columns (x, f3, f2); the pane shows only two at a time and scrolls sideways.
- 5 Edit Table Settings...: dialog "Table": Table Start (-4. at that moment), Table Step (1.0), Independent (Auto), Dependent (Auto), OK, Cancel.
- Closing: ctrl+T again, or Table > 1 Remove Table (not tried).
- The key that opened it was ctrl+T (check 4's accidental open came from Menu 6 3 in a different page).
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## D19 View items (run 2, page 1.6)
Settings: RAD, Graphs page with f(x)=x^2. Keys: Menu (clicked) 2 View, then the digit; wait 1 s between digits.
Observed:
- View menu: 1 Graphing (greyed), 2 Plane Geometry, 3 3D Graphing, 4 Hide Analytic Window (greyed), 5 Hide Axes, 6 Grid (submenu), 7 Show Entry Line (Ctrl+G), 8 Hide Axes End Values, 9 Hide Object Selection Guides.
- Grid submenu: 1 No Grid (greyed while no grid), 2 Dot Grid, 3 Lined Grid. Dot grid: small dots at each tick position. Lined grid: thin grey lines at each tick, axes drawn over them.
- 5 Hide Axes: axes, tick marks and all numbers vanished (grid stayed); the menu then read 5 Show Axes and 8 Hide Axes End Values was greyed.
- 7 Show Entry Line: an entry row "f7(x)=" (checkbox, expression, list icon) appeared at the top, pushing the graph down; the item then read Hide Entry Line.
- 8 Hide Axes End Values: -10, 10, 6.67, -6.67 labels removed; the "1" tick labels stayed; the item then read Show Axes End Values.
- 9 Hide Object Selection Guides: no visible change on this page; the item then read Show Object Selection Guides.
- All of these were toggled back at the end except the lined grid (still on this page) and the entry line (hidden again).
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## Lists update (after D14, D15, D16, D17, D19)
- Run since the lists above: D14 (prompts for Maximum, Intersection, Bounded Area, conics submenu; Bounded Area flow not completed), D15, D16, D17, D19.
- Still not run: D1–D11, D18, D20–D25, D29, D31–D33, the D13 piecewise template.
- Extra open documents on the emulator: Document6–Document11 (blank/test); Document11 holds pages 1.1–1.6 of these captures.

## D20 Point On (run 2, page 1.7)
Settings: RAD, Graphs page with f(x)=x^2 (labelled f7).
Keys: Menu 8 Geometry, 1 Points & Lines, 2 Point On; clicks on the screen; Return.
Observed:
- Points & Lines submenu: 1 Point (p), 2 Point On, 3 Point by Coordinates (p), 4 Intersection Point(s), 5 Line, 6 Segment, 7 Ray, 8 Tangent, 9 Vector, A Circle arc (more below; list not scrolled).
- Choosing 2 sets the tool (icon of a point on a line at the top left). Pointing at the curve shows a hover label "graph f7 [tab]"; at the origin it showed "intersection point [tab]" and a grey (0,0) and the curve and axis turned dotted (preview), and no point was placed by one press of the centre key.
- Clicking on the curve with the mouse: first click showed a preview (curve drawn dotted, black dot, label "point on", grey coordinates "(2.06, 4.25)"); a second click at the same spot fixed it: coordinates turned black, curve solid again, hover label "point on [tab]".
- Dragging was not tried. Double-clicking the coordinate label showed hover "text [tab]" and typing a digit did nothing; Return then put the x value (2.06) in an edit box (highlighted). Typing 3 (key press, not the type action) replaced it with "3" in a box; Return accepted and the point left the screen (y = 9 is above the 6.67 window top), consistent with moving to x = 3 on the curve.
- Esc (on-screen) leaves the tool.
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## D21 Attributes of a graph (run 2, page 1.7)
Settings: RAD, f(x)=x^2 graph. Keys: Menu 1 Actions, 4 Attributes; mouse click on the curve; Down arrow between attributes.
Observed:
- After choosing Attributes (icon top left) pressing Return or the centre key near the curve only gave the hover label "graph f7" and made the curve thick (selected); a mouse click on the curve opened the attribute bar.
- The bar is a vertical strip of icons beside the curve with a blue box on the current one and a yellow tooltip: first "(1/3) Line weight is thin"; Down: "(1/3) Line style is continuous"; Down: "(3/5) label style" (icon "fo..."); Down: "(1/2) Label parameters: Show names" (icon "a"); Down: "(1/2) Graph is continuous" (icon a parabola). Down on the last one stayed on it. Small arrows to the right of the box show Left/Right change the value. A down-arrow under the strip and an up-arrow above it appear when the strip scrolls.
- Left/Right changes were not tried.
Screenshot: none saved.
Differs from CASSim or from this file's expectation? Not compared yet.

## D24 Degree document, Graphing Angle Auto (run 2, page 1.8)
Settings: Document Settings Angle changed Radian -> Degree (title bar showed DEG); Graphs & Geometry Settings (Menu 9) read Display Digits Float 3, Graphing Angle Auto, Geometry Angle Degree, Grid No Grid, [ ] Automatically hide plot labels, [x] Show axes end values, [ ] Show tool tips for function manipulation (list scrolls).
Observed: `sin(x)` in the standard window (-10 to 10) drew an almost flat line close to the x axis, rising very slightly to the right: the graph used degrees. Document Settings list: Display Digits, Angle (Radian, Degree, Gradian), Exponential Format, Real or Complex, Calculation Mode, CAS Mode, Vector Format, Base, Unit System (SI); there is no Graphing Angle in it.
Screenshot: none saved. Differs from CASSim or from this file's expectation? Not compared yet.

## D25 Messages (run 2, pages 1.9)
Observed:
- `t^2` entered as a function (typed t^2, Return): a dialog "Create Sliders", "Create a slider for:", a ticked box "t", OK and Cancel; the entry's checkbox was red. Esc/Cancel removed the entry and drew nothing; the entry line moved on to the next free name.
- `k*x`: the same dialog for "k"; OK created a slider "k =1." (-5. to 5.) and drew a thick line y = kx, label "f10(x)=k·x" (thick, as selected).
- No error message text appeared for either.
- Not run: the last f slot (f99), the name label "f10(x)=" could not be edited.
Screenshot: none saved. Differs from CASSim or from this file's expectation? Not compared yet.

## D23 not run (Text, Coordinates and Equations, Hide/Show, Delete All, Redefine): only the Actions list was seen (D16).

## Lists update 2 (end of this session)
- Run: D12, D13 (two forms), D14, D15, D16, D17, D19, D20, D21, D24, D25 (not f99), D26, D27, D28, D30.
- Not run: D1–D11, D18, D22, D23 (labels and prompts only seen as lists), D29, D31–D33, the D13 piecewise template, D25 f99.
- Desktop state: Document11 is on page 1.9 with Radian restored (Degree was used for D24 and switched back).
