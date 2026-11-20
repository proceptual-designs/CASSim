# 0035: One maths tree, a parser bridge into it, and shared renderers

Status: accepted (Simon, 2026-11-20); stages 1 and 2 done, 3 and 4 planned. Builds on 0014 (results drawn from LaTeX), 0015 (our own template editor, kept) and 0019 (entry line drawn from Flet controls).

## The bugs that started it
1. `completeSquare(x^(2)-2x,x)` gives `(x-1)^2-1`. Up, then Enter, brought down `(x-1)^(2-1)`, a different value.
2. `solve(x^(3)-3x+1=0,x)`, then Up and Left or Right: every `√(3)` in the picked result took in the rest of the line (20 nested templates in that result).

Both had one cause. A picked history row was built with `Editor(text)`, which types the text key by key, and a typed `^` or `√` opens a template that holds everything after it. Bug 2 showed only after a key: a picked row is drawn from SymPy's LaTeX until the cursor moves in it, and from its editor after that (`screen.py`).

## What the investigation found
- **No structured way into the editor tree.** Text became a tree three ways, none using the parser: key-by-key typing (the bug), `_paste_linear` (knows only `^` and `√`; fractions, `abs` and matrices stay flat) and `modernised` (character patterns for `sqrt(`, `exp(`, `pi`).
- **Two printers for one result.** `Result.text` comes from our AST (`format.to_text`); `Result.latex` comes straight from SymPy. A screen that changes from one to the other jumps: stacked fractions become `π/9`, `\cos` becomes letter-by-letter `\mathrm`.
- **Three renderers for one tree.** `Editor.latex()` (Markdown, no hit-testing: history entries and picked rows), `devices/nspire/ui/entry.py` (Flet controls with click zones: the entry line) and SymPy LaTeX (results).
- **A template kind is defined in about five tables** (`_SLOTS`, `_CALLS`, `_LATEX`, the `entry.py` drawers, `row_height`), kept in step by hand.
- **Not shareable.** `entry.py` is inside the Nspire device, so other devices cannot reuse the entry line.
- **Speed is unmeasured.** History rows are cached; the entry line is rebuilt with several Flet controls per character on each key (0019). Not measured on a Chromebook.

The editor model itself (rows of characters and templates, a cursor path, the TI editing rules) is sound and stays.

## Options
| Option | Verdict |
|---|---|
| A. Harden our own: a parser bridge into the tree, one registry per template kind, renderers that share one tree | **Chosen.** Fixes the cause; pure Python, tested headlessly; keeps the TI rules; consistent with 0015. |
| B. MathLive in a Dart extension | Mature editing and accessibility, but the TI rules (fraction capture, `Ans`, highlight-then-delete) become its configuration, its LaTeX or MathJSON needs a converter to TI text, about 1 MB of JS and fonts, focus problems across the DOM and canvas boundary, and editor tests stop being headless. |
| C. A custom Flutter widget that only draws (Python keeps the model) | Best speed and hit-testing (one widget a line, not controls per character). Dart to maintain. Kept as a later backend behind the renderer interface (stage 4) if measurement calls for it. |
| D. `math_keyboard` or `flutter_math` editing | Rejected in 0015: too limited for the TI templates. |

## Plan
1. **Bridge (done).** `device/editor_ast.py`: `row_from_ast` turns a core AST into a row (fraction, power, root, nth root, log with a base, absolute value, matrix; anything else as characters with only the brackets precedence needs), and `row_from_text` parses first and falls back to a linear paste if the text does not parse or the tree would not read back the same. A picked history row uses it. Guard: a Hypothesis test that `parse(linear(row_from_ast(e))) == e` for random expressions (`tests/device/test_editor_ast.py`).
2. **One registry of template kinds (done).** `device/templates.py` declares each kind once in a `Spec`: slots, grid width, whether Left and Right walk its slots, its LaTeX, its linear text, and the call it is written as. A function-like kind's linear text is made from its call, and the bridge reads the same call back, so the two cannot drift (`derivative`, `∫`, `Σ` and `Π` results now come back as templates too). `editor.py` lost its six per-kind tables and special cases. Drawing as controls stays in the UI; `entry.py` names the kinds it draws (`DRAWN_KINDS`) and a test checks that against the registry, where before an unknown kind fell through to the matrix drawing unseen. The Graphs page parses a function set from text (a saved file, a menu), so a saved fraction or power comes back as its template.
   - **Fixed on the way:** a fraction or matrix template straight after a term was written `x((1)/(2))` and `x[1,2]`, which the parser reads as a call of a function x and as indexing. Typing x then the ½ template gave `x(1/2)`. Both now join with `*`, as the function-like templates did (`x/2`, `[x,2·x]`).
   - **Changed from the first plan:** pasted text and `modernised` do not go through the parser. A typed `/` stays linear while editing, as on the handheld (0017), so pasted text keeps its linear `/`; and putting the entry as typed through the parser would rewrite the student's spelling (`2x` as `2*x`) and cannot read statements such as `Define`. Changing how an entry is echoed needs emulator evidence first.
3. **One renderer interface, two backends.** A LaTeX string for rows that are only shown, and controls with hit zones for rows that are edited, both drawn from the same tree. Results are drawn from their AST through the bridge, so a picked row looks the same before and after the cursor moves; SymPy's LaTeX stays only as a fallback.
4. **Shared, measured.** Move the entry-line renderer out of `devices/nspire/ui` to a device-neutral place, with the theme and key map supplied by the device. Measure the entry line on a Chromebook; build option C only if it is too slow.

## Left open
- Until stage 3 the picked row still changes look when the cursor first moves in it (SymPy's LaTeX before, the tree's after); the structure is now right in both.
- `solve(x^3-3x+1=0,x)` gives a long `real(…)`/`imag(…)` answer. Correct, but the device's form has not been checked; it needs a corpus case of its own.
