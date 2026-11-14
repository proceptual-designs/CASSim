# Accessibility

NFR-USE-002 (Should) asks for keyboard-only operation in Computer mode and visible focus, and for every gap to be recorded here and stubbed, not skipped. This file lists what is known on 2026-11-08. Nothing here has been tested with a screen reader or an accessibility checker; "not checked" means exactly that.

## What exists

| Area | State |
|---|---|
| Keyboard in Computer mode | Entry, menus (F2, F4, numbers, arrows, Enter, Esc), pages, undo and redo, copy and paste work from the keyboard (`devices/nspire/keymap.py`, `docs/user` and the wiki's Keys page). The toolbar chips, sidebar buttons and dialogs are Flet controls; whether each can be reached and used with Tab alone is **not checked**. |
| Text size | Maths size and Zoom (50 to 200%) in Handheld Setup, saved per device. Interface text follows Zoom. The browser's own zoom also works. |
| Touch targets | Handheld keys are sized by the layout code to fit the window; the smallest size on a 360 px phone is **not measured** (NFR-PORT-003 is tested for fit, not target size). |
| Tooltips | Keys, status items and the splitter have tooltips (`devices/nspire/ui/views.py`). |
| Theme | Dark is the default (`app/theme.py`). Other themes are not built (FR-THEME-002). |

## Known gaps

| Gap | Why | Stub or next step |
|---|---|---|
| **Screen readers** | Flet draws to a canvas (CanvasKit). Flutter web adds an accessibility tree only when asked, and CASSim sets no semantic labels. The maths is drawn from LaTeX, so no text equivalent exists for results. | Add `Semantics` labels to keys, menus and the toolbar; give every result a plain-text label from the engine's text form (`to_ascii`). Test with NVDA and VoiceOver. |
| **Visible focus** | The page has one key listener (`autofocus=True`); the entry line shows a cursor, but menu rows and dialog fields use Flet's defaults, which are not checked against the dark theme. | Check focus rings on every control; add a focus style to `Theme`. |
| **Contrast** | NFR-USE-003 asks for WCAG AA (4.5:1 for text). **To check, high on Simon's list (2026-11-14): the blue labels and the grey keys.** Ratios worked out on 2026-11-14 for the Dark keypad (WCAG formula, not yet a test): the blue ctrl-layer labels (`key_label` #7fb2e8) on the light grey nav and touchpad keys (#dfe3e8: undo, sorter, CAPS, +page, ◀ page) are **1.73:1**, far below AA; the same blue on the digit keys (#4a515c: ans) is 3.60:1, also below; white on the ctrl key (#3f7fc4) is 4.16:1 and white on the Install button (#4da3ff) 2.63:1, both below. The dark keys against the page (#2b2f36 on #14161a, 1.35:1; digits 2.26:1) have no visible edge, which matters for low vision (the 3:1 rule for controls). Passing: the shift labels on dark keys 6.87:1, blue labels on dark keys 6.04:1, key text on every key above 8:1. | Darken the blue on light keys (or give light keys a dark blue), deepen the ctrl and accent blues, and give dark keys an outline; then compute every text and background pair in `app/theme.py` in a test that fails below 4.5:1 (3:1 for key edges). |
| **Colour as the only signal** | Status (Rad/Deg, Auto/Approx) is text, but the warning triangle (FR-CALC-007) is planned as colour plus a shape. | Keep a text label with every colour cue. |
| **Reduced motion** | Not checked; the app has few animations. | Review when the graph pages arrive. |
| **Reading order and headings** | Not applicable to a canvas; follows from the semantics work above. | As above. |
| **The help site** | Plain HTML built from `docs/wiki/` (`tools.wiki_site`): headings, lists, tables, a labelled navigation, light and dark colours. Contrast has not been measured. | Measure contrast with the app's themes. |

## Rule for new work

A new control gets a tooltip or label, can be reached from the keyboard in Computer mode, and its colours come from `Theme`. A new gap goes in the table above in the same commit.
