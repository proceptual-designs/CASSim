# 0036 Pseudocode convenience symbols

Date: 2026-11-19. Status: accepted. Numbered 0034 until 2026-11-25; renumbered because two records shared that number, and every "decision 0034" in the code and documents means the run 5 choices (`0034-run5-decisions.md`).

## Context

Pseudocode source must remain useful as ordinary editable text and must display exactly as typed
(FR-SYN-006). At the same time, assignment and common mathematical constants are easier to read
when shown with `←`, `ⅇ` and `π`.

## Decision

- Keep a linear source editor; do not add a structured or fully typeset source editor in this slice.
- Accept `@e` and `@pi` as explicit Nspire-style input aliases for `ⅇ` and `π`.
- Parse explicit aliases and their Unicode forms as constant nodes. They are unambiguous and are
  not shadowed by ordinary variables named `e` or `pi`.
- Preserve the existing plain `e` and `pi` semantics. Plain `pi` is still a possible user name, and
  plain `e` remains controlled by the Euler-number setting.
- Add a **Typing aids** setting, off by default. It converts one newly typed operator sequence at a
  time: `<-`, `<=`, `>=` and `!=`. `@e` and `@pi` convert as soon as the alias is complete.
- Replacement operates only in source code, not in strings or comments, and does not run for paste
  or file import. The exact typed ASCII form is recoverable with one undo.
- The AST's constant nodes are the boundary used by any pseudocode/Python translator. A future
  translator must emit `math.e` and `math.pi` without global text replacement.

## Rejected alternatives

- Live replacement of plain `e`, `pi` or function words would be ambiguous with user variables.
- Whole-program normalisation on every edit would violate FR-SYN-006 and make comments and spelling
  choices unstable.
- A full maths editor would add caret, selection, accessibility, mobile, round-trip and source-line
  complexity disproportionate to this convenience feature. Rendered maths remains appropriate for
  results and trace values.
