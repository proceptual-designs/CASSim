# 0021 Pseudocode syntax file, presets and name splitting (M7b)

Date: 2026-11-07. Status: built; the preset contents are a first cut for Simon to refine.

`src/cassim/runtime/pseudocode/syntax.py` implements the syntax file (SRS FR-SYN-001 to -004, -008, -009).
The lexer and parser now read a compiled `Syntax` instead of hard-coded tables, so the spelling of
every construct is data. `docs/pseudocode/syntax-default.yaml` is the default file, and a test keeps it
equal to the built-in default.

## What is data now

- Case-insensitive keywords on or off; comment markers; quote styles; superscript exponents.
- Operator spellings (`×` `*` `·`, `≤` `<=` `⩽`, `∧` `and`, `%` and so on), each `ok`, `warn` or `no`.
- Assignment spellings (`←` `<-` `:=` `=`), function-by-assignment, default parameters.
- `then` (if) and `do` (while, for) as `required`, `optional` or `forbidden`; `is true`; `step`.
- Block closers for if, while, for, repeat and define, including `next` and `next <variable>`, a
  function ending by dedent, the else-if spellings, and the missing-inner-end and surplus-end policies.
- Extra keywords for define, print, input, return and break; the print parentheses policy and
  juxtaposed print items; the colon after a function header.
- `names.split_products` (below). The `emit` section is validated and stored but nothing writes with
  it yet (printer, FR-SYN-005 and -007, comes with the translator).

A file is laid over the default, so a partial file is valid. `based_on: <preset>` starts from a preset.
Files are YAML or JSON text, data only, at most 20,000 characters, and are loaded with a YAML loader
in which only `true` and `false` are booleans (a bare `no` is the word `no`, not `False`). An invalid
file is rejected with one message per entry at fault; `load_or_default` falls back to the default.

## Validation (FR-SYN-004)

Unknown entries; bad modes, policies and emit values; spellings the engine does not know; a bare `end`
accepted for more than one construct; one terminator spelling for two constructs; a keyword used for
two constructs or equal to a grammar word (`if`, `to`, `mod`, ...); no spelling left for assignment, a
keyword group or a block's end. `Syntax.keyword_collisions(names)` reports reserved words a user's
saved program uses.

## Presets (FR-SYN-008)

| Preset | Character |
|---|---|
| `default` | Tolerant: every spelling in `dialect.md`; warnings for `=`, `%`, a missing inner `end` |
| `vcaa` | Default plus name splitting; the printer writes Capitalised keywords and `EndIf`, `EndFor`, ... |
| `author` | Default plus name splitting, lower-case emit (the book's style) |
| `strict` | One spelling per construct, exact-case keywords, `then` required, no `do` on loops, no `#`, `<-`, `=`, `*`, `/`, `**`, superscripts, `endif`, `next`, `wend`, dedent-ended functions; a missing inner `end` is an error |

The `vcaa` and `author` presets read every golden program exactly as the default does (tested).

## Name splitting: decided

Simon agreed the recommendation of 2026-11-06. An undefined multi-letter name made of defined
single-letter variables (`ax`) is **not** their product in the `default` and `strict` presets: the run
stops with `ax is not defined, did you mean a*x? (write a product with * or a space)`. The `vcaa` and
`author` presets set `names.split_products: true`, which gives the previous behaviour (`ax` is a × x,
and a power binds to the last letter only, so `ab²` is a × b²). Reason: exam text and the author's book
write `ax³ + bx²`, which must run, but nothing else should silently reinterpret a typo.

Corpus cases may carry `syntax: <preset>`; only `book.u2.newton3.cubic` needs one (`author`).

## Fixed on the way

- `∧`, `∨` and `¬` were lexed but never reached by the parser, so `1 < 2 ∧ 2 < 3` printed nothing. They
  now behave as `and`, `or` and `not`.
- `vcaa.2025.nht2.q18.bisection-for`: the reference Python called `loge` without defining it. It now
  imports `log as loge`, and all 49 reference programs with checkable output reproduce the recorded
  output when run in CPython.

## Not done yet

- The printer (the `emit` section) and the round-trip property tests of FR-SYN-007; the translator
  (FR-XLT) needs them.
- The settings UI to edit, preview, export and import a syntax file (FR-SYN-003) and Regularise and
  Convert symbols (FR-SYN-010 to -012). These wait for the M2 GUI shell.
- Per-spelling modes for the words `and`, `or`, `not`, `mod`, `div` are by word, not by capitalisation
  (`MOD` and `mod` share a mode).
