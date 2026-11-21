"""Token-aware, single-keystroke convenience conversions for pseudocode source."""


def _in_code(source: str, end: int) -> bool:
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


def _insertion(previous: str, current: str) -> int | None:
    if len(current) != len(previous) + 1:
        return None
    index = 0
    limit = min(len(previous), len(current))
    while index < limit and previous[index] == current[index]:
        index += 1
    if current[index + 1 :] != previous[index:]:
        return None
    return index


# Keys typed while the browser is busy can reach Python as one change: an insertion this short
# with no line break is replayed one key at a time. Anything longer is a paste and left alone.
TYPED_BURST = 4


def _burst(previous: str, current: str) -> tuple[int, str] | None:
    extra = len(current) - len(previous)
    if not 1 < extra <= TYPED_BURST:
        return None
    start = 0
    while start < len(previous) and previous[start] == current[start]:
        start += 1
    if current[start + extra :] != previous[start:]:
        return None
    inserted = current[start : start + extra]
    return None if "\n" in inserted else (start, inserted)


def convert_typing(previous: str, current: str) -> str:
    """Convert newly typed characters, leaving paste and source text contexts untouched."""
    index = _insertion(previous, current)
    if index is not None:
        return _convert_key(current, index)
    burst = _burst(previous, current)
    if burst is None:
        return current
    caret, inserted = burst
    text = previous
    for char in inserted:
        typed = text[:caret] + char + text[caret:]
        text = _convert_key(typed, caret)
        caret += 1 + len(text) - len(typed)
    return text


def _convert_key(current: str, index: int) -> str:
    """Apply the conversion that typing `current[index]` completes, if any."""
    if not _in_code(current, index):
        return current
    through = current[: index + 1]
    operators = {"<-": "←", "<=": "≤", ">=": "≥", "!=": "≠"}
    operator = through[-2:]
    if operator in operators:
        return current[: index - 1] + operators[operator] + current[index + 1 :]
    aliases = {"@e": "ⅇ", "@pi": "π"}
    for alias, symbol in aliases.items():
        if through.endswith(alias):
            start = len(through) - len(alias)
            return through[:start] + symbol + current[index + 1 :]
    return current


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
        if _in_code(source, i):
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
