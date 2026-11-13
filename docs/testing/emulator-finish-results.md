# Emulator check 6 run 2, finish-off rows (observations only)

Setup note: the original Part G document (Document2) had been reused for Parts J and H, so its pages no longer matched the brief. These G rows were run in Document1, a fresh Handheld document, Radian, Float 8, Problem 1: 1.1 Calculator (`xs:={1,...,8}`, `ys:={2,4,5,8,10,12,14,16}`), 1.2 Lists & Spreadsheet (A named `xs`, B named `ys`, C three typed values 7, 8, 9), 1.3 Graphs (`f1(x)=x`, entered as the first function, not f4). Page moves with ctrl+Left / ctrl+Right (each takes 3 to 4 s). No screenshots saved.

### G35 `xs[1]:=55` then ctrl+Z on the sheet
Keys: 1.1 `xs[1]:=55` (result 55); ctrl+Right to 1.2; ctrl+Z. Observed: A1 on 1.2 showed 55 on arrival; after ctrl+Z the screen showed page 1.1 (the history unchanged: the `xs[1]:=55` line still there) and `xs` still returned {55,2,3,4,5,6,7,8}; going back to 1.2, A1 still 55. Nothing was undone and no message appeared.

### G36 Sheet edits then ctrl+Z x3, ctrl+Y x3
Setup: B1 typed 100, B2 typed 200, then the column letter C clicked and Del pressed (C1:C3 cleared, cursor on C1).
Observed, in order: ctrl+Z (1): C1:C3 back to 7, 8, 9. ctrl+Z (2): cursor on B2 with B2 in edit mode showing `200` with the caret. ctrl+Z (3): B2 in edit mode and empty. ctrl+Y (1): B2 edit mode showing 200. ctrl+Y (2): B2 committed as 200 (not in edit). ctrl+Y (3): C1:C3 cleared again. (B1 = 100 was not reached by the three ctrl+Z.)

### G37 Graphs entry then ctrl+Z from other pages
Setup: 1.3 `f1(x)=x` entered (thick blue line while selected). From 1.1 ctrl+Z: the screen jumped to page 1.2 (A1 55, C1:C3 empty as before; nothing visibly changed). From 1.3 ctrl+Z: the screen also jumped to 1.2 and nothing changed; a further ctrl+Z on 1.2 returned to 1.3. In all cases `f1(x)=x` stayed on 1.3 (drawn thin once deselected, a "label" hover tag appeared near the cursor).

### G39 Sheet scroll position
Keys: ctrl+G, typed `h40`, Return: the view showed rows 36 to 40 with columns E (part), F, G, H and the cursor on H40 at the bottom right (row 40 was not at the top and H not at the left; a go-to scrolls the minimum). ctrl+Right then ctrl+Left: the same view and the cursor still on H40. The Go To dialog: title "Go To", one text field, OK and Cancel.

### G42 Menu open when leaving the sheet
Keys: Menu clicked (list 1 Actions, 2 Insert, 3 Data, 4 Statistics, 5 Table), then ctrl+Right. Observed: the page did not change and the menu stayed open (ctrl+Right ignored while a menu is open); ctrl+Left likewise. The page could not be left with the menu open, so "closed on return" does not arise.

### G48 Calculator: half-typed line and a picked history row
Keys: on 1.1 typed `3+`, then Up twice (the `xs` history row highlighted blue, the entry text `3+` still shown below it); ctrl+Right, then ctrl+Left. Observed: on return the `xs` row was still highlighted and `3+` was still in the entry line.

---
## Part E rows (run in Document1 page 1.2: A `xs`, B `ys`, C `d1` = 7, 8, 9, D `qq` linked to a Calculator list {1,2}; Float 8, Radian, Auto). No screenshots saved.

### E2 Context menu on a block of cells
Keys: C1 clicked, shift+Down x2, shift+Right (status shows C1:D3), right-click inside. Observed: 1 Cut, 2 Copy, 3 Paste, (line), 4 Fill, 5 Delete Cells, 6 Sort, 7 Color (submenu).
Row number context menu (right-click on row 2's number): 1 Cut, 2 Copy, 3 Paste, (line), 4 Resize Row, 5 Insert Row, 6 Delete Row, 7 Color (submenu); the row is outlined top and bottom with a blue bar.

### E4 Keys and mouse (partial)
- Enter after typing in a cell: the cursor moves down (typed `7`, Return, `8`, Return, `9`, Return filled C1:C3).
- Tab from C1: the selection went to the column's header area (name cell and the formula row outlined as a pair). shift+Tab from there: the whole sheet outlined as one block (looks like select all; status showed C1 and the entry line `7`).
- Double-click on C2: the cell enters edit mode with its text (8) selected; the entry line shows `8`. Esc leaves it.
- Drag from C1 to D2: block C1:D2 selected (status C1:D2).
- Mouse wheel, 3 notches down: the view moved to rows 6 to 10 and the cursor to C10.
- Not run: ctrl+Y/ctrl+Z singly (covered in G36), Del on each, arrows at edges.

### E7 Conflict Detected (found this time)
Cause: a formula that uses a name that is both a cell and a variable. In the formula cell of column E typed `=d1+qq` (d1 is also cell D1), Return.
Dialog "Conflict Detected": line `=d1+qq.`, line `d1 :  Cell or Variable?`, a drop-down (default "Cell Reference", other choice "Variable Reference"), buttons OK and Cancel. I chose Variable Reference and OK: the formula became `='d1+qq` (an apostrophe before the variable name). Cancel not tried.
Other dialog seen: naming column C `xs` when column A is already linked to `xs`: "Link Error" "Cannot link to same list/variable twice", OK; the name cell stayed in edit mode and Esc cleared it. Naming a column that has typed data with an existing Calculator list `qq` replaced the column's data with the list (1, 2) without a dialog.

### E11 Copy and paste of columns (partial)
Clicking the column letter outlined the name cell (not the data); ctrl+C then paste at G1 put text `xs` in G1 (stale clipboard text; no column was copied). ctrl+shift+Down turned on CAPS (title bar "CAPS") and selected only C1:C2; ctrl+C and paste at G1 gave 7 and 8 in G1:G2; one ctrl+Z removed both. ctrl+shift pressed again turned CAPS off. Not run: whole-column copy by another route, Del/cut on a whole row.

### E12 Insert and delete a row; effect on a formula past the change
Setup: G1 `=c3` (value 9). Cursor on C2, Menu > 2 Insert: 1 Insert Cell, 2 Insert Row, 3 Insert Column. Insert Row: a new row 2 across all columns (linked columns C and D show a void `_` there, E and F empty); G1's formula became `=c4`, value still 9, data below moved down. Row-number context menu > Delete Row (6): row removed, G1 returned to `=c3`, value 9.

### E20 Formula column with different list lengths
Formula cell of column E: `=d1+qq` (lengths 3 and 2) with Variable Reference. Dialog "Syntax Error in Column: e", "Dimension mismatch", "Two or more arguments must have matching dimensions. For example [1,2]+[1,2,3] is a dimension mismatch.", OK. After OK every cell of E shows `#ERR`; the formula cell shows `='d1+qq`; the selected cell E1 shows entry line `="#ERR"`. Del on the formula cell cleared the formula but the #ERR cells stayed.

### E22 Display Digits and the sheet
Document Settings > Display Digits drop-down list: Float, Float 1 to Float 12, Fix 0 to Fix 12. Cells: F1 `=1/3` shows `1/3` in all settings (exact in Auto); F2 `=1./3`: Float 3 shows `0.333`; Fix 2 shows `0.33`; Float 8 shows `0.33333...` (truncated with dots in the narrow column). So the sheet follows Document Settings. The mouse wheel over the open drop-down moved the highlight (it changed the setting while scrolling); keys Up/Down and Return choose. Restored to Float 8.

### E24 Limits
ctrl+G `a2500`: the cursor goes to A2500 (row 2500 is the last row; Down there stays on it). ctrl+G `a2501`: dialog "Go To" "Invalid reference. Please try again." with OK. ctrl+G `z1` works (column Z is the last; Right at Z1 stays); `aa1` and `zz1` give the same "Invalid reference" dialog.

## Lists
Run: G35, G36, G37, G39, G42, G48 (in a rebuilt document), E2 (block and row menus), E4 (partial), E7 (Conflict Detected), E11 (partial), E12 (insert/delete row), E20 (lengths), E22, E24.
Not run: E11 whole-column copy/paste by a working route, E4 remaining keys; E7 Cancel button; G36 B1 step (three ctrl+Z did not reach it); G39 exact "row 40 at top".

## G43 - Graphs entry line left open, leave page and return

Recording
- Settings: Document2, Radian, Float 8, Graphs page with f6(x)=x.
- Keys: ctrl+G (entry line f6(x)= opens), typed `x^` (exponent box left empty), ctrl+Right to the next page, ctrl+Left back.
- Observed: before leaving, the entry line showed `f6(x)=x` with an empty exponent box. On return the entry line was still open and showed `f6(x)=` with the caret; the typed text was not visibly kept.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## G44 - Graph Trace running at x = 2.1, leave page and return

Recording
- Settings: Document2 page 1.2 (Graphs, f5(x)=x), Radian, window -10..10, -6.67..6.67.
- Keys: menu 5 (Trace) 1 (Graph Trace), Right x7 (point at 2.1, 2.1), ctrl+Right, wait 4 s, ctrl+Left, wait 4 s, then Right once.
- Observed: trace point read `f5: (2.1, 2.1)` before leaving. After returning the trace point was still at 2.1, 2.1 but the marker was drawn as a single circle (the double ring seen while tracing was gone). Pressing Right then moved it to (2.4, 2.4), step 0.3 per key.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## G45 - Analyze Graph > Zero, lower bound set, leave page and return

Recording
- Settings: Document2 page 1.2 (Graphs, f5(x)=x), Radian, Float 8.
- Keys: menu 6 (Analyze Graph) 1 (Zero); Left x3; Return; ctrl+Right, wait 4 s, ctrl+Left, wait 4 s; Right x2; Return.
- Observed: after choosing Zero the prompt `lower bound?` showed with a dotted vertical line (bound marker) at about x = 7.5 and a hand cursor over the graph; the Zero tool icon showed top-left. Left x3 did not visibly move the dotted line. Return set the bound and the prompt became `upper bound?`, line still drawn. After leaving the page and returning, the prompt and the dotted line were gone, the Zero tool icon was still at top-left, and no prompt was showing. Right x2 then Return showed the prompt `graph?` (pick a graph) with no dotted line.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## G46 - Pan and zoom, then Window Settings values

Recording
- Settings: Document2 page 1.2 (Graphs), Radian, Float 8, YScale/XScale Auto.
- Keys: menu 4 (Window / Zoom) 1 (Window Settings) to read; mouse drag on empty graph space; menu 4 3 (Zoom - In) then Return, Return.
- Observed (start): XMin -10, XMax 10, YMin -6.6666666666667, YMax 6.6666666666667.
- Observed (stray): a first drag that started on the line f5(x)=x did not pan. It changed the function to `f5(x)=24·x` (the line became steep) and the window stayed -10..10, -6.67..6.67. Not what was planned; recorded as seen.
- Observed (pan): a drag starting on empty space about 100 px left and 60 px up moved the view. Axes showed -7.36..12.64 (x) and -8.24..5.09 (y). Window Settings then read XMin -7.3584905660377, XMax 12.641509433962, YMin -8.2389937106918, YMax 5.0943396226415 (width stays 20, height stays 13.333).
- Observed (zoom in): Zoom - In 'Center?' prompt showed a magnifier cursor with a yellow `Center?` tag. After Return, Return the Window Settings read XMin 5.990566037736, XMax 10.990566037736, YMin -5.7861635220126, YMax -2.4528301886792 (width 5, height 3.333, i.e. 4x in; I pressed Return twice, so whether that is one zoom of 4 or two of 2 was not separated).
- Dialog: Window Settings lists XMin, XMax, XScale (Auto), YMin, YMax, YScale (Auto), OK, Cancel; values shown to 14 significant figures regardless of Float 8.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## G47 - Data & Statistics: a point selected, a regression shown, leave and return

Recording
- Settings: Document2, new Data & Statistics page (1.5), Radian, Float 8. Lists xx={1,2,3,4,5,6,7}, yy={2,3,5,4,7,8,8} made on a Calculator page; xx on the x axis, yy on the y axis.
- Keys: menu 4 (Analyze) 6 (Regression) 1 (Show Linear (mx+b)); click on the point at x = 4; ctrl+Left, wait 4 s, ctrl+Right, wait 4 s.
- Observed (before): the regression line was drawn with `y = 1.07143·x+1.` and `r² = 0.907258` (first view). A click then left all points filled blue, the line thinner and the equation hidden. A second click on the point at (4, 4) ringed that point (hollow with a black ring); the others stayed blue.
- Observed (on return): the point at (4, 4) was still ringed, now with a label `(4, 4)` beside it; the regression line was still drawn; the equation text was not shown.
- Regression menu: Show Linear (mx+b), Show Linear (a+bx), Show Median-Median, Show Quadratic, Show Cubic, Show Quartic, Show Power, Show Exponential, Show Logarithmic, Show Sinusoidal, more below.
- Analyze menu items seen: Remove, Add Movable Line, Lock Intercept at Zero, Plot Function, Shade Under Function, Regression, Residuals, Plot Value, Show Normal PDF, Graph Trace.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## G49 - Generate Sequence of 500 terms, then change it from the calculator (done with changes, see below)

Recording
- Settings: Document2, new Lists & Spreadsheet page 1.6 and Calculator page 1.7, Radian, Float 8. The sequence went into column A (not G), because a new sheet opens on A1.
- Keys: menu 3 (Data) 1 (Generate Sequence); dialog fields Formula `n^2`, Initial Terms empty, n0 1, nMax 500 (typed over 255), nStep 1, Ceiling empty; Return. Then named the column `big` (click A2, Up x3, type big, Return). On 1.7 typed `big:=big+1`, Return.
- Observed (sequence): the column filled with 1, 4, 9, 16, 25 ... straight away (under 1 s by eye, nothing stale in the first view after Return). Formula row shows `=seqgen(n²,n,u,{1,500},{[ ]},1)`; the entry-bar text is `big:=seqgen(n²,n,u,{1,500},{[ ]},1)`.
- Observed (change): `big:=big+1` gave a dialog `Error: Cannot accept change: Invalid input.` (the column is a formula column), and the history row shows `"Error: Cannot accept change: Invalid input."`. `big[1]:=7` gave the same error.
- Observed (substitute): as a plain list `bg:=seq(n^2,n,1,500)` then `bg:=bg+1` both answered at once (under 1 s); `bg` showed `{1,4,9,16,25,36,49,64,81,100,121,144,169,1...` then `{2,5,10,17,26,37,50,65,82,101,122,145,170,...`. Page 1.6 appeared at once after ctrl+Left. No busy mark was seen in any view (checked at about 0, 1 and 4 s).
- Note: the timing is by eye from screenshots taken after the key; it cannot tell under-1 s apart. G49 as written (change `big` and time the sheet) could not be done because of the error.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.

## G50 - `big` plotted on Data & Statistics, change `big[1]` on 1.1

Not run as written: `big[1]` cannot be changed (see G49, `Cannot accept change: Invalid input.`), so there was no change to time. A Data & Statistics page with yy vs xx (7 points) appeared at once when added (under 1 s by eye).

## G51 - Page switch with ctrl+Right through all pages

Recording
- Settings: Document2, pages 1.1 to 1.7, tab strip shows 3 tabs at a time.
- Keys: ctrl+Left x5 then wait 6 s; ctrl+Right, zoom at once, wait 3 s, zoom, repeated for 1.2, 1.3, 1.4, 1.5.
- Observed: in every case the first view after the key already showed the finished page (1.2 Data & Statistics dot plot with caption `cat` and a dense cloud of points, 1.3 sheet with pets/sex columns plus a bar chart and dot plot, 1.4 bar chart of pets, 1.5 scatter yy vs xx with a ringed point at 4 and the regression line); the second view 3 s later was identical. No stale picture and no redraw seen, but the screenshots come some time after the key so a short stale picture could be missed.
- Also seen: page 1.2 (the first Data & Statistics page) now shows a dense cloud of several hundred blue points, not the 10 points seen earlier.
- Screenshot: not saved (zoom views only).
- Differs from CASSim or from this file's expectation? Not compared yet.
