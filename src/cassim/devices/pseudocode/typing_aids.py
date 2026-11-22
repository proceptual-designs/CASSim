"""Token-aware, single-keystroke convenience conversions for pseudocode source."""

from cassim.runtime.pseudocode.lexer import SUPERSCRIPT_RUN
from cassim.runtime.pseudocode.typing_aid import LATEX_WORDS


def in_code(source: str, end: int) -> bool:
    """Whether `source[end]` is in code, not in a string or a comment."""
    quote = ""
    comment = False
    i = 0
    while i < end:
        char = source[i]
        if char == "\n":
            quote = ""
            comment = False
        elif comment:
            pass
        elif quote:
            if char == quote:
                quote = ""
        elif char in {'"', "“"}:
            quote = char
        elif source.startswith("//", i) or char == "#":
            comment = True
        i += 1
    return not comment and not quote


# Keys typed while the browser is busy can reach Python as one change: an insertion this short
# is still typing. Anything longer is a paste and left alone.
TYPED_BURST = 4
OPERATORS = {"<-": "←", "<=": "≤", ">=": "≥", "!=": "≠"}
ALIASES = (("@pi", "π"), ("@e", "ⅇ"))


def typed_span(previous: str, current: str) -> tuple[int, int] | None:
    """Where `current` has text typed into `previous`: (start, end) of the inserted text, or
    None for a deletion, a replacement or a paste (more than TYPED_BURST characters, or a
    line break with other characters)."""
    extra = len(current) - len(previous)
    if not 1 <= extra <= TYPED_BURST:
        return None
    start = 0
    while start < len(previous) and previous[start] == current[start]:
        start += 1
    if current[start + extra :] != previous[start:]:
        return None
    if extra > 1 and "\n" in current[start : start + extra]:
        return None
    return start, start + extra


# What each plain character becomes in a superscript: digits, + - ( ), lowercase letters
# but q (from the lexer, which reads a superscript run back as the exponent).
TO_SUPERSCRIPT = {plain: sup for sup, plain in SUPERSCRIPT_RUN.items()}


def _bracket_end(text: str, start: int) -> int | None:
    """The index of the `)` matching the `(` at `start`, if it has been typed."""
    depth = 0
    for index in range(start, len(text)):
        depth += {"(": 1, ")": -1}.get(text[index], 0)
        if depth == 0:
            return index
    return None


def _superscript_group(inner: str) -> str | None:
    """`x + 1` in superscripts, or None if any character has no superscript form. Spaces go
    only beside a sign or a bracket, where they cannot join two names."""
    kept = [
        char
        for at, char in enumerate(inner)
        if char != " "
        or not (
            (at == 0 or inner[at - 1] in " +-()")
            or (at == len(inner) - 1 or inner[at + 1] in " +-()")
        )
    ]
    if not kept or any(char not in TO_SUPERSCRIPT for char in kept):
        return None
    return "".join(TO_SUPERSCRIPT[char] for char in kept)


def _superscript_at(text: str, index: int) -> tuple[int, str, int] | None:
    """A power the typing aid writes in superscripts (the lexer reads a run back as the
    exponent, so the brackets of `^( )` are dropped: `2^(x+1)` becomes `2ˣ⁺¹`):

    - `^(...)` once its `)` is typed, if every character inside has a superscript form
      (not `*`, `/`, q or capitals);
    - `^2`, `^-1`, `^n` once a character follows that cannot continue the number or name
      (not a letter, digit, `.`, `_` or `(`), so `x^2.5`, `x^2e3` and `x^f(2)` stay as typed.
      That character stays; it completes the conversion."""
    if not text.startswith("^", index):
        return None
    start = index + 1
    if text.startswith("(", start):
        close = _bracket_end(text, start)
        group = None if close is None else _superscript_group(text[start + 1 : close])
        if close is None or group is None:
            return None
        return close + 1 - index, group, close + 1 - index
    minus = text.startswith("-", start)
    first = start + minus
    after = first
    if after < len(text) and text[after].isdigit():
        while after < len(text) and text[after] in "0123456789":
            after += 1
    elif after < len(text) and text[after] in TO_SUPERSCRIPT and text[after].isalpha():
        while after < len(text) and text[after] in TO_SUPERSCRIPT and text[after].isalnum():
            after += 1
    if after == first or after >= len(text):
        return None
    following = text[after]
    if following.isalnum() or following in "._(":
        return None
    return after - index, "".join(TO_SUPERSCRIPT[c] for c in text[start:after]), after - index + 1


def _spelling_at(text: str, index: int) -> tuple[int, str, int] | None:
    """The typing-aid spelling that starts at `index`: (its length, what it becomes, and how
    far from `index` the character that completes it ends)."""
    for spelling, symbol in OPERATORS.items():
        if text.startswith(spelling, index):
            return len(spelling), symbol, len(spelling)
    for alias, symbol in ALIASES:
        after = index + len(alias)
        if text.startswith(alias, index) and not (
            after < len(text) and (text[after].isalnum() or text[after] == "_")
        ):
            return len(alias), symbol, len(alias)  # not the start of a name such as @exp
    if text.startswith("\\", index):
        for word in sorted(LATEX_WORDS, key=len, reverse=True):
            after = index + len(word)
            if text.startswith(word, index) and after < len(text) and text[after] in " \n":
                return len(word) + 1, LATEX_WORDS[word] + text[after], len(word) + 1
    return _superscript_at(text, index)


def convert_region(text: str, start: int, end: int) -> str:
    """Convert the typing-aid spellings (`<-`, `@pi`, `\theta `...) whose last character was
    typed in `text[start:end]`, leaving strings, comments and the rest of the text alone."""
    out: list[str] = []
    index = 0
    while index < len(text):
        found = _spelling_at(text, index)
        if found is not None and start < index + found[2] <= end and in_code(text, index):
            out.append(found[1])
            index += found[0]
            continue
        out.append(text[index])
        index += 1
    return "".join(out)


def convert_typing(previous: str, current: str) -> str:
    """Convert newly typed characters, leaving paste and source text contexts untouched."""
    span = typed_span(previous, current)
    return current if span is None else convert_region(current, *span)


def convert_symbols(source: str, style: str) -> str:
    """Rewrite recognised code symbols to Unicode or ASCII, preserving strings and comments."""
    if style not in ("unicode", "ascii"):
        raise ValueError(f"unknown symbol style: {style}")
    ascii_to_unicode = (
        ("<-", "←"),
        ("<=", "≤"),
        (">=", "≥"),
        ("!=", "≠"),
        ("<>", "≠"),
        ("@pi", "π"),
        ("@e", "ⅇ"),
    )
    unicode_to_ascii = (
        ("←", "<-"),
        ("≤", "<="),
        ("≥", ">="),
        ("≠", "!="),
        ("π", "@pi"),
        ("ⅇ", "@e"),
        ("×", "*"),
        ("÷", "/"),
    )
    replacements = ascii_to_unicode if style == "unicode" else unicode_to_ascii
    out: list[str] = []
    i = 0
    while i < len(source):
        if in_code(source, i):
            for old, new in replacements:
                end = i + len(old)
                macro_boundary = (
                    not old.startswith("@")
                    or end == len(source)
                    or not (source[end].isalnum() or source[end] == "_")
                )
                if macro_boundary and source.startswith(old, i):
                    out.append(new)
                    i = end
                    break
            else:
                out.append(source[i])
                i += 1
        else:
            out.append(source[i])
            i += 1
    return "".join(out)
