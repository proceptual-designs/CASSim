# CASSim pseudocode dialect (draft 0, 2026-11-02)

Working specification for the Python and pseudocode environment (PLAN section 3.2, M7). Requirements derived from it are in `docs/SRS.md` section 4.12 (`FR-PSE`, `FR-XLT`, `FR-TRC`, `FR-SET`); open points are Q-numbers in SRS section 10. Golden programs are in `corpus/pseudocode/seed.yaml` (44 cases, all run against a reference Python translation). The syntax is configurable: the spellings in sections 3 to 5 are the **default syntax file** (`docs/pseudocode/syntax-default.yaml`), which the user can change (section 11).

The dialect is the VCAA pseudocode as extended by Simon Tyler's conventions document, because that is what students meet and what his materials teach. Where the sources disagree or are silent, this file says so rather than guessing.

## 1 Sources

| Source | Gives | Rights, as stated in the document |
|---|---|---|
| VCAA, Mathematics Pseudocode page (vcaa.vic.edu.au, study design support) | Official principles, constructs, four worked examples, sample questions | (c) VCAA; question text must not ship (NFR-LEG-007) |
| S. Tyler, *Pseudocode, Flowcharts, and Python for VCE Maths* (2023) | Conventions, data types, operators, pseudocode-to-Python translation table | CC BY-SA 4.0 |
| S. Tyler, *Algorithms and Pseudocode: Practice Questions* and *Solutions* (2023-24) | Linear search, bisection, Newton, Riemann, trapezium, with trace tables | (c) author |
| S. Tyler, *Algorithms and Pseudocode in VCE Mathematics* slides (2023-25) | The four loop types, functions, simulations, Euler, arc length | (c) author |
| S. Tyler, *Pseudocode Questions from VCAA Study Design Pages* (solutions) | Answers to VCAA Q1-Q6 | CC0 (answers); questions (c) VCAA |
| S. Tyler, VCAA algorithm question slides 2023-2026 (Methods and Specialist) | Exam questions with desk checks | questions (c) VCAA |
| S. Tyler, *Desk Check and Trace Table for a Bisection Method Question* | The reference for both trace layouts (`docs/pseudocode/trace-tables.md`) | (c) author |

## 2 Scope

Decision of 2026-11-02: pseudocode needs only **numeric variables and basic strings**.

| Type | Examples | Python |
|---|---|---|
| integer | `5`, `-2`, `0` | `int` |
| rational | `3/4`, `-11/8` (Auto and Exact modes, see section 8) | `fractions.Fraction` |
| real | `1.23`, `-0.18`, `747.0` | `float` |
| complex | `1+2i`, `1+2ⅈ`, `complex(1,2)` (decided 2026-11-04; Real domain by default) | `complex` |
| string | `"3.14"`, `""`, `":P"` | `str` |

Also needed, because the sources use them: **boolean** values arising from comparisons (`true`, `false`; used in conditions and printable, as in `print avgHatP - ME ≤ p ≤ avgHatP + ME`), and **function values** passed as arguments (section 6). Both are results or arguments, not a general type system: there are no declarations.

**Lists** (with `Append`, `Sum`, `len`, `for each x in a`, nested lists) and **seeded random numbers** (`rand()`, `randint`, `seed`) are supported, Should (SRS FR-PSE-006, -007). Not supported in the first version, all Could (FR-PSE-008 to -010; each appears somewhere in the sources, see section 10): sets, dictionaries, tuples, set `for each`, `∑`, derivative notation `x'(t)`, random distributions, prose steps. Case statements are not used in VCE Maths.

## 3 Lexical rules

Every spelling in this section and in section 4 is the default of the user's syntax file (section 11): each can be added to, warned about or switched off.

- One statement per line. Blank lines and comments are ignored.
- **Keywords are case-insensitive** (`define`, `Define`, `DEFINE`). The sources use lowercase (VCAA, conventions) and capitalised (`Repeat`, `Until`, `End If`) forms interchangeably. Keywords are reserved words.
- **Identifiers are case-sensitive** (`A` and `a` differ in the trapezium example; Python agrees). Short algebra-like names are the convention. The sources contain slips such as `Count` for `count`, so an undefined name gets a "did you mean ...?" diagnostic, never a silent guess.
- **Comments**: `//` and `#` to end of line; either, consistently, is fine.
- **Assignment**: `x ← 5`. Also accepted: `<-` and `:=`. A bare `x = 5` at statement level is accepted **with a warning** (the VCAA page itself has `sum = sum + x + y`), because `=` is equality inside expressions.
- **Arithmetic**: `+ - × * ÷ /`, `DIV` and `MOD` (floor semantics, as Python `//` and `%`), powers as `^`, `**` or superscript digits (`i²`, `i³`). Minus may be `-`, `−` (U+2212, used in exam text) or `–` (U+2013).
- **Implicit multiplication**: `2a`, `2t`, `2e^x`, `(a+b)(c+d)`. A name followed by `(` is a call if it is a defined function or a function parameter, otherwise it is a product.
- **Comparison**: `=` (equality in an expression; `==` also accepted), `≠ <> !=`, `< >`, `≤ <= ⩽`, `≥ >= ⩾`. **Chained comparisons** are allowed with Python meaning: `-0.01 < cos(x) - x < 0.01`.
- **Logic**: `and or not`, and `∧ ∨ ¬` (Specialist).
- **Absolute value** bars `|R - L|`; **grouping** with `( )` and, because exam text uses it, `[ ]`.
- **Numbers**: `12`, `0.5`, `.5`, and scientific notation as `1E-3` or `1ᴇ-3` only (lowercase `e` is never an exponent marker, so `2e3` is `2 × e3`).
- **Strings**: double quotes, straight or curly. Concatenation with `+`.
- **Constants and functions**: section 7.
- **Symbol equivalents** (decided 2026-11-04): ASCII and Unicode spellings are interchangeable, in any mix; the syntax file marks each ok, warn or no. The table is the default of `syntax-default.yaml` (`symbols`):

| Meaning | ASCII | Unicode |
|---|---|---|
| assign | `<-`, `:=` | `←` |
| multiply | `*` | `×`, `·` |
| divide | `/` | `÷` |
| less or equal | `<=` | `≤`, `⩽` |
| greater or equal | `>=` | `≥`, `⩾` |
| not equal | `!=`, `<>` | `≠` |
| square root | `sqrt(x)` | `√(x)`, `√x` |
| pi | `pi` | `π` |
| infinity | `inf` | `∞` |
| absolute value | `abs(x)` | `\|x\|` |
| power | `x^2`, `x**2`, `x^-1` | `x²`, `x⁻¹` (integer exponents only) |
| minus | `-` | `−`, `–` |
| logic | `and`, `or`, `not` | `∧`, `∨`, `¬` |
| natural log | `ln(x)`, `loge(x)` | |

  The **Convert symbols** button (FR-SYN-012) switches a selection or the whole program between the two styles, working on tokens so strings, comments and names are never touched; a variable named `pi` is left alone. `x^(n+1)` has no superscript form and stays. The **symbol palette** (FR-EDT-006) inserts them on devices without the keys. The printer's `emit.symbols` (`unicode`, `ascii` or `keep`) controls what translation and Regularise write.

## 4 Statements

| Construct | Spellings accepted | Canonical (emitted) | Python |
|---|---|---|---|
| Assign | `x ← e`, `x <- e`, `x := e`, `x = e` (warn) | `x ← e` | `x = e` |
| Input | `input x`, `Input x` | `input x` | `x = read_value()` using a short generated helper, see below |
| Output | `print a, b`, `print(a, b)`, `Output a`, and items juxtaposed around string literals: `Print "zero between " x-h "and" x` (warn) | `print a, b` | `print(a, b)` |
| If | `if c then ... end if`; `then` optional; `else if c2 then`; `else` | as written | `if / elif / else` |
| While | `while c do ... end while`; `do` optional; `while c is true` (VCAA) | `while c do` | `while c:` |
| For | `for k from a to b [step c] ... end for` or `next k` | `for k from a to b ... end for` | `for k in range(a, b+1, c):` (negative step: `range(a, b-1, c)`) |
| Repeat n | `repeat n times ... end repeat` | as written | `for _ in range(n):` |
| Repeat-until | `repeat ... until c` | as written | `while True: ... if c: break` |
| Break | `break` | `break` | `break` |
| Define | `define f(x, y) ... end`; `define f(x):`; the closing `end` is optional (section 5) | `define f(x, y) ... end` | `def f(x, y):` |
| Return | `return e` | `return e` | `return e` |
| Call | `y ← f(5)` or `f(5)` as a statement | | |

**Input typing** (decided 2026-11-02, to be revisited after real use): `input x` reads a line and infers its type. Anything that can be a number is a number: `12` is an integer, `0.5` a real, `3/4` a fraction (a rational in Auto and Exact modes, the real 0.75 in Approx), a complex literal once Q28 is settled. Anything else is a string. Because Python's `input()` always returns text, the generated Python includes a small helper (`read_value`) that does the same inference; Python to pseudocode turns `int(input())`, `float(input())` and `input()` into `input x`, which is looser but safe.

`for` ranges are inclusive at both ends ("from 1 to 3" gives 1, 2, 3). `case of` is not used in VCE Maths and is not supported. The "post-condition" `repeat ... until c` stops when `c` becomes **true**.

## 5 Block structure and error tolerance

The VCAA states the principle: one statement per line, indentation shows hierarchy, nested blocks end with an `end` keyword. Real exam text does not always follow it (the author notes "the indentation is messy" for two exam questions). Therefore:

1. **End keywords decide structure; indentation is advisory.** A mismatch between indentation and structure is a warning, not an error.
2. A function body ends at its `end` (also accepted: `end define`, `end function`). If there is none (VCAA style, e.g. the factorial and `intersect` examples), the body ends at the first line dedented to the column of `define`, or at the end of the program.
3. A **missing inner `end`** is a warning, not an error: a closing keyword for an outer block (`EndFor`, `End While`, `end`) or a dedent closes any still-open inner blocks, and the warning names the block and its opening line. Real exams omit these (VCAA 2023 Exam 2 MCQ 13 has no `EndIf`; the 2023 sample MCQ 6 has none before `i ← i + 1`; both slides add it by hand). A **surplus** `end ...` with nothing open, or a closer of the wrong kind that cannot close an outer block, is an error.
4. Warnings never stop a run; they are listed beside the code and preserved when translating.

## 6 Functions and function-valued parameters

Five of the author's algorithms (linear search, bisection, Newton, Riemann, trapezium) take a function as an input:

```
define bisection(f(x), L, R, P)
...
bisection(2x-3, 0, 2, 0.1)
```

- A parameter written `f(x)` is a **function parameter**; plain `f` is accepted too (as in `define euler(f, t0, x0, dt, n)`).
- **Two ways to pass a function** (decided 2026-11-04). (1) **Expression form**, as on the CAS: the header declares `f(x)` and is followed by the variable, and the call passes an expression and the variable name: `define trapezium(f(x), x, a, b, n)` called as `trapezium(4-(x-1)^2, x, 0, 3, 6)`; inside, `f(x)` evaluates the expression at the current `x`. (2) **First-class function form**: the function is defined first and passed by name: `define f(x)` ... `trapezium(f, 0, 3, 6)`, header `define trapezium(f, a, b, n)`. Both forms are accepted; the corpus has each example in both (`<id>` and `<id>.fn`). Corpus rule: **never `lambda`**; Python references define a named `f(x)` first, and the expression form uses SymPy (`Symbol`, `subs`) in the Python reference. Binding (decided 2026-11-04, Q40): the name must match the variable the expression uses (a mismatch is an error naming both); `f(t)` evaluates the expression with that variable set to `t`; assigning to `x` inside the function is local.
- Functions are called with parentheses; `f()` with no arguments is allowed (`sum_100()`). Functions may return a number or a string, and a function with no `return` returns nothing.
- Variables assigned inside a function are local to it; top-level variables are global and readable inside a function. Recursion is allowed.

## 7 Built-ins and constants

Numeric: `abs`, `sqrt`, `√`, `exp`, `loge` (natural log; `ln` also accepted), `log10`, `sin cos tan`, `asin acos atan` (angle setting applies), `floor`, `ceil`, `round`, `min`, `max`. Constants: `π`/`pi` always; `e` is Euler's number only when the Euler toggle (FR-SET-008) is on, default off; a name the program assigns shadows either (Q29, decided 2026-11-04). Random numbers, needed by the simulation examples: `rand()` uniform on [0,1), `randint(a, b)` (also `randominteger`, the VCAA spelling) inclusive, `rand_norm()` (Could). Random calls use the seed setting so that a trace can be replayed (SRS FR-SET-003). Strings: `+`, `=`, `≠`, and `length(s)` if wanted (Q31).

## 8 Numbers and settings

The settings bar (SRS FR-SET-001) has two controls, **Number mode** (Approx | Auto | Exact) and **Angle** (Radian | Degree), and a "…" menu for everything else. Settings are saved with the program and also affect translation and traces.

| Setting | Values | Effect on a run | Effect on translation to Python |
|---|---|---|---|
| Number mode | **Approx** / **Auto** / **Exact** | **Approx**: `÷` and every non-integer operation give reals. **Auto** (the TI rule): integers and fractions stay exact, so integer ÷ integer is a rational, but any decimal literal makes its result real (`0.5 × 3/4` is real). **Exact**: like Auto, but decimal literals are read as exact fractions (`0.2` is 1/5), so a program of integers and decimals stays exact throughout. In every mode irrational results (`sqrt(2)`, `sin(1)`) are reals, since there is no symbolic algebra; `sqrt(4)` is the integer 2. Integer `+ - × DIV MOD` and `^` with a non-negative integer power stay integers. | Approx emits plain `/`; Auto and Exact emit `Fraction(...)` where a rational can arise |
| Angle | **Radian** / **Degree** | `sin(30)` is 0.5 in Degree and -0.988... in Radian; inverse functions return degrees | wraps arguments: `sin(radians(x))`, `degrees(asin(x))` |
| Display precision (… menu) | default **6 significant digits** (Mathematica style); also Fix n and Full | Reals print to the chosen precision, trailing zeros dropped (`1.2000000000000002` shows as `1.2`, `1/3` as `0.333333`). Integers and rationals always print exactly. The stored value never changes. Applies to output and to trace cells. | none: Python prints its own repr |
| Domain (… menu, Could) | Real / Complex | Real: `sqrt(-4)` is an error; Complex: gives `2ⅈ` | complex-aware functions (`cmath`) |
| Gradian, random seed (… menu, Could) | | A seed makes a run and its trace repeatable | `random.seed(n)` |
| Euler's number `e` (… menu, Should; FR-SET-008) | on / off (default off) | On: an unassigned `e` is 2.71828…; a program's own `e ← …` always shadows it | `math.e` when on |
| Run limits (… menu, Should; FR-SET-009) | max loop iterations (default 10,000), max recursion depth (default 100); adjustable | Reaching one stops the run with a message naming the limit and line; output and trace so far are kept | none |

Defaults: **Approx, Radian, 6 digits** in the standalone Code view (integer ÷ integer is a real, as in Python); on a Nspire page, the document's settings (SRS FR-SET-004). A real with a whole value prints with a trailing point (`5.`), as Mathematica does (decided 2026-11-02), so it differs from the integer `5`; rationals and integers never get one.

Exact values (Q41, decided 2026-11-04): in the first release `sqrt(2)`, `π` and similar are reals in every mode. Exact surd and index forms through the CAS engine, in Auto and Exact modes on CAS pages, are a Could (FR-PSE-012).

## 9 Diagnostics

Which spellings warn or are rejected is set by the syntax file; the table shows the defaults. Messages are in pseudocode terms (line number, the construct, what was expected), never Python tracebacks.

| Situation | Behaviour |
|---|---|
| Undefined variable | Error at the line, with a close-name suggestion (`right` is not defined, did you mean `R`?) |
| `=` used to assign | Warning, treated as `←` |
| Print items without commas | Warning, treated as separate items |
| Indentation disagrees with `end` keywords | Warning |
| Missing `end ...` | Error naming the open block |
| Division by zero, `sqrt` of a negative in Real domain | Error at the line; the trace keeps everything recorded so far |
| Run exceeds the step limit (infinite loop, e.g. `linear(1+x, 0, 0.3)`) | Stops with "stopped after N steps"; the recorded trace remains steppable |
| Unsupported construct (section 10) | Error "not supported yet: lists" etc., never a wrong answer |

## 10 Out of scope for now, with where it appears

All of these are Could in the SRS (FR-PSE-008 to -010) except lists and `rand`/`randint`/`seed`, which are Should (FR-PSE-006, -007).

| Not supported | Where it appears in the sources |
|---|---|
| Lists, `Append`, `Sum`, `for each` (NOW SHOULD, FR-PSE-006) | Sample-proportion simulation (`counts ← []`, `Append count to counts`, `Sum counts`); conventions document ("data structures: tuples, lists, sets") |
| Sets and set builders | Rational Root Finder (`A ← {factors of cn}`, `for each m ∈ A`) |
| Tuple return | VCAA Q6 `maximum_SA(V)` returns `(best_x, best_y, max_SA)` (also contains the slip `maxSA`) |
| `∑`, derivative notation | `sqrt(x'(t)^2 + y'(t)^2)` in the parametric-length slide (the author's own Python replaces it with function arguments `dx`, `dy`) |
| Random distributions beyond `rand`, `randint` (Could; `rand`, `randint`, `seed` are Should, FR-PSE-007) | `rand_norm()` in "Adding random variables" |
| Pairs in `Output (t, x)` | Euler slide; treated as `print t, x` |

## 11 The syntax file

The parser and the printer are driven by a **syntax file** (`syntax-default.yaml` shows the built-in default), not by hard-coded keywords. It is stored in the browser, edited in the app (… menu, Syntax), and can be exported and imported. The ideas:

- **Several spellings per construct**, each one `ok`, `warn` or `no`. An `if` may require, allow or forbid `then`. A `for` loop may end with `end for`, `endfor`, `next` or `next k`; a `while` with `end while`, `endwhile` or `wend`; a function with `end`, `end define`, `end function` or a dedent.
- **Optional tokens**: `then`, `do`, the colon after a `define` header, `is true` after a `while` condition, parentheses around `print` arguments.
- **Operators and symbols**: the spelling lists for `×`, `÷`, `≤`, `←` and so on, with their ASCII equivalents (the `symbols` table of section 3), and the palette contents.
- **Emit style**: what the printer writes when it translates from Python or formats code: keyword case, indent width, which terminators, whether to write `then` and `do`, the arrow and the comment marker.
- **Display**: code is always shown as the user typed it. Trace tables and the code pane refer to the user's own lines, never to a normalised reprint.
- **Safety**: the file is data only (no code, no regular-expression hooks), schema-validated and size-limited. It is rejected, with a message naming the entry, if it makes the grammar ambiguous (one spelling for two constructs; a bare `end` accepted for several constructs without the innermost-block rule; no spelling left for a required construct), and an invalid file falls back to the default.
- **Presets**: Default (tolerant), VCAA, the author's conventions, and Strict (one spelling per construct, warnings become errors). A user's file starts as a copy of a preset.
- **Testing**: for every preset and for generated valid files, printing a program in that style and parsing it again gives the same tree; every golden program must survive restyling under every preset.
- **Shared programs** may carry their non-default syntax settings; opening one asks before applying them and never changes the viewer's own file (decided 2026-11-02).

## 12 Further observations from batch 2 (2026-11-02)

Source: the author's Unit 1 & 2 Methods book (Apr 2024), his Python notebook, and the practice booklet images. These feed the syntax file defaults and the corpus.

- **`function` is a second keyword for `define`**, closed by `end function` (or `end`). Both appear in the author's book and the VCAA exams; the syntax file lists them as equal spellings.
- **`next i` closes a `for` loop** (the book uses it throughout), as well as `end for`; `for ... do` is also written.
- **Functions defined by assignment**: inside a function, `P(x) ← ax³ + bx² + cx + d` defines a local function (book `newton3`). Treat `name(params) ← expression` as a definition when the left side has a parameter list. Called as a statement, a function's return value is discarded.
- **`mod`** is an infix operator (`x ← angle mod 2π`); `π` is a constant and `2π` is implicit multiplication. Open: the book's pseudocode `sine` means the true π, while its Python uses `355/113`, so their printed errors differ.
- **Default parameter values** appear (`newton(f, x0, steps, h=10⁻⁶)`); also `10⁻⁶` and `10^-(dp+1)` as exponent spellings.
- **`⩽` (U+2A7D)** is the author's spelling of ≤ and **`|df - df_old|`** is absolute value; both are in the default syntax file.
- **Print and line ends** (Q36, decided): `print` ends the line by default; the … menu and the syntax file can change what is appended (new line, space, nothing). The book's linear-search example (two prints, one output line, split only to fit the page) is kept in the corpus as a single `print`.
- **Style** (reviewed 2026-11-04): the printer writes `print` as a command (`print total`) and multiplication explicitly (`2*a` or `2×a`); the parser still accepts `print(total)` and `2a`, and VCAA cases that use them are kept exactly as VCAA wrote them to exercise the flexible syntax. `sum` is not used as a variable name in the corpus (`total` instead; it shadows a Python builtin, and VCAA's `sum` is noted on each case). Python references have a blank line after each function.
- **Author slips** the tolerant parser must survive (as in the exams): `dfPref` for `df_old`, `P(x)`/`dP(x)` used where `f(x)`/`df(x)` were defined, `⩽` in pseudocode versus `<` in the Python.
- **Lists are Should** (`coeffs`, `tally`; 1-based by default, a toggle in the … menu switches to 0-based, decided); **sets, dictionaries, tuples, set comprehensions, prose steps and graphs/adjacency dictionaries are Could** (the middle-square "Pseudocode" is prose; the Specialist Unit 1 notebook uses sets and graphs). Generators and `yield` are Python-only (run by CPython, not translated).
- **Random numbers are Should** (`rand()`, `randint`, `seed`). The runtime reproduces CPython's seeded sequences exactly (MT19937, CPython's seeding, `random()` and `randint`; decided), so the book's `seed(42)` tallies are golden tests; unseeded programs are tested by properties (range, mean within tolerance).
- **Python subset used in the notebook** (relevant to the Python worker, FR-RUN, not to the shared tree): `input`/`float(input())`, f-strings with `:.2f`/`:.6f`/`:0>4`, list and generator comprehensions, `lambda`, `enumerate`, `zip`, `set`, `Counter`, `random`, `math`, `numpy`, `sympy` and `matplotlib`. The Pyodide worker must therefore ship numpy, sympy and matplotlib.
- **`√` and `√( )`** are sqrt (2025 and 2026 Specialist exams: `return √(x + 1)`); `π(f(left))²` is π × f(left) squared by implicit multiplication; a function named `sum` or a variable named `sum` is legal (it shadows the built-in). Function bodies without `end` (ended by dedent) are common in the 2024 and 2025 exam text.

## 13 Decisions of 2026-11-07 (from the batch-3 corpus review)

- **`and` and `or` short-circuit**, as in Python: `while i ≥ 1 and a[i] > key` must not evaluate `a[i]` when `i` is 0. The tracer shows only the operands actually evaluated.
- **Operator precedence copies Python's.** `DIV` and `MOD` have the same level as `×` and `÷`, evaluated left to right (`a × b DIV g` is `(a×b) DIV g`); `^` binds tighter than unary minus on its left (`-x^2` is `-(x^2)`).
- **Notation stays flexible.** The list spellings `Append x to a` / `append x to a`, `for each x in a`, `len(a)` and indexing `a[i]` are accepted as written in the author's sources; the syntax file can add or warn on others.
- **π is the built-in constant** (`π` or `pi`) wherever a program needs it; a program may instead define its own decimal approximation (a name it assigns shadows the constant). The book's `sine` therefore uses `π`, not 355 ÷ 113 (its printed error table is what true π gives).
- **Extended Euclid** (Bezout coefficients) is in the corpus as a Specialist example.

## 14. Decisions of 2026-11-07 (second batch: the author's own code examples)

- **Expression arguments.** The pseudocode for the expression-argument cases (`define riemannRight(f(x), x, a, b, n)` called as `riemannRight(x^2-x, x, 1, 5, 4)`) stays as written. The reference Python stays on SymPy (`Symbol`, `.subs`) for now. Idea to revisit: the Python Code view could emit different Python by mode, SymPy-based in Exact mode (exact rationals, symbolic results) and a plain `lambda` / floats in Approx mode.
- **No string manipulation in the first version.** Examples that iterate over strings, concatenate, index a string or need `ord`/`chr` (Caesar cipher, disemvowel, palindrome) are not in the corpus. Printing string literals (`print "steps", n`) is unchanged.
- **Lists are values, not passed by reference.** A function receives its own copy of a list argument; changing it inside the function does not change the caller's list. A function that sorts or updates a list RETURNS the new list, and the caller assigns it (`a ← quicksort(a)`). The in-place quicksort is therefore out; the not-in-place `quicksort` that returns a list stays. Recursive algorithms are included only in this return-the-list form.
- **Booleans.** `true` / `false` are values, and the syntax accepts any case (`true`, `TRUE`, `True`). A printed boolean is UPPERCASE, `TRUE` / `FALSE`, so test output is the same everywhere.
