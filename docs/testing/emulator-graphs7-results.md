# Emulator check 6, run 7: Part B (Graphs), observations only

Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, Keypad + SideScreen 250%. Settings: Float 8, Radian, Real or Complex Rectangular, Calculation Mode Auto, CAS On. Page 11.1 (Graphs) in Document1 (never saved). f1(x)=x^2, f2(x)=2*sin(x), f3(x)=x+1 entered (f1 first, f3 second by a keying slip, f2 third; they keep their f-numbers and colours: f1 blue, f2 red, f3 black). Screenshots: `pages-shots-7/R7-B<row>-<name>.png`. Writes in CASSim-evidence (Simon, 2026-11-27).

## Menus seen on the way (recorded, not a brief row)
- Top menu: 1 Actions ▶, 2 View ▶, 3 Graph Entry/Edit ▶, 4 Window / Zoom ▶, 5 Trace ▶, 6 Analyze Graph ▶, 7 Table ▶, 8 Geometry ▶, 9 Settings… (R7-B0-windowzoom-menu.png).
- 4 Window / Zoom: 1 Window Settings…, 2 Zoom - Box, 3 Zoom - In, 4 Zoom - Out, 5 Zoom - Standard, 6 Zoom - Quadrant 1, 7 Zoom - User, 8 Zoom - Trig, 9 Zoom - Data, A Zoom - Fit, then more below (a down arrow; not scrolled).
- 5 Trace: 1 Graph Trace, 2 Trace All, 3 Trace Step…, 4 Path Plot ▶, 5 Geometry Trace, 6 Erase Geometry Trace (grey) (R7-B0-trace-menu.png).
- Window Settings dialog: XMin, XMax, XScale (Auto), YMin, YMax, YScale (Auto), OK, Cancel. Default window: XMin -10, XMax 10, YMin -6.6666666666667, YMax 6.6666666666667 (R7-B2-window-default.png).
- Keying: ctrl+G shows/hides the entry line; Up/Down move between the f entries (a Down from f1 went to the first EMPTY entry).

## R7-B1 (Computer view): NOT RUN
Reason: it needs a second document in the Computer page size; not reached.

## R7-B2 Handheld axis drags, window x 0..10, y -2..5
Set via Window Settings: XMin 0, XMax 10, YMin -2, YMax 5 (R7-B2-window-set.png). The y axis then sits on the left edge, so only the x-axis drags were done.
1. First try: drag 50 px right from the x axis at about x=6.3. That point was on f2 where the curve crosses the axis, so the drag grabbed the CURVE: f2 became `f2(x)=2·sin(x-0.91)-0.044` (translated, label "graph f2" with a tab icon) and the window did not change. ctrl+Z restored `2·sin(x)`. Shots: R7-B2-drag-grabbed-curve.png, R7-B2-curve-restored.png. (So a drag on a function curve moves it; an axis drag must start where no curve is.)
2. Drag 50 px outward (right) from the axis at about x=8 (no curve there): the label "axes" shows and the window becomes XMin 0, XMax 8.9869565217391, YMin -1.7973913043478, YMax 4.4934782608696. Both axes shrank by the same factor 0.8987 about the origin (0,0): x 10 to 8.987, y -2 to -1.797 and 5 to 4.493. Shots: R7-B2-drag-out-view.png, R7-B2-drag-out-window.png.
3. Drag 50 px inward (left), starting at the new axis end: XMax 9.9614457831326, YMin -1.9922891566265, YMax 4.9807228915663 (factors 1.1085 on both axes, about the origin). Shot: R7-B2-drag-in-window.png.
4. A drag that starts on the axis line between tick marks (50 px right): XMax 8.9263157894737, YMin -1.7852631578947, YMax 4.4631578947369 (factor 0.8926 on both axes). Same behaviour as a tick start. Shot: R7-B2-drag-offtick-window.png.
Differs from CASSim? No: both axes rescale about the origin wherever the window is, and an off-tick start behaves the same. Note the drag start must avoid curves.
The y-axis drag and the Standard-window version of R7-B1 were not done.

## R7-B3 Graph Trace order (Standard window, Menu 5 1, x typed then Return)
Start on f1 at x=2 (f1: (2,4)): Up gives f3: (2,3); Down gives f1: (2,4); Down gives f2: (2,1.82); Down gives f3: (2,3). Shots R7-B3-x2-start/up/down1/down2/down3.png.
Start on f1 at x=-1 (f1: (-1,1)): Up gives f3: (-1,0) (the point is a zero and a yellow "zero" label shows); Down gives f1: (-1,1); Down gives f2: (-1,-1.68); Down gives f3: (-1,0) with the "zero" label. Shots R7-B3-xm1-start/up/down1/down2/down3.png.
Reading: Down follows the list order f1, f2, f3 and wraps to f1; Up goes to the previous graph and wraps from f1 to f3. At x=-1 the on-screen heights are f1 1, f3 0, f2 -1.68, so list order (f1 to f2) is NOT height order (f1 to f3): the order follows the list.
Differs from CASSim? No (CASSim: Up previous in the list, Down next). Runs 5 and 6 disagreed; this run follows the list.
Extra: typing a number in Trace and pressing Return moved the trace to that x on the current graph; a "zero" label appears when the trace lands on a zero.

## R7-B5 Zoom - Square
Setup: Window Settings XMin 0, XMax 10, YMin -1, YMax 3 (OK). Menu 4 Window/Zoom, item B Zoom - Square (the menu lists A Zoom - Fit, B Zoom - Square, C Zoom - Decimal; shot R7-B5-zoomwindow-menu-end.png).
Result (Window Settings after): XMin 0, XMax 10, XScale Auto, YMin -1.6666666666667, YMax 5, YScale Auto. Shot R7-B5-zoomsquare-window.png.
Reading: x range kept (0 to 10). y range went from 4 units (-1 to 3) to 6.6666666666667 units (-1.6666666666667 to 5), scale factor 5/3. The x axis stays at the same screen height (1/4 up from the bottom before and after), so y was scaled about the x axis (y=0), not about the centre of the old y range (the old centre y=1 would have given a different window).
Differs from CASSim? No (CASSim expectation: x kept, y scaled about the x axis).

## R7-B4 Zoom - Fit
Setup: window x 0..10 (after B5); graphs f1(x)=x², f2(x)=2·sin(x), f3(x)=x+1. Menu 4 Window/Zoom, A Zoom - Fit.
Result (Window Settings after): XMin 0, XMax 10 (unchanged), XScale Auto, YMin -12.2007997411759, YMax 110.208827088125, YScale Auto. Shots R7-B4-zoomfit-window.png, R7-B4-zoomfit-graph.png.
Reading: only y changes; x is kept. The y range covers all three graphs over x 0..10 (f1 reaches 100, f2 dips to about -2) with a margin each side: about 10.2 below -2 and about 10.2 above 100 (my arithmetic: roughly 10% of the data span, not stated by the emulator).
Differs from CASSim? Not compared in this run (no CASSim note to hand); numbers recorded for the comparison.

## R7-B6 Analyze Graph
Menu 6 Analyze Graph lists: 1 Zero, 2 Minimum, 3 Maximum, 4 Intersection, 5 Inflection, 6 dy/dx, 7 Integral, 8 Bounded Area, 9 Analyze Conics (submenu). Shot R7-B6-analyze-menu.png.
Setup note: page 11.1 held f1 x², f2 2·sin(x), f3 x+1 and extra graphs I added (f4, f5, f6, f7), so every Analyze command first asked "graph?" and I clicked the wanted curve. A first f4 typed as `x^2-4` became x^(2-4) (the exponent captured the -4); f5 = x²-4 was entered with the exponent left by Right. Bounded Area was redone on a clean page 11.2 (f8 x², f9 x+1) because labels overlapped on the cluttered page.
Prompts, in order: "graph?" (click a curve), then "lower bound?", then "upper bound?". A number typed then Return is accepted as the bound (a dotted vertical line shows the bound and the searched region is shaded grey). The prompt box text sometimes still read "lower bound?" in a screenshot taken just after the upper bound was typed (Integral, Inflection); I read that as a redraw lag, not a repeated prompt.
- Zero on f5 = x²-4, bounds -3 and 0: label "zero" with the coordinates (-2,0). Shots R7-B6-zero-graphprompt/lower/upper/result.png.
- Maximum on f6 = -x², bounds 1 and 3: label "maximum" at (1,-1), the lower bound's point (the function is decreasing there, no turning point inside). Shots R7-B6-max-graphprompt/lower/upper/result.png. Differs from CASSim? No (CASSim: Maximum at a bound marks the bound's point).
- Inflection on f7 = x³, bounds -1 and 1: label "inflection point" with (0,0). Shots R7-B6-infl-lower/upper/result.png.
- Integral on f1 = x², bounds 0 and 2: grey shading from 0 to 2 and the label 2.67 (the label is a bare number, no word "integral" seen). While the upper bound was being chosen a running value (0.883) showed. Shots R7-B6-integral-lower/upper/result.png.
- Bounded Area, x² and x+1, bounds -1 and 2 (clean page): first a Warning dialog appeared about Bounded Area and the Real or Complex setting (TI text, do not reuse). Shot R7-B6-boundedarea-warning.png. After OK, with only two graphs on the page there was NO "graph?" or "2nd graph?" prompt: it went straight to "lower bound?" (with a "point on" tooltip). On the cluttered page (several graphs) the prompts were "graph?", "2nd graph?", then "lower bound?" (shot R7-B6-boundedarea-2ndgraph.png). Typed -1 then 2 gave the label 2.23, shading between the two curves. Shots R7-B6-boundedarea-lower/upper/result.png.
Check on the warning (settled): I opened Document Settings after the Bounded Area runs and Real or Complex was Rectangular (the document was not set to Real as the brief asks for Methods rows; Angle Radian, Calculation Mode Auto, Float 8, CAS On were right). Shot R7-B6-docsettings-rectangular.png. I changed it to Real (shot R7-B6-docsettings-real.png) and re-ran Bounded Area: NO warning, it went straight to "lower bound?" (shot R7-B6-boundedarea-real-nowarning.png). So the warning belongs to Rectangular (and presumably Polar), not Real. All other Part B rows (B2 to B5 and the other B6 rows) ran under Rectangular; none showed a difference that I noticed, but I did not compare.
Labels: 2.67 and 2.23 are three significant figures; the zero, maximum and inflection coordinates were integers so no rounding showed.

## R7-B7 Kept trace point (Enter in Graph Trace)
Setup: clean page 11.2 (Real set, after B6), f8(x)=x² (this stands in for the brief's f1) and f9(x)=x+1. Menu 5 1 Graph Trace, typed 2 then Return: the trace sits on f8 at (2,4); a "f8: (2, 4)" readout shows at the bottom right. Shot R7-B7-trace-f8-x2.png.
Enter (Return) during trace: a label "(2, 4)" is placed beside the point and the point stays marked. Shot R7-B7-enter-kept.png.
Esc: the trace cursor and the readout go; the black point and its label "(2, 4)" STAY. Shot R7-B7-after-esc.png.
Redefine f8 as x²+1: the kept point moved to the new curve and its label changed to "(2, 5)" (it follows the function). The earlier Bounded Area result on the same page also redrew, and its label changed from 2.23 to 1.83 with new shading. Shot R7-B7-after-redefine.png.
Differs from CASSim? No (CASSim: the kept point stays and follows the function). New for CASSim: analysis results (Bounded Area here) also follow a redefined function.
Entry-line editing trap seen (not a brief row, recorded because it cost time): pressing Up from the empty f10 row to reach f8, then typing, did not change f8 (focus stayed on the row's checkbox or moved to the list icon; Right from the end of an exponent moved focus to the list icon, and a list "1 f8, 2 f9" popped up). Selecting the text with ctrl+a and retyping inside that row did not commit either. What worked: in a NEW row (ctrl+a, then type the full `f8(x)=x^2`, Right, `+1`, Return), which redefines f8.

## R7-B8 Attributes on a curve
Actions menu (Menu 1): 1 Pointer, 2 Select (submenu), 3 Hide/Show, 4 Attributes, 5 Set Conditions, 6 Delete all, 7 Text, 8 Coordinates and Equations, 9 Calculate, A Redefine, then a down arrow (more items below, not scrolled to). Shot R7-B8-actions-menu.png.
Menu 1 4 Attributes, then click the line f9 (x+1): a small vertical panel of icon rows opens under the pointer, headed "graph f9", with a yellow tooltip naming the highlighted row and its position, e.g. "(1/3) ...". Up/Down move between rows, Left/Right change the value (no wrap: Right stops at the last value). Esc leaves. Tooltip wording below is the emulator's own short labels; where it is a sentence I mark it (TI text, do not reuse).
Rows seen, top to bottom (f9 was changed as I went; I put continuous back before leaving):
1. Line weight: (1/3) thin, (2/3) medium, (3/3) thick (TI text). Starts on thin. Shots R7-B8-lineweight-1of3/2of3/3of3.png.
2. Line style: (1/3) continuous, (2/3) dotted, (3/3) dashed (TI text). Shots R7-B8-linestyle-1of3/2of3/3of3.png.
3. Label style: five values, tooltip always "label style" with the position (n/5). It started on 3/5. The graph label changes: 1/5 `f9`; 2/5 `f9(x)`; 3/5 `f9(x)=x+1`; 4/5 `y=f9(x)`; 5/5 `y=x+1`. Shots R7-B8-labelstyle-1of5 to 5of5.png.
4. Label parameters: (1/2) Show names, (2/2) Show values (TI text). Shots R7-B8-labelparams-1of2/2of2.png. I did not check what it changes on the label (the screen showed no obvious change while the label style was 5/5).
5. Continuous or discrete: (1/2) Graph is continuous, (2/2) Graph is discrete (TI text). Discrete draws f9 as separate dots (red points spaced along the line). Shots R7-B8-continuous.png, R7-B8-discrete.png.
6. Step size (shown after the Discrete choice): tooltip (1/1) Step size, "current value" 0.769231, "type value to change" (TI text). Typing a number changes it; I did not type one. Shot R7-B8-stepsize.png.
7. Number of points: tooltip (1/1) Number of points, current value 25, type value to change (TI text). Shot R7-B8-numpoints.png.
Rows 6 and 7 appeared once row 5 was set to Discrete and Down was pressed past it; I did not check whether they show while continuous (the panel showed the "a=" row and the continuous/discrete row only, with a down arrow, before I changed row 5).
Not pressed: any row below 7 (Down at 7 did nothing visible).
Differs from CASSim? CASSim has not built Attributes (per the brief), so nothing to compare.

## R7-B9 Graph Entry/Edit > Equation Templates
Menu 3 Graph Entry/Edit lists: 1 Function, 2 Relation, 3 Equation Templates (submenu), 4 Parametric, 5 Polar, 6 Scatter Plot, 7 Sequence (submenu), 8 Diff Eq. Shots R7-B9-graphentry-menu.png, R7-B9-eqtemplates-menu.png.
Equation Templates submenu: 1 Line, 2 Parabola, 3 Circle, 4 Ellipse, 5 Hyperbola, 6 Conic (each opens a further list). Every leaf was opened; each one puts a new row in the entry line named e1 (the row had a small icon of the curve type and NO default numbers: every coefficient is an empty dotted placeholder box). A second template replaced the empty e1 row (it stayed e1). Nothing was graphed because I filled in none of the boxes.
Leaves and the entry line each gave (⬚ = empty placeholder box; superscript 2 as drawn):
- Line (R7-B9-line-menu.png): 1 Line Slope Intercept `y=⬚·x+⬚`; 2 Vertical Line `x=⬚`; 3 Line Standard `⬚·x+⬚·y=⬚`. Shots R7-B9-line-slopeintercept/vertical/standard.png.
- Parabola (R7-B9-parabola-menu.png): 1 Vertex form `y=⬚·(x-⬚)²+⬚`; 2 Standard form `y=⬚·x²+⬚·x+⬚`; 3 Vertex form `x=⬚·(y-⬚)²+⬚`; 4 Standard form `x=⬚·y²+⬚·y+⬚`. Shots R7-B9-parabola-vertex-y/standard-y/vertex-x/standard-x.png.
- Circle (R7-B9-circle-menu.png): 1 Center form `(x-⬚)²+(y-⬚)²=⬚²`; 2 Standard form `⬚·x²+⬚·y²+⬚·x+⬚·y+⬚=0` (the menu text shows a·x²+a·y²+b·x+c·y+d=0, so both squares share a; the entry line has separate boxes for the two squares). Shots R7-B9-circle-center/standard.png.
- Ellipse (R7-B9-ellipse-menu.png): only one leaf, 1 Center form, drawn as a stacked fraction `(x-⬚)²/⬚² + (y-⬚)²/⬚² = 1` in the entry line. Shot R7-B9-ellipse-center.png.
- Hyperbola (R7-B9-hyperbola-menu.png): 1 East-West `(x-⬚)²/⬚² - (y-⬚)²/⬚² = 1`; 2 South-North `(y-⬚)²/⬚² - (x-⬚)²/⬚² = 1`. Shots R7-B9-hyperbola-ew/sn.png.
- Conic (R7-B9-conic-menu.png): 1 General `⬚·x²+⬚·x·y+⬚·y²+⬚·x+⬚·y+⬚=0` (the entry line runs off the right edge with a small scroll arrow, so the last boxes are not visible). Shot R7-B9-conic-general.png.
The menu rows show the formulas in letters (a, b, c, h, k, r); the entry line shows empty boxes only.
Differs from CASSim? CASSim has not built Equation Templates (per the brief), so nothing to compare.

## R7-B10 Actions: Select, Text, Coordinates and Equations, Calculate
Actions menu list is in R7-B8 (1 Pointer to A Redefine). Menu 1 2 Select opens a submenu: 1 Region (enabled), 2 Image (greyed), 3 Grid (greyed). Shot R7-B10-select-submenu.png.
- Select > Region: choosing it puts a small dotted-rectangle tool icon at the top left of the page. I could not make a visible selection: a quick drag (the automation's drag) PANNED the window instead (it moved about 7.5 units left; shot R7-B10-select-region-fastdrag-panned.png; I then reset with Zoom-Standard), and a slow press-move-release drag showed no rectangle and no change (shot R7-B10-select-region-slowdrag-nothing.png). So what Select Region does here is NOT established; this is a gap, not evidence that it does nothing.
- 7 Text: after choosing it, a click on the page opens a framed text box with a cursor at that spot; typed `hello` shows in italics inside the frame (shot R7-B10-text-typing.png); Return closes the frame and leaves plain italic text `hello` on the page (shot R7-B10-text-placed.png). The tool icon (AbI) stays at the top left until Esc.
- 8 Coordinates and Equations: tool icon `y:(x)` at the top left. Clicking a spot on the kept trace point or on the curves f8 and f9 did nothing visible (shot R7-B10-coords-click-on-curve-nothing.png). Clicking the dot at (-1,0), the Bounded Area lower bound marker, showed a grey ghost label `(-1, 0)`, then Return gave a small tooltip beside it that I could not read clearly (it looked like "1 point", overlapping the 1.83 label), and a second Return made the label solid black `(-1, 0)` on the page (shots R7-B10-coords-ghost-label.png, R7-B10-coords-label-placed.png). So it labels a point with its coordinates; I did not get an equation label for a curve.
- 9 Calculate: tool icon `a+b`. Clicking the plain number 1.83 (the Bounded Area result) did nothing. I typed a text `12`, chose Calculate and moved to it: a tooltip "expression" shows and the text highlights (shot R7-B10-calc-expression-prompt.png); clicking it put a second grey `12` beside it (shot R7-B10-calc-after-click.png); Return made it solid, so the page reads `1212` (the original 12 and its value 12, with the tooltip "expression" still showing; shot R7-B10-calc-after-return.png). I did not test an expression with a variable (no prompt for a value appeared for a plain number).
Differs from CASSim? CASSim has not built any of these (per the brief), nothing to compare.

## R7-B11 Entry-line Catalog, var and ans
Setup: a new Graphs page 11.3 (Real), entry line open on an empty function row (it showed `f10(x)=`; the f1 row of the brief was already used in this document). Catalog key opened with a click on the book key.
- Catalog: opens as a dialog on tab 1 (the function list). It opened where the last use left it (at getDenom(, then typing `a` jumped to the top: abs(, amortTbl(, and, angle(, ANOVA, ANOVA2way, Ans). The tab icons run 1 to 6 as in the Calculator. The list is the full list (not trimmed for Graphs): it includes `Ans`, and the statistics wizards (ANOVA) are marked with the wizard icon. Shots R7-B11-catalog-opens.png, R7-B11-catalog-abs-top.png, R7-B11-catalog-ans-selected.png.
- Choosing Ans from the Catalog and pressing Return put `Ans` into the entry line (`f10(x)=Ans`; shot R7-B11-catalog-ans-inserted.png). Pressing Return on that line gave an Error dialog: "Unsupported use of Ans. This application does not support Ans." (TI text, do not reuse; shot R7-B11-ans-error-on-enter.png). So `ans` is OFFERED (Catalog, key) but REFUSED on Enter in a Graphs entry line. The error left the text in place.
- ctrl+(-) (the `ans` key; I clicked ctrl then the (-) key): put `Ans` into the empty entry line (shot R7-B11-ctrl-minus-gives-ans.png).
- A line started with an operator: typed `+x` into an empty entry line stays `+x`; NO `Ans` is put in front (shot R7-B11-leading-plus-no-ans.png). Matches CASSim.
- Variables key (var): opens a small drop-down list of the function variables f1 to f9 (function icon each; no other variable types listed; there were no other stored variables, so I cannot say whether others would show). Up from f1 wraps to f9. Return inserted `f9()` with the cursor between the brackets. Shots R7-B11-var-list.png, R7-B11-var-list-wrapped.png, R7-B11-var-inserted.png.
Differs from CASSim? Partly. Matches: no Ans in front of a leading operator. New: `ans` is offered by the Catalog and the key but rejected on Enter with an error; the var list inserts `f9()` with brackets.
Not checked: what the Catalog offers on its other tabs in a graph entry line.


## RUN 7 Part B: lists
Run: B2 (x-axis drags, partial: no y-axis drag); B3; B4; B5; B6; B7; B8; B9; B10 (Select Region unresolved, see row); B11.
Not run: B1 (needs a Computer-page-size document; not opened in this run).
Also seen, not covered: a drag on a curve translates the function (f2 became 2·sin(x-0.91)-0.044); the Window/Zoom and Trace menus are listed above; Trace shows a "zero" label on a zero.
