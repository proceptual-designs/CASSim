"""Tokenizer for the pseudocode dialect (docs/pseudocode/dialect.md section 3).

Keywords are not decided here: a NAME is a keyword only where the parser expects one, so a variable
called `end` is still possible in expression position.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace

from cassim.runtime.pseudocode.errors import PseudocodeSyntaxError
from cassim.runtime.pseudocode.syntax import DEFAULT, Mode, Syntax

type Warn = Callable[[int, str], None]

SUPERSCRIPT = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
}  # fmt: skip
SUPERSCRIPT_MINUS = "⁻"
# Superscript signs, brackets and letters: a run such as `ˣ⁺¹` is the exponent `(x+1)`.
# Unicode has a superscript for every lowercase Latin letter but q (code points, not
# literals: several look like ordinary letters).
SUPERSCRIPT_SIGNS = {chr(0x207A): "+", chr(0x207B): "-", chr(0x207D): "(", chr(0x207E): ")"}
SUPERSCRIPT_LETTERS = {
    chr(code): letter
    for letter, code in (
        ("a", 0x1D43), ("b", 0x1D47), ("c", 0x1D9C), ("d", 0x1D48), ("e", 0x1D49),
        ("f", 0x1DA0), ("g", 0x1D4D), ("h", 0x02B0), ("i", 0x2071), ("j", 0x02B2),
        ("k", 0x1D4F), ("l", 0x02E1), ("m", 0x1D50), ("n", 0x207F), ("o", 0x1D52),
        ("p", 0x1D56), ("r", 0x02B3), ("s", 0x02E2), ("t", 0x1D57), ("u", 0x1D58),
        ("v", 0x1D5B), ("w", 0x02B7), ("x", 0x02E3), ("y", 0x02B8), ("z", 0x1DBB),
    )
}  # fmt: skip
SUPERSCRIPT_RUN = SUPERSCRIPT | SUPERSCRIPT_SIGNS | SUPERSCRIPT_LETTERS  # character -> plain

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
_CONSTANT_ALIASES = (("@pi", "π"), ("@e", "ⅇ"))
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
    return (c.isalpha() and c not in SUPERSCRIPT_LETTERS) or c == "_" or c in "ⅇⅈ∞"


def _is_name_part(c: str) -> bool:
    return (
        (c.isalnum() and c not in SUPERSCRIPT and c not in SUPERSCRIPT_LETTERS)
        or c == "_"
        or c in "ⅇⅈ'"
    )


def _spelling(
    mode: Mode | None, what: str, syntax: Syntax, at: tuple[int, int], warn: Warn
) -> None:
    """Apply a spelling's mode from the syntax file: `no` stops the parse, `warn` is noted."""
    line, col = at
    if mode == "no" or mode is None:
        raise PseudocodeSyntaxError(
            f"{what} is not accepted by the {syntax.name} syntax", line, col
        )
    if mode == "warn":
        warn(line, f"{what} is not preferred in the {syntax.name} syntax")


def _ignore(line: int, message: str) -> None:
    del line, message


def tokenize(source: str, syntax: Syntax = DEFAULT, warn: Warn = _ignore) -> list[Token]:
    tokens: list[Token] = []
    for lineno, text in enumerate(source.splitlines(), start=1):
        _tokenize_line(text, lineno, tokens, syntax, warn)
        tokens.append(Token("NEWLINE", "", lineno, len(text), len(text)))
    last = len(source.splitlines()) + 1
    tokens.append(Token("EOF", "", last, 0, 0))
    return tokens


def _comment_marker(text: str, i: int, syntax: Syntax) -> str | None:
    for marker in syntax.comments:
        if text.startswith(marker, i):
            return marker
    return None


def _scan_constant_alias(text: str, i: int, line: int, out: list[Token]) -> int:
    for alias, canonical in _CONSTANT_ALIASES:
        end = i + len(alias)
        if text.startswith(alias, i) and (end == len(text) or not _is_name_part(text[end])):
            out.append(Token("NAME", canonical, line, i, end, alias))
            return end
    raise PseudocodeSyntaxError(f"unexpected character {text[i]!r}", line, i)


def _tokenize_line(  # noqa: PLR0912
    text: str, lineno: int, out: list[Token], syntax: Syntax, warn: Warn
) -> None:
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        marker = _comment_marker(text, i, syntax)
        if c in " \t":
            i += 1
        elif marker is not None:
            what = f"the comment marker '{marker}'"
            _spelling(syntax.comments[marker], what, syntax, (lineno, i), warn)
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
            kind = "straight" if c == '"' else "curly"
            _spelling(syntax.quotes.get(kind), f"{kind} quotes", syntax, (lineno, i), warn)
            out.append(Token("STRING", text[i + 1 : j], lineno, i, j + 1))
            i = j + 1
        elif c in SUPERSCRIPT_RUN:
            _spelling(syntax.superscripts, "superscript exponents", syntax, (lineno, i), warn)
            run = _superscript_tokens(text, (lineno, i), syntax, warn)
            out.extend(run)
            i = run[-1].end
        elif c == "@":
            i = _scan_constant_alias(text, i, lineno, out)
        elif _is_name_start(c):
            j = i + 1
            while j < n and _is_name_part(text[j]):
                j += 1
            out.append(Token("NAME", text[i:j], lineno, i, j, text[i:j]))
            i = j
        else:
            for op in _OPERATORS:
                if text.startswith(op, i):
                    if op in syntax.op_modes:
                        _spelling(syntax.op_modes[op], f"'{op}'", syntax, (lineno, i), warn)
                    canon = _CANONICAL.get(op, op)
                    out.append(Token("OP", canon, lineno, i, i + len(op), op))
                    i += len(op)
                    break
            else:
                raise PseudocodeSyntaxError(f"unexpected character {c!r}", lineno, i)


def _superscript_tokens(text: str, at: tuple[int, int], syntax: Syntax, warn: Warn) -> list[Token]:
    """A run of superscripts at `at` (line, column) is an exponent: `²` and `⁻¹` stay one SUP
    token (a number); with letters, signs or brackets, `2ˣ⁺¹` reads as `2^(x+1)`."""
    lineno, i = at
    end = i
    while end < len(text) and text[end] in SUPERSCRIPT_RUN:
        end += 1
    plain = "".join(SUPERSCRIPT_RUN[ch] for ch in text[i:end])
    digits = plain.removeprefix("-")
    if digits.isascii() and digits.isdigit():
        return [_scan_superscript(text, i, lineno)]
    inner: list[Token] = []
    _tokenize_line(plain, lineno, inner, syntax, warn)
    return [
        Token("OP", "^", lineno, i, i, "^"),
        Token("OP", "(", lineno, i, i, "("),
        *(replace(tok, col=tok.col + i, end=tok.end + i) for tok in inner),
        Token("OP", ")", lineno, end, end, ")"),
    ]


def _scan_superscript(text: str, i: int, lineno: int) -> Token:
    j, n, sign = i, len(text), ""
    if text[j] == SUPERSCRIPT_MINUS:
        sign, j = "-", j + 1
    start = j
    while j < n and text[j] in SUPERSCRIPT:
        j += 1
    if j == start:
        raise PseudocodeSyntaxError("a superscript minus needs digits", lineno, i)
    digits = "".join(SUPERSCRIPT[ch] for ch in text[start:j])
    return Token("SUP", sign + digits, lineno, i, j)


def _is_digit(c: str) -> bool:
    """A decimal digit, not a superscript one (`2E3²` is 2E3 squared)."""
    return c.isdigit() and c not in SUPERSCRIPT


def _scan_number(text: str, i: int) -> int:
    n = len(text)
    j = i
    while j < n and _is_digit(text[j]):
        j += 1
    if j < n and text[j] == "." and not text.startswith("..", j):
        j += 1
        while j < n and _is_digit(text[j]):
            j += 1
    # Scientific notation is `E` or `ᴇ` only; lowercase `e` is never an exponent marker.
    if j < n and text[j] in "Eᴇ":
        k = j + 1
        if k < n and text[k] in "+-−":
            k += 1
        if k < n and _is_digit(text[k]):
            while k < n and _is_digit(text[k]):
                k += 1
            return k
    return j
