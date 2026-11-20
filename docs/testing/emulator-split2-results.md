# Emulator check 6, run 5: H rows (emulator-split2-results.md)

TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, Document7. Observations only; nothing here is simulator verification.

## R5-H1 (handheld)
Settings: Document7, page 1.3 Lists & Spreadsheet added with ctrl+i then 4; RAD / Automatic / Real / Float 8. Deviation from the brief: the brief says column F and G; I used column A (named ws) and column B and cell C1 because F and G were off screen. Column letters are therefore not the brief's.
Keys: click A1, Up twice to the name cell, typed ws, Return, Down, typed 1, 2, 3 with Return each. Clicked B's formula row, typed =ws*2, Return. Clicked C1, typed =ws[2], Return.
Observed: no Column or Variable prompt appeared for either entry. B1, B2, B3 show 2, 4, 6. The B column formula row shows =ws*2. The status line for B1 read =2 (screenshot R5-H1-colformula-ws-times-2). C1 shows 2 and its entry line shows =ws[2] drawn with a boxed index (screenshot R5-H1-cell-ws-index-2).
Screenshots: R5-H1-colformula-ws-times-2, R5-H1-cell-ws-index-2.
Differs from CASSim or from this file's expectation? Not compared in this pass.

## R5-H16 (handheld) - swap the two apps of a split page
Settings: Document7 page 1.2 (Graphs) with the table split opened by ctrl+T (graph left, table right).
Keys: doc key, 5 Page Layout, 4 Swap Applications.
Observed: Page Layout menu on a split page: 1 Custom Split, 2 Select Layout >, 3 Select App (Ctrl+K), 4 Swap Applications, 5 Delete Application, 6 Delete Page, 7 Group (grey), 8 Ungroup. After pressing 4 the panes did not move; a circular swap icon appeared over the graph pane (a swap mode). Pressing Return then swapped them: table left, graph right. On a single-app page, 4 Swap Applications is grey.
Screenshots: R5-H16-before-swap-graph-table-split, R5-H16-after-swap-applications-menu-item, R5-H16-after-return-table-left-graph-right.
Differs from CASSim or from this file's expectation? Not compared in this pass. Only Return was tried to finish the swap; other ways (arrow keys, click) not tried.

## R5-H17 (handheld) - Group and Ungroup
Settings: Document7, pages 1.2 Graphs and 1.3 Lists & Spreadsheet (ws data).
Keys: on page 1.2 (single app) doc key, 5 Page Layout: 7 Group (Ctrl+4) is enabled and 8 Ungroup (Ctrl+6) is grey. Pressed 7. Then doc, 5, 8.
Observed: Group merged pages 1.2 and 1.3 into one page 1.2 with the graph on the left and the spreadsheet on the right (the page tabs went from 1.1, 1.2, 1.3 to 1.1, 1.2). On the grouped page Group is grey and Ungroup is enabled. Ungroup restored separate pages 1.2 (Graphs, with the hello text) and 1.3 (spreadsheet).
Not tried: the Page Sorter context menu; Group of non-adjacent pages; keys ctrl+4 and ctrl+6 themselves (menu route only).
Screenshots: R5-H17-page-layout-menu-single-page, R5-H17-after-group-pages-merged, R5-H17-after-ungroup-pages-restored.
Differs? Not compared in this pass.

## R5-H14 (handheld) - Normal Cdf with Shade area
Settings: Document7 page 1.3 Lists & Spreadsheet, cell A1 selected (column A named ws holding 1, 2, 3).
Keys: Menu > 4 Statistics (the submenu showed Calculations >, Distributions >, Confidence Intervals >, Tests >), 2 Distributions. Typed digit 2 for Normal Cdf.
Observed Distributions list (first ten, list scrolls): 1 Normal Pdf..., 2 Normal Cdf..., 3 Inverse Normal..., 4 t Pdf..., 5 t Cdf..., 6 Inverse t..., 7 χ² Pdf..., 8 χ² Cdf..., 9 Inverse χ²..., A Binomial Pdf....
Normal Cdf dialog defaults: Lower Bound −∞ (selected), Upper Bound empty, μ 0, σ 1, Draw: Shade area (unticked), OK, Cancel. I typed 1 in Upper Bound (Tab from Lower Bound) and ticked Shade area by clicking its box, then clicked OK.
Result: the page split with the spreadsheet on the left and a Data & Statistics-style pane on the right (pink border, pane focused) showing the normal density curve, the label normPdf(x,0,1), shading left of x = 1 and an Area label starting .841 (cut off at the edge). The spreadsheet cell A1 was overwritten with the result: it showed 0.84134... (truncated) and its entry line began =normcdf(; B1 showed 1.6826... in that screenshot. The result went into the SELECTED cell, replacing my 1.
ctrl+Z (after clicking the status bar): A1 went back to 1; the plot pane stayed on the page. B1 looked empty in that screenshot (not investigated).
Screenshots: R5-H14-distributions-menu-top, R5-H14-normal-cdf-dialog-defaults, R5-H14-normal-cdf-dialog-filled-shade-ticked, R5-H14-after-ok-split-sheet-left-plot-right, R5-H14-after-ctrlz-cell-restored-plot-stays.
Differs from CASSim or from this file's expectation? Not compared in this pass. Not recorded: whether the new pane's Menu is the ordinary Data & Statistics menu.

## R5-H11
Already covered as R5-Q1 (xs, ys Quick Graph) in emulator-sheet5-results.md, handheld and Computer view.

## Hand-back lists
### Run
- R5-H1, R5-H14, R5-H16, R5-H17 (handheld only); H11 is in emulator-sheet5-results.md as R5-Q1.
### Not run (reason)
- H14 in Computer view: Statistics menu not reachable there.
- H1, H16, H17 in Computer view: not attempted; the document menu does not respond in Computer page size, so the Page Layout route is unreachable there.
### Also seen, not covered
- Swap Applications uses a swap mode finished with Return.
