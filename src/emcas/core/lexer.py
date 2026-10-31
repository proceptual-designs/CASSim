"""TI grammar tokenizer.

Alternative spellings are folded to one canonical form here (`<=` to `≤`, `@>` to `▶`), so the
parser sees each symbol in one form only. Text is otherwise kept as typed.

Three symbols look alike in ASCII but differ on the calculator, so canonical text is Unicode:
`e` is an ordinary variable, `ⅇ` is Euler's constant, and `ᴇ` is the exponent marker in `1.5ᴇ3`.
A plain `E` is also just a variable. The `@` spellings are TI's own (CAS guide 3.2, pp. 164-165).
"""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

from emcas.core.errors import MISSING_QUOTE, SYNTAX, TISyntaxError


class Kind(Enum):
    NUMBER = auto()
    DMS = auto()
    STRING = auto()
    NAME = auto()
    OP = auto()
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    kind: Kind
    text: str
    pos: int
    space_before: bool = False


# Spelling -> canonical operator.
_OPERATORS = {
    ":=": ":=",
    "<=>": "⇔",
    "=>": "⇒",
    "<=": "≤",
    ">=": "≥",
    "/=": "≠",
    "->": "→",
    "@>": "▶",
    "@<": "∠",
    "►": "▶",  # the guide's glyph; ▶ is the one the handheld shows
    "−": "-",
    "·": "*",
    "×": "*",
    "∗": "*",
    ".^": ".^",
    ".*": ".*",
    "./": "./",
    ".+": ".+",
    ".-": ".-",
    **{ch: ch for ch in "+-*/^=<>≤≥≠(){}[],;:|!%°'&#∠→▶ᵀʳᴳ⇒⇔"},
}
_OPERATOR_RE = re.compile("|".join(re.escape(s) for s in sorted(_OPERATORS, key=len, reverse=True)))
_POSTFIX_AT = {"t": "ᵀ", "r": "ʳ", "g": "ᴳ", "d": "°"}
_POSTFIX_AT_RE = re.compile(r"@([trgd])(?![0-9A-Za-z])")
_AT_CONSTANT = {"e": "ⅇ", "i": "ⅈ"}
_AT_CONSTANT_RE = re.compile(r"@([ei])(?![0-9A-Za-z])")
_AT_NAME_RE = re.compile(r"@[A-Za-z][0-9A-Za-z]*")
_NUMBER_RE = re.compile(
    r"0[bB][01]+|0[hH][0-9a-fA-F]+|(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:(?:ᴇ|@E)[+-]?[0-9]+)?"
)
_DMS_RE = re.compile(
    r"""[0-9]+(?:\.[0-9]*)?(?:°|@d)[0-9]+(?:\.[0-9]*)?'(?:[0-9]+(?:\.[0-9]*)?")?"""
)
# Catalog entries with an arrow inside the name, such as list▶mat( and P▶Rx(.
# TI displays inverse functions this way; arcsin is the typed form.
_INVERSE_NAME_RE = re.compile(r"(?:sin|cos|tan|sec|csc|cot)h?⁻¹")
_ARROW_NAME_RE = re.compile(
    r"(freqTable|list|mat|exp|P|R)(?:▶|►|@>)(list|mat|Rx|Ry|Pr|Pθ|Ptheta)(?=\()", re.IGNORECASE
)

WORD_OPERATORS = frozenset({"and", "or", "not", "xor", "nor", "nand"})
_ONE_CHAR_NAMES = frozenset("π∞ⅈⅇ√∫∏∑")
# Letters to Python, but symbols to the calculator.
_NOT_NAME_CHARS = _ONE_CHAR_NAMES | frozenset("ᵀʳᴳᴇ")


def _is_name_start(ch: str) -> bool:
    return ch == "_" or (ch.isalpha() and ch not in _NOT_NAME_CHARS)


def _is_name_char(ch: str, prev: str, dotted: bool) -> bool:
    category = unicodedata.category(ch)
    if ch == "_" or category == "Mn":  # Mn: combining marks, as in stat.x̄
        return True
    if ch in _NOT_NAME_CHARS:
        return False
    if category == "No":  # ² and ₁: stat.r² and χ²Cdf are names, x² is not
        return dotted or prev == "χ"
    return ch.isalnum()


def _name_end(src: str, start: int) -> int:
    """Return the end of the name at `start`, including `lib\\fn` and `stat.x` parts."""
    i = start + 1
    dotted = False
    while i < len(src):
        if _is_name_char(src[i], src[i - 1], dotted):
            i += 1
        elif src[i] in "\\." and i + 1 < len(src) and _is_name_start(src[i + 1]):
            dotted = dotted or src[i] == "."
            i += 2
        else:
            break
    return i


def _scan_string(src: str, start: int, space: bool) -> tuple[Token, int]:
    end = src.find('"', start + 1)
    if end < 0:
        raise TISyntaxError(MISSING_QUOTE, start)
    return Token(Kind.STRING, src[start + 1 : end], start, space), end + 1


def _scan_name(src: str, start: int, space: bool) -> tuple[Token, int]:
    end = _name_end(src, start)
    text = src[start:end]
    kind = Kind.OP if text.casefold() in WORD_OPERATORS else Kind.NAME
    return Token(kind, text.casefold() if kind is Kind.OP else text, start, space), end


# Tokens with a fixed shape, in priority order, each with the way to read its match.
_FIXED_TOKENS: tuple[tuple[re.Pattern[str], Kind, Callable[[re.Match[str]], str]], ...] = (
    (_DMS_RE, Kind.DMS, lambda m: m.group().replace("@d", "°")),
    (_NUMBER_RE, Kind.NUMBER, lambda m: m.group().replace("@E", "ᴇ")),
    (_INVERSE_NAME_RE, Kind.NAME, lambda m: m.group()),
    (_ARROW_NAME_RE, Kind.NAME, lambda m: f"{m.group(1)}▶{m.group(2)}"),
    (_POSTFIX_AT_RE, Kind.OP, lambda m: _POSTFIX_AT[m.group(1)]),
    (_OPERATOR_RE, Kind.OP, lambda m: _OPERATORS[m.group()]),
    (_AT_CONSTANT_RE, Kind.NAME, lambda m: _AT_CONSTANT[m.group(1)]),
    (_AT_NAME_RE, Kind.NAME, lambda m: m.group()),
)


def _scan_fixed(src: str, i: int, space: bool) -> tuple[Token, int] | None:
    for pattern, kind, read in _FIXED_TOKENS:
        if m := pattern.match(src, i):
            return Token(kind, read(m), i, space), m.end()
    return None


def _scan(src: str, i: int, space: bool) -> tuple[Token, int]:
    ch = src[i]
    if ch == '"':
        return _scan_string(src, i, space)
    found = _scan_fixed(src, i, space)
    if found:
        return found
    if ch in _ONE_CHAR_NAMES:
        return Token(Kind.NAME, ch, i, space), i + 1
    if _is_name_start(ch):
        return _scan_name(src, i, space)
    raise TISyntaxError(SYNTAX, i)


def tokenize(src: str) -> list[Token]:
    """Split an entry line into tokens, ending with an EOF token."""
    tokens: list[Token] = []
    i = 0
    space = False
    while i < len(src):
        if src[i].isspace():
            i += 1
            space = True
            continue
        token, i = _scan(src, i, space)
        tokens.append(token)
        space = False
    tokens.append(Token(Kind.EOF, "", len(src), space))
    return tokens
