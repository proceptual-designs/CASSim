"""Simple box layout of the editor tree (spike B). Pure Python: no Flet import.

A Box has a width, an ascent and a descent about its baseline and a list of items drawn relative to
its origin (x from the left, y from the baseline, downward positive). Items are tuples:
  ("t", x, y, text, face, size, sy)   text run; y is the baseline; sy a vertical scale about it
  ("r", x, y, w, h)                   filled rectangle (rules, bars); y is the top
  ("f", x, y, w, h)                   outlined rectangle (an empty slot)
Every row of the tree is recorded (RowInfo) with the x of each gap, so the caret, the selection and a
click are exact: nothing is estimated from the painted result.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from cassim.device.editor import Row, Template, at_constants, constant_style, name_styles
from cassim.device.editor import Style
from cassim.device.templates import Kind

_METRICS = json.loads((Path(__file__).parent / "metrics.json").read_text(encoding="utf-8"))

# face key -> (Flutter family suffix, bold, italic, metrics file)
FACES = {
    "main": ("Main", False, False, "Main-Regular"),
    "bold": ("Main", True, False, "Main-Bold"),
    "math": ("Math", False, True, "Math-Italic"),
    "mathbi": ("Math", True, True, "Math-BoldItalic"),
    "size1": ("Size1", False, False, "Size1-Regular"),
    "size2": ("Size2", False, False, "Size2-Regular"),
    "size3": ("Size3", False, False, "Size3-Regular"),
    "size4": ("Size4", False, False, "Size4-Regular"),
}
AXIS = 0.25  # the maths axis, in em
type Path = tuple[tuple[int, int], ...]


def glyph(face: str, ch: str) -> tuple[float, float, float]:
    """(advance, ymax, ymin) in em; a character the face lacks is measured as 0.5 wide."""
    g = _METRICS[FACES[face][3]]["glyphs"].get(ch)
    return (g[0], g[1], g[2]) if g else (0.5, 0.65, 0.0)


def baseline_offset(face: str, size: float) -> float:
    """Distance from the top of a Text (TextStyle height=1.0) to its baseline: half-leading plus
    ascent, measured in the browser to within 1 px (probe_placement.py)."""
    asc, desc = _METRICS[FACES[face][3]]["hhea"][:2]
    return (1.0 + asc + desc) / 2.0 * size  # desc is stored negative


@dataclass
class RowInfo:
    path: Path
    gaps: list[float]
    x0: float
    x1: float
    top: float
    bot: float
    nodes: list[tuple[float, float, float, float]] = field(default_factory=list)  # x0,x1,top,bot

    def moved(self, dx: float, dy: float) -> RowInfo:
        return RowInfo(
            self.path,
            [g + dx for g in self.gaps],
            self.x0 + dx,
            self.x1 + dx,
            self.top + dy,
            self.bot + dy,
            [(a + dx, b + dx, c + dy, d + dy) for a, b, c, d in self.nodes],
        )


class Box:
    def __init__(self, w: float = 0.0, asc: float = 0.0, desc: float = 0.0) -> None:
        self.w, self.asc, self.desc = w, asc, desc
        self.items: list[tuple] = []
        self.rows: list[RowInfo] = []

    def add(self, child: Box, dx: float, dy: float) -> None:
        for it in child.items:
            if it[0] == "t":
                self.items.append(("t", it[1] + dx, it[2] + dy, *it[3:]))
            else:
                self.items.append((it[0], it[1] + dx, it[2] + dy, *it[3:]))
        self.rows.extend(r.moved(dx, dy) for r in child.rows)

    def rule(self, x: float, y: float, w: float, h: float) -> None:
        self.items.append(("r", x, y, w, h))


_BINARY = frozenset("+−-*·×∗")
_RELATION = frozenset("=<>≤≥≠≈▶→")
_OPEN = frozenset("([{")
_CLOSE = {"(": ")", "[": "]", "{": "}"}
_SHOWN = {"*": "·", "-": "−"}


class Layouter:
    def __init__(self, base: float = 20.0) -> None:
        self.base = base

    # ---- small helpers ----------------------------------------------------------------------

    def sub(self, s: float) -> float:
        return max(s * 0.7, self.base * 0.5)

    @staticmethod
    def rule_w(s: float) -> float:
        return max(1.0, round(s * 0.055 * 2) / 2)

    def text(self, ch: str, face: str, s: float) -> Box:
        adv, ymax, ymin = glyph(face, ch)
        b = Box(adv * s, max(ymax, 0.0) * s, max(-ymin, 0.0) * s)
        b.items.append(("t", 0.0, 0.0, ch, face, s, 1.0))
        return b

    def word(self, text: str, face: str, s: float) -> Box:
        b = Box()
        for ch in text:
            c = self.text(ch, face, s)
            b.add(c, b.w, 0.0)
            b.w += c.w
            b.asc, b.desc = max(b.asc, c.asc), max(b.desc, c.desc)
        return _merge(b)

    def delim(self, ch: str, half: float, s: float) -> Box:
        """A bracket or brace grown to `half` above and below the axis: the smallest font whose
        glyph is tall enough, stretched vertically by the remainder."""
        total = 2 * half
        faces = ["main", "size1", "size2", "size3", "size4"]
        chosen = faces[0]
        for f in faces:
            chosen = f
            _a, ymax, ymin = glyph(f, ch)
            if (ymax - ymin) * s >= total * 0.97:
                break
        adv, ymax, ymin = glyph(chosen, ch)
        ink = (ymax - ymin) * s
        k = max(total / ink, 1.0) if chosen != "main" or total > ink else 1.0
        k = total / ink if total > ink else 1.0
        centre = -AXIS * s
        y = centre + (ymax + ymin) / 2 * s * k
        b = Box(adv * s, half + AXIS * s, half - AXIS * s)
        b.items.append(("t", 0.0, y, ch, chosen, s, k))
        return b

    # ---- rows -------------------------------------------------------------------------------

    def lay_row(self, row: Row, path: Path, s: float, lvl: int = 0) -> Box:
        if not row:
            w = 0.6 * s
            b = Box(w, 0.75 * s, 0.25 * s)
            b.items.append(("f", 0.1 * s, -0.7 * s, 0.4 * s, 0.7 * s))
            b.rows.append(RowInfo(path, [w / 2], 0.0, w, -b.asc, b.desc, []))
            return b
        styles = name_styles(row, lambda _: False)
        consts = at_constants(row)
        pieces: list[Box | None] = []
        classes: list[str] = []
        for i, node in enumerate(row):
            if isinstance(node, Template):
                pieces.append(self.template(node, path, i, s, lvl))
                classes.append("template")
                continue
            ch = consts.get(i, node)
            if i in consts and ch == "":
                pieces.append(Box())
                classes.append("nothing")
                continue
            style = constant_style(ch) if i in consts and ch in ("e", "i") else styles.get(i)
            if node == "ⅇ":
                ch, style = "e", Style.BOLD
            elif node == "ⅈ":
                ch, style = "i", Style.BOLD_ITALIC
            elif node == "ᴇ":
                ch, style = "E", Style.ROMAN
            ch = _SHOWN.get(ch, ch)
            pieces.append(self.text(ch, self.face_for(ch, style), s))
            classes.append(self.char_class(ch))
        self.stretch_pairs(row, pieces, s)
        return self.assemble(row, path, pieces, classes, s, lvl)

    @staticmethod
    def face_for(ch: str, style: Style | None) -> str:
        letter = ch.isalpha() and (ch.isascii() or ch in "πθαβγδλμσφωΔΩ")
        if style is Style.BOLD_ITALIC:
            return "mathbi"
        if style is Style.BOLD:
            return "bold"
        if style is Style.ROMAN:
            return "main"
        return "math" if letter else "main"

    @staticmethod
    def char_class(ch: str) -> str:
        if ch in _BINARY:
            return "bin"
        if ch in _RELATION:
            return "rel"
        if ch == ",":
            return "punct"
        if ch in _OPEN:
            return "open"
        return "ord"

    def stretch_pairs(self, row: Row, pieces: list[Box | None], s: float) -> None:
        """Round brackets (and braces, brackets) round something tall grow with it."""
        stack: list[int] = []
        for i, node in enumerate(row):
            if isinstance(node, Template) or node not in "()[]{}":
                continue
            if node in _OPEN:
                stack.append(i)
            elif stack and row[stack[-1]] is not None and _CLOSE.get(str(row[stack[-1]])) == node:
                j = stack.pop()
                inner = [p for p in pieces[j + 1 : i] if p is not None]
                asc = max([p.asc for p in inner], default=0.0)
                desc = max([p.desc for p in inner], default=0.0)
                if asc > 0.95 * s or desc > 0.32 * s:
                    half = max(asc - AXIS * s, desc + AXIS * s, 0.5 * s)
                    pieces[j] = self.delim(str(row[j]), half, s)
                    pieces[i] = self.delim(str(node), half, s)

    def assemble(
        self,
        row: Row,
        path: Path,
        pieces: list[Box | None],
        classes: list[str],
        s: float,
        lvl: int,
    ) -> Box:
        out = Box()
        out.asc, out.desc = 0.75 * s, 0.25 * s
        gaps = [0.0]
        nodes: list[tuple[float, float, float, float]] = []
        medium, thick, thin = (0.0, 0.0, 0.0) if lvl else (0.22 * s, 0.28 * s, 0.17 * s)
        x = 0.0
        prev = "start"
        for i, piece in enumerate(pieces):
            assert piece is not None
            cls = classes[i]
            if cls == "bin" and (prev in ("start", "bin", "rel", "open", "punct") or i + 1 == len(row)):
                cls = "ord"  # a sign
            lead = medium if cls == "bin" else thick if cls == "rel" else 0.0
            trail = lead if cls in ("bin", "rel") else thin if cls == "punct" else 0.0
            if row[i] == " ":
                trail = 0.25 * s
            x += lead
            # merge a character into the previous run when it continues it exactly
            self.place(out, piece, x)
            nodes.append((x, x + piece.w, -piece.asc, piece.desc))
            x += piece.w
            gaps.append(x)
            x += trail
            prev = cls
            out.asc, out.desc = max(out.asc, piece.asc), max(out.desc, piece.desc)
        out.w = x
        # a stretched bracket makes the row's own extents the same as its content's
        out.rows.append(RowInfo(path, gaps, 0.0, x, -out.asc, out.desc, nodes))
        return _merge(out)

    @staticmethod
    def place(out: Box, piece: Box, x: float) -> None:
        out.add(piece, x, 0.0)

    # ---- templates --------------------------------------------------------------------------

    def slot(self, node: Template, path: Path, index: int, number: int, s: float, lvl: int) -> Box:
        return self.lay_row(node.slots[number], (*path, (index, number)), s, lvl)

    def template(self, node: Template, path: Path, index: int, s: float, lvl: int) -> Box:  # noqa: PLR0911
        def slot(n: int, size: float | None = None, add: int = 0) -> Box:
            return self.slot(node, path, index, n, size or s, lvl + add)

        k = node.kind
        if k is Kind.FRACTION:
            return self.fraction(slot(0, self.sub(s), 1), slot(1, self.sub(s), 1), s)
        if k is Kind.POWER:
            return self.power(slot(0, self.sub(s), 1), s)
        if k is Kind.ROOT:
            return self.root(slot(0), None, s)
        if k is Kind.NTH_ROOT:
            return self.root(slot(1), slot(0, s * 0.5, 2), s)
        if k is Kind.ABS:
            return self.fenced(slot(0), "|", "|", s)
        if k is Kind.MATRIX:
            cells = [slot(n) for n in range(len(node.slots))]
            return self.grid(cells, node.cols, s, left="[", right="]", centre=True, gap=1.0)
        if k in (Kind.PIECEWISE, Kind.SYSTEM):
            cells = [slot(n) for n in range(len(node.slots))]
            return self.grid(cells, node.cols, s, left="{", right=None, centre=False, gap=1.0)
        if k is Kind.LIST:
            return self.list_(node, path, index, s, lvl)
        if k is Kind.LOG:
            word = self.word("log", "main", s)
            base = slot(0, self.sub(s), 1)
            b = Box()
            b.add(word, 0, 0)
            b.add(base, word.w, 0.2 * s)
            b.w = word.w + base.w
            b.asc, b.desc = word.asc, max(word.desc, base.desc + 0.2 * s)
            arg = self.fenced(slot(1), "(", ")", s)
            return self.row_of([b, arg], s)
        if k in (Kind.DERIVATIVE, Kind.DERIVATIVE2, Kind.DERIVATIVE_N):
            return self.derivative(node, path, index, s, lvl)
        if k is Kind.DMS:
            return self.row_of(
                [slot(0), self.word("°", "main", s), slot(1), self.word("'", "main", s),
                 slot(2), self.word('"', "main", s)],
                s,
            )  # fmt: skip
        if k in (Kind.INTEGRAL, Kind.ANTIDERIVATIVE):
            return self.integral(node, path, index, s, lvl)
        if k in (Kind.SUM, Kind.PRODUCT):
            return self.big_operator(node, path, index, s, lvl)
        if k is Kind.LIMIT:
            return self.limit(node, path, index, s, lvl)
        return self.word("?", "main", s)

    def row_of(self, parts: list[Box], s: float, gap: float = 0.0) -> Box:
        b = Box(asc=0.75 * s, desc=0.25 * s)
        x = 0.0
        for p in parts:
            b.add(p, x, 0.0)
            x += p.w + gap
            b.asc, b.desc = max(b.asc, p.asc), max(b.desc, p.desc)
        b.w = x
        return _merge(b)

    def fraction(self, num: Box, den: Box, s: float) -> Box:
        t = self.rule_w(s)
        a = AXIS * s
        gap = 0.12 * s
        pad = 0.1 * s
        w = max(num.w, den.w) + 2 * pad
        up = a + t / 2 + gap + num.desc  # numerator baseline above the base baseline
        down = -a + t / 2 + gap + den.asc  # denominator baseline below it
        b = Box(w, up + num.asc, down + den.desc)
        b.add(num, (w - num.w) / 2, -up)
        b.add(den, (w - den.w) / 2, down)
        b.rule(pad * 0.5, -a - t / 2, w - pad, t)
        return b

    def power(self, exp: Box, s: float) -> Box:
        raise_by = 0.42 * s
        b = Box(exp.w + 0.04 * s, raise_by + exp.asc, max(0.0, exp.desc - raise_by))
        b.add(exp, 0.0, -raise_by)
        return b

    def root(self, rad: Box, index: Box | None, s: float) -> Box:
        t = self.rule_w(s)
        gap = 0.1 * s
        total = rad.asc + gap + t + rad.desc + 0.05 * s
        faces = ["main", "size1", "size2", "size3", "size4"]
        chosen = faces[0]
        for f in faces:
            chosen = f
            _a, ymax, ymin = glyph(f, "√")
            if (ymax - ymin) * s >= total * 0.97:
                break
        adv, ymax, ymin = glyph(chosen, "√")
        ink = (ymax - ymin) * s
        k = total / ink if total > ink else 1.0
        top = -(rad.asc + gap + t)
        y = top + ymax * s * k
        lead = 0.0
        b = Box()
        if index is not None:
            lead = max(0.0, index.w - 0.45 * adv * s)
        sign_x = lead
        b.items.append(("t", sign_x, y, "√", chosen, s, k))
        rx = sign_x + adv * s
        pad = 0.06 * s
        b.add(rad, rx + pad, 0.0)
        b.rule(rx - 0.5, top, rad.w + 2 * pad + 0.5, t)
        if index is not None:
            b.add(index, 0.0, top + 0.55 * total * 0.0 + 0.45 * total - index.desc)
        b.w = rx + rad.w + 2 * pad
        b.asc = rad.asc + gap + t + (index.asc * 0.0 if index else 0.0)
        b.desc = max(rad.desc + 0.05 * s, (y - ymin * s * k) - 0.0)
        b.desc = max(rad.desc, b.desc if b.desc < 3 * s else rad.desc)
        return _merge(b)

    def fenced(self, inner: Box, left: str, right: str, s: float) -> Box:
        half = max(inner.asc - AXIS * s, inner.desc + AXIS * s, 0.5 * s)
        pad = 0.06 * s
        b = Box()
        x = 0.0
        if left == "|":
            t = self.rule_w(s)
            b.rule(pad, -AXIS * s - half, t, 2 * half)
            x = t + 2 * pad
            b.add(inner, x, 0.0)
            x += inner.w + pad
            b.rule(x, -AXIS * s - half, t, 2 * half)
            b.w = x + t + pad
        else:
            tall = inner.asc > 0.95 * s or inner.desc > 0.32 * s
            lb = self.delim(left, half, s) if tall else self.text(left, "main", s)
            rb = self.delim(right, half, s) if tall else self.text(right, "main", s)
            b.add(lb, 0, 0)
            b.add(inner, lb.w, 0)
            b.add(rb, lb.w + inner.w, 0)
            b.w = lb.w + inner.w + rb.w
        b.asc, b.desc = max(inner.asc, half + AXIS * s), max(inner.desc, half - AXIS * s)
        return b

    def grid(
        self,
        cells: list[Box],
        cols: int,
        s: float,
        *,
        left: str | None,
        right: str | None,
        centre: bool,
        gap: float,
    ) -> Box:
        rows = [cells[i : i + cols] for i in range(0, len(cells), cols)]
        colw = [max(r[c].w for r in rows) for c in range(cols)]
        ra = [max([0.7 * s, *(c.asc for c in r)]) for r in rows]
        rd = [max([0.3 * s, *(c.desc for c in r)]) for r in rows]
        rgap = 0.15 * s
        height = sum(ra) + sum(rd) + rgap * (len(rows) - 1)
        top = -AXIS * s - height / 2
        inner = Box()
        y = top
        cgap = gap * s
        for r, row in enumerate(rows):
            y += ra[r]
            x = 0.0
            for c, cell in enumerate(row):
                dx = (colw[c] - cell.w) / 2 if centre else 0.0
                inner.add(cell, x + dx, y)
                x += colw[c] + cgap
            y += rd[r] + rgap
        inner.w = sum(colw) + cgap * (cols - 1)
        inner.asc, inner.desc = -top, top + height
        inner.desc = height / 2 + AXIS * s
        pad = 0.15 * s
        b = Box()
        x = 0.0
        half = height / 2
        t = self.rule_w(s)
        if left == "[":
            self.square(b, 0.0, half, s, True)
            x = 0.3 * s
        elif left == "{":
            lb = self.delim("{", half, s)
            b.add(lb, 0, 0)
            x = lb.w + 0.1 * s
        b.add(inner, x + pad * (left == "["), 0.0)
        x += inner.w + pad * (left == "[") * 2
        if right == "]":
            self.square(b, x, half, s, False)
            x += 0.3 * s
        b.w = x
        b.asc, b.desc = half + AXIS * s, half - AXIS * s
        _ = t
        return _merge(b)

    def square(self, b: Box, x: float, half: float, s: float, is_left: bool) -> None:
        t = self.rule_w(s)
        top = -AXIS * s - half
        hgt = 2 * half
        tick = 0.12 * s
        if is_left:
            b.rule(x + 0.1 * s, top, t, hgt)
            b.rule(x + 0.1 * s, top, tick, t)
            b.rule(x + 0.1 * s, top + hgt - t, tick, t)
        else:
            b.rule(x + 0.1 * s + tick - t, top, t, hgt)
            b.rule(x + 0.1 * s, top, tick, t)
            b.rule(x + 0.1 * s, top + hgt - t, tick, t)

    def list_(self, node: Template, path: Path, index: int, s: float, lvl: int) -> Box:
        parts: list[Box] = []
        for n in range(len(node.slots)):
            if n:
                parts.append(self.word(",", "main", s))
                parts.append(Box(0.17 * s))
            parts.append(self.slot(node, path, index, n, s, lvl))
        inner = self.row_of(parts, s)
        return self.fenced(inner, "{", "}", s)

    def derivative(self, node: Template, path: Path, index: int, s: float, lvl: int) -> Box:
        sm = s * 0.8
        k = node.kind

        def slot(n: int, size: float) -> Box:
            return self.slot(node, path, index, n, size, lvl + 1)

        two = self.sub(sm)
        if k is Kind.DERIVATIVE:
            var, expr = slot(0, sm), slot(1, s)
            top = self.word("d", "main", sm)
            bottom = self.row_of([self.word("d", "main", sm), var], sm)
        elif k is Kind.DERIVATIVE2:
            var, expr = slot(0, sm), slot(1, s)
            sup = self.power(self.word("2", "main", two), sm)
            top = self.row_of([self.word("d", "main", sm), sup], sm)
            bottom = self.row_of([self.word("d", "main", sm), var, sup], sm)
        else:
            order, var, expr = slot(0, two), slot(1, sm), slot(2, s)
            top = self.row_of([self.word("d", "main", sm), self.power(order, sm)], sm)
            bottom = self.row_of([self.word("d", "main", sm), var, self.power(order, sm)], sm)
            # the order slot is shown twice; only the first is a live row
            bottom.rows = [r for r in bottom.rows if r.path[-1:] != ((index, 0),)]
        frac = self.fraction(top, bottom, s)
        return self.row_of([frac, self.fenced(expr, "(", ")", s)], s)

    def operator(self, glyph_ch: str, face: str, s: float) -> Box:
        adv, ymax, ymin = glyph(face, glyph_ch)
        y = -AXIS * s + (ymax + ymin) / 2 * s
        b = Box(adv * s, (ymax + 0.0) * s + 0.0, -ymin * s)
        b.items.append(("t", 0.0, y, glyph_ch, face, s, 1.0))
        b.asc = AXIS * s + (ymax - ymin) / 2 * s
        b.desc = (ymax - ymin) / 2 * s - AXIS * s
        return b

    def integral(self, node: Template, path: Path, index: int, s: float, lvl: int) -> Box:
        sm = self.sub(s)
        sign = self.operator("∫", "main", s)
        parts = [sign]
        if node.kind is Kind.INTEGRAL:
            lower = self.slot(node, path, index, 0, sm, lvl + 1)
            upper = self.slot(node, path, index, 1, sm, lvl + 1)
            body = self.slot(node, path, index, 2, s, lvl)
            var = self.slot(node, path, index, 3, s, lvl)
            up_x, low_x = sign.w + 0.02 * s, 0.05 * s
            up_y = -(sign.asc - 0.1 * s)
            low_y = sign.desc + lower.asc - 0.15 * s
            box = Box(max(up_x + upper.w, low_x + lower.w), sign.asc, sign.desc)
            box.add(sign, 0, 0)
            box.add(upper, up_x, up_y)
            box.add(lower, low_x, low_y)
            box.asc = max(sign.asc, upper.asc - up_y)
            box.desc = max(sign.desc, lower.desc + low_y)
            parts = [box]
        else:
            body = self.slot(node, path, index, 0, s, lvl)
            var = self.slot(node, path, index, 1, s, lvl)
        parts += [Box(0.17 * s), body, Box(0.17 * s), self.word("d", "main", s), var]
        return self.row_of(parts, s)

    def big_operator(self, node: Template, path: Path, index: int, s: float, lvl: int) -> Box:
        sm = self.sub(s)
        ch = "∑" if node.kind is Kind.SUM else "∏"
        sign = self.operator(ch, "size1", s)
        var = self.slot(node, path, index, 0, sm, lvl + 1)
        lower = self.slot(node, path, index, 1, sm, lvl + 1)
        upper = self.slot(node, path, index, 2, sm, lvl + 1)
        body = self.slot(node, path, index, 3, s, lvl)
        below = self.row_of([var, self.word("=", "main", sm), lower], sm)
        w = max(sign.w, below.w, upper.w)
        b = Box(w)
        gap = 0.1 * s
        b.add(sign, (w - sign.w) / 2, 0)
        b.add(upper, (w - upper.w) / 2, -(sign.asc + gap + upper.desc))
        b.add(below, (w - below.w) / 2, sign.desc + gap + below.asc)
        b.asc = sign.asc + gap + upper.asc + upper.desc
        b.desc = sign.desc + gap + below.asc + below.desc
        return self.row_of([_merge(b), Box(0.17 * s), body], s)

    def limit(self, node: Template, path: Path, index: int, s: float, lvl: int) -> Box:
        sm = self.sub(s)
        var = self.slot(node, path, index, 0, sm, lvl + 1)
        point = self.slot(node, path, index, 1, sm, lvl + 1)
        direction = self.slot(node, path, index, 2, self.sub(sm), lvl + 2)
        body = self.slot(node, path, index, 3, s, lvl)
        lim = self.word("lim", "main", s)
        arrow = self.word("→", "main", sm)
        sup = self.power(direction, sm)
        below = self.row_of([var, arrow, point, sup], sm)
        w = max(lim.w, below.w)
        b = Box(w, lim.asc, lim.desc + 0.1 * s + below.asc + below.desc)
        b.add(lim, (w - lim.w) / 2, 0)
        b.add(below, (w - below.w) / 2, lim.desc + 0.1 * s + below.asc)
        return self.row_of([b, Box(0.17 * s), body], s)


def _merge(box: Box) -> Box:
    """Join text runs that continue each other (same face, size, baseline, touching)."""
    out: list[tuple] = []
    widths: dict[int, float] = {}
    for it in box.items:
        if it[0] == "t" and out and out[-1][0] == "t":
            p = out[-1]
            if p[4:] == it[4:] and abs(p[2] - it[2]) < 1e-6 and it[6] == 1.0:
                end = p[1] + widths[len(out) - 1]
                if abs(end - it[1]) < 1e-6:
                    out[-1] = (*p[:3], p[3] + it[3], *p[4:])
                    widths[len(out) - 1] += glyph(it[4], it[3])[0] * it[5]
                    continue
        if it[0] == "t":
            widths[len(out)] = sum(glyph(it[4], c)[0] for c in it[3]) * it[5]
        out.append(it)
    box.items = out
    return box


class Layout:
    """The finished layout: absolute items (top-left origin) and every row."""

    def __init__(self, root: Row, size: float = 20.0) -> None:
        self.size = size
        lay = Layouter(size)
        box = lay.lay_row(root, (), size, 0)
        dy = box.asc + 2.0
        self.width = box.w + 4.0
        self.height = box.asc + box.desc + 4.0
        pad = Box()
        pad.add(box, 2.0, dy)
        self.items = pad.items
        self.rows = {r.path: r for r in pad.rows}

    def caret(self, path: Path | list, pos: int) -> tuple[float, float, float]:
        r = self.rows[tuple(path)]
        return r.gaps[min(pos, len(r.gaps) - 1)], r.top, r.bot

    def selection_rects(
        self, path: Path | list, low: int, high: int
    ) -> list[tuple[float, float, float, float]]:
        """(x, top, w, h) of the selected nodes: one rectangle from gap `low` to gap `high`, as
        tall as the nodes in it."""
        if low == high:
            return []
        r = self.rows[tuple(path)]
        tops = [n[2] for n in r.nodes[low:high]] or [r.top]
        bots = [n[3] for n in r.nodes[low:high]] or [r.bot]
        top, bot = min([r.top, *tops]), max([r.bot, *bots])
        x0, x1 = r.gaps[low], r.gaps[high]
        return [(x0, top, x1 - x0, bot - top)]

    def hit(self, x: float, y: float) -> tuple[Path, int]:
        """The innermost row under the point (nearest row if none) and its nearest gap."""
        best: tuple[tuple[int, float], RowInfo] | None = None
        for r in self.rows.values():
            dx = max(r.x0 - x, 0.0, x - r.x1)
            dy = max(r.top - y, 0.0, y - r.bot)
            inside = dx == 0.0 and dy == 0.0
            key = (0 if inside else 1, -len(r.path) if inside else dx * dx + dy * dy, 0)
            cand = (key[0], key[1] if inside else key[1] - len(r.path) * 1e-6)
            if best is None or cand < best[0]:
                best = (cand, r)
        assert best is not None
        r = best[1]
        pos = min(range(len(r.gaps)), key=lambda i: abs(r.gaps[i] - x))
        return r.path, pos
