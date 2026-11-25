# Scientific calculator

CASSim Scientific is a natural-display scientific calculator of the kind used in Australian schools for Years 7–10, VCE General Mathematics and the non-CAS parts of Methods and Specialist. Its keys can follow the Casio fx-82 series (the default), the Abacus SX-II series, the Sharp EL-531 series or the HP 10s series, so what students practise here carries over to their own calculator: see [[Choosing your calculator]].

Open it from the Home screen of <https://cassim-app.pages.dev/>, or use its own site, <https://cassim-sci.pages.dev/>, which opens straight into it.

> CASSim Scientific is an independent simulator. It is not an approved exam calculator. Its behaviour has not yet been compared key for key with a physical calculator; see [[What works and what does not yet]].

## The keypad

This page describes the fx-82 series keys. On the other calculators the keys and some sequences differ: [[Choosing your calculator]] lists the differences.


Each key does what its face says. The small yellow label above a key is its **SHIFT** function and the red label is its **ALPHA** function: press SHIFT or ALPHA first, then the key. S or A lights at the top of the screen while one is waiting.

- **MODE** chooses COMP (calculations), STAT (statistics), TABLE (a table of values) or VERIFY (true or false). **SHIFT MODE** opens SETUP.
- **SHIFT 9** (CLR) resets the setup, clears the memories, or both. Press = to confirm or AC to cancel.
- **SHIFT AC** (OFF) switches the calculator off; **ON** (or `o` on the keyboard) switches it on again.
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

The **Tutorials** panel teaches the skills students need, in the keys of the calculator you chose. On the fx-82 keys there are twelve: resetting the calculator, the frequency column, mean and standard deviation, five-number summaries, frequency tables, regression, fractions, exact trigonometry, percentages, memories, prime factorisation and tables. The SX-II, EL-531 and 10s have their own lists ([[Choosing your calculator]]).

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
| o | ON: switches the calculator on again after SHIFT AC (OFF) |
| < > | Relations, in VERIFY mode |
| Ctrl+C | Copy the answer |

Hover over a key to see its shortcut, or open **CASSim ▸ Keyboard shortcuts**.

## Saving and sharing

Your calculator is saved in the browser as you go. **Doc ▸ Save** keeps the calculator under a name in this browser, and **Doc ▸ Open** lists what you have saved, as in the other CASSim apps. To move one to another computer, **Doc ▸ Export file…** downloads a `.cassim.json` file and **Import file…** opens one. **Doc ▸ Share link** makes a link that holds the settings, memories, STAT data and TABLE function, so a teacher can send a class a data set ready to analyse. The link never sends anything to a server. **Doc ▸ Examples** loads ready-made problems.

The full-screen button at the right of the menu bar hides the bar for presenting; Esc or the button in the corner brings it back. **CASSim ▸ Appearance** offers a dark theme, a light theme and a high-contrast theme for projectors. **CASSim ▸ Settings** sets the same choices as SETUP, including a decimal comma in answers.

## On a phone

On a phone the calculator fills the screen and its keys grow to use the height. The tutorials start hidden: **CASSim ▸ Show tutorials** brings them back, below the calculator, and **Hide tutorials** puts them away (on a larger screen the same menu item, or the Tutorials button, does the same). The menu bar keeps the calculator and mode chips. In the installed app, **CASSim ▸ Avoid cutout** keeps the calculator clear of the camera cutout, and **Use cutout** draws under it again.
