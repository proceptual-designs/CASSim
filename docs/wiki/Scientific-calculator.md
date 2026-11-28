# Scientific calculator

CASSim Scientific is a natural-display scientific calculator of the kind used in Australian schools for Years 7–10, VCE General Mathematics and the non-CAS parts of Methods and Specialist. Its keys can follow the Casio fx-82 series (the default), the Abacus SX-II series, the Sharp EL-531 series or the HP 10s series, so what students practise here carries over to their own calculator: see [[Choosing your calculator]].

Open it from the Home screen of <https://cassim-app.pages.dev/>, or use its own site, <https://cassim-sci.pages.dev/>, which opens straight into it.

> CASSim Scientific is an independent simulator. It is not an approved exam calculator. Its behaviour has been checked against the makers' own emulators, but not yet against a physical calculator; see [[What works and what does not yet]].

## The keypad

This page describes the fx-82 series keys. On the other calculators the keys and some sequences differ: [[Choosing your calculator]] lists the differences.


Each key does what its face says. The small yellow label above a key is its **SHIFT** function and the red label is its **ALPHA** function: press SHIFT or ALPHA first, then the key. S or A lights at the top of the screen while one is waiting.

**hyp** opens a list of the hyperbolic functions (sinh, cosh, tanh and their inverses). While the list shows, hyp lights up, `hyp` shows at the top of the screen and the sin, cos and tan keys read sinh, cosh and tanh: press one of them, or the number in the list. Press hyp again to cancel. The real calculator keeps its key names; CASSim renames them to help you learn, and **CASSim ▸ Settings** can turn this off.

- **MODE** chooses 1 COMP (calculations), 2 STAT (statistics) or 3 VERIF (true or false). With the TABLE extra on (see below), 4 is TABLE (a table of values). **SHIFT MODE** opens SETUP.
- **SHIFT 9** (CLR) resets the setup, clears the memories, or both. Press = to confirm or AC to cancel.
- **SHIFT AC** (OFF) switches the calculator off; **ON** (or `o` on the keyboard) switches it on again.
- The arrow keys move the cursor through fractions and other templates. After an answer, ▲ and ▼ show earlier calculations and ◀ ▶ let you edit the last one.

## Answers

After a reset the calculator is in MthIO-LineO, as the fx-82 and SX-II are: you type in natural display, and answers come as decimals first (1 ÷ 200 gives 0.005) unless you typed a fraction (1/3 + 1/4 gives 7/12). **S⇔D** switches between the decimal and the fraction; **SHIFT S⇔D** switches between a mixed number and an improper fraction. In SETUP, MthIO-MathO gives fractions first. A decimal only turns into a fraction when the fraction really equals it. Like the real calculators, surds and π are shown as decimals: √2 + √8 gives 4.242640687.

**%** divides by 100. To increase 250 by 15%, type 250 + 250 × 15 SHIFT ( (%) =, which gives 287.5. (250 + 15% gives 250.15, as on the real calculator.)

SETUP sets Norm 1 or Norm 2, a fixed number of decimal places (Fix) or significant figures (Sci), degrees, radians or gradians, and natural or linear display. **ENG** shows the answer with a power of ten that is a multiple of 3; press it again for the next one, or SHIFT ENG to go the other way. **° ' "** turns the answer into degrees, minutes and seconds and back; an answer worked out from degrees, minutes and seconds (such as 2°20'30" + 39'30") comes in them already. **SHIFT ° ' "** (FACT) writes a whole number as a product of primes.

## Statistics

1. Press MODE, 2 (STAT), then 1 for one variable or 2 for a straight line (3–8 are the curved fits).
2. Type each value and press =. Use the arrow keys to move between columns. DEL deletes a row and SHIFT DEL inserts one.
3. Press AC to go back to the calculation screen. The data stays until you leave STAT mode.
4. Press SHIFT 1 for the STAT menu: Sum, Var (n, x̄, σx, sx…), MinMax (min, Q1, median, Q3, max) and, for two variables, Reg (A, B, r, x̂, ŷ). Choose an item, then press =.

Quartiles use the method taught in Australian schools: Q1 and Q3 are the medians of the lower and upper halves, leaving the median out when there is an odd number of values. sx divides by n − 1 and σx by n. To use frequencies, turn on the FREQ column first: SHIFT MODE, ▼, 3 (STAT), 1 (ON). SETUP's second page also has Disp (a decimal point or a decimal comma in answers) and CONT (contrast: ◀ ▶, then AC).

## CASSim extras

Some things the fx-82 and SX-II do not do are in CASSim as extras. They are off until you switch them on in **CASSim ▸ Settings ▸ CASSim extras**:

- **Exact surds and π**: in MathO, answers such as 3√2, √3/2 and π/2 stay exact, as on more advanced scientific calculators (the fx-8200 AU, for example). S⇔D gives the decimal.
- **TABLE mode**: adds TABLE to the MODE menu as 4 (see Tables, below).

## Tables

Switch on the TABLE extra first, then press MODE, 4. Type f(X) (ALPHA then ) types X), press =, then enter the start, end and step, pressing = after each. Use ▲ ▼ to scroll the table and AC to change the function. A table can have up to 30 rows.

## Tutorials

The **Tutorials** panel teaches the skills students need, in the keys of the calculator you chose. On the fx-82 keys there are twelve: resetting the calculator, the frequency column, mean and standard deviation, five-number summaries, frequency tables, regression, fractions, trigonometry, percentages, memories, prime factorisation and tables (with the TABLE extra on). The SX-II, EL-531 and 10s have their own lists ([[Choosing your calculator]]).

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

Your calculator is saved in the browser as you go. **Doc ▸ New** clears the calculation (entries, memories, STAT data and the table) and keeps your settings; **Doc ▸ Reset all…** clears the settings too. **Doc ▸ Save** keeps the calculator under a name in this browser, and **Doc ▸ Open** lists what you have saved, as in the other CASSim apps. To move one to another computer, **Doc ▸ Export file…** downloads a `.cassim.json` file and **Import file…** opens one. **Doc ▸ Share link** makes a link that holds the settings, memories, STAT data and TABLE function, so a teacher can send a class a data set ready to analyse. The link never sends anything to a server. **Doc ▸ Examples** loads ready-made problems. New, Open, Import and an example ask first if the calculation has changes you have not saved.

The full-screen button at the right of the menu bar hides the bar for presenting; Esc or the button in the corner brings it back. **CASSim ▸ Appearance** offers a dark theme, a light theme and a high-contrast theme for projectors; the choice is shared with Home and the other CASSim apps. **CASSim ▸ Settings** sets the same choices as SETUP, including a decimal comma in answers, and the CASSim extras.

## Views

CASSim ▸ **Computer view**, **Tablet view** or **Handheld view** (Alt+Shift+C, T or H) chooses the layout. Computer has the menu bar and chips, with the tutorials beside the calculator when there is room; Tablet always keeps the tutorials beside it; Handheld puts them below. **CASSim ▸ Settings ▸ Start in** chooses the view CASSim opens in.

## On a phone

On a phone the view follows the way you hold it: Handheld upright, Tablet on its side (Computer view is greyed). The calculator fills the screen and its keys grow to use the height. The tutorials start hidden: **CASSim ▸ Tutorials** brings them back, below the calculator, with a ✓ in the menu, and choosing it again puts them away (on a larger screen the same menu item, or the Tutorials button, does the same). The menu bar keeps the calculator and mode chips. In the installed app, **CASSim ▸ Avoid cutout** keeps the calculator clear of the camera cutout, and choosing it again draws under it.
