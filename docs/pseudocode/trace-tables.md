# Trace tables for CASSim pseudocode and Python (draft 0, 2026-11-02)

Specification of the stepwise, forwards-and-backwards trace table. Requirements: SRS 4.12, `FR-TRC-*`. The two layouts below are the ones in Simon Tyler's *Desk Check and Trace Table for a Bisection Method Question* and in his VCAA 2023 solutions ("the above uses a vertical trace table - one line of code, one line of table ... the below uses a horizontal desk check - useful for a single main loop"). The running example is the program `author.bisection.abt.x4+x-2` in `corpus/pseudocode/seed.yaml`.

## 1 What is recorded

A run produces an ordered list of **events**, one per executed step. Stepping forwards or backwards moves a cursor over this list; nothing is re-executed (so random numbers and input replay identically, and going back is instant).

| Event | Carries |
|---|---|
| line executed | source line number, kind (assign, condition, call, return, print, input, loop head) |
| assignment | variable, old value, new value, the expression with values substituted (`(−1+−2)/2 = −1.5`) |
| condition | the expression with values substituted, its true/false result, which branch or loop path follows |
| call / return | function name, argument values, returned value, nesting depth |
| output | the text printed |
| input | the prompt and the value supplied |
| halt | finished, error (with message and line), or step limit |

The same event stream feeds both layouts, the code pane highlight and the variables panel. Because all the events are kept, the table can be built up to any cursor position and rendered either way.

Limits: a step limit (default to be chosen, with the cap on recorded events shown to the user) stops infinite loops such as `linear(1+x, 0, 0.3)`; a run that hits it is still fully steppable, ending in a "stopped after N steps" row.

## 2 Vertical layout (full trace table)

One row per executed line of code (block terminators such as `end if` are skipped). Columns: **Line #**, then one column per variable that the program assigns, then one column per condition that is evaluated, then **Calcs / Output**. A variable cell is filled **only on the row where it changes** (sparse, as in the author's tables; "show every value on every row" is a display option). A line executed again appears again, so loops show as repeated line numbers (`6, 7, 10, 12, 6, ...`).

Example (bisection of x⁴ + x − 2 on [−2, −1], t = 0.2), as the author writes it, extended with the program's own function column:

| Line | a | f(a) | b | f(b) | c | f(c) | Calcs / Output |
|---|---|---|---|---|---|---|---|
| 1 | −2 | | −1 | | | | inputs a, b |
| 2 | | | | | −1.5 | | c = (−2 + −1)/2 |
| 3 | | 12 | | −2 | | | f(a)×f(b) = −24 > 0 is false |
| 6 | | | | | | | (b−a)/2 = (−1+2)/2 = 0.5 > t is true |
| 7 | | | | | | 1.5625 | f(a)×f(c) > 0 is false |
| 10 | −1.5 | | | | | | a ← c |
| 12 | | | | | −1.25 | | c = (−1.5 + −1)/2 |
| 6 | | | | | | | (b−a)/2 = 0.25 > t is true |
| 7 | | | | | | −0.809 | f(a)×f(c) < 0 is true |
| 8 | | | −1.25 | | | | b ← c |
| 12 | | | | | −1.375 | | c = (−1.5 + −1.25)/2 |
| 6 | | | | | | | (b−a)/2 = 0.125 > t is false |
| 14 | | | | | | | **−1.375** |

(The author's printed table puts line numbers in the first column and function values beside the variable they belong to; the rows above follow his execution order. Exact column set is a design decision for SDD-13: variables are discovered from the program, with function-call results such as `f(a)` shown as their own columns when they are used in a condition.)

Use this layout for any program: nested loops, several loops, early returns, recursion, programs calling functions.

## 3 Horizontal layout (desk check)

The code is listed down the left, in program order, one row per **line of code**. Columns are the **passes**: an **Init** column for the statements before the loop, then **Loop 1, Loop 2, ...**, and the loop condition's final failing test in the last column. A cell shows what that line did on that pass, with values substituted, a tick or cross for a condition, and "(skip)" where a branch was not taken.

| Code | Init | Loop 1 | Loop 2 | Loop 3 |
|---|---|---|---|---|
| `define bisection(f(x), a, b, t)` | `bisection(x⁴+x−2, −2, −1, 0.2)`, a ← −2, b ← −1, t ← 0.2 | | | |
| `c ← (a+b)/2` | c ← (−1+−2)/2 = −1.5 | | | |
| `if f(a)×f(b) > 0 then` | 12×−2 < 0 ❌ | | | |
| `print "Require ..."` | (skip) | | | |
| `else` | | | | |
| `while (b−a)/2 > t do` | | (−1+2)/2 = 0.5 > 0.2 ✔ | (−1+1.5)/2 = 0.25 > 0.2 ✔ | (−1.25+1.375)/2 = 0.0625 < 0.2 ❌ |
| `if f(a)×f(c) < 0 then` | | 12×1.56 > 0 ❌ | 1.56×−2 < 0 ✔ | |
| `b ← c` | | (skip) | b ← −1.25 | |
| `else` / `a ← c` | | a ← −1.5 | (skip) | |
| `c ← (a+b)/2` | | c ← (−1.5−1)/2 = −1.25 | c ← (−1.5+−1.25)/2 = −1.375 | |
| `print c` | | | | **−1.375** |

**Eligibility rule** (stated by the author: "good if there's one main loop you want to check"): the horizontal layout is offered when the run executes **exactly one loop and no loop is nested inside another**. One main loop inside an `else` branch, as above, still qualifies. Nested loops (VCAA 2023 Q2, Q4; the 2026 two-dice question) and several top-level loops use the vertical layout only. The corpus records `trace.horizontal_eligible` for every program.

Other examples in the author's material that use this layout: `a ← 2; while a < 20 ...` (Loop 1-4 with ✔), the 2025 remainder-by-repeated-subtraction question (`17 > 5 ✔`, `n ← 12`, ..., `2 > 5 ✘`), and the 2025 Specialist volume question (`left = 1 ≤ 3 ✔`, `volume ← 2π`, `sum ← 2π+3π`, ...).

## 4 Choosing a layout

- **Auto** (default): horizontal when eligible, otherwise vertical. The user can switch to the other layout at any time when it applies, and the choice is remembered per program.
- The layout is a **view**: switching it does not re-run anything, and the cursor stays on the same event.
- The author's practice questions use a third, per-iteration table (`Loop #, x, y, y_old, condition, Output`, one row per pass, variable values as columns). It is a simple summary of the same events and is a Could third view (FR-TRC-011, Q33 decided 2026-11-04), after the vertical and horizontal views.

## 5 Stepping and controls

- Controls: **Step back**, **Step forward**, **Back to start**, **Run to end**, **Run to next output**, **Jump to** (click any row or cell), and, for loops, **Next pass / Previous pass**. Keyboard: left/right arrows to step, Home/End.
- The code pane (and the code column of the horizontal layout) shows the program exactly as the user wrote it, in their own syntax (dialect.md section 11), never a normalised reprint; it highlights the current line and shows its warning markers; the variables panel shows every variable at the cursor.
- Rows or columns after the cursor are hidden (or greyed) so the table fills in as the student steps; **Show all** reveals the finished table.
- **Fill-in mode** (Could): cells are blank and the student types values; the app checks each against the recorded events. This mirrors the author's "complete the tracetable" questions.
- **Export** (Could): copy as CSV, Markdown or an image so a teacher can paste a worked trace into a worksheet.

## 6 Python

The same two layouts apply to Python code. Design decision (SDD-13): the supported Python subset (the translatable subset, `FR-XLT-*`) is parsed with Python's own `ast` module into the same internal program tree as pseudocode and traced by the same engine, so the table shows conditions and assignments with values substituted, in either language. The normal **Run** of Python still uses CPython directly; a differential test (`FR-XLT-004`) keeps the two in step. Python outside the subset can be run but gets at most a line-by-line variable trace (Could), not the full table.

## 7 Settings in the trace

Number mode, angle and display precision (SRS FR-SET-*) change the cell values only (`−3/2` vs `−1.5`, degrees vs radians, 6 significant digits by default), never the layout. The substituted calculation text uses the same display rules as output.
