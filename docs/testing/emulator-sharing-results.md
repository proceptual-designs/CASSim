# Emulator check 6, Part G: shared data between pages (observations only)

Note for Claude Code (from Simon): captures record behaviour, not look. Do not copy cursor shapes; use conventional touch interactions in CASSim. Keep the smooth animated transition (lerp) in Data & Statistics when data changes.

Setup: new document (Document2, Handheld size, Problem 1). Document Settings checked: Float 8, Radian, Normal, Real, Auto, CAS On. Page 1.1 Calculator (`xs`, `ys`, `d1`, `cat`, `f(x):=x^2-3`), 1.2 Lists & Spreadsheet (A `xs`, B `ys`, C `d1`, D `cat`), 1.3 Data & Statistics (xs on x, ys on y), 1.4 Graphs (`f1(x)=f(x)` and scatter `s1` xs,ys). Page navigation by ctrl+Left / ctrl+Right. Screenshots in `pages-shots-6/` named `G<row>-...png`. Every entry: Differs from CASSim or from this file's expectation? Not compared yet.

Setup note: naming a column in Lists & Spreadsheet with an existing variable name (`xs`) links it to that variable; a new Data & Statistics page opens plotting the last list `cat` as a caption (points labelled a, b, c) until x and y are chosen; the Graphs scatter entry is typed `xs`, Down, `ys`, Return.

### G1 `xs[2]:=20` on the Calculator
Keys: on 1.1 `xs[2]:=20`, Return (result 20). Observed: 1.2 A2 shows 20 on arrival. 1.3 scatter already redrawn on arrival: the point for x=2 is not on screen (window unchanged, x 1 to 8; 7 points visible). 1.4: scatter shows the other points, the x=2 point is not in view. No dialog. Screenshots G1-calc-xs2-20, G1-sheet-A2-20, G1-scatter-1.3-point-gone, G1-graphs-1.4-point-gone.

### G2 `xs:={1,2,3}`
Observed: column A shows 1, 2, 3, rows 4 to 8 empty (B, C, D keep their values). 1.3 scatter shows three points (x 1 to 3, window unchanged); 1.4 shows three points. No message on any page. Screenshots G2-*.

### G3 `DelVar xs`
Keys: `xs:={1,...,8}` then `DelVar xs` (Done). Observed: column A's name cell becomes blank (header shows `A`), its 8 values stay as constants (the cell entry line for A2 reads `=2`). 1.3: x axis variable lost, the plot becomes a vertical dot plot of ys with "Click to add variable" on x. 1.4: the scatter plot and its label disappear; f1 stays. Typing `1` in A1 did not recreate `xs` (`xs` on the Calculator returns `xs`, undefined). Naming column A `xs` afterwards made `xs` exist again with the eight values (`xs` returns `{1,2,3,4,5,6,7,8}`). Screenshots G3-*.
(G3 follow-up) After naming column A `xs` again, the scatter on 1.3 still had its x variable empty (re-chosen from the axis list: `cat, d1, xs, ys`). The Graphs scatter `s1` and its label reappeared on their own as soon as `xs` existed again. Screenshots G3-sheet-naming-column-A-xs-recreates, G3-calc-xs-recreated-from-column.

### G4 `xs:=5`
Observed: dialog **Error** "Cannot accept change, variable in use: Cannot change to requested variable type." with OK (the same dialog appears on every page visited while it is open); after OK the history line shows `"Error: Cannot accept change, variable in use▸` (cut off at the right with a ▸) and `xs` is still the list `{1,2,3,4,5,6,7,8}`; the entry line keeps `xs:=5`. Screenshots G4-error-variable-in-use-xs-eq-5, G4-calc-history-error-text-truncated.

### G5 `xs:=xs^2`
Observed: accepted, result `{1,4,9,16,25,36,49,64}`; column A shows 1, 4, 9, 16, 25; scatter on 1.3 redrawn (points for x=1 and x=4 in view, window unchanged); 1.4 redrawn. Screenshots G5-*.

### G6 `xs:={1,x,1/3,sqrt(2),2.5}`
Observed: accepted. Column A: `1` right-aligned, `x` left-aligned (text), `1/3` right-aligned (exact fraction), `√(2)` left-aligned, `2.5` right-aligned. The scatter on 1.3 shows points for 1, 1/3 (at the left edge), √2 and 2.5; there is no point for `x`. 1.4 shows a scatter with the same non-numeric element left out. No dialog. Screenshots G6-*.

### G7 `ys[9]:=18` then `ys[12]:=5`
Observed: `ys[9]:=18` accepted (result 18); `dim(ys)` = 9; `ys` = `{2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1,18}`; sheet B9 shows 18, A9 empty. `ys[12]:=5` gives dialog **Error** "Dimension error / A list or matrix index is not valid. For example if l1={1,2,3,4}, then l1[5] does not exist because l1 contains only four elements." (the dialog text names `l1`); the history shows `"Error: Dimension error"`. Scatter on 1.3 unchanged (9th y has no x). ys was retyped back to 8 values afterwards. Screenshots G7-*.

### G8 `SortA xs`
Run with xs = {8,7,6,5,4,3,2,1} (the document's xs is already sorted, so as written it does nothing). Observed: `SortA xs` gives Done; `xs` = `{1,2,3,4,5,6,7,8}`; column B did not move (SortA sorts only the one list). Screenshots G8-*.

### G9 `xs:="hello"`, then `xs:=[1,2;3,4]`
Observed: both give the same **Error** dialog as G4 ("Cannot accept change, variable in use: Cannot change to requested variable type."); xs stays the list. Screenshots G9-*.

### G10 `zz:={7,8,9}` (a new list)
Observed: page 1.2 does not change (no column E). On 1.2 the name cell of column E with the var key opens a menu **1 Store Var, 2 Unlink (grey), 3 Link To: ▶**; Link To lists `cat, d1, xs, ys, zz` (`zz` offered, `f` and the functions are not). Choosing `zz` fills column E with 7, 8, 9 and names it `zz`. Screenshots G10-*.

### G11 B3 := 50 on the sheet
Observed: `ys` on 1.1 shows `{2.1,3.9,50,7.8,...}`; scatter on 1.3 and 1.4 redrawn on arrival (the third point is off the top of the window). Screenshots G11-*.

### G12 A9 := 99 (first empty row of xs)
Observed: `dim(xs)` = 9. The scatter plots on 1.3 and 1.4 still show eight points (the 9th has no y). Screenshots G12-*.

### G13 Del and Delete Cell on A4
Observed: Del on A4 leaves a void shown as `_` in the cell and `xs` = `{1,2,3,_,5,6,7,8}`, dim 8. Right-click on a single cell gives: 1 Cut, 2 Copy, 3 Paste, 4 Insert Cell, 5 Delete Cell, 6 Fill, 7 Variables ▶ (grey), 8 Resize ▶, 9 Summary Plot, A Quick Graph, B Color ▶. Delete Cell on A4 (a void) makes the list shorter: `xs` = `{1,2,3,5,6,7,8}`, dim 7 (the cells below move up; column B did not move). Right-click on a name cell gives a different menu: 1 Cut (grey), 2 Copy (grey), 3 Paste, 4 Variables ▶ (grey), 5 Symbols…, 6 Math Templates…, 7 Generate Sequence, 8 Data Capture ▶, 9 Clear Data, A Resize ▶, B Summary Plot, then more below. Screenshots G13-*.

### G14 Formula column `sq` (column F, because column E is linked to `zz` from G10)
Keys: name cell `sq`, formula row `=xs^2`. Observed: column shows 1, 4, 9, 16, 25 ...; on 1.1 `sq` returns `{1,4,9,16,25,36,49,64}` (a variable). `sq[1]:=3`: dialog **Error** "Cannot accept change: Invalid input." and history `"Error: Cannot accept change: Invalid input."`. `sq:={1,2}`: the same dialog. `DelVar sq`: the same dialog; the formula column stays. A side result: typing `sq` into a data cell F1 and `=xs^2` into data cell F2 gave "Syntax Error in Cell: f2 / Syntax" and `#ERR` (I had missed the name cell; both cells were cleared). Screenshots G14-*.

### G15 `xs[1]:=10` with sq present
Observed: F1 shows 100 on arrival (updated). G16 below uses xs[1] too.

### G16 Cell formula `=mean(xs)` in G1
Observed: G1 shows `45/8` (xs[1]=10); after `xs[1]:=100` on 1.1, G1 shows `135/8` on arrival. Screenshots G16-*, G15-*.

### G17 Rename column A from `xs` to `ws`
Observed: no dialog. On 1.1 both `xs` and `ws` exist, both `{100,2,3,4,5,6,7,8}` (the first element was 100 from G16). Pages 1.3 and 1.4 still plot `xs` (the point at x=100 is off screen). Whether xs and ws stay linked was not tested. Screenshots G17-*.

### G18 Clear the name of column B (`ys`)
Keys: select name cell, Return, ctrl+a, BackSpace, Return. Observed: the header goes blank, the cells keep their values; `ys` is still a variable on 1.1; plots unchanged. Typing 99 in B2 afterwards did not change `ys` on 1.1 (the column is no longer linked). Naming the column `ys` again re-linked it and the cells showed the `ys` values again (99 overwritten by the variable). Navigation note: from the "=" row, Up goes to the name cell, one more Up selects the whole column (header turns blue), Down returns to the name cell. Screenshots G18-*.

### G19 Name a new column `d1` (already linked to column C)
Observed: dialog **Link Error** "Cannot link to same list/variable twice" with OK; after OK the name cell stays in edit mode with `d1`; Escape cancels and the column stays unnamed. (The "Conflict Detected" dialog of E7 did not appear.) Screenshot G19-link-error-cannot-link-same-twice.

### G20 Name a column `f`, `x`, `stat.x`
Observed: `f` gives dialog **Syntax Error** "Cannot accept change: Invalid input."; `x` is accepted (column named x, empty) and `x` on the Calculator then returns `{□}` (a one-element void list); `DelVar x` gives Done and the header goes blank. `stat.x` gives **Link Error** "Variable Error. You cannot use the Stat variable in the Lists & Spreadsheet." Screenshots G20-*.

## G21 - Two Lists & Spreadsheet pages in one Problem (page 1.5 added)

- Settings: Radian / Automatic / Real / Float 8.
- Keys: on 1.4 ctrl+i, 4 (adds Lists & Spreadsheet as page 1.5); Up, Up to the name cell of column A; typed `xs`, Return; Down to A1, typed `1`, Return; ctrl+Left to 1.2 (zoom); ctrl+Left to 1.1, typed `xs`, Return, `ws`, Return.
- Observed:
  - Naming column A `xs` on the new page 1.5 linked it straight to the existing list: the column filled at once with the Problem's `xs` values (100, 2, 3, 4, 5 ... at that time). No dialog, no error.
  - Typing `1` in A1 of 1.5 changed `xs[1]` from 100 to 1. The Calculator then shows `xs` = {1,2,3,4,5,6,7,8}.
  - Page 1.2 column A is named `ws` (from G17), and `ws` stayed {100,2,3,4,5,6,7,8}. So `xs` and `ws` are NOT linked to each other (answers the lingering question from G17). Columns E-H of 1.2 were unchanged (zz, sq =xs^2, G1 9/2 shown).
  - Two sheets can show the same list by name; the edit on one is the data seen by the Calculator.
- Screenshot: G21-sheet-1.5-xs-linked.png, G21-sheet-1.5-A1-typed-1.png, G21-sheet-1.2-after.png, G21-calc-xs-vs-ws.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G22 - Second Problem, new Lists & Spreadsheet page 2.1, column named `xs`

- Settings: Radian / Automatic / Real / Float 8 (Problem 2 showed RAD).
- Keys: Doc (click), Insert (click item 4; a digit key typed here goes to the page's entry line, not the menu), Problem, then "4 Add Lists & Spreadsheet"; Up, Up, `xs`, Return; Down, then `7` Return `8` Return `9` Return.
- Observed: the new sheet (page 2.1) was blank. Naming column A `xs` created a NEW EMPTY list: it did not pick up the Problem 1 `xs` values. After typing 7, 8, 9 the column shows 7, 8, 9. On going back to Problem 1 (ctrl+Left x6 to 1.1) `xs` still reads {1,2,3,4,5,6,7,8} and `ws` {100,2,3,...}: Problem 1 untouched. Variables are per Problem. (A stray `4` typed into the 1.1 entry line earlier showed as `4·xs` = {4,8,...,32}, a typing slip, not a finding.)
- Screenshot: G22-sheet-2.1-new-empty.png, G22-sheet-2.1-xs-named.png, G22-sheet-2.1-values-7-8-9.png, G22-calc-1.1-xs-unchanged.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G23 - Calculator page 2.2 in Problem 2

- Settings: as G22.
- Keys: on 2.1 ctrl+i, 1 (Calculator, page 2.2); typed `xs`, Return, `f(2)`, Return, `f1(2)`, Return.
- Observed: `xs` gives {7,8,9} (the Problem 2 list). `f(2)` and `f1(2)` come back unevaluated as `f(2)` and `f1(2)` with no error: `f` and `f1` are not defined in Problem 2 (they were Problem 1 variables), and an undefined function call stays symbolic.
- Screenshot: G23-calc-2.2-xs-f-f1.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G24 - Copy cells in Problem 1, paste into Problem 2

- Settings: Radian / Automatic / Real / Float 8.
- Keys: on 1.2 click E1, shift+Down x2 (E1:E3 selected, `zz` = 7,8,9), ctrl+c; ctrl+Right x4 to 2.1; click B1; ctrl+v. (Source was column E because the sheet was scrolled there; the brief's A1:A3 was not used.)
- Observed: B1:B3 on 2.1 filled with 7, 8, 9 and stayed selected (status shows B1:B3). Column B has no name, so it is not linked to any variable; the paste carried values only (no link back to `zz`, no formula). Paste across Problems raised no dialog.
- Screenshot: G24-copy-source-1.2-E1-E3.png, G24-paste-2.1-B1-B3.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G25 - Redefine `f` on the Calculator, look at Graphs 1.4

- Settings: Radian / Automatic / Real / Float 8.
- Keys: 1.1 `f(x):=x^3`, Return (ctrl+Right x3 to 1.4 after).
- Observed: 1.1 answers `Done`. On arrival at 1.4 the curve for `f1(x)=f(x)` is already the cubic (redrawn on arrival, no key needed); label unchanged `f1(x)=f(x)`. The scatter (xs,ys) points are still drawn (y window tops at 6.67 so only the first few show).
- Screenshot: G25-calc-f-cubed.png, G25-graph-f1-cubic.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G26 - Redefine the graph's own function `f1` on the Calculator

- Settings: as above.
- Keys: 1.1 `f1(x):=sin(x)`, Return; to 1.4; ctrl+g (entry line); Up, Up.
- Observed: `Done`. On 1.4 the cubic is gone and a sine curve is drawn with label `f1(x)=sin(x)`. The entry line (ctrl+g) opened on an empty scatter row `s2`; Up showed `s1` (x<-xs, y<-ys, tick box on) and a second Up wrapped to an empty `s99`. The function rows were not reached by arrows in that entry line, so the f1 row text was not read directly.
- Screenshot: G26-calc-f1-sin.png, G26-graph-f1-sin.png, G26-entry-line-s2.png, G26-entry-line-s1.png, G26-entry-line-s99.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G27 - `DelVar f1`, then `DelVar f`

- Settings: as above.
- Keys: 1.1 `DelVar f1`, Return; to 1.4. Then Menu (click) > 3 Graph Entry/Edit > 1 Function (clicked), typed `f(x)`, Return (the new row was named `f1`). Then 1.1 `DelVar f`, Return; to 1.4. Then 1.1 `f(x):=x^2-3`; to 1.4.
- Observed:
  - After `DelVar f1` (`Done`, no message anywhere) the sine curve STAYS drawn but its label changes from `f1(x)=sin(x)` to `y=sin(x)`: the plot keeps the expression, loses the name.
  - Adding a function row proposed `f1(x)=`; entering `f(x)` drew the cubic again (thick, selected) with label `f1(x)=f(x)`, beside the sin curve.
  - `DelVar f` (`Done`): on 1.4 the `f1(x)=f(x)` curve and its label disappeared; the `y=sin(x)` curve remained. No error or message.
  - Redefining `f(x):=x^2-3` brought the parabola back on arrival with label `f1(x)=f(x)`: the row stays defined, it is just hidden while `f` is undefined.
  - Also seen: a steep straight line through the scatter appeared in the last screenshot; I did not create it on purpose (probably left over from earlier rows). Not investigated.
- Screenshot: G27-calc-DelVar-f1.png, G27-graph-after-DelVar-f1.png, G27-graph-f1-restored-both.png, G27-calc-DelVar-f.png, G27-graph-after-DelVar-f.png, G27-graph-f-redefined.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G28 - `f2(x)=a*x` on Graphs 1.4: decline and accept the slider offer

- Settings: Radian / Automatic / Real / Float 8.
- Keys: on 1.4 Menu (click) > 3 Graph Entry/Edit (click) > 1 Function (click); typed `a*x`, Return. Declined with Cancel. Then 1.1: `a`, `f2(1)`. Back on 1.4 added another function row, typed `a*x`, Return, then Return on the dialog (OK). Then 1.1: `a`, `a:=3`, `f2(1)`; back to 1.4.
- Observed:
  - Dialog "Create Sliders - Create a slider for: [tick] a", buttons OK / Cancel.
  - Cancel: the row `f2(x)=a·x` is kept but nothing is drawn. On 1.1 `a` returns `a` (undefined) and `f2(1)` returns `a`.
  - OK: a slider appears bottom-left ("a=1.", range -5 to 5) and a thick line `f3(x)=a·x` is drawn (the new row is f3 because f2 already existed). On 1.1 `a` now returns 1: the slider created the variable `a`.
  - `a:=3` on 1.1 gives 3; `f2(1)` gives 3 (f2 now evaluates, since `a` is defined). On return to 1.4 the slider reads a=3 and the line is steeper. No dialog.
- Screenshot: G28-dialog-create-sliders.png, G28-graph-after-cancel.png, G28-calc-a-undefined-f2.png, G28-graph-slider-created.png, G28-calc-a-eq-1-then-a-assign-3.png, G28-graph-slider-at-3.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G29 - Graph functions called from the Calculator

- Settings: as above (`a`=3, `f(x)=x^2-3`).
- Keys: 1.1 `f1(2)`, Return; `f1`, Return; `f2(1)`, Return; `f3(1)`, Return.
- Observed: `f1(2)` = 1 (so the Graphs function row is a real variable: x^2-3 at 2). `f1` on its own gives the string "Error: Argument Error". `f3(1)` = 3. The `f2(1)` typed in this batch does not appear in the history (only the earlier `f2(1)` = 3 above it), so I did not see its result a second time; I did not retype it.
- Screenshot: G29-calc-f1-f2-f3.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G30 - Linear Regression (mx+b) from the sheet, RegEqn saved to a graph function

- Settings: Radian / Automatic / Real / Float 8.
- Keys: on 1.2 clicked an empty cell (H2; with E1:E3 selected the Statistics item is greyed out), Menu (click) > 4 Statistics > 1 Stat Calculations > 3 Linear Regression (mx+b). X List `xs`, Tab, Y List `ys`, Tab, Save RegEqn to left at its default `f4` (NOT `f3` as in the brief, because `f3` is already the `a*x` row), Return. Then to 1.4. Then 1.1: `xs[1]:=0`, `f4(2)`; back to 1.4.
- Observed:
  - Dialog defaults: X List prefilled `h[]` (the column of the selected cell), Y List empty, Save RegEqn to `f4` (the next free function name), Frequency List `1`, Category List and Include Categories empty.
  - Results went into columns I:J of the sheet from the selected cell: Title "Linear Regression (mx+b)", RegEqn `m*x+b`, m 1.997619, b 0.03571..., r² 0.99883... Cell J1 holds a formula `=LinRegMx(...)`.
  - On 1.4 `f4` is NOT drawn: nothing new appeared. It is saved as a function variable only (not looked for in the entry line).
  - After `xs[1]:=0` (answers 0) `f4(2)` gives 4.7. The sheet values gave m*2+b of about 4.03 before the edit, so `f4` was recalculated from the changed data (it follows `xs`). I did not read `f4(2)` before the edit, so the "before" figure is by arithmetic from m and b.
  - On 1.4 the first scatter point moved to x=0 (the (xs,ys) label sits on the y-axis).
- Screenshot: G30-menu-stat-calculations.png, G30-dialog-linreg-defaults.png, G30-dialog-linreg-filled.png, G30-sheet-linreg-results.png, G30-graph-after-regression.png, G30-calc-xs1-0-f4-2.png, G30-graph-after-xs1-0.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G31 - Show Linear (mx+b) on Data & Statistics 1.3, then edit `xs` on the Calculator

- Settings: Radian / Automatic / Real / Float 8. Starting state: `xs[1]` = 0 left over from G30 (so the first point (0, 2.1) is outside the plot window x 1..8 and is not drawn).
- Keys: on 1.3 Menu (click) > 4 Analyze (click) > 6 Regression (click) > 1 Show Linear (mx+b) (click). Then 1.1: `xs[1]:=1`; typed `stat.` quirks (see below); back to 1.3 (ctrl+Right x2).
- Observed:
  - Show Linear draws the line with label `y = 1.82105·x+1.05789`, `r² = 0.985709` (that is the fit with `xs[1]`=0; the plot did not rescale to show the point at x=0).
  - After `xs[1]:=1` on 1.1 (answers 1) and returning to 1.3, the plot shows the first point at x=1 and the label has changed on its own to `y = 1.99762·x+0.035714`, `r² = 0.998839`. The regression label is live and updated on arrival, no key needed.
  - The `stat.` variables on 1.1: `stat.b` = 0.03571429; `stat.FreqReg` = {1.,1.,1.,1.,1.,1.,1.} (seven 1.'s visible; I did not count whether an eighth is hidden). These were picked by typing `stat.` then Return/Down+Return from the drop-down. A typed `stat.regeqn` gave an Error dialog "Syntax" (the drop-down swallowed text; known quirk), cleared with Return and ctrl+a, BackSpace.
  - Not checked: whether `stat.b` came from the sheet's earlier regression (G30) or from the D&S regression; both give the same value once `xs[1]`=1.
- Screenshot: G31-menu-ds-plot-type.png, G31-menu-analyze.png, G31-ds-show-linear-xs1-0.png, G31-calc-stat-typing-syntax-error.png, G31-calc-stat-b-freqreg.png, G31-ds-label-after-xs1-restored.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G32 - Drag a scatter point on Data & Statistics 1.3

- Settings: Radian / Automatic / Real / Float 8. Regression line removed first (Menu > 4 Analyze > 1 Remove), because a point lying on the line is grabbed as the line.
- Keys: left-click-drag the 4th point (x=4, y=7.8) up and to the right by a small amount; Escape; ctrl+Left x2 to 1.1, `xs`, `ys`; 1.2.
- Observed:
  - The point moved with the pointer and the data changed: `xs` = {1,2,3,4.498,5,6,7,8} and `ys` = {2.1,3.9,6.2,9.875,10.1,...}. The new values are not rounded to a grid (4.498, 9.875).
  - Sheet 1.2: B4 (`ys`) shows 9.875; column A (named `ws`, not linked to `xs`) still shows 4; column F (`sq` =xs^2) row 4 shows 20.2320... (4.498 squared), so the formula column followed the drag.
  - Restored with `xs[4]:=4`, `ys[4]:=7.8`; `ys` read back as the original list. (`xs[4]:=4` was echoed 4; I did not re-display `xs` after.)
  - While the point was selected a coordinate tag "(4.498, 9.875)" was shown beside it; later it was still drawn after the data were restored (stale tag until the next redraw), seen on 1.3 on return. Not investigated further.
- Screenshot: G32-ds-before-drag.png, G32-ds-after-drag-point4.png, G32-calc-xs-ys-after-drag.png, G32-sheet-B4-9.875-A4-ws-unchanged.png, G32-sheet-sq-row4.png, G32-calc-restored.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G33 - Document Settings Display Digits Float 8 -> Float 3

- Settings: Radian / Automatic / Real, Display Digits changed Float 8 -> Float 3 (Doc > 7 Settings & Status > 2 Document Settings; drop-down list runs Float, Float 1 ... Float 8, more below), OK. Put back to Float 8 afterwards.
- Keys: on 1.1 `ys`, `approx(1/3)`, `sqrt(2)*100.`, `mean(ys)`; looked at 1.2, 1.3 (Show Linear), 1.4.
- Observed:
  - Calculator: `approx(1/3)` = 0.333, `sqrt(2)*100.` = 141., `mean(ys)` = 9.03 (exact 9.025). The list `ys` still shows its one-decimal values (2.1, 3.9, ...). Earlier history lines keep the digits they were evaluated with: after setting Float 8 again a new `approx(1/3)` shows 0.33333333 while the Float 3 line above it still shows 0.333.
  - Sheet 1.2: the visible columns (ws, ys, d1, cat, zz) all hold values of at most one decimal, so nothing changed there; the `sq` column with long decimals was NOT checked under Float 3.
  - Data & Statistics 1.3: the Show Linear label stayed `y = 1.99762·x+0.035714`, `r² = 0.998839` (six significant digits), unchanged by Float 3.
  - Graphs 1.4: the slider label `a=3.` and the axis labels (6.67, -6.67, 1) looked the same as under Float 8.
  - So in this build Float 3 changes the Calculator's results (and what a new entry displays) but not the regression label or the plot/axis numbers I saw.
- Screenshot: G33-menu-settings-status.png, G33-document-settings-float3.png, G33-dropdown-display-digits.png, G33-calc-float3.png, G33-sheet-1.2-float3.png, G33-ds-label-float3.png, G33-graph-float3.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G34 - Undo after a sheet edit, pressed from the Calculator

- Settings: Radian / Automatic / Real / Float 8.
- Keys and trouble: typed `77` in B1 on 1.2 (an earlier slip typed it into C1; C1 was put back to 2). Then ctrl+Left to 1.1 and ctrl+z. The Doc menu (click) > 2 Edit shows "1 Undo (Ctrl+Z)" and "2 Redo (Ctrl+Y)" (Redo greyed until something is undone), "3 Cut", "4 Copy", "5 Paste", "6 Delete", "7 Color". Page changes with ctrl+Left/Right lag by a second or two and keys only reach the emulator after a click on its status bar, so the first attempts were unreliable; the clean run used a click on the status bar, then a 3 s wait before looking.
- Observed, clean run: typed `88` in B2 on 1.2 (Return), then ctrl+Left to 1.1, then Doc > Edit > Undo (mouse):
  - Undo 1 (from 1.1): the document jumped to page 1.2 with the cursor on B3. B2 still showed 88. Nothing on the Calculator changed (its last entries stayed).
  - Undo 2 (now on 1.2): B2 went back into edit mode with `88` typed and not entered (entry line shows 88). Escape then left B2 at 3.9, so the edit was undone and the typed text discarded.
  - So Undo is document-wide: it navigates to the page of the last change, and steps back one edit at a time, an entry being two steps (the Return, then the typing). It did not undo the last Calculator entry; with the earlier 77 in B1 still in place the earlier ctrl+z presses just moved the page forward without visibly changing data (I did not repeat that carefully).
  - Using ctrl+z on the keyboard behaved like the menu item at least in moving pages; I did not get a clean keyboard result.
- Mishap (for the record): a Down key into the Doc menu landed on File > Close and showed "Do you want to save 'Unsaved Document'?" Yes / No / Cancel; I chose Cancel, nothing lost.
- Restored: B1 = 2.1 and B2 = 3.9 retyped by hand.
- Screenshot: G34-sheet-B1-77.png, G34-ds-regression-with-77.png, G34-after-ctrl-z-from-1.1-shows-1.2.png, G34-sheet-B2-88-entered.png, G34-doc-menu-Edit-Undo-Redo.png, G34-doc-menu-Edit-again.png, G34-mishap-save-dialog.png, G34-undo-1-jumped-to-1.2.png, G34-undo-2-B2-back-in-edit.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G35, G36, G37 - not run
Undo rows G35 to G37 were not run: after G34 showed that Undo is document-wide and jumps pages, and page changes were lagging, I put the time into the "what a page keeps" rows instead (see the lists at the end).

## G38 - Sheet: cursor cell kept when leaving and returning (D6 used, not D7)

- Settings: Radian / Automatic / Real / Float 8.
- Keys: on 1.2 cursor on D6 (the sheet was scrolled so row 2 is the top visible row); click the status bar, ctrl+Right to 1.3, wait 3 s, click the status bar, ctrl+Left, wait 3 s. (Single hop to the next page and back; no hop to another Problem.)
- Observed: on return the cursor is still on D6 and the scroll position is unchanged.
- Screenshot: G38-sheet-cursor-D6-before.png, G38-sheet-cursor-D6-after.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G40 - Sheet: a cell half typed (`12` typed in D6, no Return)

- Keys: click D6, type `12`, leave with ctrl+Right to 1.3 and come back with ctrl+Left (checked twice).
- Observed: on return D6 is still in edit mode with `12` typed and not entered (entry line shows 12). Escape then restored D6 to its old value `a`. So a half-typed cell edit survives a page change.
- Screenshot: G40-sheet-12-half-typed.png, G40-sheet-12-still-typing-after.png, G40-sheet-12-still-typing-after-2.png, G40-sheet-escape-restores-a.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G41 - Sheet: block B3:C5 selected (not B2:C4)

- Keys: click B3, shift+Down x2, shift+Right (status shows B3:C5); ctrl+Right and ctrl+Left as in G38.
- Observed: the block B3:C5 is still selected on return, same view.
- Screenshot: G41-sheet-block-B3-C5-before.png, G41-sheet-block-B3-C5-after.png
- Differs from CASSim or from this file's expectation? Not compared yet.

## G47 - Data & Statistics: point selected and regression shown (seen incidentally)

- Not set up as a row. From G32/G33 the 4th point had been left selected and Show Linear was on. On every later arrival at 1.3 (about eight visits, with other edits in between) the point still showed its heavy ring (selected) and the regression line and label were still there (label recalculated, see G31).
- Screenshot: G47-ds-point-selected-regression-kept.png
- Differs from CASSim or from this file's expectation? Not compared yet.

---

## Lists for Part G (run 2)

### Run
G1 to G24 (sheet, Calculator, Graphs and Data & Statistics sharing the lists; two sheets; two Problems; copy and paste across Problems), G25 to G33 (function redefinition, DelVar of graph functions, slider, regression saved to a function, live D&S regression label, dragging a point, Float 3), G34 (undo across pages, with caveats), G38, G40, G41 (page state kept), G47 (seen incidentally).

### Not run
- G35, G36, G37 (undo rows): time; page changes lag and keys need a status-bar click first. G34 showed Undo is document-wide.
- G39 (sheet scroll position, row 40 / column H), G42 (menu open), G43 (graph entry line half typed), G44 (Graph Trace), G45 (Analyze Graph > Zero half way), G46 (window pan/zoom), G48 (Calculator half-typed line and picked history row): not reached.
- The hop to another Problem and back for the G38 to G48 rows: not done (only next-page and back).
- G49, G50, G51 (timing with a 500-term list): not reached.
- G38 used D6 and G41 used B3:C5 instead of D7 and B2:C4 (the visible rows).

### Also seen, not covered by a row
- Update of the sheet cells, plots and labels happens on arrival at a page, not live (the page you are not on is redrawn when you reach it).
- `DelVar f1` leaves the function drawn but relabelled `y=...` (G27).
- `f1` alone on the Calculator gives the string "Error: Argument Error" (G29).
- Linear Regression results from the sheet go into two columns starting at the selected cell, `RegEqn` shows `m*x+b`, and the dialog proposes the next free function name for "Save RegEqn to" (G30).
- The Statistics menu item of the sheet is greyed while a block of cells is selected (G30).
- Float 3 did not change the D&S regression label or the plot numbers I looked at (G33).
- Doc menu: pressing Down in the open menu started from the last item used (Edit) and landed on File > Close, giving a Save dialog. Use clicks on the menu (G34).
- The Teacher Software opened a new empty `Document3` when I used open_application after the access grant expired (my work is in `Document2`). Document3 was left open and unsaved.
