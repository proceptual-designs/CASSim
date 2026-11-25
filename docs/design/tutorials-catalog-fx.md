# CASSim fx: Built-in Interactive Tutorials Catalog

Status: The lesson plan for the CASSim fx tutorial engine. Twelve lessons are built (`src/cassim/devices/scientific/tutorials.py`; SDD-14 section 7); the answers below were checked by running them on CASSim fx (2026-11-25), and the tests keep them in step.
Curriculum Alignment: Australian Curriculum Mathematics (Years 7–10), VCE General Mathematics (Units 1–4), VCE Mathematical Methods (Units 1–2), HSC Standard Mathematics (Stages 6), HSC Advanced Mathematics.
Core Reference: How-Do-I...fx82-and-fx-100AU Guide, Casio fx-82AU PLUS II User's Guide, Abacus SX-II MATRIXn Manual, and "How To Maths" HSC Standard Calculator Skills.

---

## 1. Pedagogical Architecture: User-Driven vs Passive Playback

Walkthroughs that lock the keypad and press the keys on a timer leave the student watching. 

In classroom practice, passive observation fails to develop calculator fluency and muscle memory. **CASSim fx introduces the User-Driven Tutorial Engine**:

```
+-------------------------------------------------------------------------------+
| TUTORIAL STATE MACHINE                                                        |
|                                                                               |
| [Select Lesson] --> [Apply Initial Setup: Reset / Deg / MthIO / Freq]         |
|        |                                                                      |
|        v                                                                      |
| [Step N: Show Instruction & Pedagogical Note]                                 |
|        |                                                                      |
|        +--> Spotlight Key: Glow on Target Keycap                              |
|        |                                                                      |
|        +--> Listen for User Event on Keypad (User is NOT locked out!)        |
|                 |                                                             |
|                 +---> [Correct Key Pressed]                                   |
|                 |         * Play key sound & depress animation                |
|                 |         * Update LCD screen state                           |
|                 |         * Show positive reinforcement                       |
|                 |         * Advance to Step N+1                               |
|                 |                                                             |
|                 +---> [Incorrect Key Pressed]                                 |
|                           * Gentle non-destructive pulse                      |
|                           * Show contextual hint: "Look for key [X] above [Y]"|
|                           * Retain state until correct key is pressed         |
+-------------------------------------------------------------------------------+
```

### Instructional Modes
1. **Guide Me (Interactive User-Driven - Default)**: The student presses every key. Target keys glow. Wrong presses give gentle hints.
2. **Show Me (Demonstration Fallback)**: If a student is stuck or a teacher is presenting on an interactive whiteboard, the lesson can play automatically with adjustable speed (0.5×, 1×, 1.5×, 2×).
3. **Test Me (Challenge Mode)**: Gives the student a problem (e.g. "Calculate the sample standard deviation $s_x$ for $\{4, 7, 11, 15, 18\}$"). Key glowing is disabled. The engine evaluates the student's final LCD screen and result to award a completion badge.

---

## 2. Priority 1: YouTube Playlist ("HSC Standard Maths Calculator Skills")

These 6 core tutorials form the flagship interactive starter pack, covering the highest-frequency requirements in VCE General Maths and HSC Standard Maths examinations:

### Tutorial YT-1: Resetting & Initialising the Calculator
- **Curriculum Context**: Start of every examination and diagnostic task. Ensures no residual memories ($M$, variables $A$–$F$) or incorrect angle/stat modes distort calculations.
- **Initial Setup**: Any dirty state ($M$ active, Radian mode, Stat mode).
- **Target Steps**:
  1. `[SHIFT]`: Activate the secondary function layer. (Annunciator `S` appears).
  2. `[ 9 ]` (`CLR`): Open the Clear menu on screen (`1: Setup`, `2: Memory`, `3: All`).
  3. `[ 3 ]` (`All`): Select Option 3 to reset everything. (Screen prompts: `Reset All? [=] : Yes, [AC] : Cancel`).
  4. `[ = ]`: Confirm reset. (Screen displays: `Reset All, Press [AC] key`).
  5. `[ AC ]`: Return to default calculation screen (`COMP` mode, `D` degrees, `Math` natural display).
- **Expected Final Display**: Blank top line with blinking cursor, `D` and `Math` annunciators active.

### Tutorial YT-2: Enabling the Frequency Table in Setup
- **Curriculum Context**: Grouped data analysis and frequency distributions. By default, Casio calculators ship with the frequency column turned OFF.
- **Initial Setup**: Factory default (Frequency OFF).
- **Target Steps**:
  1. `[SHIFT]`: Activate setup layer.
  2. `[ MODE ]` (`SETUP`): Open Setup menu page 1 (`1: MthIO`, `2: LineIO`, `3: Deg`, etc.).
  3. `[ ▼ ]` (D-Pad Down): Scroll to Setup menu page 2 (`1: STAT`, `2: TABLE`, `3: Disp`, `4: CONT`).
  4. `[ 1 ]` (`STAT`): Select Statistics configuration (`Frequency? 1: ON, 2: OFF`).
  5. `[ 1 ]` (`ON`): Turn frequency table ON. Calculator returns to normal screen.
- **Pedagogical Note**: "Turning Frequency ON allows you to enter data tables where scores repeat, saving hours of manual data entry."

### Tutorial YT-3: Single-Variable Mean and Standard Deviation ($s_x$ vs $\sigma_x$)
- **Curriculum Context**: VCE General Maths Data Analysis; HSC Standard Maths Statistical Analysis.
- **Problem**: Calculate the mean and sample standard deviation for scores: $12, 15, 18, 22, 25$.
- **Target Steps**:
  1. `[ MODE ]`: Open Mode menu (`1: COMP`, `2: STAT`, `3: TABLE`).
  2. `[ 2 ]`: Enter `STAT` mode. (Screen displays list of types: `1: 1-VAR`, `2: A+BX`, etc.).
  3. `[ 1 ]`: Choose `1-VAR`. Data entry grid opens with column `X`.
  4. `[ 1 ]` `[ 2 ]` `[ = ]`: Enter 12 into row 1.
  5. `[ 1 ]` `[ 5 ]` `[ = ]`: Enter 15 into row 2.
  6. `[ 1 ]` `[ 8 ]` `[ = ]`: Enter 18 into row 3.
  7. `[ 2 ]` `[ 2 ]` `[ = ]`: Enter 22 into row 4.
  8. `[ 2 ]` `[ 5 ]` `[ = ]`: Enter 25 into row 5.
  9. `[ AC ]`: Exit data grid to calculation screen (data remains safely in memory; annunciator `STAT` remains lit).
  10. `[SHIFT]` `[ 1 ]` (`STAT`): Open Statistics calculation menu (`1: Type`, `2: Data`, `3: Sum`, `4: Var`, `5: MinMax`).
  11. `[ 4 ]` (`Var`): Select Variables menu (`1: n`, `2: x̄`, `3: σx`, `4: sx`).
  12. `[ 2 ]` (`x̄`): Select Mean. Screen shows `x̄`.
  13. `[ = ]`: Compute mean. **Result**: `18.4`.
  14. `[SHIFT]` `[ 1 ]` `[ 4 ]`: Re-open Var menu.
  15. `[ 4 ]` (`sx`): Select Sample Standard Deviation.
  16. `[ = ]`: Compute sample SD. **Result**: `5.224940191`.
- **Pedagogical Highlight**: Emphasises the critical difference between $s_x$ ($n-1$, sample SD used in VCE/HSC) and $\sigma_x$ ($n$, population SD).

### Tutorial YT-4: Generating a Five-Number Summary
- **Curriculum Context**: Boxplot construction in General Maths and Year 10 5.2/5.3.
- **Data**: $4, 7, 9, 12, 14, 18, 21, 25$.
- **Target Steps**:
  1. `[ MODE ]` `[ 2 ]` `[ 1 ]`: Open 1-VAR data grid.
  2. Enter numbers: `4 = 7 = 9 = 12 = 14 = 18 = 21 = 25 =`.
  3. `[ AC ]`: Store data.
  4. `[SHIFT]` `[ 1 ]`: Open STAT menu.
  5. `[ 5 ]` (`MinMax`): Open MinMax menu (`1: minX`, `2: maxX`, `3: Q1`, `4: med`, `5: Q3`).
  6. Inspect each value, opening the menu again each time (`[SHIFT]` `[ 1 ]` `[ 5 ]`):
     - `[ 1 ]` `[ = ]`: $\min X = 4$
     - `[ 3 ]` `[ = ]`: $Q_1 = 8$ (TI/Australian school median-split: lower half $\{4, 7, 9, 12\}$, median is $\frac{7+9}{2} = 8$).
     - `[ 4 ]` `[ = ]`: $\text{med} = 13$
     - `[ 5 ]` `[ = ]`: $Q_3 = 19.5$ (upper half $\{14, 18, 21, 25\}$, median is $\frac{18+21}{2} = 19.5$).
     - `[ 2 ]` `[ = ]`: $\max X = 25$.

### Tutorial YT-5: Frequency Table Statistics
- **Curriculum Context**: Discrete frequency tables (e.g. number of siblings, test scores).
- **Data Table**:
  - Score ($X$): $1, 2, 3, 4$
  - Frequency ($FREQ$): $5, 12, 8, 3$
- **Target Steps**:
  1. Ensure Frequency is ON (via Tutorial YT-2).
  2. `[ MODE ]` `[ 2 ]` `[ 1 ]`: Open 1-VAR table with `X` and `FREQ` columns.
  3. Enter $X$ values: `1 = 2 = 3 = 4 =`.
  4. Use D-pad `[ ▲ ]` four times, then `[ ► ]`, to move to the top of the `FREQ` column (after the fourth value the cursor is on the empty fifth row).
  5. Enter frequencies: `5 = 12 = 8 = 3 =`.
  6. `[ AC ]` `[SHIFT]` `[ 1 ]` `[ 4 ]` `[ 1 ]` `[ = ]`: Check sample size $n = 28$.
  7. `[SHIFT]` `[ 1 ]` `[ 4 ]` `[ 2 ]` `[ = ]`: Check mean $\bar{x} = 2.3214...$.

### Tutorial YT-6: Bivariate Correlation Coefficient ($r$) and Linear Regression
- **Curriculum Context**: VCE General Maths Bivariate Data; HSC Standard Maths Financial Modelling.
- **Problem**: Find the equation of the least-squares regression line $y = A + Bx$ and Pearson's correlation coefficient $r$ for pairs: $(2, 5), (4, 9), (6, 12), (8, 17), (10, 20)$.
- **Target Steps**:
  1. `[ MODE ]` `[ 2 ]`: Open STAT mode.
  2. `[ 2 ]` (`A+BX`): Select Linear Regression mode. Screen shows `X` and `Y` columns.
  3. Enter $X$ column: `2 = 4 = 6 = 8 = 10 =`.
  4. Navigate to $Y$ column, enter: `5 = 9 = 12 = 17 = 20 =`.
  5. `[ AC ]`: Return to calculation screen.
  6. `[SHIFT]` `[ 1 ]`: Open STAT menu. Note that item `[ 6 ]` (`Reg`) is now active!
  7. `[ 6 ]` (`Reg`): Opens Regression menu (`1: A`, `2: B`, `3: r`, `4: x̂`, `5: ŷ`).
  8. `[ 3 ]` (`r`) `[ = ]`: Compute Pearson's $r$. **Result**: `0.9972...` (very strong positive linear relationship).
  9. `[SHIFT]` `[ 1 ]` `[ 6 ]` `[ 1 ]` `[ = ]`: Intercept $A = 1.2$.
  10. `[SHIFT]` `[ 1 ]` `[ 6 ]` `[ 2 ]` `[ = ]`: Slope $B = 1.9$. Line is $y = 1.2 + 1.9x$.
  11. Prediction: Predict $y$ when $x = 7$:
      - Type `7` `[SHIFT]` `[ 1 ]` `[ 6 ]` `[ 5 ]` (`ŷ`) `[ = ]`. **Result**: `14.5`.

---

## 3. Comprehensive Curriculum Strands (64 Interactive Lessons)

Organized into 10 structured progressive modules:

### Strand 1: Getting Started & Calculator Configuration (Lessons 1–6)
1. **Power, Contrast & Display**: Turning ON/OFF, adjusting dot-matrix contrast via Setup.
2. **Calculator Initialization**: `Shift+9 (CLR)` - resetting Setup, Memory, or All.
3. **MthIO vs LineIO**: Natural display format vs linear single-line entry.
4. **Angle Modes**: Degrees (`Deg`), Radians (`Rad`), Gradians (`Gra`).
5. **Rounding Modes**: `Fix` (fixed decimal places 0–9) and `Sci` (scientific sig-figs).
6. **Exponential Display**: `Norm 1` (scientific notation for $< 10^{-2}$ or $\ge 10^{10}$) vs `Norm 2` ($< 10^{-9}$).

### Strand 2: Fractions, Decimals & Basic Arithmetic (Lessons 7–14)
7. **Basic Natural Entry**: Using brackets, negative key `[(-)]` vs subtraction `[-]`.
8. **Entering Fractions**: The fraction template `[■/□]`, navigating numerator and denominator with D-Pad.
9. **Fractions & Decimals Toggle**: Converting answers between exact surd/fraction and decimal using `[S⇔D]`.
10. **Mixed Numbers**: Entering $a\frac{b}{c}$ using `[SHIFT] + [■/□]`.
11. **Improper Fraction Toggle**: `[SHIFT] + [S⇔D]` ($a\frac{b}{c} \Leftrightarrow \frac{d}{c}$).
12. **Percentages**: Calculating percentages with `[SHIFT] + [(]` (`%`).
13. **Percentage Increase & Decrease**: Markup and discount calculations.
14. **Multi-Statements**: Separating calculations with colon `:` (`[ALPHA] + [x³]`).

### Strand 3: Powers, Roots & Number Theory (Lessons 15–23)
15. **Squares and Cubes**: `[x²]` and `[x³]` keys.
16. **Higher Powers**: Using `[xⁿ]` with negative and fractional exponents.
17. **Square Roots and Cube Roots**: `[√]` and `[SHIFT] + [√]` (`³√`).
18. **General $n$-th Root**: `[SHIFT] + [xⁿ]` (`ⁿ√`).
19. **Reciprocal Key**: `[x⁻¹]` for rates and unit fractions.
20. **Scientific Notation**: Entering large/small numbers with `[×10ˣ]`.
21. **Engineering Notation**: `[ENG]` and `[SHIFT] + [ENG]` ($\leftarrow$).
22. **Prime Factorisation**: `[SHIFT] + [° ' "]` (`FACT`) on integer results.
23. **Greatest Common Divisor (GCD) & Lowest Common Multiple (LCM)**: `[ALPHA] + [×]` (`GCD`) and `[ALPHA] + [÷]` (`LCM`).

### Strand 4: Angles, Trigonometry & Coordinates (Lessons 24–31)
24. **Degrees, Minutes, Seconds (DMS)**: Entering angles with `[° ' "]`.
25. **Decimal to DMS Conversion**: Toggling between decimal degrees and sexagesimal format.
26. **Right-Angled Trigonometry**: Evaluating $\sin$, $\cos$, $\tan$ in degrees.
27. **Inverse Trigonometric Functions**: $\sin^{-1}$, $\cos^{-1}$, $\tan^{-1}$ using `[SHIFT]`.
28. **Trig in Radians**: Exact values ($\sin(30^\circ) = \frac{1}{2}$, $\sin(\frac{\pi}{6})$ in Rad mode).
29. **Angle Unit Override**: Overriding active unit using `[SHIFT] + [Ans]` (`DRG►`).
30. **Polar to Rectangular Coordinates**: `Rec(r, θ)` via `[SHIFT] + [-]`.
31. **Rectangular to Polar Coordinates**: `Pol(x, y)` via `[SHIFT] + [+]`.

### Strand 5: Memory Registers & Recurrence (Lessons 32–37)
32. **Answer Memory (`Ans`)**: Reusing intermediate results in chained calculations.
33. **Repeated Recurrence**: Compounding with `Ans` (e.g. `Ans × 1.05 - 200 = = =`).
34. **Letter Memories ($A, B, C, D, E, F, X, Y$)**: Storing via `[SHIFT] + [RCL]` (`STO`) and recalling via `[RCL]`.
35. **Using Variables in Formulas**: Typing variables with `[ALPHA]`.
36. **Independent Memory ($M$)**: `[M+]` and `[SHIFT] + [M+]` (`M-`).
37. **Clearing Memories**: Resetting variables without altering calculator setup.

### Strand 6: Single-Variable Statistics (Lessons 38–44)
38. **Entering Raw Data**: `STAT` $\to$ `1-VAR`.
39. **Editing & Correcting Data**: Replacing entries, deleting rows (`[DEL]`), inserting data.
40. **Summary Statistics**: Calculating sample size $n$, mean $\bar{x}$, sums $\sum x, \sum x^2$.
41. **Standard Deviation**: Distinguishing $s_x$ (sample) and $\sigma_x$ (population).
42. **Five-Number Summary**: $\min X, Q_1, \text{med}, Q_3, \max X$.
43. **Frequency Table Statistics**: Activating Frequency column in Setup and computing weighted statistics.
44. **Grouped Data Class Intervals**: Entering class midpoints into $X$ with frequencies.

### Strand 7: Bivariate Data & Linear Regression (Lessons 45–50)
45. **Bivariate Data Entry**: Selecting `STAT` $\to$ `2: A+BX`.
46. **Scatterplot Trend Analysis**: Inspecting covariance and sums $\sum xy, \sum y$.
47. **Pearson's Correlation Coefficient ($r$)**: Extracting $r$ from the `Reg` menu.
48. **Least-Squares Regression Line**: Determining intercept $A$ and slope $B$.
49. **Interpolation & Extrapolation ($\hat{y}$)**: Predicting dependent variable value for given $x$.
50. **Inverse Prediction ($\hat{x}$)**: Estimating independent variable for target $y$.

### Strand 8: Table Mode & Function Evaluation (Lessons 51–55)
51. **Generating a Table of Values**: Mode `TABLE`, entering $f(x)$ with `[ALPHA] + [ ) ]` (`X`).
52. **Configuring Start, End, Step**: Setting interval bounds and step increments.
53. **Finding Roots with Table Mode**: Locating sign changes in $f(x)$ to isolate roots.
54. **Modelling Arithmetic Sequences**: Generating linear progression tables.
55. **Modelling Geometric Sequences & Compound Interest**: Tables of exponential growth.

### Strand 9: Verification, Probability & Advanced Functions (Lessons 56–60)
56. **VERIFY Mode**: Inputting equality/inequality statements with relational operators (`=, ≠, >, ≥, <, ≤`).
57. **Random Numbers ($\text{Ran\#}$)**: Generating uniform random decimals in $[0, 1)$ to 3 d.p.
58. **Random Integers ($\text{RanInt\#}$)**: Generating dice rolls and lottery numbers with `RanInt#(1, 6)`.
59. **Permutations ($n\text{Pr}$) & Factorials ($n!$)**: Counting arrangements.
60. **Combinations ($n\text{Cr}$)**: Selection problems and Binomial probability.

### Strand 10: fx-100AU PLUS Advanced Extensions (Lessons 61–64)
61. **Complex Numbers in Rectangular Form**: `CMPLX` mode, the imaginary unit `i` (`[ENG]`), complex arithmetic.
62. **Polar/Euler Form Conversion**: Converting $a+bi$ to $r\angle\theta$ and vice versa.
63. **2D and 3D Vectors**: Vector mode, defining vectors, addition, scalar multiplication, magnitude.
64. **Vector Dot Product**: Computing $\mathbf{u} \cdot \mathbf{v}$ and angle between vectors.

---

## 4. Tutorial Data Schema (JSON)

Every tutorial in CASSim fx is specified declaratively in `catalog.json`:

```json
{
  "id": "stat-std-dev",
  "title": "Calculate Mean and Standard Deviation (sx vs σx)",
  "strand": "single-variable-statistics",
  "difficulty": "intermediate",
  "curriculum": ["VCE General Maths Units 1&2", "HSC Standard Maths Stage 6"],
  "setup": {
    "mode": "STAT",
    "stat_type": "1-VAR",
    "angle": "DEG",
    "io": "MthIO",
    "frequency": false
  },
  "problemStatement": "Find the mean and sample standard deviation for: 12, 15, 18, 22, 25.",
  "steps": [
    {
      "step": 1,
      "instruction": "Press [MODE] to open the mode selection screen.",
      "targetKey": "k_mode",
      "expectedScreen": "1: COMP    2: STAT\n3: TABLE",
      "explanation": "Mode 2 activates statistical calculations."
    },
    {
      "step": 2,
      "instruction": "Press [2] to select STAT mode.",
      "targetKey": "k_2",
      "expectedScreen": "1: 1-VAR   2: A+BX\n3: _+CX²  4: ln X",
      "explanation": "1-VAR is used for single-variable univariate data."
    },
    {
      "step": 3,
      "instruction": "Press [1] to choose 1-VAR.",
      "targetKey": "k_1",
      "expectedScreen": "  X\n1|",
      "explanation": "Opens the statistical data entry table."
    }
  ],
  "completionVerification": {
    "expectedResult": "5.224940191",
    "badgeTitle": "Standard Deviation Master"
  }
}
```

---

## 5. Teacher Integration & Classroom Whiteboard Mode

1. **Large High-Contrast Whiteboard Mode**: One-click toggle expands the keypad and LCD display to fit projector/interactive panels (Promethean, SMART Board).
2. **Key History Breadcrumbs**: Displays the last 5 keypresses above the keypad (`[MODE]` $\to$ `[2]` $\to$ `[1]` $\to$ `[12]` $\to$ `[=]`), allowing students in the back row to follow along.
3. **Downloadable Offline PWA**: Works 100% without internet access in Australian school computer labs with strict proxy firewalls.
