# Part H results: split pages (TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view)

Settings for every row unless said: Document Settings Radian / Automatic / Real / Float 8, Document2, Keypad + SideScreen view at 250% zoom. Pane sizes are in handheld pixels, worked out from a zoom of the screen (320 px wide); they are read by eye from the picture, good to about 3 px. Rows are written as I went. Screenshots for H were not saved (the zooms were read on screen), so each row says "not saved".

Note on keys: on this emulator the PC key chord ctrl+Tab does NOT move focus between panes. It switched to the next open document (Document1 appeared, a blank page 1.1 reading "Press menu"; pressing ctrl+Tab again came back to Document2). Clicking the on-screen `ctrl` key and then the on-screen `tab` key did move the focus (H4).

## H1 - Doc > 5 Page Layout menu, Custom Split, Select Layout
- Keys: click the doc key, 5 Page Layout (on a Calculator page 1.1); then 2 Select Layout.
- Observed: Page Layout submenu: 1 Custom Split, 2 Select Layout (submenu arrow), 3 Select App (Ctrl+K), 4 Swap Applications (grey on a one-pane page), 5 Delete Application, 6 Delete Page, 7 Group (Ctrl+4), 8 Ungroup (Ctrl+6, grey). Select Layout submenu: 1 Layout 1 (grey on a one-pane page, it is the current one), 2 Layout 2, 3 Layout 3, 4 Layout 4, 5 Layout 5, 6 Layout 6, 7 Layout 7, 8 Layout 8, each with a small picture. What they give when applied (from H8/H9): 1 one full pane; 2 two panes side by side; 3 two panes one above the other; 4 one wide pane on top, two side by side below; 5 two side by side on top, one wide pane below; 6 left column of two stacked panes, one tall pane on the right; 7 one tall pane on the left, two stacked panes on the right; 8 four panes (2 by 2). No scroll arrow in the layout list (8 items in all). Doc > 3 View submenu: 1 Back (Ctrl+Left), 2 Forward (Ctrl+Right), 3 Page Sorter (Ctrl+Up). Doc > 2 Edit submenu: 1 Undo (Ctrl+Z), 2 Redo (Ctrl+Y, grey), 3 Cut (Ctrl+X, grey), 4 Copy (Ctrl+C, grey), 5 Paste (Ctrl+V), 6 Delete, 7 Color (grey, submenu arrow).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H2 - Select Layout 2 on a new Calculator page
- Keys: on page 1.1 ctrl+i then 1 (new Calculator page, inserted as 1.2, right after 1.1); doc > 5 > 2 > Layout 2.
- Observed: the page split into left and right halves; the Calculator stays on the left, the new right pane reads `Press menu` (centred, no other text). The focus stays on the left pane (the entry-line cursor shows in it).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H3 - A Data & Statistics app in the empty pane
- Keys: click the right pane (or press Menu with it focused); the list `1 Add Calculator, 2 Add Graphs, 3 Add Geometry, 4 Add Lists & Spreadsheet, 5 Add Data & Statistics, 6 Add Notes, 7 Add Vernier DataQuest, 8 Add Widget, 9 Add Program Editor (submenu), A Add Python (submenu)` appears; press 5.
- Observed: clicking in an empty pane opens that same app list at once (the same list as ctrl+i). After 5 the right pane became a Data & Statistics case plot captioned `Caption: cat` (it picks the first list in the problem, as on a full page), x and y axes both "Click to add variable". It took the focus (see H4). The dots arrive by the usual lerp.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H4 - Moving focus between panes
- Keys tried: PC ctrl+Tab; a mouse click in a pane; on-screen `ctrl` then on-screen `tab`.
- Observed: ctrl+Tab on the PC keyboard did not move pane focus (it switched document, see the note above). A click in a pane focuses it (a click in an empty pane also opens the app list, H3). On-screen ctrl then tab moved the focus left to right and, pressed again, right back to left (wraps). Focus marking: the focused pane has a coloured border (pink/magenta for Data & Statistics); the Calculator pane's border is a thin grey-blue line and its entry-line text cursor is a solid vertical bar, while the unfocused Calculator shows a dashed rectangle as the cursor.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H5 - Menu with each pane focused
- Keys: click the pane, click the Menu key.
- Observed: Data & Statistics focused: a menu with 1 Plot Type (grey on a case plot), 2 Plot Properties, 3 Actions, 4 Analyze (grey), 5 Window/Zoom (grey), 6 Settings. Calculator focused: 1 Actions, 2 Number, 3 Algebra, 4 Calculus, 5 Probability, 6 Statistics, 7 Matrix & Vector, 8 Finance, 9 Functions & Programs (the same list as on a full Calculator page). The menu opens at the left edge of the screen over the left pane in both cases, with no title line, and is that app's own menu.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H6 - ctrl+Z, ctrl+G, ctrl+T, Esc with each pane focused
- Keys run: in the left Calculator pane type `2+2`, Return (answer 4); click on-screen ctrl and tab to focus the D&S pane; press ctrl+z.
- Observed: ctrl+Z with the D&S pane focused undid the last change in the document, which was the Calculator evaluation: the left pane then showed `2+2` with no answer line. So Undo is not tied to the focused pane. Not run: ctrl+G, ctrl+T and Esc per pane.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H7 - Divider drag and Custom Split
- Keys: Doc > 5 Page Layout > 1 Custom Split (page laid out as layout 4: one wide pane on top, two below); then arrow keys, then Return; then a mouse drag of the vertical divider.
- Observed: on choosing Custom Split a yellow tip appears: `Use + or − to choose a layout` and the dividers show as thin lines. Right arrow moves the vertical divider to the right about 5 px per press (3 presses: 160 px to about 176 px); at the limit (after about 40 presses) the right pane is about 15 px wide and the divider will not go further (20 more presses: no change). Up arrow moves the horizontal divider up; 60 presses took it to the top, leaving the top pane about 15 px high. While in the mode the dividers are drawn blue. Return ended the mode and kept the sizes. A mouse drag on the vertical divider (from the right edge to the middle) worked and the divider sat exactly where the mouse was released. The + and − keys were not tried.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H8 - Two-pane layouts, pane sizes
- Observed: Layout 2 (side by side): the divider is at the centre, 160 px, so the two panes are 160 by full height each. Layout 3 (one above the other): the divider is at the middle of the area below the tab bar, each pane about 320 by 110 px (approximately; the tab/title bar takes the top of the 240 px screen). A thin divider bar about 3 px wide.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H9 - Three- and four-pane layouts
- Observed: Layout 4: top pane the full width (about 320 by 110 px), below it two panes of 160 px wide each (new empty pane left, the Data & Statistics app to its right). Layout 5: the top has Calculator left and D&S right (160 px each), the bottom pane full width reading `Press menu`. Layout 6: left column with Calculator over an empty pane (each about 160 by 110), the D&S pane the full height on the right. Layout 7: Calculator the full height on the left, D&S above an empty pane on the right. Layout 8: four equal panes, Calculator top left, D&S top right, two empty panes below, the dividers at about 160 px across and the middle of the height. When a layout with more panes is chosen, the apps keep their relative order and the new panes are empty (`Press menu`).
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H10 - Delete Application
- Keys: with the D&S pane focused (layout 8), Doc > 5 Page Layout > 5 Delete Application; then Doc > 2 Edit > 6 Delete with the Calculator pane focused (empty entry).
- Observed: Delete Application removed the Data & Statistics app, and its pane went: the layout went from four panes to three, the Calculator widening across the full top row (the D&S pane's space was taken by its left neighbour) with the two empty `Press menu` panes still below. The focus went to the Calculator pane (cursor shown). Edit > Delete with a Calculator entry line as focus changed nothing visible. A pane that is empty can be filled (click it, H3). Not run: what Delete Page does to a split page.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H13 - Residual plot on a Data & Statistics scatter plot
- Keys: page with the scatter plot of `ys` against `xs` and a linear regression (equation y = 1.99762x + 0.035714, r² = 0.998839 shown); Menu > 4 Analyze > 7 Residuals > 2 Show Residual Plot; then the same path again.
- Observed: Analyze menu on this plot: 1 Hide Linear (mx+b), 2 Add Movable Line, 3 Lock Intercept at Zero (grey), 4 Plot Function, 5 Shade Under Function, 6 Regression (submenu), 7 Residuals (submenu), 8 Plot Value, 9 Show Normal PDF (grey), A Graph Trace. Residuals submenu: 1 Show Residual Squares, 2 Show Residual Plot. After 2: the scatter plot shrank to the top part of the same page and a second plot appeared below it: y axis `Residual` (0.20, 0.00, -0.20), the same x axis (xs 1 to 8), one open circle per case (blue for the cases that were selected on the scatter). Both share one pink border and one Menu (the Data & Statistics menu), so it is part of the one app, not a pane of the page layout; there was no separate focus to move to it. The second use of the same menu path removed the residual plot at once and the scatter plot went back to full height. (The menu item text for the second use was not read before the click; the plot did go away.)
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H15 - Page Sorter with a split page in the document
- Keys: ctrl+Up (after a click on the status bar); a right click on a tile; Return.
- Observed: the Page Sorter (title bar `*Unsaved Document`, `Problem 1` header with a count of 11 pages at the top right) shows each page as a miniature of what it looks like, so a split page is drawn as its panes in miniature (the two empty panes show `Press menu` text, the sheet + charts page shows the sheet on the left and two charts stacked on the right). The selected tile has a blue border. The tiles are 3 across. Return on the selected tile opens that page. Right click on a tile: 1 Cut, 2 Copy, 3 Paste (grey), 4 Delete, 5 Move, 6 Group, 7 Ungroup, 8 Insert Problem, 9 Insert Page.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H17 - Group and Ungroup
- Observed: only the menus were looked at: Doc > 5 Page Layout has 7 Group (Ctrl+4) and 8 Ungroup (Ctrl+6, grey on an ungrouped page); the Page Sorter context menu has 6 Group and 7 Ungroup (both enabled with one tile selected). I did not run Group or Ungroup, so what they do was not seen.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H18 - Leave a split page and come back
- Observed (from the part J work on the sheet + two charts page): after typing in the sheet (the sheet pane was focused), ctrl+Right to the next page and ctrl+Left back: the sheet pane was still the focused one (teal border round it, cell cursor in the cell I had left). Only that case was seen (sheet focused); focus on the other panes was not tested.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

## H19 - Type in a cell that the other pane plots
- Observed (from J15): on the split page the sheet column `pets` is plotted by the Dot Chart in the pane on the right. Typing `"fish` and moving the cursor changed nothing in the plot while the cell was still being edited; after Return the dot chart redrew (dog 5 to 4 dots, fish 1 to 2) and the sheet kept the focus. Adding an 11th entry added a new category to the chart at once on Return as well. So the redraw is on entering the cell, not on each key.
- Screenshot: not saved.
- Differs from CASSim or from this file's expectation? Not compared yet.

---
## Lists for part H (run 2)

### Run
H1, H2, H3, H4, H5, H6 (ctrl+Z only), H7, H8, H9, H10, H13, H15, H18 (one case), H19 (from J15). H17: menus only.

### Not run
H11 (Quick Graph from the sheet with `xs`, `ys`; the J11 Quick Graph on `pets` is in the J file), H12 (Graphs page ctrl+T), H14 (Normal Cdf shade on the sheet), H16 (swap applications: Doc > Page Layout > 4 Swap Applications was grey on a one-pane page, not tried on a two-pane page), the Group / Ungroup actions of H17, ctrl+G, ctrl+T and Esc in H6. Reason: I ran out of time in this session; Part B, Part D (and D26 to D33), Part N, Part C and Part K were not started.

### Also seen, not covered by a row
- The PC key chord ctrl+Tab switches to the next open document on this emulator (not pane focus); see the note at the top.
- Clicking an empty pane opens the add-app list at once.
- Deleting the D&S pane in a four-pane layout merged its space into the Calculator pane (H10).
- A new Calculator page added with ctrl+i, 1 from page 1.1 is inserted as 1.2 and renumbers the following pages (the earlier 1.2 and 1.3 became 1.3 and 1.4).
- Document state at the end: Document2 has an extra test page 1.2 (made in H2 to H10; it now holds a thin Calculator strip across the top and two empty `Press menu` panes below, after the Custom Split). Delete it if the document is reused. The earlier pages follow it, renumbered by one.
