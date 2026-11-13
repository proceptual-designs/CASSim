"""Spike C (decision 0031), engine side: SymPy expression to Python source over `math`.

Prints the source the UI worker would sample (see `spikes/spike_c_web`) and the time to make it.
"""

import time

import sympy as sp

x = sp.Symbol("x")
EXPRS = {
    "sin": sp.sin(x) + sp.Rational(3, 10) * sp.sin(7 * x),
    "cubic": x**3 / 10 - x,
    "recip": 1 / x,
    "sqrt": sp.sqrt(x),
    "gauss": sp.exp(-(x**2) / 2),
    "tan": sp.tan(x),
    "abs_piecewise": sp.Piecewise((x**2, x < 1), (2 - x, True)) + sp.Abs(x),
}

for name, expr in EXPRS.items():
    start = time.perf_counter()
    source = sp.pycode(expr, fully_qualified_modules=True)
    print(f"SPIKE: {name}: {(time.perf_counter() - start) * 1000:.2f} ms  {source}")
