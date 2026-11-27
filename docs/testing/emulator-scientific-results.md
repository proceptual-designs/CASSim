# CASSim Scientific: emulator check 1, results

Captured 2026-11-26 by Claude (computer use) on Simon's computer, from `emulator-scientific-capture.md`. Observations only; screen text is copied from the emulator. Screenshots (LCD only) are in `scientific-shots/<E>-<row>.png`, `<E>` = `FX` (Casio fx-82AU PLUS II 2nd edition), `SX` (Abacus SX-II MATRIXn), `HP` (HP 10s Virtual Calculator), `EL` (Sharp EL-531TH). The brief has rows for FX and SX only; HP and EL use rows adapted to their own keys (see their sections).

Capture method: keys clicked on the emulator's keypad; each row's LCD saved with Windows Snipping (Win+Shift+S), then copied and renamed. Screenshot pixel sizes follow the monitor scaling (about 1.32x).

---

## FX: Casio fx-82AU PLUS II 2nd edition

### Part H. Key layout

Read from the emulator window. Format: key face (SHIFT label / ALPHA label / printed under). Short labels only.

Row 1: SHIFT, ALPHA, cursor pad (REPLAY), MODE (SETUP), ON
Row 2: Abs; x³ (ALPHA `:`); [blank]; x⁻¹; x!
Row 3: fraction (SHIFT mixed-number); √■ (SHIFT ³√■); x²; x■ (SHIFT ■√■); log (SHIFT 10■); ln (SHIFT e■)
Row 4: (−) (ALPHA A); ° ' " (SHIFT FACT, ALPHA B); hyp (ALPHA C); sin (SHIFT sin⁻¹, ALPHA D); cos (SHIFT cos⁻¹, ALPHA E); tan (SHIFT tan⁻¹, ALPHA F)
Row 5: RCL (SHIFT STO); ENG (SHIFT ←); ( (SHIFT %); ) (SHIFT `,` , ALPHA X); S⇔D (ALPHA Y); M+ (SHIFT M−, ALPHA M)
Row 6: 7; 8; 9 (SHIFT CLR); DEL (SHIFT INS); AC (SHIFT OFF)
Row 7: 4; 5; 6 (SHIFT VERIFY); × (SHIFT nPr, ALPHA GCD); ÷ (SHIFT nCr, ALPHA LCM)
Row 8: 1 (SHIFT STAT); 2; 3; + (SHIFT Pol); − (SHIFT Rec)
Row 9: 0 (SHIFT Rnd); · (SHIFT Ran#, ALPHA RanInt); ×10^x (SHIFT π, ALPHA e); Ans (SHIFT DRG▶); =

### Part A. Settings, clearing and number formats

**A1.** SHIFT MODE (SETUP). Screen: `1:MthIO 2:LineIO` / `3:Deg 4:Rad` / `5:Gra 6:Fix` / `7:Sci 8:Norm` (a ▾ scroll marker at the top right). Matches CASSim. Shot: `FX-A1.png`.

**A2.** SHIFT MODE, then ▼ (SETUP page 2). Screen: `1:ab/c 2:d/c` / `3:STAT 4:Disp` / `5:◀CONT▶`. **Contradicts CASSim** (`1:STAT 2:ab/c 3:d/c`): the real order is ab/c, d/c, STAT, Disp, CONT (as the manuals give). Shot: `FX-A2.png`.

**A3.** SHIFT 9 (CLR), 3, =, AC. Screens: `Clear?` / `1:Setup 2:Memory` / `3:All`; then (after 3) `Reset All?` / `[=] :Yes` / `[AC] :Cancel`; then (after =) `Reset All` / `Press [AC] key`. Matches CASSim. Shots: `FX-A3a.png`, `FX-A3b.png`, `FX-A3c.png`.

**A4.** After the full reset (annunciators `D` and `Math` show; default is MthIO, Deg, Norm 2): 1 ÷ 200 = . Entry line `1÷200`, answer `0.005` (decimal, not a fraction). Then S⇔D: answer `1/200` (stacked). **Contradicts CASSim** (CASSim shows the stacked `1/200` first and `5×10^-3` after S⇔D): the real first answer is the decimal `0.005`, and S⇔D gives the fraction, not a ×10 form. Shots: `FX-A4.png` (answer 0.005), `FX-A4-sd.png` (after S⇔D).

**A4b.** 1 ÷ 20000000000 =. Entry `1÷20000000000`, answer `5×10^-11`. Then S⇔D: unchanged, `5×10^-11` (no fraction offered). Matches CASSim's `5×10^-11` but not its order of steps. Shots: `FX-A4b.png`, `FX-A4b-sd.png`.

**A4c.** 123456789012 =. Entry `123456789012`, answer `1.23456789×10^11`. Matches CASSim. Shot: `FX-A4c.png`.

**A4d.** SHIFT MODE 8 (Norm): the screen asks `Norm 1~2?`. Pressed 1, then 1 ÷ 200 =: entry `1÷200`, answer `5×10^-3`. Then S⇔D: `1/200` (stacked). So Norm 1 gives `5×10^-3` and Norm 2 (the post-reset default, see A4) gives `0.005`. Shots: `FX-A4d.png` (prompt), `FX-A4d-n1.png`, `FX-A4d-n1-sd.png`.

**A5.** SHIFT MODE 6 (Fix): the screen asks `Fix 0~9?`. Pressed 3. Then 2 ÷ 3 =: entry `2÷3`, answer `0.667` (FIX annunciator on). S⇔D: `2/3` (stacked). Then 5 =: entry `5`, answer `5.000`. Matches CASSim. Shots: `FX-A5.png` (prompt), `FX-A5-q.png`, `FX-A5-sd.png`, `FX-A5-5.png`.

**A5b.** (first try not completed, redone below as A5b-redo.) SHIFT MODE 7 (Sci): the screen asks `Sci 0~9?`. Shot: `FX-A5b.png`.

**A6.** After a full reset (SHIFT 9, 3, =, AC), 1234567 = : entry `1234567`, answer `1234567`. Then ENG: answer `1.234567×10^6`. ENG again: `1234.567×10^3`. (CASSim A6 gives `1.234567×10^6` for the first press and left the second open: it is `1234.567×10^3`.) Shots: `FX-A6a.png` (first ENG), `FX-A6a2.png` (second ENG).

**A6b.** 12 = then ENG: entry `12`, answer `12×10^0`. Matches CASSim. Shot: `FX-A6b.png`.

**A6c.** 12 = then SHIFT ENG (←): entry `12`, answer `0.012×10^3`. Matches CASSim. Shot: `FX-A6c.png`.

**A7.** After a reset, SHIFT MODE 1 (MthIO): the screen asks `Result Format?` / `1:MathO 2:LineO` (a title line CASSim's menu does not have; the menu itself matches). Then 1 ÷ 3 = (after leaving the menu with AC, nothing chosen): entry `1÷3` (Math annunciator on), answer `0.3333333333`. So after a reset the input is natural (MathI) but the **output is decimal (LineO)**: **contradicts CASSim's MathO default and agrees with the manuals** (MathI/LineO). This is the result SDD-14 section 8 waits for (row A7). Shots: `FX-A7.png`, `FX-A7-third.png`.

**A5b-redo.** SHIFT MODE 7 (Sci), 4, then 2 ÷ 3 =: entry `2÷3`, answer `6.667×10^-1` (SCI annunciator on). Then S⇔D: `2/3` (stacked). Matches CASSim for the decimal. Shots: `FX-A5b-q.png`, `FX-A5b-sd.png`.

---

### Part B. Natural display, exact answers and functions

Reset first (SHIFT 9, 3, =, AC), then SHIFT MODE 1 1 (MathO) so answers are natural (the post-reset default is LineO, see A7), COMP, Deg.

**B1.** fraction 1 ▼ 3 ▶ + fraction 1 ▼ 4 = : entry `1/3 + 1/4` (stacked), answer `7/12` (stacked); S⇔D: `0.5833333333`. Matches CASSim. Shots: `FX-B1.png`, `FX-B1-sd.png`.

**B2.** SHIFT fraction (mixed) 2 ▶ 1 ▼ 3 ▶ + fraction 5 ▼ 6 = : entry `2 1/3 + 5/6` (stacked, mixed), answer `19/6` (stacked); SHIFT S⇔D: `3 1/6` (mixed, stacked). Matches CASSim. Shots: `FX-B2.png`, `FX-B2-sd.png`.

**Surds are not given (B3, B3b, B4): contradicts CASSim.** With MathO set explicitly (SHIFT MODE 1 1; the Result Format menu was reopened and 1 pressed again before re-testing) this emulator answers irrational results as decimals, and S⇔D does not change them. Checked also with `√8` alone: answer `2.828427125`, S⇔D leaves it.

**B3.** √2 ▶ + √8 = : entry `√2+√8` (radicals), answer `4.242640687`. CASSim says `3√2`. Shot: `FX-B3.png`.

**B3b.** √12 ▶ ÷ 3 = : entry `√12÷3`, answer `1.154700538`. CASSim says `2√3/3`. Shot: `FX-B3b.png`.

**B4.** sin 45 ) = : entry `sin(45)`, answer `0.7071067812` (CASSim: `√2/2`). cos 30 ) = : `0.8660254038` (CASSim: `√3/2`). sin 50 ) = : `0.7660444431` (matches CASSim). Shots: `FX-B4a.png`, `FX-B4b.png`, `FX-B4c.png`.

**B5.** 0.25 = : entry `0.25`, answer `1/4` (stacked); S⇔D: `0.25`. Matches CASSim. Shots: `FX-B5.png`, `FX-B5-sd.png`.

**B5b.** . 2 5 = (no leading 0): entry `.25`, answer `1/4` (stacked). Matches CASSim. Shot: `FX-B5b.png`.

**B5c.** 0.123456789 = : entry `0.123456789`, answer `0.123456789`; S⇔D: `0.123456789` (unchanged). Matches CASSim. Shots: `FX-B5c.png`, `FX-B5c-sd.png`.

**B6.** 12 ° ' " 34 ° ' " 56 ° ' " = : entry `12°34'56"`, answer `12°34'56"` (stays in degrees, minutes, seconds). **Contradicts CASSim** (`12.58222222`, a decimal). Shot: `FX-B6.png`.

**B6b.** 12.582 = then ° ' " : entry `12.582`, answer `12°34'55.2"`. Matches CASSim. Shot: `FX-B6b.png`.

**B7.** 1050 = then SHIFT ° ' " (FACT): entry `1050`, answer `2×3×5²×7`. 360 = FACT: `2³×3²×5`. Matches CASSim. Shots: `FX-B7a.png`, `FX-B7b.png`.

**B8.** Abs (−) 3 = : entry `|-3|`, answer `3`. Matches CASSim. Shot: `FX-B8.png`.

**B8b.** No key for log with a base is printed on the keypad (log has only `10■` on SHIFT; no `log■□` legend anywhere, ALPHA included). Not found; see part H.

**B9.** 5 x! = : `5!` → `120`. 10 SHIFT ÷ (nCr) 3 = : `10C3` → `120`. 10 SHIFT × (nPr) 3 = : `10P3` → `720`. Matches CASSim. Shots: `FX-B9a.png`, `FX-B9b.png`, `FX-B9c.png`.

**B10.** 250 + 15 SHIFT ( (%) = : entry `250+15%`, answer `5003/20` (stacked); S⇔D: `250.15`. **Contradicts CASSim** (`575/2`, then `287.5`): on this emulator the % key is just ÷100, so `250+15%` is 250 + 0.15, not 250 plus 15% of 250. Shots: `FX-B10.png`, `FX-B10-sd.png`.

**B10b.** 250 × 15 % = : entry `250×15%`, answer `75/2` (stacked). Matches CASSim. Shot: `FX-B10b.png`. (So `×15%` takes 15% of 250, but `250+15%` in B10 adds 0.15: the % key is ÷100 in both; the answer `75/2` is 250 × 0.15.)

**B11.** After B10b, 1 + Ans = : entry `1+Ans`, answer `77/2` (stacked). Matches CASSim. SHIFT Ans (DRG▶): the screen shows `1:°` `2:ʳ` / `3:ᵍ`. Matches CASSim. Shots: `FX-B11a.png`, `FX-B11b.png`.

**B12b. hyp on the fx-82AU 2nd edition opens a menu, it is not a prefix.** Pressing hyp shows `1:sinh 2:cosh` / `3:tanh 4:sinh⁻¹` / `5:cosh⁻¹ 6:tanh⁻¹`. Pressing 1 puts `sinh(` on the entry line; 1 ) = : entry `sinh(1)`, answer `1.175201194`. (The brief's `hyp sin 1 ) =` assumed a prefix key; here it is `hyp 1 1 ) =`.) **Contradicts the brief's description, and Simon wants the toggle behaviour instead (see `emulator-scientific-requests.md`).** Shots: `FX-B12b-menu.png`, `FX-B12b.png`.


### FX Part C (statistics), partial, run in this order

Data entered in MODE 2 (STAT) 1-VAR: 12, 15, 18, 22, 25, each followed by `=`. Screens: scientific-shots/FX-C0-mode-menu, FX-C1-type-menu, FX-C2-empty-table, FX-C2b-data.

- C0 MODE menu: `1:COMP 2:STAT / 3:VERIF` (`MODE` page shows the three modes; there is no TABLE or BASE-N on this fx-82AU page).
- C1 STAT type menu: `1:1-VAR 2:A+BX 3:_+CX² 4:ln X 5:e^X 6:A·B^X 7:A·X^B 8:1/X`.
- C2 table: single column `X`; rows show 12, 15, 18, 22, 25 (three rows visible at once).
- C2c SHIFT 1 inside the table: `1:Type 2:Data 3:Edit`. From the calculation screen (after AC): `1:Type 2:Data 3:Sum 4:Var 5:MinMax` (FX-C3-statmenu-calc). Different menus depending on where you are.
- C3 Sum menu: `1:Σx² 2:Σx`. Var menu: `1:n 2:x̄ 3:σx 4:sx`. MinMax menu: `1:minX 2:maxX 3:Q1 4:med 5:Q3`.
- C4 results (screen shows the label on line 1, value on line 2, right aligned): n = 5; x̄ = 18.4; σx = 4.673328578; sx = 5.224940191.
- C5 results: Σx = 92; Σx² = 1802; Q1 = 13.5; med = 18; Q3 = 23.5.
- Observation: quartiles use the median-of-halves method (n=5 odd: Q1 = mean of 12 and 15, Q3 = mean of 22 and 25, the median excluded).
- Not yet captured: minX/maxX, 2-variable types (A+BX etc.), regression coefficients, data clearing, FREQ, DEL/INS (C6 to C8).
- C5 (cont.) minX = 12; maxX = 25 (FX-C5-minX, FX-C5-maxX).

### FX C6 two-variable regression (A+BX)

- Reach it by MODE 2 then 2 (A+BX). Table has columns X and Y; Return moves down, the Right arrow moves to the Y column.
- SHIFT 1 on the calculation screen (2-var): `1:Type 2:Data 3:Sum 4:Var 5:Reg 6:MinMax` (FX-C6-2var-shift1-menu). Reg menu: `1:A 2:B 3:r 4:x̂ 5:ŷ` (FX-C6-reg-menu).
- Data x = 1, 2, 3, 4; y = 2, 4, 5, 8 (FX-C6b-2var-table-good): A = 0; B = 1.9; r = 0.981155781.
- Superseded run (FX-C6-reg-A-0, -B-0, -r-MathERROR): my first entry left every Y at 0 by mistake. It shows A = 0, B = 0 and r gives `Math ERROR` with screen text `[AC]:Cancel [◀][▶]:Goto`. These are genuine emulator behaviours for all-zero Y, not for the data above.
- Not captured: x̂ and ŷ prediction, quadratic and exponential regressions, data clearing, FREQ, DEL/INS (rest of C).

## FX Part D (TABLE)

- D: not present on this emulator. The MODE menu lists only `1:COMP 2:STAT 3:VERIF` (FX-C0-mode-menu); the Down key and the arrow pad change nothing. No TABLE and no Range ERROR rows could be run.

## FX Part E (VERIFY)

The brief says MODE 4 / SHIFT 6; on this emulator VERIFY is **MODE 3**, not MODE 4.

- E0 (FX-E1-verif-entry): after MODE 3 the screen is blank with the words `TRUE/FALSE` at the lower right and the Math annunciator.
- E0b (FX-E2-verif-2plus3-return): typing `2+3` then `=` (Return) with no relation sign shows `2+3=0` and `FALSE`, so a bare expression is compared with 0. I did not find a key for the "=" sign other than the SHIFT 6 menu; typing `=` from the keyboard does nothing.
- E1 (FX-E1-verif-relation-menu), SHIFT 6: `1:= 2:≠ / 3:> 4:< / 5:≥ 6:≤`. The order is `= ≠ > < ≥ ≤` (the SX-II order in the brief, not the fx-82 order `> ≥ < ≤`).
- E2: `4 SHIFT 6 1 √16 =` shows `4=√16` and `TRUE` (FX-E2a-4eq-sqrt16); `π > 3` shows `π>3`, `TRUE` (FX-E2b-pi-gt-3); `1+2 SHIFT 6 4 3 =` (1+2<3) shows `1+2<3`, `FALSE` (FX-E2c-1p2-lt-3). The word is on line 2, right aligned; line 1 holds the statement. The annunciators `Math` and `▲` show.

## FX Part F (memories), partial

- F1 `5 SHIFT RCL(STO) (−)` then `=`: after SHIFT RCL the annunciator `STO` shows; the (−) key is variable A. Line 1 reads `5→A`, line 2 `5` (FX-F1-sto-5-to-A).
- F2 `RCL (−)` shows the annunciator `RCL` first, then line 1 `A`, line 2 `5` straight away, with no `=` needed. Typing `+10 =` after that gives `Ans+10` / `15`: an operator pressed on a result screen inserts `Ans` (PreAns behaviour) (FX-F2a-ans-plus-10, FX-F2b-ans-plus-10-after-rcl). Note: my first attempt was the same screen, because the AC cleared the recall.
- F3 `7 M+` shows `7M+` / `7` and the `M` annunciator (top left) comes on (FX-F3-7-Mplus). `RCL M+` (which is the M recall) shows `M` / `7` (FX-F3b-recall-M).
- Not captured: M−, SHIFT 9 (CLR) Memory, Ans after errors, STO on other variables, STO → fractions.

## FX Part G (errors, leaving, history), partial

- G1 `1 ÷ 0 =`: screen `Math ERROR` on line 1, then `[AC] :Cancel` and `[◀][▶]:Goto` below (FX-G1-1div0-MathERROR).
- G2 `2 + + =` and G3 `2 + =`: both show `Syntax ERROR` with the same two help lines (FX-G2, FX-G3).
- G4 ◀ after an error (G3): the expression returns to the edit line as `2+` with the cursor after it (FX-G4-left-after-error). I did not confirm where the cursor sits relative to the fault.
- G5 AC then ▲: replays the last good calculation, `Ans+10` / `15`; the errored lines were not kept in the history (FX-G5-up-history).
- Not captured: Stack ERROR, Arg ERROR, overflow, the exact ▲ history depth, ON key behaviour.

## FX unique features (so far)

- U1 Pol(: `SHIFT +` gives `Pol(`; `Pol(1,1)` shows line 1 `Pol(1,1)` and line 2 `r=1.414213562,θ=` with a ▶ marker, i.e. both results sit on one scrolling line; press ▶ to scroll. Fully scrolled: `θ=45` (Deg mode) (FX-U1-Pol-1-1, FX-U1b-Pol-scrolled, FX-U1c-Pol-theta).
- U2 Rec(: `SHIFT −` gives `Rec(`; `Rec(2,60)` shows `X=1,Y=1.7320508` then scrolls to `Y=1.732050808` (FX-U2-Rec-2-60, FX-U2b-Rec-scrolled). The comma is SHIFT `)`.
- Base-N conversion: not present on this fx-82AU (MODE menu has only COMP, STAT, VERIF).
- Not yet run: GCD/LCM, Ran#, RanInt#, Rnd(, CALC, DMS entry, ENG key detail, S⇔D variants.
- U3 Ran#: `SHIFT .` gives `Ran#`; `=` shows line 2 as a **fraction** `581/1000` in the default Math display (one run; random value) (FX-U3-Ran-hash). That is notable for CASSim: random numbers appear as thousandths fractions, not decimals.
- `SHIFT` + the Abs key did nothing visible (blank line 1); the Rnd key location was not found, so Rnd( is not captured.

## SX (ABACUS SX-II MATRIXn)

Window notes: key names on this emulator are 2nd (SHIFT), ALPHA, F↔D (S⇔D), d/c, 2nd A b/c, 2nd SET UP. After `2nd CLR 3 =` the screen shows `Reset All` / `Press [AC] key`; the calculator then needed ON before it showed anything (the display was blank after pressing AC).

### SX Part A (partial, in order run)

- A3 (SX-A0-clear-menu, SX-A0b-reset-confirm, SX-A0c-reset-done): `Clear?` / `1:Setup 2:Memory` / `3:All`; then `Reset All?` / `[=] :Yes` / `[AC] :Cancel`; then `Reset All` / `Press [AC] key`. Same wording as the fx-82 apart from spacing (SX shows `[=] :Yes`).
- After the reset the display shows the `Math` annunciator (Math input) and a blinking cursor.
- A1 `2nd MODE` (SET UP), page 1 (SX-A1-setup-page1): `1:MthIO 2:LineIO` / `3:Deg 4:Rad` / `5:Gra 6:Fix` / `7:Sci 8:Norm`, a `▼` marker at top right.
- A2 ▼, page 2 (SX-A2-setup-page2): `1:ab/c 2:d/c` / `3:STAT 4:Disp` / `5:◀CONT▶`, a `▲` marker at top right. The order is `ab/c, d/c, STAT, Disp, CONT`, as the manual lists it (CASSim has `STAT, ab/c, d/c`: contradicted).
- **Method warning (found late):** the Windows snip hotkey (Win+Shift+S) sends a Shift key press to the SX-II emulator when it has keyboard focus, and that emulator treats Shift as `2nd`. So after a snip a `2nd` annunciator can be pending and the next key is read as 2nd+key (2nd+AC is OFF, which is why the display kept going blank). Every SX reading taken straight after a snip, before this was found, is suspect and is being redone. To avoid it I now click another window's title bar before the hotkey, then click the SX-II body once (that click is swallowed) before the next key.
- A4 and A4b below are redone with that fix; any row not marked "redone" came from before it and is not trusted.
- A4 (redone, clicked keys `1 ÷ 200 =`): line 1 `1÷200`, line 2 `0.005` (decimal first) (SX-A4-1div200). Then `F↔D`: line 2 becomes `1/200` (stacked, 1 over 200) (SX-A4-1div200-fd). After a reset (Math annunciator on) the first answer is the decimal and F↔D gives the fraction, the opposite order to CASSim's fx-82 row.
- A4b (redone, `1 ÷ 20000000000 =`): line 1 `1÷20000000000`, line 2 `5×10` with a two-digit superscript exponent `11`; a minus sign is not legible at this size in the screenshot (the value must be 5×10^-11) (SX-A4b-1div20e9). F↔D left the display unchanged (clicked once, display compared before and after).
- A4c `123456789012 =`: line 1 `123456789012`, line 2 `1.23456789×10` with superscript exponent `11` (SX-A4c-123456789012). Shows 9 significant digits (CASSim says `1.23456789×10^11`: matches).
- A4d `2nd MODE 8` (Norm): the screen is one line, `Norm 1~2?` (SX-A4d-norm-prompt).
- A4d (cont.): after pressing `1` (Norm 1), `1 ÷ 200 =` shows line 2 `5×10` with a one-digit superscript `3` (a minus sign not legible), not `0.005` (SX-A4d-norm1-1div200). The default after a reset is therefore **Norm 2** (it showed `0.005`).
- A5 `2nd MODE 6` (Fix): prompt line `Fix 0~9?` (SX-A5-fix-prompt). Then `3`; `2 ÷ 3 =` shows `2÷3` / `0.667` with the `FIX` annunciator (SX-A5-fix3-2div3); `F↔D` gives `2/3` stacked (SX-A5-fix3-fd). Same order as A4: decimal first.
- A5 continued (Fix 3, integer entry): entering a single digit then `=` shows line 1 `6`, line 2 `6.000` with `FIX` annunciator (SX-A5-fix3-integer). Note: the digit on screen is 6, not the 5 planned; recorded as shown.
- A5b (after switching to Sci): same entry shows line 2 `6.000×10` with a small superscript exponent, `SCI` annunciator (SX-A5b-sci-integer). Exponent sign/value too small to read in the LCD image; to be confirmed with a larger capture.
- A5b (Sci 4): `2÷3 =` shows line 1 `2÷3`, line 2 `6.667×10` with superscript exponent (sign not legible at LCD size, expected -1), `SCI` annunciator (SX-A5b-sci4-2div3). Decimal first, as with Fix/Norm.
- Method note: an earlier `2÷3` attempt with a leftover `5` in the entry line gave `5 2÷3` = `3.333×10^0` (implicit multiplication of 5 and 2÷3); not recorded as evidence of 2÷3.
- A5b F↔D (Sci 4 still active): `2÷3` shows `2/3` stacked, `SCI` annunciator stays (SX-A5b-sci4-fd).
- A6 ENG key (Sci 4 active, entry `12345 =`): first ENG press: line 2 `12.35×10` superscript `3` (SX-A6-eng-1). Second ENG press: line 2 `12350×10` superscript `0` (SX-A6-eng-2). (Observation only; the exponent in the second capture is small and read as 0.)
- A7 SET UP page 1 shows `1:MthIO 2:LineIO / 3:Deg 4:Rad / 5:Gra 6:Fix / 7:Sci 8:Norm` (maker's menu text, do not reuse). Pressing `2` (LineIO) clears the screen and the `Math` annunciator disappears (only `D` and `SCI` remain). In LineIO with Sci still active, `1÷3 =` shows line 1 `1÷3`, line 2 `3.333×10` with superscript (sign not legible, expected -1) (SX-A7-lineio-1div3). No stacked fraction is offered in LineIO from this capture (F↔D not pressed).
- A7 MthIO: choosing `1:MthIO` from SET UP page 1 shows a prompt `Result Format?` with `1:MathO 2:LineO` (as read from the LCD; maker's text, do not reuse) (no separate screenshot; seen in a zoom only). After choosing 1, `1÷3 =` shows line 1 `1÷3`, line 2 `1/3` stacked (not decimal) with `Math` annunciator, even though SCI was active (SX-A7-mathio-1div3). Unlike A4/A5, the stacked fraction is the default answer when the result format is MathO.
- State note: the annunciators in this capture include `R` (Rad) because an earlier click selected Rad by mistake; recorded as shown. Full reset before Part B.

## SX Part B (after full reset: Reset All via 2nd CLR (above 9) -> 3:All -> =, then AC; screen shows `Math` annunciator, default MthIO/Norm)
- B1 attempt 1 (keys wrong, kept as an observation of nested entry): d/c 1 ▼ 3, then `▶` did not leave the denominator, so `+ d/c 1 ▼ 4` was entered inside it: screen shows 1 over (3 + 1/4), answer `4/13` stacked; F↔D gives `0.3076923077` (SX-B1x-nested-4over13-fd). Result formatting: 10 significant digits, same as the fx-82 decimal.
- B1 (corrected; d/c key at the fraction key, one ▶ press leaves the denominator): `1/3 + 1/4 =` shows the stacked entry `1/3 + 1/4` and answer `7/12` stacked, `Math` annunciator (SX-B1-third-plus-quarter); F↔D gives `0.5833333333` (SX-B1-third-plus-quarter-fd). The d/c key opens an empty stacked fraction with the cursor in the numerator; ▼ moves to the denominator; ▶ leaves the fraction. (Note: the brief's B1 used 1/3 + 1/4, matches.)
- B2: `2nd a b/c` (2nd + d/c) entry `2 ▶ 1 ▼ 3 ▶ + d/c 5 ▼ 6 =` shows entry as mixed number `2 1/3 + 5/6` and answer `19/6` stacked improper (SX-B2-mixed-sum). F↔D gives `3.166666667` (SX-B2-mixed-sum-fd). Mixed-number answer toggle tested next.
- B2 mixed-number answer: with `16÷6` (typed with ÷) answer showing decimal `2.666666667`, then `2nd F↔D` gives `2 2/3` (mixed number, stacked) (SX-B2-2nd-fd-mixed). So the mixed form is reached with 2nd F↔D on the SX-II (the brief's SHIFT S⇔D). Pressing `2nd d/c` on an answer screen instead opens an empty mixed-fraction entry template (`□ □/□`) (SX-B2-2nd-dc-template).
- B2b default after Reset All: `16÷6 =` (typed with the ÷ key, not the fraction template) shows line 2 `2.666666667` (decimal), Math annunciator (SX-B2b-16div6-default). Contrast: A7 after choosing MthIO showed `1÷3` as stacked `1/3`, and entries typed with the d/c template give stacked answers (B1, B2). Order of results for ÷-typed input after Reset All is decimal first.
- B3: `√2 ▶ + √8 =` (√ key opens a radical template; ▶ leaves it) shows `√2+√8` and answer `4.242640687` (decimal, no surd form) (SX-B3-sqrt2-plus-sqrt8).
- B3b: `√12 ▶ ÷ 3 =` shows `√12÷3` and answer `1.154700538` (decimal, no surd form) (SX-B3b-sqrt12-div3). F↔D leaves it unchanged (decimal) (SX-B3b-sqrt12-div3-fd). The SX-II gives no exact surd answers.
- B4 (Deg, default): `sin(45)` (the key writes `sin(`; `)` closed) `=` -> `0.7071067812` (SX-B4-sin45); `cos(30)` -> `0.8660254038` (SX-B4-cos30); `sin(50)` -> `0.7660444431` (SX-B4-sin50). Decimals only, no exact `√2/2` or `√3/2`.
- B5: `0.25 =` shows answer `0.25` (decimal first, not 1/4) (SX-B5-0p25); F↔D gives `1/4` stacked (SX-B5-0p25-fd). B5b: `.25 =` (no leading 0) shows entry `.25` and answer `0.25` (SX-B5b-p25). Decimal input stays decimal until F↔D (compare CASSim expectation of `1/4` first: this emulator differs).
- B5c: `0.123456789 =` shows answer `0.123456789` (SX-B5c-0p123456789); F↔D leaves it `0.123456789` (SX-B5c-0p123456789-fd).
- B6: `12 DMS 34 DMS 56 DMS =` (DMS key pressed after each of the three numbers) shows the entry as `12°34°56°` (the same ° symbol for all three presses) and the answer line `12°34'56"` (a DMS answer, not the decimal `12.58222222` the brief expects) (SX-B6-dms-entry).
- B6b: `12.582 =` shows `12.582`; pressing the DMS key on the answer converts it to `12°34'55.2"` (SX-B6b-12p582-dms). So the DMS key both enters ° ' " and converts a decimal answer to DMS.
- B7: `1050 =` then `2nd DMS` (FACT) shows `2×3×5²×7` (SX-B7-fact-1050); `360 =` then FACT shows `2³×3²×5` (SX-B7-fact-360). Matches the brief.
- B8 attempt: `Abs (−) 3 )` `=` gives `Syntax ERROR` with a two-line menu `[AC]:Cancel / [◀][▶]:Goto` (maker's text, do not reuse) (SX-B8-abs-syntax-error). Cause: the Abs key opens its own bars template, so my extra `)` was a stray bracket; retry without `)` next.
- B9: `5 x! =` -> `120` (SX-B9-5fact); `10 nCr 3 =` (2nd ÷) shows entry `10C3` and answer `120` (SX-B9-10nCr3).
- B8 retry: `Abs (−) 3 =` shows `|-3|` and answer `3` (SX-B8b-abs-neg3).
- B9: `10 nPr 3 =` (2nd ×) shows entry `10P3` and answer `720` (SX-B9-10nPr3).
- B10: `250 + 15 %` (2nd + the `(` key, which carries the % legend) `=` shows entry `250+15%` and answer `250.15` (SX-B10-250plus15pct); F↔D gives `5003/20` stacked (SX-B10-250plus15pct-fd). The % acts as plain ÷100 (15% = 0.15), unlike the fx-82 expectation of 575/2 (add-on percent).
- B10b: `250 × 15 %` shows `250×15%` and answer `37.5` (SX-B10b-250x15pct).
- B11: after B10b (`37.5`), `1 + Ans =` shows `1+Ans` and answer `38.5` (SX-B11-1plusAns). `2nd Ans` (DRG▸) shows `1:°  2:ʳ  3:ᵍ` (SX-B11-drg-menu), matching the brief's menu.
- B12: HYP key opens a six-item menu `1:sinh 2:cosh / 3:tanh 4:sinh⁻¹ / 5:cosh⁻¹ 6:tanh⁻¹` (SX-B12-hyp-menu). `HYP 2` (cosh) `1.5 ) + 2 =` shows `cosh(1.5)+2` and `4.352409615` (SX-B12-cosh1p5-plus2). `HYP 4 7 =` shows `sinh⁻¹(7` (the closing bracket is not auto-added, not typed) and `2.644120761` (SX-B12-asinh7). Both values match the brief.
- Design request (Simon): CASSim hyp should be a toggle that relabels the trig keys to their h forms (sin->sinh etc.); on the SX-II (HYP menu, no toggle) add the toggle as well. See emulator-scientific-requests.md.

## SX unique features seen in Part B
- Surds: none (decimal only). Percent: plain ÷100. Fraction templates: d/c and 2nd d/c (mixed). Mixed answer: 2nd F↔D. FACT: 2nd DMS. DMS: DMS key enters and converts. nCr/nPr: 2nd ÷ / 2nd ×. Abs: its own key with bars template. HYP: six-item menu.

## SX Part C (statistics) and Part D
- C0/D: MODE shows `1:COMP 2:STAT / 3:VERIF` (SX-C0-mode-menu). No TABLE mode on the SX-II (Part D: not applicable; fx-82 only per brief).
- C1: MODE 2 shows the type menu `1:1-VAR 2:A+BX / 3:_+CX² 4:ln X / 5:e^X 6:A·B^X / 7:A·X^B 8:1/X` (SX-C1-type-menu).
- C2: choosing 1 (1-VAR) opens an empty table with an `X` column and row numbers, `STAT` annunciator (SX-C2-empty-table). After entering 12, 15, 18, 22, 25 (each followed by `=`) the table scrolls, rows 4–6 show `22`, `25` and an empty row (SX-C2b-data).
- C2c: AC then `2nd STATVAR` (STAT) shows `1:Type 2:Data / 3:Sum 4:Var / 5:MinMax` (SX-C2c-stat-menu), same as the fx-82 calc-screen menu.
- C2b (Var, data 12 15 18 22 25): `2nd STATVAR 4` shows `1:n 2:x̄ / 3:σx 4:sx` (SX-C2d-var-menu). Values (line 1 label, line 2 value, right aligned, `STAT` annunciator): x̄ `18.4` (SX-C2e-xbar); σx `4.673328578` (SX-C2f-sigmax); sx `5.224940191` (SX-C2g-sx); n `5` (SX-C2h-n). All match the fx-82 values.
- C5 (data 12 15 18 22 25): `2nd STATVAR 5` shows `1:minX 2:maxX / 3:Q1 4:med / 5:Q3` (SX-C5-minmax-menu). Q1 `13.5` (SX-C5-Q1); med `18` (SX-C5-med); Q3 `23.5` (SX-C5-Q3). (Brief rows C3/C3b use different data and were not run as specified; these values come from the C2 data.)
- C5b (1-VAR Sum): `2nd STATVAR 3` shows only `1:Σx²  2:Σx` (SX-C5-sum-menu); Σx = `92` (SX-C5-sumx).
- C4/C6 (A+BX): MODE 2 2 opens a table with `X` and `Y` columns (opening screen not snipped; zoom only). Data entered: X 1 2 3 4 5 (each `=`), then ▶ and ▲ x5 to Y row 1, Y 2 4 5 4 5 (each `=`) (SX-C6-2var-table shows the bottom rows). `2nd STATVAR` shows `1:Type 2:Data / 3:Sum 4:Var / 5:Reg 6:MinMax` (SX-C6-stat-menu), matches the brief.
- C6 Reg menu (`2nd STATVAR 5`): `1:A 2:B / 3:r 4:x̂ / 5:ŷ` (SX-C6-reg-menu). Values for X 1–5, Y 2 4 5 4 5: A `2.2` (SX-C6-reg-A); B `0.6` (SX-C6-reg-B); r `0.7745966692` (SX-C6-reg-r).
- C4b Sum menu for A+BX (`2nd STATVAR 3`): `1:Σx² 2:Σx / 3:Σy² 4:Σy / 5:Σxy 6:Σx³ / 7:Σx²y 8:Σx⁴` (SX-C4b-sum-menu). So the SX-II DOES have Σx³, Σx²y and Σx⁴ (answers the brief's question; CASSim has none of them).
- C4b Var menu for A+BX (`2nd STATVAR 4`): `1:n 2:x̄ / 3:σx 4:sx / 5:ȳ 6:σy / 7:sy` (SX-C4b-var-menu).

## SX Part E (VERIFY)
- E1: MODE 3 (VERIF) opens an entry screen with `Math` annunciator and the placeholder text `TRUE/FALSE` right aligned on line 2 (SX-E1-verif-entry). `2nd 6` (VERIFY) shows `1:= 2:≠ / 3:> 4:< / 5:≥ 6:≤` (SX-E1-verif-relation-menu); matches the brief's SX-II order (`<` is item 4).
- E2: `π > 3 =` shows `π>3` and `TRUE` right aligned (SX-E2b-pi-gt-3). `1+2 < 3 =` shows `1+2<3` and `FALSE` (SX-E2c-1p2-lt-3).
- E2 slip: `5 = √16 =` (I pressed 5 instead of 4) shows `5=√16` and `FALSE` (SX-E2x-5eq-sqrt16); the correct 4 = √16 is retaken next.
- E2 retake: `4 = √16 =` shows `4=√16` and `TRUE` (SX-E2a-4eq-sqrt16). All three E2 answers use the exact words `TRUE` / `FALSE`, right aligned on line 2.

## SX Part F (memories)
- F1: `36 =`, `2nd RCL` (STO), `(−)` (A) shows line 1 `Ans→A`, line 2 `36` (SX-F1-sto-A); `=` stores it. AC, `2 ALPHA (−) =` shows `2A` and `72` (SX-F1b-2A-72). Matches the brief. (First digit click after a focus change was swallowed, so `36` was entered as shown.)
- F2: `0 =`, `2nd RCL` (STO) shows `M STO` annunciators; pressing the `M+` key right after STO shows `Ans→M` / `0` (SX-F2-sto-M). (Pressing ALPHA then M+ instead types the variable `M` and drops the STO prompt.) `5 M+` shows `5M+` with `5` on line 2 and the `M` annunciator; `3 M+` shows `3M+` with `3` on line 2 (zoom only). `RCL M+` shows `M` on line 1 and `8` on line 2 immediately, before any `=` (SX-F2b-rcl-M); `=` leaves it `M` / `8` (SX-F2c-rcl-M-equals). Memory total 8 matches the brief.

## SX Part G (errors, leaving)
- G1: `1 ÷ 0 =` shows `Math ERROR` on line 1 and a two-line prompt `[AC] :Cancel` / `[◀][▶] :Goto` (maker's text, do not reuse) (SX-G1-div0-math-error). The annunciators `M` and `Math` stay on.
- G3: pressing ◀ after the error returns to the entry `1÷0` with the cursor on the `0` (the error position) (SX-G3-left-after-error).
- G2: `2 + × 3 =` shows `Syntax ERROR` with the same `[AC] :Cancel` / `[◀][▶] :Goto` prompt (SX-G2-2plus-times-3).
- G4: `123 + 456 =` shows `123+456` / `579` (SX-G4-123plus456). First ▲ press: the screen is unchanged but the annunciator at the top right changes from `▲` to `▼▲` (history now reachable) (SX-G4-up1; the first click on the pad after a focus change may have been swallowed by the emulator, so this is not conclusive). Second ▲: the earlier calculation is shown, line 1 `M`, line 2 `8` (the RCL M recall from part F) (SX-G4-up2-earlier). ◀: the entry `M` returns with a block cursor (edit mode) (SX-G4-left-edit). Matches the brief's behaviour (history, ◀ edits).
- Method slip (G4 first attempt): the first G4 keys went in after a leftover state; the screen stayed on `M`/`8`. Redone from a clean AC; not used as evidence.

## SX unique features
- U1 Polar from rectangular: `2nd +` (legend R→P) types `Pol(`; `Pol(1,1)` (comma = 2nd `)` key) `=` shows entry `Pol(1,1)` and line 2 `r=1.414213562,θ▶` (SX-U1-Pol-1-1). The result is one line that scrolls: ▶ shows `◀1.414213562,θ=▶` (SX-U1b-Pol-scrolled); more ▶ presses are needed to reach the θ value.
- U2 Rectangular from polar: `2nd −` (legend P→R) types `Rec(`; `Rec(2,60)` shows line 2 `X=1,Y=1.7320508▶` (SX-U2-Rec-2-60); ▶ scrolls to `◀1,Y=1.732050808` (SX-U2b-Rec-scrolled). Result is a single scrolling line (not stacked).
- U1 θ: after more ▶ presses the Pol(1,1) result line reads `◀414213562,θ=45` (SX-U1c-Pol-theta): θ is 45 in Deg mode.
- U3 GCD: `ALPHA ×` (legend GCD) types `GCD(`; `GCD(12,18) =` shows `6` (SX-U3-GCD-12-18).
- U4 LCM: `ALPHA ÷` (legend LCM) types `LCM(`. Slip: I entered `LCM(4,0)` (wrong digit) and it shows `0` (SX-U4x-LCM-4-0); LCM(4,6) is retaken next.
- U4 retake: `LCM(4,6) =` shows `12` (SX-U4-LCM-4-6).
- U5 Ran#: `2nd .` types `Ran#`; `=` shows a 3-decimal number (`0.762` this time, random) (SX-U5-Ran-hash). Result is a decimal, not a fraction.
- U6 RanInt#: `ALPHA .` types `RanInt#(` and waits for arguments (SX-U6-RanInt-hash).
- U7 Rnd: `2nd 0` (legend RND) types `Rnd(` (SX-U7-Rnd-paren). All three are present on the SX-II (the fx-82 2nd edition showed Ran# only; Rnd( was not found there).

## SX Part H (key layout, read from the emulator face; legends as printed, 2nd = orange/yellow, ALPHA = blue)
Top: `SET UP` over MODE (2nd), `MODE`, `ON`, `2nd` (yellow), `ALPHA` (blue), `Abs`, `x!`, direction pad (▲▼◀▶ with centre).
Row 1: `ENG` (2nd `◂ENG`), `x⁻¹`, `log` (2nd `10ˣ`), `ln` (2nd `eˣ`), `DEL` (2nd `INS`).
Row 2: `(−)` (ALPHA `A`), `DMS` (2nd `FACT`, ALPHA `B`), `HYP` (ALPHA `C`), `x²` (2nd `:` not read), `x³` (2nd `³√`? legend read as `³√`).
Row 3: `SIN` (2nd `sin⁻¹`, ALPHA `D`), `COS` (`cos⁻¹`, `E`), `TAN` (`tan⁻¹`, `F`), `x^y` (2nd `ʸ√`), `√` (2nd `³√` legend printed above).
Row 4: `RCL` (2nd `STO`), `(` (2nd `%`), `)` (2nd `,`, ALPHA `X`), `F↔D` (2nd `A b/c ◂▸ d/c` mixed toggle, ALPHA `Y`), `d/c` (2nd `A b/c`).
Row 5: `7`, `8`, `9` (2nd `CLR`), `÷` (2nd `nCr`, ALPHA `LCM`), `AC` (red, 2nd `OFF`).
Row 6: `4`, `5`, `6` (2nd `VERIFY` bracket), `×` (2nd `nPr`, ALPHA `GCD`), `M+` (2nd `M−`, ALPHA `M`).
Row 7: `1` (2nd `STATVAR`), `2`, `3`, `−` (2nd `P→R`), `ANS` (2nd `DRG▸`).
Row 8: `0` (2nd `RND`), `·` (2nd `RAND`, ALPHA `RANDI`), `×10ˣ` (2nd `π`, ALPHA `e`), `+` (2nd `R→P`), `=`.
Notes (observed, not from the printed legend): SET UP is 2nd MODE; CLR is 2nd 9; the `(` key's 2nd is `%` (as used in B10); `2nd F↔D` toggled to a mixed number (B2). The two legends I could not read confidently are marked above.

## HP (HP 10s Scientific Calculator, Virtual Calculator)
Method: same observation-only rules; snips of the LCD only. Key coordinates found by click-and-check. Rapid repeated clicks on the same key are treated as one press, so repeated digits need a pause between clicks.
- H0 ON then MODE: LCD shows `COMP  SD  REG` with `1 2 3` under them (HP-C0-mode-menu). Only three modes (no TABLE, no VERIFY, no base-n).
- C: MODE 2 (SD): `SD` annunciator. Data entry key is M+ (legend `DT`): `12 DT 15 DT 18 DT 22 DT 25 DT`, the LCD then shows `n=` and `5` (HP-C1x-data-n5-wrong is from a first attempt where the repeated `2` in 22 was lost: the mean then read `14.4`, HP-C2x-xbar-14p4-wrong; not used).
- C2: SHIFT 2 (S-VAR) shows `x̄  xσn  xσn-1` with `1 2 3` under them (HP-C2-svar-menu).
- C3 (retake with 12, 15, 18, 22, 25): `SHIFT 2`, `1` (x̄) then `=` shows `18.4` (HP-C3-xbar-18p4). Matches the fx-82 and SX-II mean.
- C3 σ and s: `SHIFT 2`, `2` (xσn) then `=` shows label `xσn` and `4.673328578` (HP-C3-sigma-n); `SHIFT 2`, `3` (xσn-1) then `=` shows `xσn-1` and `5.224940191` (HP-C3-s-n1). Both match the fx-82 and SX-II values. The label is on line 1 (small), the value on line 2.
- C4 `SHIFT 1` (S-SUM) shows `Σx²  Σx  n` with `1 2 3` under them (HP-C4-ssum-menu). (Σy etc. appear only in REG mode, not yet captured.)
- Stray captures from a slip (a repeated click on the same key was swallowed, so the S-VAR menu stayed open when `=` was pressed): `=` on the open menu shows `Syntax ERROR`, no extra prompt (HP-Gx-syntax-error-1, HP-Gx-syntax-error-2; HP-C3x-svar-menu-still-open is the menu screen before that).
- C5 REG: MODE 3 shows a type menu `Lin  Log  Exp  ▸` with `1 2 3` (more types on the next page, not paged) (HP-C5-reg-type-menu). Choosing 1 (Lin) shows `REG` annunciator and `0.` (HP-C5-reg-lin-selected). Data is entered as `x , y DT` using the comma key (the key right of `)`), the M+ key being DT. Data X 1 2 3 4 5, Y 2 4 5 4 5, `n=5` confirmed.
- C5 S-VAR in REG: `SHIFT 2` shows three pages stepped with the pad ▶: page 1 `x̄  xσn  xσn-1 ▸` (HP-C5-reg-svar-page1); page 2 `◂ ȳ  yσn  yσn-1 ▸` (HP-C5-reg-svar-page2); page 3 `◂ A  B  r ▸` (HP-C5-reg-svar-page3-ABr). Values: A `2.2` (HP-C5-reg-A); B `0.6` (HP-C5-reg-B); r `0.774596669` (9 digits) (HP-C5-reg-r). A and B match the fx-82 and SX-II; r is shown with 9 digits where those show 10.

## HP Part B (COMP mode, default)
- B1: MODE 1 (COMP). The `a b/c` key (legend `d/c` above it) enters a fraction with a separator mark: `1 a b/c 3 + 1 a b/c 4 =` shows entry `1⌋3+1⌋4` and the answer `7⌋12` on line 2 (a small `▲` annunciator top right) (HP-B1-third-plus-quarter). `SHIFT a b/c` (d/c) on that answer leaves it `7⌋12` (HP-B1b-shift-abc-nochange), expected since it is already proper. `a b/c` again shows `0.583333333` (9 digits) (HP-B1c-abc-decimal): that key toggles fraction and decimal (there is no S⇔D key). Not natural display: fractions are in the linear `n⌋d` form.

## HP unique features
- U1 Pol(: the key `Pol(` (SHIFT gives `Rec(`) then `1 , 1 ) =` shows entry `Pol(1,1)` and a single answer `1.414213562` (r) with the `▲` annunciator (HP-U1-Pol-1-1). I could not find θ: pad ▼ leaves it unchanged (HP-U1b-pad-down-nochange); `=` again leaves it unchanged; pad ▶ only scrolls the entry line. `RCL` shows an `RCL` annunciator waiting for a variable (HP-U1c-rcl-pending); `RCL ,` (the Y legend) typed `Y` into the entry (HP-U1d-rcl-Y-typed); `=` then shows `Y` and `0.` (HP-U1e-Y-equals-0), so θ is not stored in Y. Not resolved on the HP; the θ result is not shown by anything I tried.
- B12 hyp: the `hyp` key shows a `hyp` annunciator at the top left of the LCD and waits for a trig key (HP-B12-hyp-annunciator); this is a modifier/toggle-style behaviour, as Simon wants for CASSim. A digit pressed after `hyp` clears the annunciator and types the digit (HP-B12x-hyp-then-2). `hyp sin 1 ) =` shows entry `sinh 1)` and answer `1.175201194` (HP-B12-sinh-1); it matches the fx-82 value. The keys are not relabelled on screen (printed legends are fixed).
- B4 (Deg, default): `sin 45 ) =` shows entry `sin 45)` and `0.707106781` (9 digits, decimal only) (HP-B4-sin45); `cos 30 ) =` shows `cos 30)` and `0.866025403` (HP-B4-cos30). Trig keys write `sin ` with no opening bracket shown; no exact surd forms.

### HP Part B (cont.) — combinatorics, factorial, errors
- B9a `10 nCr 3 =` → entry `10C3`, answer `120` (HP-B9-nCr-10C3).
- B9b `5 SHIFT x⁻¹ (x!) =` → entry `5!`, answer `120` (HP-B9-fact-5).
- G (HP) `1 ÷ 0 =` → `Math ERROR` (HP-Gx-math-error).

### HP Part F — memory
- F1 `7 SHIFT RCL(STO) ALPHA (−)(A)` → entry `7→A`, answer `7` (HP-F1-sto-7-A).
- F2 `AC RCL ALPHA (−)(A) =` → entry `A`, answer `7` (HP-F2-rcl-A).

### HP Part B (cont.) — DMS, ENG
- B6 `12.5 = °'"` → entry `12.5`, answer `12°30°0°` (the ″ glyph renders as °) (HP-B6-dms-12p5).
- B10 ENG: key slip — entered `1235.` (decimal point after the 5), `= ENG` → entry `1235.`, answer `1235 ×10 03` i.e. mantissa 1235 with exponent 03 (display shows ×10 annunciator + `03`) (HP-B10-eng-1235). Recorded as observed; not the 12350 case used on the Abacus.

## EL (Sharp EL-531TH, Advanced D.A.L., Virtual Calculator)

Capture note: the first set of EL screenshots (all taken with the large mirror display at the top right of the screen) captured the Claude chat window that was sitting over that area, not the calculator. Those files were deleted on 2026-11-27 (the text below was re-taken). The Sharp window was moved to the left and every EL screenshot listed here was re-captured and opened to confirm it shows the calculator. The large mirror display is a copy of the small LCD; the capture is of the mirror.

Entry order is D.A.L. (function first, no closing bracket). Fractions are linear (`1⌟2`). Errors are numbered.

### EL Part A/H — menus
- A1 MODE → `NORMAL STAT`, `0` and `1` shown. The STAT annunciator was already lit in this shot because the unit was in STAT mode when MODE was pressed (EL-A1-mode-menu). Two modes only: no TABLE, no VERIFY.
- A2 SET UP → `FSE TAB` (first page of the number-format menu) (EL-A2-setup-menu). Further pages not explored.

### EL Part B — natural display and functions
- B1 `1 a b/c 2 + 1 a b/c 3 =` → entry `1⌟2+1⌟3=`, answer `5⌟6` (EL-B1-frac-1r2-plus-1r3).
- B1b `a b/c` → `0.833333333` (EL-B1b-abc-decimal). a b/c toggles fraction/decimal.
- B4 `sin 9 0 =` → entry `sin90=`, answer `1` (DEG) (EL-B4-sin90).
- B12 `hyp sin 1 =` → entry `sinh1=`, answer `1.175201194` (EL-B12-sinh1). hyp is a prefix key and the label of the following key does not change.
- B6 `1 2 . 5 = 2ndF D°M'S` → entry `12.5=`, answer `12°30'0"` (EL-B6-dms-12p5).
- B9a `1 0 2ndF nCr 3 =` → `10C3=` → `120` (EL-B9-nCr-10C3).
- B9b `5 2ndF n! =` → `5!=` → `120` (EL-B9-fact-5).
- Not run on EL: surds, `%`, ENG, Ran#, Ans replay, DRG▸.

### EL Part C — STAT (SD)
- C0 MODE 1 (STAT) → submenu `SD LINE QUAD` with `0 1 2` and a ▸/more arrow (EL-C0-stat-submenu).
- C1 `0` (SD) then `12 M+ 15 M+ 18 M+ 22 M+ 25 M+` (a typed 23 was corrected with DEL to 22). Last M+ shows `DATA SET=` `5` (EL-C1-dataset-n5).
- C3 variables with ALPHA + key: `x̄=` `18.4` (EL-C3-xbar-18p4); `Sx=` `5.224940191` (EL-C3-sx); `σx=` `4.673328578` (EL-C3-sigmax); `n=` `5` (EL-C3-n). Same results as the Abacus, fx-82 and HP for 12 15 18 22 25.
- Not run on EL: LINE/QUAD regression, sums (Σx, Σx²), data editing, clearing statistics.

### EL Part G — errors
- G `1 ÷ 0 =` → `Error 2` (EL-Gx-error-2-div0). Numbered errors, no text message; other codes not triggered.

### EL Unique features
- U1 base conversion: `2 5 5 = 2ndF →HEX` → entry `255→HEX`, answer `FF` with `H` annunciator (EL-U1-base-255-to-HEX). `1 0 = 2ndF →BIN` → entry `10→BIN`, answer `1010` with `b` annunciator (EL-U1b-base-10-to-BIN). →PEN, →OCT and →DEC are on 2ndF + − =. The base mode is sticky: after →BIN the unit stayed in BIN (b annunciator) and rejected digit 3 until 2ndF →DEC was pressed (observed earlier; the earlier screenshot of that was among the discarded set, so this behaviour is recorded from the live screen only).
- U2 polar/rectangular: not run (separator key for the two arguments not identified; only 2ndF `(` was tried and did not insert a comma).
- Not run: RANDOM, MDF, M-CLR, STO/RCL memory, logic operators (AND/OR/XOR/NOT shown as key labels).
- No VERIFY mode.

### EL key table (Part H equivalent, from the window's legend)
Rows: hyp sin cos tan π DRG; y^x √ x² x³ log ln; Exp a b/c D°M'S RCL STO M+; 7 8 9 ( ); 4 5 6 × ÷; 1 2 3 + −; 0 . +/− =. Top: HOME, ON/C, 2ndF, ALPHA, SET UP, DEL, MODE, 4-way pad. 2ndF labels include arc-hyperbolics and arc trig (arc hyp, sin⁻¹ etc.), NOT/AND/OR/XOR, DRG▸, →rθ, →xy, n!, nCr, nPr, base keys, STAT variable letters (x̄ sx σx ȳ sy σy Σx Σx² Σxy n).

## Notes for Simon's hyp toggle request
- Abacus SX-II: HYP opens a menu (sin, cos, tan, sinh, ... see SX-B12-hyp-menu); no key relabelling was seen.
- HP 10s: hyp lights an annunciator and waits for a trig key; the keys keep their printed labels.
- EL-531TH: hyp is a prefix key (entry shows `sinh1`); the keys keep their labels.
- fx-82AU PLUS II: not re-checked in this pass for relabelling.
- No emulator relabelled keys while hyp was active, so the toggle-with-new-labels is a CASSim design addition.

## HP key table (Part H equivalent, from the emulator face)
Top row: SHIFT, ALPHA, MODE, ON, 4-way pad. Then x⁻¹ nCr Pol( a b/c; √ x² x³ x^y log ln; (−) °'" hyp sin cos tan; RCL ENG ( ) , M+; 7 8 9 DEL AC; 4 5 6 × ÷; 1 2 3 + −; 0 . EXP Ans =. SHIFT layers: x! (over x⁻¹), nPr, Rec(, d/c, STO, CLR (over 9), S-SUM, S-VAR, Rnd, Ran#, π, DRG▸, %. Digit 3-row positions per the coordinates used; legends read from the screenshot, not exhaustively verified.

## Duplicate screenshots (intentional)
Some HP files are byte-identical because the screen did not change between steps: HP-Gx-syntax-error-1/2, HP-U1-Pol-1-1 and HP-U1b-pad-down-nochange, HP-C2-svar-menu / HP-C3x-svar-menu-still-open / HP-C5-reg-svar-page1, HP-B1-third-plus-quarter and HP-B1b-shift-abc-nochange.

## FX leftovers, run 2026-11-27 ("Run the rest!")

- **C3** `MODE 2 1`, data 4 7 9 12 14 18 21 25: table shows 8 rows (FX-C3-table-8vals). `SHIFT 1 5 3 =` Q1 = `8` (FX-C3-Q1-8); med = `13` (FX-C3-med); Q3 = `19.5` (FX-C3-Q3-19p5). Matches the brief. C3b (5-number set 2 5 6 9 11 14 20) not run.
- **C6/C6b data retention:** after `MODE 1` (COMP) then `MODE 2 1` again, the table is empty (FX-C6-reenter-stat-empty). Data is cleared on leaving STAT, as CASSim does. (The SHIFT 1 2 Data check expecting retention does not apply.)
- **C7 FREQ:** SHIFT MODE, ▼ (page 2: `1:ab/c 2:d/c / 3:STAT 4:Disp / 5:◀CONT▶`), 3 (STAT) gives `Frequency? 1:ON 2:OFF` (FX-C7-freq-prompt). After 1 and MODE 2 1 the table has columns `X` and `FREQ`. X 1 2 3 4, FREQ 5 12 8 3 (FX-C7-freq-table; the FREQ cells are read from a small zoom). `x̄` = `2.321428571` (FX-C7-freq-xbar). Matches the brief.
- Not run in this pass: C3b, C4b (A+BX Sum menu: Σx³/Σx²y/Σx⁴ presence on the fx-82), C5 (r 0.9972413741, A 1.2, B 1.9, ŷ(7) 14.5), C8 (DEL/INS in the editor), Rnd(, GCD/LCM, RanInt#, DMS entry detail, hyp relabelling.

## EL and HP shots captured after "Run the rest!" (index only, values not yet transcribed)

These files exist in `scientific-shots/` and are listed from their names. The screen values still need to be read and written into the sections above before anything in them is claimed.

- EL: A3 SET UP `FSE` submenu; B3 sqrt8; B10 250+15%; B11 DRG (press 1, press 3 = DEG); B13 ENG 12350; Gx sqrt(-1) and Error 1 syntax, Error 2 with STAT no data; C5 LINE data (n=5), a, b, r; C4x alpha slips; F0y/F1/F2/F3 memory (STO 7 to A, RCL A, M+ 5 3 RCL M); U2 Pol(1,1) r, θ; U3 Rec(2,60) x, Y; U4 RANDOM prompt and result; U5 MDF.
- HP: A1/A1b/A2/A2b/A2c CLR menu and memory-clear prompt; B10 250×15%; B11 Ans, DRG menu; F3 M+/M−, F4 RCL M; U2 Ran# prompt then `Syntax ERROR` after `=`; several "blank-off" slips where AC on a cleared display powers the HP off (ON restores it).
- Duplicates by md5 (screen did not change, kept on purpose): HP-A1/A1b, HP-Gx-syntax-error-1/2, the five HP blank-off shots, EL-C1/EL-C5 dataset n5, EL-Gx-error-2-div0 / EL-Gx-sqrt-neg1 (both Error 2), HP-A2b/A2c (the clear prompt and its result look identical, so the memory clear is unconfirmed), EL-U2/U2b, HP-U1/U1b, EL-F0x-slip / EL-Gx-error-1-syntax, HP-B1/B1b.

### FX leftovers, second run 2026-11-27

- **GCD/LCM:** `ALPHA ×` types `GCD(`; `GCD(12,18)` = `6` (FX-U3-GCD-12-18). `ALPHA ÷` types `LCM(`; `LCM(4,6)` = `12` (FX-U4-LCM-4-6).
- **Rnd(:** `SHIFT 0` types `Rnd(`; `Rnd(2÷3)` = `0.6666666667` (FX-U5-Rnd-2div3). (An earlier note that Rnd( was not found is withdrawn: it is SHIFT 0.)
- **C5 regression A+BX:** X 2 4 6 8 10, Y 5 9 12 17 20 (the FREQ column stayed on from the earlier FREQ test and holds 1s) (FX-C5-table-xy). r = `0.9972413741` (FX-C5-reg-r), A = `1.2` (FX-C5-reg-A), B = `1.9` (FX-C5-reg-B), ŷ(7) = `14.5` (FX-C5-reg-yhat-7). All match the brief. A first attempt typed 9 instead of 7 (left on screen as `9ŷ`; not used).
- **C4b Sum menu (A+BX):** one screen shows all eight entries: `1:Σx² 2:Σx / 3:Σy² 4:Σy / 5:Σxy 6:Σx³ / 7:Σx²y 8:Σx⁴` (FX-C4b-sum-menu-p1; FX-C4b-sum-menu-p2 is an identical second snip after pressing ▼, kept as a duplicate). So the fx-82 has Σx³, Σx²y and Σx⁴ like the SX-II.
- Still not run on the fx-82: C3b, C8, RanInt# values, DMS entry detail, hyp relabelling.

## EL and HP shots, values transcribed 2026-11-27 (read from contact sheets in `scientific-shots/_contact-sheets/`)

### EL-531TH
- B3 `√8 =`: entry `√8=`, answer `2.828427125` (decimal, no surd) (EL-B3-sqrt8).
- B10 %: the shot shows `250+15=` answer `265`. The % key was **not** used (slip); the EL % route is still unknown (EL-B10-250plus15pct).
- B11 DRG: first press shows `RAD`, third press shows `GRAD` (file EL-B11b is named "DEG" but shows GRAD); so DRG cycles DEG, RAD, GRAD (EL-B11-drg-press1, EL-B11b-drg-press3-DEG).
- B13 ENG: `12350 =` with ENG gives `12.35000000 ×10 03` with the ENG annunciator (EL-B13-eng-12350).
- Gx `√(-1)`: `Error 2` (EL-Gx-sqrt-neg1). Syntax slip: `Error 1` (EL-Gx-error-1-syntax).
- C5 LINE regression: `a=` `2.2`, `b=` `0.6`, `r=` `0.77459666…` (EL-C5-line-a/b/r). Same as the SX-II for X 1-5, Y 2 4 5 4 5 (the data entry itself was not re-checked from a table shot).
- F memory: `7→A` / 7; `A=` / 7; `M=` / 8 after M+ with 5 and 3 (EL-F1, EL-F2, EL-F3).
- U2 Pol(1,1): `r=` `1.414213562`; next screen labelled `Y=` with `45` (the angle, shown as shown) (EL-U2-pol-1-1-r, EL-U2c-pol-theta-Y-45). U3 Rec(2,60): `x=` `1`; `Y=` `1.732050808` (EL-U3-rec-2-60-x, EL-U3b-rec-Y-1p732).
- U4 RANDOM: a menu `RAND R-DICE` (with `0 1` under it); after choosing, the screen shows `RANDOM_` and `0.` (the random value was not seen) (EL-U4-random-prompt, EL-U4b-random-equals). U5 MDF: `0=` / `0.` (EL-U5b-MDF-equals; no meaningful input given).
- A3 SET UP page 1 shows `FIX SCI ENG` with `0 1 2` (EL-A3-fse-submenu).

### HP 10s
- B10 `250×15%`: answer shown as `375` (the decimal point is not legible in the shot; 37.5 is expected) (HP-B10-250x15pct).
- B11 `Ans×2` = `10` (HP-B11-ans-x2). DRG menu `D R G` with `1 2 3` (HP-B11-drg-menu).
- A2 CLR menu `Mcl Mode All` (`1 2 3`). Choosing Mcl shows `Mem clear` and `0` (HP-A2b), and the "done" shot is identical (HP-A2c), so whether memory was actually cleared is unconfirmed.
- F3/F4: `3M−` / 3 and `M` / 3. M had a stray 3 from a slip (HP-F3b), so the M+/M− result is not clean evidence.
- U2 `Ran#` shows `Ran#` / `0`; pressing `=` gives `Syntax ERROR` (re-confirmed) (HP-U2-ran-prompt, HP-U2b-ran-equals-syntax-error).
