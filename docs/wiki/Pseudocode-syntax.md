# Pseudocode syntax

This page lists what the Pseudocode & Python app accepts with its default settings. The style follows the VCAA Mathematics pseudocode and the conventions taught in VCE Maths classes, but the app is deliberately tolerant: most constructs can be written several ways, so code copied from an exam paper, a textbook or a classmate usually runs as it is.

- **ok** means accepted silently.
- **warning** means it runs, but it is not the usual spelling. (The app does not show these warnings yet.)
- Keywords can be in any case (`if`, `If`, `IF`). Variable names are case-sensitive: `A` and `a` are different variables.
- Each column shows the same thing in pseudocode and in the Python that **Translate** writes. Pseudocode lists count from 1 and Python lists from 0; the translation takes care of that.

## Statements

| What | Pseudocode (recommended) | Also accepted | Python |
|---|---|---|---|
| Comment | `// a note` | `# a note` | `# a note` |
| Assignment | `count ← 5` | `count <- 5`, `count := 5`; `count = 5` (warning, because `=` also means "is equal to") | `count = 5` |
| Input | `input n` | `Input n` | `n = read_value()` (a short helper that turns typed numbers into numbers) |
| Output | `print x, 5, x*x` | `print(x, 5, x*x)`, `output x`, `Output x`; `print "x is" x` without a comma (warning) | `print(x, 5, x*x)` |
| Define a function | `define f(x)` … `end` | `function f(x)` … `end function`; `end define`; a colon after the header (`define f(x):`); no `end` at all, if the next line is back at the indent of `define` | `def f(x):` |
| One-line function | `f(x) ← x² + 1` | | `def f(x):` / `return x ** 2 + 1` |
| Default value | `define newton(f, x0, h=10⁻⁶)` | | `def newton(f, x0, h=10**-6):` |
| Return | `return x*x` | | `return x*x` |
| Call a function | `y ← f(5)` | `f(5)` on its own line (the result is thrown away) | `y = f(5)` |
| Break out of a loop | `break` | | `break` |

## Selection

| What | Pseudocode (recommended) | Also accepted | Python |
|---|---|---|---|
| If | `if x > 0 then` … `end if` | no `then`; `endif` | `if x > 0:` |
| If … else | `if c then` … `else` … `end if` | as above | `if c:` … `else:` |
| Else if | `else if c2 then` | `elseif c2`, `elif c2` (`then` is optional) | `elif c2:` |

## Iteration (loops)

| What | Pseudocode (recommended) | Also accepted | Python |
|---|---|---|---|
| Count-controlled | `for k from 1 to n` … `end for` | `do` at the end of the first line; `endfor`, `next`, `next k` | `for k in range(1, n + 1):` |
| With a step | `for k from 10 to 0 step -2` | as above | `for k in range(10, -1, -2):` |
| Pre-condition (zero or more times) | `while x < 10 do` … `end while` | no `do`; `endwhile`, `wend`; `while done is true` | `while x < 10:` |
| Fixed number of times | `repeat 5 times` … `end repeat` | `endrepeat` | `for _ in range(5):` |
| Post-condition (at least once) | `repeat` … `until x > 10` | `Repeat` … `Until` | `while True:` … `if x > 10: break` |
| For each item of a list | `for each v in data` … `end for` | `for v in data` (Python style); `next v` | `for v in data:` |

`for` ranges include both ends: `for k from 1 to 3` runs with k = 1, 2 and 3. A `repeat … until` loop stops when its condition becomes **true**.

## Lists

| What | Pseudocode | Python |
|---|---|---|
| Make a list | `data ← [2, 3, 4]`, an empty list `[]` | `data = [2, 3, 4]` |
| An item (first is 1) | `data[1]` | `data[0]` |
| Change an item | `data[2] ← 7` | `data[1] = 7` |
| Add to the end | `append 5 to data` (or `Append`) | `data.append(5)` |
| Length, total | `len(data)`, `sum(data)` | `len(data)`, `sum(data)` |

Square brackets always make a list. Use round brackets `( )` to group.

## Operators

| What | Recommended | Also accepted | Python |
|---|---|---|---|
| Add, subtract | `+`, `-` | `−` and `–` (the minus signs in exam papers) | `+`, `-` |
| Multiply | `×` | `*`, `·`; nothing at all between a number and a name or bracket: `2a`, `2(a+1)`, `(a+1)(a-1)` | `*` |
| Divide | `÷` | `/` | `/` |
| Whole-number division and remainder | `div`, `mod` | `DIV`, `MOD`; `%` (warning) | `//`, `%` |
| Power | `x²`, `x⁻¹`, `2ˣ⁺¹` | `x^2`, `x**2`, `2^(x+1)` | `x**2` |
| Square root | `√(x)` | `√x`, `sqrt(x)` | `x ** 0.5` |
| Absolute value | `\|x\|` | `abs(x)` | `abs(x)` |
| Equal | `=` | `==` | `==` |
| Not equal | `≠` | `<>`, `!=` | `!=` |
| Less, greater | `<`, `>` | | `<`, `>` |
| Less or equal | `≤` | `<=`, `⩽` | `<=` |
| Greater or equal | `≥` | `>=`, `⩾` | `>=` |
| And, or, not | `and`, `or`, `not` | `∧`, `∨`, `¬` | `and`, `or`, `not` |

Comparisons can be chained as in maths: `0 < x ≤ 1`. `and` and `or` stop early, as in Python, so `i ≥ 1 and a[i] > 0` never looks at `a[0]`.

Superscripts: a run of superscript digits is a power (`x²`, `10⁻⁶`). A run that has letters, `⁺`, `⁻` or brackets is the whole exponent, so `2ˣ⁺¹` means `2^(x+1)`. There is no superscript `q`, `×` or `÷`, so write those powers with `^`. With the typing aid on (Settings), typing `x^2` or `2^(x+1)` becomes the superscript form after a short pause.

## Values and built-in functions

| What | Accepted |
|---|---|
| Numbers | `12`, `-2`, `0.5`, `.5`, and powers of ten as `1E-3` or `1ᴇ-3` (a lower-case `e` is never a power of ten: `2e3` is 2 × e3) |
| True and false | `true`, `false`, in any case; printed as `TRUE` and `FALSE` |
| Text | `"straight"` or `“curly”` quotes |
| π | `π`, `pi`, `@pi` |
| Euler's number | `ⅇ`, `@e`, and a plain `e` unless your program gives `e` its own value (Settings can turn this off) |
| Infinity | `∞`, `inf` |
| Functions | `sqrt`, `√`, `abs`, `exp`, `ln` or `loge`, `log10`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `floor`, `ceil`, `round`, `min`, `max`, `sum`, `len` |
| Random numbers | `rand()` (between 0 and 1), `randint(a, b)` or `randominteger(a, b)` (both ends included), `seed(n)` to repeat the same numbers |

Angles are in radians unless Settings says Degree.

## Functions as inputs

A function can be given to another function in two ways:

- **By name:** define `f` first, then call `bisection(f, 0, 2, 0.001)` with the header `define bisection(f, a, b, tol)`.
- **As an expression, as on a CAS:** write the header as `define trapezium(f(x), x, a, b, n)` and call `trapezium(4 - (x-1)², x, 0, 3, 6)`. Inside, `f(t)` works out the expression with `x` replaced by `t`.

Variables given a value inside a function belong to that function. A list passed to a function is a copy: to change a list, return the new one and assign it (`a ← sorted_list(a)`).

## Layout

- One statement per line. Blank lines are ignored.
- Indent the inside of a block (two or four spaces is usual). The `end` words decide where blocks finish. If one is missing, the closing word of an outer block, or a line back at the outer indent, closes it with a warning.
- A colon is allowed only after a `define` header. `if x > 0:` is an error: use `then` or nothing.
- A comment can be on its own line or at the end of a line. **Translate** keeps comments on their own lines and blank lines in both directions (several blank lines in a row become one); comments at the end of a line are not kept yet.

## Not supported yet

- Sets, tuples, dictionaries and `case of` statements
- Joining or slicing text (printing text is fine)
- `∑` and derivative notation such as `x'(t)`
- Several statements on one line
