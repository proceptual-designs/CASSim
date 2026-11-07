"""The TI-Nspire CX CAS menus and dialogs as data (FR-DEV-001, FR-DEV-007, FR-CALC-005).

The Calculator Menu follows the handheld's numbering, so `menu 3 1` is Solve as on the device.
Items the engine cannot do yet are left out; the others keep their real numbers (`key=`). The
tree is reconstructed from the Reference Guide and the device; `docs/decisions/0022` lists what
still needs checking on the simulator. A label ending in `…` opens a dialog (a `Wizard`).
"""

from __future__ import annotations

import string
from collections.abc import Mapping

from cassim.device.menu import MenuItem
from cassim.device.wizard import CURSOR, Field, Wizard
from cassim.profiles.nspire_syntax import COMMANDS, CONVERSIONS, FUNCTIONS


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


def call(name: str, *args: str) -> str:
    """`name(a,b,c)` with empty trailing arguments dropped (they are optional)."""
    kept = list(args)
    while kept and not kept[-1]:
        kept.pop()
    return f"{name}({','.join(kept)})"


# ---- dialogs ----------------------------------------------------------------------------------

_MU, _SIGMA = Field("mu", "μ", "0"), Field("sigma", "σ", "1")
_LOWER = Field("lower", "Lower Bound", "-9ᴇ999")
_UPPER = Field("upper", "Upper Bound", "9ᴇ999")
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
    Field("count", "Number of Equations", "2", whole=(1, 20)),
    Field("vars", "Variables", "x,y"),
)


def _dist(title: str, name: str, *fields: Field) -> Wizard:
    """A distribution dialog: pastes `name(fields…)` and runs it, as the handheld does."""
    names = [field.name for field in fields]
    return Wizard(title, fields, run=True, build=lambda v: call(name, *(v[n] for n in names)))


def _derivative_at(v: Mapping[str, str]) -> str:
    order = "" if v["order"] == "1" else f",{v['order']}"
    return f"derivative({CURSOR},{v['var']}{order})|{v['var']}={v['value']}"


def _n_derivative_at(v: Mapping[str, str]) -> str:
    order = "" if v["order"] == "1" else f",{v['order']}"
    return f"nDerivative({CURSOR},{v['var']}={v['value']}{order})"


def _system(v: Mapping[str, str]) -> str:
    """The equations as a list; the cursor waits in the first one."""
    slots = CURSOR + "," * (int(v["count"]) - 1)
    return f"solve({{{slots}}},{{{v['vars']}}})"


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
    """Stat Calculations: run the command, then show `stat.results` as the handheld does."""
    fields = (Field("x", "X List"), Field("y", "Y List"), _FREQ)
    return Wizard(title, fields, command + " {x},{y},{freq}: stat.results", run=True)


_TVM_ORDER = ("n", "i", "pv", "pmt", "fv")
_TVM_NAMES = {"n": "tvmN", "i": "tvmI", "pv": "tvmPV", "pmt": "tvmPmt", "fv": "tvmFV"}


def _finance(v: Mapping[str, str]) -> str:
    """Finance Solver: the TVM function for the chosen unknown, from the other four values."""
    target = v["solve"]
    known = [v[name] for name in _TVM_ORDER if name != target]
    return call(_TVM_NAMES[target], *known, v["ppy"], v["cpy"], v["pmtat"])


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

_DISTRIBUTIONS = (
    ("Normal Pdf", "normPdf", "1", (_X, _MU, _SIGMA)),
    ("Normal Cdf", "normCdf", "2", (_LOWER, _UPPER, _MU, _SIGMA)),
    ("Inverse Normal", "invNorm", "3", (_AREA, _MU, _SIGMA)),
    ("t Pdf", "tPdf", "4", (_X, _DF)),
    ("t Cdf", "tCdf", "5", (_LOWER, _UPPER, _DF)),
    ("Inverse t", "invt", "6", (_AREA, _DF)),
    ("χ² Pdf", "χ²Pdf", "7", (_X, _DF)),
    ("χ² Cdf", "χ²Cdf", "8", (_LOWER, _UPPER, _DF)),
    ("Inverse χ²", "invχ²", "9", (_AREA, _DF)),
    ("F Pdf", "fPdf", "A", (_X, _DFN, _DFD)),
    ("F Cdf", "fCdf", "B", (_LOWER, _UPPER, _DFN, _DFD)),
    ("Inverse F", "invF", "C", (_AREA, _DFN, _DFD)),
    ("Binomial Pdf", "binomPdf", "D", (_N, _P, _X)),
    (
        "Binomial Cdf",
        "binomCdf",
        "E",
        (_N, _P, Field("lower", "Lower Bound", "0"), Field("upper", "Upper Bound")),
    ),
    ("Inverse Binomial", "invBinom", "F", (Field("c", "Cumulative Prob"), _N, _P)),
    ("Poisson Pdf", "poissPdf", "H", (_LAMBDA, _X)),
    (
        "Poisson Cdf",
        "poissCdf",
        "I",
        (_LAMBDA, Field("lower", "Lower Bound", "0"), Field("upper", "Upper Bound")),
    ),
    ("Geometric Pdf", "geomPdf", "J", (_P, _X)),
    (
        "Geometric Cdf",
        "geomCdf",
        "K",
        (_P, Field("lower", "Lower Bound", "1"), Field("upper", "Upper Bound")),
    ),
)

WIZARDS: dict[str, Wizard] = {
    "derivative_at": Wizard(
        "Derivative at a Point",
        (Field("var", "Variable", "x"), Field("value", "Value"), _ORDER),
        build=_derivative_at,
    ),
    "n_derivative_at": Wizard(
        "Numerical Derivative at a Point",
        (Field("var", "Variable", "x"), Field("value", "Value"), _ORDER),
        build=_n_derivative_at,
    ),
    "solve_system": Wizard("Solve System of Equations", _SYSTEM_FIELDS, build=_system),
    "solve_linear_system": Wizard(
        "Solve System of Linear Equations", _SYSTEM_FIELDS, build=_system
    ),
    "poly_roots": Wizard(
        "Find Roots of Polynomial",
        (
            Field("coeffs", "Coefficients, highest power first", "1,0,-1"),
            Field("var", "Variable", "x"),
            Field("roots", "Roots", "real", choices=(("real", "Real"), ("complex", "Complex"))),
        ),
        run=True,
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
    "finance": Wizard(
        "Finance Solver",
        (
            Field(
                "solve",
                "Solve for",
                "fv",
                choices=(("n", "N"), ("i", "I (%)"), ("pv", "PV"), ("pmt", "Pmt"), ("fv", "FV")),
            ),
            Field("n", "N"),
            Field("i", "I (%)"),
            Field("pv", "PV"),
            Field("pmt", "Pmt"),
            Field("fv", "FV"),
            Field("ppy", "PpY", "1"),
            Field("cpy", "CpY", "1"),
            Field("pmtat", "PmtAt", "0", choices=(("0", "END"), ("1", "BEGIN"))),
        ),
        run=True,
        build=_finance,
    ),
    **{name: _dist(title, name, *fields) for title, name, _, fields in _DISTRIBUTIONS},
    **{command.casefold(): _regression(title, command) for title, command, _ in _REGRESSIONS},
}


DISTRIBUTIONS = sub(
    "Distributions",
    "5",
    *(wiz(title, name, key, FUNCTIONS[name]) for title, name, key, _ in _DISTRIBUTIONS),
)

# The Calculator's Menu (menu key, F2 on a computer).
MENU = MenuItem(
    "Menu",
    items=(
        sub(
            "Actions",
            "1",
            cmd("Define", "Define", "1"),
            cmd("Delete Variable", "DelVar", "3"),
            cmd("Clear a-z", "ClearAZ", "4"),
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
            sub("Fraction Tools", "7", fn("Proper Fraction", "propFrac", "1")),
            sub(
                "Number Tools",
                "8",
                fn("Round", "round", "1"),
                fn("Integer Part", "iPart", "2"),
                fn("Fractional Part", "fPart", "3"),
                fn("Sign", "sign", "4"),
                fn("Modulo", "mod", "5"),
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
            fn("Prime Number Test", "isPrime", "A"),
        ),
        sub(
            "Algebra",
            "3",
            fn("Solve", "solve", "1"),
            fn("Factor", "factor", "2"),
            fn("Expand", "expand", "3"),
            fn("Zeros", "zeros", "4"),
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
            ),
            sub(
                "Fraction Tools",
                "9",
                fn("Proper Fraction", "propFrac", "1"),
                fn("Common Denominator", "comDenom", "4"),
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
            fn("Derivative", "derivative", "1"),
            wiz("Derivative at a Point", "derivative_at", "2", "derivative(Expr, Var)|Var=Value"),
            fn("Integral", "∫", "3"),
            fn("Limit", "limit", "4"),
            fn("Sum", "Σ", "5"),
            fn("Product", "Π", "6"),
            fn("Function Minimum", "fMin", "7"),
            fn("Function Maximum", "fMax", "8"),
            fn("Tangent Line", "tangentLine", "9"),
            fn("Normal Line", "normalLine", "A"),
            sub("Series", "C", fn("Taylor Polynomial", "taylor", "1")),
            fn("Differential Equation Solver", "deSolve", "D"),
            fn("Implicit Differentiation", "impDif", "E"),
            sub(
                "Numerical Calculations",
                "F",
                wiz(
                    "Numerical Derivative at a Point",
                    "n_derivative_at",
                    "1",
                    FUNCTIONS["nDerivative"],
                ),
                fn("Numerical Integral", "nInt", "2"),
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
                sub(
                    "Standard Deviation",
                    "7",
                    fn("Sample Standard Deviation", "stDevSamp", "1"),
                    fn("Population Standard Deviation", "stDevPop", "2"),
                ),
                sub(
                    "Variance",
                    "8",
                    fn("Sample Variance", "varSamp", "1"),
                    fn("Population Variance", "varPop", "2"),
                ),
            ),
            sub(
                "List Operations",
                "4",
                cmd("Sort Ascending", "SortA", "1"),
                cmd("Sort Descending", "SortD", "2"),
                fn("Cumulative Sum List", "cumulativeSum", "3"),
                fn("Convert Matrix to List", "mat▶list", "7"),
                fn("Convert List to Matrix", "list▶mat", "8"),
            ),
            DISTRIBUTIONS,
        ),
        sub(
            "Matrix & Vector",
            "7",
            sub(
                "Create",
                "1",
                wiz("Matrix", "matrix", "1", "Rows × columns template"),
                fn("Identity", "identity", "3"),
                fn("Sub-matrix", "subMat", "7"),
                fn("Augment", "augment", "8"),
            ),
            conv("Transpose", "ᵀ", "2"),
            fn("Determinant", "det", "3"),
            fn("Reduced Row-Echelon Form", "rref", "5"),
            fn("Simultaneous", "simult", "6"),
            sub("Norms", "7", fn("Norm", "norm", "1")),
            sub("Dimensions", "8", fn("Dimension", "dim", "1")),
            sub("Advanced", "B", fn("Eigenvalue", "eigVl"), fn("Eigenvector", "eigVc")),
            sub(
                "Vector",
                "C",
                fn("Unit Vector", "unitV", "1"),
                fn("Cross Product", "crossP", "2"),
                fn("Dot Product", "dotP", "3"),
            ),
        ),
        sub(
            "Finance",
            "8",
            wiz("Finance Solver", "finance", "1", "Solves for one of N, I, PV, Pmt, FV"),
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
            sub(
                "Interest Conversion",
                "5",
                fn("Nominal Interest Rate", "nom", "1"),
                fn("Effective Interest Rate", "eff", "2"),
            ),
        ),
    ),
)

# Doc (doc key, F4). Doc > 4 Insert > 1 Problem / 3 Calculator and Doc > 7 Settings & Status are the
# routes used on the simulator; the other entries are CASSim's own, numbered after the real ones.
DOC = MenuItem(
    "Doc",
    items=(
        sub(
            "File",
            "1",
            MenuItem("New Document", "new_document", key="1"),
            MenuItem("Open Document…", "dialog", "open_file", key="2"),
            MenuItem("Save As…", "dialog", "save_file", key="3"),
            MenuItem("Copy share link", "dialog", "share_link"),
        ),
        sub(
            "Edit",
            "2",
            MenuItem("Undo", "undo", key="1", hint="ctrl+Z"),
            MenuItem("Redo", "redo", key="2", hint="ctrl+Y"),
            MenuItem("Cut", "cut", key="3", hint="ctrl+X"),
            MenuItem("Copy", "copy", key="4", hint="ctrl+C"),
            MenuItem("Paste", "paste", key="5", hint="ctrl+V"),
            MenuItem("Delete Page", "delete_page"),
            MenuItem("Move Page Earlier", "move_page", "-1"),
            MenuItem("Move Page Later", "move_page", "1"),
            MenuItem("Move Problem Earlier", "move_problem", "-1"),
            MenuItem("Move Problem Later", "move_problem", "1"),
            MenuItem("Undo Page Change", "undo_pages"),
            MenuItem("Redo Page Change", "redo_pages"),
        ),
        sub(
            "View",
            "3",
            MenuItem("Page Sorter", "dialog", "page_sorter", key="1", hint="ctrl+▲"),
            MenuItem("Next Page", "next_page", hint="ctrl+▶"),
            MenuItem("Previous Page", "prev_page", hint="ctrl+◀"),
        ),
        sub(
            "Insert",
            "4",
            MenuItem("Problem", "add_problem", key="1"),
            MenuItem("Calculator", "add_page", "calculator", key="3", hint="ctrl+I"),
        ),
        sub(
            "Settings & Status",
            "7",
            MenuItem("System Settings…", "dialog", "system_settings", key="1"),
            MenuItem("Document Settings…", "dialog", "document_settings", key="2"),
        ),
    ),
)


def _insert_items(*pairs: tuple[str, str]) -> tuple[MenuItem, ...]:
    return tuple(MenuItem(label, "insert", text) for label, text in pairs)


_TRIG = ("sin", "cos", "tan", "csc", "sec", "cot")
_HYPERBOLIC = ("sinh", "cosh", "tanh", "csch", "sech", "coth")
# The trig key's list.
TRIG = MenuItem(
    "Trig",
    items=tuple(
        fn(name, name)
        for name in (
            *_TRIG,
            *(f"{name}⁻¹" for name in _TRIG),
            *_HYPERBOLIC,
            "sinh⁻¹",
            "cosh⁻¹",
            "tanh⁻¹",
        )
    ),
)

# ctrl+= on the keypad (confirmed on the simulator, shortcuts S2).
RELATIONS = MenuItem(
    "Relations",
    items=_insert_items(
        (">", ">"), ("<", "<"), ("≠", "≠"), ("≥", "≥"), ("≤", "≤"), ("| (with)", "|")
    ),
)

# The templates key. The handheld shows a grid; here it is a list in the same spirit.
TEMPLATES = MenuItem(
    "Templates",
    items=(
        MenuItem("Fraction  □/□", "template", "fraction", hint="ctrl+÷"),
        MenuItem("Exponent  □^□", "insert", "^", hint="^"),
        MenuItem("Square root  √□", "template", "root", hint="ctrl+x²"),
        MenuItem("ⅇ exponent  ⅇ^□", "insert", "ⅇ^", hint="eˣ"),
        MenuItem("Log  log(□,□)", "insert", "log(", hint=FUNCTIONS["log"]),
        MenuItem("Absolute value  |□|", "insert", "abs(", hint=FUNCTIONS["abs"]),
        MenuItem("Matrix 2×2", "template", "matrix:2,2"),
        wiz("Matrix m×n", "matrix", hint="Rows × columns template"),
        MenuItem("Sum  Σ", "insert", "Σ(", hint=FUNCTIONS["Σ"]),
        MenuItem("Product  Π", "insert", "Π(", hint=FUNCTIONS["Π"]),
        MenuItem("Derivative  d/d□", "insert", "derivative(", hint=FUNCTIONS["derivative"]),
        MenuItem("Integral  ∫", "insert", "∫(", hint=FUNCTIONS["∫"]),
        MenuItem("Limit  lim", "insert", "limit(", hint=FUNCTIONS["limit"]),
    ),
)

# ?!▸ and π▸ on the letter keys.
PUNCTUATION = MenuItem(
    "Punctuation",
    items=_insert_items(
        ("?", "?"),
        ("!", "!"),
        ("°", "°"),
        ("'", "'"),
        ('"', '"'),
        ("%", "%"),
        (":", ":"),
        (";", ";"),
        ("_", "_"),
        ("\\", "\\"),
        ("→  store", "→"),
        ("▶  convert", "▶"),
    ),
)
SYMBOLS = MenuItem(
    "Symbols",
    items=(
        *_insert_items(
            ("π", "π"),
            ("θ", "θ"),
            ("∞", "∞"),
            ("ⅇ", "ⅇ"),
            ("ⅈ", "ⅈ"),
            ("≤", "≤"),
            ("≥", "≥"),
            ("≠", "≠"),
            ("∠", "∠"),
            ("ᵀ", "ᵀ"),
            ("⇒", "⇒"),
            ("⇔", "⇔"),
        ),
        fn("√", "√"),
    ),
)


def _catalog() -> MenuItem:
    """The catalog key: every command A to Z with its syntax, a submenu per first letter (the
    letter is its key, so typing `s` jumps to S as on the handheld)."""
    entries = [(name, fn(name, name)) for name in FUNCTIONS]
    entries += [(name, cmd(name, name)) for name in COMMANDS]
    groups: dict[str, list[MenuItem]] = {}
    for name, item in sorted(entries, key=lambda pair: pair[0].casefold()):
        first = name[0].upper()
        groups.setdefault(first if first in string.ascii_uppercase else "", []).append(item)
    letters = tuple(
        sub(letter, letter, *groups[letter])
        for letter in string.ascii_uppercase
        if letter in groups
    )
    return MenuItem("Catalog", items=(*letters, sub("Σ ∫ χ² √", "1", *groups[""])))


CATALOG = _catalog()

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
