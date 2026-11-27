# SDD-14. Scientific Calculator (CASSim Scientific)

Status: Design for CASSim Scientific, a natural-display scientific calculator of the class used in Australian schools (fx-82AU PLUS II / fx-100AU PLUS / Abacus SX-II MATRIXn). Requirements: FR-FX-MOD, -CFG, -DSP, -MEM, -FNC, -STA, -TUT, -SHR and -UI in SRS section 4.12 (section 3 maps them to this document). Built in `src/cassim/devices/scientific/` (device id `scientific`, bundle `sci`, site `cassim-sci`; `fx` in file names and requirement IDs is the working name it started with). Section 8 records what is built and what is not.
Author: CASSim Team (Simon Tyler).
Conventions: Clean room boundary (decision 0028, NFR-LEG-008, NFR-LEG-009). Pure Python core, headless device state, Flet UI rendering, Pyodide offline execution. Numbered SDD-14 because SRS appendix A reserves SDD-12 for device profiles (first written as SDD-12, renamed 2026-11-25).

---

## 1. Executive Summary & Purpose

In Australian secondary mathematics (Year 7–10, VCE General Mathematics, VCE Mathematical Methods, VCE Sciences, HSC Standard Mathematics, HSC Advanced Mathematics), non-programmable, non-graphing scientific calculators are mandatory for exams or specific assessment modules where CAS devices are prohibited or unnecessary. Some of the standard classroom devices in Australia are:
1. **Casio fx-82AU PLUS II** (and 2nd edition) - the overwhelming de facto standard in Australian schools.
2. **Casio fx-100AU PLUS** - extended version with complex numbers, vectors, 40 metric conversions, and normal distribution probabilities.
3. **Abacus SX-II MATRIXn** - approved Australian curriculum equivalent manufactured by Abacus with identical functional mappings, carbon faceplate, and 2nd/ALPHA key styling.
4. **TI-30XB** - Texas Instruments Multiview calculator.
5. **HP Scientific Calculator 10s II** - Hewlett Packard scientific calculator.
6. **Sharp Scientific Calculator EL-531TH** - Sharp's advanced scientific calculator.

**CASSim Scientific** is a scientific calculator device package (`src/cassim/devices/scientific`) in the CASSim multi-app browser shell. It delivers:
- A responsive handheld calculator in CASSim's own design that keeps the familiar 50-key arrangement, usable with a mouse, touch or the computer keyboard.
- Natural Display (MthIO) input and exact answers: fractions, mixed numbers, surds and multiples of π.
- The statistics conventions CASSim uses everywhere (median-split quartiles, $n-1$ sample $s_x$, $n$ population $\sigma_x$, Pearson's $r$).
- A **user-driven interactive tutorial engine** in which the student presses every key (Guide me), watches the keys played (Show me), or solves a new problem unaided (Test me).

---

## 2. Clean-Room Boundary, Trade Dress & Trademark Governance

Per CASSim decisions 0028, NFR-LEG-008, and NFR-LEG-009:
1. **No ROM, Firmware, or Proprietary Code**: No binary dumps or decompiled code from Casio, Abacus, or any other manufacturer. The simulator is a purely behavioral, mathematical reconstruction built from curriculum specifications, user manuals, and syllabus requirements.
2. **No Proprietary Brand Trademarks**: The product is strictly **CASSim Scientific**. Manufacturer trademarks such as "Casio", "fx-82AU", "fx-100AU", "Natural V.P.A.M.", "ClassWiz", and "Abacus" are never used as product names, screen badges, or UI assets. Generic, descriptive terminology is employed: "CASSim Scientific", "Natural Display", "MathIO / LineIO", "S⇔D Toggle", "Scientific Calculator". The one place a maker and model class is named is the Appearance ▸ Calculator list (FR-FX-UI-005, decided 2026-11-25), which names the class of calculator a keypad layout follows ("Casio fx-82 series") so students and teachers can find their own model; logos, artwork, fonts and copyright text are never copied.
3. **No Trade Dress Mimicry**: Skins and visual themes must **not** be faithful reproductions or traces of proprietary physical calculator casings. We replicate the abstract functional arrangement of keys (the standard 50-key matrix) so that students build transferable muscle memory for examinations, but the physical presentation—curvatures, bevels, badge placements, unique color combinations, textures, and keycap profiles—is CASSim's own original digital design.
4. **Original CASSim Design Language**: Rather than attempting to mimic physical plastics or branded hardware replicas, CASSim Scientific adopts CASSim's unified software design language: clean flat-design aesthetics, elegant dark/light/high-contrast accessibility palettes, modern typography, and vector-rendered components.
5. **Documentation & Help Prose**: All instructional texts, step-by-step guides, and tutorial explanations are original pedagogical prose written from scratch for Australian classrooms.

Behaviour that has not been checked against a real device is marked as such in section 8; it is CASSim's best reading of the requirement, not a verified match.

---

## 3. Requirements

The requirements are in `docs/SRS.md` section 4.12 ("CASSim Scientific") and nowhere else, so the two documents cannot drift apart; `docs/traceability.md` traces them to tests. This document designs for them:

| IDs | Area | Designed in |
|---|---|---|
| FR-FX-MOD-001 to 005, FR-FX-CFG-001 to 006 | Modes (COMP, STAT, TABLE, VERIFY; CMPLX and VECTOR later), SETUP and CLR | sections 4.2, 6 and 8 |
| FR-FX-DSP-001 to 009 | The two-line display, annunciators, natural input, S⇔D, ENG, DMS, FACT | sections 4, 5 and 6 |
| FR-FX-MEM-001 to 004 | Ans, the nine variables, M+ and M−, PreAns | sections 4 and 8 |
| FR-FX-FNC-001 to 009 | Functions: trigonometry, hyperbolics, powers, logarithms, nPr and nCr, Pol and Rec, GCD and LCM, %, Rnd | section 4 |
| FR-FX-STA-001 to 006 | Statistics: data entry, summaries, school quartiles, regression, the STAT menu | sections 4.2 and 6 |
| FR-FX-TUT-001 to 006 | Tutorials: Guide me, Show me, Test me | sections 5.1 and 7 |
| FR-FX-SHR-001 to 006 | Autosave, share links and files | section 6 |
| FR-FX-UI-001 to 007 | Top bar, presentation mode, tutorial panel, computer keyboard, calculator layouts, phones | sections 4.1, 4.2 and 5.1 |

---

## 4. Keypad layout

The keypad keeps the standard 50-key arrangement. Small labels above a key are its SHIFT layer (left, yellow) and its ALPHA layer (right, red). `keys.py` holds this table; the drawing, the device state, the tutorials and the keyboard map all use it, and a test checks that every printed label does something.

```
[Row 1: Modifiers & D-Pad]
  [ SHIFT ]                    [ ▲ ]                   (SETUP)
  [ ALPHA ]                 [◀]     [▶]                [ MODE ]
                               [ ▼ ]                   [ ON ]

[Row 2]
  [ Abs ]      [ x³ ]          [ x⁻¹ ]        [ x! ]
                                 (the D-pad sits above rows 1 and 2)

[Row 3: Templates]
  [ ■/□ ]      [ √■ ]          [ x² ]         [ x■ ]    [ log ]   [ ln ]
  (a b/c)      (³√)                           (■√)      (10■)     (e■)

[Row 4: Trigonometry]
  [ (−) ]      [ ° ' " ]       [ hyp ]        [ sin ]   [ cos ]   [ tan ]
  (A)          (FACT / B)      (C)            (sin⁻¹/D) (cos⁻¹/E) (tan⁻¹/F)

[Row 5: Memory & Formatting]
  [ RCL ]      [ ENG ]         [ ( ]          [ ) ]     [ S⇔D ]   [ M+ ]
  (STO)        (←)             (%)            (, / X)   (ab/c⇔d/c / Y) (M− / M)

[Row 6]
  [ 7 ]        [ 8 ]           [ 9 ]          [ DEL ]   [ AC ]
                               (CLR)          (INS)     (OFF)

[Row 7]
  [ 4 ]        [ 5 ]           [ 6 ]          [ × ]     [ ÷ ]
                               (VERIFY)       (nPr/GCD) (nCr/LCM)

[Row 8]
  [ 1 ]        [ 2 ]           [ 3 ]          [ + ]     [ − ]
  (STAT)                                      (Pol)     (Rec)

[Row 9]
  [ 0 ]        [ · ]           [ ×10ˣ ]       [ Ans ]   [ = ]
  (Rnd)        (Ran# / RanInt) (π / e)        (DRG▶)
```

The default layout (section 4.2) follows the fx-82 series, whose row 2 is `Abs x³ x⁻¹ x!`; the log■□ template (FR-FX-DSP-003) is typed with the keyboard key `g`. Other changes from the first draft of this document: `)` carries the comma on SHIFT and `X` on ALPHA; `S⇔D` carries `Y` and `M+` carries `M` on ALPHA. SHIFT 6 (VERIFY) opens the relations `= ≠ > ≥ < ≤`. SHIFT DEL (INS) inserts a row in the STAT editor; the calculation screen is always in insert mode.

Priority, highest first: brackets and functions; postfix keys (x², x⁻¹, x!, %, °, ʳ, ᵍ, x̂, ŷ) and powers; the negative sign; nPr and nCr; multiplication with the × left out (so 1÷2π is 1÷(2π)); × and ÷; + and −; relations. `a + b%` adds b% of a. A missing `)` at the end of an entry is allowed.

### 4.1 Computer keyboard (FR-FX-UI-004)

| Keys | Calculator keys |
|---|---|
| 0–9 . + - * / ( ) ^ | as on the keypad (`/` is ÷, `^` is x■) |
| Enter or = | = (in VERIFY mode `=` types the relation and Enter calculates) |
| Backspace, Delete | DEL |
| Esc | AC; shows the menu bar when it is hidden |
| Arrow keys | the D-pad |
| Home, End | start or end of the entry |
| F1, F2 | SHIFT, ALPHA (then any key) |
| Ctrl+M | MODE (F1 then Ctrl+M is SETUP) |
| Ctrl+/ | fraction template (as in the Nspire app) |
| s c t / S C T | sin cos tan / their inverses |
| h, l, n, L, N, r, R, q, g | hyp, log, ln, 10■, e■, √, ³√, x², log■□ |
| ! % , | x!, %, the comma |
| d, D | ° ' " and FACT |
| m, M | M+ and M− |
| p, e, a, x, y | π, e, Ans, X, Y |
| o | ON: switches the calculator on after SHIFT AC (OFF); the EL-531's ON/C does too |
| < > | relations |
| Ctrl+C | copy the answer |

Tab is deliberately unbound: it moves the browser's focus, and Enter would then also press the focused button. The keypad keys are not focusable for the same reason. Only the non-typing shortcuts are listed in the device profile (`Profile.computer`), which the published page uses to keep them from the browser (`tools/publish.py`).

---

### 4.2 Calculator layouts (FR-FX-UI-005; `layouts.py`)

A layout is data: rows of keys, each with its face, its legends and, for each layer (plain, after SHIFT, after ALPHA), the canonical key sequence it stands for. Pressing a layout key sends that sequence to the one device state, so the maths engine and the keyboard map are shared. After STO or RCL a key sends the letter or statistic printed above it, with no ALPHA (the EL-531's STO then yˣ for A, RCL then 4 for x̄). Pseudo-keys serve keys only some calculators have: `TOK:<token>` types a token printed on a key (a statistic, or the 10s's `;`), `DATA` adds the entry as a STAT data row (the EL-531's DATA and the 10s's DT; M+ outside STAT), and the EL-531's `HOME`, `CA`, `MCLR`, `RANDOM`, `DRG`, `DRGCONV` and `STOXY` (STO, which is (x,y) in STAT mode). Layouts follow each class's arrangement and key names closely but not exactly; the key *sequences* follow the makers' manuals (`references/`).

Each layout names a **dialect**, the way the device state runs its menus (`state.py`):

- `casio` (fx-82): as the SRS rows (FR-FX-MOD, -CFG, -STA) and section 4.1 describe. The two-variable STAT menu is 1 Type, 2 Data, 3 Sum, 4 Var, 5 Reg, 6 MinMax (corrected 2026-11-25; Reg was 6).
- `sx2` (SX-II): as `casio`, but HYP opens a menu (1 sinh … 6 tanh⁻¹), the VERIFY menu is = ≠ > < ≥ ≤, and Norm 2 is the default.
- `ms` (the fx-82MS family the HP 10s follows): MODE shows COMP, SD, REG, and MODE again shows Deg/Rad/Gra, then Fix/Sci/Norm, then Disp (a b/c or d/c). SHIFT MODE is CLR: 1 Scl (in SD/REG) or Mcl, 2 Mode, 3 All, then =. SD and REG take data on the calculation screen: x DT, x ; f DT, x , y DT, and DT alone repeats the last entry. SHIFT 1 (S-SUM) and SHIFT 2 (S-VAR) are menus of pages turned with ◀ ▶ (S-VAR: x̄, xσn, xσn-1; ȳ, yσn, yσn-1; A, B, r; x̂, ŷ). % works out the whole entry: A × B % is B% of A, and + or − straight after adds it on or takes it off; A ÷ B %, A + B % and A − B % are the ratio, the total and the change as a percentage of B. a b/c types a fraction mark (2⌟3, 1⌟2⌟3) and, after an answer, switches between a fraction and a decimal. Defaults: LineIO, Norm 2, mixed numbers.
- `sharp` (EL-531): MODE 0 is NORMAL and MODE 1 n is STAT (0 SD, 1 LINE, 2 QUAD, 3 EXP, 4 LOG, 5 PWR, 6 INV), with data typed as x DATA, x (x,y) f DATA or x (x,y) y DATA; RCL and a statistics key shows its value. SET UP 0 n sets FIX, SCI, ENG, NORM1, NORM2 and SET UP 1 n sets TAB. DRG cycles the angle unit and 2ndF DRG▸ converts the answer into the next unit. 2ndF % works out the entry (125 + 10 % is 137.5). a b/c as for `ms`. 2ndF CA clears the answer and the statistics; 2ndF M-CLR offers 0 (memories) and 1 (reset, then =). Defaults: LineIO, mixed numbers.

| | Casio fx-82 series | Abacus SX-II series | Sharp EL-531 series | HP 10s series |
|---|---|---|---|---|
| SHIFT / ALPHA keys | SHIFT, ALPHA | 2nd, ALPHA | 2ndF, ALPHA | SHIFT, ALPHA |
| Display | natural | natural ("Math") | two-line linear | two-line linear |
| Modes listed | COMP, STAT, TABLE, VERIFY | COMP, STAT, VERIFY | COMP, STAT | COMP, STAT |
| Exact/decimal key | S⇔D | F↔D | a b/c after an answer | a b/c after an answer |
| SETUP | SHIFT MODE | 2nd SET UP | SET UP 0 (FSE), 1 (TAB); DRG key | MODE pressed again |
| Clear | SHIFT 9 (CLR) | 2nd CLR | 2ndF CA; 2ndF M-CLR | SHIFT MODE (CLR) |
| STAT data entry | table editor | table editor | x (x,y) f DATA | x ; f DT, x , y DT |
| STAT results | SHIFT 1 menus | 2nd STATVAR menus | RCL + key | SHIFT S-SUM / S-VAR pages |
| Lessons not offered | — | TABLE | freq, fivenum, prime, table | freq, fivenum, prime, table |
| On the keys but not simulated | — | — | base-n, logic, ENG display mode, STAT VAR list | CL (delete a data item), Σx³ page, `:` |

Older fx-82 models (fx-82MS) have a linear display and no VERIFY or TABLE; the fx-82 layout follows the natural-display models, and the HP 10s layout shows how the MS family works. Not yet checked against a real calculator: the EL-531's M-CLR menu (not in its operation guide), CA's exact reach, and STAT VAR (it opens the fx-82's STAT menu). Doc ▸ Examples are the fx-82's keys; they are pressed on its menus and refused where the calculator lacks the feature.

---

## 5. Visual Styling & Original CASSim Themes

To avoid trade dress mimicry, CASSim Scientific does **not** reproduce physical hardware shells, branded badges, or proprietary manufacturing finishes. It keeps the functional 50-key layout and applies CASSim's own flat design. The theme is CASSim's shared one (SDD-15 section 7): Dark, Light or High contrast, chosen in CASSim ▸ Appearance… here, on Home or in any app. `ui/skins.py` gives the calculator's own colours for each preset; the page, the menu bar, its chips and the panel text come from the shared theme, so customised colours apply there too:

1. **Dark (the default)**: chassis `#1e2229`; function keys `#282c35` with `#f0f2f5` labels; number keys `#363c48`; SHIFT amber `#e5a93c` and ALPHA coral (`#ef7b7b`, lighter than the first draft's `#e05d5d` for contrast on the dark body); DEL and AC emerald `#43a047` / `#2e7d32`; sage LCD `#dce5d3` with `#121810` characters.
2. **High contrast**: charcoal chassis `#121316` with white keys and black labels; AC `#c62828`, DEL `#37474f`; paper LCD `#f4f6f8` with black characters. The legends above the keys sit on the dark body, so they are light gold `#ffb020` and light blue `#7cc0ff`; the draft's `#d48800` and `#0050b3` are used where they sit on white (the SHIFT and ALPHA key labels).
3. **Light**: chassis `#e9ecef` with a `#ced4da` edge; function keys `#495057`, number keys `#f8f9fa`; LCD `#e8edf2` with `#1a202c` characters.

The badge on every theme reads **`CASSim Scientific`** with the subtitle **`NATURAL DISPLAY`**. The LCD uses Roboto Mono (bundled), whose fixed character width lets fraction bars and scrolling be laid out without measuring text; symbols fall back to the bundled Noto fonts so nothing is fetched at run time.

The calculator scales to the window (between 0.7× and 1.3× of a 360 × 700 design) so every key is visible on a Chromebook screen; below 0.7× the page scrolls. The tutorial panel moves under the calculator when the window is too narrow for both.

### 5.1 Top Navigation Bar & Presentation Mode (CASSim Consistency)

1. **Top bar (FR-FX-UI-001)**:
   - **CASSim menu** (the shared menu, SDD-15 section 4): Home; Tutorials (✓ when shown), Fullscreen or, on an installed phone, Avoid cutout; Settings… (the SETUP choices as a form), Appearance…, Keyboard shortcuts…; Install, Check for Updates, the offline status; Help (wiki)…, About CASSim….
   - **Doc menu**: Open…, Save, Save as… (calculations kept by name in the app's storage: `cassim.app.saved`, decision 0033), Import file…, Export file… (`.cassim.json`), Share link…, Examples ▸ (standard deviation, five-number summary, linear regression, table of values, mixed numbers, exact trigonometry, degrees-minutes-seconds, prime factorisation), Reset all… (asks first).
   - **Status chips**: mode, angle unit, input mode; clickable.
2. **Presentation mode (FR-FX-UI-002)**: the full-screen button hides the bar; a floating button or Esc restores it.
3. **Tutorial panel (FR-FX-UI-003)**: shown or hidden by the Tutorials button or CASSim ▸ Tutorials (✓ when shown); lesson list (completed lessons ticked), Guide me / Show me / Test me, playback speed, step counter, instruction and reason, next-key chip, expected screen, keys so far, Back / Skip step / Restart / End. The student's own calculation is put aside when a lesson starts and comes back when it ends.

---

## 6. Architecture & Integration with CASSim Core

```
src/cassim/devices/scientific/
  __init__.py     DEVICE (id "scientific", storage "scientific.", help page); the profile lists the
                  keyboard shortcuts
  keys.py         every key: id, labels, layers; the computer keyboard map
  layouts.py      the four calculator layouts, and the translation from their keys to canonical keys
  values.py       exact values (fractions, two-term surds, multiples of π) and arithmetic
  layout.py       the LCD as a tree: text, fractions, roots, raised and lowered parts, cursor
  editor.py       the input line: tokens and templates with a cursor that moves through slots
  parser.py       tokenizer and Pratt parser that evaluate an entry (no Python eval)
  display.py      SETUP settings and answer formatting (Norm, Fix, Sci, ENG, exact forms, DMS)
  engine.py       statistics: one- and two-variable summaries, school quartiles, all regressions
  state.py        the device: modes, menus, STAT editor, TABLE, memories, history, files, links
  tutorials.py    lessons, sessions, expected screens computed by running the lessons
  examples.py     Doc ▸ Examples as key presses
  ui/             FLET: app.py (the view), render.py (natural display), skins.py (themes)
```

The device follows decision 0032: it imports no other device, only `ui/` imports Flet, files and links use the CASSim document envelope with `"device": "scientific"`, and its storage keys have their own prefix. No SymPy, NumPy or SciPy: statistics are pure Python. The shell opens the device from Home, from `#/app/scientific`, from `cassim --app scientific`, or from a share link that names it.

---

## 7. Tutorials

The tutorial catalogue (`tutorials-catalog-fx.md`) plans 64 lessons. Twelve are built, covering the six priority lessons (reset, frequency setup, mean and standard deviation, five-number summary, frequency tables, regression) and fractions with S⇔D, exact trigonometry, percentage increase, storing to a variable, FACT and TABLE mode. Each lesson has a Test me problem. Tests run every lesson to its stated answer and check that every key it asks for is a keypad key.

---

## 8. Implementation status (2026-11-25)

| Area | Status |
|---|---|
| COMP, STAT (all eight types), TABLE, VERIFY | Built and unit tested. |
| CMPLX and VECTOR (FR-FX-MOD-005, Could) | Not built: they need an fx-100 series layout (FR-FX-UI-006, Could, deferred 2026-11-25). |
| SETUP, CLR, annunciators | Built and tested, including Disp (decimal comma) and CONT (contrast). SETUP page 2 is ab/c, d/c, STAT, Disp, CONT and the default is Norm 2, as the fx-82AU PLUS II and SX-II manuals give (corrected 2026-11-25). The manuals also give MthIO-LineO as the default output; CASSim keeps MathO until the emulator check (`docs/testing/emulator-scientific-capture.md`, row A7) confirms it. |
| Natural display input and exact answers | Built: fraction, mixed, √, ³√, ⁿ√, power, ×10ˣ, Abs, log■□ templates; fractions, surds with up to two terms, multiples of π; exact trigonometry at multiples of 30° and 45°. |
| Multi-statement `:` | Not built. |
| PreAns (FR-FX-MEM-004, Could) | Held as a variable; no key types it: none of the four calculators' manuals shows a PreAns key. |
| Tutorials | Twelve lessons on the fx-82 keys (eleven on the SX-II), and lessons written in the HP 10s's and EL-531's own keys; Guide, Show and Test modes; progress kept in browser storage per calculator. |
| Files, links, autosave | Built; links and files use the CASSim document envelope. Open, Save and Save as keep calculations by name in the app's storage and files are Import and Export, as in every CASSim app (changed 2026-11-25; they used to download and pick files). |
| Keyboard | Built (section 4.1). `o` is ON, so the calculator can be switched on again from the keyboard. |
| Phones (FR-FX-UI-007) | Built 2026-11-25: the calculator fills a phone's width and its keys stretch to its height (scale down to 0.4 on a landscape phone); tutorials start hidden; dialogs size to the window; Avoid cutout in the installed app. Simulated phone tests (`test_scientific_ui.py`: 360 × 640, 390 × 844, 412 × 915 and 844 × 390) check that the calculator and every dialog fit. Flet draws to a canvas, so the browser tests cannot see overflow; these layout tests stand in for them. |
| Drawing (`ui/render.py`) | √ and its vinculum are one stroke sized to the argument (a √ character and a separate line did not meet). A mixed-number answer's fraction follows its whole part directly, as in the typed entry (it had a whole character's space). |
| Calculator layouts | Built (section 4.2): fx-82 (default), SX-II, EL-531 and 10s series, from the keypad pictures in the makers' manuals (`references/`; no screenshots are kept, see `docs/design/reference/scientific/README.md`). Checked in Chrome on 2026-11-25. |
| Browser (E) verification | Checked by hand in Chrome on 2026-11-25 (layout at 1366 × 650 and 1920 × 935, keyboard input, natural display, Guide and Show modes, themes). No Playwright test yet. |
| Device verification | None of the behaviour has been compared with a physical calculator. The emulator check (`docs/testing/emulator-scientific-capture.md`) covers the fx-82AU PLUS II and SX-II: Norm thresholds, the default output, ENG on whole numbers, mixed-number display, the clearing of STAT data on leaving STAT mode and the keypad legends. The HP 10s and EL-531 sequences come from their manuals only. |
