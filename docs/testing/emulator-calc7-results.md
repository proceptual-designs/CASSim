# Emulator check 6, run 6: CAS rows R6-C1 to R6-C6 and Calculator rows R6-H (results)

Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld, Keypad + SideScreen at 250%.
Settings (set in Document2 before the CAS rows, checked on screen in Document Settings): Display Digits Float 8, Angle Radian, Exponential Format Normal, Real or Complex Rectangular (the document had Real; the drop-down lists Real, Rectangular, Polar), Calculation Mode Auto, CAS Mode On.
Page: Calculator page 1.3 of Document2 (unsaved). Typed symbols are TI ASCII; results are recorded in Unicode.

## R6-C2: `domain(...)`
Keys: Calculator entry line, typed in chunks, Return after each. `^` followed by Right in entry 4.
| Entry | Result as shown |
|---|---|
| `domain(1/x,x)` | `x≠0` |
| `domain(√(x-2),x)` (typed `sqrt(`, drawn as √) | `2≤x<∞` |
| `domain(ln(x)+ln(4-x),x)` | `0<x<4` |
| `domain(1/(x²-1),x)` | `x≠-1 and x≠1` |
| `domain(tan(x),x)` | `x≠((2·n1−1)·π)/2` (stacked fraction, with `n1` in bold italic) |
Screenshots: `R6-C2-hh-domain-1-over-x.png`, `R6-C2-hh-domain-sqrt-x-minus-2.png`, `R6-C2-hh-domain-ln-1-over-x2-minus-1-tan.png` (the last one shows the ln, 1/(x²-1) and tan lines together). Two further half-scale captures were not kept.
Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-C3: `solve` twice, constants numbering `c`/`n`, `fMin`
Settings: as above (Float 8, Radian, Rectangular, Auto). Problem 1, Calculator page 1.3, straight after the five `domain` entries (so `n1` had already been used by `domain(tan(x),x)`).
| Entry (in order) | Result as shown |
|---|---|
| `solve(2x+y+z=1 and x-y=2,x,y,z)` (typed as `2x`, drawn `2·x`) | `x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1` (stacked fractions, `c1` bold italic) |
| the same entry again | the same with `c2` in place of `c1` |
| `solve(sin(x)=0,x)` | `x=n2·π` |
| `solve(sin(x)=0,x)` again | `x=n3·π` |
| `fMin(sin(x)+cos(x),x)` | `x=((4·n4-3)·π)/4 and (-1)^n4>0` |
Numbering: `c` and `n` are separate counters. Each counts up through the Problem, and each use gets the next number (c1, c2; n1 from the tan domain, then n2, n3, n4), with no reset between entries or after a repeated identical entry.

New Problem: Insert menu (top menu bar, Insert at about (128,33)): Problem, Page (Ctrl+I), Calculator, Graphs, Geometry, Lists & Spreadsheet, Data & Statistics, Notes, Vernier DataQuest™, Widget, Question…, Image… (greyed), Program Editor ▶, Script Editor ▶, Python ▶. Clicked Problem, the page was labelled 2.1 with the add-page menu, pressed 1 (Add Calculator). In Problem 2: `solve(sin(x)=0,x)` gave `x=n1·π` and then `solve(2x+y+z=1 and x-y=2,x,y,z)` gave `x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1`. So both counters restart at 1 in a new Problem. I did not reopen Document Settings for Problem 2 (the title bar still read RAD).
Screenshots: `R6-C3-hh-solve-3var-first-c1.png`, `R6-C3-hh-solve-3var-second-c2.png`, `R6-C3-hh-solve-sin-first-n2.png`, `R6-C3-hh-solve-sin-second-n3.png`, `R6-C3-hh-fMin-sin-plus-cos-n4.png`, `R6-C3-hh-new-problem-restart-n1-c1.png`, `R6-C3-hh-insert-menu-scaled0.6.jpg` (scaled).
Differs from CASSim or from this file's expectation? Not compared in this run.

## R6-C4: derivatives
Settings: as above. Problem 2, Calculator page 2.1. Entered as `derivative(f(x),x)`; the history shows the `d/dx` template.
Keys: `^` followed by Right every time; `sqrt(` typed and drawn as √.
| Entry | Result as shown | Warning triangle |
|---|---|---|
| `derivative(x²·sin(x),x)` | `x²·cos(x)+2·x·sin(x)` | no |
| `derivative((x+1)/(x-1),x)` | `-2/(x-1)²` (stacked) | YES, a yellow ⚠ at the left of the entry |
| `derivative(ln(x²-1),x)` | `2·x/(x²-1)` (stacked) | no |
| `derivative(x·ⅇ^(-x),x)` (ⅇ from the e^x key, see below) | `(1-x)·ⅇ^(-x)` | no |
| `derivative((x²+1)³,x)` | `6·x·(x²+1)²` | no |
| `derivative(√(x²+1),x)` | `x/√(x²+1)` (stacked) | no |
The ⅇ in rows 4 shows as a bold upright "e" on screen.

Typing ⅇ (what went wrong first):
- Typing ASCII `@e` in the entry line (as the typing notes for this emulator say) was NOT converted: the line showed a literal `@e`, then Return gave Error "Syntax" (OK to close it). Entry was `derivative(x*@e^(-x),x)` typed in chunks.
- Using the e^x key on the keypad (at about (75,565)) works. It inserts `e^(` with a boxed exponent; type `-x`, press Right ONCE to leave the exponent, then `,x)`. A second Right jumped over the closing bracket of `derivative(` and the entry then gave Error "Too few arguments" ("The function or command is missing one or more arguments." (TI text, do not reuse)).
- If the key click and the next typing come with no pause, the `-x` was typed before the exponent box and the line showed `x·-xe□`, which gave Error "Syntax". With a 1 s wait after the key click it worked.
- ctrl+a then BackSpace cleared the junk entry line each time; the failed entries were not added to the history.
Screenshots: `R6-C4-hh-d-x2-sin-x.png`, `R6-C4-hh-d-quotient-and-ln.png` (quotient with triangle and the ln line), `R6-C4-hh-d-x-times-e-to-minus-x.png`, `R6-C4-hh-d-x2-plus-1-cubed.png`, `R6-C4-hh-d-sqrt-x2-plus-1.png`, errors: `R6-C4-hh-typed-at-e-literal-syntax-error.png`, `R6-C4-hh-e-key-too-few-arguments-error.png`, `R6-C4-hh-e-key-typed-too-fast-syntax-error.png`, `R6-C4-hh-e-key-entry-line-before-return-zoom.jpg` (zoom, not full size).
The Show Warning Info text for the quotient's triangle was NOT read in this run (see R6-C1).
Differs from CASSim or from this file's expectation? Not compared in this run.

## C5 – definite integrals (Handheld, page 2.1, Document2)

Settings: Float 8, Radian, Auto, Rectangular, CAS On. Integrals typed as `integral(f,x,a,b)` (the e^x key used for ⅇ^(x²); `x^2`, Right, Right).

| # | Entry | Observed result | Screenshot |
|---|---|---|---|
| 1 | ∫₀¹ ⅇ^(x²) dx | 1.4626517 (decimal in Auto mode) | R6-C5-hh-int-0-1-e-to-x2.png; entry line zoom R6-C5-hh-e-to-x2-entry-line-zoom.jpg |
| 2 | ∫₁² sin(x)/x dx | 0.65932991 | R6-C5-hh-int-1-2-sin-x-over-x.png |
| 3 | ∫₀^π √(1+cos(x)²) dx | 3.8201978 | R6-C5-hh-int-0-pi-sqrt-1-plus-cos2.png |
| 4 | ∫₀¹ x^x dx | 0.78343051 | R6-C5-hh-int-0-1-x-to-x.png |
| 5 | ∫₀² 1/(x³+x+2) dx | Exact sum, not a decimal: `3·√7·tan⁻¹(3·√7/7)/28 + √7·tan⁻¹(√7/7)/28 + ln(9/2)/8 …`. Scrolling the answer with Right showed `…√7·tan⁻¹(3√7/7)/28 + 3·√7·tan⁻¹(√7/7)/28 + ln(9/2)/8`. Any text after `ln(9/2)/8` was NOT confirmed seen; the term order differs between the two views as read, so the exact expression is not fully transcribed. ctrl+Enter decimal NOT run. | R6-C5-hh-int-0-2-rational-start.png, R6-C5-hh-int-0-2-rational-end.png |

Differs from CASSim or from this file's expectation? Not compared in this run.

### C5 row 5 decimal
Keys: Escape, ctrl+a, BackSpace, Up, Return (re-entered the previous integral entry), ctrl+Enter. Observed: `0.53085063` (Float 8). Screenshot: R6-C5-hh-int-0-2-rational-decimal.png. The history showed the exact expression again above the decimal; the tail after `ln(` is still cut off at the right edge in that view.
Differs from CASSim or from this file's expectation? Not compared in this run.

## C6 – `t=150*ln(59/40)` (Handheld, page 2.1)
Settings: Float 8, Radian, Auto, Rectangular, CAS On. Typed `t=150*ln` then `(59/40)`.
- Enter: the entry was echoed back unchanged as `t=150·ln(59/40)` (stacked fraction 59 over 40), right-hand side the same equation, no evaluation, no error. Screenshot: R6-C6-hh-t-equals-enter.png.
- Up, Return (re-entry) then ctrl+Enter: `t=58.298698`. Screenshot: R6-C6-hh-t-equals-ctrl-enter.png.
Differs from CASSim or from this file's expectation? Not compared in this run.

## Closing lists (this file)

### Run on the emulator (Handheld view, Document2)
- C2 (domain entries), C3 (solve twice, fMin, c/n numbering), C4 (derivatives), C5 (five integrals), C6 (`t=150*ln(59/40)`, Enter then ctrl+Enter).

### Not run, with reason
- C1 (Show Warning Info on the paper entries): not reached in this run (stopped before it). Only the quotient derivative with a ⚠ triangle on page 2.1 was seen, not opened.
- R6-H items (hidden A3/A11, Part B 4–7, editor rows, H1/H2/H4/H7 letters, ctrl+1 with 20 entries, Clear History then ctrl+Z): not reached.
- C5 row 5: full exact expression not fully read (tail after `ln(9/2)/8`).

### Also seen, not covered
- Coordinates and Equations, Calculate and Redefine (Graphs Actions) showed no visible change on click; not investigated.

# RUN 6 per brief of 2026-11-23 (Part B rows R6-B1 to R6-B9, Part D rows R6-D1 to R6-D7)

Emulator: TI-Nspire CX CAS Premium Teacher Software, Handheld, Keypad + SideScreen at 250%. Document2 (unsaved), Problem 3 for B2/B3, Problem 4 for the restart check. Settings checked in Document Settings for Problem 3: Float 8, Radian, Normal, Rectangular (set from Real), Auto, CAS On. Problem 4 was added with Insert > Problem and its settings were not re-opened (it showed RAD). Typed in TI ASCII, recorded in Unicode.

## R6-B1 Show Warning Info on the paper entries
Not run in this pass (reason: needs about 25 entries retyped from `emulator-papers-results.md`; deferred, see the lists at the end).

## R6-B2 domain()
Keys: `domain(expr,x)` Return. Screenshots: R6-B2-hh-domain-1overx-sqrt.png, R6-B2-hh-domain-ln-rational-tan.png.

| Entry | Result as shown |
|---|---|
| `domain(1/x,x)` | x≠0 |
| `domain(√(x-2),x)` | 2≤x<∞ |
| `domain(ln(x)+ln(4-x),x)` | 0<x<4 |
| `domain(1/(x^2-1),x)` | x≠-1 and x≠1 |
| `domain(tan(x),x)` | x≠(2·n1−1)·π/2, with n1 shown in bold italic (an integer-family symbol) |

Differs from CASSim? CASSim's `x≠0`, `2≤x<∞` and `x≠-1 and x≠1` styles are CONFIRMED. CASSim "echoes tan": CONTRADICTED, the device returns the family x≠(2·n1−1)·π/2. The n1 here is the first n in this Problem; the domain call took it (see B3).

## R6-B3 c and n counters
Keys: typed in one Problem, then repeated in a new Problem. Screenshots: R6-B3-hh-solve-system-twice.png, R6-B3-hh-sin-twice-fmin.png, R6-B3-hh-new-problem-restart.png.

| Entry (in order, Problem 3) | Result |
|---|---|
| (domain(tan(x),x) earlier) | n1 |
| `solve(2x+y+z=1 and x-y=2,x,y,z)` | x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1 |
| the same again | x=-(c2-3)/3 and y=-(c2+3)/3 and z=c2 |
| `solve(sin(x)=0,x)` | x=n2·π |
| the same again | x=n3·π |
| `fMin(sin(x)+cos(x),x)` | x=(4·n4-3)·π/4 and (-1)^n4>0 |
| Problem 4: first solve again | x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1 (restarts at c1) |
| Problem 4: `solve(sin(x)=0,x)` | x=n1·π (restarts at n1) |

Observed: c numbers and n numbers each count up through a Problem (c1, c2; n1, n2, n3, n4) and restart at 1 in a new Problem. The two counters are separate. Every call that produces an integer family takes the next n, even `domain` and `fMin`. fMin on sin(x)+cos(x) gives an n family with a condition, not a decimal.
Differs from CASSim? CASSim "starts at c1 in every answer; no n family yet (gives a decimal)": CONTRADICTED on both counts.

## R6-B4 Derivatives
Keys: typed `derivative(expr,x)` Return (the display shows the d/dx template form; the template key was not used). Problem 4, page 4.1. Screenshots: R6-B4-hh-derivs-1-3.png, ...-4-5.png, ...-5-6.png.

| Entry | Result exactly as shown |
|---|---|
| x²·sin(x) | x²·cos(x)+2·x·sin(x) |
| (x+1)/(x-1) | -2/(x-1)² (a warning triangle at the left of the line) |
| ln(x²-1) | 2·x/(x²-1) |
| x·ⅇ^(-x) | (1-x)·ⅇ^(-x) |
| (x²+1)³ | 6·x·(x²+1)² |
| √(x²+1) | x/√(x²+1) |

Differs from CASSim? "Rationals over one denominator, cancelled": CONFIRMED for the first quotient (−2/(x−1)²). "Polynomials expanded unless longer": here the results stay factored, 6·x·(x²+1)² is not expanded (to compare with CASSim's rule). The first result is a sum, not combined.
Note: a long entry typed in one go (17 characters) is pasted through the clipboard and was garbled once (`derivative(sqrt(x` became wrong); it was cleared with ctrl+A, BackSpace and retyped in short pieces.

## R6-B5 Definite integrals
Keys: typed `integral(f,x,a,b)` Return, about 3 to 5 s wait each. ⅇ^(x²) typed as `exp(x^2)` (shown as ⅇ^(x²)). Screenshots: R6-B5-hh-integrals-1-2.png, ...-3-4.png, ...-5-exact.png, ...-5-approx.png.

| Integral | Shown |
|---|---|
| ∫₀¹ ⅇ^(x²) dx | 1.4626517 (decimal) |
| ∫₁² sin(x)/x dx | 0.65932991 (decimal) |
| ∫₀^π √(1+cos(x)²) dx | 3.8201978 (decimal) |
| ∫₀¹ x^x dx | 0.78343051 (decimal) |
| ∫₀² 1/(x³+x+2) dx | an exact value, too long for the line (scroll arrow at the right): `3·√7·tan⁻¹(3·√7/7)/28 + 3·√7·tan⁻¹(√7/7)/28 + ln(…` then cut off. `approx(ans)` gives 0.53085063 |

Differs from CASSim? CASSim gives a decimal when there is no closed form: CONFIRMED for the first four. The fifth integral is returned in exact form here (long, three-part), not as a decimal: CONTRADICTS "or when the exact form is long".

## R6-B6 Enter and ctrl+Enter
Keys: `t=150*ln(59/40)` then Return; again then ctrl+Enter. Screenshot: R6-B6-hh-enter-vs-ctrlenter.png.
- Return: `t=150·ln(59/40)` (the equation echoed in stacked-fraction form, not evaluated).
- ctrl+Enter: `t=58.298698`.
So ctrl+Enter gives t=58.298698.

## R6-B7 Four entries
Settings as above (Problem 4). Screenshots: R6-B7-hh-solve-bar-tcollect.png, R6-B7-hh-solve-ey-echo.png, R6-B7-hh-expand-rational.png.

| Entry | Shown |
|---|---|
| `solve(x^2=4,x)|x=2` | x=-2 or x=2 (the `|x=2` did not substitute) |
| `tCollect(dotP([5cos(t)-4cos(5t/2),5sin(t)-4sin(5t/2)],[same]))` | 41-40·cos(3·t/2) (a warning triangle at the left of the line; the typed line is cut off at the right) |
| `solve(x*ⅇ^(-2y)+y²*ⅇ^x=8*ⅇ^4,y)` | not solved; the equation is rewritten as (y²·ⅇ^x-8·ⅇ^4)·ⅇ^(2·y)=-x (a warning triangle) |
| `expand((x²+a)/(b*x+c),x)` | (a·b²+c²)/(b²·(b·x+c)) + x/b - c/b² |

Differs from CASSim? CASSim says `true` for the first: CONTRADICTED (x=-2 or x=2). CASSim says tCollect gives -(100·cos(3·t/2)-125): CONTRADICTED, the device gives 41-40·cos(3·t/2) (this is the correct value of 25+16-40·cos(3t/2)). The solve with ⅇ and y: CASSim "echoed": similar (a rewritten equation, not a solution for y). `expand`: CASSim "not divided out": the device does split it into three terms in x (x/b - c/b² + a fraction).

## R6-B8 tTest sign convention (typed, Problem 4 page 4.1, Radian/Automatic/Real)
Argument order on the emulator: `tTest μ0,List[,Freq[,Hypoth]]`. The brief's third argument `1` is therefore Freq, not the alternative. Both forms were run; the list was {2,4,4,4,5,5,7,9}, μ0 = 4.
- `tTest 4,{2,4,4,4,5,5,7,9},1` (Freq 1, Hypoth omitted): Done. `stat.results` shows Title "t Test", Alternate Hyp "μ ≠ μ0", t 1.3228757, PVal 0.22745282, df 7., x̄ 5., sx := sn-1x 2.1380899, n 8. Omitted Hypoth = ≠. Shot R6-B8-tTest-default-neq.png.
- `tTest 4,{...},1,1`: Alternate Hyp "μ > μ0", PVal 0.11372641 (t, df, x̄, sx, n unchanged). Shot R6-B8-tTest-sign-plus1.png.
- `tTest 4,{...},1,-1`: Alternate Hyp "μ < μ0", PVal 0.88627359. Shot R6-B8-tTest-sign-minus1.png.
- `tTest 4,{...},1,0`: Alternate Hyp "μ ≠ μ0", PVal 0.22745282. Shot R6-B8-tTest-sign-0.png.
- Check: 0.11372641 + 0.88627359 = 1, and 2 × 0.11372641 = 0.22745282.
- CASSim note CONFIRMED (positive is >, negative is <, 0 is ≠), with the extra detail that omitting the sign gives ≠.
- Name in the stat. drop-down is lowercase `stat.results` (list: df, n, pval, results, stat, sx, t, values, x̄); the results table labels the p-value "PVal". Shot R6-B8-stat-dropdown.png.

## R6-B9 LinRegtTest and stat.RegEqn (typed, Problem 4 page 4.1)
Syntax on the emulator: `LinRegtTest X,Y[,Freq[,Hypoth]]`. The brief's trailing `0` is therefore Freq.
- `LinRegtTest {1,2,3,4,5},{2.1,3.9,6.2,7.8,10.1},0`: error dialog "Domain error" / "An argument must be in a specified domain." (TI text, do not reuse). After OK the history line shows "Error: Domain error". Freq 0 is not allowed. Shot R6-B9-domain-error-freq0.png.
- `LinRegtTest {1,2,3,4,5},{2.1,3.9,6.2,7.8,10.1},1,0`: Done. `stat.results` shows Title "Linear Reg t Test"; Alternate Hyp "β & ρ ≠ 0"; RegEqn "a+b·x"; t 33.321291; PVal 0.00005942; df 3.; a 0.05; b 1.99; s 0.18885621; SESlope 0.05972158; r² 0.99730533; r 0.99865176; Resid "{...}". Shots R6-B9-linregttest-top.png and R6-B9-linregttest-bottom.png.
- Row order in the table: Title, Alternate Hyp, RegEqn, t, PVal, df, a, b, s, SESlope, r², r, Resid.
- `stat.RegEqn(x)` EXISTS and is a function: result `1.99·x+0.05` (the entry history shows it as `stat.RegEqn(x)`, drawn with capitals R, E). Shot R6-B9-regeqn-x.png.
- The stat. drop-down for LinRegtTest lists: a, b, df, pval, r, r², regeqn, resid, results, s, seslope, stat ... The drop-down item inserts the opening bracket itself (`stat.regeqn(`), so a typed `(x)` after it gives `((x))`; type only `x`. Shot R6-B9-stat-dropdown-regeqn.png.
- Note the stored variable is lowercase in the drop-down (`regeqn`) and is drawn as `RegEqn` after evaluation.

## R6-D2 Clear History, ctrl+Z, and `ans` on a new page (Problem 4)
- Menu 1 Actions on a Calculator page lists: 1 Define, 2 Recall Definition, 3 Delete Variable, 4 Clear a–z…, 5 Clear History, 6 Insert Comment, 7 Library ▸, 8 Lock ▸. Shot R6-D2-actions-menu.png.
- Menu 1 5 (Clear History): the whole history disappears at once, no dialog, an empty entry line left. Shot R6-D2-clear-history.png.
- ctrl+Z straight after: the history comes back (the xs…cat definitions are shown again, entry line empty). CASSim note ("undo restores") CONFIRMED. Shot R6-D2-after-ctrlz.png.
- `ans` on a NEW Calculator page of the same Problem while the page before had answers: error dialog "Undefined Ans" with text that the previous calculation did not create Ans or none was entered (TI text, do not reuse). CASSim note ("`ans` is undefined on the new page") CONFIRMED. Shot R6-D2-ans-new-page-error.png. (ctrl+i 1 put the new page right after the page that was open, so the tab order became 4.1, 4.2 Calculator, 4.3 Lists & Spreadsheet.)

## R6-D3 PC Backspace against keypad del after a fraction template
- Fraction template inserted from the templates palette (first icon; a click on the icon inserts it at once, no Return needed; a Return pressed after that evaluates the empty template and gives a Syntax error). Typed 1, Down, 2, Right: the cursor sits after the fraction (shot R6-D3-fraction-before.png, red cursor marks at both sides).
- One PC Backspace: the whole fraction is HIGHLIGHTED (selected), nothing deleted yet; a second Backspace would delete it. Shot R6-D3-pc-backspace-highlight.png.
- One keypad del (clicked on the on-screen key) on the same state: the fraction is REMOVED at once, empty entry line. Shot R6-D3-keypad-del-removed.png.
- Brief's guess CONFIRMED: Backspace highlights first, del removes at once.
- Side note: with the cursor INSIDE the denominator (`57`), Backspace deleted one digit (57 to 5) with no highlight; del after leaving gave an empty fraction collapse to the numerator text.

## R6-D4 Deleting a middle history pair (page 4.2, pairs 1 to 5, typed `1`…`5`, Return each)
Selection by Up: Up goes result, then input, then the previous result (Up ×5 reached the RESULT of pair 3; one more Up the INPUT of pair 3).
- **PC Delete** sent with the RESULT of pair 3 selected: nothing changes (pairs 2 3 4 5 still shown, result 3 still highlighted). Shot R6-D4-delete-on-result-nochange.png. Sent again with the INPUT of pair 3 selected: still nothing. Shot R6-D4-delete-on-input-nochange.png. So the PC Delete key (as sent by the computer-use tool) has no effect here. CASSim's "Delete selects the next pair's input" could NOT be checked; the key may need a real keyboard.
- **PC Backspace** with the INPUT of pair 3 selected: pair 3 is deleted, and the INPUT of the PREVIOUS pair (2) becomes selected. Shot R6-D4-after-backspace.png. CASSim ("Backspace selects the previous one's") CONFIRMED.
- **Keypad del** (clicked) with the INPUT of pair 7 selected (pairs 4 5 6 7 8): pair 7 is deleted and the INPUT of the previous pair (6) is selected. Shots R6-D4-before-keypad-del.png, R6-D4-after-keypad-del.png. CASSim ("del selects the previous one's") CONFIRMED.
- Caution: an earlier keypad del after a Down press (not recorded as a row) was ambiguous about which pair it removed, so only the clean run is reported.

## R6-D5 Second click on a picked history row (page 4.2; history 4, 5, 6, 8; entry line empty)
- Mouse, click 1 on the input `5`: a text caret appears after the 5 in that row (row not selected, nothing brought down). Shot R6-D5-mouse-click1.png. Click 2 on the same row: the caret is no longer drawn (it blinks or is gone); nothing is brought down to the entry line, which stays empty. Shot R6-D5-mouse-click2.png.
- Keypad pointer (the centre click button of the arrow pad), with input `5` already picked by Up: click 1 leaves the row picked (blue); click 2 turns the pick into a caret at the START of the row (`|5`). Nothing brought down. Shots R6-D5-keypad-click1.png, R6-D5-keypad-click2.png.
- Both devices: a second click only moves the cursor, it does not bring the row down. This matches what Simon chose for CASSim. Brief row note: the row was not brought down by Return either (not tested).

## R6-D1 Inverse Binomial and Inverse Binomial N with Matrix Form ticked (Menu 5 Probability > 5 Distributions)
- Distributions list: 1 Normal Pdf, 2 Normal Cdf, 3 Inverse Normal, 4 t Pdf, 5 t Cdf, 6 Inverse t, 7 χ² Pdf, 8 χ² Cdf, 9 Inverse χ², A Binomial Pdf, B Binomial Cdf, C Inverse Binomial…, D Inverse Binomial N… (more below D). Shots R6-D1-distributions-menu-top.png, -end.png.
- **Inverse Binomial N** (item D) dialog is titled "Num Trials" with fields Cumulative Prob, Prob Success p, Successes x, and a Display Result checkbox "Matrix Form". Entered 0.9, 0.5, 5, ticked Matrix Form. Pasted line: `invBinomN(0.9,0.5,5,1)` (the ticked box adds a 4th argument 1). Result shown: matrix [[7, 0.9375],[8, 0.85546875]] (rows: n, then the cumulative probability). Shots R6-D1-invbinomN-dialog.png, -filled.png, -result.png.
- **Inverse Binomial** (item C) dialog is titled "Num Successes" with fields Cumulative Prob, Num Trials n, Prob Success p, and the same Matrix Form box. Entered 0.9, 10, 0.5, ticked. Pasted line: `invBinom(0.9,10,0.5,1)`. Result: matrix [[6, 0.828125],[7, 0.9453125]] (rows: x, then the cumulative probability). Shots R6-D1-invbinom-dialog.png, -filled.png, -result.png.
- Both give a two-row matrix with the answer and the next value beside their cumulative probabilities.

## RUN 6 Parts B and D: lists
Run: B2-B9; D1-D5.
Not run: B1 (Show Warning Info, needs entries retyped from emulator-papers-results.md); D6 (simulator-todo E1, E3, E7, F1, F2, F5); D7 (run 5 leftovers).
Also seen, not covered: tTest argument order is tTest mu0,List[,Freq[,Hypoth]] (a sign or 0 as 3rd argument is Freq in LinRegtTest, so ,0 gives a Domain error); PC Delete key did nothing in the entry line.
