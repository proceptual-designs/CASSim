import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

T = standard_transformations + (implicit_multiplication_application, convert_xor)


class Problem:
    def __init__(s):
        s.vars = {}

    def ev(s, line):
        line = line.strip()
        m = re.match(r"^(\w+)\(([\w,]*)\)\s*:=\s*(.+)$", line)
        if m:
            n, a, b = m.groups()
            args = sp.symbols(a)
            s.vars[n] = sp.Lambda(args, parse_expr(b, transformations=T, local_dict=s.ns()))
            return "Done"
        m = re.match(r"^(.+?)\s*(?:→|->)\s*(\w+)$", line)
        if m:
            v = s.ev(m.group(1))
            s.vars[m.group(2)] = v
            return v
        m = re.match(r"^(\w+)\s*:=\s*(.+)$", line)
        if m:
            v = s.ev(m.group(2))
            s.vars[m.group(1)] = v
            return v
        line = line.replace("√(", "sqrt(").replace("≤", "<=").replace("≥", ">=").replace("π", "pi")
        return eval_ti(line, s)

    def ns(s):
        d = dict(s.vars)
        d.update(x=sp.Symbol("x", real=True), e=sp.E, i=sp.I)
        return d


def eval_ti(line, s):
    cond = None
    if "|" in line:
        line, cond = [p.strip() for p in line.rsplit("|", 1)]

    def solve(eq, v):
        v = sp.Symbol(str(v), real=True)
        e = eq if not isinstance(eq, sp.Basic) else eq
        sol = sp.solve(e, v, dict=False)
        if cond:
            sol = [
                r
                for r in sol
                if sp.simplify(parse_expr(cond.replace(str(v), "(%s)" % r), transformations=T))
                == True
            ]
        return sol

    ns = s.ns()
    ns.update(
        solve=solve,
        derivative=lambda f, v: sp.diff(f, v),
        expand=sp.expand,
        factor=sp.factor,
        integral=lambda f, v, a=None, b=None: (
            sp.integrate(f, v) if a is None else sp.integrate(f, (v, a, b))
        ),
        det=lambda m: m.det(),
        limit=sp.limit,
        Eq=sp.Eq,
    )
    # '=' -> Eq inside solve(...)
    line = re.sub(r"solve\((.+?)=(.+?),", r"solve(Eq(\1,\2),", line)
    # matrices [1,2;3,4]
    line = re.sub(
        r"\[([^\[\]]*;[^\[\]]*)\]",
        lambda m: "Matrix([" + ",".join("[" + r + "]" for r in m.group(1).split(";")) + "])",
        line,
    )
    ns["Matrix"] = sp.Matrix
    return parse_expr(line, transformations=T, local_dict=ns)


p = Problem()
for l in [
    "f(x):=x^2-4",
    "solve(f(x)=0,x)",
    "solve(f(x)=0,x)|x>0",
    "5→a",
    "a*2",
    "derivative(f(x),x)",
    "integral(f(x),x,0,2)",
    "2x(x-1)",
    "det([1,2;3,4])",
    "expand((x+1)^3)",
    "√(2)+π",
]:
    try:
        print("%-26s -> %s" % (l, p.ev(l)))
    except Exception as e:
        print("%-26s -> ERR %r" % (l, e))
