import time

t = time.time()
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
    rationalize,
)

print("import sympy %.2fs" % (time.time() - t))
T = standard_transformations + (implicit_multiplication_application, convert_xor)
x, y, k = sp.symbols("x y k", real=True)


def P(s):
    return parse_expr(s, transformations=T, local_dict={"x": x, "y": y, "k": k, "e": sp.E})


tests = [
    ("solve x^2-4=0", lambda: sp.solve(P("x^2-4"), x)),
    ("solve ax^2 (implicit mult)", lambda: P("2x(x-1)")),
    ("factor", lambda: sp.factor(P("x^4-1"))),
    ("complex factor", lambda: sp.factor(P("x^2+1"), extension=sp.I)),
    ("deriv", lambda: sp.diff(P("x^2*sin(x)"), x)),
    ("integral", lambda: sp.integrate(P("x*exp(x)"), (x, 0, 1))),
    ("limit", lambda: sp.limit(P("sin(x)/x"), x, 0)),
    ("propFrac", lambda: sp.apart(P("(x^2+1)/(x-1)"), x)),
    ("solve exp", lambda: sp.solve(sp.Eq(sp.exp(x), 5), x)),
    ("solve trig", lambda: sp.solve(sp.sin(x) - sp.Rational(1, 2), x)),
    ("system", lambda: sp.solve([x + y - 3, x - y - 1], [x, y])),
    (
        "norm cdf exact",
        lambda: sp.N(sp.Rational(1, 2) * (1 + sp.erf(sp.Rational(1, 1) / sp.sqrt(2))), 8),
    ),
    ("det", lambda: sp.Matrix([[1, 2], [3, 4]]).det()),
    (
        "deSolve",
        lambda: sp.dsolve(
            sp.Function("y")(x).diff(x) - sp.Function("y")(x),
            sp.Function("y")(x),
            ics={sp.Function("y")(0): 2},
        ),
    ),
    ("cubic exact", lambda: sp.solve(x**3 - x - 1, x)),
    ("fMin", lambda: sp.minimum(x**2 - 4 * x, x)),
    ("nInt", lambda: sp.N(sp.Integral(sp.exp(-(x**2)), (x, 0, 1)), 8)),
]
for n, f in tests:
    t = time.time()
    try:
        r = f()
    except Exception as e:
        r = "ERR %r" % e
    print("%-24s %6.3fs  %s" % (n, time.time() - t, str(r)[:90]))
