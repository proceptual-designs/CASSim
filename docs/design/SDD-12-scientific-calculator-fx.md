# SDD-12. Scientific Calculator (CASSim fx)

Status: Design and Functional Requirements Specification for CASSim fx (Australian Curriculum Scientific Calculator: Casio fx-82AU PLUS II / fx-100AU PLUS / Abacus SX-II MATRIXn class).
Branch: `feature/cassim-fx` (worktree `C:\dev\CASSim-fx`).
Author: CASSim Team (Simon Tyler).
Conventions: Clean room boundary (decision 0028, NFR-LEG-008, NFR-LEG-009). Pure Python core, headless device profile, Flet UI rendering, Pyodide offline execution.

---

## 1. Executive Summary & Purpose

In Australian secondary mathematics (Year 7–10, VCE General Mathematics, VCE Mathematical Methods, VCE Sciences, HSC Standard Mathematics, HSC Advanced Mathematics), non-programmable, non-graphing scientific calculators are mandatory for exams or specific assessment modules where CAS devices are prohibited or unnecessary. Some of the standard classroom devices in Australia are:
1. **Casio fx-82AU PLUS II** (and 2nd edition) - the overwhelming de facto standard in Australian schools.
2. **Casio fx-100AU PLUS** - extended version with complex numbers, vectors, 40 metric conversions, and normal distribution probabilities.
3. **Abacus SX-II MATRIXn** - approved Australian curriculum equivalent manufactured by Abacus with identical functional mappings, carbon faceplate, and 2nd/ALPHA key styling.
4. **TI-30XB** - Texas Instruments Multiview calculator.
5. **HP Scientific Calculator 10s II** - Hewlett Packard scientific calculator.
6. **Sharp Scientific Calculator EL-531TH** - Sharp's advanced scientific calculator.

**CASSim fx** introduces a dedicated scientific calculator device package (`src/cassim/devices/fx`) to the CASSim multi-app browser shell. It delivers:
- An authentic, responsive handheld experience interpolating the sleek dark aesthetic of CASSim with the ergonomic familiarity of the fx-82AU / Abacus hardware.
- Full Natural Display (Natural V.P.A.M. / MthIO) rendering for fractions, radicals, exponents, and calculus templates.
- Complete Australian curriculum statistics engine conforming to the TI/school quartile convention (median-split, $n-1$ sample $s_x$, $n$ population $\sigma_x$, Pearson's $r$).
- A novel **User-Driven Interactive Tutorial Engine** that guides students through key operations (Standard Deviation, 5-Number Summary, Frequency Tables, Linear Regression, Fractions, Trigonometry) where the student actively executes each step rather than merely watching passive playback like a youtube video.

---

## 2. Clean-Room Boundary & IP Governance

Per CASSim decisions 0028, NFR-LEG-008, and NFR-LEG-009:
1. **No ROM, Firmware, or Proprietary Code**: No binary dumps or decompiled code from Casio or Abacus. The simulator is a behavioral reconstruction built from user manuals, teacher guides, syllabus requirements, and physical keyboard analysis.
2. **No Proprietary Brand Artwork or Logos**: The product is strictly **CASSim fx**. Casio, Natural V.P.A.M., and Abacus logos/trademarks are not used. Generic functional terminology is employed (e.g. "Natural Display", "MathIO / LineIO", "S⇔D Toggle").
3. **Visual Cleanliness**: The physical bezel and key shapes are original vector designs that interpolate between CASSim's Nspire-like handheld dark palette and the physical button geometries of the reference calculators.
4. **Documentation & Help**: All instructional text and tutorial explanations are original pedagogical prose written for Australian students and teachers.

---

## 3. Functional Requirements (FRs)

Priority follows MoSCoW: **M** (Must), **S** (Should), **C** (Could), **W** (Won't for initial release).
Verification: **T** (Unit/Corpus Test), **E** (Playwright E2E), **I** (Inspection), **D** (Demonstration).

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

### 3.2 Display & Mathematical Input (Natural V.P.A.M. / MthIO)

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-DSP-001** | Screen simulates authentic 2-line dot-matrix LCD display with dot matrix top input line (96×31 pixels equivalent) and bottom numeric/exact result line. | M | E, D |
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
| **FR-FX-STA-006** | Statistical variables menu (`Shift+1 (STAT)`): `1: Type`, `2: Data`, `3: Sum`, `4: Var`, `5: MinMax`, `6: Reg`. | M | T, E |

### 3.6 Interactive User-Driven Tutorial Engine

| ID | Description | MoSCoW | Verif |
|---|---|---|---|
| **FR-FX-TUT-001** | **User-Driven Execution**: The tutorial does not lock the keypad or advance on an automatic timer. The user must press the highlighted key or enter the required input on the keypad to progress. | M | E, D |
| **FR-FX-TUT-002** | **Spotlight & Hinting**: The target key illuminates with an animated pedagogical glow/accent. When a multi-key sequence is required (e.g. `Shift` then `MODE`), the immediate next key is highlighted. | M | E, D |
| **FR-FX-TUT-003** | **Validation & Error Correction**: If the student presses an incorrect key, the system provides an immediate non-punitive gentle hint (e.g., "Press [8] to enter the score, or [AC] to clear") without breaking state. | M | E, D |
| **FR-FX-TUT-004** | **Step-by-Step Explanation**: Each step displays the physical key icon, the mathematical reasoning behind the action, and the expected LCD screen appearance. | M | E, I |
| **FR-FX-TUT-005** | **Three Instructional Modes**: <br>1. *Guide Me (Interactive)*: Step-by-step user-driven execution with key highlights.<br>2. *Show Me (Demonstration)*: Automated playback fallback if a student is stuck.<br>3. *Test Me (Challenge)*: Practical problem prompt with key highlights disabled; verifies the student's final screen and result. | M | E, D |
| **FR-FX-TUT-006** | **Curriculum Catalog**: Built-in structured catalog covering Australian curricula (Year 7–10, VCE GM, VCE MM, HSC Standard/Advanced) organized by strands. | M | I |
| **FR-FX-TUT-007** | **Offline & Private**: Tutorials and student bookmarks run 100% locally in browser storage without network calls or telemetry. | M | T |

---

## 4. Hardware Keypad Layout & Physical Mapping

The physical keypad layout follows the Australian standard 50-key matrix:

```
[Row 1: Top Modifiers & D-Pad]
  [ SHIFT ]    [ ALPHA ]       [ ▲ ]         [ MODE/SETUP ]    [ ON ]
                             [◄]   [►]
                               [ ▼ ]

[Row 2: Function Keys - Top Tier]
  [ Abs ]      [ x³ ]                         [ x⁻¹ ]          [ x! ]

[Row 3: Mathematical Templates]
  [ 믐 ]       [ ³√ ]          [ x² ]         [ xⁿ ]    [ log ]   [ ln ]
  (Mixed 믐)   (ⁿ√ )          (x³)          (10ⁿ)     (eⁿ)

[Row 4: Scientific & Trig Row]
  [ (-) ]      [ ° ' " ]       [ hyp ]        [ sin ]   [ cos ]   [ tan ]
  (A)          (FACT / B)      (C)            (sin⁻¹/D) (cos⁻¹/E) (tan⁻¹/F)

[Row 5: Memory & Formatting]
  [ RCL ]      [ ENG ]         [ ( ]          [ ) ]     [ S⇔D ]   [ M+ ]
  (STO)        (←)             (%)            (,)       (a b/c)   (M-)

[Row 6: Numeric Keypad 1 & Editing]
  [ 7 ]        [ 8 ]           [ 9 ]          [ DEL ]   [ AC ]
                               (CLR)          (INS)     (OFF)

[Row 7: Numeric Keypad 2 & Operations]
  [ 4 ]        [ 5 ]           [ 6 ]          [ × ]     [ ÷ ]
                               (VERIFY)       (nPr/GCD) (nCr/LCM)

[Row 8: Numeric Keypad 3 & Advanced]
  [ 1 ]        [ 2 ]           [ 3 ]          [ + ]     [ - ]
  (STAT)                       (Pol)          (Rec)

[Row 9: Bottom Row]
  [ 0 ]        [ . ]           [ ×10ˣ ]       [ Ans ]   [ = ]
  (Rnd)        (Ran#/RanInt)   (π / e)        (DRG►)
```

---

## 5. Visual Styling & Skin Interpolation

To satisfy the user's requirement to interpolate between the current CASSim Nspire handheld and the reference hardware (Casio fx-82AU PLUS II, fx-100AU PLUS, and Abacus SX-II MATRIXn), CASSim fx defines three cohesive, switchable visual skins:

1. **CASSim fx Modern (Default)**:
   - Interpolates the dark obsidian chassis of CASSim (`#14161a` background, `#1e2229` body) with subtle matte curvature.
   - Keycaps: Deep slate function keys (`#282c35`), lighter graphite numeric keys (`#363c48`).
   - Modifiers: Warm golden-amber `SHIFT` (`#e5a93c`), vibrant rose-coral `ALPHA` (`#e05d5d`).
   - Action Keys: Elegant emerald/jade `DEL` (`#43a047`) and `AC` (`#2e7d32`).
   - Screen: High-contrast authentic LCD grey-green (`#dce5d3` background, `#10180e` active pixels) with dot-matrix text and subtle pixel shadow.
   - D-Pad: Contoured directional cross with central concave dish and metallic rim.

2. **Casio fx Heritage**:
   - Faithful recreation of the Australian classroom classic: Dark charcoal body (`#242628`).
   - High-visibility neon lime `DEL` and `AC` (`#76c043`).
   - Distinctive oval top keys (`SHIFT`, `ALPHA`, `MODE`, `ON`).

3. **Abacus Matrix Carbon**:
   - Textured micro-carbon weave faceplate.
   - Machined brushed aluminium ring around a royal navy directional D-pad.
   - Vivid primary yellow `2nd` key (`#fbc02d`), sky blue `ALPHA` (`#03a9f4`), deep cobalt `ON` (`#1565c0`), and crimson red `AC` (`#d32f2f`).

---

## 6. Architecture & Integration with CASSim Core

```
                       +-----------------------------+
                       |    CASSim Home Chooser      |
                       |  (src/cassim/app/home.py)   |
                       +--------------+--------------+
                                      |
                                      v
                       +-----------------------------+
                       |       CASSim fx Device      |
                       | (src/cassim/devices/fx/)    |
                       +--------------+--------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+-------------------------------+                       +-------------------------------+
|       Headless Engine         |                       |        UI & Flet Layer        |
| - fx/engine.py                |                       | - fx/ui/handheld.py           |
| - fx/keymap.py                |                       | - fx/ui/lcd_screen.py         |
| - fx/stat_engine.py           |                       | - fx/ui/tutorial_panel.py     |
| - fx/table_engine.py          |                       | - fx/ui/skins.py              |
+---------------+---------------+                       +---------------+---------------+
                |                                                       |
                v                                                       v
+-------------------------------+                       +-------------------------------+
|       Shared CASSim Core      |                       |     Interactive Tutorial      |
| - core/exact_math.py          |                       | - fx/tutorial/engine.py       |
| - stats/school_quartiles.py   |                       | - fx/tutorial/catalog.json    |
| - device/keys.py              |                       | - User-driven action gating   |
+-------------------------------+                       +-------------------------------+
```

The device conforms strictly to CASSim's architecture:
1. `src/cassim/devices/fx/__init__.py` exposes `DEVICE = Device("fx", "CASSim fx", ...)`.
2. Headless engine has zero imports from Flet; tested with pytest and Hypothesis.
3. Statistics engine uses pure Python and mpmath; quartiles follow the school median-split rule already agreed in CASSim decisions.
