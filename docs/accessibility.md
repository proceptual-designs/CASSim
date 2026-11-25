# Accessibility

NFR-USE-002 (Should) asks for keyboard-only operation in Computer mode and visible focus, and for every gap to be recorded here and stubbed, not skipped. This file lists what is known on 2026-11-08. Nothing here has been tested with a screen reader or an accessibility checker; "not checked" means exactly that.

## What exists

| Area | State |
|---|---|
| Keyboard in Computer mode | Entry, menus (F2, F4, numbers, arrows, Enter, Esc), pages, undo and redo, copy and paste work from the keyboard (`devices/nspire/keymap.py`, `docs/user` and the wiki's Keys page). The toolbar chips, sidebar buttons and dialogs are Flet controls; whether each can be reached and used with Tab alone is **not checked**. |
| Computer columns | System Settings has a “Show keyboard-accessible column controls” option that exposes move and resize buttons. The option is saved; Tab-only operation and screen-reader labels remain **not checked**. |
| Text size | Maths size and Zoom (50 to 200%) in Handheld Setup, saved per device. Interface text follows Zoom. The browser's own zoom also works. |
| Touch targets | Handheld keys are sized by the layout code to fit the window; the smallest size on a 360 px phone is **not measured** (NFR-PORT-003 is tested for fit, not target size). |
| Tooltips | Keys, status items and the splitter have tooltips (`devices/nspire/ui/keypad.py`, `views.py`). |
| CASSim Scientific | Every keypad key can be pressed from the keyboard (SDD-14 section 4.1; CASSim ▸ Keyboard shortcuts); keys carry a tooltip with their spoken name and shortcut, and a `Semantics` label and button role. The keys are deliberately not focusable (Tab must not land on a key that Enter would also press), so Tab reaches only the menus and panel buttons. The calculator scales to the window (0.7× to 1.3×). Three themes, including Classroom high contrast; the SHIFT and ALPHA legends on the dark body were lightened for contrast. Contrast ratios, the LCD's natural-display text for screen readers, and Tab order are **not checked**. |
| Theme | Dark, Light and High contrast presets are selectable in Handheld Setup > Appearance. Individual colours can be edited per preset and reset; user-edited colours can reduce contrast. Theme-file import and export remain unbuilt (FR-THEME-002). |

## Known gaps

| Gap | Why | Stub or next step |
|---|---|---|
| **Screen readers** | Flet draws to a canvas (CanvasKit). Flutter web adds an accessibility tree only when asked, and CASSim sets no semantic labels. The maths is drawn from LaTeX, so no text equivalent exists for results. | Add `Semantics` labels to keys, menus and the toolbar; give every result a plain-text label from the engine's text form (`to_ascii`). Test with NVDA and VoiceOver. |
| **Visible focus** | The page has one key listener (`autofocus=True`); the entry line shows a cursor, but menu rows and dialog fields use Flet's defaults, which are not checked against the dark theme. | Check focus rings on every control; add a focus style to `Theme`. |
| **Contrast** | NFR-USE-003 asks for WCAG AA. Automated checks cover keypad text, its context-menu icon, selected modifier states, highlighted outlines, and selected sidebar/menu colours in the three default presets. The remaining app surfaces and custom colours have not been comprehensively checked; in Dark the dark keys still have low-contrast boundaries against the background. | Audit all other controls, dialog, sheet, graph and page colours; check on real devices, including the small keypad legend. Custom colours carry a contrast warning. |
| **Colour as the only signal** | Status (Rad/Deg, Auto/Approx) is text. An active Ctrl or Shift also has a dot beside its name, and the context-menu icon has a tooltip. The different secondary layers still rely on colour and the modifier's position to identify them. | Review the layers and other states without colour, and add text or shape cues where needed. |
| **Reduced motion** | Not checked; the app has few animations. | Review when the graph pages arrive. |
| **Reading order and headings** | Not applicable to a canvas; follows from the semantics work above. | As above. |
| **The help site** | Plain HTML built from `docs/wiki/` (`tools.wiki_site`): headings, lists, tables, a labelled navigation, light and dark colours. Contrast has not been measured. | Measure contrast with the app's themes. |

## Rule for new work

A new control gets a tooltip or label, can be reached from the keyboard in Computer mode, and its colours come from `Theme`. A new gap goes in the table above in the same commit.
