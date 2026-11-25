"""The CASSim Scientific device: what each key does and what the screen shows (SDD-14 3, 6).

`ScientificState.press(key)` takes the key ids of `keys.py`; `display()` describes the LCD for the
view (and as text for the tests and the tutorials). The state also reads and writes its part of a
`.cassim.json` file and of a share link (decision 0032 item 4: both name the device).

Pure Python: no Flet.
"""

from __future__ import annotations

import base64
import copy
import json
import math
import random
import zlib
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Literal, cast

from cassim.devices.scientific import display as fmt
from cassim.devices.scientific import keys as k
from cassim.devices.scientific import values as v
from cassim.devices.scientific.display import Setup
from cassim.devices.scientific.editor import (
    MAX_ITEMS,
    SLOTS,
    TOKENS,
    Editor,
    Item,
    Tmpl,
    TmplKind,
    Tok,
    count,
)
from cassim.devices.scientific.engine import (
    STAT_TYPE_LABELS,
    STAT_TYPES,
    OneVar,
    Regression,
    StatType,
    TwoVar,
    factor_layout,
    one_var,
    regression,
    two_var,
)
from cassim.devices.scientific.layout import Seq, to_text
from cassim.devices.scientific.parser import Context, Pair, Value, evaluate, number
from cassim.devices.scientific.values import CalcError, Exact, Number

DEVICE_ID = "scientific"
FORMAT = "cassim-document"  # the same envelope as every CASSim file (doc/serialize.py)
SCHEMA = 5
SHARE_PREFIX = "doc="  # a share link is the same for every device; its JSON names the device
MAX_FRAGMENT = 2000
MAX_JSON = 200_000
MAX_HISTORY = 30
MAX_STAT_ROWS = 40
MAX_TABLE_ROWS = 30
GRID_ROWS = 3  # data rows the LCD shows at once
MAX_DEPTH = 12

CalcMode = Literal["COMP", "STAT", "TABLE", "VERIFY"]
MODES: tuple[CalcMode, ...] = ("COMP", "STAT", "TABLE", "VERIFY")
ScreenKind = Literal[
    "calc", "menu", "error", "message", "stat_editor", "table_fx", "table_prompt", "table", "off"
]  # fmt: skip
Form = Literal["auto", "decimal", "exact", "dms", "eng", "fact"]
VARIABLES = ("A", "B", "C", "D", "E", "F", "M", "X", "Y")


class DocumentFileError(ValueError):
    """The text is not a CASSim Scientific document this version can open."""


# ---- what the LCD shows ---------------------------------------------------------------------


@dataclass(frozen=True)
class Grid:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    first_row: int  # the row number (from 1) of rows[0]
    cursor: tuple[int, int] | None  # (index into rows, column)


@dataclass(frozen=True)
class Display:
    kind: Literal["calc", "menu", "grid", "message", "off"]
    title: str = ""
    input: Seq = ()
    result: Seq = ()
    error: str = ""
    options: tuple[str, ...] = ()
    grid: Grid | None = None
    footer: str = ""

    def text(self) -> str:
        """The screen on plain lines (cursor left out)."""
        lines: list[str] = []
        if self.title:
            lines.append(self.title)
        if self.kind == "menu":
            lines.extend(self.options)
        if self.grid is not None:
            lines.append(" ".join(self.grid.headers))
            for index, row in enumerate(self.grid.rows):
                lines.append(f"{self.grid.first_row + index} " + " ".join(row))
        entry = to_text(self.input)
        if entry:
            lines.append(entry)
        if self.error:
            lines.append(self.error)
        answer = to_text(self.result)
        if answer:
            lines.append(answer)
        if self.footer:
            lines.append(self.footer)
        return "\n".join(lines)


@dataclass
class MenuSpec:
    title: str
    options: tuple[str, ...]
    pick: Callable[[int], None]  # called with the chosen number (1-based)
    numbers: str = ""  # keys that choose, when not 1..len(options) (Fix 0~9)
    up: str = ""  # the menu ▲ shows, if any
    down: str = ""


@dataclass
class HistoryEntry:
    items: list[Item]
    value: Value


@dataclass
class ScientificState:
    """Everything the calculator holds."""

    setup: Setup = field(default_factory=Setup)
    mode: CalcMode = "COMP"
    stat_type: StatType = "1-VAR"
    variables: dict[str, Number] = field(
        default_factory=lambda: {name: v.ZERO for name in (*VARIABLES, "Ans", "PreAns")}
    )
    editor: Editor = field(default_factory=Editor)
    result: Value | None = None
    form: Form = "auto"
    mixed: bool | None = None
    eng: int | None = None
    error: str = ""
    showing_result: bool = False
    history: list[HistoryEntry] = field(default_factory=list)
    history_index: int = 0
    shift: bool = False
    alpha: bool = False
    hyp: bool = False
    sto: bool = False
    rcl: bool = False
    screen: ScreenKind = "calc"
    menu: str = ""
    back: ScreenKind = "calc"  # where AC returns from a menu
    message: tuple[str, str] = ("", "")
    pending: str = ""  # CLR choice awaiting =
    stat_rows: list[list[Number | None]] = field(default_factory=list)
    stat_cursor: tuple[int, int] = (0, 0)
    stat_top: int = 0
    stat_entry: Editor = field(default_factory=Editor)
    table_function: Editor = field(default_factory=Editor)
    table_range: list[Number] = field(
        default_factory=lambda: [v.rational(1), v.rational(5), v.rational(1)]
    )
    table_prompt: int = 0
    table_entry: Editor = field(default_factory=Editor)
    table_rows: list[tuple[Number, Value | str]] = field(default_factory=list)
    table_cursor: tuple[int, int] = (0, 0)
    table_top: int = 0
    fact: Seq = ()
    rng: random.Random = field(default_factory=random.Random)
    allowed_modes: tuple[CalcMode, ...] = MODES  # the modes the chosen keypad layout has
    linear_layout: bool = False  # the layout's calculator has a linear display
    note: str = ""  # a line above the entry (DATA SET)

    # ------------------------------------------------------------------------------------------
    # keys
    # ------------------------------------------------------------------------------------------

    def press(self, key: str) -> None:  # noqa: PLR0912
        """One keypad key (or a keyboard key that stands for one)."""
        if self.screen == "off":
            if key == k.ON:
                self.screen = "calc"
                self._clear_entry()
            return
        if key == k.SHIFT:
            self.shift, self.alpha = not self.shift, False
            return
        if key == k.ALPHA:
            self.alpha, self.shift = not self.alpha, False
            return
        shift, alpha = self.shift, self.alpha
        self.shift = self.alpha = False
        if self._global(key, shift=shift):
            return
        if self._pseudo(key):
            return
        match self.screen:
            case "menu":
                self._menu_key(key)
            case "message":
                if key in (k.AC, k.ON):
                    self._to_calc()
                elif key == k.EQ and self.pending:
                    self._do_clear(self.pending)
            case "error":
                self._error_key(key)
            case "stat_editor":
                self._stat_key(key, shift=shift, alpha=alpha)
            case "table_fx":
                self._table_fx_key(key, shift=shift, alpha=alpha)
            case "table_prompt":
                self._table_prompt_key(key, shift=shift, alpha=alpha)
            case "table":
                self._table_key(key)
            case _:
                self._calc_key(key, shift=shift, alpha=alpha)

    def _global(self, key: str, *, shift: bool) -> bool:
        """Keys that work on any screen."""
        if key == k.AC and shift:
            self.screen = "off"
            return True
        if key == k.ON:
            self.hyp = self.sto = self.rcl = False
            self._to_calc()
            return True
        if key == k.MODE:
            self.hyp = self.sto = self.rcl = False
            self.open_menu("setup1" if shift else "mode")
            return True
        if shift and key == "9" and self.screen not in ("menu", "message"):
            self.open_menu("clr")
            return True
        if shift and key == "1" and self.mode == "STAT" and self.screen != "menu":
            self.open_menu("stat")
            return True
        return False

    # ---- the calculation screen ----

    def _calc_key(self, key: str, *, shift: bool, alpha: bool) -> None:  # noqa: PLR0911, PLR0912, PLR0915
        if self.sto or self.rcl:
            storing = self.sto
            self.sto = self.rcl = False
            name = k.VARIABLE_KEYS.get(key)
            if name is not None:
                self._store(name) if storing else self._recall(name)
                return
        if key == k.EQ:
            self.execute()
            return
        if key == k.AC:
            self._clear_entry()
            return
        if key == k.RCL:
            if shift:
                self.sto = True
            else:
                self.rcl = True
            return
        if key == k.DEL:
            if self.showing_result:
                self._resume(at_end=True)
            elif not shift:
                self.editor.delete()
            return
        if key in (k.LEFT, k.RIGHT):
            editor = self.editor
            at_start = not editor.path and editor.pos == 0
            at_end = not editor.path and editor.pos == len(editor.items)
            if self.showing_result:
                self._resume(at_end=key == k.LEFT)
            elif key == k.LEFT:
                editor.end() if at_start else editor.left()  # the cursor wraps round
            else:
                editor.home() if at_end else editor.right()
            return
        if key in (k.UP, k.DOWN):
            step = -1 if key == k.UP else 1
            if self.showing_result or self.editor.is_empty():
                self._replay(step)
            else:
                self.editor.vertical(step)
            return
        if key == k.HOME:
            self.editor.home()
            return
        if key == k.END:
            self.editor.end()
            return
        if key == k.SD:
            if alpha:
                self._type(key, shift=False, alpha=True)
                return
            self._answer_then(lambda: self._toggle_sd(mixed=shift))
            return
        if key == k.ENG:
            self._answer_then(lambda: self._engineering(up=shift))
            return
        if key == k.DMS and not alpha:
            if shift:
                self._answer_then(self._factorise)
            elif self.showing_result:
                self.form = "auto" if self.form == "dms" else "dms"
            else:
                self.editor.insert("dms")
            return
        if key == k.MPLUS and not alpha:
            self._memory(minus=shift)
            return
        if key == k.ANS and shift:
            self.open_menu("drg")
            return
        if key == "6" and shift:
            self.open_menu("rel")
            return
        if key == k.HYP and not alpha:
            self.hyp = True
            return
        self._type(key, shift=shift, alpha=alpha)

    def _type(self, key: str, *, shift: bool, alpha: bool) -> None:
        action = key_action(key, shift=shift, alpha=alpha, hyp=self.hyp)
        self.hyp = False
        if action is None:
            return
        self.note = ""
        if self.showing_result:
            continuing = action_continues(action)
            self.editor = Editor()
            if continuing:
                self.editor.insert("Ans")
            self.showing_result = False
        self.result = None
        apply_action(self.editor, action)

    def _answer_then(self, then: Callable[[], None]) -> None:
        if not self.showing_result:
            if self.editor.is_empty():
                return
            self.execute()
            if not self.showing_result:
                return
        then()

    def execute(self) -> None:
        """= : evaluate the entry."""
        if self.editor.is_empty():
            return
        try:
            value = evaluate(self.editor.items, self.context())
            if not isinstance(value, (Pair, bool)) and math.isnan(float(number(value))):
                raise v.math_error()
        except CalcError as error:
            self.error = error.message
            self.screen = "error"
            return
        if isinstance(value, Pair):
            self.variables["X"], self.variables["Y"] = value.first, value.second
            self._set_ans(value.first)
        elif not isinstance(value, bool):
            self._set_ans(number(value))
        self.history.append(HistoryEntry(copy.deepcopy(self.editor.items), value))
        del self.history[:-MAX_HISTORY]
        self.history_index = len(self.history) - 1
        self._show(value)

    def _set_ans(self, value: Number) -> None:
        self.variables["PreAns"] = self.variables["Ans"]
        self.variables["Ans"] = value

    def _show(self, value: Value) -> None:
        self.result = value
        self.form = "auto"
        self.mixed = None
        self.eng = None
        self.showing_result = True
        self.error = ""
        self.screen = "calc"

    def _resume(self, *, at_end: bool) -> None:
        """◀ ▶ after an answer: edit the entry again."""
        self.showing_result = False
        self.result = None
        if at_end:
            self.editor.end()
        else:
            self.editor.home()

    def _replay(self, step: int) -> None:
        """▲ ▼: show an earlier calculation and its answer (FR-FX-DSP-004)."""
        if not self.history:
            return
        if self.showing_result:
            index = self.history_index + step
        elif self.editor.is_empty() and step < 0:
            index = len(self.history) - 1
        else:
            return
        if not 0 <= index < len(self.history):
            return
        self.history_index = index
        entry = self.history[index]
        self.editor = Editor(copy.deepcopy(entry.items))
        self._show(entry.value)

    def _clear_entry(self) -> None:
        self.editor = Editor()
        self.result = None
        self.showing_result = False
        self.error = ""
        self.hyp = self.sto = self.rcl = False
        self.history_index = len(self.history) - 1
        if self.screen != "off":
            self.screen = "calc" if self.mode != "TABLE" else "table_fx"
        if self.mode == "TABLE":
            self.editor = self.table_function

    def _to_calc(self) -> None:
        self.pending = ""
        self.screen = "calc"
        self._clear_entry()

    def _toggle_sd(self, *, mixed: bool) -> None:
        if self.result is None or isinstance(self.result, (bool, Pair)):
            return
        if mixed:
            current = self.setup.fraction == "ab/c" if self.mixed is None else self.mixed
            self.mixed = not current
            if self.form == "decimal":
                self.form = "exact"
            return
        value = number(self.result)
        shown_exact = self._shows_exact()
        self.form = "decimal" if shown_exact else "exact"
        if self.form == "exact" and fmt.exact(value, self.setup, mixed=False) is None:
            self.form = "decimal"
        self.eng = None

    def _shows_exact(self) -> bool:
        if self.result is None or isinstance(self.result, (bool, Pair)):
            return False
        value = number(self.result)
        if self.form == "exact":
            return True
        if self.form != "auto":
            return False
        return (
            isinstance(value, Exact)
            and self._prefer_exact()
            and (fmt.exact(value, self.setup, mixed=False) is not None)
        )

    def _prefer_exact(self) -> bool:
        """Natural display shows exact answers, except for an angle typed in ° ' "; LineIO shows a
        fraction only when the entry has one."""
        items = self.editor.items
        if any(isinstance(item, Tok) and item.id == "dms" for item in items):
            return False
        if self.setup.input == "math":
            return True
        return any(isinstance(item, Tmpl) and item.kind in ("frac", "mixed") for item in items)

    def _engineering(self, *, up: bool) -> None:
        if self.result is None or isinstance(self.result, (bool, Pair)):
            return
        x = float(number(self.result))
        if self.form != "eng" or self.eng is None:
            self.eng = fmt.engineering_exponent(x)
            if up:
                self.eng += 3
        else:
            self.eng += 3 if up else -3
        self.form = "eng"

    def _factorise(self) -> None:
        if self.result is None or isinstance(self.result, (bool, Pair)):
            return
        n = v.as_integer(number(self.result))
        try:
            if n is None:
                raise v.math_error()
            self.fact = factor_layout(n)
        except CalcError as error:
            self.error = error.message
            self.screen = "error"
            return
        self.form = "fact"

    def _memory(self, *, minus: bool) -> None:
        """M+ and M−: add the answer (calculating the entry first) to M (FR-FX-MEM-003)."""
        if not self.showing_result:
            if self.editor.is_empty():
                value = self.variables["Ans"]
            else:
                self.execute()
                if not self.showing_result:
                    return
                value = self.variables["Ans"]
        else:
            value = self.variables["Ans"]
        try:
            self.variables["M"] = (v.sub if minus else v.add)(self.variables["M"], value)
        except CalcError as error:
            self.error = error.message
            self.screen = "error"

    def _store(self, name: str) -> None:
        """STO then a variable key: the answer (calculating the entry first) goes into it."""
        if not self.showing_result and not self.editor.is_empty():
            self.execute()
            if not self.showing_result:
                return
        value = self.variables["Ans"]
        self.variables[name] = value
        self.editor = Editor([Tok("Ans"), Tok("→"), Tok(name)])
        self._show(value)

    def _recall(self, name: str) -> None:
        self.editor = Editor([Tok(name)])
        self.execute()

    def _error_key(self, key: str) -> None:
        if key == k.AC:
            self.error = ""
            self._back_from_error()
            if self.screen == "calc":
                self._clear_entry()
        elif key in (k.LEFT, k.RIGHT, k.DEL):
            self.error = ""
            self._back_from_error()

    def _back_from_error(self) -> None:
        self.screen = self.back if self.back in ("stat_editor", "table_prompt") else "calc"
        self.back = "calc"
        if self.screen == "calc" and self.mode == "TABLE":
            self.screen = "table_fx"
        self.showing_result = False

    def context(self, *, statistics: bool = True) -> Context:
        stats_on = statistics and self.mode == "STAT"
        return Context(
            angle=self.setup.angle,
            variables=self.variables,
            stat=self.stat_value if stats_on else None,
            estimate=self.estimate if stats_on and self.stat_type != "1-VAR" else None,
            rnd=lambda value: fmt.rnd(value, self.setup),
            rng=self.rng,
            relations=self.mode == "VERIFY",
        )

    # ---- menus ----

    def open_menu(self, name: str) -> None:
        if self.screen not in ("menu", "error"):
            self.back = self.screen
        self.menu = name
        self.screen = "menu"

    def menu_spec(self) -> MenuSpec:  # noqa: PLR0911, PLR0912
        name = self.menu
        match name:
            case "mode":
                options = tuple(f"{i}:{m}" for i, m in enumerate(self.allowed_modes, start=1))
                return MenuSpec("", options, self._pick_mode)
            case "stat_type":
                options = tuple(
                    f"{i}:{STAT_TYPE_LABELS[t]}" for i, t in enumerate(STAT_TYPES, start=1)
                )
                return MenuSpec("", options, self._pick_stat_type)
            case "setup1":
                return MenuSpec(
                    "",
                    ("1:MthIO", "2:LineIO", "3:Deg", "4:Rad", "5:Gra", "6:Fix", "7:Sci", "8:Norm"),
                    self._pick_setup1,
                    down="setup2",
                )
            case "setup2":
                return MenuSpec("", ("1:STAT", "2:ab/c", "3:d/c"), self._pick_setup2, up="setup1")
            case "setup_io":
                return MenuSpec("MthIO", ("1:MathO", "2:LineO"), self._pick_io)
            case "fix":
                return MenuSpec("Fix 0~9?", (), self._pick_digits("Fix"), numbers="0123456789")
            case "sci":
                return MenuSpec("Sci 0~9?", (), self._pick_digits("Sci"), numbers="0123456789")
            case "norm":
                return MenuSpec("Norm 1~2?", (), self._pick_digits("Norm"), numbers="12")
            case "freq":
                return MenuSpec("Frequency?", ("1:ON", "2:OFF"), self._pick_frequency)
            case "clr":
                return MenuSpec("CLR", ("1:Setup", "2:Memory", "3:All"), self._pick_clear)
            case "drg":
                return MenuSpec("", ("1:°", "2:ʳ", "3:ᵍ"), self._insert_from(("deg", "rad", "gra")))
            case "rel":
                return MenuSpec(
                    "",
                    ("1:=", "2:≠", "3:>", "4:≥", "5:<", "6:≤"),
                    self._insert_from(("=", "≠", ">", "≥", "<", "≤")),
                )
            case "stat":
                options = ["1:Type", "2:Data", "3:Sum", "4:Var", "5:MinMax"]
                if self.stat_type != "1-VAR":
                    options.append("6:Reg")
                return MenuSpec("", tuple(options), self._pick_stat)
        tokens = self._stat_menu_tokens(name)
        labels = tuple(f"{i}:{TOKENS[t].text}" for i, t in enumerate(tokens, start=1))
        return MenuSpec("", labels, self._insert_from(tokens))

    def _stat_menu_tokens(self, name: str) -> tuple[str, ...]:  # noqa: PLR0911
        two = self.stat_type != "1-VAR"
        match name:
            case "stat_sum":
                return ("Σx²", "Σx", "Σy²", "Σy", "Σxy") if two else ("Σx²", "Σx")
            case "stat_var":
                return ("n", "x̄", "σx", "sx", "ȳ", "σy", "sy") if two else ("n", "x̄", "σx", "sx")
            case "stat_minmax":
                if two:
                    return ("minX", "maxX", "minY", "maxY")
                return ("minX", "maxX", "Q1", "med", "Q3")
            case "stat_reg":
                if self.stat_type == "_+CX2":
                    return ("regA", "regB", "regC", "x̂1", "x̂2", "ŷ")
                return ("regA", "regB", "r", "x̂", "ŷ")
        return ()

    def _menu_key(self, key: str) -> None:
        spec = self.menu_spec()
        if key in (k.AC,):
            self.screen = self.back if self.back != "menu" else "calc"
            if self.screen == "calc" and self.mode == "TABLE":
                self.screen = "table_fx"
            return
        if key == k.DOWN and spec.down:
            self.menu = spec.down
            return
        if key == k.UP and spec.up:
            self.menu = spec.up
            return
        if spec.numbers:
            if key in spec.numbers:
                spec.pick(int(key))
            return
        if key in k.DIGITS and 1 <= int(key) <= len(spec.options):
            spec.pick(int(key))

    def _insert_from(self, tokens: tuple[str, ...]) -> Callable[[int], None]:
        def pick(n: int) -> None:
            target = self.back
            if target not in ("calc", "table_fx", "stat_editor"):
                target = "calc"
            if (
                target == "stat_editor"
                and tokens[n - 1] in TOKENS
                and self.menu.startswith("stat_")
            ):
                target = "calc"  # statistics are read on the calculation screen
            self.screen = target
            editor = self._target_editor()
            if self.screen == "calc" and self.showing_result:
                token = TOKENS[tokens[n - 1]]
                self.editor = Editor()
                if token.kind in ("estimator", "postfix", "op"):
                    self.editor.insert("Ans")
                self.showing_result = False
                self.result = None
                editor = self.editor
            editor.insert(tokens[n - 1])

        return pick

    def _target_editor(self) -> Editor:
        if self.screen == "stat_editor":
            return self.stat_entry
        if self.screen == "table_fx":
            return self.table_function
        return self.editor

    def _pick_mode(self, n: int) -> None:
        mode = self.allowed_modes[n - 1]
        if mode == "STAT":
            self.back = "calc"
            self.menu = "stat_type"
            return
        self._enter_mode(mode)

    def _enter_mode(self, mode: CalcMode) -> None:
        if self.mode == "STAT" and mode != "STAT":
            self.stat_rows = []  # leaving STAT clears its data, as the device does
        self.mode = mode
        self.history = []
        self.history_index = 0
        if mode == "TABLE":
            self.table_function = Editor()
            self.screen = "table_fx"
            self.editor = self.table_function
            self.result = None
            self.showing_result = False
            return
        self.screen = "calc"
        self._clear_entry()

    def _pick_stat_type(self, n: int) -> None:
        self.mode = "STAT"
        self.stat_type = STAT_TYPES[n - 1]
        self.stat_rows = []
        self.stat_cursor = (0, 0)
        self.stat_top = 0
        self.stat_entry = Editor()
        self.history = []
        self.editor = Editor()
        self.result = None
        self.showing_result = False
        self.screen = "stat_editor"

    def _pick_stat(self, n: int) -> None:
        match n:
            case 1:
                self.menu = "stat_type"
            case 2:
                self.screen = "stat_editor"
                self.stat_entry = Editor()
            case 3:
                self.menu = "stat_sum"
            case 4:
                self.menu = "stat_var"
            case 5:
                self.menu = "stat_minmax"
            case 6:
                self.menu = "stat_reg"

    def _after_setup(self) -> None:
        if self.mode == "STAT" and self.back == "stat_editor":
            self.screen = "stat_editor"
            return
        self._to_calc()

    def _pick_setup1(self, n: int) -> None:
        match n:
            case 1:
                self.menu = "setup_io"
                return
            case 2:
                self.setup.input = "line"
                self.setup.output = "line"
            case 3 | 4 | 5:
                self.setup.angle = ("DEG", "RAD", "GRA")[n - 3]
            case 6:
                self.menu = "fix"
                return
            case 7:
                self.menu = "sci"
                return
            case 8:
                self.menu = "norm"
                return
        self._after_setup()

    def _pick_setup2(self, n: int) -> None:
        if n == 1:
            self.menu = "freq"
            return
        self.setup.fraction = "ab/c" if n == 2 else "d/c"  # noqa: PLR2004
        self._after_setup()

    def _pick_io(self, n: int) -> None:
        self.setup.input = "math"
        self.setup.output = "math" if n == 1 else "line"
        self._after_setup()

    def _pick_digits(self, disp: Literal["Fix", "Sci", "Norm"]) -> Callable[[int], None]:
        def pick(n: int) -> None:
            self.setup.disp = disp
            self.setup.digits = n
            self._after_setup()

        return pick

    def _pick_frequency(self, n: int) -> None:
        self.set_frequency(on=n == 1)
        self._after_setup()

    def set_frequency(self, *, on: bool) -> None:
        if self.setup.frequency == on:
            return
        self.setup.frequency = on
        for row in self.stat_rows:
            if on:
                row.append(v.rational(1))
            elif row:
                row.pop()
        self.stat_cursor = (self.stat_cursor[0], 0)

    def _pick_clear(self, n: int) -> None:
        choice = ("setup", "memory", "all")[n - 1]
        self.pending = choice
        question = {"setup": "Reset Setup?", "memory": "Clear Memory?", "all": "Reset All?"}[choice]
        self.message = (question, "[=] :Yes  [AC] :Cancel")
        self.screen = "message"

    def _do_clear(self, choice: str) -> None:
        """CLR (FR-FX-CFG-006): reset the setup, clear the memories, or both."""
        if choice in ("setup", "all"):
            self.setup = self.default_setup()
            self.mode = "COMP"
        if choice in ("memory", "all"):
            for name in self.variables:
                self.variables[name] = v.ZERO
        if choice == "all":
            self.stat_rows = []
            self.table_function = Editor()
            self.table_range = [v.rational(1), v.rational(5), v.rational(1)]
        self.history = []
        self.history_index = 0
        self.pending = ""
        self.editor = Editor()
        self.result = None
        self.showing_result = False
        done = {"setup": "Reset Setup", "memory": "Clear Memory", "all": "Reset All"}[choice]
        self.message = (done, "Press [AC] Key")
        self.screen = "message"

    # ---- STAT data editor (FR-FX-STA-001) ----

    def stat_columns(self) -> tuple[str, ...]:
        base = ("X",) if self.stat_type == "1-VAR" else ("X", "Y")
        return (*base, "FREQ") if self.setup.frequency else base

    def _stat_key(self, key: str, *, shift: bool, alpha: bool) -> None:  # noqa: PLR0911, PLR0912
        entry = self.stat_entry
        row, col = self.stat_cursor
        columns = len(self.stat_columns())
        if key == k.EQ:
            if not entry.is_empty():
                try:
                    value = number(evaluate(entry.items, self.context(statistics=False)))
                except CalcError as error:
                    self.error = error.message
                    self.back = "stat_editor"
                    self.screen = "error"
                    return
                self._put_cell(row, col, value)
                self.stat_entry = Editor()
            self._move_stat(row + 1, col)
            return
        if key == k.AC:
            if entry.is_empty():
                self.screen = "calc"
                self._clear_entry()
            else:
                self.stat_entry = Editor()
            return
        if key == k.DEL:
            if shift:
                if row < len(self.stat_rows) and len(self.stat_rows) < MAX_STAT_ROWS:
                    self.stat_rows.insert(row, self._blank_row())
            elif not entry.is_empty():
                entry.delete()
            elif row < len(self.stat_rows):
                del self.stat_rows[row]
                self._move_stat(row, col)
            return
        if key in (k.UP, k.DOWN):
            self.stat_entry = Editor()
            self._move_stat(row + (1 if key == k.DOWN else -1), col)
            return
        if key in (k.LEFT, k.RIGHT):
            if entry.is_empty():
                self._move_stat(row, max(0, min(columns - 1, col + (1 if key == k.RIGHT else -1))))
            elif key == k.LEFT:
                entry.left()
            else:
                entry.right()
            return
        if key == k.HYP and not alpha:
            self.hyp = True
            return
        action = key_action(key, shift=shift, alpha=alpha, hyp=self.hyp)
        self.hyp = False
        if action is not None:
            apply_action(entry, action)

    def _blank_row(self) -> list[Number | None]:
        row: list[Number | None] = [None] * len(self.stat_columns())
        if self.setup.frequency:
            row[-1] = v.rational(1)
        return row

    def _put_cell(self, row: int, col: int, value: Number) -> None:
        if row >= len(self.stat_rows):
            if len(self.stat_rows) >= MAX_STAT_ROWS:
                return
            self.stat_rows.append(self._blank_row())
            row = len(self.stat_rows) - 1
        self.stat_rows[row][col] = value

    def _move_stat(self, row: int, col: int) -> None:
        last = min(len(self.stat_rows), MAX_STAT_ROWS - 1)
        row = max(0, min(row, last))
        self.stat_cursor = (row, col)
        if row < self.stat_top:
            self.stat_top = row
        elif row >= self.stat_top + GRID_ROWS:
            self.stat_top = row - GRID_ROWS + 1

    def stat_data(self) -> list[tuple[float, float, float]]:
        """The complete rows as (x, y, frequency); y is 0 for 1-VAR."""
        out: list[tuple[float, float, float]] = []
        two = self.stat_type != "1-VAR"
        for row in self.stat_rows:
            x = row[0]
            y = row[1] if two else v.ZERO
            freq = row[-1] if self.setup.frequency else v.rational(1)
            if x is None or y is None:
                continue
            out.append((float(x), float(y), float(freq) if freq is not None else 1.0))
        return out

    def _one(self) -> OneVar:
        return one_var([(x, f) for x, _, f in self.stat_data()])

    def _two(self) -> TwoVar:
        return two_var(self.stat_data())

    def _model(self) -> Regression:
        return regression(self.stat_type, self.stat_data())

    def stat_value(self, name: str) -> Number:
        """A STAT variable from the data editor's rows (FR-FX-STA-002 to -004)."""
        if self.stat_type == "1-VAR":
            one = self._one()
            table = {
                "n": one.n,
                "x̄": one.mean,
                "σx": one.sigma_x,
                "sx": one.sx,
                "Σx": one.sum_x,
                "Σx²": one.sum_x2,
                "minX": one.min_x,
                "maxX": one.max_x,
                "Q1": one.q1,
                "med": one.median,
                "Q3": one.q3,
            }
        else:
            if name in ("regA", "regB", "regC", "r"):
                model = self._model()
                found = {"regA": model.a, "regB": model.b, "regC": model.c, "r": model.r}[name]
                return _stat_number(found)
            two = self._two()
            table = {
                "n": two.n,
                "x̄": two.mean_x,
                "σx": two.sigma_x,
                "sx": two.sx,
                "ȳ": two.mean_y,
                "σy": two.sigma_y,
                "sy": two.sy,
                "Σx": two.sum_x,
                "Σx²": two.sum_x2,
                "Σy": two.sum_y,
                "Σy²": two.sum_y2,
                "Σxy": two.sum_xy,
                "minX": two.min_x,
                "maxX": two.max_x,
                "minY": two.min_y,
                "maxY": two.max_y,
            }
        if name not in table:
            raise v.syntax_error()
        return _stat_number(table[name])

    def estimate(self, name: str, value: Number) -> Number:
        """x̂, ŷ, x̂₁, x̂₂ (FR-FX-STA-005)."""
        model = self._model()
        x = float(value)
        if name == "ŷ":
            return _stat_number(model.predict_y(x))
        if name in ("x̂1", "x̂2"):
            if self.stat_type != "_+CX2":
                raise v.syntax_error()
            return _stat_number(model.predict_x(x, 1 if name == "x̂1" else 2))
        if self.stat_type == "_+CX2":
            raise v.syntax_error()
        return _stat_number(model.predict_x(x))

    # ---- TABLE mode (FR-FX-MOD-003) ----

    def _table_fx_key(self, key: str, *, shift: bool, alpha: bool) -> None:
        self.editor = self.table_function
        if key == k.EQ:
            if self.table_function.is_empty():
                return
            self.table_prompt = 0
            self.table_entry = Editor()
            self.screen = "table_prompt"
            return
        if key == k.AC:
            self.table_function.clear()
            return
        self._edit_key(self.table_function, key, shift=shift, alpha=alpha)

    def _edit_key(self, editor: Editor, key: str, *, shift: bool, alpha: bool) -> None:
        match key:
            case k.DEL:
                if not shift:
                    editor.delete()
            case k.LEFT:
                editor.left()
            case k.RIGHT:
                editor.right()
            case k.UP | k.DOWN:
                editor.vertical(-1 if key == k.UP else 1)
            case k.HOME:
                editor.home()
            case k.END:
                editor.end()
            case k.HYP if not alpha:
                self.hyp = True
            case _:
                action = key_action(key, shift=shift, alpha=alpha, hyp=self.hyp)
                self.hyp = False
                if action is not None:
                    apply_action(editor, action)

    def _table_prompt_key(self, key: str, *, shift: bool, alpha: bool) -> None:
        if key == k.EQ:
            if not self.table_entry.is_empty():
                try:
                    value = number(evaluate(self.table_entry.items, self.context()))
                except CalcError as error:
                    self.error = error.message
                    self.back = "table_prompt"
                    self.screen = "error"
                    return
                self.table_range[self.table_prompt] = value
            self.table_entry = Editor()
            if self.table_prompt < 2:  # noqa: PLR2004
                self.table_prompt += 1
                return
            self._build_table()
            return
        if key == k.AC:
            self.screen = "table_fx"
            self.editor = self.table_function
            return
        self._edit_key(self.table_entry, key, shift=shift, alpha=alpha)

    def _build_table(self) -> None:
        start, end, step = (float(x) for x in self.table_range)
        if step == 0 or (end - start) / step < 0:
            self.error = "Math ERROR"
            self.back = "table_prompt"
            self.screen = "error"
            return
        count = math.floor((end - start) / step + 1e-9) + 1
        if count > MAX_TABLE_ROWS:
            self.error = "Range ERROR"
            self.back = "table_prompt"
            self.screen = "error"
            return
        rows: list[tuple[Number, Value | str]] = []
        saved = self.variables["X"]
        try:
            for index in range(count):
                x = v.add(self.table_range[0], v.mul(self.table_range[2], v.rational(index)))
                self.variables["X"] = x
                try:
                    rows.append((x, number(evaluate(self.table_function.items, self.context()))))
                except CalcError:
                    rows.append((x, "ERROR"))
        finally:
            self.variables["X"] = saved
        self.table_rows = rows
        self.table_cursor = (0, 0)
        self.table_top = 0
        self.screen = "table"

    def _table_key(self, key: str) -> None:
        row, col = self.table_cursor
        if key == k.AC:
            self.screen = "table_fx"
            self.editor = self.table_function
            return
        if key in (k.UP, k.DOWN):
            row = max(0, min(len(self.table_rows) - 1, row + (1 if key == k.DOWN else -1)))
        elif key in (k.LEFT, k.RIGHT):
            col = 0 if key == k.LEFT else 1
        self.table_cursor = (row, col)
        if row < self.table_top:
            self.table_top = row
        elif row >= self.table_top + GRID_ROWS:
            self.table_top = row - GRID_ROWS + 1

    # ------------------------------------------------------------------------------------------
    # keypad layouts (FR-FX-UI-005; layouts.py)
    # ------------------------------------------------------------------------------------------

    def default_setup(self) -> Setup:
        """SETUP's defaults: linear display for a layout whose calculator has one."""
        if self.linear_layout:
            return Setup(input="line", output="line")
        return Setup()

    def use_layout(
        self, modes: tuple[CalcMode, ...], *, linear: bool, switch_display: bool = True
    ) -> None:
        """Take on a keypad layout's modes and display. A mode the layout lacks is left for COMP.
        When the layout changes between a natural and a linear calculator the display switches to
        match (`switch_display`; a restored calculator keeps the SETUP it was saved with)."""
        self.allowed_modes = modes
        if self.linear_layout != linear:
            self.linear_layout = linear
            if switch_display:
                self.setup.input = self.setup.output = "line" if linear else "math"
        if self.mode not in modes:
            self._enter_mode("COMP")
        elif self.screen == "menu":
            self._to_calc()

    def _pseudo(self, key: str) -> bool:
        """Keys only some layouts have: a token key, a STAT submenu key, and DATA."""
        if key.startswith("TOK:"):
            self._insert_token(key[4:])
            return True
        if key.startswith("STATSUB:"):
            if self.mode == "STAT" and self.screen != "menu":
                self.open_menu("stat")
                self._menu_key(key.split(":", 1)[1])
            return True
        if key == "DATA":
            if self.mode == "STAT" and self.screen == "calc":
                self._data_entry()
            elif self.mode != "STAT":
                self._memory(minus=False)
            return True
        return False

    def _insert_token(self, token: str) -> None:
        if token not in TOKENS or self.screen not in ("calc", "table_fx", "stat_editor"):
            return
        editor = self._target_editor()
        if self.screen == "calc" and self.showing_result:
            self.editor = Editor()
            if TOKENS[token].kind in ("estimator", "postfix", "op"):
                self.editor.insert("Ans")
            self.showing_result = False
            self.result = None
            editor = self.editor
        self.note = ""
        editor.insert(token)

    def _data_entry(self) -> None:
        """DATA (DT): the entry, x or x,y (and a frequency when FREQ is on), becomes a new data
        row; the screen counts the rows."""
        if self.showing_result or self.editor.is_empty():
            return
        parts: list[list[Item]] = [[]]
        for item in self.editor.items:
            if isinstance(item, Tok) and item.id == ",":
                parts.append([])
            else:
                parts[-1].append(item)
        columns = len(self.stat_columns())
        try:
            if not 1 <= len(parts) <= columns:
                raise v.syntax_error()
            values = [number(evaluate(part, self.context(statistics=False))) for part in parts]
        except CalcError as error:
            self.error = error.message
            self.screen = "error"
            return
        if len(self.stat_rows) >= MAX_STAT_ROWS:
            return
        row = self._blank_row()
        for index, value in enumerate(values):
            row[index] = value
        if self.stat_type != "1-VAR" and len(values) == 1:
            return  # a pair needs its y
        self.stat_rows.append(row)
        self.editor = Editor()
        self.note = "DATA SET="
        self._show(v.rational(len(self.stat_rows)))
        self.showing_result = True

    # ------------------------------------------------------------------------------------------
    # the screen
    # ------------------------------------------------------------------------------------------

    def annunciators(self) -> dict[str, bool]:
        """Which status indicators are lit (FR-FX-DSP-002)."""
        in_history = self.screen == "calc" and self.showing_result
        return {
            "S": self.shift,
            "A": self.alpha,
            "M": float(self.variables["M"]) != 0,
            "STO": self.sto,
            "RCL": self.rcl,
            "STAT": self.mode == "STAT",
            "D": self.setup.angle == "DEG",
            "R": self.setup.angle == "RAD",
            "G": self.setup.angle == "GRA",
            "FIX": self.setup.disp == "Fix",
            "SCI": self.setup.disp == "Sci",
            "Math": self.setup.input == "math",
            "▲": in_history and self.history_index > 0,
            "▼": in_history and self.history_index < len(self.history) - 1,
        }

    def answer(self) -> Seq:
        """The answer line as it is shown now."""
        if self.result is None:
            return ()
        if self.form == "fact":
            return self.fact
        return fmt.show(
            self.result,
            self.setup,
            self.form,
            mixed=self.mixed,
            eng=self.eng,
            prefer_exact=self._prefer_exact(),
        )

    def answer_text(self) -> str:
        return to_text(self.answer())

    def display(self) -> Display:  # noqa: PLR0911
        natural = self.setup.input == "math"
        match self.screen:
            case "off":
                return Display("off")
            case "menu":
                spec = self.menu_spec()
                return Display("menu", title=spec.title, options=spec.options)
            case "message":
                return Display("message", title=self.message[0], footer=self.message[1])
            case "error":
                footer = "[AC] :Cancel  [◀][▶] :Goto"
                return Display("message", title=self.error, footer=footer)
            case "stat_editor":
                return Display(
                    "grid",
                    input=self.stat_entry.layout(natural=natural),
                    grid=self._stat_grid(),
                )
            case "table_fx":
                return Display(
                    "calc", title="f(X)=", input=self.table_function.layout(natural=natural)
                )
            case "table_prompt":
                name = ("Start?", "End?", "Step?")[self.table_prompt]
                current = fmt.show(self.table_range[self.table_prompt], self.setup, "decimal")
                return Display(
                    "calc",
                    title=name,
                    input=self.table_entry.layout(natural=natural),
                    result=() if not self.table_entry.is_empty() else current,
                )
            case "table":
                return Display("grid", grid=self._table_grid())
        title = "VERIFY" if self.mode == "VERIFY" else self.note
        return Display(
            "calc",
            title=title,
            input=self.editor.layout(natural=natural, cursor=not self.showing_result),
            result=self.answer(),
        )

    def _cell(self, value: Number | Value | str | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (bool, Pair)):
            return to_text(fmt.show(value, self.setup))
        x = float(number(value))
        return to_text(fmt.decimal(x, Setup(disp="Sci", digits=6) if _wide(x) else self.setup))

    def _stat_grid(self) -> Grid:
        headers = self.stat_columns()
        rows = []
        last = len(self.stat_rows)
        for index in range(self.stat_top, min(self.stat_top + GRID_ROWS, last + 1)):
            if index < last:
                rows.append(tuple(self._cell(cell) for cell in self.stat_rows[index]))
            else:
                rows.append(tuple("" for _ in headers))
        cursor = (self.stat_cursor[0] - self.stat_top, self.stat_cursor[1])
        return Grid(headers, tuple(rows), self.stat_top + 1, cursor)

    def _table_grid(self) -> Grid:
        rows = tuple(
            (self._cell(x), self._cell(fx))
            for x, fx in self.table_rows[self.table_top : self.table_top + GRID_ROWS]
        )
        cursor = (self.table_cursor[0] - self.table_top, self.table_cursor[1])
        return Grid(("X", "F(X)"), rows, self.table_top + 1, cursor)

    # ------------------------------------------------------------------------------------------
    # settings shortcuts the CASSim menus use (they change state as SETUP would)
    # ------------------------------------------------------------------------------------------

    def set_angle(self, angle: Literal["DEG", "RAD", "GRA"]) -> None:
        self.setup.angle = angle

    def reset(self) -> None:
        """Everything back to its starting state (CLR 3 without the questions), keeping the
        keypad layout's modes and display."""
        fresh = ScientificState(
            rng=self.rng, allowed_modes=self.allowed_modes, linear_layout=self.linear_layout
        )
        fresh.setup = fresh.default_setup()
        for name in fresh.__dataclass_fields__:
            setattr(self, name, getattr(fresh, name))

    def load_items(self, items: list[Item]) -> None:
        """Put an entry on the calculation screen (Examples)."""
        self.editor = Editor(items)
        self.result = None
        self.showing_result = False
        self.screen = "calc"

    # ------------------------------------------------------------------------------------------
    # files and share links (FR-FX-SHR-001 to -006)
    # ------------------------------------------------------------------------------------------

    def to_dict(self, *, history: bool = True) -> dict[str, Any]:
        defaults = Setup().to_dict()
        data: dict[str, Any] = {"mode": self.mode}
        setup = {key: v for key, v in self.setup.to_dict().items() if v != defaults[key]}
        if setup:
            data["setup"] = setup  # only what differs, so links stay short
        if self.mode == "STAT":
            data["stat_type"] = self.stat_type
        saved = {
            name: dump_number(value)
            for name, value in self.variables.items()
            if not _is_zero(value)
        }
        if saved:
            data["variables"] = saved
        if self.mode != "TABLE" and not self.editor.is_empty():
            data["entry"] = dump_items(self.editor.items)
        if self.stat_rows:
            data["stat"] = [[dump_cell(cell) for cell in row] for row in self.stat_rows]
        if not self.table_function.is_empty():
            data["table"] = {
                "f": dump_items(self.table_function.items),
                "range": [dump_number(x) for x in self.table_range],
            }
        if history and self.history:
            data["history"] = [dump_items(entry.items) for entry in self.history[-10:]]
        return data

    def from_dict(self, data: object) -> None:  # noqa: PLR0912, PLR0915
        """Replace the state with a saved one. Entries are tokens and are only parsed, never run:
        answers in the history are worked out again here."""
        if not isinstance(data, dict):
            msg = "the calculator state is not an object"
            raise DocumentFileError(msg)
        fresh = ScientificState(rng=self.rng)
        try:
            fresh.setup = Setup.from_dict(data.get("setup"))
            mode = data.get("mode", "COMP")
            fresh.mode = mode if mode in MODES else "COMP"
            stat_type = data.get("stat_type", "1-VAR")
            fresh.stat_type = stat_type if stat_type in STAT_TYPES else "1-VAR"
            saved = data.get("variables", {})
            if isinstance(saved, dict):
                for name, value in saved.items():
                    if name in fresh.variables:
                        fresh.variables[name] = load_number(value)
            columns = len(fresh.stat_columns())
            for row in data.get("stat", [])[:MAX_STAT_ROWS]:
                if not isinstance(row, list) or len(row) != columns:
                    raise DocumentFileError("a STAT row has the wrong number of columns")
                fresh.stat_rows.append([load_cell(cell) for cell in row])
            table = data.get("table")
            if isinstance(table, dict):
                fresh.table_function = Editor(load_items(table.get("f", [])))
                bounds = table.get("range", [])
                if isinstance(bounds, list) and len(bounds) == 3:  # noqa: PLR2004
                    fresh.table_range = [load_number(x) for x in bounds]
            memories = dict(fresh.variables)
            for items in data.get("history", [])[-10:]:
                fresh.editor = Editor(load_items(items))
                fresh.execute()
                if fresh.screen != "calc":
                    fresh.screen = "calc"
                    fresh.error = ""
            fresh.variables = memories  # replaying the history must not change Ans, X or Y
            entry = load_items(data.get("entry", []))
            fresh.editor = Editor(entry)
            fresh.result = None
            fresh.showing_result = False
            last = fresh.history[-1] if fresh.history else None
            if last is not None and entry and dump_items(entry) == dump_items(last.items):
                fresh.history_index = len(fresh.history) - 1
                fresh._show(last.value)  # the calculation on screen when it was saved
        except (TypeError, ValueError, KeyError, AttributeError, ZeroDivisionError) as error:
            if isinstance(error, DocumentFileError):
                raise
            msg = f"the calculator state is damaged: {error}"
            raise DocumentFileError(msg) from error
        screens: dict[str, ScreenKind] = {"STAT": "stat_editor", "TABLE": "table_fx"}
        fresh.screen = screens.get(fresh.mode, "calc")
        if fresh.mode == "STAT" and not fresh.stat_rows:
            fresh.screen = "calc"
        if fresh.mode == "TABLE":
            fresh.editor = fresh.table_function
        for name in fresh.__dataclass_fields__:
            setattr(self, name, getattr(fresh, name))

    def to_document(self, name: str = "Untitled", *, history: bool = True) -> dict[str, Any]:
        return {
            "format": FORMAT,
            "schema": SCHEMA,
            "device": DEVICE_ID,
            "name": name,
            "calculator": self.to_dict(history=history),
        }

    def dumps(self, name: str = "Untitled", *, compact: bool = False) -> str:
        document = self.to_document(name)
        if compact:
            return json.dumps(document, ensure_ascii=False, separators=(",", ":"))
        return json.dumps(document, ensure_ascii=False, indent=1)

    def loads(self, text: str) -> str:
        """Open a document's text; returns its name. Another device's file is refused with the
        site that opens it (FR-PROF-009), and nothing changes."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            msg = f"the file is not valid JSON: {error}"
            raise DocumentFileError(msg) from error
        if not isinstance(data, dict) or data.get("format") != FORMAT:
            msg = "this is not a CASSim document"
            raise DocumentFileError(msg)
        device = data.get("device", "nspire")
        if device != DEVICE_ID:
            msg = f"this document is for the {device} app, not CASSim Scientific"
            raise DocumentFileError(msg)
        self.from_dict(data.get("calculator"))
        name = data.get("name", "Untitled")
        return name if isinstance(name, str) else "Untitled"

    def share_fragment(self, name: str = "Untitled") -> str:
        """The share link fragment (no `#`): a compressed document, history left out."""
        text = json.dumps(
            self.to_document(name, history=False), ensure_ascii=False, separators=(",", ":")
        )
        packed = zlib.compress(text.encode("utf-8"), 9)
        fragment = SHARE_PREFIX + base64.urlsafe_b64encode(packed).decode("ascii").rstrip("=")
        if len(fragment) > MAX_FRAGMENT:
            msg = f"the link would be {len(fragment)} characters (the limit is {MAX_FRAGMENT})"
            raise ValueError(msg)
        return fragment

    def open_fragment(self, fragment: str) -> bool:
        """Load a share link's state. False when the fragment is not a share link."""
        body = fragment.lstrip("#/")
        if not body.startswith(SHARE_PREFIX):
            return False
        body = body[len(SHARE_PREFIX) :]
        try:
            packed = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
            expander = zlib.decompressobj()
            raw = expander.decompress(packed, MAX_JSON)
            if expander.unconsumed_tail:
                msg = "the link holds too much data"
                raise DocumentFileError(msg)
            self.loads(raw.decode("utf-8"))
        except (ValueError, zlib.error) as error:
            if isinstance(error, DocumentFileError):
                raise
            msg = f"the link is damaged: {error}"
            raise DocumentFileError(msg) from error
        return True


# ---- what each key types --------------------------------------------------------------------

type Action = tuple[str, ...]  # ("tok", id, ...) or ("tmpl", kind, slot, absorb, filled...)


def _tok(*ids: str) -> Action:
    return ("tok", *ids)


def _tmpl(kind: TmplKind, slot: int = 0, *, absorb: bool = False, filled: str = "") -> Action:
    return ("tmpl", kind, str(slot), "1" if absorb else "", filled)


_PLAIN: dict[str, Action] = {
    **{digit: _tok(digit) for digit in k.DIGITS},
    k.DOT: _tok("."),
    k.ADD: _tok("+"),
    k.SUB: _tok("−"),
    k.MUL: _tok("×"),
    k.DIV: _tok("÷"),
    k.LPAREN: _tok("("),
    k.RPAREN: _tok(")"),
    k.NEG: _tok("neg"),
    k.ANS: _tok("Ans"),
    k.X2: _tok("²"),
    k.X3: _tok("³"),
    k.XINV: _tok("⁻¹"),
    k.LOG: _tok("log("),
    k.LN: _tok("ln("),
    k.EXP: _tmpl("exp10"),
    k.FRAC: _tmpl("frac", absorb=True),
    k.SQRT: _tmpl("sqrt"),
    k.POW: _tmpl("pow"),
    k.ABS: _tmpl("abs"),
    k.LOGAB: _tmpl("logab"),
    k.REL_EQ: _tok("="),
    k.REL_LT: _tok("<"),
    k.REL_GT: _tok(">"),
}
_SHIFTED: dict[str, Action] = {
    "0": _tok("Rnd("),
    k.DOT: _tok("Ran#"),
    k.EXP: _tok("π"),
    k.ADD: _tok("Pol("),
    k.SUB: _tok("Rec("),
    k.MUL: _tok("nPr"),
    k.DIV: _tok("nCr"),
    k.LPAREN: _tok("%"),
    k.RPAREN: _tok(","),
    k.XINV: _tok("!"),
    k.FRAC: _tmpl("mixed", absorb=True),
    k.SQRT: _tmpl("root", 1, filled="3"),
    k.POW: _tmpl("root"),
    k.LOG: ("seq", "ten"),
    k.LN: ("seq", "e"),
}
_ALPHA: dict[str, Action] = {
    **{key: _tok(name) for key, name in k.VARIABLE_KEYS.items()},
    k.DOT: _tok("RanInt#("),
    k.EXP: _tok("e"),
    k.MUL: _tok("GCD("),
    k.DIV: _tok("LCM("),
}


def key_action(key: str, *, shift: bool, alpha: bool, hyp: bool) -> Action | None:
    """What a key types into an entry, or None if it types nothing."""
    if key in (k.SIN, k.COS, k.TAN) and not alpha:
        name = {k.SIN: "sin", k.COS: "cos", k.TAN: "tan"}[key] + ("h" if hyp else "")
        return _tok(f"{name}⁻¹(" if shift else f"{name}(")
    if alpha:
        return _ALPHA.get(key)
    if shift:
        return _SHIFTED.get(key)
    return _PLAIN.get(key)


def action_continues(action: Action) -> bool:
    """Whether the action, typed just after an answer, starts with Ans (Ans+, Ans², Ans×10³)."""
    if action[0] == "tok":
        return TOKENS[action[1]].kind in ("op", "postfix", "estimator")
    return action[0] == "tmpl" and action[1] in ("pow", "exp10")


def apply_action(editor: Editor, action: Action) -> None:
    match action[0]:
        case "tok":
            editor.insert(*action[1:])
        case "tmpl":
            kind = cast("TmplKind", action[1])
            filled = (tuple(action[4]),) if action[4] else ()
            editor.template(kind, filled, int(action[2]), absorb=bool(action[3]))
        case "seq":  # 10■ and e■: the base, then an empty power
            if editor.insert(action[1]):
                editor.template("pow")


# ---- saving entries and numbers -------------------------------------------------------------


def dump_items(items: list[Item]) -> list[Any]:
    out: list[Any] = []
    for item in items:
        if isinstance(item, Tok):
            out.append(item.id)
        else:
            out.append({"t": item.kind, "s": [dump_items(slot) for slot in item.slots]})
    return out


def load_items(data: object, depth: int = 0) -> list[Item]:
    if not isinstance(data, list) or depth > MAX_DEPTH:
        msg = "an entry is damaged"
        raise DocumentFileError(msg)
    items: list[Item] = []
    for entry in data:
        if isinstance(entry, str):
            if entry not in TOKENS:
                msg = f"unknown key {entry!r} in an entry"
                raise DocumentFileError(msg)
            items.append(Tok(entry))
        elif isinstance(entry, dict) and entry.get("t") in SLOTS:
            kind = cast("TmplKind", entry["t"])
            slots = entry.get("s", [])
            if not isinstance(slots, list) or len(slots) != SLOTS[kind]:
                msg = "a template in an entry is damaged"
                raise DocumentFileError(msg)
            items.append(Tmpl(kind, [load_items(slot, depth + 1) for slot in slots]))
        else:
            msg = "an entry is damaged"
            raise DocumentFileError(msg)
    if depth == 0 and count(items) > MAX_ITEMS:
        msg = "an entry is too long"
        raise DocumentFileError(msg)
    return items


def dump_number(value: Number) -> object:
    """A number in a file: an exact value as [[radicand, π power, "p/q"], ...], a decimal as a
    JSON number."""
    if isinstance(value, Exact):
        return [[r, p, str(c)] for r, p, c in value.terms]
    return float(value)


def load_number(data: object) -> Number:
    if isinstance(data, bool):
        raise DocumentFileError("a number is damaged")
    if isinstance(data, (int, float)):
        x = float(data)
        if not math.isfinite(x) or abs(x) >= v.MAX_MAGNITUDE:
            raise DocumentFileError("a number is out of range")
        return x
    if isinstance(data, list):
        total: Number = v.ZERO
        for term in data[: v.MAX_TERMS]:
            if not (isinstance(term, list) and len(term) == 3):  # noqa: PLR2004
                raise DocumentFileError("a number is damaged")
            radicand, power, coeff = term
            if (
                not isinstance(radicand, int)
                or not 1 <= radicand <= v.MAX_FACTOR
                or power not in (0, 1)
                or not isinstance(coeff, str)
                or len(coeff) > 2 * v.MAX_DIGITS + 1
            ):
                raise DocumentFileError("a number is damaged")
            part = v.mul(v.rational(Fraction(coeff)), v.sqrt(v.rational(radicand)))
            if power:
                part = v.mul(part, v.PI)
            total = v.add(total, part)
        return total
    raise DocumentFileError("a number is damaged")


def dump_cell(value: Number | None) -> object:
    return None if value is None else dump_number(value)


def load_cell(data: object) -> Number | None:
    return None if data is None else load_number(data)


def _is_zero(value: Number) -> bool:
    return isinstance(value, Exact) and not value.terms


def _stat_number(x: float) -> Number:
    if math.isnan(x):
        raise v.math_error()
    if x == int(x) and abs(x) < 1e15:  # noqa: PLR2004
        return v.rational(int(x))
    return v.check(x)


def _wide(x: float) -> bool:
    return x != 0 and (abs(x) >= 1e6 or abs(x) < 1e-3)  # noqa: PLR2004
