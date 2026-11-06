"""The TI-Nspire CX CAS keymaps (FR-DEV-007: device data lives here, not in `cassim.device`).

Sources: `docs/design/shortcuts.md` and the emulator runs in `docs/testing/`. Handheld key names
are CASSim's own labels for the keypad keys; the computer names are browser `KeyboardEvent.key`
values with a `ctrl+`, `shift+` or `alt+` prefix.
"""

from cassim.core.settings import Settings
from cassim.device.keys import Binding, Key, Keymap, Keypad
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

PROFILE = Profile("TI-Nspire CX CAS", HANDHELD, COMPUTER, MODIFIERS, KEYPAD, status_line)
