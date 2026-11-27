# Documents and sharing

A **document** holds Problems; a Problem holds Pages. Calculator and Lists & Spreadsheet pages
work; Graphs, Data & Statistics and Notes can be inserted but are not built yet. Variables belong
to a Problem, so a new Problem starts clean.

- Add a page with Ctrl+I (on the keypad: ctrl then doc), or Doc, Insert.
- Add a Problem with Ctrl+Alt+I (on the keypad: shift then doc), or Doc, Insert. Choose the type
  of its first page from the picker.
- Move between pages with Ctrl+Left and Ctrl+Right (or Alt+Left and Alt+Right), or click the page list.
- The **Page sorter** (Ctrl+Up, or click the problem.page number at the top left of the screen) shows the pages as tiles on the calculator's screen, a row per Problem, so the keypad still works. The arrow keys move the highlight (left and right through the pages, up and down between Problems), **Enter** or **Esc** opens the highlighted page, and **Delete** (or **del**) removes it. Tap a tile to highlight it and tap it again to open it. The buttons above the tiles move the page earlier or later, delete it, undo, redo and close the sorter.
- Spreadsheet tiles show named columns; Data & Statistics tiles show the selected variables and plot type. Long previews are shortened to fit.

## Saving

CASSim **autosaves** what you are working on, so a reload or crash loses nothing. The autosave is not the same as saving: it keeps your work in progress, not a named copy.

**Doc, File, Save** (Ctrl+S) keeps the document in this browser under a name. The first time, it asks for the name; **Save as** saves under a new one. The name shows in the middle of the screen's title bar, with a `*` in front while there are changes you have not saved. **Doc, File, Open document** (Ctrl+O) lists your saved documents, newest first; the bin icon deletes one. New document and Open ask before throwing away unsaved changes.

Saved documents live on this device and browser only, and clearing the site's data removes them. To keep a copy elsewhere, or move it to another computer, use **Doc, File, Export file…**: it downloads a `.cassim.json` file. **Import file…** opens one again and recalculates every entry, so the answers match your current settings.

## Sharing

**Doc, File, Copy share link** puts the document in a web link. When someone opens the link, CASSim asks first, then replaces what is open with the shared document. Nothing is sent to a server: the document is part of the link itself. Very large documents are too long for a link, so export a file and send that instead.

Opening a shared link or file never runs anything by itself.

## Privacy

CASSim has no server, no account, no telemetry and no analytics.
