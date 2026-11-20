# Emulator notes results (check 6, run 5) - PARTIAL

Document: new Handheld-size document (Document4), page 1.1 Notes. Settings checked: Radian, Automatic, Real, Float 8, CAS On (title bar RAD).
Screenshots in pages-shots-6/ (menu shots are 0.6-scale captures cropped to the handheld screen, so low resolution).

## N1 Notes menu (Menu key), observed
Top level: 1 Actions ▶, 2 Templates ▶, 3 Insert ▶, 4 Format ▶, 5 Math Box Options ▶ (grey on an empty page), 6 Calculations ▶.
- 1 Actions: 1 Evaluate (Enter), 2 Approximate (Ctrl+Enter), 3 Evaluate & Replace, 4 Deactivate (grey), 5 Deactivate All, 6 Activate (grey), 7 Activate All.
- 2 Templates: 1 Q&A, 2 Proof, 3 Default (grey), 4 Hide Answer (Q&A) (grey).
- 3 Insert: 1 Math Box (Ctrl+M), 2 Chem Box (Ctrl+E), 3 Shape ▶, 4 Comment ▶, 5 Slider.
  - 3 Shape: 1 Angle, 2 Triangle, 3 Circle, 4 Line, 5 Segment, 6 Ray, 7 Vector.
  - 4 Comment: 1 Teacher, 2 Reviewer.
- 4 Format: 1 Format text..., 2 Line color (grey), 3 Fill color, 4 Text color.
- 6 Calculations: 1 Define Variables ▶, 2 Number ▶, 3 Algebra ▶, 4 Calculus ▶, 5 Probability ▶, 6 Statistics ▶, 7 Matrix & Vector ▶, 8 Finance ▶. Sub-items NOT opened.
Shots: R5-N1-notes-menu-top, -actions-sub, -templates-sub, -insert-sub, -insert-shape-sub, -insert-comment-sub, -format-sub, -calc-sub.
Differs from CASSim? Not compared (CASSim files not read in this run).

## N2 text and Math Box, observed
Typed "Line one", Return, "Line two here", Return, a 90-character line: it wraps onto a second line. Ctrl+M then `2+3` then Return shows `2+3 ▶ 5` (input blue, arrow and result green), and a new empty Math Box (dotted red frame) appears below. Escape on the empty box removes it; text typed after that ("xs") is plain text beside the result on the same line, not a Math Box. `xs` was not defined in this document, so no list value was tried.
Shots: R5-N2-text-and-mathbox, R5-N2-escape-then-plain-xs.

## N3 context menus (right-click), observed
- On plain text: 1 Cut (grey), 2 Copy (grey), 3 Paste, 4 Delete, 5 Format text..., 6 Color ▶, 7 Insert Math Box, 8 Insert Chem Box, 9 Actions ▶, A Select Variable ▶, B Symbols...; the list scrolls (arrow at the bottom), further items not seen.
- On a Math Box: 1 Show Warning Info (grey), 2 Cut (grey), 3 Copy (grey), 4 Paste, 5 Delete, 6 Format text..., 7 Color ▶, 8 Math Box Attributes..., 9 Actions ▶.
Cut/Copy grey because nothing was selected. Paste enabled (clipboard held earlier typed text; not checked).
Shots: R5-N3-context-menu-text, R5-N3-context-menu-mathbox.

## N4 Format text (Menu 4 1) with "Line one" selected, observed
Dialog "Format Text": font box "TI-Nspire Sans", size box 11, buttons B, I, U, superscript, subscript, strikethrough. Clicking B then U: both highlighted, and "Line one" shows bold and underlined. Closing with the X leaves it formatted. I, superscript, subscript, strikethrough, other fonts/sizes, Text color and Fill color NOT tried.
Shots: R5-N4-format-text-dialog, R5-N4-bold-underline-applied, R5-N4-dialog-closed.

## Row mapping (correction)
The headings above use my own numbering. Against the brief's N table (emulator-sharing-capture.md): "N1 Notes menu" = brief N2; "N2 text and Math Box" = brief N3 plus the `2+3` half of N5; "N3 context menus" = brief N4; "N4 Format text" = brief N6 (bold and underline only).

## Brief N1 first screen, observed
New Notes page 1.1: empty white page, text cursor at the top left, tab "1.1", title "*Doc", RAD. Shot: R5-N1-first-screen.

## Brief N5 Math Box with a variable, observed
On a Calculator page 1.2 in the same Problem: `xs:={1,2,3,4,5,6,7,8}` gives that list. Back on Notes 1.1, a Math Box with `xs` shows `xs ▶ {1,2,3,4,5,6,7,8}` (xs bold blue, result green). On 1.2 I then entered `xs:={9,8,7}`; on returning to 1.1 the box showed `xs ▶ {9,8,7}`. I only looked after switching pages, so whether it updates live is not known. A vertical scroll bar appeared on the Notes page once the content passed the screen height.
Shots: R5-N5-calc-define-xs, R5-N5-mathbox-xs-defined, R5-N5-mathbox-xs-after-change-and-N7-return.

## Brief N7 leave and return, observed
After switching to 1.2 and back, the page showed the same content and the empty Math Box at the end (red dotted frame) as before leaving. The cursor position inside the text was not tested separately. Shot: same as N5 last.

## Run / not run / also seen
Run: brief N1, N2 (to submenu level, Calculations leaves not opened), N3, N4, N5, N6 (bold and underline only), N7 (basic).
Not run: italic, colour, Text color and Fill color routes; Calculations sub-items; Math Box Attributes...; cursor position test for N7. Reason: time.
Also seen, not covered: scroll bar on the Notes page.
