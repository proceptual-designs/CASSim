"""Tokenizer for the pseudocode dialect (docs/pseudocode/dialect.md section 3).

Keywords are not decided here: a NAME is a keyword only where the parser expects one, so a variable
called `end` is still possible in expression position.
"""

from dataclasses import dataclass

from cassim.runtime.pseudocode.errors import PseudocodeSyntaxError

SUPERSCRIPT = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
}  # fmt: skip
SUPERSCRIPT_MINUS = "⁻"

# Longest spelling first.
_OPERATORS = (
    "<-", ":=", "<=", ">=", "<>", "!=", "==", "**",
    "←", "≤", "≥", "≠", "⩽", "⩾", "∧", "∨", "¬", "√",
    "+", "-", "−", "–", "×", "*", "·", "÷", "/", "^", "%",
    "(", ")", "[", "]", ",", "=", "<", ">", "|", ":",
)  # fmt: skip
_CANONICAL = {
    "<-": "←", ":=": "←", "<=": "≤", ">=": "≥", "<>": "≠", "!=": "≠", "==": "=",
    "⩽": "≤", "⩾": "≥", "**": "^", "−": "-", "–": "-", "×": "*", "·": "*", "∧": "and",
    "∨": "or", "¬": "not", "÷": "÷",
}  # fmt: skip
_QUOTES = {'"': '"', "“": "”", "”": "”"}


@dataclass(frozen=True, slots=True)
class Token:
    kind: str  # NUMBER NAME STRING OP SUP NEWLINE EOF
    text: str
    line: int
    col: int
    end: int  # column just past the token, to tell `a[i]` from `a [i]`
    raw: str = ""  # the spelling as typed (OP and NAME)


def _is_name_start(c: str) -> bool:
    return c.isalpha() or c == "_" or c in "ⅇⅈ∞"


def _is_name_part(c: str) -> bool:
    return (c.isalnum() and c not in SUPERSCRIPT) or c == "_" or c in "ⅇⅈ'"


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    for lineno, text in enumerate(source.splitlines(), start=1):
        _tokenize_line(text, lineno, tokens)
        tokens.append(Token("NEWLINE", "", lineno, len(text), len(text)))
    last = len(source.splitlines()) + 1
    tokens.append(Token("EOF", "", last, 0, 0))
    return tokens


def _tokenize_line(text: str, lineno: int, out: list[Token]) -> None:  # noqa: PLR0912
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t":
            i += 1
        elif text.startswith("//", i) or c == "#":
            break
        elif (c.isdigit() and c not in SUPERSCRIPT) or (
            c == "." and i + 1 < n and text[i + 1].isdigit()
        ):
            j = _scan_number(text, i)
            out.append(Token("NUMBER", text[i:j], lineno, i, j))
            i = j
        elif c in _QUOTES:
            close = _QUOTES[c]
            j = i + 1
            while j < n and text[j] not in (close, '"' if close == '"' else close):
                j += 1
            if j >= n:
                raise PseudocodeSyntaxError("unterminated string", lineno, i)
            out.append(Token("STRING", text[i + 1 : j], lineno, i, j + 1))
            i = j + 1
        elif c in SUPERSCRIPT or c == SUPERSCRIPT_MINUS:
            j = i
            sign = ""
            if text[j] == SUPERSCRIPT_MINUS:
                sign, j = "-", j + 1
            start = j
            while j < n and text[j] in SUPERSCRIPT:
                j += 1
            if j == start:
                raise PseudocodeSyntaxError("a superscript minus needs digits", lineno, i)
            digits = "".join(SUPERSCRIPT[ch] for ch in text[start:j])
            out.append(Token("SUP", sign + digits, lineno, i, j))
            i = j
        elif _is_name_start(c):
            j = i + 1
            while j < n and _is_name_part(text[j]):
                j += 1
            out.append(Token("NAME", text[i:j], lineno, i, j, text[i:j]))
            i = j
        else:
            for op in _OPERATORS:
                if text.startswith(op, i):
                    canon = _CANONICAL.get(op, op)
                    out.append(Token("OP", canon, lineno, i, i + len(op), op))
                    i += len(op)
                    break
            else:
                raise PseudocodeSyntaxError(f"unexpected character {c!r}", lineno, i)


def _scan_number(text: str, i: int) -> int:
    n = len(text)
    j = i
    while j < n and text[j].isdigit() and text[j] not in SUPERSCRIPT:
        j += 1
    if j < n and text[j] == "." and not text.startswith("..", j):
        j += 1
        while j < n and text[j].isdigit() and text[j] not in SUPERSCRIPT:
            j += 1
    # Scientific notation is `E` or `ᴇ` only; lowercase `e` is never an exponent marker.
    if j < n and text[j] in "Eᴇ":
        k = j + 1
        if k < n and text[k] in "+-−":
            k += 1
        if k < n and text[k].isdigit():
            while k < n and text[k].isdigit():
                k += 1
            return k
    return j
