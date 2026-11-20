# Emulator sheet / Q results (check 6, run 5) - PARTIAL

Document5 (Handheld), Radian / Automatic / Real / Float 8. Page 1.4 is a Lists & Spreadsheet page with columns named xs (A), ys (B), d1 (C) by typing the list name in each column's name cell. Deviation: xs, ys and d1 hold the values changed by the R5-G1 drags (xs 4 is 4.435, ys 4 is 9.776, d1 has 4.536 and 7.536), not the brief's original lists.
Shots in pages-shots-6/.

## R5-Q1 Quick Graph
Keys and observed:
- A cell range selected with shift+Down (C1:C8): in Menu 3 Data, 1 Generate Sequence, 4 Clear Data, 5 Random, 6 List Math, 7 List Operations and 9 Quick Graph are grey; 3 Fill and 8 Summary Plot are enabled; Menu 2 Insert is grey. (Also gives the S leftover "Fill using a shift+Down range": the item is enabled; I did not run Fill.)
- Whole column d1 selected (Up to the name cell): Menu 3 Data has Generate Sequence, Data Capture ▶, Clear Data, Random ▶, List Math ▶, List Operations ▶, Summary Plot, Quick Graph enabled; 3 Fill grey. Quick Graph (3 9): the page splits left and right at about half each; the sheet is on the left (scrolled), a dot plot of d1 on the right with x axis d1 (2 to 9). The column stays highlighted in the sheet; I could not tell which pane had focus from the screen.
- ctrl+Z: the plot disappears and the full-width sheet returns with column C still selected. One ctrl+Z undid the whole Quick Graph.
- Columns xs and ys selected together (Left Left, shift+Right): Quick Graph gives a scatter plot on the right half, x = xs, y = ys, with many points drawn selected. ctrl+Z removes it the same way.
Shots: R5-Q1-range-selected-data-menu, -column-d1-selected, -data-menu-column-selected, -quickgraph-d1, -d1-after-ctrlZ, -columns-xs-ys-selected, -quickgraph-xs-ys, -xs-ys-after-ctrlZ.

## R5-Q2 Summary Plot (Menu 3 8)
Dialog "Summary Plot": X List (prefilled xs from the selection), Summary List (prefilled ys), Display On (default Split Page; options Split Page, New Page), OK, Cancel. Escape in the open Display On drop-down closed only the drop-down.
- Split Page: sheet on the left, a bar-style summary plot of ys against xs on the right (axis labels xs and ys, y 0 to 18, bars from 1 to 8), and a small table icon at the bottom left of the plot.
- New Page (after ctrl+Z of the first): a new page 1.5 with the same plot full width.
Shots: R5-Q2-summary-plot-dialog, -display-on-options, -split-page-result, -dialog-new-page, -new-page-result.

## R5-Q3 save, close, reopen
Keys: on page 1.4 I re-made the split Quick Graph of xs and ys (the earlier one had been undone), pressed ctrl+S; the Save dialog was hidden from my screenshots, I typed C:\dev\CASSim-capture\R5-q.tns and Return. The file on disk is Document5.tns, not R5-q.tns (the dialog's own name was used; deviation). Closed the tab, ctrl+O (a Java "Open" dialog), double-clicked Document5.tns.
Observed after reopening (pages 1.1 to 1.5):
- 1.1 Calculator: lists and values as before (with the dragged values).
- 1.2 histogram of d1: back, bars un-highlighted (earlier selection gone).
- 1.3 scatter with the regression line and label "y = 1.99209·x+0.199..." and "r² = 0.995402": back; the points are no longer drawn selected; the label runs off the right edge of the screen.
- 1.4 split page: sheet on the left, scatter of xs against ys on the right, as before; the sheet cursor is at A1 and no columns are selected.
- 1.5 summary plot New Page: back, axes xs and ys, bars unchanged.
So split pages, plots and axis variables came back; the selection highlights and the sheet cursor position did not. The Q2 Split Page version was not in the saved file (undone before saving) and the Q1 d1 split was not either, so only the xs/ys split and the New Page summary plot were checked.
Shots: R5-Q3-before-save-split-page, -reopened-page-1-1, -reopened-histogram, -reopened-regression, -reopened-split-page, -reopened-summary-plot-new-page.

## Run / not run / also seen
Run: R5-Q1, R5-Q2, R5-Q3 (partly: only the xs/ys split page and the New Page summary plot were in the saved file).
Not run: the S leftovers other than the Fill menu state, E rows, Insert/Delete Column and Cell, Data menu leaves. Reason: time in this session.
Also seen, not covered: the Open dialog is a Java dialog; typing a path into it did nothing until I double-clicked the file.

## Computer view (page size: Computer) - split-page work

Document6, Page Size: Computer (status bar). Settings: Radian, Automatic, Real, Float 8 (checked). xs, ys, d1 defined on a Calculator page 1.1, then a Lists & Spreadsheet page 1.2 added with ctrl+i then "4:Add Lists & Spreadsheet". Columns A, B, C named xs, ys, d1 by clicking each name cell and typing.

### R5-Q1 (Computer view) Quick Graph split
- Keys: right-click the column A name cell. Context menu (Computer view, name cell): 1 Cut (grey), 2 Copy (grey), 3 Paste, 4 Variables ▶ (grey), 5 Symbols…, 6 Math Templates…, 7 Generate Sequence, 8 Data Capture ▶, 9 Clear Data, A Resize ▶, B Summary Plot, C Quick Graph, D Color ▶. Clicked C Quick Graph.
- Observed: page splits about half and half, sheet left, dot plot right; "Click to add variable" on the vertical axis; eight dots at 1..8, axis label xs. Page area is larger than on the handheld, so all of columns A-C and rows 1-8 stay visible beside the plot.
- Screenshot: pages-shots-6/R5-Q1-computer-quickgraph-xs.png
- Differs from CASSim or this file's expectation? Not compared with the simulator.
- A right-click on a data cell (A2) gives a different menu: 1 Cut, 2 Copy, 3 Paste, 4 Insert Cell, 5 Delete Cell, 6 Fill, 7 Variables ▶ (grey), 8 Resize ▶, 9 Summary Plot, A Quick Graph, B Color ▶.
- ctrl+Z removed the Quick Graph split.

### R5-Q2 (Computer view) Summary Plot, Split Page
- Keys: right-click name cell A, B Summary Plot. Dialog: X List xs, Summary List d1, Display On Split Page (all as offered). OK.
- Observed: histogram of d1 against xs on the right half, bars 1-9 on x, heights 2,4,4,4,5,5,7,9, y axis 0-10. Small table icon at the bottom left of the plot.
- Screenshot: pages-shots-6/R5-Q2-computer-summaryplot-split.png
- Right-click on the histogram: 1 Box Plot, 2 Bin Settings ▶, 3 Zoom ▶, 4 Color ▶.
- Differs? Not compared with the simulator.

### Deviations / also seen (Computer view)
- Clicking a name cell then pressing Up did not move the selection, so I clicked the name cell directly.
- A wrong click (menu item 3 Paste on the name cell after an undo) put `xs:=a5` into the name-cell formula bar; ctrl+Z and Escape cancelled it, column A name stayed xs. Not a result row.
- Stat tests (Menu 4 Statistics) not reached in Computer view: the on-screen menu key (clicked), ctrl+m, the right-click menus and the top Tools menu (Live Presenter, Screen Capture, Transfer Tool, Prepare Handhelds, Variables, Refresh Libraries, Install OS) gave no Statistics menu. So I2 stat-test panes and the 2x2 split were NOT captured in Computer view.
- Summary Plot "New Page" in Computer view not run.

## Handheld sheet rows run later (Document7, page 1.4 Lists & Spreadsheet, RAD / Automatic / Real / Float 8)

### R5-E7 (rest) column names
Keys: clicked the name cell of column A and typed each name, Return.
Observed:
- `1a`: dialog "Syntax Error" / "Cannot accept change: Invalid input." with an OK button; the name cell stayed in edit mode showing 1a after OK; Escape cancelled.
- `sin`: the same dialog, same text.
- var key in an empty name cell: a drop-down of variables opens with function-type items f1, f2, then ws (list icon), then zzz_p1, zzz_p2, zzz_p3, zzz_p4 (function icons; I did not define these; the list may scroll further).
- `ws` (an existing list): the column simply links to ws and shows 1, 2, 3; no Conflict dialog. The Conflict Detected dialog for a name like d1 was not re-run (no d1 in this document); its buttons are not recorded here.
Screenshots: R5-E7-name-1a-syntax-error, R5-E7-name-sin-syntax-error, R5-E7-var-key-in-name-cell-list, R5-E7-name-existing-list-ws-links.
Differs from CASSim or from this file's expectation? Not compared.

### R5-E4 keys and mouse
Keys, on page 1.4 with column A linked to ws (1, 2, 3):
- click A1, Down: A2; Right: B2; Tab from B2: the status cell read just "B" (the column-level cell, I think; the zoom was small); shift+Tab: back to B2; Return and Escape left B2 selected; ctrl+Right and ctrl+Down left the selection at B2 (no visible change).
- Typing 9 in B2 then Return: B2 shows 9 and the selection moves DOWN to B3.
- Up then Delete on B2: B2 cleared. ctrl+Z: 9 returned. ctrl+Y: cleared again.
- Double-click a linked-list cell (A2): the cell enters edit mode with its entry `=2` selected (the entry line also showed `=2`); Escape leaves editing; the entry line still reads `=2` afterwards.
- Not run: drag selection, mouse wheel.
Screenshot: R5-E4-end-state-after-key-sweep (end state only; the steps were read from zoom views).
Differs? Not compared.

### R5-S19 typing over and Return on a filled cell
Keys: C1 typed 7 Return; clicked C1, typed 8 Return; clicked C1, Return.
Observed: C1 is 8 (typing replaced the 7, not 78). Return on the filled cell starts editing with `8` selected in the cell and entry line; it does not move down.
Screenshot: R5-S19-return-on-filled-cell-edits.

### R5-S Data menu and Fill with a shift+Down range
Keys: C1:C3 holding 3, 1, 2 selected with click on C1 then shift+Down twice (status shows C1:C3). Menu > 3 Data.
Observed: with that block selected, Data lists 1 Generate Sequence (grey), 2 Data Capture > (grey), 3 Fill (black), 4 Clear Data (grey), 5 Random > (grey), 6 List Math > (grey), 7 List Operations > (grey), 8 Summary Plot (black), 9 Quick Graph (grey). Top menu: 1 Actions, 2 Insert (grey), 3 Data, 4 Statistics (grey), 5 Table. Pressing 3 for Fill: no prompt or visible change; typing 5 and Return after it also changed nothing (cells stayed 3, 1, 2). Fill again showed no visible effect (fifth try).
Screenshots: R5-S-data-menu-with-range-selected, R5-S-fill-range-selected-no-effect.

### R5-S20 sort and ctrl+Z
Keys: C1:C3 selected; Menu > 1 Actions > 6 Sort.
Observed Actions list with the block selected: 1 Move Column (grey), 2 Resize > (grey), 3 Select > (grey), 4 Go To (Ctrl+G), 5 Recalculate (Ctrl+R), 6 Sort. Sort dialog: Range c1:c3, Sort By c, Sort Ascending, OK, Cancel. OK: C1:C3 became 1, 2, 3. One ctrl+Z: back to 3, 1, 2.
Not run: Fill with =g1 then ctrl+Z; Insert Row at 2 then ctrl+Z (Insert was grey with the block selected).
Screenshots: R5-S20-actions-menu-range-selected, R5-S20-sort-dialog-c1-c3, R5-S20-after-sort-ascending, R5-S20-after-ctrlz-sort-undone.

## Hand-back lists (emulator-sheet5-results.md, as of now)
### Run
- Handheld: Q1, Q2, Q3, E7 (invalid names, var key, existing list), E4 (partial), S19, Data menu with a block selected, Fill with a shift+Down range, S20 sort and ctrl+Z.
- Computer view: Q1, Q2 (Split Page).
### Not run (reason)
- Insert Column, Delete Column, Insert Cell, Generate Sequence, Random, List Math and List Operations leaves (grey with a block selected; need a single cell or column selected): not attempted.
- E7 Cancel button and Conflict Detected buttons: not run.
- E11 whole-column copy and paste: not run in this pass.
- S20 Fill and Insert Row parts: not run.
- Computer view of E, S and Data rows; Summary Plot New Page: not run. Statistics menu not reachable in Computer view.
### Also seen, not covered
- Cells of a column linked to a list show `=2` style entries in the entry line.
- A click on the right half of a split page lands in the other app (it took my typing into the plot pane once).

## Data menu leaves (handheld, Document7 page 1.4) - added after the lists above
Settings: RAD / Automatic / Real / Float 8. Menu > 3 Data.
- With a single data cell selected (C1): 1 Generate Sequence, 2 Data Capture >, 3 Fill, 4 Clear Data (grey), 5 Random >, 6 List Math >, 7 List Operations >, 8 Summary Plot, 9 Quick Graph (grey). (Fill is black here; with a block it was also black; in the later menu below it was grey when the name cell was the selection.)
- 1 Generate Sequence dialog "Sequence": Formula: u(n)= (empty, focused), Initial Terms: (empty), n0: 1, nMax: 255, nStep: 1, Ceiling Value: (empty), OK, Cancel. Cancel clicked; nothing entered.
- 5 Random > : 1 Number, 2 Integer, 3 Binomial, 4 Normal, 5 Sample.
- 6 List Math > : 1 Minimum, 2 Maximum, 3 Mean, 4 Median, 5 Sum of Elements, 6 Product of Elements, 7 Sample Standard Deviation, 8 Sample Variance, 9 Population Standard Deviation, A Population Variance (the list may continue below A; I did not scroll it).
- 7 List Operations > : 1 Cumulative Sum List, 2 Difference List, 3 Augment, 4 Convert Matrix to List (grey), 5 Left, 6 Mid, 7 Right.
- When the second menu was opened the selection was the column name cell (status bar showed just C): Fill grey, Clear Data black. Selection state therefore changes the grey items.
Screenshots: R5-S-data-menu-single-cell, R5-S-generate-sequence-dialog, R5-S-random-submenu, R5-S-list-math-submenu, R5-S-list-operations-submenu.
Not run: the leaves themselves (Random Number etc.), Data Capture submenu, Insert Column/Delete Column/Insert Cell.
Differs from CASSim? Not compared.
