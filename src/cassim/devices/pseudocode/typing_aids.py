"""Token-aware, single-keystroke convenience conversions for pseudocode source."""

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


def _spelling_at(text: str, index: int) -> tuple[int, str] | None:
    """The typing-aid spelling that starts at `index`: (its length, what it becomes)."""
    for spelling, symbol in OPERATORS.items():
        if text.startswith(spelling, index):
            return len(spelling), symbol
    for alias, symbol in ALIASES:
        after = index + len(alias)
        if text.startswith(alias, index) and not (
            after < len(text) and (text[after].isalnum() or text[after] == "_")
        ):
            return len(alias), symbol  # not the start of a longer name such as @exp
    if text.startswith("\\", index):
        for word in sorted(LATEX_WORDS, key=len, reverse=True):
            after = index + len(word)
            if text.startswith(word, index) and after < len(text) and text[after] in " \n":
                return len(word) + 1, LATEX_WORDS[word] + text[after]
    return None


def convert_region(text: str, start: int, end: int) -> str:
    """Convert the typing-aid spellings (`<-`, `@pi`, `\theta `...) whose last character was
    typed in `text[start:end]`, leaving strings, comments and the rest of the text alone."""
    out: list[str] = []
    index = 0
    while index < len(text):
        found = _spelling_at(text, index)
        if found is not None and start < index + found[0] <= end and in_code(text, index):
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
