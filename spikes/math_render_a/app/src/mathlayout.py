"""Spike A: TeX-style layout of the 2D editor tree from real font metrics (no Flet here).

Everything is in ems of the base font size, x to the right, y down, the root row's baseline at
y = 0. The rules follow KaTeX (which flutter_math_fork ports) in text style: atom classes and
spacing, \\frac shifts (num2/denom2 and the clearance rule), sup/sub shifts, \\sqrt's clearance,
\\left \\right sizing (delimiterFactor 901, delimiterExtend 5pt), arrays (baselineskip 12pt,
arraycolsep 5pt), and op symbols set from KaTeX_Size1 with side limits.

The output of `layout()` is a `Layout`: a flat list of draw items (glyph runs, rules, filled
polygons) and, for each row of the tree, its gaps (cursor stops), baseline and extent. Cursor,
selection and click mapping work on those numbers only; nothing about them changes the drawing.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---- fonts --------------------------------------------------------------------------------------

_METRICS: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parent / "metrics.json").read_text(encoding="utf-8")
)
MATH_ITALIC = {"Math-Italic", "Math-BoldItalic"}


def glyph(font: str, ch: str) -> tuple[float, float, float, float, float] | None:
    """(advance, height, depth, xmin, xmax) in ems, or None if the font lacks it."""
    g = _METRICS[font]["glyphs"].get(str(ord(ch)))
    return None if g is None else tuple(g)  # type: ignore[return-value]


def font_vertical(font: str) -> dict[str, list[float]]:
    m = _METRICS[font]
    return {"hhea": m["hhea"], "typo": m["typo"], "win": m["win"]}


# ---- KaTeX's font parameters (sigmas), per style size: text, script, scriptscript -------------

SIGMA = {
    "xHeight": (0.431, 0.431, 0.431),
    "quad": (1.000, 1.171, 1.472),
    "num1": (0.677, 0.732, 0.925),
    "num2": (0.394, 0.384, 0.387),
    "num3": (0.444, 0.471, 0.504),
    "denom1": (0.686, 0.752, 1.025),
    "denom2": (0.345, 0.344, 0.532),
    "sup1": (0.413, 0.503, 0.504),
    "sup2": (0.363, 0.431, 0.404),
    "sup3": (0.289, 0.286, 0.294),
    "sub1": (0.150, 0.143, 0.200),
    "sub2": (0.247, 0.286, 0.400),
    "supDrop": (0.386, 0.353, 0.494),
    "subDrop": (0.050, 0.071, 0.100),
    "axisHeight": (0.250, 0.250, 0.250),
    "rule": (0.04, 0.049, 0.049),
    "sqrtRule": (0.04, 0.04, 0.04),
}
SCALES = (1.0, 0.7, 0.5)
PT = 0.1  # 1pt in ems at 10pt


@dataclass(frozen=True, slots=True)
class St:
    """A math style: size 0 text, 1 script, 2 scriptscript; cramped or not."""

    size: int = 0
    cramped: bool = False

    @property
    def scale(self) -> float:
        return SCALES[self.size]

    def sig(self, name: str) -> float:
        return SIGMA[name][self.size] * self.scale

    @property
    def mu(self) -> float:
        return self.sig("quad") / 18

    def smaller(self, *, cramped: bool | None = None) -> St:
        return St(min(self.size + 1, 2), self.cramped if cramped is None else cramped)

    def sup(self) -> St:
        return self.smaller()

    def sub(self) -> St:
        return self.smaller(cramped=True)

    def num(self) -> St:
        return self.smaller()

    def den(self) -> St:
        return self.smaller(cramped=True)

    def cramp(self) -> St:
        return St(self.size, True)


# ---- draw items ---------------------------------------------------------------------------------


@dataclass(slots=True)
class Glyphs:
    """A run of characters in one font and size, its baseline starting at (x, y)."""

    font: str
    scale: float
    x: float
    y: float
    text: str
    width: float
    exact: bool  # the run's width is exactly the font's own advances, so it can be merged


@dataclass(slots=True)
class Rule:
    x: float
    y: float  # top
    w: float
    h: float


@dataclass(slots=True)
class Poly:
    points: list[tuple[float, float]]


type Item = Glyphs | Rule | Poly


def _shift(item: Item, dx: float, dy: float) -> Item:
    match item:
        case Glyphs():
            return Glyphs(item.font, item.scale, item.x + dx, item.y + dy, item.text, item.width, item.exact)
        case Rule():
            return Rule(item.x + dx, item.y + dy, item.w, item.h)
        case Poly():
            return Poly([(x + dx, y + dy) for x, y in item.points])


# marks: ("node", key, index, x0, x1, top, bottom) and ("row", key, x0, x1, baseline, h, d, scale)
type Mark = tuple[Any, ...]


def _shift_mark(m: Mark, dx: float, dy: float) -> Mark:
    if m[0] == "node":
        return ("node", m[1], m[2], m[3] + dx, m[4] + dx, m[5] + dy, m[6] + dy)
    return ("row", m[1], m[2] + dx, m[3] + dx, m[4] + dy, m[5], m[6], m[7])


@dataclass(slots=True)
class Box:
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    items: list[Item] = field(default_factory=list)
    marks: list[Mark] = field(default_factory=list)
    italic: float = 0.0  # italic correction already included in width (op symbols)

    def put(self, child: Box, dx: float, dy: float) -> None:
        """Place `child`'s contents with its origin (left, baseline) at (dx, dy)."""
        self.items.extend(_shift(i, dx, dy) for i in child.items)
        self.marks.extend(_shift_mark(m, dx, dy) for m in child.marks)


def char_box(font: str, ch: str, st: St, shown: str | None = None) -> Box:
    text = shown if shown is not None else ch
    g = glyph(font, text) or glyph("Main-Regular", text) or glyph("AMS-Regular", text)
    if g is None:
        g = (0.5, 0.7, 0.0, 0.0, 0.5)  # unknown: a guess, and the painter's font may differ
    adv, h, d, _xmin, xmax = g
    s = st.scale
    italic = max(0.0, xmax - adv) if font in MATH_ITALIC else 0.0
    width = (adv + italic) * s
    return Box(width, h * s, d * s, [Glyphs(font, s, 0.0, 0.0, text, width, italic == 0.0)])


def kern(w: float) -> Box:
    return Box(width=w)


# ---- atoms and spacing --------------------------------------------------------------------------

THIN, MED, THICK = 3, 4, 5
_SPACING = {
    "ord": {"op": THIN, "bin": MED, "rel": THICK, "inner": THIN},
    "op": {"ord": THIN, "op": THIN, "rel": THICK, "inner": THIN},
    "bin": {"ord": MED, "op": MED, "open": MED, "inner": MED},
    "rel": {"ord": THICK, "op": THICK, "open": THICK, "inner": THICK},
    "open": {},
    "close": {"op": THIN, "bin": MED, "rel": THICK, "inner": THIN},
    "punct": {"ord": THIN, "op": THIN, "rel": THICK, "open": THIN, "close": THIN, "punct": THIN, "inner": THIN},
    "inner": {"ord": THIN, "op": THIN, "bin": MED, "rel": THICK, "open": THIN, "punct": THIN, "inner": THIN},
}
_TIGHT = {"ord": {"op": THIN}, "op": {"ord": THIN, "op": THIN}, "close": {"op": THIN}, "inner": {"op": THIN}}


@dataclass(slots=True)
class Atom:
    left: str  # class seen by the atom before it
    right: str  # class seen by the atom after it
    box: Box
    index: int | None = None  # the node it draws, for the row's marks
    key: str | None = None


def hlist(atoms: list[Atom], st: St) -> Box:
    """Set atoms side by side with TeX's inter-atom glue; mark each node's extent."""
    # a binary sign with nothing to its left (or a relation, an opening...) is unary: ord
    prev = None
    for a in atoms:
        if a.left == "bin" and (prev is None or prev.right in ("bin", "op", "rel", "open", "punct")):
            a.left = a.right = "ord"
        if a.left in ("rel", "close", "punct") and prev is not None and prev.right == "bin":
            prev.left = prev.right = "ord"
        if a.left != "kern":
            prev = a
    if prev is not None and prev.right == "bin":
        prev.left = prev.right = "ord"
    table = _TIGHT if st.size > 0 else _SPACING
    out = Box()
    x = 0.0
    prev = None
    for a in atoms:
        if a.left == "kern":
            x += a.box.width
            continue
        if prev is not None:
            x += table.get(prev.right, {}).get(a.left, 0) * st.mu
        out.put(a.box, x, 0.0)
        if a.index is not None:
            out.marks.append(("node", a.key, a.index, x, x + a.box.width, -a.box.height, a.box.depth))
        x += a.box.width
        out.height = max(out.height, a.box.height)
        out.depth = max(out.depth, a.box.depth)
        prev = a
    out.width = x
    return out


# ---- characters ---------------------------------------------------------------------------------

_SHOWN = {"-": "−", "*": "⋅", "<": "<", ">": ">"}
_BIN = frozenset("+-*±×÷")
_REL = frozenset("=<>≤≥≠→:~≈")
_OPEN = frozenset("([{")
_CLOSE = frozenset(")]}!")
_PUNCT = frozenset(",;")
_MATH_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZπθαβγδλμσφω")
_STYLE_FONT = {"roman": "Main-Regular", "bold": "Main-Bold", "bold italic": "Math-BoldItalic"}


def char_atom(ch: str, mark: list[str] | None, st: St) -> Atom:
    if mark is not None:
        style, shown = mark
        if style == "hidden":
            return Atom("ord", "ord", Box())
        return Atom("ord", "ord", char_box(_STYLE_FONT[style], ch, st, shown))
    if ch == "ⅇ":
        return Atom("ord", "ord", char_box("Main-Bold", "e", st))
    if ch == "ⅈ":
        return Atom("ord", "ord", char_box("Math-BoldItalic", "i", st))
    if ch == "ᴇ":
        return Atom("ord", "ord", char_box("Main-Regular", "E", st))
    if ch == '"':
        return Atom("ord", "ord", char_box("Typewriter-Regular", ch, st))
    if ch in _MATH_LETTERS:
        return Atom("ord", "ord", char_box("Math-Italic", ch, st))
    cls = (
        "bin" if ch in _BIN else "rel" if ch in _REL else "open" if ch in _OPEN
        else "close" if ch in _CLOSE else "punct" if ch in _PUNCT else "ord"
    )
    return Atom(cls, cls, char_box("Main-Regular", ch, st, _SHOWN.get(ch)))


# ---- delimiters ---------------------------------------------------------------------------------

_STACK = {  # top, repeat, bottom, middle (Size4 pieces)
    "(": ("⎛", "⎜", "⎝", None),
    ")": ("⎞", "⎟", "⎠", None),
    "[": ("⎡", "⎢", "⎣", None),
    "]": ("⎤", "⎥", "⎦", None),
    "{": ("⎧", "⎪", "⎩", "⎨"),
    "}": ("⎫", "⎪", "⎭", "⎬"),
}


def null_delim(st: St) -> Box:
    return kern(0.12 * st.scale)


def delimiter(ch: str, inner_h: float, inner_d: float, st: St) -> Box:
    """A \\left or \\right delimiter around content of this height and depth (KaTeX's
    makeLeftRightDelim): the smallest glyph tall enough, then Size1..4, then a stack."""
    if ch == ".":
        return null_delim(st)
    axis = st.sig("axisHeight")
    dist = max(inner_h - axis, inner_d + axis)
    total = max(dist / 500 * 901, 2 * dist - 5 * PT * st.scale)
    bar = ch == "|"
    small = "∣" if bar else ch
    # small glyphs at the current style and the bigger styles up to text size
    g = glyph("Main-Regular", small)
    assert g is not None
    for size in range(st.size, -1, -1):
        if (g[1] + g[2]) * SCALES[size] >= total:
            # a glyph from a bigger style is lowered so its axis stays on this style's axis
            return _lowered(char_box("Main-Regular", small, St(size)), 0.25 * (SCALES[size] - st.scale))
    if not bar:
        for n in range(1, 5):
            font = f"Size{n}-Regular"
            gs = glyph(font, ch)
            if gs is not None and gs[1] + gs[2] >= total:
                b = char_box(font, ch, St(0))
                return _lowered(b, (b.height - b.depth) / 2 - axis)
    return _stacked(ch, total, st)


def _lowered(b: Box, shift: float) -> Box:
    out = Box(b.width, b.height - shift, b.depth + shift)
    out.put(b, 0.0, shift)
    return out


def _stacked(ch: str, total: float, st: St) -> Box:
    """A delimiter taller than Size4: end pieces with a rule between (centred on the axis)."""
    axis = SIGMA["axisHeight"][0]
    top_y, bottom_y = -(total / 2 + axis), total / 2 - axis
    out = Box(height=total / 2 + axis, depth=total / 2 - axis)
    if ch == "|":
        g = glyph("Main-Regular", "∣")
        assert g is not None
        out.width = g[0]
        out.items.append(Rule(g[3], top_y, g[4] - g[3], total))
        return out
    top, rep, bottom, middle = _STACK[ch]
    font = "Size4-Regular"
    gt, gr, gb = glyph(font, top), glyph(font, rep), glyph(font, bottom)
    assert gt and gr and gb
    out.width = gt[0]
    # place each end piece by its ink: top piece's ink top at the stack's top, and so on
    out.items.append(Glyphs(font, 1.0, 0.0, top_y + gt[1], top, gt[0], True))
    out.items.append(Glyphs(font, 1.0, 0.0, bottom_y - gb[2], bottom, gb[0], True))
    seg_top, seg_bottom = top_y + gt[1] + gt[2], bottom_y - gb[1] - gb[2]
    if middle is not None:
        gm = glyph(font, middle)
        assert gm
        mid_h = gm[1] + gm[2]
        my = -axis  # the axis, y down
        out.items.append(Glyphs(font, 1.0, 0.0, my + (gm[1] - gm[2]) / 2, middle, gm[0], True))
        rx, rw = gr[3], gr[4] - gr[3]
        out.items.append(Rule(rx, seg_top, rw, my - mid_h / 2 - seg_top))
        out.items.append(Rule(rx, my + mid_h / 2, rw, seg_bottom - my - mid_h / 2))
    elif seg_bottom > seg_top:
        out.items.append(Rule(gr[3], seg_top - 0.01, gr[4] - gr[3], seg_bottom - seg_top + 0.02))
    return out


def leftright(inner: Box, left: str, right: str, st: St) -> tuple[Box, Box, Box]:
    """The two delimiters for `inner`, sized as \\left \\right does."""
    return (delimiter(left, inner.height, inner.depth, st), inner, delimiter(right, inner.height, inner.depth, st))


def row_of(boxes: Sequence[Box]) -> Box:
    out = Box()
    x = 0.0
    for b in boxes:
        out.put(b, x, 0.0)
        x += b.width
        out.height, out.depth = max(out.height, b.height), max(out.depth, b.depth)
    out.width = x
    return out


# ---- structures ---------------------------------------------------------------------------------


def fraction(num: Box, den: Box, st: St, *, bar: bool = True) -> Box:
    rule = st.sig("rule") if bar else 0.0
    axis = st.sig("axisHeight")
    num_shift, den_shift = (st.sig("num2") if bar else st.sig("num3")), st.sig("denom2")
    clearance = rule if bar else 3 * st.sig("rule")
    if bar:
        cand = (num_shift - num.depth) - (axis + rule / 2)
        if cand < clearance:
            num_shift += clearance - cand
        cand = (axis - rule / 2) - (den.height - den_shift)
        if cand < clearance:
            den_shift += clearance - cand
    width = max(num.width, den.width)
    nd = 0.12 * st.scale
    out = Box(width + 2 * nd, num_shift + num.height, den_shift + den.depth)
    out.put(num, nd + (width - num.width) / 2, -num_shift)
    out.put(den, nd + (width - den.width) / 2, den_shift)
    if bar:
        out.items.append(Rule(nd, -(axis + rule / 2), width, rule))
    return out


def supsub(base: Box, sup: Box | None, sub: Box | None, st: St, *, char_base: bool, sup_st: St, sub_st: St) -> Box:
    """KaTeX's supsub: shifts for a superscript and/or subscript after `base`."""
    sup_shift = sub_shift = 0.0
    if not char_base:
        if sup is not None:
            sup_shift = base.height - sup_st.sig("supDrop")
        if sub is not None:
            sub_shift = base.depth + sub_st.sig("subDrop")
    xh = st.sig("xHeight")
    min_sup = st.sig("sup3") if st.cramped else st.sig("sup2")
    space = 0.05  # \scriptspace, 0.5pt at the base size
    out = Box(base.width, base.height, base.depth)
    out.put(base, 0.0, 0.0)
    if sup is not None and sub is None:
        sup_shift = max(sup_shift, min_sup, sup.depth + 0.25 * xh)
        out.put(sup, base.width, -sup_shift)
        out.width = base.width + sup.width + space
        out.height = max(base.height, sup_shift + sup.height)
        out.depth = max(base.depth, sup.depth - sup_shift)
    elif sub is not None and sup is None:
        sub_shift = max(sub_shift, st.sig("sub1"), sub.height - 0.8 * xh)
        out.put(sub, base.width - base.italic, sub_shift)
        out.width = base.width - base.italic + sub.width + space
        out.height = max(base.height, sub.height - sub_shift)
        out.depth = max(base.depth, sub_shift + sub.depth)
    elif sup is not None and sub is not None:
        sup_shift = max(sup_shift, min_sup, sup.depth + 0.25 * xh)
        sub_shift = max(sub_shift, st.sig("sub2"))
        rule = st.sig("rule")
        if (sup_shift - sup.depth) - (sub.height - sub_shift) < 4 * rule:
            sub_shift = 4 * rule - (sup_shift - sup.depth) + sub.height
            psi = 0.8 * xh - (sup_shift - sup.depth)
            if psi > 0:
                sup_shift += psi
                sub_shift -= psi
        out.put(sup, base.width, -sup_shift)
        out.put(sub, base.width - base.italic, sub_shift)
        out.width = base.width + max(sup.width, sub.width - base.italic) + space
        out.height = max(base.height, sup_shift + sup.height)
        out.depth = max(base.depth, sub_shift + sub.depth)
    return out


def op_symbol(ch: str, st: St) -> Box:
    """A big operator in text style: the Size1 glyph, centred on the axis, italic kept."""
    b = char_box("Size1-Regular", ch, st)
    g = glyph("Size1-Regular", ch)
    assert g is not None
    italic = max(0.0, g[4] - g[0]) * st.scale
    b.width += italic
    b.items[0] = Glyphs("Size1-Regular", st.scale, 0.0, 0.0, ch, b.width, italic == 0.0)
    shift = (b.height - b.depth) / 2 - st.sig("axisHeight")
    out = _lowered(b, shift)
    out.italic = italic
    return out


def op_text(word: str, st: St) -> Box:
    return row_of([char_box("Main-Regular", c, st) for c in word])


def under(base: Box, sub: Box) -> Box:
    """A limit set under its operator (KaTeX's assembleSupSub). flutter_math does this for
    `\\lim` even in text style, so we do too."""
    kern_ = max(0.166, 0.6 - sub.height)  # bigOpSpacing2, bigOpSpacing4
    width = max(base.width, sub.width)
    out = Box(width, base.height, base.depth + kern_ + sub.height + sub.depth)
    out.put(base, (width - base.width) / 2, 0.0)
    out.put(sub, (width - sub.width) / 2, base.depth + kern_ + sub.height)
    return out


def surd(inner: Box, st: St) -> Box:
    """\\sqrt: KaTeX's clearance rules; the radical sign is our own filled polygon."""
    theta = st.sig("rule")
    clearance = theta + theta / 4
    ih = inner.height if inner.height > 0 else st.sig("xHeight")
    need = ih + inner.depth + clearance + theta
    s = st.scale
    for size_h, adv in ((1.0, 0.833), (1.2, 1.0), (1.8, 1.0), (2.4, 1.0), (3.0, 1.0)):
        if size_h * s >= need or size_h == 3.0 and need <= 3.0:
            img_h, advance = size_h * s, adv * s
            break
    else:
        img_h, advance = need, 1.056 * s
    rule = SIGMA["sqrtRule"][st.size] * s
    # TeX (and KaTeX) would now share out the surd's extra depth: clearance = (clearance +
    # img_h - rule - ih - depth) / 2. flutter_math's drawing evidently does not (its √2 hugs the
    # 2, and the brackets round 1+√2 in a script numerator stay script-sized), so neither do we.
    top = -(ih + clearance + rule)
    out = Box(advance + inner.width, ih + clearance + rule, img_h - (ih + clearance + rule))
    out.put(inner, advance, 0.0)
    out.items.append(radical_poly(0.0, top, advance, img_h, inner.width, rule, s))
    return out


def radical_poly(x: float, top: float, adv: float, h: float, over: float, rule: float, s: float) -> Poly:
    """One filled outline: tick, heavy down-stroke, thin up-stroke, then the vinculum."""
    bottom = top + h
    # the sign's shape in the small size; the tick sits low on taller signs
    tick_y = bottom - min(0.42 * s, 0.42 * h)
    pts = [
        (x + 0.06 * s, tick_y + 0.035 * s),
        (x + 0.17 * s, tick_y - 0.03 * s),
        (x + 0.40 * s, bottom - 0.14 * s),  # outer edge of the heavy stroke
        (x + adv - 0.035 * s, top),
        (x + adv + over, top),
        (x + adv + over, top + rule),
        (x + adv - 0.01 * s, top + rule),
        (x + 0.415 * s, bottom),
        (x + 0.375 * s, bottom),
        (x + 0.15 * s, tick_y + 0.03 * s),
        (x + 0.085 * s, tick_y + 0.07 * s),
    ]
    return Poly(pts)


def array(cells: list[list[Box]], st: St, *, stretch: float = 1.0, align: str = "c",
          gaps: tuple[float, ...] | None = None) -> Box:
    """KaTeX's array: rows at least a strut tall, centred on the axis; columns `align`ed."""
    skip = 1.2 * stretch  # baselineskip 12pt
    strut_h, strut_d = 0.7 * skip, 0.3 * skip
    ncols = max(len(r) for r in cells)
    widths = [max((r[c].width for r in cells if c < len(r)), default=0.0) for c in range(ncols)]
    sep = gaps if gaps is not None else tuple(1.0 for _ in range(ncols - 1))  # 2 x arraycolsep
    rows: list[tuple[float, float, float]] = []  # (pos, h, d)
    total = 0.0
    for r in cells:
        h = max([strut_h, *(b.height for b in r)])
        d = max([strut_d, *(b.depth for b in r)])
        total += h
        rows.append((total, h, d))
        total += d
    offset = total / 2 + st.sig("axisHeight")
    out = Box(height=offset, depth=total - offset)
    x = 0.0
    for c in range(ncols):
        for r, (pos, _h, _d) in zip(cells, rows, strict=True):
            if c < len(r):
                b = r[c]
                dx = (widths[c] - b.width) / 2 if align == "c" else 0.0
                out.put(b, x + dx, pos - offset)
        x += widths[c] + (sep[c] if c < len(sep) else 0.0)
    out.width = x
    return out


# ---- the tree -----------------------------------------------------------------------------------

type Path_ = tuple[tuple[int, int], ...]
type StyleLookup = Callable[[Path_], dict[str, list[str]]]


def _key(path: Path_) -> str:
    return "/".join(f"{i}.{s}" for i, s in path)


def _stretched(row: list[Any]) -> dict[int, int]:
    """Round brackets that grow (`_stretch_brackets`): a pair around any template but a power."""
    pairs: dict[int, int] = {}
    opened: list[int] = []
    in_text = False
    for i, n in enumerate(row):
        if n == '"':
            in_text = not in_text
        elif in_text:
            continue
        elif n == "(":
            opened.append(i)
        elif n == ")" and opened:
            s = opened.pop()
            if any(not isinstance(m, str) and str(m.kind) != "power" for m in row[s + 1 : i]):
                pairs[s] = i
    return pairs


class _Builder:
    def __init__(self, styles: StyleLookup) -> None:
        self.styles = styles

    def row(self, row: list[Any], path: Path_, st: St) -> Box:
        key = _key(path)
        if not row:
            b = char_box("AMS-Regular", "□", st)
            out = Box(b.width, b.height, b.depth)
            out.put(b, 0.0, 0.0)
        else:
            marks = self.styles(path)
            out = hlist(self._atoms(row, 0, len(row), path, key, st, marks, _stretched(row)), st)
        out.marks.append(("row", key, 0.0, out.width, 0.0, out.height, out.depth, st.scale))
        return out

    def _atoms(self, row, a, b, path, key, st, marks, pairs) -> list[Atom]:
        atoms: list[Atom] = []
        i = a
        while i < b:
            node = row[i]
            if i in pairs and pairs[i] < b:
                j = pairs[i]
                inner = hlist(self._atoms(row, i + 1, j, path, key, st, marks, pairs), st)
                lb, _, rb = leftright(inner, "(", ")", st)
                group = Box()
                group.put(lb, 0.0, 0.0)
                group.marks.append(("node", key, i, 0.0, lb.width, -lb.height, lb.depth))
                group.put(inner, lb.width, 0.0)
                x = lb.width + inner.width
                group.put(rb, x, 0.0)
                group.marks.append(("node", key, j, x, x + rb.width, -rb.height, rb.depth))
                group.width = x + rb.width
                group.height = max(lb.height, inner.height, rb.height)
                group.depth = max(lb.depth, inner.depth, rb.depth)
                atoms.append(Atom("inner", "inner", group))
                i = j + 1
                continue
            if isinstance(node, str):
                atom = char_atom(node, marks.get(str(i)), st)
            else:
                atom = self.template(node, (*path, ), i, st)
            atom.index, atom.key = i, key
            atoms.append(atom)
            i += 1
        return atoms

    def slot(self, t, path: Path_, i: int, s: int, st: St) -> Box:
        return self.row(t.slots[s], (*path, (i, s)), st)

    def template(self, t, path: Path_, i: int, st: St) -> Atom:  # noqa: C901, PLR0911, PLR0912
        kind = str(t.kind)
        sl = lambda s, style=st: self.slot(t, path, i, s, style)  # noqa: E731
        if kind == "fraction":
            return Atom("ord", "ord", fraction(sl(0, st.num()), sl(1, st.den()), st))
        if kind == "power":
            return Atom("ord", "ord", supsub(Box(), sl(0, st.sup()), None, st, char_base=False,
                                             sup_st=st.sup(), sub_st=st.sub()))
        if kind == "root":
            return Atom("ord", "ord", surd(sl(0, st.cramp()), st))
        if kind == "nth_root":
            body = surd(sl(1, st.cramp()), st)
            index = sl(0, St(2, True))
            raise_ = 0.6 * (body.height - body.depth)
            out = Box()
            out.put(index, 5 / 18 * st.scale, -raise_)
            x = max(5 / 18 * st.scale + index.width - 10 / 18 * st.scale, 0.0)
            out.put(body, x, 0.0)
            out.width = x + body.width
            out.height = max(body.height, raise_ + index.height)
            out.depth = body.depth
            return Atom("ord", "ord", out)
        if kind == "abs":
            return Atom("inner", "inner", row_of(leftright(sl(0), "|", "|", st)))
        if kind == "matrix":
            cols = t.cols or 1
            cells = [[sl(r * cols + c) for c in range(cols)] for r in range(len(t.slots) // cols)]
            return Atom("inner", "inner", row_of(leftright(array(cells, st), "[", "]", st)))
        if kind in ("piecewise", "system"):
            cols = t.cols or 1
            cells = []
            for r in range(len(t.slots) // cols):
                line = []
                for c in range(cols):
                    b = sl(r * cols + c)
                    if kind == "piecewise" and c == 0:
                        comma = char_box("Main-Regular", ",", st)
                        b = row_of([b, comma])
                    line.append(b)
                cells.append(line)
            body = array(cells, st, stretch=1.0, align="l", gaps=(1.0,) * (cols - 1))
            return Atom("inner", "inner", row_of(leftright(body, "{", ".", st)))
        if kind == "list":
            parts: list[Atom] = []
            for s in range(len(t.slots)):
                if s:
                    parts.append(Atom("punct", "punct", char_box("Main-Regular", ",", st)))
                    parts.append(Atom("kern", "kern", kern(THIN * st.mu)))
                parts.append(Atom("ord", "ord", sl(s)))
            return Atom("inner", "inner", row_of(leftright(hlist(parts, st), "{", "}", st)))
        if kind == "log":
            base = op_text("log", st)
            op = supsub(base, None, sl(0, st.sub()), st, char_base=False, sup_st=st.sup(), sub_st=st.sub())
            arg = row_of(leftright(sl(1), "(", ")", st))
            return Atom("op", "inner", hlist([Atom("op", "op", op), Atom("inner", "inner", arg)], st))
        if kind in ("derivative", "derivative2", "derivative_n"):
            d = lambda: char_box("Math-Italic", "d", st.num())  # noqa: E731
            if kind == "derivative":
                num, var, order, expr = row_of([d()]), sl(0, st.den()), None, sl(1)
            elif kind == "derivative2":
                two = lambda: char_box("Main-Regular", "2", st.num().sup())  # noqa: E731
                num = supsub(d(), two(), None, st.num(), char_base=True, sup_st=st.num().sup(), sub_st=st.num().sub())
                var, order, expr = sl(0, st.den()), "2", sl(1)
            else:
                num = supsub(d(), sl(0, st.num().sup()), None, st.num(), char_base=True,
                             sup_st=st.num().sup(), sub_st=st.num().sub())
                var, order, expr = sl(1, st.den()), "n", sl(2)
            dst = st.den()
            den_parts = [char_box("Math-Italic", "d", dst), var]
            if order == "2":
                den_parts.append(supsub(Box(), char_box("Main-Regular", "2", dst.sup()), None, dst,
                                        char_base=False, sup_st=dst.sup(), sub_st=dst.sub()))
            elif order == "n":
                den_parts.append(supsub(Box(), sl(0, dst.sup()), None, dst, char_base=False,
                                        sup_st=dst.sup(), sub_st=dst.sub()))
            frac = fraction(num, row_of(den_parts), st)
            arg = row_of(leftright(expr, "(", ")", st))
            # flutter_math sets d/dx right against its bracket (no ord-inner thin space)
            return Atom("ord", "inner", row_of([frac, arg]))
        if kind in ("integral", "antiderivative"):
            definite = kind == "integral"
            op = op_symbol("∫", st)
            if definite:
                op = supsub(op, sl(1, st.sup()), sl(0, st.sub()), st, char_base=False,
                            sup_st=st.sup(), sub_st=st.sub())
            body, var = (sl(2), sl(3)) if definite else (sl(0), sl(1))
            atoms = [
                Atom("op", "op", op), Atom("ord", "ord", body), Atom("kern", "kern", kern(THIN * st.mu)),
                Atom("ord", "ord", char_box("Math-Italic", "d", st)), Atom("ord", "ord", var),
            ]
            return Atom("op", "ord", hlist(atoms, st))
        if kind in ("sum", "product"):
            op = op_symbol("∑" if kind == "sum" else "∏", st)
            sub_st = st.sub()
            low = hlist([Atom("ord", "ord", sl(0, sub_st)), Atom("rel", "rel", char_box("Main-Regular", "=", sub_st)),
                         Atom("ord", "ord", sl(1, sub_st))], sub_st)
            op = supsub(op, sl(2, st.sup()), low, st, char_base=False, sup_st=st.sup(), sub_st=sub_st)
            return Atom("op", "ord", hlist([Atom("op", "op", op), Atom("ord", "ord", sl(3))], st))
        if kind == "limit":
            sub_st = st.sub()
            point = supsub(sl(1, sub_st), sl(2, sub_st.sup()), None, sub_st, char_base=False,
                           sup_st=sub_st.sup(), sub_st=sub_st.sub())
            low = hlist([Atom("ord", "ord", sl(0, sub_st)), Atom("rel", "rel", char_box("Main-Regular", "→", sub_st)),
                         Atom("ord", "ord", point)], sub_st)
            op = under(op_text("lim", st), low)
            return Atom("op", "ord", hlist([Atom("op", "op", op), Atom("ord", "ord", sl(3))], st))
        if kind == "dms":
            parts = []
            for s, mark in enumerate(("∘", "′", "″")):
                sup_box = char_box("Main-Regular", mark, st.sup()) if mark != "″" else row_of(
                    [char_box("Main-Regular", "′", st.sup()), char_box("Main-Regular", "′", st.sup())])
                parts.append(supsub(sl(s), sup_box, None, st, char_base=True, sup_st=st.sup(), sub_st=st.sub()))
            return Atom("ord", "ord", row_of(parts))
        # unknown kind: its slots side by side
        return Atom("ord", "ord", row_of([sl(s) for s in range(len(t.slots))]))


# ---- the result ---------------------------------------------------------------------------------


@dataclass(slots=True)
class RowInfo:
    path: Path_
    x0: float
    x1: float
    baseline: float
    height: float
    depth: float
    scale: float
    nodes: list[tuple[float, float, float, float]] = field(default_factory=list)  # x0, x1, top, bottom
    gaps: list[float] = field(default_factory=list)


@dataclass
class Layout:
    width: float
    height: float
    depth: float
    items: list[Item]
    rows: dict[Path_, RowInfo]

    # -- cursor, selection, clicks (pure arithmetic on the rows) --

    def caret(self, path: Sequence[tuple[int, int]], pos: int) -> tuple[float, float, float]:
        r = self.rows[tuple(path)]
        x = r.gaps[pos]
        top, bottom = r.baseline - 0.75 * r.scale, r.baseline + 0.25 * r.scale
        for k in (pos - 1, pos):
            if 0 <= k < len(r.nodes):
                top, bottom = min(top, r.nodes[k][2]), max(bottom, r.nodes[k][3])
        return x, top, bottom

    def selection_rects(self, path: Sequence[tuple[int, int]], low: int, high: int) -> list[tuple[float, float, float, float]]:
        """(x, y, w, h) boxes covering nodes low..high-1 of the row at `path`."""
        r = self.rows[tuple(path)]
        if high <= low or not r.nodes:
            return []
        nodes = r.nodes[low:high]
        x0, x1 = nodes[0][0], nodes[-1][1]
        top = min([r.baseline - 0.75 * r.scale, *(n[2] for n in nodes)])
        bottom = max([r.baseline + 0.25 * r.scale, *(n[3] for n in nodes)])
        return [(x0, top, x1 - x0, bottom - top)]

    def hit(self, x: float, y: float) -> tuple[Path_, int]:
        """The innermost row whose box holds the point, and the gap in it nearest to x."""
        best: RowInfo | None = None
        pad = 0.04
        for r in self.rows.values():
            if r.x0 - pad <= x <= r.x1 + pad and r.baseline - r.height <= y <= r.baseline + r.depth:
                if best is None or len(r.path) > len(best.path) or (
                    len(r.path) == len(best.path)
                    and (r.x1 - r.x0) * (r.height + r.depth) < (best.x1 - best.x0) * (best.height + best.depth)
                ):
                    best = r
        if best is None:
            best = self.rows[()]
        pos = min(range(len(best.gaps)), key=lambda k: abs(best.gaps[k] - x))
        return best.path, pos

    def stops(self) -> list[tuple[Path_, int]]:
        """Every cursor stop in reading order (a stand-in for the editor's Left/Right)."""
        out: list[tuple[Path_, int]] = []

        def walk(path: Path_) -> None:
            r = self.rows[path]
            n = len(r.gaps)
            children: dict[int, list[Path_]] = {}
            for p in self.rows:
                if len(p) == len(path) + 1 and p[: len(path)] == path:
                    children.setdefault(p[-1][0], []).append(p)
            for pos in range(n):
                out.append((path, pos))
                for child in sorted(children.get(pos, []), key=lambda p: p[-1][1]):
                    walk(child)

        walk(())
        return out


def _rows_from_marks(marks: list[Mark]) -> dict[Path_, RowInfo]:
    rows: dict[str, RowInfo] = {}
    for m in marks:
        if m[0] == "row":
            _, key, x0, x1, base, h, d, s = m
            path = tuple(tuple(int(v) for v in step.split(".")) for step in key.split("/")) if key else ()
            rows[key] = RowInfo(path, x0, x1, base, h, d, s)  # type: ignore[arg-type]
    nodes: dict[str, dict[int, tuple[float, float, float, float]]] = {}
    for m in marks:
        if m[0] == "node":
            nodes.setdefault(m[1], {})[m[2]] = (m[3], m[4], m[5], m[6])
    for key, r in rows.items():
        found = nodes.get(key, {})
        r.nodes = [found[i] for i in range(len(found))] if found else []
        if not r.nodes:
            r.gaps = [(r.x0 + r.x1) / 2]  # an empty slot: the cursor at the box's centre
            continue
        g = [r.nodes[0][0]]
        g += [(r.nodes[k - 1][1] + r.nodes[k][0]) / 2 for k in range(1, len(r.nodes))]
        g.append(r.nodes[-1][1])
        r.gaps = g
        r.x0, r.x1 = min(r.x0, g[0]), max(r.x1, g[-1])
    return {r.path: r for r in rows.values()}


def merge_runs(items: list[Item]) -> list[Item]:
    """Join glyphs that share font, size and baseline and sit exactly at each other's advance."""
    glyphs = sorted((i for i in items if isinstance(i, Glyphs) and i.text), key=lambda g: (g.font, g.scale, g.y, g.x))
    out: list[Item] = [i for i in items if not isinstance(i, Glyphs)]
    run: Glyphs | None = None
    for g in glyphs:
        if (
            run is not None and run.exact and run.font == g.font and run.scale == g.scale
            and abs(run.y - g.y) < 1e-9 and abs(run.x + run.width - g.x) < 1e-9
        ):
            run = Glyphs(run.font, run.scale, run.x, run.y, run.text + g.text, run.width + g.width, g.exact)
            continue
        if run is not None:
            out.append(run)
        run = Glyphs(g.font, g.scale, g.x, g.y, g.text, g.width, g.exact)
    if run is not None:
        out.append(run)
    return out


def layout(row: list[Any], styles: StyleLookup = lambda _: {}, *, merge: bool = True) -> Layout:
    box = _Builder(styles).row(row, (), St())
    items = merge_runs(box.items) if merge else box.items
    return Layout(box.width, box.height, box.depth, items, _rows_from_marks(box.marks))
