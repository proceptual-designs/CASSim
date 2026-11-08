"""The TI-Nspire CX CAS keymaps (FR-DEV-007: device data lives here, not in `cassim.device`).

Sources: `docs/design/shortcuts.md` and the emulator runs in `docs/testing/`. Handheld key names
are CASSim's own labels for the keypad keys; the computer names are browser `KeyboardEvent.key`
values with a `ctrl+`, `shift+` or `alt+` prefix.
"""

from cassim.core.settings import Settings
from cassim.device.editor import MARK
from cassim.device.keys import Binding, Key, Keymap, Keypad, gap
from cassim.profiles import Profile
from cassim.profiles.nspire_menus import DOC, MENU, MENUS, WIZARDS

__all__ = ["DOC", "MENU", "PROFILE"]

MODIFIERS = ("shift", "ctrl")

_ARROWS = {
    "left": Binding("left"),
    "right": Binding("right"),
    "up": Binding("up"),
    "down": Binding("down"),
}

HANDHELD: Keymap = {
    **_ARROWS,
    "click": Binding("select"),  # the touchpad's centre: chooses in a menu
    "ctrl+up": Binding("dialog", "page_sorter"),
    "ctrl+left": Binding("prev_page"),
    "ctrl+right": Binding("next_page"),
    "esc": Binding("escape"),
    "ctrl+esc": Binding("undo"),
    "doc": Binding("open_menu", "doc"),
    "ctrl+doc": Binding("add_page"),
    "menu": Binding("open_menu", "menu"),
    "tab": Binding("tab"),
    "shift+tab": Binding("shift_tab"),
    "shift+left": Binding("select_left"),
    "shift+right": Binding("select_right"),
    "var": Binding("open_menu", "variables"),
    "ctrl+var": Binding("insert", "→"),
    "ctrl+shift": Binding("caps"),  # the shift key's ctrl layer, CAPS
    "del": Binding("backspace"),
    "ctrl+del": Binding("clear"),
    "=": Binding("insert", "="),
    "ctrl+=": Binding("open_menu", "relations"),
    "trig": Binding("open_menu", "trig"),
    "templates": Binding("open_menu", "templates"),
    "ctrl+templates": Binding("insert", ":="),
    "catalog": Binding("open_menu", "catalog"),
    "ctrl+catalog": Binding("open_menu", "symbols"),
    "enter": Binding("enter"),
    "return": Binding("select"),  # ⏎ does nothing on a Calculator page (results M3)
    "ctrl+enter": Binding("approximate"),
    "plus": Binding("insert", "+"),
    "shift+plus": Binding("template", "integral"),
    "minus": Binding("insert", "-"),
    "shift+minus": Binding("template", "derivative"),
    "times": Binding("insert", "*"),
    "ctrl+times": Binding("insert_linear", f'"{MARK}"'),  # a pair of quotes
    "div": Binding("insert", "/"),
    "ctrl+div": Binding("template", "fraction"),
    "shift+div": Binding("insert", "\\"),
    "pow": Binding("insert", "^"),
    "ctrl+pow": Binding("template", "nth_root"),
    "square": Binding("power", "2"),
    "ctrl+square": Binding("template", "root"),
    "exp": Binding("insert", "ⅇ^"),
    "ctrl+exp": Binding("insert", "ln("),
    "10x": Binding("insert", "10^"),
    "ctrl+10x": Binding("template", "log"),  # log with a base slot first
    "ctrl+(": Binding("insert_linear", f"[{MARK}]"),  # a bracket pair, cursor inside
    "ctrl+)": Binding("insert_linear", f"{{{MARK}}}"),
    "neg": Binding("insert", "-"),
    "ctrl+neg": Binding("insert", "Ans"),
    "space": Binding("insert", " "),
    "ctrl+space": Binding("insert", "_"),
    "EE": Binding("insert", "ᴇ"),
    "punct": Binding("open_menu", "punctuation"),
    "pi": Binding("open_menu", "symbols"),
    "ctrl+8": Binding("home"),
    "ctrl+2": Binding("end"),
}

COMPUTER: Keymap = {
    "ArrowLeft": Binding("left"),
    "ArrowRight": Binding("right"),
    "ArrowUp": Binding("up"),
    "ArrowDown": Binding("down"),
    "Home": Binding("home"),
    "End": Binding("end"),
    "Escape": Binding("escape"),
    "CapsLock": Binding("caps"),  # the same lock as the keypad's ctrl+shift
    "F2": Binding("open_menu", "menu"),
    "F4": Binding("open_menu", "doc"),
    "Tab": Binding("tab"),
    "shift+Tab": Binding("shift_tab"),
    "shift+ArrowLeft": Binding("select_left"),
    "shift+ArrowRight": Binding("select_right"),
    "shift+ArrowUp": Binding("select_cells", "row:-1"),
    "shift+ArrowDown": Binding("select_cells", "row:1"),
    "alt+shift+ArrowLeft": Binding("select_cells", "col:-1"),
    "alt+shift+ArrowRight": Binding("select_cells", "col:1"),
    "ctrl+shift+ArrowLeft": Binding("select_word_left"),
    "ctrl+shift+ArrowRight": Binding("select_word_right"),
    "ctrl+ArrowLeft": Binding("word_left"),
    "ctrl+ArrowRight": Binding("word_right"),
    "shift+Home": Binding("select_to_start"),
    "shift+End": Binding("select_to_end"),
    "ctrl+a": Binding("select_all"),
    "ctrl+i": Binding("add_page"),
    "ctrl+l": Binding("open_menu", "variables"),
    "ctrl+ArrowUp": Binding("dialog", "page_sorter"),
    "alt+ArrowRight": Binding("next_page"),
    "alt+ArrowLeft": Binding("prev_page"),
    "ctrl+c": Binding("copy"),
    "ctrl+x": Binding("cut"),
    "ctrl+v": Binding("paste"),
    "Backspace": Binding("backspace"),
    "Delete": Binding("delete"),
    "Enter": Binding("enter"),
    "ctrl+Enter": Binding("approximate"),
    "ctrl+/": Binding("template", "fraction"),
    "ctrl+z": Binding("undo"),
    "ctrl+y": Binding("redo"),
    "ctrl+ ": Binding("insert", "_"),
    "ctrl+=": Binding("insert", "≠"),  # as the Teacher Software does
}


_ANGLE = {"radian": "RAD", "degree": "DEG", "gradian": "GRAD"}
_CALC = {"auto": "AUTO", "exact": "EXACT", "approximate": "APPROX"}
_DOMAIN = {"real": "REAL", "rectangular": "RECT", "polar": "POLAR"}


def status_line(settings: Settings) -> str:
    """The settings shown in the title bar: `RAD AUTO REAL`."""
    return f"{_ANGLE[settings.angle]} {_CALC[settings.calc]} {_DOMAIN[settings.domain]}"


_PAIR = 0.5  # the narrow keys that sit two to a column on the handheld


def _fn(name: str, label: str, ctrl: str = "", shift: str = "") -> Key:
    return Key(name, label, shift=shift, ctrl=ctrl, width=_PAIR, style="fn")


def _digit(name: str, ctrl: str = "") -> Key:
    return Key(name, name, ctrl=ctrl, style="digit")


def _alpha(name: str, label: str = "", ctrl: str = "", width: float = 0.0) -> Key:
    return Key(name, label or name, ctrl=ctrl, width=width or _ALPHA, height=0.75, style="alpha")


def _nav(name: str, label: str, ctrl: str = "", width: float = 1.0) -> Key:
    return Key(name, label, ctrl=ctrl, width=width, style="nav")


_ALPHA = 5 / 9  # nine letter keys across the five-unit keypad
_SIDE = 1.0  # the columns either side of the touchpad
_PAD = 1.0  # each touchpad cell

# The handheld's key layout and secondary labels (FR-DEV-005), in CASSim's own drawing: no TI
# artwork. Units: a digit key is 1 wide; the keypad is 5 units across. Scratchpad, home and the
# flag key have nothing to do yet, so they are gaps.
_MAIN: Keypad = (
    (
        _nav("esc", "esc", ctrl="undo"),
        gap(),
        Key("up", "▲", width=_PAD, style="pad"),
        gap(),
        gap(_SIDE),
    ),
    (
        gap(_SIDE),
        Key("left", "◀", width=_PAD, style="pad"),
        Key("click", "●", width=_PAD, style="pad"),
        Key("right", "▶", width=_PAD, style="pad"),
        _nav("doc", "doc", ctrl="+page"),
    ),
    (
        _nav("tab", "tab"),
        gap(),
        Key("down", "▼", width=_PAD, style="pad"),
        gap(),
        _nav("menu", "menu"),
    ),
    (
        Key("ctrl", "ctrl", width=_PAIR * 2, style="ctrl"),
        _nav("shift", "shift", ctrl="CAPS"),
        gap(),
        _nav("var", "var", ctrl="sto→"),
        _nav("del", "del", ctrl="clear"),
    ),
    (
        _fn("=", "=", ctrl="≠≥▸"),
        _fn("trig", "trig"),
        _digit("7"),
        _digit("8"),
        _digit("9"),
        _fn("templates", "▦", ctrl=":="),
        _fn("catalog", "cat", ctrl="∞β°"),
    ),
    (
        _fn("pow", "^", ctrl="ⁿ√"),
        _fn("square", "x²", ctrl="√"),
        _digit("4"),
        _digit("5"),
        _digit("6"),
        _fn("times", "×", ctrl='""'),
        _fn("div", "÷", ctrl="a/b", shift="\\"),
    ),
    (
        _fn("exp", "eˣ", ctrl="ln"),
        _fn("10x", "10ˣ", ctrl="log"),
        _digit("1"),
        _digit("2"),
        _digit("3"),
        _fn("plus", "+", shift="∫"),
        _fn("minus", "−", shift="d/dx"),
    ),
    (
        _fn("(", "(", ctrl="[ ]"),
        _fn(")", ")", ctrl="{ }"),
        _digit("0"),
        _digit("."),
        Key("neg", "(−)", ctrl="ans", style="digit"),
        Key("enter", "enter", ctrl="≈", style="enter"),
    ),
)

# The letter block, alphabetical as on the CX II, or QWERTY (ten keys across) as a System Setting.
_ABC: Keypad = (
    tuple(
        _alpha(n, label)
        for n, label in (("EE", "EE"), *((c, c) for c in "abcdefg"), ("punct", "?!▸"))
    ),
    (*(_alpha(n, label) for n, label in (("pi", "π▸"), *((c, c) for c in "hijklmn"))), gap(_ALPHA)),
    tuple(
        _alpha(n, label) for n, label in ((",", ","), *((c, c) for c in "opqrstu"), ("return", "⏎"))
    ),
    (
        gap(_ALPHA),
        *(_alpha(c) for c in "vwxyz"),
        _alpha("space", "␣", ctrl="_"),
        gap(_ALPHA * 2),
    ),
)
_Q = 0.5  # ten QWERTY keys across
_QWERTY: Keypad = (
    tuple(_alpha(c, width=_Q) for c in "qwertyuiop"),
    (*(_alpha(c, width=_Q) for c in "asdfghjkl"), _alpha("return", "⏎", width=_Q)),
    (
        _alpha("EE", "EE", width=_Q),
        *(_alpha(c, width=_Q) for c in "zxcvbnm"),
        _alpha(",", ",", width=_Q),
        _alpha("punct", "?!▸", width=_Q),
    ),
    (
        gap(_Q),
        _alpha("pi", "π▸", width=_Q),
        _alpha("space", "␣", ctrl="_", width=_Q * 6),
        gap(_Q * 2),
    ),
)
KEYPAD: Keypad = (*_MAIN, *_ABC)
KEYPAD_QWERTY: Keypad = (*_MAIN, *_QWERTY)
KEYPADS = {"ABC": KEYPAD, "QWERTY": KEYPAD_QWERTY}  # the letter layouts, by setting name

PROFILE = Profile(
    "TI-Nspire CX CAS",
    HANDHELD,
    COMPUTER,
    MODIFIERS,
    KEYPAD,
    status_line,
    MENUS,
    WIZARDS,
    KEYPADS,
)
