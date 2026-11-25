"""TeX-style layout of the 2D editor's tree from the fonts' own metrics (decision 0038).

`layout()` turns a `Row` into a `Layout`: a flat list of things to draw (glyph runs, rules, filled
outlines) and, for every row of the tree, where it sits and where its gaps (the cursor's stops)
are. Nothing here draws, and nothing here imports Flet: a painter turns the items into shapes
(`app/math_canvas.py` today; a Flutter widget may replace it), and the cursor, the selection and
clicks are plain arithmetic on the rows. So the cursor and the selection are never part of the
maths, and moving them cannot move it.

Units are ems of the line's own text size, x to the right and y down, with the root row's
baseline at y = 0. The rules are TeX's as KaTeX applies them in text style (flutter_math, which
draws the history's LaTeX, is a port of KaTeX): atom classes and the spaces between them, the
fraction shifts and clearances, superscript and subscript shifts, the radical's clearance,
`\\left \\right` sizing, arrays, and big operators with their limits at the side. The numbers
come from the KaTeX fonts Flet ships (`math_metrics.json`, written by
`tools/math_metrics.py`).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path as FilePath

from cassim.device.editor import (
    Row,
    Style,
    Template,
    at_constants,
    constant_style,
    name_styles,
)
from cassim.device.templates import Kind

type Path = tuple[tuple[int, int], ...]  # a row's place in the tree: (node index, slot) steps
type Metrics = tuple[float, float, float, float, float]  # advance, height, depth, ink left, right
type Rect = tuple[float, float, float, float]  # x, y (top), width, height

FALLBACK = ""  # the "font" of a character no KaTeX font has: the painter uses the app's own
_UNKNOWN: Metrics = (0.6, 0.7, 0.0, 0.0, 0.6)  # a guess at such a character
MAIN, BOLD, ITALIC, BOLD_ITALIC = "Main-Regular", "Main-Bold", "Math-Italic", "Math-BoldItalic"
AMS, TYPEWRITER = "AMS-Regular", "Typewriter-Regular"
_SLANTED = frozenset({ITALIC, BOLD_ITALIC})


@cache
def _metrics() -> dict[str, dict[str, Metrics]]:
    source = FilePath(__file__).with_name("math_metrics.json").read_text(encoding="utf-8")
    return {
        font: {chr(int(code)): tuple(values) for code, values in data["glyphs"].items()}
        for font, data in json.loads(source).items()
    }


@cache
def ascent(font: str) -> float:
    """How far the baseline is below the top of a line of text in `font`, in ems: the font's
    ascender and half its line gap, which is where Flutter puts the first baseline."""
    source = FilePath(__file__).with_name("math_metrics.json").read_text(encoding="utf-8")
    up, _down, gap = json.loads(source)[font]["hhea"]
    return up + gap / 2


def glyph(font: str, char: str) -> Metrics | None:
    """A character's metrics in `font`, or None if the font lacks it."""
    return _metrics().get(font, {}).get(char)


def _found(font: str, char: str) -> tuple[str, Metrics]:
    """The font to draw `char` in (`font` if it has it) and its metrics there."""
    bold = font in (BOLD, BOLD_ITALIC)
    for name in (font, BOLD if bold else MAIN, MAIN, AMS):
        metrics = glyph(name, char)
        if metrics is not None:
            return name, metrics
    return FALLBACK, _UNKNOWN


# ---- TeX's font parameters, for text, script and script-of-script size -------------------------

_SIGMA = {
    "xHeight": (0.431, 0.431, 0.431),
    "quad": (1.000, 1.171, 1.472),
    "num2": (0.394, 0.384, 0.387),
    "denom2": (0.345, 0.344, 0.532),
    "sup2": (0.363, 0.431, 0.404),
    "sup3": (0.289, 0.286, 0.294),
    "sub1": (0.150, 0.143, 0.200),
    "sub2": (0.247, 0.286, 0.400),
    "supDrop": (0.386, 0.353, 0.494),
    "subDrop": (0.050, 0.071, 0.100),
    "axisHeight": (0.250, 0.250, 0.250),
    "rule": (0.04, 0.049, 0.049),
}
SCALES = (1.0, 0.7, 0.5)
_SMALLEST = len(SCALES) - 1
_NULL_DELIMITER = 0.12  # the space TeX leaves either side of a fraction
_SCRIPT_SPACE = 0.05  # after a superscript or a subscript
_EXTEND = 0.5  # a stretched bracket may be this much shorter than what it holds
LINE_ASCENT, LINE_DESCENT = 0.75, 0.25  # a line of text, for the cursor and the selection


@dataclass(frozen=True, slots=True)
class Size:
    """A TeX style: 0 text, 1 script, 2 script of a script; cramped under a bar or a radical."""

    level: int = 0
    cramped: bool = False

    @property
    def scale(self) -> float:
        return SCALES[self.level]

    def of(self, name: str) -> float:
        """A font parameter at this size, in ems of the line's size."""
        return _SIGMA[name][self.level] * self.scale

    @property
    def mu(self) -> float:
        return self.of("quad") / 18

    def raised(self) -> Size:
        return Size(min(self.level + 1, _SMALLEST), self.cramped)

    def lowered(self) -> Size:
        return Size(min(self.level + 1, _SMALLEST), True)

    def cramp(self) -> Size:
        return Size(self.level, True)


_TEXT = Size()
_TINY = Size(_SMALLEST, True)

# ---- what is drawn, and what is remembered about where -----------------------------------------


@dataclass(slots=True)
class Glyphs:
    """Characters in one font and size, the baseline starting at (x, y)."""

    font: str
    scale: float
    x: float
    y: float
    text: str
    width: float
    joins: bool = True  # the width is the font's own advances, so the next run may be joined on
    faint: bool = False  # a bracket Enter will add

    def moved(self, dx: float, dy: float) -> Glyphs:
        return Glyphs(
            self.font, self.scale, self.x + dx, self.y + dy, self.text, self.width, self.joins,
            self.faint,
        )  # fmt: skip


@dataclass(slots=True)
class Rule:
    """A filled rectangle; (x, y) is its top left corner."""

    x: float
    y: float
    width: float
    height: float

    def moved(self, dx: float, dy: float) -> Rule:
        return Rule(self.x + dx, self.y + dy, self.width, self.height)


@dataclass(slots=True)
class Outline:
    """A filled polygon (a radical sign taller than any glyph)."""

    points: list[tuple[float, float]]

    def moved(self, dx: float, dy: float) -> Outline:
        return Outline([(x + dx, y + dy) for x, y in self.points])


type Item = Glyphs | Rule | Outline


@dataclass(slots=True)
class _NodeMark:
    """Where node `index` of the row at `path` was set."""

    path: Path
    index: int
    x0: float
    x1: float
    top: float
    bottom: float

    def moved(self, dx: float, dy: float) -> _NodeMark:
        return _NodeMark(
            self.path, self.index, self.x0 + dx, self.x1 + dx, self.top + dy, self.bottom + dy
        )


@dataclass(slots=True)
class _RowMark:
    path: Path
    x0: float
    x1: float
    baseline: float
    height: float
    depth: float
    scale: float

    def moved(self, dx: float, dy: float) -> _RowMark:
        return _RowMark(
            self.path, self.x0 + dx, self.x1 + dx, self.baseline + dy, self.height, self.depth,
            self.scale,
        )  # fmt: skip


@dataclass(slots=True)
class _AreaMark:
    """The part of a template that is a slot's own for clicks: a matrix cell with its padding,
    the whole width above a fraction's bar."""

    path: Path
    x0: float
    x1: float
    top: float
    bottom: float

    def moved(self, dx: float, dy: float) -> _AreaMark:
        return _AreaMark(self.path, self.x0 + dx, self.x1 + dx, self.top + dy, self.bottom + dy)


type _Mark = _NodeMark | _RowMark | _AreaMark


@dataclass(slots=True)
class Box:
    """Something set: its size about its baseline, and its contents placed from its left end."""

    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    items: list[Item] = field(default_factory=list)
    marks: list[_Mark] = field(default_factory=list)
    italic: float = 0.0  # how far a big operator's top leans past its foot (its subscript tucks in)
    path: Path | None = None  # the row this is, when it is a slot

    def put(self, child: Box, dx: float = 0.0, dy: float = 0.0) -> None:
        """Place `child` with the left end of its baseline at (dx, dy)."""
        self.items.extend(item.moved(dx, dy) for item in child.items)
        self.marks.extend(mark.moved(dx, dy) for mark in child.marks)

    def area(self, slot: Box, x: tuple[float, float], y: tuple[float, float]) -> None:
        if slot.path is not None:
            self.marks.append(_AreaMark(slot.path, x[0], x[1], y[0], y[1]))


def _char_box(font: str, char: str, size: Size) -> Box:
    font, (advance, height, depth, _left, right) = _found(font, char)
    scale = size.scale
    lean = max(0.0, right - advance) if font in _SLANTED else 0.0  # TeX's italic correction
    width = (advance + lean) * scale
    run = Glyphs(font, scale, 0.0, 0.0, char, width, joins=lean == 0.0 and font != FALLBACK)
    return Box(width, height * scale, depth * scale, [run])


def _word(text: str, size: Size) -> Box:
    return _beside([_char_box(MAIN, char, size) for char in text])


def _beside(boxes: Sequence[Box]) -> Box:
    out = Box()
    for box in boxes:
        out.put(box, out.width)
        out.width += box.width
        out.height, out.depth = max(out.height, box.height), max(out.depth, box.depth)
    return out


def _dropped(box: Box, by: float) -> Box:
    out = Box(box.width, box.height - by, box.depth + by, italic=box.italic)
    out.put(box, 0.0, by)
    return out


# ---- atoms and the spaces between them ----------------------------------------------------------

_THIN, _MEDIUM, _THICK = 3, 4, 5  # in mu, an 18th of a quad
_SPACES: dict[str, dict[str, int]] = {
    "ord": {"op": _THIN, "bin": _MEDIUM, "rel": _THICK, "inner": _THIN},
    "op": {"ord": _THIN, "op": _THIN, "rel": _THICK, "inner": _THIN},
    "bin": {"ord": _MEDIUM, "op": _MEDIUM, "open": _MEDIUM, "inner": _MEDIUM},
    "rel": {"ord": _THICK, "op": _THICK, "open": _THICK, "inner": _THICK},
    "open": {},
    "close": {"op": _THIN, "bin": _MEDIUM, "rel": _THICK, "inner": _THIN},
    "punct": dict.fromkeys(("ord", "op", "open", "close", "punct", "inner"), _THIN)
    | {"rel": _THICK},
    "inner": dict.fromkeys(("ord", "op", "open", "punct", "inner"), _THIN)
    | {"bin": _MEDIUM, "rel": _THICK},
}
# In a script only an operator name keeps its thin space
_TIGHT_SPACES: dict[str, dict[str, int]] = {
    "ord": {"op": _THIN},
    "op": {"ord": _THIN, "op": _THIN},
    "close": {"op": _THIN},
    "inner": {"op": _THIN},
}
_NOT_AFTER = frozenset({"bin", "op", "rel", "open", "punct"})  # a `+` after one of these is a sign
_NOT_BEFORE = frozenset({"rel", "close", "punct"})  # and so is one before one of these
_SPACE = "space"  # not an atom: TeX's own space, which the atoms either side see past


@dataclass(slots=True)
class Atom:
    left: str  # the class the atom before it sees
    right: str  # the class the atom after it sees
    box: Box
    index: int | None = None  # the node of its row that it draws


def _atom(kind: str, box: Box) -> Atom:
    return Atom(kind, kind, box)


def _signs(atoms: list[Atom]) -> None:
    """A binary operator with nothing to work on is an ordinary sign (TeX's rule)."""
    before: Atom | None = None
    for atom in atoms:
        if atom.left == _SPACE:
            continue
        if atom.left == "bin" and (before is None or before.right in _NOT_AFTER):
            atom.left = atom.right = "ord"
        if atom.left in _NOT_BEFORE and before is not None and before.right == "bin":
            before.left = before.right = "ord"
        before = atom
    if before is not None and before.right == "bin":
        before.left = before.right = "ord"


def _line(atoms: list[Atom], size: Size, path: Path | None = None) -> Box:
    """The atoms side by side with TeX's spaces between; each node's place is marked."""
    _signs(atoms)
    spaces = _TIGHT_SPACES if size.level else _SPACES
    out = Box()
    x = 0.0
    before: Atom | None = None
    for atom in atoms:
        if before is not None and atom.left != _SPACE:
            x += spaces.get(before.right, {}).get(atom.left, 0) * size.mu
        out.put(atom.box, x)
        if atom.index is not None and path is not None:
            box = atom.box
            out.marks.append(_NodeMark(path, atom.index, x, x + box.width, -box.height, box.depth))
        x += atom.box.width
        out.height, out.depth = max(out.height, atom.box.height), max(out.depth, atom.box.depth)
        if atom.left != _SPACE:
            before = atom
    out.width = x
    return out


# ---- characters ---------------------------------------------------------------------------------

# Characters named by code point are ones an editor's font may draw like another
_DIVIDES, _SIMILAR, _PRIME = chr(0x2223), chr(0x223C), chr(0x2032)
_SHOWN = {"-": "−", "*": "⋅", "·": "⋅", "|": _DIVIDES, "~": _SIMILAR, "▶": "▹", "ᴇ": "E"}
_RAISED = {"°": "∘", "'": _PRIME, "ᵀ": "T", "ʳ": "r", "ᵍ": "g"}  # set as superscripts
_CLASSES = {
    **dict.fromkeys("+-*±×÷▶", "bin"),
    **dict.fromkeys("=<>≤≥≠→:~≈", "rel"),
    **dict.fromkeys("([{", "open"),
    **dict.fromkeys(")]}!?", "close"),
    **dict.fromkeys(",;", "punct"),
}
_GREEK = frozenset("πθαβγδελμσφω")
_STYLED = {Style.ROMAN: MAIN, Style.BOLD: BOLD, Style.BOLD_ITALIC: BOLD_ITALIC}
_NOT = chr(0xE020)  # the stroke TeX puts through `=` to make `≠`


def _not_equal(size: Size) -> Box:
    box = _char_box(MAIN, "=", size)
    box.put(_char_box(MAIN, _NOT, size))
    return box


# Characters with a drawing of their own: the constants, bold so they stand out from the
# variables e and i; `≠`, which no font here has whole; a string's quote, straight
_SPECIAL: dict[str, tuple[str, Callable[[Size], Box]]] = {
    "ⅇ": ("ord", lambda size: _char_box(BOLD, "e", size)),
    "ⅈ": ("ord", lambda size: _char_box(BOLD_ITALIC, "i", size)),
    "≠": ("rel", _not_equal),
    '"': ("ord", lambda size: _char_box(TYPEWRITER, '"', size)),
    " ": (_SPACE, lambda size: Box(width=0.25 * size.scale)),
}


def _char_atom(char: str, style: Style | None, size: Size) -> Atom:
    if style is not None:
        return _atom("ord", _char_box(_STYLED[style], _SHOWN.get(char, char), size))
    if char in _SPECIAL:
        kind, draw = _SPECIAL[char]
        return _atom(kind, draw(size))
    if char in _RAISED:
        mark = _char_box(MAIN, _RAISED[char], size.raised())
        return _atom("ord", _scripts(Box(), mark, None, size))
    if (char.isascii() and char.isalpha()) or char in _GREEK:
        return _atom("ord", _char_box(ITALIC, char, size))
    return _atom(_CLASSES.get(char, "ord"), _char_box(MAIN, _SHOWN.get(char, char), size))


# ---- brackets -----------------------------------------------------------------------------------

_LARGE = ("Size1-Regular", "Size2-Regular", "Size3-Regular", "Size4-Regular")
_PIECES = {  # top, middle (or None), bottom, and the piece repeated between: all in the last font
    "(": ("⎛", None, "⎝", "⎜"),
    ")": ("⎞", None, "⎠", "⎟"),
    "[": ("⎡", None, "⎣", "⎢"),
    "]": ("⎤", None, "⎦", "⎥"),
    "{": ("⎧", "⎨", "⎩", "⎪"),
    "}": ("⎫", "⎬", "⎭", "⎪"),
}


def _bracket(char: str, inner: Box, size: Size) -> Box:
    """`\\left` or `\\right` round `inner`: the smallest glyph tall enough at this size or a
    larger one, then the four large sizes, then one built from pieces."""
    if not char:
        return Box(width=_NULL_DELIMITER * size.scale)
    axis = size.of("axisHeight")
    reach = max(inner.height - axis, inner.depth + axis)
    total = max(reach / 500 * 901, 2 * reach - _EXTEND * size.scale)
    shown = _SHOWN.get(char, char)
    metrics = glyph(MAIN, shown)
    if metrics is not None:
        for level in range(size.level, -1, -1):
            if (metrics[1] + metrics[2]) * SCALES[level] > total:
                # a glyph from a larger size is lowered to keep its middle on this size's axis
                small = _char_box(MAIN, shown, Size(level))
                return _dropped(small, 0.25 * (SCALES[level] - size.scale))
    if char in _PIECES:
        for font in _LARGE:
            metrics = glyph(font, char)
            if metrics is not None and metrics[1] + metrics[2] > total:
                large = _char_box(font, char, _TEXT)
                return _dropped(large, (large.height - large.depth) / 2 - axis)
    return _built(char, total, axis)


def _built(char: str, total: float, axis: float) -> Box:
    """A bracket taller than any glyph: end pieces with a rule between, centred on the axis."""
    top, bottom = -(total / 2 + axis), total / 2 - axis
    out = Box(height=-top, depth=bottom)
    if char not in _PIECES:  # an absolute value's bar
        _advance, _h, _d, left, right = glyph(MAIN, _DIVIDES) or _UNKNOWN
        out.width = _advance
        out.items.append(Rule(left, top, right - left, total))
        return out
    font = _LARGE[-1]
    first, middle, last, repeat = _PIECES[char]
    head, foot, link = (glyph(font, piece) or _UNKNOWN for piece in (first, last, repeat))
    out.width = head[0]
    out.items.append(Glyphs(font, 1.0, 0.0, top + head[1], first, head[0]))
    out.items.append(Glyphs(font, 1.0, 0.0, bottom - foot[2], last, foot[0]))
    upper, lower = top + head[1] + head[2], bottom - foot[1] - foot[2]
    x, width = link[3], link[4] - link[3]
    if middle is None:
        if lower > upper:
            out.items.append(Rule(x, upper - 0.01, width, lower - upper + 0.02))
        return out
    waist = glyph(font, middle) or _UNKNOWN
    half = (waist[1] + waist[2]) / 2
    out.items.append(Glyphs(font, 1.0, 0.0, -axis + (waist[1] - waist[2]) / 2, middle, waist[0]))
    out.items.append(Rule(x, upper - 0.01, width, -axis - half - upper + 0.02))
    out.items.append(Rule(x, -axis + half - 0.01, width, lower + axis - half + 0.02))
    return out


def _fenced(inner: Box, left: str, right: str, size: Size) -> Box:
    return _beside([_bracket(left, inner, size), inner, _bracket(right, inner, size)])


# ---- fractions, scripts, radicals, arrays -------------------------------------------------------


def _fraction(top: Box, bottom: Box, size: Size) -> Box:
    rule, axis = size.of("rule"), size.of("axisHeight")
    up, down = size.of("num2"), size.of("denom2")
    up += max(0.0, rule - ((up - top.depth) - (axis + rule / 2)))
    down += max(0.0, rule - ((axis - rule / 2) - (bottom.height - down)))
    width = max(top.width, bottom.width)
    pad = _NULL_DELIMITER * size.scale
    out = Box(width + 2 * pad, up + top.height, down + bottom.depth)
    out.put(top, pad + (width - top.width) / 2, -up)
    out.put(bottom, pad + (width - bottom.width) / 2, down)
    out.items.append(Rule(pad, -(axis + rule / 2), width, rule))
    # all the width above the bar is the numerator's for a click, and all below the denominator's
    out.area(top, (pad, pad + width), (-out.height, -axis - rule))
    out.area(bottom, (pad, pad + width), (-axis + rule, out.depth))
    return out


def _scripts(
    base: Box, above: Box | None, below: Box | None, size: Size, *, char: bool = False
) -> Box:
    """`base` with a superscript and/or a subscript (TeX's rules 18a to 18f)."""
    up = down = 0.0
    if not char:
        up = base.height - size.raised().of("supDrop") if above is not None else 0.0
        down = base.depth + size.lowered().of("subDrop") if below is not None else 0.0
    x_height, rule = size.of("xHeight"), size.of("rule")
    out = Box(base.width, base.height, base.depth)
    out.put(base)
    tucked = base.width - base.italic  # a subscript sits under an operator's foot
    if above is not None:
        up = max(up, size.of("sup3" if size.cramped else "sup2"), above.depth + 0.25 * x_height)
    if above is not None and below is not None:
        down = max(down, size.of("sub2"))
        gap = (up - above.depth) - (below.height - down)
        if gap < 4 * rule:
            down += 4 * rule - gap
            lift = max(0.0, 0.8 * x_height - (up - above.depth))
            up, down = up + lift, down - lift
    elif below is not None:
        down = max(down, size.of("sub1"), below.height - 0.8 * x_height)
    if above is not None:
        out.put(above, base.width, -up)
        out.width = base.width + above.width + _SCRIPT_SPACE
        out.height = max(out.height, up + above.height)
        out.depth = max(out.depth, above.depth - up)
    if below is not None:
        out.put(below, tucked, down)
        out.width = max(out.width, tucked + below.width + _SCRIPT_SPACE)
        out.height = max(out.height, below.height - down)
        out.depth = max(out.depth, down + below.depth)
    return out


def _operator(char: str, size: Size) -> Box:
    """∫, ∑ or ∏ in text style: the first large size, centred on the axis."""
    font = _LARGE[0]
    _advance, _h, _d, _left, right = glyph(font, char) or _UNKNOWN
    box = _char_box(font, char, size)
    lean = max(0.0, right - _advance) * size.scale
    run = box.items[0]
    assert isinstance(run, Glyphs)
    box.width += lean
    run.width, run.joins = box.width, lean == 0.0
    out = _dropped(box, (box.height - box.depth) / 2 - size.of("axisHeight"))
    out.italic = lean
    return out


def _under(base: Box, below: Box) -> Box:
    """`below` centred under `base`, as a limit's `x→0` is even in text style."""
    gap = max(0.166, 0.6 - below.height)
    width = max(base.width, below.width)
    out = Box(width, base.height, base.depth + gap + below.height + below.depth)
    out.put(base, (width - base.width) / 2)
    out.put(below, (width - below.width) / 2, base.depth + gap + below.height)
    return out


_SURD = "√"
_SURD_RULE = 0.04  # the bar's thickness, which is drawn into the top of each sign's glyph
_TALL_SURD_WIDTH = 1.056


def _radical(inner: Box, size: Size) -> Box:
    """A square root. The sign is the first glyph taller than the radicand and its clearance:
    the ordinary one at this size or a larger, then the four large ones; what the sign has to
    spare is shared above and below the radicand (TeX's rule 11)."""
    clearance = size.of("rule") * 1.25
    height = inner.height or size.of("xHeight")
    signs = [(MAIN, SCALES[level]) for level in range(size.level, -1, -1)]
    signs += [(font, 1.0) for font in _LARGE]
    font, scale, advance, up, tall = "", 1.0, _TALL_SURD_WIDTH, 0.0, 0.0
    for name, at in signs:
        metrics = glyph(name, _SURD) or _UNKNOWN
        if (metrics[1] + metrics[2]) * at > height + inner.depth + clearance + _SURD_RULE * at:
            font, scale = name, at
            advance, up, tall = metrics[0] * at, metrics[1] * at, (metrics[1] + metrics[2]) * at
            break
    rule = _SURD_RULE * scale
    need = height + inner.depth + clearance + rule
    tall = max(tall, need)
    clearance += (tall - need) / 2
    top = height + clearance + rule
    out = Box(advance + inner.width, top, max(tall - top, inner.depth))
    if font:
        out.items.append(Glyphs(font, scale, 0.0, up - top, _SURD, advance))
    else:
        out.items.append(_tall_surd(-top, tall, inner.width, rule))
    out.items.append(Rule(advance, -top, inner.width, rule))
    out.put(inner, advance)
    return out


def _tall_surd(top: float, height: float, over: float, rule: float) -> Outline:
    """A radical sign taller than the largest glyph, as one outline: the tick, the heavy
    down stroke, the thin up stroke and the start of the bar."""
    bottom, right = top + height, _TALL_SURD_WIDTH
    tick = bottom - 0.42
    return Outline(
        [
            (0.06, tick + 0.035),
            (0.17, tick - 0.03),
            (0.40, bottom - 0.14),
            (right - 0.035, top),
            (right + min(over, 0.05), top),
            (right + min(over, 0.05), top + rule),
            (right - 0.01, top + rule),
            (0.415, bottom),
            (0.375, bottom),
            (0.15, tick + 0.03),
            (0.085, tick + 0.07),
        ]
    )


_ROW_SKIP = 1.2  # an array's rows are at least this far apart
_COLUMN_GAP = 1.0


def _array(cells: list[list[Box]], size: Size, *, centred: bool = True) -> Box:
    """A grid: each row at least a strut tall, the whole centred on the axis."""
    columns = max(len(row) for row in cells)
    widths = [
        max((row[c].width for row in cells if c < len(row)), default=0.0) for c in range(columns)
    ]
    lines: list[tuple[float, float, float]] = []  # baseline from the top, height, depth
    total = 0.0
    for row in cells:
        height = max([0.7 * _ROW_SKIP, *(box.height for box in row)])
        depth = max([0.3 * _ROW_SKIP, *(box.depth for box in row)])
        lines.append((total + height, height, depth))
        total += height + depth
    lift = total / 2 + size.of("axisHeight")
    out = Box(height=lift, depth=total - lift)
    x = 0.0
    for c in range(columns):
        for row, (baseline, height, depth) in zip(cells, lines, strict=True):
            if c >= len(row):
                continue
            box = row[c]
            out.put(box, x + ((widths[c] - box.width) / 2 if centred else 0.0), baseline - lift)
            # a cell's click area takes half the gap to the next column, but none of a bracket
            edges = (
                x - (_COLUMN_GAP / 2 if c else 0.0),
                x + widths[c] + (_COLUMN_GAP / 2 if c < columns - 1 else 0.0),
            )
            out.area(box, edges, (baseline - height - lift, baseline + depth - lift))
        x += widths[c] + (_COLUMN_GAP if c < columns - 1 else 0.0)
    out.width = x
    return out


# ---- the tree -----------------------------------------------------------------------------------

_EMPTY = "□"


def stretched_brackets(row: Row) -> dict[int, int]:
    """The round brackets that grow with what they hold: each pair round a template other than a
    power, opening index to closing index (as `\\left( \\right)` in the LaTeX)."""
    pairs: dict[int, int] = {}
    opened: list[int] = []
    in_text = False
    for index, node in enumerate(row):
        if node == '"':
            in_text = not in_text
        elif in_text:
            continue
        elif node == "(":
            opened.append(index)
        elif node == ")" and opened:
            start = opened.pop()
            inside = row[start + 1 : index]
            if any(isinstance(n, Template) and n.kind is not Kind.POWER for n in inside):
                pairs[start] = index
    return pairs


@dataclass(slots=True)
class _Setting:
    """One row being set: what each of its characters is drawn as."""

    row: Row
    path: Path
    size: Size
    styles: dict[int, Style]
    constants: dict[int, str]
    pairs: dict[int, int]


class _Slots:
    """A template's slots, each set on request at a size."""

    def __init__(self, builder: _Builder, node: Template, path: Path, size: Size) -> None:
        self.builder, self.node, self.path, self.size = builder, node, path, size

    def __call__(self, slot: int, size: Size | None = None) -> Box:
        path = (*self.path[:-1], (self.path[-1][0], slot))
        return self.builder.row(self.node.slots[slot], path, size or self.size)

    def __len__(self) -> int:
        return len(self.node.slots)

    @property
    def cols(self) -> int:
        return self.node.cols or 1


class _Builder:
    def __init__(self, is_defined: Callable[[str], bool]) -> None:
        self.is_defined = is_defined

    def row(self, row: Row, path: Path, size: Size, closers: str = "") -> Box:
        if row or not path:
            setting = _Setting(
                row, path, size, name_styles(row, self.is_defined), at_constants(row),
                stretched_brackets(row),
            )  # fmt: skip
            atoms = self._atoms(setting, 0, len(row))
            for char in closers:
                ghost = _char_atom(char, None, size)
                for item in ghost.box.items:
                    if isinstance(item, Glyphs):
                        item.faint = True
                atoms.append(ghost)
            out = _line(atoms, size, path)
        else:  # an empty slot is a box to type in
            out = _char_box(AMS, _EMPTY, size)
        out.marks.append(_RowMark(path, 0.0, out.width, 0.0, out.height, out.depth, size.scale))
        out.path = path
        return out

    def _atoms(self, setting: _Setting, start: int, end: int) -> list[Atom]:
        atoms: list[Atom] = []
        row, size = setting.row, setting.size
        index = start
        while index < end:
            close = setting.pairs.get(index, end)
            if close < end:
                atoms.append(self._pair(setting, index, close))
                index = close + 1
                continue
            node = row[index]
            if isinstance(node, Template):
                slots = _Slots(self, node, (*setting.path, (index, 0)), size)
                atom = _TEMPLATES[node.kind](slots)
            elif index in setting.constants:
                letter = setting.constants[index]
                atom = (
                    _char_atom(letter, constant_style(letter), size)
                    if letter
                    else _atom(_SPACE, Box())
                )
            else:
                atom = _char_atom(node, setting.styles.get(index), size)
            atom.index = index
            atoms.append(atom)
            index += 1
        return atoms

    def _pair(self, setting: _Setting, start: int, end: int) -> Atom:
        """A pair of round brackets grown to what is between them, as one atom."""
        size, path = setting.size, setting.path
        inner = _line(self._atoms(setting, start + 1, end), size, path)
        left, right = _bracket("(", inner, size), _bracket(")", inner, size)
        out = _beside([left, inner, right])
        out.marks.append(_NodeMark(path, start, 0.0, left.width, -left.height, left.depth))
        out.marks.append(
            _NodeMark(path, end, out.width - right.width, out.width, -right.height, right.depth)
        )
        return _atom("inner", out)


# How each kind of template is set. A slot is asked for by its number in Tab order.


def _set_fraction(s: _Slots) -> Atom:
    return _atom("ord", _fraction(s(0, s.size.raised()), s(1, s.size.lowered()), s.size))


def _set_power(s: _Slots) -> Atom:
    return _atom("ord", _scripts(Box(), s(0, s.size.raised()), None, s.size))


def _set_root(s: _Slots) -> Atom:
    return _atom("ord", _radical(s(0, s.size.cramp()), s.size))


def _set_nth_root(s: _Slots) -> Atom:
    body = _radical(s(1, s.size.cramp()), s.size)
    index = s(0, _TINY)
    lift = 0.6 * (body.height - body.depth)
    lead = 5 / 18 * s.size.scale
    x = max(lead + index.width - 2 * lead, 0.0)
    out = Box(x + body.width, max(body.height, lift + index.height), body.depth)
    out.put(index, lead, -lift)
    out.put(body, x)
    return _atom("ord", out)


def _set_abs(s: _Slots) -> Atom:
    return _atom("inner", _fenced(s(0), "|", "|", s.size))


def _grid(s: _Slots, *, comma: bool = False) -> list[list[Box]]:
    cells: list[list[Box]] = []
    for start in range(0, len(s), s.cols):
        line = [s(start + c) for c in range(s.cols)]
        if comma:  # a piecewise value is followed by a comma, then its condition
            line[0] = _beside([line[0], _char_box(MAIN, ",", s.size)])
            line[0].path = None
        cells.append(line)
    return cells


def _set_matrix(s: _Slots) -> Atom:
    return _atom("inner", _fenced(_array(_grid(s), s.size), "[", "]", s.size))


def _set_piecewise(s: _Slots) -> Atom:
    return _atom(
        "inner", _fenced(_array(_grid(s, comma=True), s.size, centred=False), "{", "", s.size)
    )


def _set_system(s: _Slots) -> Atom:
    return _atom("inner", _fenced(_array(_grid(s), s.size, centred=False), "{", "", s.size))


def _set_list(s: _Slots) -> Atom:
    parts: list[Atom] = []
    for slot in range(len(s)):
        if slot:
            parts.append(_atom("punct", _char_box(MAIN, ",", s.size)))
            parts.append(_atom(_SPACE, Box(width=_THIN * s.size.mu)))
        parts.append(_atom("ord", s(slot)))
    return _atom("inner", _fenced(_line(parts, s.size), "{", "}", s.size))


def _set_log(s: _Slots) -> Atom:
    name = _scripts(_word("log", s.size), None, s(0, s.size.lowered()), s.size)
    argument = _fenced(s(1), "(", ")", s.size)
    return Atom("op", "inner", _line([_atom("op", name), _atom("inner", argument)], s.size))


def _derivative(s: _Slots, order: Callable[[Size], Box] | None, variable: int) -> Atom:
    """d/dx, d²/dx² or dⁿ/dxⁿ of the bracketed last slot; `order` sets the 2 or the n."""
    up, down = s.size.raised(), s.size.lowered()
    top = _char_box(ITALIC, "d", up)
    under = [_char_box(ITALIC, "d", down), s(variable, down)]
    if order is not None:
        top = _scripts(top, order(up.raised()), None, up, char=True)
        under.append(_scripts(Box(), order(down.raised()), None, down))
    fraction = _fraction(top, _beside(under), s.size)
    argument = _fenced(s(len(s) - 1), "(", ")", s.size)
    return Atom("ord", "inner", _beside([fraction, argument]))  # d/dx sits against its bracket


def _set_derivative(s: _Slots) -> Atom:
    return _derivative(s, None, 0)


def _set_derivative2(s: _Slots) -> Atom:
    return _derivative(s, lambda size: _char_box(MAIN, "2", size), 0)


def _set_derivative_n(s: _Slots) -> Atom:
    return _derivative(s, lambda size: s(0, size), 1)


def _integral(s: _Slots, sign: Box, body: int) -> Atom:
    atoms = [
        _atom("op", sign),
        _atom("ord", s(body)),
        _atom(_SPACE, Box(width=_THIN * s.size.mu)),
        _atom("ord", _char_box(ITALIC, "d", s.size)),
        _atom("ord", s(body + 1)),
    ]
    return Atom("op", "ord", _line(atoms, s.size))


def _set_integral(s: _Slots) -> Atom:
    sign = _operator("∫", s.size)
    sign = _scripts(sign, s(1, s.size.raised()), s(0, s.size.lowered()), s.size)
    return _integral(s, sign, 2)


def _set_antiderivative(s: _Slots) -> Atom:
    return _integral(s, _operator("∫", s.size), 0)


def _series(s: _Slots, sign: str) -> Atom:
    small = s.size.lowered()
    start = [
        _atom("ord", s(0, small)),
        _atom("rel", _char_box(MAIN, "=", small)),
        _atom("ord", s(1, small)),
    ]
    head = _scripts(_operator(sign, s.size), s(2, s.size.raised()), _line(start, small), s.size)
    return Atom("op", "ord", _line([_atom("op", head), _atom("ord", s(3))], s.size))


def _set_limit(s: _Slots) -> Atom:
    small = s.size.lowered()
    point = _scripts(s(1, small), s(2, small.raised()), None, small)
    approach = [
        _atom("ord", s(0, small)),
        _atom("rel", _char_box(MAIN, "→", small)),
        _atom("ord", point),
    ]
    head = _under(_word("lim", s.size), _line(approach, small))
    return Atom("op", "ord", _line([_atom("op", head), _atom("ord", s(3))], s.size))


def _set_dms(s: _Slots) -> Atom:
    raised = s.size.raised()
    parts: list[Box] = []
    for slot, marks in enumerate(("∘", _PRIME, _PRIME * 2)):
        mark = _beside([_char_box(MAIN, char, raised) for char in marks])
        parts.append(_scripts(s(slot), mark, None, s.size, char=True))
    return _atom("ord", _beside(parts))


_TEMPLATES: dict[Kind, Callable[[_Slots], Atom]] = {
    Kind.FRACTION: _set_fraction,
    Kind.POWER: _set_power,
    Kind.ROOT: _set_root,
    Kind.MATRIX: _set_matrix,
    Kind.NTH_ROOT: _set_nth_root,
    Kind.LOG: _set_log,
    Kind.ABS: _set_abs,
    Kind.PIECEWISE: _set_piecewise,
    Kind.SYSTEM: _set_system,
    Kind.DERIVATIVE: _set_derivative,
    Kind.DERIVATIVE2: _set_derivative2,
    Kind.DERIVATIVE_N: _set_derivative_n,
    Kind.DMS: _set_dms,
    Kind.INTEGRAL: _set_integral,
    Kind.ANTIDERIVATIVE: _set_antiderivative,
    Kind.SUM: lambda s: _series(s, "∑"),
    Kind.PRODUCT: lambda s: _series(s, "∏"),
    Kind.LIMIT: _set_limit,
    Kind.LIST: _set_list,
}
# Every kind this sets; a test checks it against `Kind`, so a new kind cannot fall through unseen
SET_KINDS = frozenset(_TEMPLATES)

# ---- the result ---------------------------------------------------------------------------------


@dataclass(slots=True)
class RowPlace:
    """Where one row of the tree was set."""

    path: Path
    x0: float
    x1: float
    baseline: float
    height: float
    depth: float
    scale: float
    nodes: list[Rect] = field(default_factory=list)  # each node's box
    gaps: list[float] = field(default_factory=list)  # x of each cursor stop: len(row) + 1 of them
    area: Rect | None = None  # the part of its template that is this row's for a click

    @property
    def box(self) -> Rect:
        return (self.x0, self.baseline - self.height, self.x1 - self.x0, self.height + self.depth)


_HIT_PAD = 0.04


@dataclass(slots=True)
class Layout:
    width: float
    height: float
    depth: float
    items: list[Item]
    rows: dict[Path, RowPlace]

    def caret(self, path: Sequence[tuple[int, int]], pos: int) -> tuple[float, float, float]:
        """The cursor at `pos` in the row at `path`: its x, its top and its bottom. It is as
        tall as a line of the row's text, whatever is beside it."""
        row = self.rows[tuple(path)]
        x = row.gaps[max(0, min(pos, len(row.gaps) - 1))]
        return x, row.baseline - LINE_ASCENT * row.scale, row.baseline + LINE_DESCENT * row.scale

    def selection(self, path: Sequence[tuple[int, int]], low: int, high: int) -> Rect | None:
        """The box round nodes `low` to `high - 1` of the row at `path`."""
        row = self.rows[tuple(path)]
        nodes = row.nodes[low:high]
        if not nodes:
            return None
        left, right = nodes[0][0], nodes[-1][0] + nodes[-1][2]
        top = min([row.baseline - LINE_ASCENT * row.scale, *(node[1] for node in nodes)])
        bottom = max(
            [row.baseline + LINE_DESCENT * row.scale, *(node[1] + node[3] for node in nodes)]
        )
        return (left, top, right - left, bottom - top)

    def cell(self, path: Sequence[tuple[int, int]]) -> Rect:
        """The whole of a grid's cell, padding and all (for a selected row or column)."""
        row = self.rows[tuple(path)]
        return row.area or row.box

    def hit(self, x: float, y: float) -> tuple[Path, int]:
        """The place a click at (x, y) means: the innermost row there, and its nearest gap."""
        best = self.rows[()]
        size = float("inf")
        for row in self.rows.values():
            left, top, width, height = row.area or row.box
            inside = left - _HIT_PAD <= x <= left + width + _HIT_PAD and top <= y <= top + height
            if not inside or not row.path:
                continue
            deeper = len(row.path) - len(best.path)
            if deeper > 0 or (deeper == 0 and width * height < size):
                best, size = row, width * height
        return best.path, min(range(len(best.gaps)), key=lambda k: abs(best.gaps[k] - x))


def _places(marks: list[_Mark]) -> dict[Path, RowPlace]:
    rows: dict[Path, RowPlace] = {}
    nodes: dict[Path, dict[int, Rect]] = {}
    areas: dict[Path, Rect] = {}
    for mark in marks:
        if isinstance(mark, _RowMark):
            rows[mark.path] = RowPlace(
                mark.path, mark.x0, mark.x1, mark.baseline, mark.height, mark.depth, mark.scale
            )
        elif isinstance(mark, _NodeMark):
            box = (mark.x0, mark.top, mark.x1 - mark.x0, mark.bottom - mark.top)
            nodes.setdefault(mark.path, {})[mark.index] = box
        else:
            areas[mark.path] = (mark.x0, mark.top, mark.x1 - mark.x0, mark.bottom - mark.top)
    for path, row in rows.items():
        row.area = areas.get(path)
        found = nodes.get(path, {})
        row.nodes = [found[index] for index in range(len(found))]
        if not row.nodes:  # an empty row: the cursor in the middle of its box (or at the start)
            row.gaps = [(row.x0 + row.x1) / 2 if path else row.x0]
            continue
        # a gap is midway between its neighbours, so the cursor sits in the space TeX left
        ends = [(left, left + width) for left, _top, width, _height in row.nodes]
        row.gaps = [
            ends[0][0],
            *((ends[k - 1][1] + ends[k][0]) / 2 for k in range(1, len(ends))),
            ends[-1][1],
        ]
    return rows


def _joined(items: list[Item]) -> list[Item]:
    """Glyph runs that follow one another exactly, in one font and size on one baseline, as one
    run: a line of plain text is then a single thing to draw."""
    runs = sorted(
        (item for item in items if isinstance(item, Glyphs) and item.text),
        key=lambda run: (run.font, run.scale, run.faint, run.y, run.x),
    )
    out: list[Item] = [item for item in items if not isinstance(item, Glyphs)]
    last: Glyphs | None = None
    for run in runs:
        follows = (
            last is not None
            and last.joins
            and (last.font, last.scale, last.faint) == (run.font, run.scale, run.faint)
            and abs(last.y - run.y) < 1e-9  # noqa: PLR2004
            and abs(last.x + last.width - run.x) < 1e-9  # noqa: PLR2004
        )
        if follows and last is not None:
            last.text += run.text
            last.width += run.width
            last.joins = run.joins
            continue
        last = run.moved(0.0, 0.0)
        out.append(last)
    return out


def layout(
    row: Row, is_defined: Callable[[str], bool] = lambda _: False, *, closers: str = ""
) -> Layout:
    """Set `row`. A name `is_defined` says the Problem defines is bold; `closers` are the
    brackets Enter will add, drawn faintly after the row."""
    box = _Builder(is_defined).row(row, (), _TEXT, closers)
    return Layout(box.width, box.height, box.depth, _joined(box.items), _places(box.marks))


def width(row: Row) -> float:
    """How wide `row` is drawn, in ems."""
    return layout(row).width


def lines(row: Row) -> float:
    """How tall `row` is drawn, in lines of its text: 1 for plain text, more for a fraction, a
    matrix, a raised power."""
    set_out = layout(row)
    return max(set_out.height, LINE_ASCENT) + max(set_out.depth, LINE_DESCENT)
