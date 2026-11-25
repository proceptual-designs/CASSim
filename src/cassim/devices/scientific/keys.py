"""The CASSim fx keypad and computer keyboard, as data (SDD-14 section 4).

One table names every key once. The keypad drawing, the device state, the tutorials and the computer
keyboard map all use these names, so a key that the drawing shows is a key the state handles
(`tests/devices/scientific/test_scientific_keys.py` checks both directions).

Pure data: no Flet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cassim.device.keys import Binding

KeyStyle = Literal["fn", "num", "mod_shift", "mod_alpha", "nav", "del", "ac", "eq"]


@dataclass(frozen=True)
class KeySpec:
    """A keypad key: its id, its face label, the labels of its SHIFT and ALPHA layers, and how it
    is coloured. `name` is the spoken name for tooltips and screen readers."""

    id: str
    label: str
    shift: str = ""
    alpha: str = ""
    style: KeyStyle = "fn"
    name: str = ""

    @property
    def spoken(self) -> str:
        return self.name or self.label


# ---- key ids ------------------------------------------------------------------------------------

SHIFT, ALPHA, MODE, ON = "SHIFT", "ALPHA", "MODE", "ON"
UP, DOWN, LEFT, RIGHT = "UP", "DOWN", "LEFT", "RIGHT"
ABS, X3, XINV, LOGAB = "ABS", "X3", "XINV", "LOGAB"
FRAC, SQRT, X2, POW, LOG, LN = "FRAC", "SQRT", "X2", "POW", "LOG", "LN"
NEG, DMS, HYP, SIN, COS, TAN = "NEG", "DMS", "HYP", "SIN", "COS", "TAN"
RCL, ENG, LPAREN, RPAREN, SD, MPLUS = "RCL", "ENG", "LPAREN", "RPAREN", "SD", "MPLUS"
DEL, AC = "DEL", "AC"
MUL, DIV, ADD, SUB = "MUL", "DIV", "ADD", "SUB"
DOT, EXP, ANS, EQ = "DOT", "EXP", "ANS", "EQ"
DIGITS = tuple("0123456789")

# Keys a computer keyboard can send that have no keypad key of their own.
HOME, END = "HOME", "END"  # cursor to the start, end of the entry
REL_EQ, REL_LT, REL_GT = "REL_EQ", "REL_LT", "REL_GT"  # relations for VERIFY

# The variable each key types after ALPHA (and stores to after STO, recalls after RCL).
VARIABLE_KEYS: dict[str, str] = {
    NEG: "A",
    DMS: "B",
    HYP: "C",
    SIN: "D",
    COS: "E",
    TAN: "F",
    RPAREN: "X",
    SD: "Y",
    MPLUS: "M",
}

# ---- the keypad, row by row (row 1 is drawn specially: modifiers, D-pad, MODE and ON) ----------

ROW1_LEFT = (
    KeySpec(SHIFT, "SHIFT", style="mod_shift", name="Shift"),
    KeySpec(ALPHA, "ALPHA", style="mod_alpha", name="Alpha"),
)
ROW1_RIGHT = (
    KeySpec(MODE, "MODE", shift="SETUP", name="Mode"),
    KeySpec(ON, "ON", name="On"),
)
DPAD = (
    KeySpec(UP, "▲", style="nav", name="Up"),
    KeySpec(LEFT, "◀", style="nav", name="Left"),
    KeySpec(RIGHT, "▶", style="nav", name="Right"),
    KeySpec(DOWN, "▼", style="nav", name="Down"),
)

ROWS: tuple[tuple[KeySpec, ...], ...] = (
    (
        KeySpec(ABS, "Abs", name="Absolute value"),
        KeySpec(X3, "x³", name="Cube"),
        KeySpec(XINV, "x⁻¹", shift="x!", name="Reciprocal"),
        KeySpec(LOGAB, "log■□", name="Logarithm with a base"),
    ),
    (
        KeySpec(FRAC, "■/□", shift="a b/c", name="Fraction"),
        KeySpec(SQRT, "√■", shift="³√", name="Square root"),
        KeySpec(X2, "x²", name="Square"),
        KeySpec(POW, "x■", shift="■√", name="Power"),
        KeySpec(LOG, "log", shift="10■", name="Logarithm"),
        KeySpec(LN, "ln", shift="e■", name="Natural logarithm"),
    ),
    (
        KeySpec(NEG, "(−)", alpha="A", name="Negative"),
        KeySpec(DMS, "° ' \"", shift="FACT", alpha="B", name="Degrees, minutes, seconds"),
        KeySpec(HYP, "hyp", alpha="C", name="Hyperbolic"),
        KeySpec(SIN, "sin", shift="sin⁻¹", alpha="D", name="Sine"),
        KeySpec(COS, "cos", shift="cos⁻¹", alpha="E", name="Cosine"),
        KeySpec(TAN, "tan", shift="tan⁻¹", alpha="F", name="Tangent"),
    ),
    (
        KeySpec(RCL, "RCL", shift="STO", name="Recall"),
        KeySpec(ENG, "ENG", shift="←", name="Engineering notation"),
        KeySpec(LPAREN, "(", shift="%", name="Open bracket"),
        KeySpec(RPAREN, ")", shift=",", alpha="X", name="Close bracket"),
        KeySpec(SD, "S⇔D", shift="ab/c⇔d/c", alpha="Y", name="Exact or decimal"),
        KeySpec(MPLUS, "M+", shift="M−", alpha="M", name="Memory add"),
    ),
    (
        KeySpec("7", "7", style="num"),
        KeySpec("8", "8", style="num"),
        KeySpec("9", "9", shift="CLR", style="num"),
        KeySpec(DEL, "DEL", shift="INS", style="del", name="Delete"),
        KeySpec(AC, "AC", shift="OFF", style="ac", name="All clear"),
    ),
    (
        KeySpec("4", "4", style="num"),
        KeySpec("5", "5", style="num"),
        KeySpec("6", "6", shift="VERIFY", style="num"),
        KeySpec(MUL, "×", shift="nPr", alpha="GCD", style="num", name="Multiply"),
        KeySpec(DIV, "÷", shift="nCr", alpha="LCM", style="num", name="Divide"),
    ),
    (
        KeySpec("1", "1", shift="STAT", style="num"),
        KeySpec("2", "2", style="num"),
        KeySpec("3", "3", style="num"),
        KeySpec(ADD, "+", shift="Pol", style="num", name="Add"),
        KeySpec(SUB, "−", shift="Rec", style="num", name="Subtract"),
    ),
    (
        KeySpec("0", "0", shift="Rnd", style="num"),
        KeySpec(DOT, "·", shift="Ran#", alpha="RanInt", style="num", name="Decimal point"),
        KeySpec(EXP, "×10ˣ", shift="π", alpha="e", style="num", name="Times ten to the power"),
        KeySpec(ANS, "Ans", shift="DRG▶", style="num", name="Answer"),
        KeySpec(EQ, "=", style="eq", name="Equals"),
    ),
)

ALL_KEYS: tuple[KeySpec, ...] = (*ROW1_LEFT, *ROW1_RIGHT, *DPAD, *(k for row in ROWS for k in row))
KEYS_BY_ID: dict[str, KeySpec] = {key.id: key for key in ALL_KEYS}

# ---- the computer keyboard (SDD-14 section 4.1) -------------------------------------------------
# Names are `cassim.app.keyboard.key_name` names. Each binds a sequence of keypad keys, so a
# shortcut does exactly what pressing those keys does (the tutorials accept either).


def _seq(*keys: str) -> Binding:
    return Binding("place", " ".join(keys))


COMPUTER: dict[str, Binding] = {
    **{digit: _seq(digit) for digit in DIGITS},
    ".": _seq(DOT),
    "+": _seq(ADD),
    "-": _seq(SUB),
    "*": _seq(MUL),
    "/": _seq(DIV),
    "(": _seq(LPAREN),
    ")": _seq(RPAREN),
    "^": _seq(POW),
    "!": _seq(SHIFT, XINV),
    "%": _seq(SHIFT, LPAREN),
    ",": _seq(SHIFT, RPAREN),
    "=": _seq(EQ),
    "Enter": _seq(EQ),
    "Backspace": _seq(DEL),
    "Delete": _seq(DEL),
    "Escape": _seq(AC),
    "ArrowUp": _seq(UP),
    "ArrowDown": _seq(DOWN),
    "ArrowLeft": _seq(LEFT),
    "ArrowRight": _seq(RIGHT),
    "Home": _seq(HOME),
    "End": _seq(END),
    "<": _seq(REL_LT),
    ">": _seq(REL_GT),
    "ctrl+/": _seq(FRAC),
    "ctrl+m": _seq(MODE),
    "F1": _seq(SHIFT),
    "F2": _seq(ALPHA),
    # letters: a function key; the capital letter is that key's SHIFT layer
    "s": _seq(SIN),
    "S": _seq(SHIFT, SIN),
    "c": _seq(COS),
    "C": _seq(SHIFT, COS),
    "t": _seq(TAN),
    "T": _seq(SHIFT, TAN),
    "h": _seq(HYP),
    "l": _seq(LOG),
    "L": _seq(SHIFT, LOG),
    "n": _seq(LN),
    "N": _seq(SHIFT, LN),
    "r": _seq(SQRT),
    "R": _seq(SHIFT, SQRT),
    "q": _seq(X2),
    "d": _seq(DMS),
    "D": _seq(SHIFT, DMS),
    "m": _seq(MPLUS),
    "M": _seq(SHIFT, MPLUS),
    "p": _seq(SHIFT, EXP),
    "e": _seq(ALPHA, EXP),
    "a": _seq(ANS),
    "x": _seq(ALPHA, RPAREN),
    "X": _seq(ALPHA, RPAREN),
    "y": _seq(ALPHA, SD),
    "Y": _seq(ALPHA, SD),
    "ctrl+c": Binding("copy"),
}

# What the shortcuts dialog and the help page list, in order: (keys, what they do).
SHORTCUT_HELP: tuple[tuple[str, str], ...] = (
    ("0–9 . + - * / ( ) ^", "Type as on the keypad (/ is ÷, ^ is x■)"),
    ("Enter or =", "Calculate (=); in VERIFY mode = types the relation"),
    ("Backspace, Delete", "DEL"),
    ("Esc", "AC (and shows the menu bar when it is hidden)"),
    ("Arrow keys", "Move the cursor; ▲ ▼ recall earlier calculations"),
    ("Home, End", "Start or end of the entry"),
    ("F1, F2", "SHIFT and ALPHA: then any key, as on the keypad"),
    ("Ctrl+M", "MODE (F1 then Ctrl+M: SETUP)"),
    ("Ctrl+/", "Fraction template"),
    ("s c t, S C T", "sin cos tan, and their inverses"),
    ("h", "hyp"),
    ("l n, L N", "log ln, and 10■ e■"),
    ("r, R", "√ and ³√"),
    ("q", "x²"),
    ("!  %  ,", "x!, %, and the comma"),
    ("d, D", "° ' \" and FACT"),
    ("m, M", "M+ and M−"),
    ("p, e", "π and e"),
    ("a, x, y", "Ans, and the variables X and Y"),
    ("< >", "Relations (VERIFY mode)"),
    ("Ctrl+C", "Copy the answer"),
)


COMMANDS: dict[str, Binding] = {name: b for name, b in COMPUTER.items() if len(name) > 1}
"""The non-typing shortcuts (F1, Ctrl+M, arrows...). Only these go in the device profile, which
the published page uses to keep them from the browser; typed characters reach the app anyway."""


def sequence(binding: Binding) -> tuple[str, ...]:
    """The keypad keys a computer-keyboard binding presses."""
    return tuple(binding.arg.split())
