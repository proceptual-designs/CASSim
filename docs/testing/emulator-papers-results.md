# Emulator check 6, run 5 - Part 4 exam-paper rows (observations only)

Screenshots: `pages-shots-6/K<row>-p<problem>.<page>-<n>.png`. Documents opened from the Documents Toolbox file browser, never saved, never copied. Question text and solutions not copied; entries are the calculator inputs and outputs as shown.

## K4 - 2021MM2-w-CAS-Working-Simon.tns
Settings (document's own, as opened): Display Digits Float 6, Angle Radian, Exponential Normal, Real or Complex Rectangular, Calculation Mode Auto, CAS On, Vector Format Rectangular, Base Decimal, Unit System SI. Screenshot: K4-docsettings.png
Document: Handheld page size; pages in order: 1.1 Calculator, 2.1 Calculator, 3.1 Calculator, 3.2 Graphs, 3.3 Graphs, 4.1 Calculator, 5.1 Calculator, 5.2 Graphs, 6.1 Calculator, 6.2 Graphs. (Problem number = question group; no Notes or spreadsheet pages.)

### 1.1 Calculator (top to bottom)
1. `v(x):=2·x·(25-2·x)·(25-x)` Done
2. `domain(v(x),x)` -> `-∞<x<∞`
3. `solve(v(x)>0,x)|x>0` -> `0<x<25/2 or x>25`
4. `d/dx(v(x))` (derivative template) -> `12·x²-300·x+1250`
5. `solve(d/dx(v(x))=0,x)|0<x<25/2` -> `x=-25·(√3-3)/6`
6. `v(x)|x=-25·(√3-3)/6` -> `15625·√3/9`
7. `v(x):=2·x·(h-2·x)·(h-x)` Done
8. `solve(d/dx(v(x))=0,x)|0<x<h/2` -> warning triangle; `x=-h·(√3-3)/6 and h>0`
9. `v(x)|x=-h·(√3-3)/6 and h>0` -> `h³·√3/9`
10. `v(x):=x·(h-2·x)²` Done
11. `solve(d/dx(v(x))=0,x)|0<x<h/2` -> warning triangle; `x=h/6 and h>0`
12. `v(x)|x=h/6 and h>0` -> `2·h³/27`
Screenshots: K4-p1.1-1.png (entries 1-5), K4-p1.1-2.png (5-7), K4-p1.1-3.png (8-10), K4-p1.1-4.png (11-12). The warning triangle's text was not opened.

### 2.1 Calculator
1. `x²|x={1/4,2/4,3/4,1}` -> `{1/16,1/4,9/16,1}`
2. `{1/16,1/4,9/16,1}·1/4` (shown as fraction over 4) -> `{1/64,1/16,9/64,1/4}`
3. `sum({1/64,1/16,9/64,1/4})` -> `15/32`
4. `15/32.` -> `0.46875`
5. `1/3.` -> `0.333333`
6. `∫(x^(1/2)-x²)dx` from 0 to 1 -> `1/3`
7. `∫(x^(1/2)-a·x²)dx` from 0 to a -> `2·a^(3/2)/3 - a⁴/3`
8. `solve(2·a^(3/2)/3 - a⁴/3 = 1/3, a)` -> `a=0.770231 or a=1`
Screenshot: K4-p2.1-1.png (entries 1-3).

### 3.1 Calculator
1. `q(x):=ln(x²-1)-ln(1-x)` Done
2. `domain(q(x),x)` -> `-∞<x<-1`
3. `d/dx(q(x))` -> warning triangle; `1/(x+1)`
4. `tangentLine(q(x),x,-2)` -> `-x-2`
Screenshot: K4-p3.1-1.png.

### 3.2 Graphs
- f1(x)=q(x) (blue), f2(x)=-x-2 (red), f3(x)=x+2 (black). Window labels at the edges: x from -9.68 to 1.68, y from -4.48 to 3.78. Axes with tick marks; function labels shown on the graph.
- Screenshot: K4-p3.2-1.png.

### 3.3 Graphs
- f4(x)=ⅇ^(-2·x)-2·ⅇ^(-x)+1 (magenta). Window labels: x from -1.88 to 8.6, y from -0.49 to 3.36. Labels 0.2 near the axes.
- Screenshot: K4-p3.3-1.png.

### 4.1 Calculator (long, 19 entries; read bottom to top by arrow keys)
1. `p(x):=ⅇ^(-2·x)-2·ⅇ^(-x)+1` Done
2. `solve(p(x)=x+2,x)` -> warning triangle; `x=-0.750403`
3. `xs:=-0.75040315889581` -> `-0.750403`
4. `∫(p(x))dx` xs to 0 -> `0.257348`
5. `∫(x+2)dx` -2 to xs -> `0.780746`
6. sum of the two integrals above -> `1.03809`
7. `tan(π/12)` -> `-(√3-2)`
8. `tan(5·π/12)` -> `√3+2`
9. `d/da(p(a))` -> `2·ⅇ^(-a)-2·ⅇ^(-2·a)`
10. `solve(2·ⅇ^(-a)-2·ⅇ^(-2·a)=√3+2,a)` -> `false`
11. `solve(2·ⅇ^(-a)-2·ⅇ^(-2·a)=-√3+2,a)` -> `a=ln(-(√3+2)·(√(2·√3-3)-1)) or a=ln((√3 ...` (result runs off the right edge, truncated with a ▸ marker)
12. `tan(π-π/12)` -> `√3-2`
13. `tan(π/2+π/12)` -> `-(√3+2)`
14. `solve(2·ⅇ^(-a)-2·ⅇ^(-2·a)=-√3-2,a)` -> `a=ln(-(√3-2)·(√(2·√3+5)-1))`
15. `solve(2·ⅇ^(-a)-2·ⅇ^(-2·a)=√3-2,a)` -> `a=ln((√3+2)·(√(5-2·√3)-1))`
16. `a=ln(-(√3-2)·(√(2·√3+5)-1))` -> `-0.670214`
17. `a=ln((√3+2)·(√(5-2·√3)-1))` -> `-0.113022`
18. `solve(√3=(1-(2·ⅇ^(-a)-2·ⅇ^(-2·a)))/(1+2·ⅇ^(-a)-2·ⅇ^(-2·a)),a)` -> `a=-0.113022`
19. `solve(√3=-(1-(...))/(1+...),a)` -> `a=-0.670214`
Screenshots: K4-p4.1-2.png (top, entries 1-5), K4-p4.1-1.png (bottom, entries 18-19). Entries 6-17 read from zoomed views (not cropped evidence).

### 5.1 Calculator (14 entries)
1. `normCdf(11,∞,10,0.8)` -> `0.10565`
2. `invNorm(0.8,10,0.8)` -> `10.6733`
3. `p:=0.08` -> `0.08`
4. `√(p·(1-p)/25)` -> `0.054259`
5. `p:=2/25` -> `2/25`
6. `√(p·(1-p)/25)` -> `√46/125`
7. `normCdf(0.1,∞,p,√(p·(1-p)/25))` -> `0.356211`
8. `f(x):=` piecewise: x/500 for 0≤x<20; (50-x)/750 for 20≤x≤50; 0 for true. Done
9. `solve(∫(f(x))dx from 0 to m = 1/2, m)` -> warning triangle; `m=22.6139`
10. `∫(x·f(x))dx` 0 to 50 -> `23.3333`
11. `∫((x-23.3333333333)²·f(x))dx` 0 to 50 -> `105.556`
12. `√105.55555555556` -> `10.274`
13. `22.613872124742/30` -> `0.753796`
14. `1/0.7537957374914` -> `1.32662`
Screenshots: K4-p5.1-2.png (top), K4-p5.1-1.png (bottom).

### 5.2 Graphs
- f1(x)=f(x) (blue): a piecewise-linear triangular shape starting at the axis, peaking, then returning to zero. Window labels: x from -10.11 to 93.59, y from -0.016 to 0.07; a label `2` and `0.005` near the origin.
- Screenshot: K4-p5.2-1.png.

### 6.1 Calculator (14 entries)
1. `f(x):=sin(x/2)+cos(2·x)` Done
2. `fMin(f(x),x)` -> `x=-1.65576`
3. `f(x)|x=-1.6557594787701` -> `-1.7221`
4. `f(2·π-x)-f(x)` -> `0`
5. `g(x,a):=sin(x/a)+cos(a·x)` Done
6. `∫g(x,a)dx` -> `sin(a·x)/a - a·cos(x/a)`
7. `∫g(x,a)dx` from 0 to 2·a·π -> `sin(2·a²·π)/a`
8. `fMin(g(x,a),x)` -> warning triangle; returned unevaluated `fMin(g(x,a),x)`
9. `fMin(g(x,1),x)` -> `x=(4·n3-3)·π/4 and (-1)^n3>0` (n3 shown bold italic)
10. `g(x,1)|x=(4·n3-3)·π/4 and (-1)^n3>0` -> warning triangle; `-(-1)^n3·√2`
11. `fMin(g(x,2),x)` -> `x=-1.65576`
12. `g(x,2)|x=-1.6557594787701` -> `-1.7221`
13. `fMin(g(x,0.5),x)` -> `x=5.54306`
14. `g(x,0.5)|x=5.5430583998095` -> `-1.92821`
Screenshots: K4-p6.1-1.png (top). Other entries read from zoomed views.

### 6.2 Graphs
- f1(x)=g(x,a) (blue) with a slider `a=1.`, slider range -5. to 5.; window labels x -10 to 10, y -6.67 to 6.67.
- Screenshot: K4-p6.2-1.png.

### Re-run in a new Problem (Insert > Problem, same document settings)
The new Problem was inserted after Problem 4, so it became Problem 5 (old 5 and 6 became 6 and 7); one Calculator page.
| from page | entry typed | result |
|---|---|---|
| 1.1 | `v(x):=2*x*(25-2*x)*(25-x)` then `solve(v(x)>0,x)|x>0` | Done; `0<x<25/2 or x>25` (same) |
| 2.1 | `sum({1/64,1/16,9/64,1/4})` | `15/32` (same) |
| 3.1 | `domain(ln(x^2` Right `-1)-ln(1-x),x)` | `-∞<x<-1` (same) |
| 4.1 | `tan(5*pi/12)` | `√3+2` (same) |
| 5.1 | `normCdf(11,∞,10,0.8)` | `0.10565` (same) |
| 6.1 | `f(x):=sin(x/2)+cos(2*x)` then `fMin(f(x),x)` | Done; `x=-1.65576` (same) |
Seen on screen: typing `@inf` for infinity did not give ∞: it was read as `@i` (imaginary i) followed by `nf`, shown `normCdf(11,i·nf,10,0.8)` and returned unevaluated as `normCdf(11,nf·i,10,0.8)`. A typed Unicode `∞` worked (second try gave 0.10565). Screenshots: K4-p5.1-rerun-1.png (first entries), K4-p5.1-rerun-2.png (the `@inf` attempt and the working `∞` entry).

Differs from CASSim or from this file's expectation? Not compared in this pass (observation only). Items for CASSim to check: `domain` returning an inequality; `tangentLine`; warning triangle on `solve(...|...)` and on `d/dx` of ln terms; n3 bold-italic arbitrary integer from `fMin`; unevaluated `fMin(g(x,a),x)`; `false` result from `solve`.

## K5 — 2025 SM Exam 1.tns (Handheld page size)

**Document Settings (as opened):** Float 8, Radian, Normal, Rectangular, Auto, CAS On, Vector Format Rectangular, Base Decimal, Unit System SI. Title bar RAD. Screenshot: `pages-shots-6/K5-docsettings.png`.

Pages: 1.1, 2.1, 3.1 (three Calculator pages, one per Problem). Opened from the file browser, closed with "No" at the save prompt (never saved).

### 1.1 Calculator (4 entries; screenshots K5-p1.1-1, K5-p1.1-2)
| Input | Result |
|---|---|
| `eqn:=x·ⅇ^(-2·y)+y²·ⅇ^x=8·ⅇ⁴` | `ⅇ^x·y²+x·ⅇ^(-2·y)=8·ⅇ⁴` |
| `eqn|x=4 and y=-2` | `true` |
| `impDif(eqn,x,y)|x=4 and y=-2` | `5/12` |
| `solve(eqn,y)` | warning triangle; `(y²·ⅇ^x-8·ⅇ⁴)·ⅇ^(2·y)=-x` |

### 2.1 Calculator (5 entries; screenshot K5-p2.1-1)
| Input | Result |
|---|---|
| `l1(t):=[2 3 1]+t·[1 2 -1]` | Done |
| `l2(s):=[1 3 2]+s·[-1 -1 1]` | Done |
| `solve(l1(t)=l2(s),s,t)` | `s=-2 and t=1` |
| `l1(t)|s=-2 and t=1` | `[3 5 0]` |
| `l2(s)|s=-2 and t=1` | `[3 5 0]` |

### 3.1 Calculator (6 entries; screenshot K5-p3.1-1; upper entries read from zooms)
| Input | Result |
|---|---|
| `v(t):=t/√(t²+k)` | Done |
| `∫₀ᵗ v(t) dt` | `√(t²+k)-√k` |
| `d/dt(v(t))` | warning triangle; `k/(t²+k)^(3/2)` |
| `√(t²+k)-√k=t|t=3` | `√(k+9)-√k=3` |
| `t-(√(t²+k)-√k)=1|t=3` | `-√(k+9)+√k+3=1` |
| `solve(-√(k+9)+√k+3=1,k)` | `k=25/16` |

### Re-run (new Problem 4, page 4.1, same settings; screenshot K5-p4.1-rerun-1)
Typed with ⅇ as `exp()` and `y²` as `y·y`, so the input is equivalent, not identical to 1.1.
| Page | Input | Result | Matched? |
|---|---|---|---|
| 1.1 | `impDif(x·ⅇ^(-2·y)+y·y·ⅇ^x=8·ⅇ^4,x,y)|x=4 and y=-2` | `5/12` | yes |
| 2.1 | `solve([2 3 1]+t·[1 2 -1]=[1 3 2]+s·[-1 -1 1],s,t)` | `s=-2 and t=1` | yes |
| 3.1 | `solve(-√(k+9)+√k+3=1,k)` | `k=25/16` | yes |

Differs from CASSim or from this file's expectation? Not compared against the simulator in this run; observations only.

## K6 — 2025 SM Exam 2 MCQ.tns (Handheld page size)

**Document Settings (as opened):** Float 8, Radian, Normal, Rectangular, Auto, CAS On, Vector Format Rectangular, Base Decimal, Unit System SI. Title bar RAD. Screenshots: `K6-docsettings-1`, `K6-docsettings-2`.

One page only: 1.1 Calculator, 16 entries (listed top to bottom). Opened from the file browser, closed with "No" at the save prompt (never saved).
Screenshots: `K6-p1.1-01`..`04` (the mouse-wheel scroll skips entries, so most entries were read from zooms while stepping with Up; only the entries visible in those four screens are in a screenshot).

| # | Input | Result |
|---|---|---|
| 1 | `expand((x²+a)/(b·x+c))` | warning triangle; `a/(b·x+c)+c²/(b²·(b·x+c))+x/b-c/b²` |
| 2 | `eq(z):=z³+a·z²+b·z-52=0` | Done |
| 3 | `solve(eq(2-3·ⅈ) and eq(2+3·ⅈ),a,b)` | warning triangle; `a=-8. and b=29.` (decimal points) |
| 4 | `eq(z)|a=-8 and b=29` | `z³-8·z²+29·z-52=0` |
| 5 | `factor(z³-8·z²+29·z-52=0)` | `(z-4)·(z²-4·z+13)=0` |
| 6 | `cFactor((z-4)·(z²-4·z+13)=0)` | `(z-4)·(z-(2-3·ⅈ))·(z-(2+3·ⅈ))=0` |
| 7 | `expand(π·∫₀ᵃ (cos(y/3))² dy)` | `3·sin(2·a/3)·π/4+a·π/2` |
| 8 | `3·sin(2·a/3)·π/4+a·π/2|a=π` | `π²/2+3·π·√3/8` |
| 9 | `solve(-49=20·t-1/2·9.81·t²,t)` | `t=-1.7224142 or t=5.7998862` |
| 10 | `solve([1+m;0+m;s-m]=[4;3;t],m,t)` (column matrices) | `m=3 and t=s-3` |
| 11 | `solve([2+l;r-l;-3+4·l]=[4;3;t],l,t)` | `l=2 and r=5 and t=5` |
| 12 | `solve(m=3 and t=s-3 and l=2 and r=5 and t=▸` (input truncated on screen with ▸; rest not seen) | `r=5 and s=8 and t=5 and l=2 and m=3` |
| 13 | `r16(t):=[n·ⅇ^(-2·t)  -t²]` (row vector) | Done |
| 14 | `dotP(d/dt(r16(t)),d²/dt²(r16(t)))=0|t=1/2` | `2-8·n²·ⅇ^(-2)=0` |
| 15 | `solve(2-8·n²·ⅇ^(-2)=0,n)|n>0` | `n=ⅇ/2` |
| 16 | `d/dt(t²)` | `2·t` |

### Re-run (new Problem 2, page 2.1, same settings; screenshot K6-p2.1-rerun-1)
Entry 9 retyped as `solve(-49=20·t-1/2·9.81·t·t,t)` (t·t for t²): result `t=-1.7224142 or t=5.7998862`, matched. Only one entry re-run (one Calculator page).

Differs from CASSim or from this file's expectation? Not compared against the simulator in this run; observations only. Noted for later checking: entry 3 returns decimals with a warning triangle although the mode is Auto; entry 1 also shows a warning triangle.

## K7 — 2025 SM Exam 2 ERQ.tns (Handheld page size)

**Document Settings (as opened):** Float 8, Radian, Normal, Rectangular, Auto, CAS On, Vector Format Rectangular, Base Decimal, Unit System SI. Title bar RAD. Screenshots: `K7-docsettings-1`, `K7-docsettings-2`.

Pages in order: 1.1 Calculator, 1.2 Graphs, 2.1 blank page ("Press menu"), 3.1 Calculator, 4.1 Calculator, 5.1 Calculator (last). Opened from the file browser, closed with "No" at the save prompt (never saved).

### 1.1 Calculator (15 entries; screenshots K7-p1.1-01..05; entries 5–7 read from zooms only)
| # | Input | Result |
|---|---|---|
| 1 | `f1(x):=3·x/(x³+x+2)` | Done |
| 2 | `factor(f1(x))` | `3·x/((x+1)·(x²-x+2))` |
| 3 | `solve(1/f1(x)=0,x)` | warning triangle; `x=-1` |
| 4 | `solve(d/dx(f1(x))=0,x)` | warning triangle; `x=1` |
| 5 | `solve(d²/dx²(f1(x))=0,x)` | warning triangle; `x=1.6864614` |
| 6 | `f1(x)|x=1.6864614283651` | `0.5964135` |
| 7 | `∫₀² (π·(f1(x))²) dx` | `2.2880103` |
| 8 | `f2(x):=3·x/(x³-5·x+2)` | Done |
| 9 | `solve(1/f2(x)=0,x)` | warning triangle; `x=-(√2+1) or x=√2-1 or x=2` |
| 10 | `f3(x,a):=3·x/(x³+a·x+2)` | Done |
| 11 | `solve(d/dx(f3(x,a))=0,x)` | warning triangle; `x=1` |
| 12 | `f3(1,a)` | `3/(a+3)` |
| 13 | `d/dx(f3(x,a))` | warning triangle; `-6·(x³-1)/(x³+a·x+2)²` |
| 14 | `solve(x³+a·x+2=0,a)|x=1` | `a=-3` |
| 15 | `solve(d²/dx²(f3(x,a))=0,a)|x=2` | warning triangle; `a=24/5` |

### 1.2 Graphs (screenshots K7-p1.2-1, K7-p1.2-window, K7-p1.2-entry-f1)
- Window Settings (menu 4 Window / Zoom ▶, 1 Window Settings…): XMin -4, XMax 4, XScale Auto, YMin -2, YMax 2, YScale Auto.
- Function entry line: f1(x)=3·x/(x³+x+2) ticked (plotted); f2(x) and f3(x,a) rows exist and are unticked (not plotted); next empty row is f4(x)=.
- On the plot: the f1 curve, a vertical blue line labelled `x=-1`, two labelled points `(1, 0.75)` and `(1.69, 0.596)`, and the function label `f1(x)=3·x/(x³+x+2)` at upper right.
- Not examined: how the vertical line and the labels were made (no Attributes check).

### 2.1 blank page
Shows only the text "Press menu" (an empty page, no application chosen). Screenshot K7-p2.1-1.

### 3.1 Calculator (5 entries; screenshots K7-p3.1-01, -02)
| # | Input | Result |
|---|---|---|
| 1 | `euler((300-q)/150,t,q,{0,30},5,15)` | `[[0. 15. 30.][5. 34.5 61.05]]` |
| 2 | `deSolve(q'=(300-q)/150 and q(0)=5,t,q)` | `q=300-295·ⅇ^(-t/150)` |
| 3 | `solve(100=300-295·ⅇ^(-t/150),t)` | `t=150·ln(59/40)` |
| 4 | `solve(1/20=(100+2·t)/(3000+20·t),t)` | warning triangle; `t=50` |
| 5 | `t=150·ln(59/40)` | `t=58.298698` |

### 4.1 Calculator (12 entries; screenshots K7-p4.1-01, -02; middle entries from zooms)
| # | Input | Result |
|---|---|---|
| 1 | `r(t):=[5·cos(t)-4·cos(5·t/2)  5·sin(t)-4·sin(▸` (truncated on screen) | Done |
| 2 | `r(0)` | `[1 0]` |
| 3 | `r(2·π)` | `[9 0]` |
| 4 | `r(2·π+0.01)` | `[8.9985001 0.14998875]` |
| 5 | `dr(t):=d/dt(r(t))` | Done |
| 6 | `dr(0)` | `[0 -5]` |
| 7 | `dr(2·π)` | `[0 15]` |
| 8 | `r(0)` | `[1 0]` |
| 9 | `r(π)` | `[-5 -4]` |
| 10 | `tCollect(dotP(dr(t),dr(t)))` | warning triangle; `125-100·cos(3·t/2)` |
| 11 | `√(125-100·cos(3·t/2))` | `5·√(5-4·cos(3·t/2))` |
| 12 | `∫₀^π (5·√(5-4·cos(3·t/2))) dt` | `36.607844` |
(Zoom reading order at the lower end: entries 8–9 appeared as `r(0)`, `r(π)` directly above the `tCollect` entry; the first `r(0)` is entry 2.)

### 5.1 Calculator (Simon's LazyMath UDF library `sm_linalg` in use; screenshots K7-p5.1-01, -02)
Entries seen (top to bottom):
| # | Input | Result |
|---|---|---|
| 1 | `[[2 0 9][3 6 5][1 9 -3]]^-1·[8;7;7]` | `[-5;2;2]` |
| 2 | `pi1:=2·x+9·z=8` | `2·x+9·z=8` |
| 3 | `pi2:=3·x+6·y+5·z=7` | `3·x+6·y+5·z=7` |
| 4 | `pi3:=x+9·y-3·z=7` | `x+9·y-3·z=7` |
| 5 | `solve(pi1 and pi2 and pi3,x,y,z)` | `x=-5 and y=2 and z=2` |
| 6 | `crossP([3 6 5],[1 9 -3])` | `[-63 14 21]` |
| 7 | `solve(pi2 and pi3,x,y,z)` | `x=-(3·c1-1) and y=2·(c1+1)/3 and z=c1` |
| 8 | `sm_linalg\distplp(pi3,[1 1 2])` | step-by-step text output ("Given", "Find normal…", "Determine a point on the plane": `OA=[7 0 0]`, …); rest not read |
| 9 | `sm_linalg\dist2pl(pi1,6·x+27·z=1)` | step-by-step output ("Normal Vector": `n=[2 0 9]`, `|n|=√85`, `n_hat=[2·√85/85 0 9·√85/85]`, "Point on Plane"…); rest not read |
| 10 | `sm_linalg\dist2pl(pi1,6·x+27·z=47)` | same layout; ends "Project AP in direction of n_hat", `|AP·n_hat|=|23·√85/255|`, "Minimum Distance:" `23·√85/255`, then Done |
Note: the middle of each UDF output (several screens) was not read line by line; only the pieces above were seen. The mouse wheel scrolls whole entries here.

### Re-run (new Problem 6, page 6.1, same settings; screenshots K7-p6.1-rerun-1, -2)
Typed with `^` exponent followed by Right, `nInt` for the integral, plane name `p1` for `pi1` (to avoid π).
| Page | Input | Result | Matched? |
|---|---|---|---|
| 1.1 | `f1(x):=3·x/(x^3+x+2)` then `factor(f1(x))` | `3·x/((x+1)·(x²-x+2))` | yes |
| 3.1 | `solve(1/20=(100+2·t)/(3000+20·t),t)` | warning triangle; `t=50` | yes |
| 4.1 | `nInt(5·√(5-4·cos(3·t/2)),t,0,π)` | `36.607844` (original used ∫, so input differs) | value yes |
| 5.1 | `p1:=2·x+9·z=8` then `sm_linalg\dist2pl(p1,6·x+27·z=47)` | ends with Minimum Distance `23·√85/255`, Done | yes (end of output only) |
Page 1.2 (Graphs) not re-run: no Calculator entry.

Differs from CASSim or from this file's expectation? Not compared against the simulator in this run. Worth checking in CASSim: the warning triangles on entries that return results (K7 1.1 entries 3, 4, 5, 9, 11, 13, 15; 3.1 entry 4; 4.1 entry 10), `sm_linalg` library calls, `euler(...)` output as a 2-row matrix with decimal points, `tCollect`.

---
## Hand-back (emulator-papers-results.md)

**Run on the emulator (observed on screen):**
- K4 2021MM2-w-CAS-Working-Simon.tns (all 10 pages, re-run done).
- K5 2025 SM Exam 1.tns (3 pages, re-run done).
- K6 2025 SM Exam 2 MCQ.tns (1 page, re-run done).
- K7 2025 SM Exam 2 ERQ.tns (6 pages, re-run on the Calculator pages).
- Rows 1–3 (SAC files) are in `emulator-sac-results.md`.

**Not run, with reason:**
- Any comparison against the CASSim simulator (observation-only run).
- Solutions PDFs were not opened for K5–K7 beyond identifying files; no question text copied.
- K7 5.1: the middle of the `sm_linalg` step output was not read line by line.
- K7 1.2: the vertical line and point labels were not inspected for how they were made.
- Entries read from zooms only are marked in each section.

**Also seen, not covered:**
- K6 1.1 entry 12 input truncated with ▸ on screen (full text not seen).
- K4 4.1 `@inf` observation (see K4 section).
- The `.tns` files were opened from the file browser and closed without saving; none was copied, renamed, uploaded or unpacked.
