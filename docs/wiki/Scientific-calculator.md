# CASSim Scientific (scientific calculator)

CASSim Scientific is a natural-display scientific calculator of the kind used in Australian schools for Years 7–10, VCE General Mathematics and the non-CAS parts of Methods and Specialist. It has the familiar 50-key layout, so what students practise here carries over to their own calculator. It is in the testing version of CASSim while it is being built: open it from the Home screen, or go straight to it with `#/app/scientific` after the site address.

> CASSim Scientific is an independent simulator. It is not an approved exam calculator. Its behaviour has not yet been compared key for key with a physical calculator; see [[What works and what does not yet]].

## The keypad

Each key does what its face says. The small yellow label above a key is its **SHIFT** function and the red label is its **ALPHA** function: press SHIFT or ALPHA first, then the key. S or A lights at the top of the screen while one is waiting.

- **MODE** chooses COMP (calculations), STAT (statistics), TABLE (a table of values) or VERIFY (true or false). **SHIFT MODE** opens SETUP.
- **SHIFT 9** (CLR) resets the setup, clears the memories, or both. Press = to confirm or AC to cancel.
- The arrow keys move the cursor through fractions and other templates. After an answer, ▲ and ▼ show earlier calculations and ◀ ▶ let you edit the last one.

## Answers

In natural display (MthIO, the default) answers stay exact: fractions, surds such as 3√2 and multiples of π. **S⇔D** switches between the exact answer and the decimal; **SHIFT S⇔D** switches between a mixed number and an improper fraction. A decimal answer only turns into a fraction when the fraction really equals it.

SETUP sets Norm 1 or Norm 2, a fixed number of decimal places (Fix) or significant figures (Sci), degrees, radians or gradians, and natural or linear display. **ENG** shows the answer with a power of ten that is a multiple of 3; press it again for the next one, or SHIFT ENG to go the other way. **° ' "** turns the answer into degrees, minutes and seconds, and **SHIFT ° ' "** (FACT) writes a whole number as a product of primes.

## Statistics

1. Press MODE, 2 (STAT), then 1 for one variable or 2 for a straight line (3–8 are the curved fits).
2. Type each value and press =. Use the arrow keys to move between columns. DEL deletes a row and SHIFT DEL inserts one.
3. Press AC to go back to the calculation screen. The data stays until you leave STAT mode.
4. Press SHIFT 1 for the STAT menu: Sum, Var (n, x̄, σx, sx…), MinMax (min, Q1, median, Q3, max) and, for two variables, Reg (A, B, r, x̂, ŷ). Choose an item, then press =.

Quartiles use the method taught in Australian schools: Q1 and Q3 are the medians of the lower and upper halves, leaving the median out when there is an odd number of values. sx divides by n − 1 and σx by n. To use frequencies, turn on the FREQ column first: SHIFT MODE, ▼, 3 (STAT), 1 (ON). SETUP's second page also has Disp (a decimal point or a decimal comma in answers) and CONT (contrast: ◀ ▶, then AC).

## Tables

Press MODE, 3. Type f(X) (ALPHA then ) types X), press =, then enter the start, end and step, pressing = after each. Use ▲ ▼ to scroll the table and AC to change the function. A table can have up to 30 rows.

## Tutorials

The **Tutorials** panel teaches twelve skills: resetting the calculator, the frequency column, mean and standard deviation, five-number summaries, frequency tables, regression, fractions, exact trigonometry, percentages, memories, prime factorisation and tables.

- **Guide me**: you press every key. The next key glows; a wrong key gives a hint and changes nothing.
- **Show me**: the lesson plays itself, at a speed you choose.
- **Test me**: a new problem with no hints. Press **Check my answer** when you have it.

Your own calculation is put aside during a lesson and comes back when the lesson ends. Finished lessons are ticked. Progress is kept in your browser only.

## Keyboard

| Keys | What they do |
|---|---|
| 0–9 . + - * / ( ) ^ | As on the keypad (/ is ÷ and ^ is the power key) |
| Enter or = | = (in VERIFY mode = types the equals sign; Enter calculates) |
| Backspace, Delete | DEL |
| Esc | AC, and shows the menu bar when it is hidden |
| Arrow keys, Home, End | Move the cursor; ▲ ▼ recall earlier calculations |
| F1, F2 | SHIFT and ALPHA, then any key |
| Ctrl+M | MODE (F1 then Ctrl+M for SETUP) |
| Ctrl+/ | Fraction |
| s, c, t (S, C, T) | sin, cos, tan (their inverses) |
| h, l, n (L, N) | hyp, log, ln (10■ and e■) |
| r (R), q | √ (³√), x² |
| g | log■□, a logarithm with a base |
| ! % , | x!, %, comma |
| d (D) | ° ' " (FACT) |
| m (M) | M+ (M−) |
| p, e, a, x, y | π, e, Ans, X, Y |
| < > | Relations, in VERIFY mode |
| Ctrl+C | Copy the answer |

Hover over a key to see its shortcut, or open **CASSim ▸ Keyboard shortcuts**.

## Choose your calculator's keys

**CASSim ▸ Appearance ▸ Calculator** shows the keys of the calculator you use, so you can find them in the same places: the Casio fx-82 series (the default), the Abacus SX-II series, the Sharp EL-531 series or the HP 10s series. The title on the calculator says which, for example CASSim Scientific (SX-II). The key names, the labels above the keys and the arrangement follow that calculator, and so do the key sequences: the menus, clearing, entering statistics and getting the results work as they do on that calculator, so you can practise on your own model. The look is CASSim's own. The tutorials are written in that calculator's keys.

Those calculators do differ in what they can do, and CASSim follows them:

| | fx-82 series | SX-II series | EL-531 series | 10s series |
|---|---|---|---|---|
| SHIFT key is called | SHIFT | 2nd | 2ndF | SHIFT |
| Display | natural (textbook) | natural ("Math") | two lines, linear | two lines, linear |
| Modes | COMP, STAT, TABLE, VERIFY | COMP, STAT, VERIF | NORMAL, STAT (SD, LINE and other fits) | COMP, SD, REG |
| Settings | SHIFT MODE (SETUP) | 2nd SET UP | SET UP, and DRG for the angle | MODE, pressed again for each page |
| Clearing | SHIFT 9 (CLR) | 2nd CLR | 2ndF M-CLR, 2ndF CA | SHIFT MODE (CLR) |
| Exact or decimal | S⇔D | F↔D | a b/c after an answer | a b/c after an answer |
| Entering STAT data | the data table | the data table | x (x,y) f DATA | x ; f DT, or x , y DT |
| STAT results | SHIFT 1 menus | 2nd STATVAR menus | RCL then the key (RCL x̄) | SHIFT S-SUM, SHIFT S-VAR |
| Q1, median, Q3 | yes | yes | no | no |
| Prime factors (FACT) | yes | yes | no | no |

- On a linear calculator a fraction shows as 2⌟3 and a surd as a decimal. Choosing the EL-531 or 10s keys switches SETUP to linear display; you can switch it back in SETUP.
- The EL-531 keys also show base-n and logic functions; CASSim Scientific does not do those, so the keys do nothing.
- The tutorials offer only what your calculator can do, in its own keys: the HP 10s and EL-531 have no frequency setting, five-number summary, prime factorisation or table lessons.
- On the HP 10s, % works out the whole calculation as the fx-82MS family does: 250 × 15 SHIFT % gives 37.5, and + straight after gives 287.5. On the EL-531, 250 + 15 2ndF % gives 287.5.
- The computer keyboard types the fx-82's keys, so F1 then Ctrl+M is SETUP on the fx-82 but CLR on the HP 10s, as SHIFT MODE is on each.
- The EL-531's M-CLR menu, CA and STAT VAR have not yet been checked against a real calculator.
- Older fx-82 models (such as the fx-82MS) have a linear display and no VERIFY or TABLE.

## Saving and sharing

Your calculator is saved in the browser as you go. **Doc ▸ Save** and **Open** use `.cassim.json` files, like the other CASSim apps. **Doc ▸ Share link** makes a link that holds the settings, memories, STAT data and TABLE function, so a teacher can send a class a data set ready to analyse. The link never sends anything to a server. **Doc ▸ Examples** loads ready-made problems.

The full-screen button at the right of the menu bar hides the bar for presenting; Esc or the button in the corner brings it back. **CASSim ▸ Appearance** offers a dark theme, a light theme and a high-contrast theme for projectors.
