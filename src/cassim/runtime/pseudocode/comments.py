"""Comments kept across translation (Simon, 2026-11-22).

Both translators work on trees, which have no comments. A full-line comment is attached to the
next statement: the translator writes a placeholder line before that statement (so it lands in
the right block, at its indentation), and the placeholder becomes the comment in the output.
Comments after the last statement go at the end. End-of-line comments are not kept yet.

Blank lines travel the same way (Simon, 2026-11-22): a blank line is a comment with no text
(`None`). The translators add a blank line of their own before a function, so runs of blank
lines are written as one.
"""

import io
import re
import tokenize
from collections.abc import Iterable
from dataclasses import fields, is_dataclass
from typing import get_args

from cassim.runtime.pseudocode.tree import Stmt

PLACEHOLDER = "__cassim_comment_{}__"
_PLACEHOLDER_LINE = re.compile(r"(?m)^([ \t]*)__cassim_comment_(\d+)__$")
_BLANK_RUN = re.compile(r"\n(?:[ \t]*\n)+")
_STATEMENTS = get_args(Stmt.__value__)


def pseudocode_comments(lines: list[str], markers: Iterable[str]) -> list[tuple[int, str | None]]:
    """Full-line comments: (line number, the text after the marker), and blank lines."""
    found: list[tuple[int, str | None]] = []
    for number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            found.append((number, None))
            continue
        for marker in sorted(markers, key=len, reverse=True):
            if text.startswith(marker):
                found.append((number, text[len(marker) :]))
                break
    return found


def python_comments(source: str) -> list[tuple[int, str | None]]:
    """Full-line Python comments, leaving out the translator's own `# CASSim` notes, and
    blank lines (not those inside a string)."""
    found: list[tuple[int, str | None]] = []
    lines = source.splitlines()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError, SyntaxError:
        return found
    for token in tokens:
        if token.type == tokenize.NL and not token.line.strip():
            found.append((token.start[0], None))
            continue
        if token.type != tokenize.COMMENT:
            continue
        row, column = token.start
        if lines[row - 1][:column].strip() or token.string.startswith("# CASSim"):
            continue
        found.append((row, token.string[1:]))
    return found


def statement_lines(tree: object) -> list[int]:
    """The line of every pseudocode statement in a tree (or list of them)."""
    found: list[int] = []
    stack = [tree]
    while stack:
        node = stack.pop()
        if isinstance(node, _STATEMENTS):
            found.append(node.line)
        if isinstance(node, (list, tuple)):
            stack.extend(node)
        elif is_dataclass(node) and not isinstance(node, type):
            stack.extend(getattr(node, f.name) for f in fields(node))
    return found


def anchor(
    comments: list[tuple[int, str | None]], lines: Iterable[int]
) -> tuple[dict[int, list[int]], list[str | None], list[int]]:
    """Attach each comment to the next statement's line.

    Returns (statement line -> placeholder numbers, every comment's text by placeholder
    number, placeholder numbers of the comments after the last statement)."""
    starts = sorted(set(lines))
    before: dict[int, list[int]] = {}
    texts: list[str | None] = []
    trailing: list[int] = []
    for line, text in comments:
        if text is None and not any(start > line for start in starts):
            continue  # blank lines at the end are not kept
        number = len(texts)
        texts.append(text)
        following = next((start for start in starts if start > line), None)
        if following is None:
            trailing.append(number)
        else:
            before.setdefault(following, []).append(number)
    return before, texts, trailing


def restore(code: str, texts: list[str | None], trailing: list[int], marker: str) -> str:
    """Turn the placeholders back into comments written with `marker`, and blank lines."""

    def line(match: re.Match[str]) -> str:
        text = texts[int(match.group(2))]
        return "" if text is None else match.group(1) + marker + text

    restored = _BLANK_RUN.sub("\n\n", _PLACEHOLDER_LINE.sub(line, code)).lstrip("\n")
    if trailing:  # only comments: blank lines at the end are not anchored
        restored = (
            restored.rstrip("\n")
            + "\n"
            + "".join(marker + str(texts[number]) + "\n" for number in trailing)
        )
    return restored
