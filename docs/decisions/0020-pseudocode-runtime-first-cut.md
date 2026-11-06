# 0020 Pseudocode runtime, first cut (M7b)

Date: 2026-11-06. Status: built, awaiting review by Simon.

`src/cassim/runtime/pseudocode/` holds a tokenizer, a line-oriented block parser with a Pratt
expression parser, a tree-walking interpreter that records one `Step` per executed line, and the two
trace-table builders (`trace.py`). All 58 golden programs in `corpus/pseudocode/seed.yaml` replay
green, including the five `expect_by_settings` cases; loop-pass counts match the corpus exactly.

## Choices made while building (please confirm or overrule)

1. **Grammar is hard-coded, not yet driven by the syntax file.** The tolerant default of
   `syntax-default.yaml` is written directly in `parser.py`. FR-SYN-001 to -009 (the table-driven
   parser, presets, validation) are the next step; the tables at the top of `parser.py` and `lexer.py`
   are where it plugs in.
2. **Block ends.** End keywords decide structure. A missing `end if` (and the other inner closers) is
   a warning and is closed by an outer closer or by a dedent, but a dedent closes a block only when the
   block's first body line is indented deeper than its opener, so flat-indented programs with proper
   `end` keywords still work. A function body ends at `end` or a dedent, with no warning. A bare `end`
   closes only `define`.
3. **`[x]` with one item is a grouping, not a list**, because exam text groups with square brackets.
   `[]` and `[1, 2]` are lists. A one-item list cannot be written yet; options are a different literal
   or deciding by position (right of `←`).
4. **Euler's `e`.** The toggle (FR-SET-008) is off by default, as the dialect says, but corpus case
   `vcaa.2023.q3.bisection-count` writes `2e^x`, so the corpus replay turns the toggle on for every
   case. Worth deciding whether the VCAA preset should default it on.
5. **Name splitting.** An undefined multi-letter name made of defined single-letter variables is their
   product (`ax³ + bx²` in the author's `newton3`), and a power binds to the last letter only
   (`ab²` is a × b²). Undefined names that cannot be split give a "did you mean" error.
6. **Expression-form function arguments** follow Q40. If the header names a variable that is not also a
   parameter (VCAA MCQ 6: `bisection(f(x), a, b, max)` called as `bisection(sin(x), 3, 5, 2)`), the
   variable is the one in the header.
7. **Trace record.** Each step carries its line, kind, depth, variable changes, the substituted
   condition or calculation, and its innermost loop pass. A user-function call is a step of its own
   (it carries the parameter bindings, which fill the `define` row of the desk check); lines inside the
   function are recorded at depth 1 and the vertical table hides them unless asked.
8. **Run limits** are counted per loop pass across all loops (10,000), recursion depth (100) and
   recorded steps (200,000, reported as `event_cap`), each ending the run with a final `halt` step so
   the trace stays steppable.

## Disagreement for Simon

`trace.horizontal_eligible` is `false` in the corpus for `book.u1.linear-search.x4-10x-2` and
`vcaa.2024.nov.mm2.q17.integer-roots`, but each runs exactly one un-nested loop, so the rule in
`trace-tables.md` section 3 says they qualify (the other 54 flags agree with the rule). The replay
marks those two as expected failures. Either the flag should change or the rule needs a second
condition (for example a maximum number of passes).
