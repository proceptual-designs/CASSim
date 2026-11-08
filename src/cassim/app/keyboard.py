"""Browser key events to key names (FR-DEV-001, FR-CALC-004).

Flet reports the key, not the typed character: `Shift+6` arrives as key `6` with shift set
(decision 0015 finding 4). So shifted symbols come from a US/AU layout table, which suits the
Chromebooks first and is wrong on other layouts until typed characters are captured (to do, see
decision 0024).
"""

from __future__ import annotations

_NAMED = {
    "Arrow Left": "ArrowLeft",
    "Arrow Right": "ArrowRight",
    "Arrow Up": "ArrowUp",
    "Arrow Down": "ArrowDown",
    "Numpad Enter": "Enter",
    "Enter": "Enter",
    "Backspace": "Backspace",
    "Delete": "Delete",
    "Tab": "Tab",
    "Home": "Home",
    "Escape": "Escape",
    "Caps Lock": "CapsLock",
    "F2": "F2",
    "F4": "F4",
    "End": "End",
    "Space": " ",
    "Slash": "/",
    "Minus": "-",
    "Equal": "=",
    "Period": ".",
    "Comma": ",",
    "Asterisk": "*",
    "Plus": "+",
    "Bracket Left": "[",
    "Bracket Right": "]",
    "Semicolon": ";",
    "Quote": "'",
    "Backslash": "\\",
    "Backquote": "`",
    "Numpad Add": "+",
    "Numpad Subtract": "-",
    "Numpad Multiply": "*",
    "Numpad Divide": "/",
    "Numpad Decimal": ".",
}
_SHIFTED = {
    **dict(zip("1234567890", "!@#$%^&*()", strict=True)),
    "-": "_",
    "=": "+",
    "[": "{",
    "]": "}",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
    "\\": "|",
    "`": "~",
}


def key_name(
    key: str, *, shift: bool = False, ctrl: bool = False, alt: bool = False, meta: bool = False
) -> str | None:
    """The name a computer keymap uses for this event, or None for a bare modifier or a key we
    do not know. A typed character is its own name (`^`); a command key is `ctrl+z`,
    `shift+Tab`, `alt+Enter`. The Mac Command key counts as ctrl."""
    base = _NAMED.get(key, key)
    command = ctrl or meta
    if len(base) == 1:
        if base.isalpha():
            base = base.upper() if shift and not (command or alt) else base.lower()
        elif shift and base in _SHIFTED:
            base = _SHIFTED[base]
        if not (command or alt):
            return base
        return ("ctrl+" if command else "") + ("alt+" if alt else "") + base
    if base not in _NAMED.values():
        return None  # bare modifiers, other F-keys...
    return (
        ("ctrl+" if command else "") + ("alt+" if alt else "") + ("shift+" if shift else "") + base
    )
