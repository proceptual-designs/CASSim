# Emulator check 5, Part D: Graphs (partial)

Handheld view, CX II-T CAS 6.0.3.374. Settings: Radian, Automatic, Real, Float 8 (document); Problem 2 page 2.1 (Graphs), `f1(x)=x^2`, `f2(x)=sin(x)` typed in the entry line.
Screenshots: not saved for this part (observations transcribed from zoomed views only).

### D1 Graphs menu (menu key)
Settings: Graphs page, entry line open.
Keys: menu key, then Right/Left/Down to open each submenu.
Observed:
- 1 Actions ▶; 2 View ▶; 3 Graph Entry/Edit ▶; 4 Window / Zoom ▶; 5 Trace ▶; 6 Analyze Graph ▶; 7 Table ▶; 8 Geometry ▶; 9 Settings…
- 1 Actions: 1 Pointer, 2 Select ▶, 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw (list ends at C; scrolls with a ▼ arrow).
- 2 View: 1 Graphing (grey), 2 Plane Geometry, 3 3D Graphing, 4 Hide Analytic Window (grey), 5 Hide Axes, 6 Grid ▶, 7 Show Entry Line (Ctrl+G), 8 Hide Axes End Values, 9 Hide Object Selection Guides.
- 3 Graph Entry/Edit: 1 Function, 2 Relation, 3 Equation Templates ▶, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▶, 8 Diff Eq.
- 4 Window / Zoom: 1 Window Settings…, 2 Zoom - Box, 3 Zoom - In, 4 Zoom - Out, 5 Zoom - Standard, 6 Zoom - Quadrant 1, 7 Zoom - User, 8 Zoom - Trig, 9 Zoom - Data, A Zoom - Fit, B Zoom - Square, C Zoom - Decimal (list ends at C; scrolls).
- 5 Trace: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▶, 5 Geometry Trace, 6 Erase Geometry Trace (grey).
- 6 Analyze Graph: 1 Zero, 2 Minimum, 3 Maximum, 4 Intersection, 5 Inflection, 6 dy/dx, 7 Integral, 8 Bounded Area, 9 Analyze Conics ▶.
- 7 Table: 1 Split-screen Table (Ctrl+T), 2 Remove Table (Ctrl+T, grey when no table).
- 8 Geometry: 1 Points & Lines ▶, 2 Shapes ▶, 3 Measurement ▶, 4 Construction ▶, 5 Transformation ▶ (more items below not scrolled).
- 9 Settings… opens "Graphs & Geometry Settings": Display Digits Float 3, Graphing Angle Auto, Geometry Angle Degree, Grid No Grid, checkbox Automatically hide plot labels (off), Show axes end values (on), more below (scrollbar), OK / Cancel.
Differs from CASSim or expectation?: for the builder to compare; not checked against code.

### D8 Zoom modes: Window Settings after each (default start: XMin -10, XMax 10, YMin -6.6666666666667, YMax 6.6666666666667, XScale Auto, YScale Auto)
- Zoom - Quadrant 1 (with f1=x^2): XMin -4, XMax 20, YMin -2.6666666666667, YMax 13.333333333333; axes at left/bottom.
- Zoom - Trig: XMin -2·π, XMax 2·π, YMin -4.1887902047864, YMax 4.1887902047864 (x end labels shown as -2·π, 2·π; y end labels 4.19).
- Zoom - Data (f1, f2 only, no data): XMin -7.2831853071796, XMax 7.2831853071796, YMin -5.1887902047864, YMax 5.1887902047864 (applied after Trig).
- Zoom - Fit (after Data): XMin/XMax unchanged -7.2831853071796 / 7.2831853071796, YMin -5.3041698312765, YMax 58.349238950535.
- Zoom - Decimal: XMin -32, XMax 32, YMin -21.3, YMax 21.3.
- Zoom - Standard, Square, In, Out, Box, User: not run.
Note: the Window Settings dialog has fields XMin, XMax, XScale (Auto drop-down), YMin, YMax, YScale (Auto drop-down), OK, Cancel.

### D3/D18 Function entry
Keys: Graphs page opens with entry line `f1(x)=`; typing `x^2` then Right, Return plots a thick blue curve with the label `f1(x)=x²`; Down moves to `f2(x)=`.

### D14 Analyze Graph > Zero prompts
Keys: menu 6 Analyze Graph, Right, 1 Zero (f1=x^2, Zoom - Standard window).
Observed: toolbar badge "zero" top left; a dotted vertical line follows the cursor; bottom-left prompt `lower bound?`; Return sets it and the prompt becomes `upper bound?`. Both bounds set at nearly the same point left of the curve (Return, Right x3, Return): dialog "Error / No zero found within the specified bounds" with OK. Redone with lower bound at the start position and the upper bound moved Right 15 steps: the point is marked with label `zero` and coordinates `(0,0)` drawn as a large (0,0). Escape leaves the tool.

### D17 Table (Ctrl+T)
Keys: Ctrl+T on the Graphs page.
Observed: split screen, graph left, table right. Columns: `x` and `f1(x):=` with the formula row `x^2`; rows 1. 4. 9. 16. 25 for x = 1. 2. 3. 4. 5 (shown with decimal points here though the document is Automatic). Entry strip at the bottom of the table showing `1`. f2 not shown as a column yet.

### D12/D13 Discontinuities and domains (standard window)
Keys: Ctrl+G opens the entry line; Up/Down move between function numbers (Up from f1 wraps to `f99`, Down from f99 stays); Return plots and closes the line. Note: Down from `f1` after plotting did not give f2 here; the entry line shows the next free number (f4 after f3 was auto-used), so `sin(x)` typed earlier was not plotted (it went nowhere).
- `f4(x)=1/x`: two hyperbola branches, no vertical asymptote line, branches run off the top/bottom edge near x=0; label drawn as a stacked fraction `f4(x)=1/x` in magenta. New curves take the next colour (f1 blue, f4 magenta, f3 black).
- `f99(x)=tan(x)` (typed in line 99): steep branches, no asymptote lines drawn, drawn blue; label `f99(x)=tan(x)`.
- `f3(x)=√(x)` : curve starts at x=0 and exists only for x>=0 (nothing drawn for x<0); label `f3(x)=√x`.
Screenshot: none saved.

### D15 Relation entry
Keys: menu 3 Graph Entry/Edit, Right, 2 Relation.
Observed: entry line shows `rel1(x,y)` label with a second text field below it. Typing `x^2` then `+y^2=9` without leaving the exponent gives y^(2=9): error dialog "Invalid Input" listing supported relation inputs (TI text, do not reuse; it lists relations using ≤ < = > ≥, polynomial relations in x and y, relations equivalent to y=f(x) or x=g(y), restricted domains, with examples such as `x+3y=4`, `y=sin(x) and -2π<x≤2π`, `x^2+y^3=4| x≥0 and y≥0`). Retyped as `x^2`, Right, `+y^2`, Right, `=9`, Return: a thick blue circle radius 3 is drawn, labelled `x²+y²=9` (no `rel1` label).

### D16 Insert Slider
Keys: menu 1 Actions, Right, B Insert Slider.
Observed: dialog "Slider Settings": Variable `v1` (drop-down), Value `1`, Minimum `-5`, Maximum `5`, Step Size Automatic (drop-down), Style Horizontal (drop-down), Display Digits Float 3 (drop-down), checkboxes Minimized (off), Show Variable (on), Show Scale (on), OK/Cancel. After OK a horizontal slider `v1=1.` with scale -5 to 5 appears at the top right overlapping the graph, in a selected box with handles; Escape leaves placement.

### D23 Actions > 6 Delete all
Keys: menu 1 Actions, Right, 6. Dialog "Delete all" with the text "Are you sure you want to delete everything?" and buttons Yes (default, highlighted) and No. After Yes: all functions, the relation and curves are removed, BUT the slider `v1` stays on the page, and the entry line shows `rel1(x,y)` (the last-used type) with a text field; typing a function there does not plot it as a function. Use menu 3 Graph Entry/Edit > 1 Function for a function line; each use takes the next free slot (`f1` reused first, then f2, f3, ...).

### D12 Discontinuities, more (standard window; each plotted with a new colour in order blue, red, black, magenta, green, orange)
- `1/(x-1)^2` (f1): blue curve rising to the top on both sides of x=1, no vertical line, label drawn as a stacked fraction `f1(x)=1/(x-1)²`.
- `floor(x)` (f2): separate red horizontal segments, one per integer step, drawn thick and flat; no vertical connectors and no open or closed end circles; label `f2(x)=floor(x)`.
- `abs(x)/x` (f3): black horizontal line y=1 for x>0 and y=-1 for x<0, nothing at x=0 and no join; label drawn as `f3(x)=|x|/x` stacked.
- `ln(x)` (f4): magenta curve only for x>0, running off the bottom edge near x=0; label `f4(x)=ln(x)`.
- `√(4-x^2)` (f5, typed `√(4-x^2` Right `)`): green upper semicircle from x=-2 to 2, no end circles; label `f5(x)=√(4-x²)`.
- Labels of different functions overlap near the right of the screen and over the slider; no automatic avoidance seen.

### D13 Restricted domain
`x^2|x>0` (menu 3 1, type `x^2`, Right, `|x>0`): the orange curve is drawn only for x>0 with no circle at the open end; the label reads as a brace form `f6(x)={x², x>0}` (partly hidden under other labels).
`x^2|-1<x<2` and the piecewise template: not run.

### D14 Analyze Graph prompts (f1=4-x², f2=x+1, Standard window, slider v1 on page)
Keys: menu 6 Analyze Graph, Right, then the number. Mouse clicks on the graph set the points (arrow keys moved the SLIDER, not the cursor, when a slider was on the page; Tab also selected the slider).
- 3 Maximum: toolbar badge "max"; first prompt `graph?` (two graphs on the page; hovering a graph shows the tooltip `graph f1`); after clicking f1: `lower bound?` (dotted vertical line follows the pointer), then `upper bound?`; result: a black dot at the top with label `(0,4)`, drawn as big brackets.
- 4 Intersection: badge icon; goes straight to `lower bound?` then `upper bound?` (no `graph?` prompt with two graphs); result: dot with label `(1.3,2.3)` (the true value 1.30278 shown to 2 sig. dp), and a small tooltip `text` near it.
- 8 Bounded Area: prompts `lower bound?`, `upper bound?` (no graph prompt); result: a grey shaded region between f1 and f2 with the value `5.8` printed in it, black dots at the bounds. (Bounds were clicked at about x=0 and x=-1.5, not the true intersections; value is for the clicked bounds.)
- 9 Analyze Conics submenu: 1 Center, 2 Vertices, 3 Foci, 4 Axes of Symmetry, 5 Directrix, 6 Asymptotes, 7 Radius, 8 Eccentricity, 9 Latus Rectum (all enabled with a function page; prompts not run).
- Coordinate label after Minimum: not run.

### D8 Zoom - Box and Zoom - Out (more)
- Zoom - Box (menu 4, Right, 2): toolbar badge (magnifier with dotted box); a yellow tooltip `1st corner?` next to a magnifier pointer; after the first click it becomes `2nd corner?`; after the second click the window zooms to the box and the tool restarts at `1st corner?` (stays in Box mode until Esc). Box corners clicked at screen (850,330) and (1100,520): Window Settings after: XMin -2.7044025157233, XMax 3.9622641509434, YMin -0.9433962264151, YMax 4.0880503144654 (the box was fitted to the aspect ratio of the screen).
- Zoom - Out (menu 4, Right, 4): magnifier badge with minus; yellow tooltip `Center?`; one click re-centres on the clicked point and doubles the window width and height. From the Box window above (width 6.6666666666667, height 5.0314465408805) the Window Settings after one click: XMin -6.0377358490567, XMax 7.2955974842767, YMin -3.12685415925, YMax 6.936038922511 (width 13.333333333333, height 10.062893081761); the tool stays active (still shows `Center?`) until Esc.
- Zoom - In, User, Data (with scatter) and Fit on x²: not run.

### D19 View items
Keys: menu 2 View, Right, then the number.
- 6 Grid ▶: 1 No Grid (greyed when current), 2 Dot Grid, 3 Lined Grid. Dot Grid: small grey dots at each tick intersection (one per scale step). Lined Grid: thin light-grey lines at each tick step across the whole plot. The grid stays when axes are hidden.
- 5 Hide Axes: axes, tick marks, end values and the `x`/`y` labels disappear; the grid and the curves stay; the menu item becomes `5 Show Axes`, and `8 Hide Axes End Values` turns grey (key 8 does nothing and the menu stays open). Show Axes restores them.
- 8 Hide Axes End Values: removes the end labels (-10, 10, 6.67, -6.67); the `1` tick labels and the `x`, `y` axis letters stay. Choosing it again restores them (the menu item text changes to Show Axes End Values after).
- 7 Show Entry Line (Ctrl+G): toggles the entry line (not re-shot).
Screenshots: none saved.

### D21 Attributes (menu 1 Actions > 4 Attributes)
Settings: Radian, Automatic, Real, Float 8; page 2.1 with f1=4-x², f2=x+1, bounded area shaded.
Keys: Menu 1, Right, 4; click an object (a small selection cursor with a grab icon appears and a tooltip names the object, e.g. `(1/13) Circle`, `point`, `bounded area`); Return opens the attribute chooser; Down/Up moves between attributes; Left/Right changes the value; Return accepts; Escape closes.
Observed: after Return on the bound line the chooser showed, in order, `(1/3) Line weight is thin` (3 weights, a hatched-line icon) and `(1/3) Line style is continuous`; Right gave `(2/3) Line style is dotted` and after Return the selected line was drawn dotted. The tooltip format is `(n/N) <attribute> is <value>`. Which object receives the change depends on what the cursor was on when clicked (here the vertical bound line, not the curve).
Screenshot: not saved separately (tooltips seen in zooms only).
Differs from CASSim or from this file's expectation? Attribute list depends on the object type; only line weight and line style were seen for the bound line. Colour and other attributes not checked.

### D20 Point On (menu 8 Geometry > 1 Points & Lines > 2 Point On), on f1
Settings: Radian, Automatic, Real, Float 8; page 2.1 with f1=4-x², f2=x+1.
Keys: Menu 8, Right, 2. Points & Lines list: 1 Point (p), 2 Point On, 3 Point by Coordinates (p), 4 Intersection Point(s), then 5 Line, 6 Segment, 7 Ray, 8 Tangent, 9 Vector, A Circle arc (more below; list continues). Same menu level shows Shapes, Measurement, Construction, Transformation as further submenus.
Observed: the cursor (a hand) over the curve shows the tooltip `graph f1` and the curve is drawn thicker. Return on it dropped a point on the curve labelled with live coordinates, about (1.05, 2.9), and the cursor tooltip read `point on` with the `tab` chip. A click that missed the curve placed nothing and the tooltip stayed `text`/empty.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The point is constrained to the curve (coordinates follow f1). Dragging it was not tried.

### D17 Table details (Ctrl+T, Table menu, Edit Table Settings)
Settings: Radian, Automatic, Real, Float 8; page 2.1 with f1=4-x², f2=x+1.
Keys: Ctrl+T (opens the split-screen table on the right half; graph stays on the left, squeezed); Menu shows `1 Actions ▶` and `2 Table ▶` (graph menu items are replaced by the table's). Table ▶: 1 Remove Table (Ctrl+T), 2 Delete Column, 3 Choose..., 4 Edit Expression, 5 Edit Table Settings...
Observed: columns are `x` then `f1(x):=` (header row shows the expression `4-x^2` in a formula row) then `f2(x):=` (`x+1`); Right moves to the next function column. Default rows start 1., 2., ... with f1 values 3., 0., -5., -12., -21. Edit Table Settings dialog `Table`: Table Start (0.), Table Step (1.0), Independent (Auto ▶), Dependent (Auto ▶), OK, Cancel. Entering Start -2 and Step 0.5 gave rows -2., -1.5, -1., -0.5, 0.,... with f1 0., 1.75, 3., 3.75, 4. and f2 -1., -0.5, 0., 0.5, 1. Entry line at the bottom of the table shows the selected cell value.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Ctrl+T is the key route (also via Menu > Table > Split-screen Table).

### D16 Slider offer: f3(x)=a*x^2
Settings: Radian, Automatic, Real, Float 8; page 2.1 (already holds a slider v1).
Keys: Ctrl+G, Menu 3 > 1 Function, typed `f3(x)=a*x` then `^2` then Right, Return. Typed `a*x` alone on a line with the prefix removed, then `f3(x)=` typed in front, plainly gave a line `f3(x)=a·x²`.
Observed: Return on the line opened a dialog `Create Sliders` with text `Create a slider for:` and a ticked checkbox `a`, buttons OK and Cancel. OK created a slider `a =1.` with a track from -5. to 5. (a small box with two end handles, selected), placed at the bottom left of the graph; the parabola y=a·x² was drawn in black at once (a=1). The entry-line function chooser (Ctrl+G with the entry line already closed) showed a drop-down `1 f1`, `2 f2`, `3 f3` (f2 red, f3 selected).
Also seen: an earlier mistyped line `a·x(x)=a·x²` (a stray `a·x` left in front of `(x)=`) gave an Error dialog `Reserved name` with an OK button (x used as a function name). TI text: `Reserved name` (short; fine to reuse).
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The slider name is the variable name (`a`), with defaults value 1, range -5 to 5.

### D25 Undefined variable and wrong variable
Settings: Radian, Automatic, Real, Float 8; page 2.1 with f1, f2, f3=a·x² and slider a=1.
Keys: Ctrl+G, Menu 3 > 1 Function (opens the next free slot), typed the body, Return.
Observed:
- `f4(x)=k*x` (k undefined): Return opened `Create Sliders` / `Create a slider for:` with a ticked box `k`, OK and Cancel. Escape (cancel) closed the entry line, drew nothing and left f4 occupied: the next Menu 3 > 1 Function opened `f5(x)=`, not `f4`.
- `f5(x)=t^2` (t instead of x): the same dialog appeared with box `t`. OK created a slider `t` (default 1., range -5..5, placed top left over slider a) and drew the line `f5(x)=t²` as a horizontal green line at y=1. No error is shown, the function is just constant in x.
- A line typed with `x(x)=` in front gave Error `Reserved name` (see D16).
Last f slot: Up from f1 wraps to f99 (seen earlier, D5 not otherwise run).
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Any undefined name other than x in a function line triggers the slider offer rather than an error.

### D22 Entry-line types (Menu 3 Graph Entry/Edit)
Settings: Radian, Automatic, Real, Float 8; page 2.1 (Problem 2, so Problem 1's `xs`/`ys` are not visible; literal lists used instead).
Keys: Menu 3 then the number; the entry line opens in the new type. Menu 3 list: 1 Function, 2 Relation, 3 Equation Templates ▶, 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence ▶ (1 Sequence, 2 Custom), 8 Diff Eq.
Observed entry lines:
- 4 Parametric: `x1(t)=` / `y1(t)=` / `0≤t≤6.28 tstep=0.13`.
- 5 Polar: `r1(θ)=` / `0≤θ≤6.28 θstep=0.13`.
- 6 Scatter Plot: `s1  { x←` / `y←`, two fields (Tab between). Typed `{1,2,3,4}`, Tab, `{2,3,5,4}`, Return: four blue dots plotted and the label `s1:user-defined` drawn in blue italics. (Typing `xs`/`ys` from another Problem was not run.)
- 7 > 1 Sequence: `u1(n)=` / `Initial Terms:=` / `1≤n≤99 nstep=1`. 7 > 2 Custom: `p1  { x←` / `y←` / `1≤n≤99 nstep=1`.
- 8 Diff Eq: a different layout: a tick box and `y1` with the equation field `y1' =` (primed), `(x0,y1₀):  ( <x> , <y> )` with a magnifier icon, and a `d1:` row label. Menu `...` at the right.
- 3 Equation Templates ▶: 1 Line ▶ (1 Line Slope Intercept y=m·x+b, 2 Vertical Line x=c, 3 Line Standard a·x+b·y=c); 2 Parabola ▶ (1 Vertex form y=a·(x-h)²+k, 2 Standard form y=a·x²+b·x+c, 3 Vertex form x=a·(y-k)²+h, 4 Standard form x=a·y²+b·y+c); 3 Circle ▶ (1 Center form (x-h)²+(y-k)²=r², 2 Standard form a·x²+a·y²+b·x+c·y+d=0); 4 Ellipse ▶ (1 Center form (x-h)²/a²+(y-k)²/b²=1); 5 Hyperbola ▶ (1 East-West, 2 South-North, both over a²/b²); 6 Conic ▶ (1 General a·x²+b·x·y+c·y²+d·x+e·y+f=0).
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Equation Templates not yet entered (labels only); the scatter label `s1:user-defined` is the default for literal lists.

### D2 Context menus (right-click)
Settings: Radian, Automatic, Real, Float 8; page 2.1 with several objects.
Keys: right-click at the spot on the handheld screen.
Observed:
- Empty space: 1 Recent ▶, 2 Hide/Show ▶, 3 Select ▶, 4 Window / Zoom ▶, 5 Text, 6 Delete all, 7 Erase Geometry Trace (grey), 8 Pin.
- Slider (right-click on slider v1): 1 Move, 2 Settings..., 3 Minimize, 4 Animate, 5 Delete.
- A graph (f1, tooltip `graph f1`): 1 Recent ▶, 2 Label (grey here), 3 Attributes, 4 Hide, 5 Delete, 6 Edit Relation (this is the Edit label shown for a function graph), 7 Trace ▶, 8 Analyze Graph ▶, 9 Table ▶, A Pin (grey), B Color ▶, C Conditions... (the list scrolls, with an arrow at the top and bottom; the end of the list was not seen beyond C).
- Y axis: 1 Recent ▶, 2 Attributes, 3 Hide/Show ▶, 4 Window / Zoom ▶, 5 Pin, 6 Color ▶, 7 Conditions...
- With several objects selected (tooltip `multi-select`): 1 Group (grey), 2 Delete, 3 Pin (grey), 4 Color ▶, 5 Conditions...
Not run: right-click on a point alone, a graph label alone, and the entry line.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The menu items depend on the object under the click. The curve menu says `Edit Relation` on the function graph (reading from the zoom; check against later screenshots).

### D11 Trace (Menu 5 Trace) and D1 Path Plot
Settings: Radian, Automatic, Real, Float 8; page 2.1, Standard window x -10..10, f1=4-x², f2=x+1 plus extras.
Keys: Menu 5, 1 (Graph Trace), Right x3, Up; Escape leaves. Trace submenu: 1 Graph Trace, 2 Trace All, 3 Trace Step..., 4 Path Plot ▶, 5 Geometry Trace, 6 Erase Geometry Trace (grey). Path Plot ▶: 1 Function, 2 Parametric, 3 Polar, 4 Path Setup...
Observed: Graph Trace starts on f1; after three Right presses the label read `f1: (0.9, 3.19)` at the bottom with a small circle on the curve (so the automatic step is 0.3 here); Up moved to f2 and the label read `f2: (0.9, 1.9)` with a red circle. Trace Step... dialog `Trace Step` with a field `Automatic` (drop-down), OK, Cancel.
Not run: Trace All, Path Setup, Path Plot runs, typing a value in the trace, tracing the scatter plot.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The trace label is `<name>: (x, y)` in the colour of the function, placed at the lower right of the screen.

### D15 (rest) Inequalities and a vertical line
Settings: Radian, Automatic, Real, Float 8; page 2.1, Standard window.
Keys: Ctrl+G, Menu 3 > 2 Relation, typed the line (`y<x+1`; `y>=x` then `^2` then Right; `x=3`), Return. `>=` typed in ASCII shows as ≥.
Observed:
- `y<x+1`: the half-plane below the line is shaded in translucent blue (the next free relation colour), with a thick solid boundary line, label `y<x+1` placed in a white box near the origin.
- `y≥x²`: the region above the parabola shaded in translucent red, boundary thick; label `y≥x²`.
- `x=3`: a vertical black line at x=3, label `x=3`.
No error dialogs. Overlaps blend (translucent shading). Whether strict `<` draws a dashed boundary was not distinguishable in the zoom (boundary looked solid).
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Inequality regions are shaded areas with a bold edge, not a plotted curve only.

### D24 Degree document with Graphing Angle Auto, `sin(x)`
Settings: Document Settings Angle changed Radian to Degree (title bar shows DEG); Graphs & Geometry Settings seen at Display Digits Float 3, Graphing Angle Auto, Geometry Angle Degree, Grid No Grid, tick boxes `Automatically hide plot labels` (off) and `Show axes end values` (on), OK, Cancel (the list scrolls).
Keys: Menu 1 > 6 Delete all (dialog `Delete all` / `Are you sure you want to delete everything?` / Yes, No), Menu 9 (settings seen, then Escape), doc, 7, 2 (Angle drop-down: Radian, Degree, Gradian), Ctrl+G, Menu 3 > 1, `sin(x)`, Return.
Observed: label `f1(x)=sin(x)`; in the Standard window (x -10..10) the curve is almost flat along the x axis (sin in degrees reaches only about 0.17 at x=10). Graphing Angle Auto follows the document angle. Slider `v1` and `a` remain after Delete all (sliders are not deleted).
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Graph angle follows the document (Degree) when set to Auto.

### D6 `f1` used on a Calculator page (new page 2.2, same Problem 2, Degree)
Keys: Ctrl+I, 1 (Add Calculator); typed `f1(30)`, `f1(x)`, `f2(1)` with Return.
Observed: `f1(30)` gives ½ (stacked fraction, Degree); `f1(x)` gives `sin(x)`; `f2(1)` echoes `f2(1)` unevaluated because f2 was deleted by Delete all (no error).
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Graph functions are ordinary variables on the Calculator page within the same Problem.

### D9 Pan and rescale (mouse)
Settings: Degree document, page 2.1, window started at x -10..10, y -6.67..6.67 (Standard), f1=sin(x), sliders v1 and a on the page.
Keys: mouse drags on the handheld screen.
Observed: dragging on empty space pans without changing the width: a drag of 100 px left and 60 px up gave x -7.3..12.7, y -8.24..5.09 (width still 20); a second drag gave x -4.65..15.35 and a third x -6.23..13.77. Axis end values are shown at the ends (`-7.3`, `12.7`, `5.09`, `-8.24`). A drag that starts on a slider moves the slider (v1 went from 5 to 3). Clicking the slider's end value (`5.`) opens an editable box on the slider range and typing 30 set the range to -5..30 (this edits the slider, not the axis). Mouse wheel scroll over the graph did nothing. Axis rescaling by dragging the axis or editing the axis end value was not reached because the sliders sit over the axis end values on this page.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Pan keeps scale; rescale not captured.

### D13 (rest) `x^2|-1<x<2` and piecewise
Settings: Degree document, new Graphs page 2.2 (functions numbered on from f2 because f1 is used on page 2.1; the add-page menu was: 1 Add Calculator, 2 Add Graphs, 3 Add Geometry, 4 Add Lists & Spreadsheet, 5 Add Data & Statistics, 6 Add Notes, 7 Add Vernier DataQuest™, 8 Add Widget, 9 Add Program Editor ▶, A Add Python ▶).
Keys: Menu 3 > 1 Function, then typed text. `^` trap: `x^2|-1<x<2` typed straight through put `,-1<x<2` inside the exponent (the label showed `x` with exponent `{2, -1<x<2`; the curve still drew only on -1<x<2). Correct entry: `x`, `^2`, Right, `|-1<x<2`.
Observed: `f3(x)=x^2|-1<x<2` plots a parabola only between x=-1 and x=2 (no end dots) and the label reads as a one-line piecewise `{x², -1<x<2` (a large brace, two stacked entries). `f4(x)=piecewise(x+1,x<0,x^2)` (typed `piecewise(`, `x+1,x<0,x`, `^2`, Right, `)`): label `{x+1, x<0 / x², Else` in magenta, drawing the line for x<0 and the parabola for x>=0.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The label shows `Else` as the closing case; a restricted-domain function is shown as a piecewise.

### D1 (rest) Actions menu in full, D23 Text / Hide/Show, D5 entry line, D4 keys, D10 labels
Settings: Radian, Automatic, Real, Float 8; Graphs page 2.2 with f3=x²|-1<x<2, f4 piecewise, f5 from LinRegMx.
- Actions (Menu 1) in full: 1 Pointer, 2 Select ▶ (1 Region, 2 Image grey, 3 Grid grey), 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, B Insert Slider, C MathDraw (the list scrolls; arrow at the bottom, Up from the top wraps to C).
- D23 Text (Menu 1 > 7): click an empty spot, type `note`, Return: the text `note` appears in italics at that spot; the tool icon (AbI) stays top left until Escape. Hide/Show (Menu 1 > 3): eye icon top left; hidden items are drawn ghosted; hovering gives the tooltip `text`; clicking the text hid it, Escape left the tool. Coordinates and Equations (8): tool icon `y=f(x)` top left; my clicks on the f4 line produced no label (not captured). Redefine (A): tool icon active; a click on the f4 line did nothing visible (not captured).
- D5 entry line: Ctrl+G opened `f5(x)=1.9·x+0.` (the next used slot, written by LinRegMx); Up went to `f4`: tick box ticked and the piecewise shown as `{x+1,x<0 / x², ▯` with an empty last case box; Down Down Down went to empty `f7(x)=`, one more Down `f8(x)=`; Escape closed the line.
- D4 keys and mouse: with no entry line, arrow keys moved the hand cursor over the graph (tooltip `label` with the `tab` chip when over f4's label); Return on a label selected/grabbed it (blue frame around the label); Escape released it; Ctrl+Right moved to the next page (2.3); the on-screen Menu key must be clicked; Ctrl+G toggles the entry line.
- D10 labels: hovering the f4 label shows the tooltip `label`; a label can be grabbed with Return and moved; the long piecewise label was drawn as a large brace with three lines. The `Automatically hide plot labels` setting was seen (off). Menu 2 Label item on a graph was grey.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? The cursor here is a hand moved by arrow keys, and the entry line keeps one slot per function with a tick box.

### D8 (rest) Zoom - Standard, In, Fit, Square, User on page 2.2 (functions f3, f4, f5 plotted)
Settings: Radian, Automatic, Real, Float 8; Window Settings dialog read with Menu 4 > 1 (fields XMin, XMax, XScale (Auto ▶), YMin, YMax, YScale (Auto ▶), OK, Cancel). Window / Zoom list: 1 Window Settings..., 2 Zoom - Box, 3 Zoom - In, 4 Zoom - Out, 5 Zoom - Standard, 6 Zoom - Quadrant 1, 7 Zoom - User, 8 Zoom - Trig, 9 Zoom - Data, A Zoom - Fit, B Zoom - Square, C Zoom - Decimal.
- Zoom - Standard: XMin -10, XMax 10, YMin -6.6666666666667, YMax 6.6666666666667.
- Zoom - In: prompt `Center?` (yellow tooltip); a click on the graph halves the window about that point (reading XMin -5 .. XMax 5, y -2.58 .. 4.09 after the click).
- Zoom - Fit (from x -5..5): XMin -5, XMax 5 unchanged; YMin -6.9004012506668, YMax 27.904413757335 (fits all plotted functions over that x range).
- Zoom - Square (from that window): XMin -5, XMax 5, YMin -1.3217330703775, YMax 5.3449335962892 (y range set so units are equal on screen).
- Zoom - User: returned to the earlier stored window (x -5..5, y -2.58..4.09 as after Zoom - In); no dialog.
Screenshot: zooms only, not saved as PNG.
Differs from CASSim or from this file's expectation? Fit keeps x and refits y only; User restores the stored user window.

## D1 (rest): Geometry submenus (Menu 8 on a Graphs page, page 2.1; half-scale JPEG zooms `pages-shots-5/d1-geom-00` to `d1-geom-07`)
Settings: Radian, Automatic, Real, Float 8. Keys: click Menu key, 8, then the digit for each group; Left closes one level.
Observed:
- 8 Geometry has five groups: 1 Points & Lines, 2 Shapes, 3 Measurement, 4 Construction, 5 Transformation.
- 1 Points & Lines: 1 Point (p), 2 Point On, 3 Point by Coordinates (p), 4 Intersection Point(s), a divider, 5 Line, 6 Segment, 7 Ray, 8 Tangent, 9 Vector, A Circle arc (the last item).
- 2 Shapes: 1 Circle, 2 Triangle, 3 Rectangle, 4 Polygon, 5 Regular Polygon, 6 Ellipse, 7 Parabola, 8 Hyperbola, 9 Conic by Five Points.
- 3 Measurement: 1 Length, 2 Area, 3 Slope, 4 Angle, 5 Directed Angle.
- 4 Construction: 1 Perpendicular, 2 Parallel, 3 Perpendicular Bisector, 4 Angle Bisector, 5 Midpoint, a divider, 6 Locus, 7 Compass, 8 Measurement transfer.
- 5 Transformation: 1 Symmetry, 2 Reflection, 3 Translation, 4 Rotation, 5 Dilation.
Differs from CASSim or from this file's expectation? The group contents were not in the earlier expectations; record as the build's menu. The items were not run (menu read only).

## Run
D1 (all menus with their list ends: Actions in full, View, Graph Entry/Edit, Window/Zoom, Trace, Analyze, Table, Geometry top level and all five Geometry groups, Settings), D2 (empty space, slider, graph, axis, multi-select menus), D4 (keys, mouse, page change), D5 (entry-line navigation), D6, D7 (not in the brief's rows; nothing to run), D8 (all zoom items except Data with a scatter plot), D9 (pan; rescale not obtained), D10 (label hover and grab), D11, D12, D13 (all three), D14, D15 (circle, inequalities, `x=3`), D16, D17, D19, D20, D21, D22, D23 (Text, Hide/Show, Delete all; Coordinates and Equations and Redefine seen as tools but no result), D24, D25, function entry.

## Not run (reason)
D8 Zoom - Data with a scatter plot (Standard, In, Fit, Square, User now recorded; Fit was on f3/f4/f5, not on `x^2` alone). D9 rescale by dragging an axis or an axis end value (sliders covered the end values; the attempts moved the slider). D23 Coordinates and Equations and Redefine results (clicks on the f4 line did not take). D22 scatter plot from `xs`/`ys` (Problem 1 variables not visible on a Problem 2 page) and Equation Template entries. Running any Geometry item (menus read only). Trace All, Path Setup, Path Plot runs. Right-click on a point alone, a label alone, the entry line.

## Also seen, not covered
Menu 7 Table has Remove Table greyed with no table open. Zoom - Data on a page with no data still changes the window. 4 Hide Analytic Window and 1 Graphing are greyed in View. The Attributes cursor selects whatever object is under the pointer, so choosing the curve versus its bound line needs the pointer tooltip checked first. A function typed with extra text left in front of `(x)=` gives `Reserved name`. Graph Trace label is drawn at the lower right as `<name>: (x, y)`. Clicking the status bar at (1150,793) before each key batch was needed to keep emulator focus. A regression command run from a Catalog wizard saves its equation into the next free graph function.
