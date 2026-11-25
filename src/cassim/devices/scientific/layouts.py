"""Keypad layouts: one calculator behind the keys of different school calculators (FR-FX-UI-005).

A layout changes only what the keys are called and where they are. Each layout key names, for each
layer (plain, after SHIFT/2nd, after ALPHA), the sequence of canonical keys (`keys.py`) it stands
for, so the device state, the keyboard map and the tutorials stay the same for every layout. A
sequence may hold three pseudo-keys the state understands: `TOK:<token>` types one token (the
statistics variables printed on some keys), `STATSUB:<n>` opens item n of the STAT menu, and
`DATA` adds the entry as a STAT data row.

Layouts follow the arrangement and the key names of each class of calculator, so students can
find their own keys; the artwork, fonts and colours are CASSim's own (decision 0028).

Pure data and functions: no Flet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from cassim.devices.scientific import keys as k
from cassim.devices.scientific.keys import KeyStyle

CalcModeName = Literal["COMP", "STAT", "TABLE", "VERIFY"]
DpadPlace = Literal["center", "right"]
Seq = tuple[str, ...]

SHIFT, ALPHA = k.SHIFT, k.ALPHA


@dataclass(frozen=True)
class LKey:
    """A key of a layout: its face, the legends above it, and what each layer presses."""

    id: str
    face: str
    plain: Seq
    shift: Seq = ()
    alpha: Seq = ()
    shift_label: str = ""
    alpha_label: str = ""
    style: KeyStyle = "fn"
    name: str = ""
    span: int = 1  # columns it takes in its row

    @property
    def spoken(self) -> str:
        return self.name or self.face


type Cell = LKey | None  # None leaves a column empty


@dataclass(frozen=True)
class Layout:
    id: str
    title: str  # what the Appearance list calls it
    shift_name: str  # the face of the SHIFT key ("2nd", "2nd F")
    alpha_name: str
    top: tuple[tuple[Cell, ...], ...]  # rows beside the D-pad
    rows: tuple[tuple[Cell, ...], ...]
    dpad: DpadPlace = "center"
    modes: tuple[CalcModeName, ...] = ("COMP", "STAT", "TABLE", "VERIFY")
    linear: bool = False  # a two-line linear display: choosing it switches SETUP to LineIO
    shift_colour: str = ""  # legend colours on a dark body; "" keeps the theme's
    alpha_colour: str = ""
    shift_mark: str = "S"  # the status indicators
    alpha_mark: str = "A"
    notes: tuple[str, ...] = field(default_factory=tuple)  # differences, for the help text

    def all_keys(self) -> tuple[LKey, ...]:
        """Every key, the D-pad included."""
        drawn = tuple(cell for row in (*self.top, *self.rows) for cell in row if cell is not None)
        return (*drawn, *DPAD_KEYS)

    def key(self, key_id: str) -> LKey:
        for cell in self.all_keys():
            if cell.id == key_id:
                return cell
        raise KeyError(key_id)


# ---- helpers for writing layouts --------------------------------------------------------


def std(  # noqa: PLR0913
    key_id: str,
    face: str,
    shift_label: str = "",
    alpha_label: str = "",
    *,
    style: KeyStyle = "fn",
    name: str = "",
) -> LKey:
    """A key that is the canonical key of the same id, with the canonical SHIFT and ALPHA layers."""
    return LKey(
        id=key_id,
        face=face,
        plain=(key_id,),
        shift=(SHIFT, key_id) if shift_label else (),
        alpha=(ALPHA, key_id) if alpha_label else (),
        shift_label=shift_label,
        alpha_label=alpha_label,
        style=style,
        name=name or k.KEYS_BY_ID[key_id].name if key_id in k.KEYS_BY_ID else name,
    )


def num(digit: str, shift_label: str = "", alpha_label: str = "") -> LKey:
    return std(digit, digit, shift_label, alpha_label, style="num")


def var(letter: str) -> Seq:
    """ALPHA then the key that types this variable."""
    for key_id, name in k.VARIABLE_KEYS.items():
        if name == letter:
            return (ALPHA, key_id)
    raise KeyError(letter)


def tok(token: str) -> Seq:
    return (f"TOK:{token}",)


SHIFT_KEY = LKey("SHIFT", "SHIFT", (SHIFT,), style="mod_shift", name="Shift")
ALPHA_KEY = LKey("ALPHA", "ALPHA", (ALPHA,), style="mod_alpha", name="Alpha")
DPAD = k.DPAD
DPAD_KEYS: tuple[LKey, ...] = tuple(
    LKey(spec.id, spec.label, (spec.id,), style="nav", name=spec.name) for spec in k.DPAD
)

# ---- Casio fx-82 series (the default) -------------------------------------------------------

FX82 = Layout(
    id="fx82",
    title="Casio fx-82 series",
    shift_name="SHIFT",
    alpha_name="ALPHA",
    top=(
        (
            SHIFT_KEY,
            ALPHA_KEY,
            LKey(k.MODE, "MODE", (k.MODE,), (SHIFT, k.MODE), shift_label="SETUP", name="Mode"),
            std(k.ON, "ON"),
        ),
        (
            std(k.ABS, "Abs"),
            std(k.X3, "x³"),
            std(k.XINV, "x⁻¹"),
            LKey("FACTORIAL", "x!", (SHIFT, k.XINV), name="Factorial"),
        ),
    ),
    rows=(
        (
            std(k.FRAC, "■/□", "■□/□"),
            std(k.SQRT, "√■", "³√■"),
            std(k.X2, "x²"),
            std(k.POW, "x■", "■√□"),
            std(k.LOG, "log", "10■"),
            std(k.LN, "ln", "e■"),
        ),
        (
            std(k.NEG, "(−)", alpha_label="A"),
            std(k.DMS, "° ' \"", "FACT", "B"),
            std(k.HYP, "hyp", alpha_label="C"),
            std(k.SIN, "sin", "sin⁻¹", "D"),
            std(k.COS, "cos", "cos⁻¹", "E"),
            std(k.TAN, "tan", "tan⁻¹", "F"),
        ),
        (
            std(k.RCL, "RCL", "STO"),
            std(k.ENG, "ENG", "←"),
            std(k.LPAREN, "(", "%"),
            std(k.RPAREN, ")", ",", "X"),
            std(k.SD, "S⇔D", "ab/c⇔d/c", "Y"),
            std(k.MPLUS, "M+", "M−", "M"),
        ),
        (
            num("7"),
            num("8"),
            num("9", "CLR"),
            std(k.DEL, "DEL", "INS", style="del"),
            std(k.AC, "AC", "OFF", style="ac"),
        ),
        (
            num("4"),
            num("5"),
            num("6", "VERIFY"),
            std(k.MUL, "×", "nPr", "GCD", style="num"),
            std(k.DIV, "÷", "nCr", "LCM", style="num"),
        ),
        (
            num("1", "STAT"),
            num("2"),
            num("3"),
            std(k.ADD, "+", "Pol", style="num"),
            std(k.SUB, "−", "Rec", style="num"),
        ),
        (
            num("0", "Rnd"),
            std(k.DOT, "·", "Ran#", "RanInt", style="num"),
            std(k.EXP, "×10ˣ", "π", "e", style="num"),
            std(k.ANS, "Ans", "DRG▶", style="num"),
            std(k.EQ, "=", style="eq"),
        ),
    ),
)

# ---- Abacus SX-II series --------------------------------------------------------------------

SX2 = Layout(
    id="sx2",
    title="Abacus SX-II series",
    shift_name="2nd",
    alpha_name="ALPHA",
    shift_mark="2nd",
    shift_colour="#f2d15c",
    alpha_colour="#5fb4ff",
    modes=("COMP", "STAT", "VERIFY"),
    top=(
        (
            LKey(k.MODE, "MODE", (k.MODE,), (SHIFT, k.MODE), shift_label="SET UP", name="Mode"),
            std(k.ON, "ON"),
        ),
        (LKey("SHIFT", "2nd", (SHIFT,), style="mod_shift", name="Second"), std(k.ABS, "Abs")),
        (ALPHA_KEY, LKey("FACTORIAL", "x!", (SHIFT, k.XINV), name="Factorial")),
    ),
    rows=(
        (
            LKey(k.ENG, "ENG", (k.ENG,), (SHIFT, k.ENG), shift_label="←ENG", name="Engineering"),
            std(k.XINV, "x⁻¹"),
            std(k.LOG, "log", "10ˣ"),
            std(k.LN, "ln", "eˣ"),
            std(k.DEL, "DEL", "INS", style="del"),
        ),
        (
            std(k.NEG, "(−)", alpha_label="A"),
            std(k.DMS, "DMS", "FACT", "B"),
            std(k.HYP, "HYP", alpha_label="C"),
            std(k.X2, "x²"),
            std(k.X3, "x³"),
        ),
        (
            std(k.SIN, "SIN", "SIN⁻¹", "D"),
            std(k.COS, "COS", "COS⁻¹", "E"),
            std(k.TAN, "TAN", "TAN⁻¹", "F"),
            std(k.POW, "xʸ", "ˣ√"),
            std(k.SQRT, "√", "³√"),
        ),
        (
            std(k.RCL, "RCL", "STO"),
            std(k.LPAREN, "(", "%"),
            std(k.RPAREN, ")", ",", "X"),
            std(k.SD, "F↔D", "A b/c↔d/c", "Y", name="Fraction or decimal"),
            LKey(k.FRAC, "d/c", (k.FRAC,), (SHIFT, k.FRAC), shift_label="A b/c", name="Fraction"),
        ),
        (
            num("7"),
            num("8"),
            num("9", "CLR"),
            std(k.DIV, "÷", "nCr", "LCM", style="num"),
            std(k.AC, "AC", "OFF", style="ac"),
        ),
        (
            num("4"),
            num("5"),
            num("6", "VERIFY"),
            std(k.MUL, "×", "nPr", "GCD", style="num"),
            std(k.MPLUS, "M+", "M−", "M"),
        ),
        (
            num("1", "STATVAR"),
            num("2"),
            num("3"),
            LKey(k.SUB, "−", (k.SUB,), (SHIFT, k.SUB), shift_label="P→R", style="num"),
            std(k.ANS, "ANS", "DRG▸", style="num"),
        ),
        (
            num("0", "RND"),
            std(k.DOT, "·", "RAND", "RANDI", style="num"),
            std(k.EXP, "×10ˣ", "π", "e", style="num"),
            LKey(k.ADD, "+", (k.ADD,), (SHIFT, k.ADD), shift_label="R→P", style="num"),
            std(k.EQ, "=", style="eq"),
        ),
    ),
    notes=("No TABLE mode.", "F↔D switches between a fraction and a decimal, like S⇔D."),
)

# ---- Sharp EL-531 series --------------------------------------------------------------------

_NONE: Seq = ()

EL531 = Layout(
    id="el531",
    title="Sharp EL-531 series",
    shift_name="2ndF",
    alpha_name="ALPHA",
    shift_mark="2ndF",
    shift_colour="#f29a4a",
    alpha_colour="#6fd19a",
    modes=("COMP", "STAT"),
    linear=True,
    top=(
        (
            LKey("HOME", "HOME", (k.MODE, "1"), name="Home: back to normal calculation"),
            LKey(k.ON, "ON/C", (k.AC,), (SHIFT, k.AC), shift_label="OFF", name="On, clear"),
        ),
        (
            LKey("SHIFT", "2ndF", (SHIFT,), style="mod_shift", name="Second function"),
            LKey(k.MODE, "MODE", (k.MODE,), (SHIFT, "9"), shift_label="CA", name="Mode"),
        ),
    ),
    rows=(
        (
            LKey(
                k.ALPHA,
                "ALPHA",
                (ALPHA,),
                (SHIFT, "1"),
                shift_label="STAT VAR",
                style="mod_alpha",
                name="Alpha",
            ),
            LKey("SETUP", "SET UP", (SHIFT, k.MODE), name="Set up"),
            std(k.DEL, "DEL", "INS", style="del"),
            None,
            None,
            None,
        ),
        (
            LKey(k.HYP, "hyp", (k.HYP,), (k.HYP, SHIFT), shift_label="archyp", name="Hyperbolic"),
            std(k.SIN, "sin", "sin⁻¹"),
            std(k.COS, "cos", "cos⁻¹"),
            std(k.TAN, "tan", "tan⁻¹"),
            LKey("PI", "π", (SHIFT, k.EXP), name="Pi"),
            LKey("DRG", "DRG", (SHIFT, k.ANS), (SHIFT, k.ANS), shift_label="DRG▸", name="Angle"),
        ),
        (
            LKey(k.POW, "yˣ", (k.POW,), (SHIFT, k.POW), var("A"), "ˣ√", "A", name="Power"),
            LKey(k.SQRT, "√", (k.SQRT,), alpha=var("B"), alpha_label="B", name="Square root"),
            LKey(k.X2, "x²", (k.X2,), (k.XINV,), var("C"), "x⁻¹", "C", name="Square"),
            LKey(k.X3, "x³", (k.X3,), (SHIFT, k.SQRT), var("D"), "³√", "D", name="Cube"),
            LKey(k.LOG, "log", (k.LOG,), (SHIFT, k.LOG), var("E"), "10ˣ", "E", name="Logarithm"),
            LKey(k.LN, "ln", (k.LN,), (SHIFT, k.LN), var("F"), "eˣ", "F", name="Natural log"),
        ),
        (
            LKey(k.EXP, "Exp", (k.EXP,), (k.ENG,), shift_label="←→", name="Exponent"),
            LKey(k.FRAC, "a b/c", (k.FRAC,), (SHIFT, k.SD), shift_label="d/c", name="Fraction"),
            LKey(k.DMS, "D°M'S", (k.DMS,), (k.DMS,), shift_label="↔DEG", name="DMS"),
            LKey(k.RCL, "RCL", (k.RCL,), alpha=var("X"), alpha_label="X", name="Recall"),
            LKey(
                "STO",
                "STO",
                (SHIFT, k.RCL),
                (SHIFT, k.RPAREN),
                var("Y"),
                ",",
                "Y",
                name="Store",
            ),
            LKey(k.MPLUS, "M+", ("DATA",), (SHIFT, k.MPLUS), var("M"), "M−", "M", name="M+ (DATA)"),
        ),
        (
            LKey("7", "7", ("7",), (SHIFT, k.DOT), tok("ȳ"), "RANDOM", "ȳ", style="num"),
            LKey("8", "8", ("8",), (SHIFT, k.ADD), tok("sy"), "→rθ", "sy", style="num"),
            LKey("9", "9", ("9",), (SHIFT, k.SUB), tok("σy"), "→xy", "σy", style="num"),
            LKey(k.LPAREN, "(", (k.LPAREN,), tok("x̂"), tok("regA"), "x′", "a"),  # noqa: RUF001
            LKey(k.RPAREN, ")", (k.RPAREN,), tok("ŷ"), tok("regB"), "y′", "b"),  # noqa: RUF001
        ),
        (
            LKey("4", "4", ("4",), (SHIFT, k.XINV), tok("x̄"), "n!", "x̄", style="num"),
            LKey("5", "5", ("5",), (SHIFT, k.DIV), tok("sx"), "nCr", "sx", style="num"),
            LKey("6", "6", ("6",), (SHIFT, k.MUL), tok("σx"), "nPr", "σx", style="num"),
            LKey(k.MUL, "×", (k.MUL,), _NONE, tok("regC"), "→HEX", "c", style="num"),
            LKey(k.DIV, "÷", (k.DIV,), _NONE, tok("r"), "→BIN", "r", style="num"),
        ),
        (
            LKey("1", "1", ("1",), (SHIFT, k.LPAREN), tok("Σxy"), "%", "Σxy", style="num"),
            LKey("2", "2", ("2",), alpha=tok("Σy"), alpha_label="Σy", style="num"),
            LKey("3", "3", ("3",), alpha=tok("Σy²"), alpha_label="Σy²", style="num"),
            LKey(k.ADD, "+", (k.ADD,), _NONE, shift_label="→PEN", style="num"),
            LKey(k.SUB, "−", (k.SUB,), _NONE, shift_label="→OCT", style="num"),
        ),
        (
            LKey("0", "0", ("0",), (SHIFT, "0"), tok("n"), "MDF", "n", style="num"),
            LKey(k.DOT, "·", (k.DOT,), alpha=tok("Σx"), alpha_label="Σx", style="num"),
            LKey(
                k.NEG,
                "+/−",
                (k.NEG,),
                (SHIFT, "9", "2"),
                tok("Σx²"),
                "M-CLR",
                "Σx²",
                style="num",
                name="Negative",
            ),
            LKey(k.EQ, "=", (k.EQ,), _NONE, (k.ANS,), "→DEC", "ANS", style="eq", span=2),
        ),
    ),
    notes=(
        "A two-line linear display: fractions show as 2⌟3 and surds as decimals.",
        "No TABLE or VERIFY mode, and no prime factorisation (FACT) or S⇔D key.",
        "In STAT mode M+ is DATA: it adds the entry (x, or x,y) as a new data row.",
        "Base-n conversions and logic operations are on the keys but are not part of CASSim fx.",
        "Statistics variables are typed with ALPHA and the key they are printed above.",
    ),
)

# ---- HP 10s series --------------------------------------------------------------------------

HP10S = Layout(
    id="hp10s",
    title="HP 10s series",
    shift_name="SHIFT",
    alpha_name="ALPHA",
    shift_colour="#5fb4ff",
    alpha_colour="#ff7a6b",
    modes=("COMP", "STAT"),
    linear=True,
    dpad="right",
    top=(
        (
            SHIFT_KEY,
            ALPHA_KEY,
            LKey(k.MODE, "MODE", (k.MODE,), (SHIFT, k.MODE), shift_label="SETUP", name="Mode"),
            std(k.ON, "ON"),
        ),
        (
            LKey(k.XINV, "x⁻¹", (k.XINV,), (SHIFT, k.XINV), shift_label="x!", name="Reciprocal"),
            LKey("NCR", "nCr", (SHIFT, k.DIV), (SHIFT, k.MUL), shift_label="nPr", name="nCr"),
            LKey("POL", "Pol(", (SHIFT, k.ADD), (SHIFT, k.SUB), shift_label="Rec(", name="Pol("),
            LKey(k.FRAC, "a b/c", (k.FRAC,), (SHIFT, k.SD), shift_label="d/c", name="Fraction"),
        ),
    ),
    rows=(
        (
            std(k.SQRT, "√"),
            std(k.X2, "x²"),
            LKey(k.X3, "x³", (k.X3,), (SHIFT, k.SQRT), shift_label="³√", name="Cube"),
            std(k.POW, "yˣ", "ˣ√"),
            std(k.LOG, "log", "10ˣ"),
            LKey(k.LN, "ln", (k.LN,), (SHIFT, k.LN), (ALPHA, k.EXP), "eˣ", "e", name="ln"),
        ),
        (
            std(k.NEG, "(−)", alpha_label="A"),
            LKey(k.DMS, "° ' \"", (k.DMS,), (k.DMS,), var("B"), "←", "B", name="DMS"),
            std(k.HYP, "hyp", alpha_label="C"),
            std(k.SIN, "sin", "sin⁻¹", "D"),
            std(k.COS, "cos", "cos⁻¹", "E"),
            std(k.TAN, "tan", "tan⁻¹", "F"),
        ),
        (
            std(k.RCL, "RCL", "STO"),
            std(k.ENG, "ENG", "←"),
            std(k.LPAREN, "("),
            std(k.RPAREN, ")", alpha_label="X"),
            LKey("COMMA", ",", (SHIFT, k.RPAREN), alpha=var("Y"), alpha_label="Y", name="Comma"),
            LKey(k.MPLUS, "M+", ("DATA",), (SHIFT, k.MPLUS), var("M"), "M−", "M", name="M+ (DT)"),
        ),
        (
            num("7"),
            num("8"),
            num("9"),
            std(k.AC, "AC", "OFF", style="ac"),
            LKey(k.DEL, "DEL", (k.DEL,), (SHIFT, "9"), shift_label="CLR", style="del"),
        ),
        (
            num("4"),
            num("5"),
            num("6"),
            std(k.MUL, "×", style="num"),
            LKey(k.DIV, "÷", (k.DIV,), (SHIFT, k.DEL), shift_label="INS", style="num"),
        ),
        (
            LKey("1", "1", ("1",), ("STATSUB:3",), shift_label="S-SUM", style="num"),
            LKey("2", "2", ("2",), ("STATSUB:4",), shift_label="S-VAR", style="num"),
            num("3"),
            std(k.ADD, "+", style="num"),
            std(k.SUB, "−", style="num"),
        ),
        (
            num("0", "Rnd"),
            std(k.DOT, "·", "Ran#", style="num"),
            std(k.EXP, "EXP", "π", style="num"),
            std(k.ANS, "Ans", "DRG▸", style="num"),
            LKey(k.EQ, "=", (k.EQ,), (SHIFT, k.LPAREN), shift_label="%", style="eq"),
        ),
    ),
    notes=(
        "A two-line linear display: fractions show as 2⌟3 and surds as decimals.",
        "No TABLE or VERIFY mode, and no prime factorisation (FACT) or S⇔D key.",
        "In STAT mode M+ is DT: it adds the entry (x, or x,y) as a new data row.",
        "SHIFT 1 (S-SUM) and SHIFT 2 (S-VAR) open the sums and the statistics in STAT mode.",
    ),
)

LAYOUTS: tuple[Layout, ...] = (FX82, SX2, EL531, HP10S)
LAYOUTS_BY_ID: dict[str, Layout] = {layout.id: layout for layout in LAYOUTS}
DEFAULT = FX82


# ---- translation --------------------------------------------------------------------------


def expand(seq: Seq) -> list[str]:
    """Canonical keys with STATSUB written out as SHIFT 1 n, for comparing with a lesson."""
    out: list[str] = []
    for key in seq:
        if key.startswith("STATSUB:"):
            out.extend((SHIFT, "1", key.split(":", 1)[1]))
        else:
            out.append(key)
    return out


def normalize(seq: list[str]) -> list[str]:
    """What a key sequence does, with modifiers that cancel each other taken out: SHIFT SHIFT is
    nothing, and SHIFT ALPHA is ALPHA (ALPHA replaces a waiting SHIFT, and the other way round)."""
    out: list[str] = []
    for key in seq:
        if out and out[-1] in (SHIFT, ALPHA) and key in (SHIFT, ALPHA):
            waiting = out.pop()
            if waiting != key:
                out.append(key)
            continue
        out.append(key)
    return out


def press(lkey: LKey, *, shift: bool, alpha: bool) -> list[str]:
    """The canonical keys a layout key sends when SHIFT or ALPHA may already be waiting."""
    layer = lkey.shift if shift else lkey.alpha if alpha else lkey.plain
    active = SHIFT if shift else ALPHA if alpha else None
    if active is None:
        return list(layer)
    if not layer:
        return [active]  # no function on that layer: the modifier is just cancelled
    if layer == (active,):
        return [active]  # pressing SHIFT again cancels it
    if layer[0] == active:
        return list(layer[1:])
    return [active, *layer]  # cancel the waiting modifier first


@dataclass(frozen=True)
class Step:
    presses: tuple[LKey, ...]
    produces: tuple[str, ...]  # canonical keys, STATSUB expanded


def _candidates(layout: Layout) -> list[Step]:
    """Every press or modifier-and-press, with the canonical keys it produces from no modifier."""
    shift_key = next(key for key in layout.all_keys() if key.plain == (SHIFT,))
    alpha_key = next(key for key in layout.all_keys() if key.plain == (ALPHA,))
    found: list[Step] = []
    for key in layout.all_keys():
        plain = press(key, shift=False, alpha=False)
        # A lone SHIFT or ALPHA is never a step of its own: what it does depends on the next key,
        # so it is planned only together with that key.
        if plain and plain not in ([SHIFT], [ALPHA]):
            found.append(Step((key,), tuple(expand(tuple(plain)))))
        for modifier, flag in ((shift_key, "shift"), (alpha_key, "alpha")):
            layer = key.shift if flag == "shift" else key.alpha
            if not layer or key is modifier:
                continue
            first = SHIFT if flag == "shift" else ALPHA
            rest = press(key, shift=flag == "shift", alpha=flag == "alpha")
            found.append(Step((modifier, key), tuple(normalize(expand((first, *rest))))))
    return found


def plan(layout: Layout, canonical: list[str]) -> list[Step] | None:
    """The layout presses that produce these canonical keys (longest match first), or None when
    the layout cannot produce them."""
    candidates = _candidates(layout)
    steps: list[Step] = []
    i = 0
    while i < len(canonical):
        best: Step | None = None
        for step in candidates:
            n = len(step.produces)
            if tuple(canonical[i : i + n]) == step.produces and (
                best is None or n > len(best.produces)
            ):
                best = step
        if best is None:
            return None
        steps.append(best)
        i += len(best.produces)
    return steps


def describe(layout: Layout, canonical: list[str]) -> str:
    """The keys to press, by their faces on this layout: 'SHIFT then 9', '2nd then 9'."""
    steps = plan(layout, canonical)
    if steps is None:
        steps = plan(DEFAULT, canonical) or []
    return " then ".join(key.face for step in steps for key in step.presses)
