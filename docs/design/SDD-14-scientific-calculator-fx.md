# SDD-14. Scientific Calculator (CASSim Scientific)

Status: Design and functional requirements for CASSim Scientific, a natural-display scientific calculator of the class used in Australian schools (fx-82AU PLUS II / fx-100AU PLUS / Abacus SX-II MATRIXn). Built in `src/cassim/devices/scientific/` (device id `scientific`, bundle and site `fx`). Section 8 records what is built and what is not.
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

## 3. Functional Requirements (FRs)

Priority follows MoSCoW: **M** (Must), **S** (Should), **C** (Could), **W** (Won't for initial release).
Verification: **T** (Unit/Corpus Test), **E** (Playwright E2E), **I** (Inspection), **D** (Demonstration).
The same rows are in `docs/SRS.md` section 4.12 and are traced in `docs/traceability.md`.

### 3.1 Operating Modes & System Configuration

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-MOD-001** | Support `COMP` mode (Mode 1) for general arithmetic, functions, fraction simplification, and trigonometry. | M | T, E |
| **FR-FX-MOD-002** | Support `STAT` mode (Mode 2) with 1-variable (`1: 1-VAR`) and 2-variable regression options (`2: A+BX`, `3: _+CX^2`, `4: ln X`, `5: e^X`, `6: A*B^X`, `7: A*X^B`, `8: 1/X`). | M | T, E |
| **FR-FX-MOD-003** | Support `TABLE` mode (Mode 3) for generating a table of values for $f(x)$ given Start, End, and Step parameters. | M | T, E |
| **FR-FX-MOD-004** | Support `VERIFY` mode (Mode 4 / fx-82AU submode) evaluating relational equality/inequality expressions to `TRUE` or `FALSE`. | S | T, E |
| **FR-FX-MOD-005** | (fx-100 extension) Support `CMPLX` mode (Complex numbers $a+bi$ and $r\angle\theta$) and `VECTOR` mode (2D/3D vectors). | C | T |
| **FR-FX-CFG-001** | Support Setup selection of display format: `MthIO` (MathO natural output or LineO linear output) vs `LineIO`. | M | T, E |
| **FR-FX-CFG-002** | Support Angle unit configuration: Degrees (`Deg`), Radians (`Rad`), Gradians (`Gra`). Active unit indicated on screen annunciator. | M | T, E |
| **FR-FX-CFG-003** | Support Numerical display rounding modes: `Norm 1` / `Norm 2` (exponential threshold), `Fix 0..9` (fixed decimal places), `Sci 0..9` (scientific significant figures). | M | T, E |
| **FR-FX-CFG-004** | Support Fraction result format: Mixed number $a\frac{b}{c}$ vs Improper fraction $\frac{d}{c}$. | M | T, E |
| **FR-FX-CFG-005** | Support `STAT` frequency table toggle in Setup (`Shift+MODE` $\to$ `▼` $\to$ `STAT` $\to$ `1: ON`, `2: OFF`). | M | T, E |
| **FR-FX-CFG-006** | Support Initialisation/Reset via `Shift+9 (CLR)` with options: `1: Setup`, `2: Memory`, `3: All`. Reset restores factory defaults and clears memories. | M | T, E |

### 3.2 Display & Mathematical Input (Natural Display / MthIO)

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-DSP-001** | Screen simulates a two-line LCD: a natural-display input line and an answer line, with the whole calculator scaled to fit the window. | M | E, D |
| **FR-FX-DSP-002** | Render top annunciator status icons: `S` (Shift), `A` (Alpha), `M` (Independent memory active), `STO` (Store), `RCL` (Recall), `STAT` (Stat mode), `D`/`R`/`G` (Angle unit), `FIX` (Fixed d.p.), `SCI` (Scientific), `Math` (MthIO active), `▲▼` (Replay history available). | M | E, I |
| **FR-FX-DSP-003** | Natural input editing: fractions $\frac{\Box}{\Box}$, mixed numbers $\Box\frac{\Box}{\Box}$, square root $\sqrt{\Box}$, cube root $\sqrt[3]{\Box}$, $n$-th root $\sqrt[\Box]{\Box}$, power $x^\Box$, absolute value $\|\Box\|$, logarithmic with base $\log_{\Box}(\Box)$. | M | T, E |
| **FR-FX-DSP-004** | 4-way D-pad navigation: cursor movement through slots and nested templates, history navigation (`▲`/`▼`), and multi-statement browsing. | M | T, E |
| **FR-FX-DSP-005** | `S⇔D` button toggles result between exact symbolic form (surd, $\pi$-multiple, exact fraction) and decimal representation. | M | T, E |
| **FR-FX-DSP-006** | `Shift + S⇔D` toggles between mixed number ($a\frac{b}{c}$) and improper fraction ($\frac{d}{c}$). | M | T, E |
| **FR-FX-DSP-007** | `ENG` key adjusts decimal exponent down by 3 ($10^{-3}, 10^{-6}$); `Shift + ENG` ($\leftarrow$) adjusts exponent up by 3 ($10^3, 10^6$). | M | T |
| **FR-FX-DSP-008** | DMS key (`° ' "`) inputs sexagesimal angles and converts decimal degrees to degrees, minutes, and seconds on result. | M | T |
| **FR-FX-DSP-009** | `Shift + ° ' "` (`FACT`) performs prime factorisation of integer results (e.g. $1050 \to 2 \times 3 \times 5^2 \times 7$). | M | T |

### 3.3 Memory Registers

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-MEM-001** | Automatic `Ans` register stores the result of the last completed calculation and updates on `=`. | M | T |
| **FR-FX-MEM-002** | 9 variable registers: `A, B, C, D, E, F, M, X, Y`. Stored via `Shift+RCL (STO)` + variable key; recalled via `RCL` + key or typed via `ALPHA` + key in expressions. | M | T |
| **FR-FX-MEM-003** | Independent memory `M`: `M+` adds current value to $M$; `Shift+M+ (M-)` subtracts current value from $M$. Annunciator `M` lights when $M \ne 0$. | M | T |
| **FR-FX-MEM-004** | (fx-100 extension) `PreAns` memory holds the second-to-last answer for recurrence relations. | C | T |

### 3.4 Scientific & Syllabus Mathematical Functions

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-FNC-001** | Standard trigonometry: $\sin, \cos, \tan$ and inverses $\sin^{-1}, \cos^{-1}, \tan^{-1}$ respecting active angle unit (`Deg`, `Rad`, `Gra`). | M | T |
| **FR-FX-FNC-002** | Hyperbolic functions via `hyp`: $\sinh, \cosh, \tanh, \sinh^{-1}, \cosh^{-1}, \tanh^{-1}$. | M | T |
| **FR-FX-FNC-003** | Powers and roots: $x^2, x^3, x^{-1}, x^y, \sqrt{\Box}, \sqrt[3]{\Box}, \sqrt[y]{x}$. | M | T |
| **FR-FX-FNC-004** | Logarithms and exponentials: natural $\ln, e^x$, common $\log, 10^x$, and arbitrary base $\log_a(b)$. | M | T |
| **FR-FX-FNC-005** | Combinatorics & Probability: Permutations $n\text{Pr}$, Combinations $n\text{Cr}$, Factorial $n!$, Random decimal $\text{Ran\#} \in [0, 1)$, Random integer $\text{RanInt\#}(a, b) \in [a, b]$. | M | T |
| **FR-FX-FNC-006** | Coordinate conversions: $\text{Pol}(x, y)$ returns $(r, \theta)$ with $r$ in $X$ and $\theta$ in $Y$; $\text{Rec}(r, \theta)$ returns $(x, y)$. | M | T |
| **FR-FX-FNC-007** | Number theory: $\text{GCD}(a, b)$ (Greatest Common Divisor) and $\text{LCM}(a, b)$ (Least Common Multiple). | M | T |
| **FR-FX-FNC-008** | Percent calculations (`%`): basic percent, percentage increase, percentage decrease. | M | T |
| **FR-FX-FNC-009** | Rounding function `Rnd(x)`: rounds argument to current display precision (`Fix` or `Sci`). | M | T |

### 3.5 Australian School Statistics Engine

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-STA-001** | Data entry grid: 1-VAR single column (or two-column with FREQ enabled); 2-VAR bivariate two-column (X, Y) (or three-column with FREQ). | M | T, E |
| **FR-FX-STA-002** | Single-variable summary statistics: $n, \bar{x}, \sum x, \sum x^2, s_x, \sigma_x$. | M | T |
| **FR-FX-STA-003** | 5-number summary: $\min X, Q_1, \text{med}, Q_3, \max X$. Quartiles strictly computed using TI/Australian school median-split convention (median excluded when $n$ is odd). | M | T |
| **FR-FX-STA-004** | Bivariate linear regression: $y = A + Bx$, calculating $A$ (intercept), $B$ (gradient), Pearson's correlation coefficient $r$. | M | T |
| **FR-FX-STA-005** | Regression estimation: predicting $\hat{x}$ for given $y$, and $\hat{y}$ for given $x$. | M | T |
| **FR-FX-STA-006** | Statistical variables menu (`Shift+1 (STAT)`): `1: Type`, `2: Data`, `3: Sum`, `4: Var`, `5: MinMax`, `6: Reg` (Reg for two-variable types only). | M | T, E |

### 3.6 Interactive User-Driven Tutorial Engine

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-TUT-001** | **User-Driven Execution**: The tutorial does not lock the keypad or advance on an automatic timer. The user must press the highlighted key or enter the required input on the keypad (or the computer keyboard) to progress. | M | E, D |
| **FR-FX-TUT-002** | **Spotlight & Hinting**: The target key is outlined with a calm accent glow. When a multi-key sequence is required (e.g. `Shift` then `MODE`), the immediate next key is highlighted. | M | E, D |
| **FR-FX-TUT-003** | **Validation & Error Correction**: If the student presses an incorrect key, the system gives an immediate non-punitive hint naming the right key, and the wrong key does not change the calculator. | M | E, D |
| **FR-FX-TUT-004** | **Step-by-Step Explanation**: Each step shows the key to press, the reason for it, and what the screen should then show (computed by running the lesson, never written by hand). | M | E, I |
| **FR-FX-TUT-005** | **Three Instructional Modes**: <br>1. *Guide Me (Interactive)*: Step-by-step user-driven execution with key highlights.<br>2. *Show Me (Demonstration)*: Automated playback at 0.5×–2× for a stuck student or a whiteboard.<br>3. *Test Me (Challenge)*: Practical problem prompt with key highlights disabled; verifies the student's final screen and result. | M | E, D |
| **FR-FX-TUT-006** | **Offline & Private**: Tutorials and student progress run 100% locally in browser storage without network calls or telemetry. | M | T |

### 3.7 Browser Persistence & URL State Sharing

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-SHR-001** | **Automatic Browser Persistence**: Calculator state is saved to browser storage (the shell's storage, under the device prefix `scientific.`) shortly after each key press. On reload the mode, settings, variables, STAT data, table and recent history are restored. A tutorial never overwrites the student's own saved work. | M | T, E |
| **FR-FX-SHR-002** | **URL Fragment State Sharing**: The calculator is serialised as a CASSim document naming the device, compressed with zlib and URL-safe Base64 into the shared `#/doc=` fragment (decision 0032 item 4). Loading a share link recreates the calculator; the shell routes it to CASSim Scientific by its `device`. | M | T, E |
| **FR-FX-SHR-003** | **Privacy by Construction**: The shared state payload resides strictly in the URL fragment (`#...`), which web browsers never send to an HTTP server (NFR-SEC-001). No student data or teacher problem data is ever uploaded or logged. A link holds key names and numbers only; nothing in it is executed. | M | I, T |
| **FR-FX-SHR-004** | **Compact Link Budget**: A typical calculator link is 80–300 characters, well within the 2,000-character ceiling (`MAX_FRAGMENT`); history is left out of links and default settings are omitted. | M | T |
| **FR-FX-SHR-005** | **Teacher Pre-Populated Problem Sets**: Teachers can share a single link that pre-loads a data set (e.g. a 25-row bivariate table) or a TABLE-mode function, so students begin solving immediately. | S | D, E |
| **FR-FX-SHR-006** | **Named State Snapshots**: Users can save and open named `.cassim.json` files (Doc ▸ Save, Save as, Open), the one CASSim file format (FR-DOC-006). | S | T, E |

### 3.8 Shell integration and keyboard (added 2026-11-25)

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-UI-001** | **Top bar**: the CASSim and Doc menus of every CASSim app (section 5.1) and status chips for the mode, angle unit and input mode, readable in every theme. Clicking a chip opens MODE, changes the angle unit, or switches MthIO/LineIO. | M | T, E |
| **FR-FX-UI-002** | **Presentation mode**: the top bar can be hidden; a floating button or Esc brings it back. | S | T, E |
| **FR-FX-UI-003** | **Tutorial panel**: quiet styling, a step counter, the instruction and reason, the expected screen, and a close button; it sits beside the calculator, or below it when the window is narrow. | S | T, D |
| **FR-FX-UI-004** | **Computer keyboard**: every key can be reached from the computer keyboard (section 4.1): digits and operators directly, common functions by letter, SHIFT and ALPHA as F1 and F2, MODE as Ctrl+M. Each keypad key's tooltip names its shortcut, and CASSim ▸ Keyboard shortcuts lists them. Keyboard input is ignored while a dialog is open. | M | T, E |
| **FR-FX-UI-005** | **Calculator layouts**: CASSim ▸ Appearance ▸ Calculator shows the keys of a chosen class of school calculator (Casio fx-82 series, the default; Abacus SX-II series; Sharp EL-531 series; HP 10s series): their names, legends, SHIFT and ALPHA key names and arrangement, in CASSim's own artwork and fonts. The calculator behind the keys is the same. A layout lists only the modes that calculator has, a linear-display calculator switches SETUP to LineIO, and lessons name and highlight the chosen keys (a lesson needing a missing mode or key uses the fx-82 keys and says so). The choice is remembered. | S | T, E |

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
| < > | relations |
| Ctrl+C | copy the answer |

Tab is deliberately unbound: it moves the browser's focus, and Enter would then also press the focused button. The keypad keys are not focusable for the same reason. Only the non-typing shortcuts are listed in the device profile (`Profile.computer`), which the published page uses to keep them from the browser (`tools/publish.py`).

---

### 4.2 Calculator layouts (FR-FX-UI-005; `layouts.py`)

A layout is data: rows of keys, each with its face, its legends and, for each layer (plain, after SHIFT, after ALPHA), the canonical key sequence it stands for. Pressing a layout key sends that sequence to the one device state, so the engine, the keyboard map and the tutorials are shared. Three pseudo-keys serve keys only some calculators have: `TOK:<token>` types a statistics variable printed on a key, `STATSUB:<n>` opens item n of the STAT menu (the 10s's S-SUM and S-VAR), and `DATA` adds the entry as a STAT data row (the EL-531's DATA and the 10s's DT; M+ outside STAT). Layouts follow each class's arrangement and key names closely but not exactly.

| | Casio fx-82 series | Abacus SX-II series | Sharp EL-531 series | HP 10s series |
|---|---|---|---|---|
| SHIFT / ALPHA keys | SHIFT, ALPHA | 2nd, ALPHA | 2ndF, ALPHA | SHIFT, ALPHA |
| Display | natural | natural ("Math") | two-line linear | two-line linear |
| Modes listed | COMP, STAT, TABLE, VERIFY | COMP, STAT, VERIFY | COMP, STAT | COMP, STAT |
| Exact/decimal key | S⇔D | F↔D | none (a b/c, d/c) | none (a b/c, d/c) |
| STAT data entry | table editor | table editor | DATA key (and the table) | DT key (and the table) |
| Not on the keys | — | TABLE | TABLE, VERIFY, FACT, S⇔D | TABLE, VERIFY, FACT, S⇔D, MinMax, Reg |
| On the keys but not in CASSim Scientific | — | — | base-n conversions, logic operations, MDF-like functions beyond Rnd | — |

Older fx-82 models (fx-82MS) have a linear display and no VERIFY or TABLE; the fx-82 layout follows the natural-display models. The 10s's quartile, MinMax and regression menus are not reachable from its keys (its S-VAR key opens CASSim's Var menu). Lessons that need something a layout lacks run on the fx-82 keys (tests list which).

---

## 5. Visual Styling & Original CASSim Themes

To avoid trade dress mimicry, CASSim Scientific does **not** reproduce physical hardware shells, branded badges, or proprietary manufacturing finishes. It keeps the functional 50-key layout and applies CASSim's own flat design. The themes use CASSim's names, so Appearance works as in the other apps (`ui/skins.py`):

1. **CASSim Slate (Dark, the default)**: chassis `#1e2229`; function keys `#282c35` with `#f0f2f5` labels; number keys `#363c48`; SHIFT amber `#e5a93c` and ALPHA coral (`#ef7b7b`, lighter than the first draft's `#e05d5d` for contrast on the dark body); DEL and AC emerald `#43a047` / `#2e7d32`; sage LCD `#dce5d3` with `#121810` characters.
2. **Classroom high contrast**: charcoal chassis `#121316` with white keys and black labels; AC `#c62828`, DEL `#37474f`; paper LCD `#f4f6f8` with black characters. The legends above the keys sit on the dark body, so they are light gold `#ffb020` and light blue `#7cc0ff`; the draft's `#d48800` and `#0050b3` are used where they sit on white (the SHIFT and ALPHA key labels).
3. **Studio Light**: chassis `#e9ecef` with a `#ced4da` edge; function keys `#495057`, number keys `#f8f9fa`; LCD `#e8edf2` with `#1a202c` characters.

The badge on every theme reads **`CASSim Scientific`** with the subtitle **`NATURAL DISPLAY`**. The LCD uses Roboto Mono (bundled), whose fixed character width lets fraction bars and scrolling be laid out without measuring text; symbols fall back to the bundled Noto fonts so nothing is fetched at run time.

The calculator scales to the window (between 0.7× and 1.3× of a 360 × 700 design) so every key is visible on a Chromebook screen; below 0.7× the page scrolls. The tutorial panel moves under the calculator when the window is too narrow for both.

### 5.1 Top Navigation Bar & Presentation Mode (CASSim Consistency)

1. **Top bar (FR-FX-UI-001)**:
   - **CASSim menu**: Home, Settings… (the SETUP choices as a form), Appearance…, Keyboard shortcuts…, Check for updates, Help (wiki)…, About CASSim….
   - **Doc menu**: Open…, Save, Save as…, Share link…, Examples ▸ (standard deviation, five-number summary, linear regression, table of values, mixed numbers, exact trigonometry, degrees-minutes-seconds, prime factorisation), Reset all… (asks first).
   - **Status chips**: mode, angle unit, input mode; clickable.
2. **Presentation mode (FR-FX-UI-002)**: the full-screen button hides the bar; a floating button or Esc restores it.
3. **Tutorial panel (FR-FX-UI-003)**: lesson list (completed lessons ticked), Guide me / Show me / Test me, playback speed, step counter, instruction and reason, next-key chip, expected screen, keys so far, Back / Skip step / Restart / End. The student's own calculation is put aside when a lesson starts and comes back when it ends.

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
| CMPLX and VECTOR (FR-FX-MOD-005, Could) | Not built. |
| SETUP, CLR, annunciators | Built and tested. Contrast (CONT) and the decimal-comma Disp setting are not built. |
| Natural display input and exact answers | Built: fraction, mixed, √, ³√, ⁿ√, power, ×10ˣ, Abs, log■□ templates; fractions, surds with up to two terms, multiples of π; exact trigonometry at multiples of 30° and 45°. |
| Multi-statement `:` | Not built. |
| PreAns (FR-FX-MEM-004, Could) | Held as a variable; no key types it (the fx-82AU layout has none). |
| Tutorials | Twelve lessons with Guide, Show and Test modes; progress kept in browser storage. |
| Files, links, autosave | Built; links and files use the CASSim document envelope. |
| Keyboard | Built (section 4.1). |
| Calculator layouts | Built (section 4.2): fx-82 (default), SX-II, EL-531 and 10s series, from the makers' keypad pictures. Checked in Chrome on 2026-11-25. |
| Browser (E) verification | Checked by hand in Chrome on 2026-11-25 (layout at 1366 × 650 and 1920 × 935, keyboard input, natural display, Guide and Show modes, themes). No Playwright test yet. |
| Device verification | None of the behaviour has been compared with a physical calculator. In particular Norm thresholds, the order of SETUP page 2, ENG on whole numbers, mixed-number display and the clearing of STAT data on leaving STAT mode follow this document and should be checked against a real device. |
