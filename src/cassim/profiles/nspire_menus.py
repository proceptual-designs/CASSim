"""The TI-Nspire CX CAS menus and dialogs as data (FR-DEV-001, FR-DEV-007, FR-CALC-005).

Checked against the Teacher Software on 2026-11-08 (`docs/testing/emulator-menus-results.md`):
every menu lists the device's items in the device's order with its numbers, so `menu 3 1` is Solve
and `menu 5 5 2` is Normal Cdf… as on the handheld. Items CASSim cannot do yet are greyed
placeholders (`todo`) in their real places; a placeholder submenu still opens and shows the device's
items, all greyed. A label ending in `…` opens a dialog (a `Wizard`).
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from cassim.core.compat import finance as fin
from cassim.device.keys import Binding
from cassim.device.menu import MenuItem
from cassim.device.wizard import Field, Wizard
from cassim.profiles.nspire_syntax import COMMANDS, CONVERSIONS, FUNCTIONS

NOT_YET = "Not in CASSim yet"


def fn(label: str, name: str, key: str = "") -> MenuItem:
    """A leaf that types `name(`, with its syntax hint (`√` is the root template)."""
    if name == "√":
        return MenuItem(label, "template", "root", key=key, hint=FUNCTIONS[name])
    return MenuItem(label, "insert", f"{name}(", key=key, hint=FUNCTIONS[name])


def cmd(label: str, name: str, key: str = "") -> MenuItem:
    """A leaf that types a command, and a space if it takes arguments (`SortA `)."""
    text = f"{name} " if " " in COMMANDS[name] else name
    return MenuItem(label, "insert", text, key=key, hint=COMMANDS[name])


def conv(label: str, text: str, key: str = "") -> MenuItem:
    """A leaf that types a conversion written after its value (`▶Decimal`)."""
    return MenuItem(label, "insert", text, key=key, hint=CONVERSIONS[text])


def sub(label: str, key: str, *items: MenuItem) -> MenuItem:
    return MenuItem(label, items=items, key=key)


def wiz(label: str, name: str, key: str = "", hint: str = "") -> MenuItem:
    """A leaf that opens dialog `name`; the hint is the command it pastes."""
    return MenuItem(f"{label}…", "wizard", name, key=key, hint=hint)


def todo(label: str, key: str = "") -> MenuItem:
    """A greyed placeholder for a device item CASSim cannot do yet: it keeps its number so the
    keys match the handheld."""
    return MenuItem(label, key=key, hint=NOT_YET, enabled=False)


def todo_sub(label: str, key: str, *labels: str) -> MenuItem:
    """A device submenu none of whose items CASSim has yet: it opens, showing them greyed."""
    return MenuItem(label, key=key, items=tuple(todo(name) for name in labels))


def call(name: str, *args: str) -> str:
    """`name(a,b,c)` with empty trailing arguments dropped (they are optional)."""
    kept = list(args)
    while kept and not kept[-1]:
        kept.pop()
    return f"{name}({','.join(kept)})"


# ---- dialogs ----------------------------------------------------------------------------------

_MU, _SIGMA = Field("mu", "μ", "0"), Field("sigma", "σ", "1")
_LOWER = Field("lower", "Lower Bound", "-∞")  # the device's default is the symbol −∞
_UPPER = Field("upper", "Upper Bound")
_X = Field("x", "X Value")
_AREA = Field("area", "Area")
_DF = Field("df", "Deg of Freedom, df")
_DFN, _DFD = Field("dfn", "Num df"), Field("dfd", "Den df")
_N, _P = Field("n", "Num Trials, n"), Field("p", "Prob Success, p")
_LAMBDA = Field("lam", "λ")
_FREQ = Field("freq", "Frequency List", "1")
_ORDER = Field(
    "order", "Derivative", "1", choices=(("1", "1st Derivative"), ("2", "2nd Derivative"))
)
_SYSTEM_FIELDS = (
    Field("count", "Number of equations", "2", whole=(1, 20)),
    Field("vars", "Variables", "x,y"),
)


def _dist(title: str, name: str, *fields: Field) -> Wizard:
    """A distribution dialog: pastes `name(fields…)` and runs it on OK, as the handheld does."""
    names = [field.name for field in fields]
    return Wizard(title, fields, run=True, build=lambda v: call(name, *(v[n] for n in names)))


def _derivative_at(v: Mapping[str, str]) -> list[Binding]:
    """d/dx(□)|x=Value, as the device pastes it: the variable filled in, the cursor in the box."""
    kind = "derivative" if v["order"] == "1" else "derivative2"
    after = f"|{v['var']}={v['value']}"
    return [
        Binding("template", kind),
        Binding("insert", v["var"]),
        Binding("tab"),  # to the expression
        Binding("tab"),  # out of the template
        Binding("insert", after),
        *(Binding("left") for _ in after),
        Binding("left"),  # back into the expression
    ]


def _system(v: Mapping[str, str], command: str = "solve") -> list[Binding]:
    """`solve(` (or `linSolve(`) with the device's system template and the variables; the
    cursor in the first equation."""
    count, after = int(v["count"]), f",{{{v['vars']}}})"
    return [
        Binding("insert", f"{command}("),
        Binding("template", f"system:{count}"),
        *(Binding("tab") for _ in range(count)),  # out of the template
        Binding("insert", after),
        *(Binding("left") for _ in after),
        Binding("left"),  # into the last equation
        *(Binding("shift_tab") for _ in range(count - 1)),  # back to the first
    ]


def _desolve(v: Mapping[str, str]) -> str:
    """deSolve(equation and conditions, x, y), as the device's dialog pastes it."""
    parts = [v["equation"], *(v[name] for name in ("c1", "c2") if v[name])]
    return f"deSolve({' and '.join(parts)},{v['x']},{v['y']})"


def polynomial(coefficients: str, var: str) -> str:
    """`1,-3,2` in `x` is `x^2-3*x+2` (highest power first)."""
    parts = [c.strip() for c in coefficients.split(",") if c.strip()]
    terms: list[str] = []
    for power, part in zip(range(len(parts) - 1, -1, -1), parts, strict=True):
        if part == "0":
            continue
        c = f"({part})" if any(op in part[1:] for op in "+-") else part
        var_part = "" if power == 0 else var if power == 1 else f"{var}^{power}"
        if not var_part:
            terms.append(c)
        elif c in ("1", "-1"):
            terms.append(c[:-1] + var_part)
        else:
            terms.append(f"{c}*{var_part}")
    return "+".join(terms).replace("+-", "-") or "0"


def _poly_roots(v: Mapping[str, str]) -> str:
    name = "polyRoots" if v["roots"] == "real" else "cZeros"
    return f"{name}({polynomial(v['coeffs'], v['var'])},{v['var']})"


def _regression(title: str, command: str) -> Wizard:
    """Stat Calculations: run the command and show `stat.results` at once, as the handheld does.
    (The device also offers "Save RegEqn to", which needs `CopyVar`.)"""
    fields = (Field("x", "X List"), Field("y", "Y List"), _FREQ)
    return Wizard(title, fields, command + " {x},{y},{freq}: stat.results", run=True)


_TVM_ORDER = ("n", "i", "pv", "pmt", "fv")
_TVM_LABELS = {
    "n": "N",
    "i": "I (%)",
    "pv": "PV",
    "pmt": "Pmt",
    "fv": "FV",
    "ppy": "PpY",
    "cpy": "CpY",
}


def _number(v: Mapping[str, str], name: str) -> float:
    """A box of the Finance Solver as a number: decimals, `ᴇ` or `E`, a fraction `a/b`."""
    text = v.get(name, "").strip().replace("ᴇ", "e").replace("−", "-")
    try:
        top, _, bottom = text.partition("/")
        return float(top) / float(bottom) if bottom else float(top)
    except ValueError, ZeroDivisionError:
        raise ValueError(f"{_TVM_LABELS[name]}: enter a number") from None


def _shown(number: float) -> str:
    text = f"{number:.9g}"  # the iterative interest solve is good to about 9 digits
    return "0" if text == "-0" else text


def finance_calculate(v: Mapping[str, str], target: str) -> dict[str, str]:
    """The Finance Solver's live calculation (the handheld's: put the cursor in a box, press
    Enter): `target` is worked out from the other four values and the timing."""
    if target not in _TVM_ORDER:
        raise ValueError("Choose N, I (%), PV, Pmt or FV to calculate")
    known = {name: _number(v, name) for name in (*_TVM_ORDER, "ppy", "cpy") if name != target}
    pp, cp, at = known["ppy"], known["cpy"], 1 if v.get("pmtat") == "1" else 0
    rate = fin.period_rate(known["i"], pp, cp) if target != "i" else 0.0
    n, pv, pmt, fv = (known.get(name, 0.0) for name in ("n", "pv", "pmt", "fv"))
    solvers = {
        "n": lambda: fin.periods(rate, pv, pmt, fv, at),
        "i": lambda: fin.nominal_percent(fin.interest_rate(n, pv, pmt, fv, at), pp, cp),
        "pv": lambda: fin.present_value(n, rate, pmt, fv, at),
        "pmt": lambda: fin.payment(n, rate, pv, fv, at),
        "fv": lambda: fin.future_value(n, rate, pv, pmt, at),
    }
    try:
        answer = solvers[target]()
    except ValueError, ZeroDivisionError, OverflowError:
        raise ValueError(f"{_TVM_LABELS[target]}: no solution for these values") from None
    if not math.isfinite(answer):
        raise ValueError(f"{_TVM_LABELS[target]}: no solution for these values")
    return {**v, target: _shown(answer)}


_REGRESSIONS = (
    ("Linear Regression (mx+b)", "LinRegMx", "3"),
    ("Linear Regression (a+bx)", "LinRegBx", "4"),
    ("Median-Median Line", "MedMed", "5"),
    ("Quadratic Regression", "QuadReg", "6"),
    ("Cubic Regression", "CubicReg", "7"),
    ("Quartic Regression", "QuartReg", "8"),
    ("Power Regression", "PowerReg", "9"),
    ("Exponential Regression", "ExpReg", "A"),
    ("Logarithmic Regression", "LnReg", "B"),
    ("Sinusoidal Regression", "SinReg", "C"),
    ("Logistic Regression (d=0)", "Logistic", "D"),
    ("Logistic Regression (d≠0)", "LogisticD", "E"),
)

_BOUNDS_FROM_0 = (Field("lower", "Lower Bound", "0"), Field("upper", "Upper Bound"))
# Dialog titles that differ from the menu label (Cowork run 2, part 2).
_DIST_TITLES = {"invBinom": "Num Successes", "invBinomN": "Num Trials"}
# In the device's order (Probability > 5 and Statistics > 5 are the same list).
_DISTRIBUTIONS = (
    ("Normal Pdf", "normPdf", "1", (_X, _MU, _SIGMA)),
    ("Normal Cdf", "normCdf", "2", (_LOWER, _UPPER, _MU, _SIGMA)),
    ("Inverse Normal", "invNorm", "3", (_AREA, _MU, _SIGMA)),
    ("t Pdf", "tPdf", "4", (_X, _DF)),
    ("t Cdf", "tCdf", "5", (_LOWER, _UPPER, _DF)),
    ("Inverse t", "invt", "6", (_AREA, _DF)),
    ("χ² Pdf", "χ²Pdf", "7", (_X, _DF)),
    ("χ² Cdf", "χ²Cdf", "8", (*_BOUNDS_FROM_0, _DF)),
    ("Inverse χ²", "invχ²", "9", (_AREA, _DF)),
    ("Binomial Pdf", "binomPdf", "A", (_N, _P, Field("x", "X Value (optional)"))),
    ("Binomial Cdf", "binomCdf", "B", (_N, _P, *_BOUNDS_FROM_0)),
    ("Inverse Binomial", "invBinom", "C", (Field("c", "Cumulative Prob"), _N, _P)),
    (
        "Inverse Binomial N",
        "invBinomN",
        "D",
        (Field("c", "Cumulative Prob"), _P, Field("x", "Successes, x")),
    ),
    ("F Pdf", "FPdf", "E", (_X, _DFN, _DFD)),
    ("F Cdf", "FCdf", "F", (*_BOUNDS_FROM_0, _DFN, _DFD)),
    ("Inverse F", "invF", "G", (_AREA, _DFN, _DFD)),
    ("Geometric Pdf", "geomPdf", "H", (_P, _X)),
    (
        "Geometric Cdf",
        "geomCdf",
        "I",
        (_P, Field("lower", "Lower Bound", "1"), Field("upper", "Upper Bound")),
    ),
    ("Poisson Pdf", "poissPdf", "J", (_LAMBDA, _X)),
    ("Poisson Cdf", "poissCdf", "K", (_LAMBDA, *_BOUNDS_FROM_0)),
)

WIZARDS: dict[str, Wizard] = {
    "derivative_at": Wizard(
        "Derivative at a Point",
        (Field("var", "Variable", "x"), Field("value", "Value"), _ORDER),
        steps=_derivative_at,
    ),
    "solve_system": Wizard("Solve a System of Equations", _SYSTEM_FIELDS, steps=_system),
    "solve_linear_system": Wizard(
        "Solve a System of Linear Equations",
        _SYSTEM_FIELDS,
        steps=lambda v: _system(v, "linSolve"),
    ),
    "desolve": Wizard(
        "Differential Equation Solver",
        (
            Field("equation", "Equation", "y'=2*y"),
            Field("x", "Independent Var", "x"),
            Field("y", "Dependent Var", "y"),
            Field("c1", "Condition (Optional)"),
            Field("c2", "Condition (Optional)"),
        ),
        run=True,
        build=_desolve,
    ),
    "piecewise": Wizard(
        "Create Piecewise Function",
        (Field("count", "Number of function pieces", "3", whole=(1, 20)),),
        template="piecewise:{count}",
    ),
    "system": Wizard(
        "Create a System of Equations",
        (Field("count", "Number of equations", "3", whole=(1, 20)),),
        template="system:{count}",
    ),
    "poly_roots": Wizard(  # the device asks the degree, then the coefficients; it does not run
        "Find Roots of a Polynomial",
        (
            Field("coeffs", "Coefficients, highest power first", "1,0,-1"),
            Field("var", "Variable", "x"),
            Field("roots", "Roots", "real", choices=(("real", "Real"), ("complex", "Complex"))),
        ),
        build=_poly_roots,
    ),
    "matrix": Wizard(
        "Create a Matrix",
        (
            Field("rows", "Number of rows", "2", whole=(1, 99)),
            Field("cols", "Number of columns", "2", whole=(1, 99)),
        ),
        template="matrix:{rows},{cols}",
    ),
    "one_var": Wizard(
        "One-Variable Statistics",
        (Field("x", "X1 List"), _FREQ),
        "OneVar {x},{freq}: stat.results",
        run=True,
    ),
    "two_var": Wizard(
        "Two-Variable Statistics",
        (Field("x", "X List"), Field("y", "Y List"), _FREQ),
        "TwoVar {x},{y},{freq}: stat.results",
        run=True,
    ),
    # Live: Enter in a box works it out. Closing pastes nothing, as on the device.
    "finance": Wizard(
        "Finance Solver",
        (
            Field("n", "N", "0"),
            Field("i", "I (%)", "0"),
            Field("pv", "PV", "0"),
            Field("pmt", "Pmt", "0"),
            Field("fv", "FV", "0"),
            Field("ppy", "PpY", "1"),
            Field("cpy", "CpY", "1"),
            Field("pmtat", "PmtAt", "0", choices=(("0", "END"), ("1", "BEGIN"))),
        ),
        calculate=finance_calculate,
        copies=(("ppy", "cpy"),),  # changing PpY changes CpY, as on the device
    ),
    **{
        name: _dist(_DIST_TITLES.get(name, title), name, *fields)
        for title, name, _, fields in _DISTRIBUTIONS
    },
    **{command.casefold(): _regression(title, command) for title, command, _ in _REGRESSIONS},
}


DISTRIBUTIONS = sub(
    "Distributions",
    "5",
    *(wiz(title, name, key, FUNCTIONS[name]) for title, name, key, _ in _DISTRIBUTIONS),
)


def _template_item(label: str, kind: str, name: str, key: str) -> MenuItem:
    """A menu item that pastes a 2D template, as the device's Calculus items do."""
    return MenuItem(label, "template", kind, key=key, hint=FUNCTIONS[name])


# The Calculator's Menu (menu key, F2 on a computer).
MENU = MenuItem(
    "Menu",
    items=(
        sub(
            "Actions",
            "1",
            cmd("Define", "Define", "1"),
            todo("Recall Definition", "2"),
            cmd("Delete Variable", "DelVar", "3"),
            cmd("Clear a-z…", "ClearAZ", "4"),
            todo("Clear History", "5"),
            todo("Insert Comment", "6"),
            todo_sub(
                "Library",
                "7",
                "Refresh Libraries",
                'Insert "\\" character',
                "Create Library Shortcut",
                "Define LibPriv",
                "Define LibPub (Show in Catalog)",
            ),
            todo_sub("Lock", "8", "Lock Variable", "Unlock Variable", "Get Lock Info"),
        ),
        sub(
            "Number",
            "2",
            conv("Convert to Decimal", "▶Decimal", "1"),
            conv("Approximate to Fraction", "▶approxFraction()", "2"),
            fn("Factor", "factor", "3"),
            fn("Least Common Multiple", "lcm", "4"),
            fn("Greatest Common Divisor", "gcd", "5"),
            fn("Remainder", "remain", "6"),
            sub(
                "Fraction Tools",
                "7",
                fn("Proper Fraction", "propFrac", "1"),
                todo("Get Numerator", "2"),
                todo("Get Denominator", "3"),
                fn("Common Denominator", "comDenom", "4"),
            ),
            sub(
                "Number Tools",
                "8",
                fn("Round", "round", "1"),
                fn("Integer Part", "iPart", "2"),
                fn("Fractional Part", "fPart", "3"),
                fn("Sign", "sign", "4"),
                fn("Mod", "mod", "5"),
                fn("Floor", "floor", "6"),
                fn("Ceiling", "ceiling", "7"),
            ),
            sub(
                "Complex Number Tools",
                "9",
                fn("Complex Conjugate", "conj", "1"),
                fn("Real Part", "real", "2"),
                fn("Imaginary Part", "imag", "3"),
                fn("Polar Angle", "angle", "4"),
                fn("Magnitude", "abs", "5"),
                conv("Convert to Polar", "▶Polar", "6"),
                conv("Convert to Rectangular", "▶Rect", "7"),
            ),
        ),
        sub(
            "Algebra",
            "3",
            fn("Solve", "solve", "1"),
            fn("Factor", "factor", "2"),
            fn("Expand", "expand", "3"),
            fn("Zeros", "zeros", "4"),
            todo("Complete the Square", "5"),
            fn("Numerical Solve", "nSolve", "6"),
            sub(
                "Solve System of Equations",
                "7",
                wiz(
                    "Solve System of Equations",
                    "solve_system",
                    "1",
                    "solve({Eq1, Eq2}, {Var1, Var2})",
                ),
                wiz(
                    "Solve System of Linear Equations",
                    "solve_linear_system",
                    "2",
                    "solve({Eq1, Eq2}, {Var1, Var2})",
                ),
            ),
            sub(
                "Polynomial Tools",
                "8",
                wiz("Find Roots of Polynomial", "poly_roots", "1", FUNCTIONS["polyRoots"]),
                fn("Real Roots of Polynomial", "polyRoots", "2"),
                fn("Complex Roots of Polynomial", "cZeros", "3"),
                todo("Remainder of Polynomial", "4"),
                todo("Quotient of Polynomial", "5"),
                todo("Greatest Common Divisor", "6"),
                todo("Coefficients of Polynomial", "7"),
                todo("Degree of Polynomial", "8"),
            ),
            sub(
                "Fraction Tools",
                "9",
                fn("Proper Fraction", "propFrac", "1"),
                todo("Get Numerator", "2"),
                todo("Get Denominator", "3"),
                fn("Common Denominator", "comDenom", "4"),
            ),
            todo_sub(
                "Convert Expression",
                "A",
                "Convert to ln",
                "Convert to logbase",
                "Convert to exp",
                "Convert to sin",
                "Convert to cos",
            ),
            sub("Trigonometry", "B", fn("Expand", "tExpand", "1"), fn("Collect", "tCollect", "2")),
            sub(
                "Complex",
                "C",
                fn("Solve", "cSolve", "1"),
                fn("Factor", "cFactor", "2"),
                fn("Zeros", "cZeros", "3"),
            ),
            sub("Extract", "D", fn("Left", "left", "1"), fn("Right", "right", "2")),
        ),
        sub(
            "Calculus",
            "4",
            _template_item("Derivative", "derivative", "derivative", "1"),
            wiz("Derivative at a Point", "derivative_at", "2", "derivative(Expr, Var)|Var=Value"),
            _template_item("Integral", "integral", "∫", "3"),
            _template_item("Limit", "limit", "limit", "4"),
            _template_item("Sum", "sum", "Σ", "5"),
            _template_item("Product", "product", "Π", "6"),
            fn("Function Minimum", "fMin", "7"),
            fn("Function Maximum", "fMax", "8"),
            fn("Tangent Line", "tangentLine", "9"),
            fn("Normal Line", "normalLine", "A"),
            todo("Arc Length", "B"),
            sub(
                "Series",
                "C",
                fn("Taylor Polynomial", "taylor", "1"),
                todo("Generalized Series", "2"),
                todo("Dominant Term", "3"),
            ),
            wiz("Differential Equation Solver", "desolve", "D", FUNCTIONS["deSolve"]),
            fn("Implicit Differentiation", "impDif", "E"),
            sub(
                "Numerical Calculations",
                "F",
                fn("Numerical Derivative at a Point", "nDerivative", "1"),  # no dialog
                todo("Central Difference Quotient with Step", "2"),
                fn("Numerical Integral", "nInt", "3"),
                todo("Numerical Function Minimum", "4"),
                todo("Numerical Function Maximum", "5"),
            ),
        ),
        sub(
            "Probability",
            "5",
            MenuItem("Factorial (!)", "insert", "!", key="1", hint="Value!"),
            fn("Permutations", "nPr", "2"),
            fn("Combinations", "nCr", "3"),
            sub(
                "Random",
                "4",
                fn("Number", "rand", "1"),
                fn("Integer", "randInt", "2"),
                fn("Binomial", "randBin", "3"),
                fn("Normal", "randNorm", "4"),
                todo("Sample", "5"),
                cmd("Seed", "RandSeed", "6"),
            ),
            DISTRIBUTIONS,
        ),
        sub(
            "Statistics",
            "6",
            sub(
                "Stat Calculations",
                "1",
                wiz("One-Variable Statistics", "one_var", "1", COMMANDS["OneVar"]),
                wiz("Two-Variable Statistics", "two_var", "2", COMMANDS["TwoVar"]),
                *(
                    wiz(title, command.casefold(), key, COMMANDS[command])
                    for title, command, key in _REGRESSIONS
                ),
                todo("Multiple Linear Regression…", "F"),
                todo("Correlation Matrix", "G"),
            ),
            MenuItem("Stat Results", "insert", "stat.results", key="2", hint="stat.results"),
            sub(
                "List Math",
                "3",
                fn("Minimum", "min", "1"),
                fn("Maximum", "max", "2"),
                fn("Mean", "mean", "3"),
                fn("Median", "median", "4"),
                fn("Sum of Elements", "sum", "5"),
                fn("Product of Elements", "product", "6"),
                fn("Sample Standard Deviation", "stDevSamp", "7"),
                fn("Sample Variance", "varSamp", "8"),
                fn("Population Standard Deviation", "stDevPop", "9"),
                fn("Population Variance", "varPop", "A"),
            ),
            sub(
                "List Operations",
                "4",
                cmd("Sort Ascending", "SortA", "1"),
                cmd("Sort Descending", "SortD", "2"),
                fn("Cumulative Sum List", "cumulativeSum", "3"),
                todo("Fill", "4"),
                fn("Sequence", "seq", "5"),
                todo("Difference List", "6"),
                fn("Augment", "augment", "7"),
                fn("Convert List to Matrix", "list▶mat", "8"),
                fn("Convert Matrix to List", "mat▶list", "9"),
                fn("Left", "left", "A"),
                todo("Mid", "B"),
                fn("Right", "right", "C"),
            ),
            DISTRIBUTIONS,
            todo_sub(
                "Confidence Intervals",
                "6",
                "z Interval…",
                "t Interval…",
                "2-Sample z Interval…",
                "2-Sample t Interval…",
                "1-Prop z Interval…",
                "2-Prop z Interval…",
                "Linear Reg t Intervals…",
                "Multiple Reg Intervals…",
            ),
            todo_sub(
                "Stat Tests",
                "7",
                "z Test…",
                "t Test…",
                "2-Sample z Test…",
                "2-Sample t Test…",
                "1-Prop z Test…",
                "2-Prop z Test…",
                "χ² GOF…",
                "χ² 2-way Test…",
                "2-Sample F Test…",
                "Linear Reg t Test…",
                "Multiple Reg Tests…",
                "ANOVA…",
                "ANOVA 2-Way…",
            ),
        ),
        sub(
            "Matrix & Vector",
            "7",
            sub(
                "Create",
                "1",
                wiz("Matrix", "matrix", "1", "Rows × columns template"),
                todo("Zero Matrix", "2"),
                fn("Identity", "identity", "3"),
                todo("Diagonal", "4"),
                todo("Random Matrix", "5"),
                todo("Fill", "6"),
                fn("Submatrix", "subMat", "7"),
                fn("Augment", "augment", "8"),
                todo("Column Augment", "9"),
                todo("Construct Matrix", "A"),
            ),
            conv("Transpose", "ᵀ", "2"),
            fn("Determinant", "det", "3"),
            todo("Row-Echelon Form", "4"),
            fn("Reduced Row-Echelon Form", "rref", "5"),
            fn("Simultaneous", "simult", "6"),
            sub("Norms", "7", fn("Norm", "norm", "1"), todo("Row", "2"), todo("Column", "3")),
            sub("Dimensions", "8", fn("Matrix", "dim", "1"), todo("Row", "2"), todo("Column", "3")),
            todo_sub(
                "Row Operations", "9", "Swap Rows", "Row Add", "Multiply Row", "Multiply Row & Add"
            ),
            todo_sub(
                "Element Operations",
                "A",
                "Dot Add",
                "Dot Subtract",
                "Dot Multiply",
                "Dot Divide",
                "Dot Power",
            ),
            sub(
                "Advanced",
                "B",
                todo("Trace", "1"),
                todo("LU Decomposition", "2"),
                todo("QR Decomposition", "3"),
                fn("Eigenvalues", "eigVl", "4"),
                fn("Eigenvectors", "eigVc", "5"),
                todo("Characteristic Polynomial", "6"),
            ),
            sub(
                "Vector",
                "C",
                fn("Unit Vector", "unitV", "1"),
                fn("Cross Product", "crossP", "2"),
                fn("Dot Product", "dotP", "3"),
                conv("Convert to Polar", "▶Polar", "4"),
                conv("Convert to Rectangular", "▶Rect", "5"),
                conv("Convert to Cylindrical", "▶Cylind", "6"),
                conv("Convert to Spherical", "▶Sphere", "7"),
            ),
        ),
        sub(
            "Finance",
            "8",
            wiz("Finance Solver", "finance", "1", "Press Enter in a box to calculate it"),
            sub(
                "TVM Functions",
                "2",
                fn("Number of Periods", "tvmN", "1"),
                fn("Interest Rate per Year", "tvmI", "2"),
                fn("Present Value", "tvmPV", "3"),
                fn("Payment Amount", "tvmPmt", "4"),
                fn("Future Value", "tvmFV", "5"),
            ),
            sub(
                "Amortization",
                "3",
                fn("Amortization Table", "amortTbl", "1"),
                fn("Balance", "bal", "2"),
                fn("Interest Paid", "ΣInt", "3"),
                fn("Principal Paid", "ΣPrn", "4"),
            ),
            todo_sub(
                "Cash Flows",
                "4",
                "Net Present Value",
                "Internal Rate of Return",
                "Modified Internal Rate of Return",
            ),
            sub(
                "Interest Conversion",
                "5",
                fn("Nominal Interest Rate", "nom", "1"),
                fn("Effective Interest Rate", "eff", "2"),
            ),
            todo_sub("Days between Dates", "6", "Month Day Format", "Day Month Format"),
        ),
        sub(
            "Functions & Programs",
            "9",
            todo_sub("Program Editor", "1", "New…", "Open…", "Import…", "View…"),
            todo("Func…EndFunc", "2"),
            todo("Prgm…EndPrgm", "3"),
            todo("Local", "4"),
            todo_sub(
                "Control",
                "5",
                "If",
                "If…Then…EndIf",
                "If…Then…Else…EndIf",
                "ElseIf…Then",
                "For…EndFor",
                "While…EndWhile",
                "Loop…EndLoop",
                "Try…Else…EndTry",
                "ClrErr",
                "PassErr",
                "errCode",
                "warnCodes",
                "Wait",
            ),
            todo_sub("Transfer", "6", "Return", "Cycle", "Exit", "Lbl", "GoTo Lbl", "Stop"),
            todo_sub(
                "I/O",
                "7",
                "Disp",
                "DispAt",
                "Request",
                "RequestStr",
                "Text",
                "getKey",
                "Get",
                "GetStr",
                "Send",
                "RefreshProbeVars",
            ),
            sub(
                "Mode",
                "8",
                todo_sub(
                    "Display Digits",
                    "1",
                    "Float",
                    "Float1",
                    "Float2",
                    "Float3",
                    "Float4",
                    "Float5",
                    "Float6",
                    "Float7",
                    "Float8",
                    "Float9",
                    "Float10",
                    "Float11",
                    "Float12",
                    "Fix0",
                    "Fix1",
                    "Fix2",
                    "Fix3",
                    "Fix4",
                    "Fix5",
                    "Fix6",
                    "Fix7",
                    "Fix8",
                    "Fix9",
                    "Fix10",
                    "Fix11",
                    "Fix12",
                ),
                todo_sub("Angle", "2", "Radian", "Degree", "Gradian"),
                todo_sub("Exponential Format", "3", "Normal", "Scientific", "Engineering"),
                todo_sub("Real or Complex", "4", "Real", "Rectangular", "Polar"),
                todo_sub("Auto or Approx", "5", "Auto", "Approximate", "Exact"),
                todo_sub("Vector Format", "6", "Rectangular", "Cylindrical", "Spherical"),
                todo_sub("Base", "7", "Decimal", "Hex", "Binary"),
                todo_sub("Unit System", "8", "SI", "Eng/US"),
                todo("Get Mode", "9"),
                todo("Get Language Info", "A"),
                todo("Get Platform Info", "B"),
            ),
            todo("Add New Line", "9"),
        ),
    ),
)

# Doc (doc key, F4), as on the device. CASSim's own extras come after the device's items.
DOC = MenuItem(
    "Doc",
    items=(
        sub(
            "File",
            "1",
            MenuItem("New Document", "new_document", key="1", hint="ctrl+N"),
            MenuItem("Open Document", "dialog", "open_file", key="2", hint="ctrl+O"),
            todo("Close", "3"),
            MenuItem("Save", "dialog", "save_file", key="4", hint="ctrl+S"),
            MenuItem("Save As…", "dialog", "save_file", key="5"),
            todo("Send", "6"),
            todo("View copyright information", "7"),
            MenuItem("Copy share link", "dialog", "share_link", hint="CASSim"),
        ),
        sub(
            "Edit",
            "2",
            MenuItem("Undo", "undo", key="1", hint="ctrl+Z"),
            MenuItem("Redo", "redo", key="2", hint="ctrl+Y"),
            MenuItem("Cut", "cut", key="3", hint="ctrl+X"),
            MenuItem("Copy", "copy", key="4", hint="ctrl+C"),
            MenuItem("Paste", "paste", key="5", hint="ctrl+V"),
            MenuItem("Delete", "delete", key="6"),
            todo_sub("Color", "7", "Fill Color", "Text Color"),
            MenuItem("Move Page Earlier", "move_page", "-1", hint="CASSim"),
            MenuItem("Move Page Later", "move_page", "1", hint="CASSim"),
            MenuItem("Move Problem Earlier", "move_problem", "-1", hint="CASSim"),
            MenuItem("Move Problem Later", "move_problem", "1", hint="CASSim"),
            MenuItem("Undo Page Change", "undo_pages", hint="CASSim"),
            MenuItem("Redo Page Change", "redo_pages", hint="CASSim"),
        ),
        sub(
            "View",
            "3",
            MenuItem("Back", "prev_page", key="1", hint="ctrl+◀"),
            MenuItem("Forward", "next_page", key="2", hint="ctrl+▶"),
            MenuItem("Page Sorter", "dialog", "page_sorter", key="3", hint="ctrl+▲"),
        ),
        sub(
            "Insert",
            "4",
            MenuItem("Problem", "add_problem", key="1"),
            MenuItem("Page", "add_page", "calculator", key="2", hint="ctrl+I"),
            MenuItem("Calculator", "add_page", "calculator", key="3"),
            todo("Graphs", "4"),
            todo("Geometry", "5"),
            todo("Lists & Spreadsheet", "6"),
            todo("Data & Statistics", "7"),
            todo("Notes", "8"),
            todo("Vernier DataQuest™", "9"),
            todo("Widget", "A"),
            todo_sub("Program Editor", "B", "New…", "Open…", "Import…", "View…"),
            todo_sub("Add Python", "C", "New…", "Open…", "Shell"),
        ),
        sub(
            "Page Layout",
            "5",
            todo("Custom Split", "1"),
            todo_sub("Select Layout", "2", "Layout 1", "Layout 2", "Layout 3"),
            todo("Select App", "3"),
            todo("Swap Applications", "4"),
            todo("Delete Application", "5"),
            MenuItem("Delete Page", "delete_page", key="6"),
            todo("Group", "7"),
            todo("Ungroup", "8"),
        ),
        todo("Refresh Libraries", "6"),
        sub(
            "Settings & Status",
            "7",
            todo("Change Language…", "1"),
            MenuItem("Document Settings…", "dialog", "document_settings", key="2"),
            MenuItem("Handheld Setup…", "dialog", "system_settings", key="3", hint="CASSim"),
            todo("Status…", "4"),
            todo("Login…", "5"),
            todo("Restore Factory Defaults…", "6"),
            MenuItem("About CASSim…", "dialog", "about", key="7", hint="CASSim"),
        ),
        todo("Login…", "8"),
        todo_sub("Press-to-Test", "9", "Exit Press-to-Test", "Transfer Press-to-Test", "Help"),
    ),
)


def _cells(*pairs: tuple[str, str]) -> tuple[MenuItem, ...]:
    """Grid cells that type their text; the label is shown, the hint names it."""
    return tuple(MenuItem(label, "insert", text, hint=text) for label, text in pairs)


_TRIG = ("sin", "cos", "tan", "csc", "sec", "cot")
# The trig key: a 6 × 2 grid, the inverses under their functions. No hyperbolic row.
TRIG = MenuItem(
    "Trig",
    columns=6,
    items=tuple(fn(name, name) for name in (*_TRIG, *(f"{name}⁻¹" for name in _TRIG))),
)

# ctrl+= on the keypad: a 3 × 2 grid (confirmed on the simulator).
RELATIONS = MenuItem(
    "Relations",
    columns=3,
    items=_cells((">", ">"), ("<", "<"), ("≠", "≠"), ("≥", "≥"), ("≤", "≤"), ("|", "|")),
)

# ?!▸: a grid 6 wide.
PUNCTUATION = MenuItem(
    "Punctuation",
    columns=6,
    items=_cells(
        ("?", "?"),
        ("!", "!"),
        ("$", "$"),
        ("°", "°"),
        ("'", "'"),
        ("%", "%"),
        ('"', '"'),
        (":", ":"),
        (";", ";"),
        ("_", "_"),
        ("\\", "\\"),
    ),
)

# π▸: a grid 5 wide (ⅈ and ⅇ are the imaginary unit and Euler's number).
SYMBOLS = MenuItem(
    "Symbols",
    columns=5,
    items=_cells(
        ("π", "π"),
        ("ⅈ", "ⅈ"),
        ("∞", "∞"),
        ("ⅇ", "ⅇ"),
        ("θ", "θ"),
        ("°", "°"),
        ("ʳ", "ʳ"),
        ("ᵍ", "ᵍ"),
        ("'", "'"),
    ),
)


def _cell(label: str, name: str, spec: str) -> MenuItem:
    """A template cell: `spec` is the template kind, as for the `template` key action."""
    return MenuItem(label, "template", spec, hint=name)


# The templates key: the device's 25 icons, 11 to a row, in order. Templates CASSim does not have
# yet are greyed.
TEMPLATES = MenuItem(
    "Templates",
    columns=11,
    items=(
        MenuItem("a/b", "template", "fraction", hint="Fraction (ctrl+÷)"),
        MenuItem("xʸ", "insert", "^", hint="Exponent (^)"),
        MenuItem("√", "template", "root", hint="Square root (ctrl+x²)"),
        _cell("ⁿ√", "Nth root (ctrl+^)", "nth_root"),
        MenuItem("eˣ", "insert", "ⅇ^", hint="e exponent (eˣ)"),
        _cell("log", "Log with base (ctrl+10ˣ)", "log"),
        _cell("{2", "Piecewise, 2 pieces", "piecewise:2"),
        MenuItem("{n", "wizard", "piecewise", hint="Piecewise, N pieces…"),
        _cell("{=", "System of 2 equations", "system:2"),
        MenuItem("{n=", "wizard", "system", hint="System of N equations…"),
        _cell("|x|", "Absolute value", "abs"),
        _cell("°'\"", "Degrees, minutes, seconds", "dms"),
        MenuItem("2×2", "template", "matrix:2,2", hint="2 × 2 matrix"),
        MenuItem("1×2", "template", "matrix:1,2", hint="1 × 2 matrix"),
        MenuItem("2×1", "template", "matrix:2,1", hint="2 × 1 matrix"),
        MenuItem("m×n", "wizard", "matrix", hint="m × n matrix…"),
        _cell("Σ", "Sum", "sum"),
        _cell("Π", "Product", "product"),
        _cell("d/d", "First derivative (shift+−)", "derivative"),
        _cell("d²", "Second derivative", "derivative2"),
        _cell("dⁿ", "Nth derivative", "derivative_n"),
        _cell("∫ₐᵇ", "Definite integral (shift++)", "integral"),
        _cell("∫", "Indefinite integral", "antiderivative"),
        _cell("lim", "Limit", "limit"),
        MenuItem("x₁", hint="Subscript: " + NOT_YET, enabled=False),
        # Not on the device (its lists are typed as {1,2,3}); a comma starts the next element.
        _cell("{ }", "List template (CASSim)", "list:3"),
    ),
)

# The first rows of the Catalog's Symbols tab (the device's grid, 11 wide). Further rows (arrows,
# shapes, currency, set and logic symbols, letters) are left out for now.
_SYMBOL_ROWS = (
    "π ⅇ ⅈ ᴇ ∞ θ → _ ▶ ° ʳ",
    "ᵍ ' ∠ = ≠ < ≤ > ≥ (−) +",
    "− * · × / ÷ ^ ± ᵀ √ ∏",
    "∑ d ∫ ! © @ # $ % & |",
    '" : ; , . ? ( ) { } [',
    "] x̄ ȳ Σ μ σ F χ ² ⁻¹ ₁",
    "₂ ₃ p̂ ŷ c n Δ µ Ω",
)
# Then the Greek capitals and small letters, in Unicode order (no final sigma), 11 to a row.
_GREEK = [chr(c) for c in (*range(0x391, 0x3AA), *range(0x3B1, 0x3CA)) if c not in (0x3A2, 0x3C2)]
_SPECIAL = {"(−)": "-", "−": "-", "^": "^", "√": "√"}


def _symbol_cell(symbol: str) -> MenuItem:
    if symbol == "√":
        return MenuItem("√", "template", "root", hint="Square root")
    return MenuItem(symbol, "insert", _SPECIAL.get(symbol, symbol), hint=symbol)


CATALOG_SYMBOLS = MenuItem(
    "Symbols",
    key="4",
    columns=11,
    items=tuple(_symbol_cell(symbol) for symbol in (*" ".join(_SYMBOL_ROWS).split(), *_GREEK)),
)


def _catalog_entry(name: str) -> MenuItem:
    """A Catalog function, listed as the device lists it: `abs(`."""
    item = fn(name, name)
    return MenuItem(f"{name}(", item.action, item.arg, hint=item.hint)


def _catalog_list() -> MenuItem:
    """Tab 1: every command A to Z in one list with its syntax; a typed letter jumps to it."""
    entries = [(name, _catalog_entry(name)) for name in FUNCTIONS]
    entries += [(name, cmd(name, name)) for name in COMMANDS]
    entries.sort(key=lambda pair: pair[0].casefold())
    return MenuItem("Catalog", key="1", jump=True, items=tuple(item for _, item in entries))


def _tab(item: MenuItem) -> MenuItem:
    """A Catalog tab: no keys of its own, so a digit switches tab as on the device."""
    return MenuItem(item.label, key=item.key, items=item.items, jump=True)


# The catalog key: six tabs, opening on the alphabetical list. Pressing 1 to 6 switches tab.
CATALOG = MenuItem(
    "Catalog",
    start=(0,),
    items=(
        _catalog_list(),
        _tab(todo_sub("Math Functions", "2", "Number", "Angle", "List", "Matrix", "Vector")),
        _tab(todo_sub("Units", "3", "Conversion Assistant", "Constants", "Length", "Area")),
        CATALOG_SYMBOLS,
        MenuItem("Math Expression Templates", key="5", columns=11, items=TEMPLATES.items),
        _tab(todo_sub("Library", "6", "Current Problem")),
    ),
)

MENUS = {
    "doc": DOC,
    "menu": MENU,
    "trig": TRIG,
    "templates": TEMPLATES,
    "catalog": CATALOG,
    "relations": RELATIONS,
    "punctuation": PUNCTUATION,
    "symbols": SYMBOLS,
}
