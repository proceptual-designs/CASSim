# Emulator check 4, Part C: Catalog sweep (TI-Nspire CX CAS Premium Teacher Software 6.0.3.374)

Observations only. Settings: new handheld-page-size document (Document16), Radian, Automatic, Real, Float 8, CAS On (RAD in the title bar). Catalog opened with the keypad's book key at (382,480) (the key just left of it is the Templates key). Screenshots (cropped to the list and hint pane, about 390x260 px) are in pages-shots/.

How the sweep was done: the Catalog opens on tab 1 with the last-used item selected; Home jumps to the first item; Down x7 moved one screenful (7 rows visible). The hint pane under the list shows the syntax line of the highlighted row (the last row of each screenful), so each screenshot shows one hint. On some screens the top row is clipped by half a row, so one row may be missing at a few screen boundaries (marked "top clipped"). The Claude window sometimes covered the right of the screen; list names stay readable. A wizard icon (starburst) marks entries that open a wizard; "Wizards On" checkbox is unticked.

## C1 Catalog tab 1 (alphabetical list), 63 screens
Tab bar: 1 (book, selected on open), 2 (integral/sigma), 3 (units), 4 (symbols), 5 (templates), 6 (libraries). Order observed: A to Z entries, then operators and symbols, ending at 10^( ; one further Down wrapped to the top (abs(). The list is not strictly alphabetical for symbols (Greek and operator characters sit among the letters, for example Σ( and Π( between P and Q entries and after sqrt/sum).

Format below: screen number | the 7 rows visible (top to bottom) | hint pane text for the last row. File: pages-shots/C1-tab1-catalog-<number>.png. "*" after a name is a wizard icon.

001 | abs( ; amortTbl( ; and ; angle( ; ANOVA* ; ANOVA2way* ; Ans   | hint: abs(Expr)   (* = wizard icon)
002 | approx( ; ▶approxFraction( ; approxRational( ; arccos( ; arccosh( ; arccot( ; arccoth( | hint: arccoth(Expr)
003 | arccsc( ; arccsch( ; arcsec( ; arcsech( ; arcsin( ; arcsinh( ; arctan( | hint: arctan(Expr)  (Claude window covered right of screen)
004 | arctanh( ; arcLen( ; avgRC( ; augment( ; bal( ; ▶Base2 ; ▶Base10 | hint: Integer ▶Base10
005 | ▶Base16 ; binomCdf(* ; binomPdf(* ; ceiling( ; centralDiff( ; cFactor( ; char( | hint: char(Integer)
006 | charPoly( ; χ²2way* ; chi22way ; χ²Cdf(* ; chi2Cdf( ; χ²GOF* ; chi2GOF* | hint: chi2GOF obsList, expList, df
007 | χ²Pdf(* ; chi2Pdf(* ; Clear ; ClearAZ* ; ClrErr ; colAugment( ; colDim( | hint: colDim(Matrix)
008 | colNorm( ; comDenom( ; completeSquare( ; conj( ; constructMat( ; CopyVar ; corrMat( | hint: corrMat(List1, List2 [,... [,List20]])
009 | cos( ; cos⁻¹( ; ▶cos ; cosh( ; cosh⁻¹( ; cot( ; cot⁻¹( | hint: cot⁻¹(Expr)
010 | coth( ; coth⁻¹( ; count( ; countIf( ; cPolyRoots(* ; crossP( ; csc( | hint: csc(Expr)
011 | csc⁻¹( ; csch( ; csch⁻¹( ; cSolve( ; CubicReg* ; cumulativeSum( ; Cycle | hint: function logic statement (Cycle)
012 | ▶Cylind ; cZeros( ; dbd( ; dbd_DMY( ; dbd_MDY( ; d( (italic) ; ▶DD | hint: Number ▶DD
013 | ▶Decimal ; Define ; Define LibPriv ; Define LibPub ; deltaList( ; deltaTmpCnv( ; DelVar | hint: DelVar Var1 [, Var2] [, Var3] ...
014 | delVoid( ; derivative( ; deSolve(* ; det( ; diag( ; dim( ; Disp | hint: Disp exprOrString1 [,exprOrString2]...
015 | DispAt ; domain( ; dominantTerm( ; ▶DMS ; dotP( ; DrawArc ; DrawCircle | hint: DrawCircle x, y, radius
016 | DrawLine ; DrawPoly ; DrawRect ; DrawText ; E (small) ; e^( ; eff( | hint: eff(nominalRate, CpY)
017 | eigVc( ; eigVl( ; Else ; ElseIf ; EndFor ; EndFunc ; EndIf | hint: If BooleanExpr Statement (EndIf; text cut by Claude window)
018 | EndLoop ; EndPrgm ; EndTry ; EndWhile ; errCode ; euler( ; exact( | hint: exact(Expr[,Tolerance])
019 | Exit ; exp( ; ▶exp ; expand( ; exp▶list( ; expr( ; ExpReg* | hint: ExpReg X,Y[,[Freq][,Category,Include]]
020 | (top row clipped) factor( ; false ; FCdf(* ; FCdf(* ; Fill ; FillArc ; FillCircle | hint: FillCircle x, y, radius
021 | FillPoly ; FillRect ; FiveNumSummary ; floor( ; fMax( ; fMin( ; For | hint: For Var, Low, High [,Step] (Claude window over right side)
022 | format( ; fPart( ; FPdf(* ; FPdf(* ; freqTable▶list( ; frequency( ; FTest_2Samp* | hint: FTest_2Samp
023 | FTest_2Samp* ; Func ; gcd( ; geomCdf(* ; geomPdf(* ; Get ; getDenom( | hint: getDenom(Expr)
024 | (top row clipped) getKey( ; getLangInfo() ; getLockInfo( ; getMode( ; getNum( ; getPlatform( ; GetStr | hint: GetStr [promptString,] Var [, statusVar]
025 | getType( ; getVarInfo( ; Goto ; ▶Grad ; identity( ; If ; ifFn( | hint: ifFn(BooleanExpr,Value_If_true [,Value_If_fal... (hint box truncated)
026 | imag( ; impDif( ; inString( ; int( ; intDiv( ; ∫( ; integral( | hint: integral(Expr, Var[, Lower, Upper])
027 | (top row clipped) interpolate( ; invBinom(* ; invBinomN(* ; invχ²(* ; invChi2(* ; invF(* ; invF(* | hint: invF(Area, dfNumer, dfDenom)
028 | (top clipped) invNorm(* ; invt(* ; iPart( ; irr( ; isPrime( ; isVoid( ; Lbl | hint: Lbl labelName
029 | lcm( ; left( ; LibPriv ; LibPub ; libShortcut( ; lim( ; limit( | hint: limit(Expr, Var, Value [,Direction])
030 | (top rows clipped) LinRegMx ; LinRegBx ; LinRegtIntervals ; LinRegtTest ; linSolve( ; ΔList( ; list▶mat( | hint: list▶mat(List[,elementsPerRow]) (Claude window over right side)
031 | ln( ; ▶ln ; LnReg* ; Local ; Lock ; log( ; ▶logbase( | hint: Expr1 ▶logbase(Expr2)
032 | (top clipped) Logistic* ; LogisticD* ; Loop ; LU ; mat▶list( ; max( ; mean( | hint: mean(List[, freqList])
033 | median( ; MedMed* ; mid( ; min( ; mirr( ; mod( ; mRow( | hint: mRow(Expr, Matrix, Index)
034 | mRowAdd( ; MultReg* ; MultRegIntervals* ; MultRegTests* ; nand ; nCr( ; nDerivative( | hint: nDerivative(Expr, Var=Value [,Order])
035 | newList( ; newMat( ; nfMax( ; nfMin( ; nInt( ; nom( ; nor | hint: BooleanExpr1 nor BooleanExpr2 (Claude window over right)
036 | norm( ; normalLine( ; normCdf(* ; normPdf(* ; not ; nPr( ; npv( | hint: npv(interestRate, CF0, CFList[,CFFreq])
037 | nSolve( ; OneVar* ; or ; ord( ; P▶Rx( ; P▶Ry( ; PaintBuffer | hint: PaintBuffer
038 | PassErr ; piecewise( ; PlotXY ; poissCdf( ; poissPdf( ; ▶Polar ; polyCoeffs( | hint: polyCoeffs(Poly[,Var]) (Claude window over right)
039 | (top clipped) polyDegree( ; polyEval( ; polyGcd( ; polyQuotient( ; polyRemainder( ; polyRoots(* ; PowerReg* | hint: PowerReg X,Y[,[Freq][,Category,Include]]
040 | (top clipped) Prgm ; Π( ; prodSeq( ; product( ; propFrac( ; QR ; QuadReg* | hint: QuadReg X,Y[,[Freq][,Category,Include]]
041 | QuartReg* ; R▶Pθ( ; R▶Pr( ; ▶Rad ; rand( ; randBin( ; randInt( | hint: randInt(lowBound, upBound[,#Trials])
042 | randMat( ; randNorm( ; randPoly( ; randSamp( ; RandSeed ; real( ; ▶Rect | hint: Vector ▶Rect
043 | ref( ; remain( ; Request ; RequestStr ; Return ; right( ; rk23( | hint: rk23(Expr, Var, depVar, {Var0, VarMax}, ... (Claude window over right)
044 | root( ; rotate( ; round( ; rowAdd( ; rowDim( ; rowNorm( ; rowSwap( | hint: rowSwap(Matrix, rIndex1, rIndex2)
045 | rref( ; sec( ; sec⁻¹( ; sech( ; sech⁻¹( ; Send ; seq( | hint: seq(Expr, Var, Low, High[,Step])
046 | seqn( ; seqGen( ; series( ; SetColor ; setMode( ; SetPen ; SetWindow | hint: SetWindow xMin, xMax, yMin, yMax
047 | shift( ; sign( ; simult( ; sin( ; sin⁻¹( ; ▶sin ; sinh( | hint: sinh(Expr)
048 | sinh⁻¹( ; SinReg ; solve( ; solve( system ; SortA ; SortD ; ▶Sphere | hint: Vector ▶Sphere (Claude window over right)
049 | (top clipped) sqrt( ; Stat.results ; stDevPop( ; stDevSamp( ; Stop ; string( ; subMat( | hint: subMat(Matrix, [startRow], [startCol], ...
050 | (top clipped) Σ( ; sum( ; sumIf( ; ΣInt( ; ΣPrn( ; sumSeq( ; system( | hint: system(Eqn1[,Eqn2[,Eqn3[,...]]])
051 | (top clipped, a small mark) tan( ; tan⁻¹( ; tanh( ; tanh⁻¹( ; tangentLine( ; taylor( | hint: taylor(Expr, Var, Order[,Value])
052 | (top clipped) tCdf(* ; tCollect( ; tExpand( ; Text ; Then ; tInterval* ; tInterval_2Samp* | hint: tInterval_2Samp
053 | (top clipped) tmpCnv( ; ΔtmpCnv( ; trace( ; true ; Try ; tPdf(* ; tTest* | hint: tTest μ0,List[,Freq[,Hypoth]]
054 | tTest_2Samp* ; tvmFV( ; tvmI( ; tvmN( ; tvmPmt( ; tvmPV( ; TwoVar* | hint: TwoVar X,Y[,[Freq][,Category,Include]]
055 | undef ; unitV( ; Unlock ; UseBuffer ; varPop( ; varSamp( ; Wait | hint: Wait timeInSeconds
056 | warnCodes( ; when( ; While ; xor ; zeros( ; zInterval* ; zInterval_1Prop* | hint: zInterval_1Prop x,n[,CLevel]
057 | zInterval_2Prop* ; zInterval_2Samp* ; zTest* ; zTest_1Prop* ; zTest_2Prop* ; zTest_2Samp* ; → | hint: Expr → Var
058 | =: ; := ; _ ; ▶ ; ° ; ʳ (radian mark) ; ᵍ (gradian mark) | hint: Expr^g
059 | (top clipped) ' ; ∠ ; = ; ≠ ; < ; ≤ ; > | hint: Expr1 > Expr2 (Claude window over right)
060 | ≥ ; − (minus) ; + ; − (negate) ; * ; / ; ^ | hint: Expr1^Expr2 (Claude window over right)
061 | .+ ; .− ; .* ; ./ ; .^ ; ᵀ (transpose) ; √( | hint: √(Expr)
062 | Π( ; Σ( ; d( ; ∫( ; ! ; © ; # | hint: # varNameString
063 | & ; % ; | ; ⇒ ; ⇔ ; e^( ; 10^( | hint: 10^(Expr) (Claude window over right)
(next press of Down wrapped to the top of the list: abs( amortTbl( and angle( ANOVA ... ; two wrap screens not kept)

## C1 Catalog tab 2 (tree of categories)
Observed: a tree with plus-boxes. Top-level rows in order: Number, Angle, List, Matrix, Vector, Algebra, Trigonometry, Hyperbolic, Calculus, Probability, Statistics, Finance, Test, Base. Right on Number expanded it to: Convert to Decimal, Approximate to Fraction, Factor, Least Common Multiple, Greatest Common Divisor, Remainder, Fraction Tools (+), Number Tools (+), Complex Number Tools (+). The hint pane shows only the row name here. Only the Number category was expanded; the other 13 categories were not opened.
Screenshot: pages-shots/C1-tab2-categories-001.png, C1-tab2-categories-002.png, C1-tab2-categories-003-bottom.png, C1-tab2-number-expanded.png, C1-tab2-number-tools-algebra.png, C1-tab2-trig-to-test.png, C1-tab2-matrix-selected-wrap.png
Differs from CASSim or from this file's expectation? not known

## Tabs 3 to 6 (first screens only)
- Tab 3 (units): rows Conversion Assistant, Conversion Symbol (▶), Constants (+), Length (+), Area (+), Volume (+), Time (+), Velocity (+) (screens 1 and 2). Screenshot: C1-tab3-first.png, C1-tab3-second.png.
- Tab 4 (symbols): grid of characters; first screen starts π, e, i, E (small), ∞, θ, →, _, ▶, °, r(radian mark), g, ', ∠, =, ≠, <, ≤, >, ≥, −, +, −, *, ·, ×, /, ÷, ^, ±, T, √, Π (selected, hint "n-ary product"), Σ, d, ∫, !, ©, @, #, $, %, &, |, ", :, ;, ,, ., ?, (, ), {, }, [ ; the next screen shows ], x̄, ȳ, Σ, µ, σ, F, χ, superscripts, p̂, ŷ, c, n, Δ, µ, Greek capitals and small letters (selected: λ, hint "Greek small letter lambda"). Screenshot: C1-tab4-symbols-first.png, C1-tab4-symbols-second.png.
- Tab 5 (templates): the same 21 template icons as the Templates key (fraction, power, square root, nth root, e^, log, piecewise 2/3/n, system 2/n, absolute value, DMS, matrices 2x2/1x2/2x1/3x3?, sum, product, derivative, 2nd derivative, nth derivative, definite integral, integral, limit, and a box icon). Hint pane for the first: "fraction". Screenshot: C1-tab5-templates.png.
- Tab 6 (libraries): tree rows Current Problem (+), gm_data (+), gm_fin (+), gm_mat (+), gm_net (+), linalg (+), linalgcas (+); not expanded. Screenshot: C1-tab6-libraries.png.
Differs from CASSim or from this file's expectation? not known

## C2 Syntax hints
The hint pane was read for the 63 screens of tab 1 (one entry per screen, the highlighted bottom row), see the list above. Overload lines beyond the first were not seen (the pane shows one line; long hints were truncated in the pane, for example ifFn and subMat and rk23). Hints for the other six rows of each screen were not read.
Screenshot: see C1-tab1-catalog-*.png
Differs from CASSim or from this file's expectation? not known

## C3 One example per command (partial, sample only)
The Reference Guide was not consulted in this run, so no match against the guide's printed result was checked. Typed lines were chosen by me, not taken from the guide.

| command | settings | typed | displayed | matches guide? | screenshot |
|---|---|---|---|---|---|
| iPart( | Radian, Automatic, Real, Float 8 | iPart(-1.234) | -1. | not checked | C3-group1-iPart-to-tanh.png |
| isPrime( | same | isPrime(7) | true | not checked | same |
| left( | same | left({1,3,-2,4},2) | {1,3} | not checked | same |
| right( | same | right({1,3,-2,4},2) | {-2,4} | not checked | same |
| remain( | same | remain(7,-3) | 1 | not checked | same |
| tanh( | same | tanh(1.2) | 0.83365461 | not checked | same |
| rotate( | same | rotate({1,2,3,4}) | {4,1,2,3} | not checked | C3-group2-rotate-char-RandSeed-rand.png |
| char( | same | char(38) | "&" | not checked | same |
| RandSeed | same | RandSeed 1 | Done | not checked | same |
| rand() | same, after RandSeed 1 | rand() three times | 0.74556077, 0.8559006, 0.22536006 | not checked | same |

Also typed (newList(4), trace([1,2;3,4]), shift({1,2,3,4})): their output scrolled off before it was captured, so no result is recorded.
Differs from CASSim or from this file's expectation? not known

## Lists

### Run on the emulator
C1 tab 1 (full list, 63 screens, hint of one row per screen), C1 tab 2 (category rows and the Number expansion), tabs 3 to 6 (first screens), C2 for the highlighted row of each tab-1 screen, C3 for the ten commands in the table above.

### Not run, with reasons
- C1 tab 2: the other 13 categories were not expanded; Number Tools, Fraction Tools and Complex Number Tools sub-lists not opened (time).
- C1 tabs 3, 4, 6: only the first screens; the sub-lists under tab 3 and the libraries under tab 6 were not expanded (time).
- C2: hint panes for the 6 non-highlighted rows of each screen, and full overload lines for long hints (pane truncates; time).
- C3: about 190 of the roughly 200 commands in groups 1 to 3 (no Reference Guide lookup, time); the Group 3 stat.results matrices; Group 2 commands.
- Programming commands skipped as instructed.

### Also seen, not covered
- The wizard icons on statistics, regression, test and interval entries (ANOVA, ANOVA2way, binomCdf, binomPdf, ClearAZ, cPolyRoots, deSolve, polyRoots, normCdf, normPdf, OneVar, TwoVar, the regression commands, invBinom, invNorm, invt and others); the wizards were not opened.
- Catalog contains Stat.results, Send, Get, GetStr, SetPen, PlotXY, UseBuffer and similar entries beyond the commands in the spec.
- Library tab lists gm_data, gm_fin, gm_mat, gm_net, linalg and linalgcas in this build.
- iPart(-1.234) shows a trailing decimal point (-1.), which follows from the decimal argument; not compared with CASSim.
