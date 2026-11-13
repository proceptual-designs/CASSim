# Lists & Spreadsheet results, check 6 (part E)

> **Note for Claude Code (from Simon):** These captures record the behaviour of the TI-Nspire emulator, not its look. We do not need to copy exact appearance, such as mouse cursor shapes (the hand pointer seen while resizing a column, the I-beam, and so on). CASSim should also use conventional touch interactions for its UI (tap, long-press, swipe, drag handles, on-screen menus), not copy the desktop keyboard and mouse gestures one for one. Where a capture describes a key chord, right-click or cursor change, read it as the function it reaches (for example "resize a column", "open the context menu") and give that function a touch-friendly route.


TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, handheld view. Document2, Problem 1: page 1.1 Calculator (xs, ys, d1, d2, cat defined), page 1.2 Lists & Spreadsheet with A xs, B ys, C d1, D d2, E cat linked.
Settings used: Radian, Automatic, Real, Float 8 (title bar RAD).

## Setup and first screen

### E3 First screen of a new sheet
Observed: columns A to D, 5 data rows, grey formula row ("="), name row, bottom bar with cell name (A1) and edit field with two arrow buttons.
Screenshot: pages-shots-6/E3-first-screen-new-sheet.png
Also: E0-setup-calculator-lists.png, E0-setup-columns-linked.png.

### E7 (part) Linking a column by typing a list name in the name cell
Observed: typing `xs` in the name cell of column A links the column directly, no dialog.
Screenshot: pages-shots-6/E7-link-column-by-name-xs.png

## E5 Cell entry in column F, Automatic mode

### E5 F1 to F5 plain entries
Settings: Radian / Automatic / Real / Float 8.
Keys typed in cells F1 to F5 (Return after each): `5`, `1/3`, `2^0.5`, `sqrt(2)`, `pi`.
Observed: F1 `5` (right-aligned). F2 `1/3` right-aligned, shown as 1/3. F3 shown `2^(0.5)` left-aligned, not evaluated. F4 shown `sqrt(2)` left-aligned, not evaluated. F5 shown `π` left-aligned.
Screenshots: pages-shots-6/E5-auto-F2-F5-after-entry.png, E5-auto-F1-F5-top.png
Differs from CASSim or from this file's expectation? Not compared yet; recorded as seen.

### E5 F6 to F9 text, name, formulas
Keys: `"text` then Right, Return; `abc` Return; `=f1+1` Return; `=f1:f3` Return.
Observed: F6 text shown without quotes, left-aligned. F7 `abc` left-aligned. F8 `=f1+1` gives 6 (right-aligned). F9 `=f1:f3`: dialog "Syntax Error in Cell: f9", message "Syntax", button OK; after OK the cell shows `#ERR`, cursor moves to F10; the edit field for F9 still reads `=f1:f3`.
Screenshots: pages-shots-6/E5-auto-F6-F9-range-syntax-error.png, E5-auto-F6-F10-after-dialog.png


## E5 Approximate mode (Document Settings > Calculation Mode)

### E5 Calculation Mode drop-down
Keys: doc, 7, 2; click Calculation Mode arrow; click Approximate; OK.
Observed: drop-down items are Auto, Exact, Approximate (current value shows "Auto"). Other fields: Display Digits Float 8, Angle Radian, Exponential Format Normal, Real or Complex Real, CAS Mode On.
Screenshot: pages-shots-6/E5-approx-settings-dialog.png

### E5 Existing column F after switching to Approximate
Observed: F1 5 shows `5.`; F2 (was 1/3) shows `0.33333...` (cut off at the cell edge); F3 `2^(0.5)`, F4 `sqrt(2)`, F5 `π` unchanged (left-aligned text); F6 `text`, F7 `abc` unchanged; F8 (`=f1+1`) shows `6.`; F9 still `#ERR`. Columns C and D numbers now show decimal points (`2.`, `4.`, `5.`, `7.`, `9.`, `30.`).
Screenshots: pages-shots-6/E5-approx-F1-F5-existing.png, E5-approx-F6-F10-existing.png

### E5 New entries in column F, Approximate (F11 to F15)
Keys: `1/3`, `2^0.5`, `sqrt(2)`, `pi`, `=f1+1`, Return after each.
Observed: F12 `2^(0.5)`, F13 `sqrt(2)`, F14 `π` left-aligned, same as Automatic; F15 `6.`. (F11 `1/3` scrolled off, not captured.)
Screenshot: pages-shots-6/E5-approx-F12-F16-new-entries.png

## E14 Data menu (Menu > 3 Data)
Settings: Radian / Automatic / Real / Float 8. Run on scratch page 1.3, column E selected.
Top level: 1 Generate Sequence, 2 Data Capture ▶, 3 Fill (grey when a column is selected, active with a single cell), 4 Clear Data (grey with an empty cell), 5 Random ▶, 6 List Math ▶, 7 List Operations ▶, 8 Summary Plot, 9 Quick Graph (grey without two columns selected). Menu bar order: 1 Actions ▶, 2 Insert ▶, 3 Data ▶, 4 Statistics ▶, 5 Table ▶.
Screenshot: pages-shots-6/E14-data-menu-items.png

### E14 1 Generate Sequence
Observed dialog "Sequence": Formula: u(n)= (empty), Initial Terms (empty), n0 1, nMax 255, nStep 1, Ceiling Value (empty), OK, Cancel.
Keys: `n^2`, Right, Tab x3, ctrl+a, `5`, Return.
Observed: column E gets 1, 4, 9, 16, 25; the formula row of E reads `=seqgen(n²,n,u,{1,5},{□},1)` (the empty box is the unused Initial Terms).
Screenshots: pages-shots-6/E14-generate-sequence-dialog.png, E14-generate-sequence-filled-dialog.png, E14-generate-sequence-result-column-E.png

### E14 Submenus (items only, none run except where stated)
2 Data Capture ▶: 1 Automatic, 2 Manual.
5 Random ▶: 1 Number, 2 Integer, 3 Binomial, 4 Normal, 5 Sample.
6 List Math ▶: 1 Minimum, 2 Maximum, 3 Mean, 4 Median, 5 Sum of Elements, 6 Product of Elements, 7 Sample Standard Deviation, 8 Sample Variance, 9 Population Standard Deviation, A Population Variance. Up from the top wraps to the last item, A Population Variance, so the list ends there. Choosing 3 Mean writes `=mean(` into the formula row of the selected column with the cursor inside the brackets (the existing formula would be replaced); Escape cancelled it and `=seqgen(...)` stayed.
7 List Operations ▶: 1 Cumulative Sum List, 2 Difference List, 3 Augment, 4 Convert Matrix to List (grey), 5 Left, 6 Mid, 7 Right.
Screenshots: pages-shots-6/E14-data-capture-submenu.png, E14-random-submenu.png, E14-list-math-submenu.png, E14-list-math-last-item-A-population-variance.png, E14-list-math-mean-inserts-formula.png, E14-list-operations-submenu.png

### E14 8 Summary Plot
Observed dialog "Summary Plot": X List: cat, Summary List: cat, Display On: Split Page, OK, Cancel.
OK with both lists `cat`: dialog "Evaluation Error", "Invalid summary list. The list must be numeric." with OK; the Summary Plot dialog stays open.
Summary List drop-down lists cat, d1, d2, qq, xs (and more below: scrollbar). Choosing d1 and OK: the page becomes a split page with the sheet on the left and a bar chart on the right: bars a about 20, b 9, c 11 (sums of d1 per category), y-axis title d1, x-axis title cat, a small table icon at the bottom left of the plot.
Screenshots: pages-shots-6/E14-summary-plot-dialog.png, E14-summary-plot-error-non-numeric-list.png, E14-summary-plot-summary-list-choices.png, E14-summary-plot-result-bar-chart.png
Not run: Data Capture Automatic and Manual, Random items, List Math items other than Mean, List Operations items, Fill from the menu with a column, Clear Data, Quick Graph with xs and ys.

## E6 Copy-down of `$` references (Menu > 3 Data > 3 Fill)
Settings: Radian / Automatic / Real / Float 8 (switched back from Approximate).

### E6 `=f1*$g$1` filled down H1:H4 (G1 = 2)
Keys: G1 `2`; H1 `=f1*$g$1`, Return. Select block H1:H4 with shift+Down, then Menu, 3, 3: nothing happened (block stays selected, H2:H4 stay empty, also after Return).
Then: click H1 alone, Menu, 3 Data, 3 Fill: a dotted rectangle appears from H1; Down x3 extends it to H4; Return fills.
Observed: H1 10, H2 2/3, H3 2.82842... (tooltip 2.8284271247462), H4 2·√(2). Edit fields: H1 `=f1·$g$1`, H2 `=f2·$g$1`, H3 `=f3·$g$1`. The `$g$1` reference stays fixed, `f1` becomes f2, f3. (`*` is displayed as `·` in the edit field.) F3 (text `2^(0.5)`) is treated as a number in the formula: H3 is a decimal while H4 (from `sqrt(2)`) is exact 2·√(2).
Screenshots: pages-shots-6/E6-fill-block-no-effect.png, E6-fill-H1-selected-formula.png, E6-fill-dotted-range-H1-H4.png, E6-fill-result-H1-H4.png, E6-fill-H2-formula.png, E6-fill-H3-formula-tooltip.png
Differs from CASSim or from this file's expectation? Not compared yet.

### E6 (rest) functions of ranges and lists, column I
Keys (I1 to I5, Return after each): `=sum(f1:f4)`, `=mean(xs)`, `=mean(a[])`, `=d1[2]`, `=i5`.
Observed: I1 8.16176... (F3 and F4 counted as numbers). I2 9/2. I3 9/2. I4 4. I5 `=i5` (circular, entered in I5 itself instead of `=h1` in H1, to keep H1): dialog "Syntax Error" with message "Circular definition" and OK; after OK the cell is still in edit mode showing `=i5`; Escape leaves I5 empty.
Screenshots: pages-shots-6/E6-sum-mean-I1-I2.png, E6-circular-i5-dialog.png, E6-circular-after-OK-still-editing.png, E6-circular-after-Escape-cell-empty.png
Differs from CASSim or from this file's expectation? Not compared yet.

## E7 Invalid names, var key in the name cell, link conflicts

### E7 Invalid column names
Settings: Radian / Automatic / Real / Float 8. Cursor on the name cell of empty column J.
Keys: `1a`, Return; OK; ctrl+a, BackSpace, `sin`, Return.
Observed: both give a dialog titled "Syntax Error" with the message "Cannot accept change: Invalid input." and OK. After OK the name cell is still in edit mode showing the typed text; Escape leaves the name cell empty.
Screenshots: pages-shots-6/E7-name-1a-dialog.png, E7-name-1a-after-OK-still-editing.png, E7-name-sin-dialog.png

### E7 var key in the name cell
Keys: click the on-screen var key with the name cell of column J selected.
Observed: a menu with 1 Store Var, 2 Unlink (grey), 3 Link To: ▶. Link To: lists the list variables cat, d1, d2, xs, ys (list icon each), the first (cat) highlighted. Choosing 1 Store Var puts the text `var` (selected) in the name cell in edit mode.
Screenshots: pages-shots-6/E7-var-key-name-cell-menu.png, E7-var-link-to-submenu.png, E7-var-store-var-name-cell.png
(No item of Link To: was chosen.)

### E7 Linking to a name already used on the sheet
Keys: name cell of column I (data from `=sum(f1:f4)` etc.), `xs`, Return.
Observed: dialog "Link Error", message "Cannot link to same list/variable twice", OK. Name cell stays in edit mode showing `xs`.
Screenshot: pages-shots-6/E7-name-xs-twice-link-error.png

### E7 Naming a column with data after a list defined on the Calculator page
Setup: Calculator page 1.1 `qq:={7,8,9}`. Back on 1.2, name cell of column I (holding four formula values), `qq`, Return.
Observed: no dialog. Column I now shows 7, 8, 9 in rows 1 to 3 (row 4 empty); the old cell values are gone. The "Conflict Detected" dialog did not appear in this case, so its buttons are not recorded.
Screenshot: pages-shots-6/E7-name-qq-existing-list-column-I.png

## E10 Navigation keys
Settings: Radian / Automatic / Real / Float 8. Cursor started on H1 (formula `=f1·$g$1`), column H holding four values.

### E10 ctrl+arrows
Keys: ctrl+Down, ctrl+Right, ctrl+Up, ctrl+Left (one at a time from H1).
Observed: ctrl+Down and ctrl+Right: no visible change (cursor stays on H1). ctrl+Up: the screen changes to the page sorter ("*Unsaved Document", Problem 1, two page thumbnails, the second selected). ctrl+Left: stays in the page sorter. Return in the page sorter goes back to page 1.2 with H1 selected.
Screenshots: pages-shots-6/E10-ctrl-Down-no-move.png, E10-ctrl-Right-no-move.png, E10-ctrl-Up-page-sorter.png, E10-ctrl-Left-in-page-sorter.png

### E10 ctrl+7 and ctrl+1
Observed: ctrl+7 from H1: no visible change. ctrl+1 then: cursor moves to H4 (edit field `=f4·$g$1`), the last filled cell of column H.
Screenshots: pages-shots-6/E10-ctrl-7-no-visible-change.png, E10-ctrl-1-moved-to-H4.png

### E10 ctrl+G (Go To)
Keys: ctrl+g; `a12`, Return; ctrl+g; `xs`, Return.
Observed: a "Go To" dialog with an edit field, OK and Cancel. `a12`: cell A12 is selected and the view scrolls so rows 8 to 12 show (columns A to D). `xs`: the whole column A is selected (header highlighted), view stays on rows 8 to 12.
Screenshots: pages-shots-6/E10-ctrl-G-go-to-dialog.png, E10-goto-a12-result.png, E10-goto-xs-column-selected.png

### E10 Page Up / Page Down
Keys: click B10, PageUp, PageDown.
Observed: PageUp moves the selection from B10 to B6 (view rows 3 to 7); PageDown moves it from B6 back to B10 (view rows 7 to 11).
Screenshots: pages-shots-6/E10-PageUp-B10-to-B6.png, E10-PageDown-B6-to-B10.png

## E11 Selection, copy, cut, paste, Del, ctrl+Z
Settings: Radian / Automatic / Real / Float 8. Test data: column I (name `qq`, 7, 8, 9). Pasted into column K.

### E11 Single cell copy and paste
Keys: ctrl+g `i1`; ctrl+c; Right twice; ctrl+v. Then ctrl+z.
Observed: K1 shows 7; its edit field reads `=7`. ctrl+z removes it (K1 empty again).
Screenshots: pages-shots-6/E11-copy-cell-I1-paste-K1.png, E11-ctrl-z-undo-paste-K1-empty.png

### E11 Block copy and paste
Keys: select I1:I3 (shift+Down twice), ctrl+c, move to K1, ctrl+v.
Observed: K1:K3 show 7, 8, 9 and stay selected (bottom bar K1:K3).
Screenshot: pages-shots-6/E11-block-copy-paste-K1-K3.png

### E11 Cut, Del, ctrl+Z on a block
Keys: ctrl+x on K1:K3; ctrl+z; Delete; ctrl+z.
Observed: ctrl+x empties K1:K3 (selection kept); ctrl+z restores 7, 8, 9; Delete empties them; ctrl+z restores them.
Screenshots: pages-shots-6/E11-cut-K1-K3.png, E11-undo-cut-restored.png, E11-Del-K1-K3-cleared.png, E11-undo-Del-restored.png

### E11 Column and row selection
Click the name cell of K: only the name cell is selected (bottom bar `K`). ctrl+c then Right, ctrl+v: dialog "Cannot Paste", "The contents cannot be pasted because the copy and paste areas have incompatible sizes." with OK.
ctrl+g `k`: dialog "Go To", "Invalid reference. Please try again." with OK (k is not a list name; `xs` selected the whole column in E10).
Click the row 1 number: whole row 1 is selected (bottom bar `1`). ctrl+c, Down x4 to row 5, ctrl+v: dialog "Data Loss", "This operation may overwrite data in the current column(s). Do you wish to proceed?" with OK and Cancel. Escape cancels: nothing pasted. OK was not pressed.
Screenshots: pages-shots-6/E11-click-column-K-name-cell.png, E11-paste-name-cell-incompatible-sizes.png, E11-goto-k-invalid-reference.png, E11-click-row-1-header.png, E11-row-copy-row-5-selected.png, E11-paste-row-data-loss-dialog.png, E11-row-paste-cancelled-nothing-pasted.png
Not run: whole-column copy and paste (no way found to select a whole column other than Go To a list name), paste of row with OK pressed.
Differs from CASSim or from this file's expectation? Not compared yet.

## E12 Insert and delete cell, row, column; Move Column
Settings: Radian / Automatic / Real / Float 8. Insert Cell was tried on page 1.2 (column K). The rest on a new scratch Lists & Spreadsheet page 1.3 (A1:A3 = 1, 2, 3; B1:B3 = 4, 5, 6), so the linked lists stay intact. Insert Row at A12 on page 1.2 showed no visible change (empty region) and is not counted.

### E12 Menu > 2 Insert
Observed: 1 Insert Cell, 2 Insert Row, 3 Insert Column.
Screenshot: pages-shots-6/E12-insert-menu-items.png

### E12 Insert Cell (page 1.2, K1 holding 7, 8, 9)
Observed: K1 becomes empty and 7, 8, 9 move down to K2:K4.
Screenshot: pages-shots-6/E12-insert-cell-K1-shifts-down.png

### E12 Insert Row and Insert Column (page 1.3, cursor on B2)
Observed: Insert Row: a blank row 2 appears across all columns, old rows 2 and 3 move down to 3 and 4. Insert Column: a new empty column B appears, the old column B (4, 5, 6) becomes column C.
Screenshots: pages-shots-6/E12-scratch-sheet-1.3-before.png, E12-insert-row-at-2.png, E12-insert-column-at-B.png

### E12 Delete via context menus (right-click)
Single cell menu (E2): 1 Cut, 2 Copy, 3 Paste, 4 Insert Cell, 5 Delete Cell, 6 Fill, 7 Variables ▶, 8 Resize ▶, 9 Summary Plot, A Quick Graph (grey), B Color ▶. Delete Cell on C3 (value 5): the value below (6) moves up into C3.
Row menu (right-click the row number, row selected with Menu > Actions > Select > Select Row): 1 Cut, 2 Copy, 3 Paste, 4 Resize Row, 5 Insert Row, 6 Delete Row, 7 Color ▶. Delete Row on row 3: the row is removed and rows below move up.
Column menu (right-click the column letter, column selected with Select > Select Column): 1 Cut, 2 Copy, 3 Paste, 4 Insert Column, 5 Delete Column, 6 Move Column, 7 Resize ▶, 8 Data ▶, 9 Color ▶. Delete Column on A: the column is removed, the column to its right moves left.
Screenshots: pages-shots-6/E2-context-menu-single-cell.png, E12-delete-cell-C3-shifts-up.png, E2-context-menu-row.png, E12-delete-row-3.png, E2-context-menu-column.png, E12-delete-column-A.png

### E12 Menu > 1 Actions
Observed: 1 Move Column, 2 Resize ▶, 3 Select ▶, 4 Go To (Ctrl+G), 5 Recalculate (Ctrl+R), 6 Sort (grey with a single cell selected). No delete items in Actions.
Select ▶: 1 Select Row, 2 Select Column, 3 Select Formula Range (grey).
Screenshots: pages-shots-6/E12-actions-menu-items.png, E12-actions-select-submenu.png

### E12 Actions > 1 Move Column
Keys: select column B (value 4), Menu, 1, 1; Right; Return.
Observed: after choosing Move Column column B is highlighted; after Right a dark vertical bar appears at the right edge of column C; after Return the column holding 4 is in column C (B empty).
Screenshots: pages-shots-6/E12-move-column-B-selected.png, E12-move-column-marker-after-Right.png, E12-move-column-result-now-C.png

## E13 Resize
Settings: Radian / Automatic / Real / Float 8. Scratch page 1.3, column C (value 4) selected.

### E13 Actions > 2 Resize
Observed: 1 Resize Column Width, 2 Maximize Column Width, 3 Minimize Column Width, 4 Resize Row Height (grey). With the column already at maximum width, 2 Maximize Column Width is greyed too and 1 and 3 stay active.
Screenshots: pages-shots-6/E13-actions-resize-submenu.png, E13-menu-when-column-maximised.png

### E13 Resize Column Width
Keys: Menu, 1, 2, 1; Right, Right; Return.
Observed: column C is highlighted with a blue frame; after Right x2 a hand pointer appears at the right edge of the header and the column is wider (about 24 px on the 499 px zoom for two presses); after Return the column keeps the new width and the hand disappears.
Screenshots: pages-shots-6/E13-resize-column-width-mode.png, E13-resize-column-C-after-Right-x2.png, E13-resize-after-Return.png, E13-resize-confirmed-final.png

### E13 Maximize and Minimize Column Width
Observed: Maximize makes column C fill the whole visible width of the screen (columns A and B scroll off to the left edge, only a sliver left). Minimize returns it to a narrow width (columns D, E, F visible again to the right; value 4 still shown).
Screenshots: pages-shots-6/E13-maximize-column-width-C.png, E13-minimize-column-width-C.png

### E13 Too-wide numbers and dragging the column edge
Keys: in C2 `123456789012345`, Return; in C3 `0.000012345678`, Return (narrow column).
Observed: C2 shows `1234...` and C3 `0.00...`, both left-aligned and cut off with an ellipsis. Select C3: a yellow tooltip shows `1.2345678ᴇ-5` and the edit field reads `1.2345678ᴇ-5`.
Dragging the column edge in the header from the C/D boundary to the right widens C: C2 then shows `123456789...` (still cut off), C3 shows `0.00001235`.
Screenshots: pages-shots-6/E13-too-wide-numbers-truncated.png, E13-C3-tooltip-and-edit-field.png, E13-drag-column-edge-wider.png

### E13 Incidental
After Minimize, my first attempt to repeat the menu keys while File Explorer was in front sent the digits into a Two-Variable Statistics dialog (X List showed `3`); a Windows "Warning: Please close any open dialogs before performing this action." with OK appeared; both were closed (OK, then Cancel). Not a CASSim behaviour.
Screenshot: pages-shots-6/E13-unexpected-two-variable-stats-dialog.png
Not run: Resize Row Height (grey in this state), Resize items in the context menus.

## E18 Sort (Menu > 1 Actions > 6 Sort)
Settings: Radian / Automatic / Real / Float 8. New scratch page 1.4: A1:A4 = 9, 3, 7, 1; B1:B4 = a, d, c, b; C formula row `=a[]*2` (values 18, 6, 14, 2). Block A1:C4 selected with shift+arrows.

### E18 Sort with a formula column in the range
Observed: Menu, 1, 6 gives a dialog "Data Loss": "This operation may overwrite data in the current column(s). Do you wish to proceed?" OK, Cancel. OK opens the dialog "Sort": Range a1:c4, Sort By: a (drop-down), Sort: Ascending (drop-down), OK, Cancel.
Pressing Return in the Sort dialog closed it and nothing was sorted (rows stayed 9, 3, 7, 1). Clicking OK on screen sorted by a ascending: rows become 1/b/2, 3/d/6, 7/c/14, 9/a/18; the rows move together across columns. After the sort the formula row of column C is empty: C2 shows the constant `=6` in its edit field, the `=a[]*2` formula is gone.
Screenshots: pages-shots-6/E18-sort-range-selected-incl-formula-column.png, E18-sort-data-loss-dialog.png, E18-sort-dialog.png, E18-after-Return-in-sort-dialog-unchanged.png, E18-sorted-by-a-ascending-clicking-OK.png

### E18 Sort options and descending on a text column
Second run (no Data Loss dialog this time, the formula column no longer exists): Sort drop-down items Ascending, Descending. Sort By drop-down items a, b, c (the column names of the range).
Sort By b, Descending, click OK: rows become 3/d/6, 7/c/14, 1/b/2, 9/a/18.
Screenshots: pages-shots-6/E18-sort-dialog-second-run.png, E18-sort-order-dropdown.png, E18-sort-by-dropdown-a-b-c.png, E18-sort-dialog-b-descending.png, E18-sorted-by-b-descending.png
Not run: Sort of linked lists with more than one key, Sort with a block that cuts a column.

## Also seen (for part F)
With a Summary Plot split page (E14) and the plot pane focused, Menu shows 1 Plot Type ▶ (Dot Plot, Box Plot, Histogram, Normal Probability Plot, Scatter Plot, XY Line Plot, Dot Chart, Bar Chart, Pie Chart; all grey except Pie Chart highlighted for the category plot), 2 Plot Properties, 3 Actions, 4 Analyze, 5 Window/Zoom, 6 Settings...
Screenshot: pages-shots-6/F-plot-type-menu-summary-plot-pane.png

---

## E20 / E21 / E23: cell errors, void cells, random cells (page 1.4, column D)

Settings: Radian / Automatic / Real / Float 8 (checked, title bar RAD).

### E20 `=1/0`
Settings: as above. Keys: D1, type `=1/0`, Return. Observed: cell shows `#UNDEF`, no dialog. Screenshot: `pages-shots-6/E20-1-div-0-UNDEF.png`. Differs from CASSim or from this file's expectation? Not compared yet.

### E20 number plus string
Keys: D2 `=a1+"x"` (A1 = 3), Return. Observed: cell shows `"x"+3` (unevaluated sum, no error dialog). Screenshot: `E20-a1-plus-string-x.png`. Differs? Not compared yet.

### E20 undefined name in a formula
Keys: D3 `=undefinedname`, Return. Observed: dialog "Syntax Error / Syntax error during insertion." with OK; after OK the cell is still being edited; Escape cancels. This is the same message as the earlier unsolved E16 case, so that case was an undefined/invalid name. Screenshots: `E20-undefinedname-syntax-error.png`, `E20-undefinedname-after-OK-still-editing.png`. Differs? Not compared yet.

### E21 void cell
Keys: D3 `_`, Return. Observed: cell shows `_` (void). Screenshot: `E21-void-underscore-D3.png`. Differs? Not compared yet.

### E21 `=mean(` over ranges with gaps and errors
Keys: D4 `=mean(c1:c3)` ; D5 `=mean(c1:c6)` (C5, C6 empty); D6 `=mean(d1:d4)` (contains #UNDEF). C = 6, 14, 2, 18 constants.
Observed: D4 = `22/3`; D5 = `10` (empty cells ignored, mean of 6,14,2,18); D6 = `#UNDEF`. Screenshots: `E21-mean-c1-c3-D4.png`, `E21-mean-with-gaps-and-undef.png`. Differs? Not compared yet.

### E23 `randint(1,6,5)` in a cell
Keys: D8 `=randint(1,6,5)`, Return. Observed: dialog "Syntax Error in Cell: d8 / Syntax" with OK; after OK the cell shows `#ERR`. (A list result does not fit a cell.) Screenshots: `E23-randint-1-6-5-syntax-error-dialog.png`, `E23-randint-list-cell-ERR.png`. Differs? Not compared yet.

### E23 `randint(1,100)` and ctrl+R
Keys: D9 `=randint(1,100)`, Return; then ctrl+R twice. Observed: first value 74. Each ctrl+R recalculates the sheet: the same Syntax Error in Cell: d8 dialog appears again (D8 still holds the list formula), OK dismisses it, and D9 changes (74, then 96, then 1). Screenshots: `E23-randint-1-100-D9-74.png`, `E23-ctrlR-D9-96-after-dialog.png`, `E23-ctrlR-D9-1-second.png`. Differs? Not compared yet.

---

## Lists for Part E (end of this run)

### Run
E0 setup, E2 (single cell, row, column context menus), E3, E5 (Auto and Approximate), E6, E7 (except Conflict Detected), E10, E11 (except whole-column copy), E12 (column insert/delete/move), E13, E14 (menu lists, Generate Sequence, Summary Plot), E18, E20 (div by zero, string sum, undefined name), E21 (void, mean with gaps/errors), E23 (randint cell, ctrl+R).

### Not run (with reason)
E20 differing list lengths; E22 other Float settings; E24 last column; E2 block-of-cells context menu; E4 keys/mouse sweep; E15 other regressions; E16 One-Var with Frequency List and category run; E17 other distributions/tests; E7 Conflict Detected buttons (could not reproduce); E14 Data Capture Auto/Manual, Random items, other List Math/Operations items, Fill from menu on a column, Clear Data, Quick Graph with xs,ys; E11 whole-column copy; E12 Insert Row on main sheet. Reason: stopped at the point of hand-back for this session; moved to the check-6 remaining list.

### Also seen, not covered by the brief
Plot Type menu inside the Summary Plot pane (see E14 section); naming a data column `qq` silently replaced its contents; Summary Plot with a category list gives "Invalid summary list. The list must be numeric."; typed non-"=" entries (`2^0.5`, `sqrt(2)`, `pi`) stay as text but are usable numerically in formulas.
