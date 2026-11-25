"""The input line: tokens and templates with a cursor (FR-FX-DSP-003, FR-FX-DSP-004).

An entry is a sequence of items. A `Tok` is one key's worth of input (`7`, `sin(`, `Ans`); a `Tmpl`
is a natural-display template with slots (a fraction has a numerator and a denominator). The cursor
is a path of (item, slot) steps from the top sequence plus a position in the innermost sequence,
so it can sit in any slot of any nested template. The parser reads the same tree (`parser.py`).
Pure Python: no Flet.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from cassim.devices.scientific.layout import (
    Abs,
    Box,
    Cursor,
    Frac,
    Node,
    Root,
    Seq,
    Sqrt,
    Sub,
    Sup,
    Text,
)

MAX_ITEMS = 99  # the most input items one entry holds

TokKind = Literal[
    "digit", "dot", "op", "neg", "lparen", "rparen", "comma", "func", "const", "var",
    "statvar", "estimator", "postfix", "rel", "store",
]  # fmt: skip


@dataclass(frozen=True)
class Token:
    kind: TokKind
    text: str  # what the LCD shows
    sup: str = ""  # shown raised in natural display (x², x⁻¹)


def _tokens() -> dict[str, Token]:
    table: dict[str, Token] = {digit: Token("digit", digit) for digit in "0123456789"}
    table["."] = Token("dot", ".")
    for op, text in (("+", "+"), ("−", "−"), ("×", "×"), ("÷", "÷"), ("nPr", "P"), ("nCr", "C")):
        table[op] = Token("op", text)
    table["neg"] = Token("neg", "-")
    table["("] = Token("lparen", "(")
    table[")"] = Token("rparen", ")")
    table[","] = Token("comma", ",")
    for name in (
        "sin", "cos", "tan", "sin⁻¹", "cos⁻¹", "tan⁻¹", "sinh", "cosh", "tanh", "sinh⁻¹",
        "cosh⁻¹", "tanh⁻¹", "log", "ln", "Pol", "Rec", "GCD", "LCM", "Rnd", "RanInt#",
    ):  # fmt: skip
        table[f"{name}("] = Token("func", f"{name}(")
    for name, text in (("π", "π"), ("e", "e"), ("Ran#", "Ran#"), ("ten", "10")):
        table[name] = Token("const", text)
    for name in ("A", "B", "C", "D", "E", "F", "M", "X", "Y", "Ans", "PreAns"):
        table[name] = Token("var", name)
    for name in (
        "n", "x̄", "σx", "sx", "ȳ", "σy", "sy", "Σx", "Σx²", "Σy", "Σy²", "Σxy", "minX", "maxX",
        "minY", "maxY", "Q1", "med", "Q3", "r",
    ):  # fmt: skip
        table[name] = Token("statvar", name)
    for name, text in (("regA", "A"), ("regB", "B"), ("regC", "C")):
        table[name] = Token("statvar", text)
    for name, text in (("x̂", "x̂"), ("ŷ", "ŷ"), ("x̂1", "x̂₁"), ("x̂2", "x̂₂")):
        table[name] = Token("estimator", text)
    table["²"] = Token("postfix", "²", sup="2")
    table["³"] = Token("postfix", "³", sup="3")
    table["⁻¹"] = Token("postfix", "⁻¹", sup="−1")
    table["!"] = Token("postfix", "!")
    table["%"] = Token("postfix", "%")
    table["dms"] = Token("postfix", "°")
    table["deg"] = Token("postfix", "°")
    table["rad"] = Token("postfix", "ʳ")
    table["gra"] = Token("postfix", "ᵍ")
    for rel in ("=", "≠", ">", "≥", "<", "≤"):
        table[rel] = Token("rel", rel)
    table["→"] = Token("store", "→")  # shown after STO (Ans→A); not something to calculate
    return table


TOKENS: dict[str, Token] = _tokens()

TmplKind = Literal["frac", "mixed", "sqrt", "root", "pow", "exp10", "abs", "logab"]
SLOTS: dict[str, int] = {
    "frac": 2,
    "mixed": 3,
    "sqrt": 1,
    "root": 2,
    "pow": 1,
    "exp10": 1,
    "abs": 1,
    "logab": 2,
}


@dataclass
class Tok:
    id: str

    @property
    def token(self) -> Token:
        return TOKENS[self.id]


@dataclass
class Tmpl:
    kind: TmplKind
    slots: list[list[Item]] = field(default_factory=list)

    def __post_init__(self) -> None:
        while len(self.slots) < SLOTS[self.kind]:
            self.slots.append([])


type Item = Tok | Tmpl


def count(items: list[Item]) -> int:
    total = 0
    for item in items:
        total += 1
        if isinstance(item, Tmpl):
            total += sum(count(slot) for slot in item.slots)
    return total


def toks(*ids: str) -> list[Item]:
    return [Tok(i) for i in ids]


class Editor:
    """An entry and its cursor."""

    def __init__(self, items: list[Item] | None = None) -> None:
        self.items: list[Item] = items if items is not None else []
        self.path: list[tuple[int, int]] = []  # (item index, slot index) steps into templates
        self.pos = len(self.items)

    # ---- where the cursor is ----------------------------------------------------------------

    def _seq_at(self, path: list[tuple[int, int]]) -> list[Item]:
        seq = self.items
        for index, slot in path:
            item = seq[index]
            assert isinstance(item, Tmpl)
            seq = item.slots[slot]
        return seq

    @property
    def seq(self) -> list[Item]:
        return self._seq_at(self.path)

    def is_empty(self) -> bool:
        return not self.items

    def copy(self) -> Editor:
        other = Editor(copy.deepcopy(self.items))
        other.path = list(self.path)
        other.pos = self.pos
        return other

    def clear(self) -> None:
        self.items = []
        self.path = []
        self.pos = 0

    def home(self) -> None:
        self.path = []
        self.pos = 0

    def end(self) -> None:
        self.path = []
        self.pos = len(self.items)

    # ---- typing -----------------------------------------------------------------------------

    def _room(self, n: int) -> bool:
        return count(self.items) + n <= MAX_ITEMS

    def insert(self, *ids: str) -> bool:
        """Type tokens at the cursor. False when the entry is full."""
        if not self._room(len(ids)):
            return False
        seq = self.seq
        for token_id in ids:
            seq.insert(self.pos, Tok(token_id))
            self.pos += 1
        return True

    def template(
        self,
        kind: TmplKind,
        filled: tuple[tuple[str, ...], ...] = (),
        slot: int = 0,
        *,
        absorb: bool = False,
    ) -> bool:
        """Insert a template, its leading slots pre-filled with tokens, and put the cursor at the
        end of `slot`. With `absorb`, a number just before the cursor becomes the first slot (typing
        2 then the fraction key makes 2 the numerator)."""
        if not self._room(1 + sum(len(f) for f in filled)):
            return False
        seq = self.seq
        new = Tmpl(kind)
        for index, ids in enumerate(filled):
            new.slots[index] = [Tok(i) for i in ids]
        if absorb:
            start = self.pos
            while start > 0 and isinstance(seq[start - 1], Tok):
                previous = seq[start - 1]
                assert isinstance(previous, Tok)
                if previous.token.kind not in ("digit", "dot"):
                    break
                start -= 1
            if start < self.pos:
                new.slots[0] = seq[start : self.pos]
                del seq[start : self.pos]
                self.pos = start
                slot = max(slot, 1)
        seq.insert(self.pos, new)
        self.path = [*self.path, (self.pos, slot)]
        self.pos = len(new.slots[slot])
        return True

    # ---- moving -----------------------------------------------------------------------------

    def _parent(self) -> tuple[list[tuple[int, int]], int, int]:
        """The path to the sequence holding the current template, its index there, and the slot."""
        index, slot = self.path[-1]
        return self.path[:-1], index, slot

    def left(self) -> None:
        if self.pos > 0:
            item = self.seq[self.pos - 1]
            if isinstance(item, Tmpl):
                last = len(item.slots) - 1
                self.path = [*self.path, (self.pos - 1, last)]
                self.pos = len(item.slots[last])
            else:
                self.pos -= 1
            return
        if not self.path:
            return
        parent, index, slot = self._parent()
        if slot > 0:
            self.path = [*parent, (index, slot - 1)]
            self.pos = len(self.seq)
        else:
            self.path = parent
            self.pos = index

    def right(self) -> None:
        seq = self.seq
        if self.pos < len(seq):
            item = seq[self.pos]
            if isinstance(item, Tmpl):
                self.path = [*self.path, (self.pos, 0)]
                self.pos = 0
            else:
                self.pos += 1
            return
        if not self.path:
            return
        parent, index, slot = self._parent()
        template = self._seq_at(parent)[index]
        assert isinstance(template, Tmpl)
        if slot < len(template.slots) - 1:
            self.path = [*parent, (index, slot + 1)]
            self.pos = 0
        else:
            self.path = parent
            self.pos = index + 1

    def vertical(self, step: int) -> bool:
        """Move between a fraction's numerator and denominator (step -1 up, +1 down). False when
        the cursor is not in a fraction, so ▲ ▼ can recall history instead."""
        for depth in range(len(self.path) - 1, -1, -1):
            index, slot = self.path[depth]
            template = self._seq_at(self.path[:depth])[index]
            assert isinstance(template, Tmpl)
            first = {"frac": 0, "mixed": 1}.get(template.kind)
            if first is None:
                continue
            target = slot + step
            if template.kind == "mixed" and slot == 0:
                target = 1 if step > 0 else -1
            if first <= target <= first + 1:
                self.path = [*self.path[:depth], (index, target)]
                self.pos = len(self.seq)
                return True
        return False

    def delete(self) -> None:
        """DEL: remove the item before the cursor. An empty template is removed; a filled one is
        entered so its contents can be deleted first."""
        seq = self.seq
        if self.pos > 0:
            item = seq[self.pos - 1]
            if isinstance(item, Tmpl) and any(item.slots):
                self.left()
                return
            del seq[self.pos - 1]
            self.pos -= 1
            return
        if not self.path:
            return
        parent, index, _ = self._parent()
        template = self._seq_at(parent)[index]
        assert isinstance(template, Tmpl)
        if not any(template.slots):
            del self._seq_at(parent)[index]
            self.path = parent
            self.pos = index
        else:
            self.left()

    # ---- drawing ----------------------------------------------------------------------------

    def layout(self, *, natural: bool = True, cursor: bool = True) -> Seq:
        return _layout(self.items, [], self.path if cursor else None, self.pos, natural=natural)


def _layout(
    items: list[Item],
    here: list[tuple[int, int]],
    path: list[tuple[int, int]] | None,
    pos: int,
    *,
    natural: bool,
) -> Seq:
    nodes: list[Node] = []
    at_cursor = path is not None and path == here

    def slot(item_index: int, slot_index: int) -> Seq:
        template = items[item_index]
        assert isinstance(template, Tmpl)
        inner = _layout(
            template.slots[slot_index],
            [*here, (item_index, slot_index)],
            path,
            pos,
            natural=natural,
        )
        if natural and not inner:
            return (Box(),)
        if natural and inner == (Cursor(),):
            return (Cursor(), Box())
        return inner

    for index, item in enumerate(items):
        if at_cursor and index == pos:
            nodes.append(Cursor())
        if isinstance(item, Tok):
            token = item.token
            if natural and token.sup:
                nodes.append(Sup((Text(token.sup),)))
            else:
                nodes.append(Text(token.text))
            continue
        nodes.extend(_template(item.kind, index, slot, natural=natural))
    if at_cursor and pos == len(items):
        nodes.append(Cursor())
    return tuple(nodes)


def _template(  # noqa: PLR0911, PLR0912
    kind: TmplKind, index: int, get: Callable[[int, int], Seq], *, natural: bool
) -> list[Node]:
    """The nodes of a template; `get(item, slot)` draws one slot."""
    if natural:
        match kind:
            case "frac":
                return [Frac(get(index, 0), get(index, 1))]
            case "mixed":
                return [*get(index, 0), Frac(get(index, 1), get(index, 2))]
            case "sqrt":
                return [Sqrt(get(index, 0))]
            case "root":
                return [Root(get(index, 0), get(index, 1))]
            case "pow":
                return [Sup(get(index, 0))]
            case "exp10":
                return [Text("×10"), Sup(get(index, 0))]
            case "abs":
                return [Abs(get(index, 0))]
            case "logab":
                return [Text("log"), Sub(get(index, 0)), Text("("), *get(index, 1), Text(")")]
    match kind:
        case "frac":
            return [*get(index, 0), Text("⌟"), *get(index, 1)]
        case "mixed":
            return [*get(index, 0), Text("⌟"), *get(index, 1), Text("⌟"), *get(index, 2)]
        case "sqrt":
            return [Text("√("), *get(index, 0), Text(")")]
        case "root":
            return [Text("("), *get(index, 0), Text(")ˣ√("), *get(index, 1), Text(")")]
        case "pow":
            return [Text("^("), *get(index, 0), Text(")")]
        case "exp10":
            return [Text("ᴇ"), *get(index, 0)]
        case "abs":
            return [Text("Abs("), *get(index, 0), Text(")")]
        case "logab":
            return [Text("log("), *get(index, 0), Text(","), *get(index, 1), Text(")")]
    return []
