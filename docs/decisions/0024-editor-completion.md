# 0024 Editor completion: lists, matrix rows and columns, touch selection, tall radicals (M2d)

Date: 2026-11-08. Status: built and checked in the browser (headless Edge). Screenshots in
`docs/testing/app-shots/2d-*.png`. Code: `device/editor.py`, `app/entry.py`, `app/ui.py`; tests
`tests/device/test_matrix_list.py` and `tests/app/test_entry_touch.py`.

## What

**List template** (`Kind.LIST`). Not on the device, whose lists are typed as `{1,2,3}` text and still
can be. It is a one-row grid drawn with braces. A comma inside an element ends it and the text after
the cursor starts the next element; Backspace at the start of an element undoes the comma. It reads as
`{a,b,c}`. It is the last cell of the Templates menu, after the device's 25 icons, and the template key
action takes a count (`list:4`).

**Rows and columns of a matrix** (`Editor.cell_sel`, `select_cells`). Shift+Up/Down selects the row the
cursor is in, then grows it a row at a time; Alt+Shift+Left/Right does the same for columns. The
handheld has no such keys, so these are CASSim's own and are on the Computer keymap only. Selected
cells are highlighted. Copy and cut take a matrix of the selected rows or columns, and pasting a matrix
of the same shape over a selection fills those cells (otherwise it nests, as any paste does).
Backspace or Delete removes the selected rows or columns (or only empties them if that would leave
nothing); typing over a selection empties it first. Any move, click or shift-arrow drops the selection.

**Selecting by touch.** A long press on the entry line extends the selection to that place, as
shift+click does. The keypad's shift key, pressed and then followed by a tap in the entry, does the
same and is used up by it, as it is for any key.

**Stretching radical.** The radical sign (square root and nth root) is set larger for a taller
radicand. `row_height` in `app/entry.py` estimates a row's height in lines of text (a fraction is the
sum of its parts plus the bar, a matrix is its rows, a power is raised a little); the sign's font size
follows it. It is an estimate, not a measured layout, so a very unusual radicand may be a little off.

## Not done, on purpose

- **Typed characters on other keyboard layouts** (Simon, 2026-11-08: cannot be checked here, so do it
  later). Flet's key event names the key, not the character: Shift+6 arrives as `6` with shift, so
  `app/keyboard.py` still maps shifted symbols with a US/AU table. An attempt was made (the page posts
  `event.key` over the `cassim` BroadcastChannel and the app uses it in place of the table) but it was
  taken out again because it had only unit tests and no way to run it on a UK, French or German layout.
  To pick up: page-side keydown listener in `tools/publish.py` (skip ctrl/meta, keep AltGr, ignore dead
  keys and composition), a `Bridge` method in `app/web.py` that returns the fresh character or waits
  about 20 ms for it, and a `typed_name` in `keyboard.py` that the key handler tries before `key_name`.
  The race between the DOM event and Flutter's own is the thing to test on real hardware.
- No stretching for brackets, absolute-value bars or the derivative and limit templates.
- No handles for selecting a row or column by touch; the keys are the only way.

## Caps Lock (added 2026-11-08, branch `keyboard-caps-lock`)

Flet's key event has no Caps Lock state, so with the lock on a typed letter came out small (`ans`,
not `Ans`). Fixed by tracking the lock in the app rather than reading it: `AppState.caps` is toggled
by the Caps Lock key (Flet reports it as `Caps Lock`) and by the keypad's ctrl then shift (the
handheld's CAPS, `ctrl+shift` in the keymap; `Keyboard.press` now lets a bound modifier pair through
instead of replacing the pending modifier). With the lock on, a typed letter swaps case, so Shift
still gives a small letter as on a PC. The title bar shows `CAPS`. Checked in the browser (key press
on, `aNS`, key press off, `b`) and by `tests/app/test_state.py` and the `methods-caps-lock` flow.

Limits: the lock is tracked from its own key presses, so it is wrong if it was already on when the
page loaded, or was toggled while the window was not focused. The page could read the real state
(`getModifierState("CapsLock")` on any key event) and send it over the BroadcastChannel; that fits
with the typed-character work below. On a Mac the browser sends the Caps Lock key down only when it
turns on and key up only when it turns off; the Flet event is a key down, so turning it off may be
missed there (not tested).

