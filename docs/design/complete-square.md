# Complete the Square

`completeSquare` rewrites a quadratic expression as a sum of completed-square terms. It accepts
an expression or equation followed by one variable, a variable raised to a rational power, or
multiple variables supplied as separate arguments or as a list. For a univariate expression
`a*x^2+b*x+c`, the completed form is `a*(x+b/(2*a))^2+c-b^2/(4*a)`. For an equation, the
completed quadratic is written equal to the remaining value.

When completing more than one variable, the command completes each variable's pure quadratic and
linear terms in order. Cross terms between the requested variables remain in the residual
expression; they are not absorbed into a shifted square. For example, the supplied image shows
`completeSquare(-2*a^2-a+b^2-5*b+a*b,{a,b})` retaining `a*b` outside the two completed squares.

The function is registered in the algebra catalog, accepts a variable or a brace-enclosed list,
and is available from Algebra > Complete the Square.

## Evidence

- The TI-Nspire CAS Reference Guide 3.2, printed p. 20 (PDF p. 26), documents the
  expression/equation forms, single-variable and rational-power variable forms, and
  multiple-variable argument forms.
- The simulator example `completeSquare(x^2+4*x+1,x)` gives `(x+2)^2-3` in
  [emulator-calc4-results.md](../testing/emulator-calc4-results.md).
- The additional univariate and multivariate examples are transcribed from a user-provided
  screenshot and retained in the golden corpus as unverified expectations.
