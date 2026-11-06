"""Print engine LaTeX for a fixed set of entries (input for spike 5)."""

import json

from cassim.core.session import Session

ENTRIES = [
    "1/3+1/4",
    "solve(x^2-5x+6=0,x)",
    "√(8)",
    "d/dx(x^3*sin(x))",
    "∫(x^2,x,0,2)",
    "∫(ⅇ^(-x^2),x)",
    "limit(sin(x)/x,x,0)",
    "[[1,2],[3,4]]^-1",
    "{1,2,3}",
    "(x^2-1)/(x+1)",
    "expand((x+1)^5)",
    "ⅇ^(ⅈ*π/3)",
    "Σ(1/n^2,n,1,∞)",
    "[[1,3/2],[-x/2,√(2)]]",
    "piecewise(x,x≥0,-x)",
    "sin⁻¹(1/2)+ln(x)",
    "abs(x-1)",
    "(x^2+1)^(1/3)",
    "solve(x^2+y^2=1,y)",
    "√(2)/2+ⅇ^2",
]
s = Session()
out = []
for e in ENTRIES:
    r = s.eval(e)
    out.append({"in": e, "text": r.text, "latex": r.latex, "error": r.error})
print(json.dumps(out, ensure_ascii=False, indent=1))
