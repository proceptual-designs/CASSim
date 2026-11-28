# 0042. CASSim is released under the MIT licence

Date: 2026-11-28. Status: accepted (Simon).

## Decision

CASSim moves from the Unlicense to the MIT licence, with the copyright line
"Copyright (c) 2026 Simon Tyler and CASSim contributors". The year is the project's first (its first commit was on
2026-11-01).

## Why

- The Unlicense works by dedicating the code to the public domain, which Australian law has no way
  to do; it then falls back to a permissive licence whose wording is less standard. MIT is an
  ordinary copyright licence that works the same everywhere.
- Schools, education departments and other projects approve MIT routinely; some organisations
  question or forbid the Unlicense.
- MIT's "as is" warranty disclaimer is the familiar one, which matters for a tool students may rely
  on.
- MIT keeps the author's name on copies; "and CASSim contributors" leaves room for others' work
  without a contributor agreement.

## Consequences

- `LICENSE`, `pyproject.toml` (`license = "MIT"`), the About dialog (`about.LICENCE` and
  `about.COPYRIGHT`), the README, SRS (NFR-LEG-003), PLAN and AGENTS say MIT.
- Copies already published under the Unlicense stay usable under it.
- Nothing about the third-party parts changes: each keeps its own licence and notice. The About
  dialog now also names CodeMirror (MIT) and Flutter and its packages, whose full list ships as
  `assets/NOTICES`.
- LazyMath stays Unlicense; porting its UDFs into an MIT project is allowed (NFR-LEG-004 still
  asks for the check to be recorded first).
- The IP boundary and clean-room rule (decision 0028) are unchanged.
