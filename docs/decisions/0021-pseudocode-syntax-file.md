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

- The translator (FR-XLT), which uses the printer.
- The settings UI to edit, preview, export and import a syntax file (FR-SYN-003) and Regularise and
  Convert symbols (FR-SYN-010 to -012). These wait for the M2 GUI shell.
- Per-spelling modes for the words `and`, `or`, `not`, `mod`, `div` are by word, not by capitalisation
  (`MOD` and `mod` share a mode).

## Symbolic pseudocode promoted to Should (2026-11-07)

Simon asked for exact values in pseudocode, with the CAS's Approx / Auto / Exact toggle. FR-PSE-012 moved
from Could to Should and Q41 was revised (see `docs/SRS.md`). Not built yet.

Design notes for when it is:

- Values: add an exact number type backed by SymPy, touched only in `core/compat/sympy_adapter.py`. The
  interpreter's `arith.py` already routes arithmetic, so Exact and Auto swap the number kind there.
- Auto: exact while every operand is exact; a decimal, `rand()` or an Approx function makes the result a float.
- Default stays Approx, so the 58 golden programs do not change. Add Exact and Auto corpus cases (surds,
  `π/6`, `7/2`, `2^(1/3)`).
- Conditions (`if`, `while`) compare numerically; trace cells and `print` show the exact form.
- Translator: exact mode needs `sympy` in the generated Python; FR-XLT-004 compares exact results
  symbolically, not as floats.
- Risks: the 20,000-step limit does not bound expression growth in loops (for example Newton's method in
  Exact mode gives huge fractions). Plan a size cap on exact values that falls back to a decimal with a warning.

## The printer and round trips (FR-SYN-005, FR-SYN-007), 2026-11-07

`runtime/pseudocode/printer.py`: `print_program(tree, syntax)`, `print_expr`, `shape` (a tree without line
numbers, for comparing) and `PrintError`.

- **Emit options used:** `keyword_case`, `indent`, `assign`, `times`, `divide`, `if_then`, `while_do`,
  `for_do`, `print_parentheses`, `terminators`, `symbols` (`ascii` writes `<-`, `*`, `/`, `<=`, `>=`,
  `!=` and `^` for powers; `unicode` and `keep` are the same, because the tree does not remember the
  user's spelling). Validated with entry-naming messages. `comment` is validated but unused: the tree has no comments.
- **Never writes what the syntax refuses.** A preferred spelling the syntax marks `no` is replaced by one
  it accepts (strict with `symbols: ascii` still writes `≤`). A `then`/`do` the syntax requires is written
  whatever `if_then`/`while_do` say, and one it forbids is left out. In a case-sensitive syntax every keyword is
  written in lower case. `and`, `or`, `not`, `mod`, `div` are written as words, not `∧ ∨ ¬`.
- **Brackets** are added only where precedence needs them, and a tree that already has `Paren` nodes
  keeps them. `a^b^c` reads as a^(b^c), and `√x²` as √(x²), as the parser does.
- **`PrintError`** (named reason) when the tree has something the syntax cannot write: a function by
  assignment under strict, a string with a quote mark the syntax rejects, an empty function that has only
  dedent to end it, a `step` where it is refused. Printing never guesses.
- **Property tests** (`tests/runtime/test_pseudocode_printer.py`): all 58 golden programs under all four presets
  (strict skips the one that defines a function by assignment); hypothesis-generated expressions and programs
  under every preset; and generated syntax files (random emit section, `then`/`do`/print/colon policies, case
  sensitivity, optional `based_on`). Comparison is `shape`, which treats `/` and `÷` as one operator and, for
  built trees, ignores grouping brackets.
- **Found on the way:** `next <variable>` was written with its placeholder (fixed); an ASCII `<=` was written
  under strict, which refuses it (fixed).
- **Lexer bug found by the property test:** `2E3²` read the `²` as an exponent digit (`2E3` then `2`); superscripts
  are no longer digits in a number's exponent.
