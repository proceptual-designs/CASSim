"""What the LCD draws, as a small tree (SDD-14 section 6.3).

The input line and the answer line are both sequences of these nodes. The Flet view turns them into
controls (`ui/render.py`); `to_text` gives the one-line form the tests and the tutorials' expected
screens use. Pure data: no Flet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Text:
    text: str


@dataclass(frozen=True)
class Frac:
    num: Seq
    den: Seq


@dataclass(frozen=True)
class Sqrt:
    arg: Seq


@dataclass(frozen=True)
class Root:
    index: Seq
    arg: Seq


@dataclass(frozen=True)
class Sup:
    """A raised part: the exponent of the item before it."""

    exp: Seq


@dataclass(frozen=True)
class Sub:
    """A lowered part: the base of log■□."""

    arg: Seq


@dataclass(frozen=True)
class Abs:
    arg: Seq


@dataclass(frozen=True)
class Box:
    """An empty template slot."""


@dataclass(frozen=True)
class Cursor:
    pass


type Node = Text | Frac | Sqrt | Root | Sup | Sub | Abs | Box | Cursor
type Seq = tuple[Node, ...]

_SUPERSCRIPT = str.maketrans("0123456789-−.+()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁻·⁺⁽⁾")


def superscript(text: str) -> str:
    return text.translate(_SUPERSCRIPT)


def _plain(seq: Seq) -> str:
    return to_text(seq)


def _grouped(seq: Seq) -> str:
    shown = tuple(node for node in seq if not isinstance(node, Cursor))
    text = to_text(shown)
    simple = len(shown) == 1 and (
        isinstance(shown[0], Box)
        or (isinstance(shown[0], Text) and text.replace(".", "").isalnum())
    )
    return text if simple else f"({text})"


def to_text(seq: Seq, *, cursor: bool = False) -> str:
    """The sequence on one line: fractions as a⌟b, roots as √(…), exponents raised when they are
    plain numbers."""
    parts: list[str] = []
    for node in seq:
        match node:
            case Text(text):
                parts.append(text)
            case Frac(num, den):
                parts.append(f"{_grouped(num)}⌟{_grouped(den)}")
            case Sqrt(arg):
                parts.append(f"√{_grouped(arg)}")
            case Root(index, arg):
                parts.append(f"{superscript(_plain(index))}√{_grouped(arg)}")
            case Sup(exp):
                inner = _plain(exp)
                raised = superscript(inner)
                plain_number = all(ch in "0123456789-−." for ch in inner) and inner
                parts.append(raised if plain_number else f"^({inner})")
            case Sub(arg):
                parts.append(f"_{_grouped(arg)}")
            case Abs(arg):
                parts.append(f"|{_plain(arg)}|")
            case Box():
                parts.append("□")
            case Cursor():
                if cursor:
                    parts.append("_")
    return "".join(parts)
