# 0007. Parser grammar (M1a)

Date: 2026-11-01. Status: accepted; the choices in "To check on the simulator" are provisional.
Code: `src/cassim/core/{lexer,parser,ast,errors}.py`. Tests: `tests/unit/test_{lexer,parser,printer,parser_corpus}.py`.

## Settled by the Reference Guide (CAS 3.2, EOS appendix, pp. 166-167)

- Operator precedence, levels 1 to 18 (`Prec` in `ast.py`). `^` is right-associative; post operators bind tighter than `^` (`4^3!` is `4^6`); `^` binds tighter than negation (`-9^2` is `-81`).
- A name followed by parentheses is always a function call: `a(b+c)` calls `a`, and `2x(x-1)` is `2*x(x-1)`. The evaluator decides whether that call is valid. The guide lists error 440, "Invalid implied multiply", for `x(x+1)`.
- Error codes: 910 syntax, 680/690 missing parentheses, 700 missing quote, 710 missing `]`, 720 missing `}`.

## Settled by Simon (2026-11-01)

- **Implied multiplication has the strength of `*`**, so `1/2x` is `(1/2)*x`.
- **`e`, `ⅇ` and `ᴇ` are three different things.** `e` is an ordinary variable, `ⅇ` (bold on the calculator) is Euler's constant, and `ᴇ` (the special uppercase E) is the exponent marker. So `2e3` is `2*e3` and `2e-1` is `2*e-1`. A plain `E` is a variable too, since names are case-insensitive.
- **Canonical text is Unicode**, because ASCII cannot carry that distinction. The GUI shows it directly. `to_ascii` in `format.py` respells it for the REPL, using spellings the lexer accepts. The spellings are TI's own table in the CAS guide, pp. 164-165: `@e`, `@i`, `@E`, `@t`, `@r`, `@g`, `@d` (°), `@<` (∠), `@>`, `infinity`, `pi`, `theta`.
- **`polar()` was considered for `∠` and dropped**: TI's `@<` keeps it infix and reserves no name.
- **`°` multiplies by π/180 in Radian mode and by 1 in Degree mode** (for M1b; Gradian mode is not yet checked). It also appears in results: `▶DD` shows `30°` and `▶DMS` shows `30°30'`.

## Design decisions

- **One AST for one meaning.** Implied multiplication becomes `Binary("*")`, spellings are folded in the lexer (`<=` to `≤`, `@>` to `▶`), and `[[1,2],[3,4]]` flattens to `[1,2;3,4]`. Assign and Store stay separate so printing preserves what was typed.
- **Text kept as typed.** `Number` holds its raw text because `1.` and `1` differ (approximate versus exact). Names keep their case and are not resolved: `pi`, `π`, `infinity`, `∞`, `theta`, `θ`, `true`, `Ans`, `undef`, `ⅇ` and `ⅈ` are plain `Name`s, and so is the display form `sin⁻¹`; the evaluator must treat each spelled and symbol form as one. Only `and or not xor nor nand` are keywords.
- **Chained relations** are one `Compare` node, so `0≤x≤2*π` keeps its shape for `|` constraints.
- **Commands** are recognised from a fixed list only at the start of a statement. Those names are reserved, and using one in an expression is a syntax error. Control flow (`If`, `For`, ...) and multi-line `Func` bodies are left to `cassim.basic` in M5.
- **`▶` and `∠`** are missing from the EOS table. `▶` binds just above Store, because the guide allows it only at the end of an entry line. `∠` binds just below `+` and `-`, so `2∠π/4+1` keeps a whole angle; `∠θ` alone is a prefix form because TI displays vectors as `[r ∠θ z]`.
- **Spaces inside `[ ]`** separate elements, since TI displays results as `[√(2) ∠π/4 1]` and the replay harness must parse displayed results. A minus stays binary, so `[1 -2]` is one element, `-1`.
- **Depth limit.** A budget (`MAX_DEPTH`) covers both nesting and chain length, so a tree can never overflow the stack in later recursive code. Limits: about 80 levels of parentheses, or a sum of about 240 terms; beyond this the user gets a syntax error. Long data lists are unaffected.

## To check on the simulator

The guide does not settle these. None is pinned by a corpus case, so each is a guess at TI's behaviour. Each row is one entry to type.

| Entry | Parser now reads it as | Why it matters |
|---|---|---|
| `2 3` | syntax error | |
| `x 3`, `(x+1)2` | products | |
| `sin (0)` | call to `sin` | |
| `[1 2 3]`, `[1 -2]` | 3 elements; 1 element | Input form not yet seen, only display |
| `+3` | syntax error | Could be accepted as `3` |
| `√4` | error "Missing (" | |
| `x²` | syntax error | |
| `(2∠π/4+1)` | angle is `π/4+1` | |
| `2+3@>Rad`, and `@>` in mid-line | applies to the whole of `2+3` | |
| `a!=b` | `a!` then `=b` | |
| `lu:=1`, `text:=1`, `wait:=1`, `fill:=1` | syntax error (reserved) | Students may use these names |
| `5→a→b` | syntax error | |

## Known limit

`(list)▶mat(1)` prints as `list▶mat(1)`, which reads back as the catalog function `list▶mat`. This needs a variable called `list`, `mat` or `exp` converted with a function-style target, which no real conversion uses.
