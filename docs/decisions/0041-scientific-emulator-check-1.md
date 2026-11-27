# 0041: CASSim Scientific follows its emulator check; exact answers and TABLE are extras

Status: accepted 2026-11-27 (Simon). Requirements: FR-FX-CFG-001, FR-FX-DSP-005, FR-FX-DSP-008, FR-FX-FNC-002, FR-FX-FNC-005, FR-FX-FNC-008, FR-FX-MOD-003, FR-FX-MOD-004, FR-FX-UI-005, FR-FX-UI-008 (new). Changes SDD-14 (sections 1, 4, 4.2, 5.1, 7 and 8), SDD-15 (sections 1 and 6) and the SRS rows named here.

## Context

Emulator check 1 (2026-11-26 and 27) ran the brief `docs/testing/emulator-scientific-capture.md` on the makers' own PC emulators of the four calculators behind CASSim's layouts: the fx-82AU PLUS II 2nd edition, the SX-II MATRIXn, the HP 10s and the EL-531TH. The results are in `docs/testing/emulator-scientific-results.md`; the screenshots (about 340) and Cowork's handoff are in the evidence repository (`docs/testing/scientific-shots/`, `docs/handoff/`; decision 0039). Where the emulators and CASSim differed, the fx-82AU PLUS II manual was checked too. It agreed with the emulators on every point below.

## Decision

1. **Follow the emulators by default.**
   - Reset gives MthIO-LineO and Norm 2. An answer is a decimal first (1÷200 is 0.005) unless the entry has a fraction in it, and S⇔D gives the fraction. Fractions are drawn stacked whenever the input is MthIO.
   - Surds and multiples of π are decimals, even in MathO: √2+√8 is 4.242640687, and sin 45° is 0.7071067812.
   - `%` divides by 100 on the fx-82 and SX-II, so 250+15% is 250.15. A percentage increase is typed 250+250×15%, as the manual shows. The EL-531 and 10s keep their add-on percent, which is what their manuals give (125+10% is 137.5).
   - An entry of ° ' " values joined by + − × ÷ answers in ° ' ".
   - The MODE menu is COMP, STAT, VERIF on the fx-82 as on the SX-II, so VERIFY is MODE 3.
   - hyp opens the six-item menu on the fx-82, as on the SX-II.
2. **Exact surds and π are an opt-in extra** (Settings ▸ CASSim extras; `Setup.surds`, saved with the calculation). They apply in MathO only and have up to two terms. That is what the more advanced scientific calculators do:

   | Model | Exact surds | π kept as π |
   |---|---|---|
   | fx-8200 AU | yes, two terms | yes |
   | fx-991ES PLUS | yes, two terms | yes |
   | HP 300s+ | yes | yes |
   | TI-36X Pro, TI-30XS MultiView | yes, through the answer toggle | yes |

   None of them keeps e symbolic (the Casio manuals show e as 2.718281828), so CASSim does not offer that.
3. **TABLE is an opt-in extra mode** for the fx-82 and SX-II (remembered in the browser). When it is on, TABLE is MODE 4. Its lesson and example ask for it. A calculation saved or shared in TABLE mode switches the extra on.
4. **hyp shows that it is waiting.** While its menu is open, or on the 10s and EL-531 while the prefix waits:
   - the hyp key is lit and a `hyp` mark shows on the LCD;
   - sin, cos and tan, and their SHIFT legends, read sinh, cosh and tanh;
   - on the fx-82 and SX-II a trig key picks from the menu, as its new name says, and hyp pressed again cancels.

   This is a learning aid that changes appearance, not the maths. It is on by default and can be switched off in Settings (remembered in the browser). No calculator renames its keys, so it is CASSim's own (SDD-15 section 1).
5. **Ran#** is always a three-place decimal, in MathO as well (Simon, 2026-11-27). The fx-82 in MathO shows thousandths as a fraction (581/1000); CASSim does not follow it there. S⇔D still turns the decimal into a fraction, as it does for any decimal.

The rule for later work: toggles, assists and hints are on by default; extra functionality and extra menus are opt-in.

## Consequences

- Tests: `tests/devices/scientific/test_scientific_check1.py` holds the emulator rows. The older calculation tests run in MthIO-MathO with the surds extra on, so the exact forms stay checked.
- The device tests are against emulators, not physical calculators. If a real calculator differs, change the default only, not the settings.
- The emulator licence terms are to be recorded with the evidence (NFR-LEG-006) before the next capture.
