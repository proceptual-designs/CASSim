"""The TI-Nspire CX CAS keymaps (FR-DEV-007: device data lives here, not in `cassim.device`).

Sources: `docs/design/shortcuts.md` and the emulator runs in `docs/testing/`. Handheld key names
are CASSim's own labels for the keypad keys; the computer names are browser `KeyboardEvent.key`
values with a `ctrl+`, `shift+` or `alt+` prefix.
"""

from cassim.core.settings import Settings
from cassim.device.keys import Binding, Key, Keymap, Keypad
from cassim.device.menu import MenuItem
from cassim.profiles import Profile

MODIFIERS = ("shift", "ctrl")

_ARROWS = {
    "left": Binding("left"),
    "right": Binding("right"),
    "up": Binding("up"),
    "down": Binding("down"),
}

HANDHELD: Keymap = {
    **_ARROWS,
    "esc": Binding("escape"),
    "doc": Binding("open_menu", "doc"),
    "menu": Binding("open_menu", "menu"),
    "tab": Binding("tab"),
    "shift+tab": Binding("shift_tab"),
    "shift+left": Binding("select_left"),
    "shift+right": Binding("select_right"),
    "del": Binding("backspace"),
    "enter": Binding("enter"),
    "ctrl+enter": Binding("approximate"),
    "plus": Binding("insert", "+"),
    "minus": Binding("insert", "-"),
    "times": Binding("insert", "*"),
    "div": Binding("insert", "/"),
    "pow": Binding("insert", "^"),
    "neg": Binding("insert", "-"),
    "square": Binding("power", "2"),
    "space": Binding("insert", " "),
    "EE": Binding("insert", "ᴇ"),
    "ctrl+div": Binding("template", "fraction"),
    "ctrl+square": Binding("template", "root"),
    "ctrl+neg": Binding("insert", "Ans"),
    "ctrl+space": Binding("insert", "_"),
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
    "F2": Binding("open_menu", "menu"),
    "F4": Binding("open_menu", "doc"),
    "Tab": Binding("tab"),
    "shift+Tab": Binding("shift_tab"),
    "shift+ArrowLeft": Binding("select_left"),
    "shift+ArrowRight": Binding("select_right"),
    "ctrl+shift+ArrowLeft": Binding("select_word_left"),
    "ctrl+shift+ArrowRight": Binding("select_word_right"),
    "ctrl+ArrowLeft": Binding("word_left"),
    "ctrl+ArrowRight": Binding("word_right"),
    "shift+Home": Binding("select_to_start"),
    "shift+End": Binding("select_to_end"),
    "ctrl+a": Binding("select_all"),
    "ctrl+i": Binding("add_page"),
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
}


_ANGLE = {"radian": "RAD", "degree": "DEG", "gradian": "GRAD"}
_CALC = {"auto": "AUTO", "exact": "EXACT", "approximate": "APPROX"}
_DOMAIN = {"real": "REAL", "rectangular": "RECT", "polar": "POLAR"}


def status_line(settings: Settings) -> str:
    """The settings shown in the title bar: `RAD AUTO REAL`."""
    return f"{_ANGLE[settings.angle]} {_CALC[settings.calc]} {_DOMAIN[settings.domain]}"


# CASSim's own keypad, five keys across (FR-DEV-005): not a copy of the handheld's artwork.
# Letters come from the computer keyboard; x and y are here for the common cases.
KEYPAD: Keypad = (
    (Key("esc", "esc"), Key("doc", "doc"), Key("menu", "menu")),
    (
        Key("ctrl", "ctrl"),
        Key("shift", "shift"),
        Key("tab", "tab"),
        Key("up", "▲"),
        Key("del", "del"),
    ),
    (Key("x", "x"), Key("y", "y"), Key("left", "◀"), Key("down", "▼"), Key("right", "▶")),
    (
        Key("square", "x²", ctrl="√"),
        Key("pow", "^"),
        Key("(", "("),
        Key(")", ")"),
        Key("div", "÷", ctrl="a/b"),
    ),
    (Key("7", "7"), Key("8", "8"), Key("9", "9"), Key("times", "×"), Key("π", "π")),
    (Key("4", "4"), Key("5", "5"), Key("6", "6"), Key("minus", "−"), Key(",", ",")),
    (Key("1", "1"), Key("2", "2"), Key("3", "3"), Key("plus", "+"), Key("EE", "ᴇ")),
    (
        Key("0", "0"),
        Key(".", "."),
        Key("neg", "(−)", ctrl="Ans"),
        Key("space", "␣", ctrl="_"),
        Key("enter", "enter", ctrl="≈"),
    ),
)


def _insert(*names: str) -> tuple[MenuItem, ...]:
    """Leaves that type a command name and its opening bracket."""
    return tuple(MenuItem(name, "insert", f"{name}(") for name in names)


# Doc: Insert > Problem and Calculator, and Settings & Status > Document Settings are the routes
# used on the simulator (TESTING.md section 6). The other entries are CASSim's own.
DOC = MenuItem(
    "Doc",
    items=(
        MenuItem(
            "Page",
            key="2",
            items=(
                MenuItem("Next page", "next_page"),
                MenuItem("Previous page", "prev_page"),
                MenuItem("Delete page", "delete_page"),
            ),
        ),
        MenuItem(
            "Insert",
            key="4",
            items=(
                MenuItem("Problem", "add_problem"),
                MenuItem("Calculator", "add_page", "calculator", key="3"),
            ),
        ),
        MenuItem(
            "Settings & Status",
            key="7",
            items=(MenuItem("Document Settings", "dialog", "document_settings", key="2"),),
        ),
    ),
)

# The calculator's Menu: command names to type. Layout follows the handheld's top-level groups;
# the entries are a starter set, grown with the catalog in M2d.
MENU = MenuItem(
    "Menu",
    items=(
        MenuItem(
            "Number",
            items=(
                *_insert("abs", "round", "floor", "ceiling", "gcd", "lcm", "factor"),
                MenuItem("Fraction tools", items=_insert("propFrac", "getNum", "getDenom")),
            ),
        ),
        MenuItem(
            "Algebra",
            items=_insert(
                "solve", "factor", "expand", "zeros", "cSolve", "completeSquare", "nSolve"
            ),
        ),
        MenuItem(
            "Calculus",
            items=_insert("derivative", "integral", "limit", "nInt", "fMin", "fMax"),
        ),
        MenuItem(
            "Probability",
            items=(
                MenuItem(
                    "Distributions", items=_insert("normCdf", "invNorm", "binomPdf", "binomCdf")
                ),
                *_insert("randInt", "randNorm"),
            ),
        ),
        MenuItem("Statistics", items=_insert("mean", "median", "stDevSamp", "stDevPop")),
        MenuItem("Matrix & Vector", items=_insert("det", "identity", "dotP", "crossP", "norm")),
    ),
)

PROFILE = Profile(
    "TI-Nspire CX CAS",
    HANDHELD,
    COMPUTER,
    MODIFIERS,
    KEYPAD,
    status_line,
    {"doc": DOC, "menu": MENU},
)
