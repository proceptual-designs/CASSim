# Documents and sharing

A **document** holds Problems; a Problem holds Pages. At the moment only the Calculator page works; Graphs, Lists & Spreadsheet, Data & Statistics and Notes pages can be inserted, but they only say they are not built yet. Variables belong to a Problem, so a new Problem starts clean.

- Add a page with Ctrl+I (on the keypad: ctrl then doc), or Doc, Insert.
- Move between pages with Alt+Left and Alt+Right, or click the page list.
- The **Page Sorter** (Ctrl+Up) shows the pages as tiles on the calculator's screen, a row per Problem, so the keypad still works. The arrow keys move the highlight (left and right through the pages, up and down between Problems), **Enter** or **Esc** opens the highlighted page, and **Delete** (or **del**) removes it. Tap a tile to highlight it and tap it again to open it. The buttons above the tiles move the page earlier or later, delete it, undo, redo and close the sorter.

## Saving

CASSim **autosaves** what you are working on, so a reload or crash loses nothing. The autosave is not the same as saving: it keeps your work in progress, not a named copy.

**Doc, File, Save** (Ctrl+S) keeps the document in this browser under a name. The first time, it asks for the name; **Save As** saves under a new one. The name shows in the middle of the screen's title bar, with a `*` in front while there are changes you have not saved. **Doc, File, Open Document** (Ctrl+O) lists your saved documents, newest first; the bin icon deletes one. New Document and Open ask before throwing away unsaved changes.

Saved documents live on this device and browser only, and clearing the site's data removes them. To keep a copy elsewhere, or move it to another computer, use **Doc, File, Export File…**: it downloads a `.cassim.json` file. **Import File…** opens one again and recalculates every entry, so the answers match your current settings.

## Sharing

**Doc, File, Copy share link** puts the document in a web link. When someone opens the link, CASSim asks first, then replaces what is open with the shared document. Nothing is sent to a server: the document is part of the link itself. Very large documents are too long for a link, so export a file and send that instead.

Opening a shared link or file never runs anything by itself.

## Privacy

CASSim has no server, no account, no telemetry and no analytics.
