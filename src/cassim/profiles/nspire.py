"""The TI-Nspire CX CAS keymaps (FR-DEV-007: device data lives here, not in `cassim.device`).

Sources: `docs/design/shortcuts.md` and the emulator runs in `docs/testing/`. Handheld key names
are CASSim's own labels for the keypad keys; the computer names are browser `KeyboardEvent.key`
values with a `ctrl+`, `shift+` or `alt+` prefix.
"""

from cassim.device.keys import Binding, Keymap

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
    "Backspace": Binding("backspace"),
    "Delete": Binding("delete"),
    "Enter": Binding("enter"),
    "ctrl+Enter": Binding("approximate"),
    "ctrl+/": Binding("template", "fraction"),
    "ctrl+z": Binding("undo"),
    "ctrl+y": Binding("redo"),
    "ctrl+ ": Binding("insert", "_"),
}
