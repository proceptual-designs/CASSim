# 0033: Named documents in the browser; files are Import and Export

Status: accepted 2026-11-14 (asked for by Simon). Requirements: FR-DOC-010 (new), FR-DOC-003, FR-DOC-004, FR-DOC-006. It changes how decision 0028 and decision 0022 use Open and Save: Open and Save now work on documents kept by name in browser storage. Files on disk are Import and Export.

## Context

Until now Save downloaded a `.cassim.json` file and Open read one. The autosave kept the working state through a reload. The open document had no name and no saved or unsaved state. On a phone or Chromebook, downloading and picking files is slow and awkward. A teacher wants to keep several documents and switch between them, as on the handheld.

## Decision

1. **Library.** Doc > File > Save stores the document by name in the browser's storage, in IndexedDB beside the autosave (`doc/library.py`). An index (key `library`) lists the names, newest first. Each document's text is under `doc:<name>`. Names are matched without regard to case.
2. **Save, Save As, Open.** Save writes under the current name. A document that has never been saved here asks for a name first. Save As always asks, and it confirms before replacing another saved document. Open lists the saved documents with the date each was last saved, and each one can be deleted (after a confirmation). ctrl+S and ctrl+O open Save and Open.
3. **Unsaved changes.** The screen's title bar shows the document's name in the middle, with `*` in front while it differs from its saved copy. The page number stays on the left and the settings toggles on the right. A change is judged by a fingerprint of the document without the page that is showing, so moving between pages is not a change. The fingerprint is computed with the autosave (0.5 s after the last change), so the `*` appears a moment after typing.
4. **Autosave is not Save.** The autosave still keeps the working state, and it also keeps the name and the fingerprint of the saved copy (key `current`), so a reload shows the same name and marker. It never writes the named copy.
5. **Discarding.** New Document, Open and Import ask before they drop unsaved changes. A new document counts as saved, because it has nothing to lose. An imported file or a share link counts as unsaved, because it is not in the library yet.
6. **Files.** File > Import File… and Export File… read and write `.cassim.json`. If `.tns` is ever built, it goes under Import and Export too (FR-DOC-006 is unchanged on that point).
7. **Compact text (schema 2).** A Calculator row is saved as runs of text between templates, not as one string per character, and an exact entry is only its row. Storage and share links use JSON without spaces. Exported files stay indented. Schema 1 files open unchanged.

## Consequences

- A document is still on one browser and one site only. Export File… or a share link moves it, as before.
- Clearing the site's data removes the saved documents. The help pages say so.
- Not done: Close (File 3) and a "Save changes?" choice with Save as one of its buttons. The question offers only Discard or Cancel.
