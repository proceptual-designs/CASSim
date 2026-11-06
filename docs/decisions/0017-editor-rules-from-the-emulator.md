# 0017. Editor rules confirmed or corrected by the emulator

Date: 2026-11-06. Status: accepted. Source: `docs/testing/emulator-editor-results.md` (Cowork run, OS 6.0.3.374), plus Simon's own check of `1/3` and `1/3x`.

## What the emulator does
- A typed `/` (or the ÷ key) stays **linear** while editing. `1/3` is stacked only after Return, in the history. `1/3x` is read as (1/3)·x and gives `x/3`; the engine already does this.
- A stacked fraction in the entry line comes only from the **fraction template** in the palette. It takes the term before the cursor as its numerator (digits, decimals, letters, function calls, powers, roots, finished fractions, and whole products such as `2*3`), stops at `+` and `-`, and puts the cursor in the denominator. On an empty line it leaves an empty numerator box.
- A bracketed plain sum loses its brackets as a numerator (`(a+b)/2`); a bracketed power keeps them (`(a+b)²/c`).
- Backspace just after a template highlights it; a second press deletes it. Backspace at the start of the first slot (numerator, exponent, radicand) highlights the whole template; at the start of the denominator it dissolves the fraction and keeps its contents.
- Right leaves the slot it is in, including a numerator. Tab visits slots in order, then leaves. Down goes from numerator to denominator.
- The fraction template also has a shortcut: **ctrl+/** on a computer keyboard and **ctrl+÷** on the handheld keypad (confirmed by Simon, 2026-11-06; not yet run through the emulator). Plain `/` and ÷ stay linear.
- An operator typed first on an empty line (`/ ^ * + -`) inserts `Ans`.
- Up on an **empty** entry line selects the last result, then the last entry; Return copies it into the line. This belongs to the document/history layer, not the editor (M2c).
- `^` and `√` build templates while typing and stay open until Right (confirmed).

## Changes made (`device/editor.py`)
Typed `/` is a plain character; `insert_template(Kind.FRACTION)` is the palette fraction with the capture rule above. Added highlight state (`selected`), `tab()`, the `Ans` rule, and the numerator and bracket rules. Tests in `tests/device/test_editor.py`.

## Not done, still open
- Drawing the highlight in `latex()`; the history echo that stacks a typed `/` after Return (GUI/result layer).
- Matrix, list and the other palette templates (slot orders are in the results file, section T7).
- Not tested on the emulator: forward delete, adding matrix rows and columns, copy and paste, `%`, `≤`, the EE key, Left from a denominator. Typing `ᴇ` is not accepted by the emulator, so the keypad EE key must be used.
- The `vce-cas-solver` skill says a typed `/` captures the rest as the denominator. The emulator shows it does not; that note should be corrected.
