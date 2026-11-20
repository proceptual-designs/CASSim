"""Undo-safe typing-aid replacements for the pseudocode editor (FR-SYN-013)."""

from dataclasses import dataclass

_DIRECT = (
    ("<=", "≤"),
    (">=", "≥"),
    ("!=", "≠"),
    ("<-", "←"),
)
_LATEX = {
    r"\pi": "π",
    r"\sqrt": "√",
    r"\le": "≤",
    r"\ge": "≥",
    r"\theta": "θ",
}
_TEXT_TERMINATORS = {" ", "\n"}


@dataclass(frozen=True, slots=True)
class TypingReplacement:
    text: str
    start: int
    end: int
    replacement: str


def replacement_before_cursor(text: str, cursor: int) -> TypingReplacement | None:
    """Return an unambiguous suffix replacement ending at `cursor`, if one exists."""
    if cursor < 0 or cursor > len(text):
        return None
    before = text[:cursor]
    for source, target in _DIRECT:
        if before.endswith(source):
            return TypingReplacement(text, cursor - len(source), cursor, target)
    if before and before[-1] in _TEXT_TERMINATORS:
        stem = before[:-1]
        for source, target in _LATEX.items():
            if stem.endswith(source):
                return TypingReplacement(
                    text,
                    cursor - len(source) - 1,
                    cursor,
                    f"{target}{before[-1]}",
                )
    return None
