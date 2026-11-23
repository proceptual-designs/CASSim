"""Headless device state and URL fragment sharing for CASSim fx.

Encapsulates active calculation mode (COMP, STAT, TABLE, VERIFY), system settings (Angle unit,
MthIO/LineIO, Rounding, Frequency), variable registers (A-F, M, X, Y, Ans), statistical data tables,
and history stack.

Supports compact, private client-side URL fragment sharing (#fx=...) compressed with zlib.
Pure Python: zero Flet imports.
"""

from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass, field
from typing import Literal

from cassim.devices.scientific.engine import (
    AngleUnit,
    format_prime_factors,
    safe_eval,
    to_exact_or_decimal,
    to_mixed_fraction,
)

CalcMode = Literal["COMP", "STAT", "TABLE", "VERIFY"]
RoundingMode = Literal["Norm", "Fix", "Sci"]
IoMode = Literal["MthIO", "LineIO"]
SHARE_PREFIX = "fx="
MAX_FRAGMENT = 2000
MIN_ITEM_LEN = 2

MODES: tuple[CalcMode, ...] = ("COMP", "STAT", "TABLE", "VERIFY")
ANGLE_UNITS: tuple[AngleUnit, ...] = ("DEG", "RAD", "GRA")
IO_MODES: tuple[IoMode, ...] = ("MthIO", "LineIO")
ROUNDING_MODES: tuple[RoundingMode, ...] = ("Norm", "Fix", "Sci")


def _pick[T](value: object, options: tuple[T, ...], default: T) -> T:
    """The option equal to value, or default when value is not one of them."""
    for option in options:
        if option == value:
            return option
    return default


@dataclass
class ScientificState:
    mode: CalcMode = "COMP"
    stat_type: str = "1-VAR"
    angle: AngleUnit = "DEG"
    io_mode: Literal["MthIO", "LineIO"] = "MthIO"
    rounding_mode: RoundingMode = "Norm"
    rounding_digits: int = 2
    frequency_table: bool = False

    # Variable registers: A, B, C, D, E, F, M, X, Y, Ans
    variables: dict[str, float] = field(
        default_factory=lambda: {
            "A": 0.0,
            "B": 0.0,
            "C": 0.0,
            "D": 0.0,
            "E": 0.0,
            "F": 0.0,
            "M": 0.0,
            "X": 0.0,
            "Y": 0.0,
            "Ans": 0.0,
        }
    )

    # Statistical data grids
    stat_1var: list[tuple[float, int]] = field(default_factory=list)
    stat_2var: list[tuple[float, float]] = field(default_factory=list)

    # Display buffers
    expr: str = ""
    result: str = "0"
    exact_result: str = "0"
    is_exact_active: bool = False

    # Modifiers and status
    shift_active: bool = False
    alpha_active: bool = False
    sto_active: bool = False
    rcl_active: bool = False
    cursor_visible: bool = True

    # Calculation history: (expression, result)
    history: list[tuple[str, str]] = field(default_factory=list)

    @property
    def angle_unit(self) -> AngleUnit:
        return self.angle

    @angle_unit.setter
    def angle_unit(self, val: AngleUnit) -> None:
        self.angle = val

    @property
    def mthio(self) -> bool:
        return self.io_mode == "MthIO"

    @mthio.setter
    def mthio(self, val: bool) -> None:
        self.io_mode = "MthIO" if val else "LineIO"

    def press(self, key: str) -> None:  # noqa: PLR0911, PLR0912, PLR0915
        """Handle a logical keypress event."""
        if key == "SHIFT":
            self.shift_active = not self.shift_active
            self.alpha_active = False
            return
        if key == "ALPHA":
            self.alpha_active = not self.alpha_active
            self.shift_active = False
            return

        is_shift = self.shift_active
        is_alpha = self.alpha_active
        self.shift_active = False
        self.alpha_active = False

        if key == "ON":
            self.expr = ""
            self.result = "0"
            return

        if key == "AC":
            if is_shift:  # OFF
                return
            self.expr = ""
            return

        if key == "DEL":
            if self.expr:
                self.expr = self.expr[:-1]
            return

        if key == "=":
            self.execute_equals()
            return

        if key in ("SD", "S<=>D"):
            if is_shift:
                self.toggle_mixed()
            else:
                self.toggle_sd()
            return

        if key == "M+":
            if self.expr:
                self.execute_equals()
            val = self.variables.get("Ans", 0.0)
            if is_shift:
                self.variables["M"] -= val
            else:
                self.variables["M"] += val
            return

        if key == "DMS" and is_shift:  # FACT
            self.prime_factorise()
            return

        # Operators and Ans-chaining
        if key in ("+", "-", "*", "/", "×", "÷"):
            op = "*" if key == "×" else ("/" if key == "÷" else key)
            if self.history and (not self.expr or self.expr == self.history[-1][0]):
                self.expr = f"Ans{op}"
                return
        elif key in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."):
            if self.history and self.expr == self.history[-1][0]:
                self.expr = ""

        # Digit and operator appending
        char_map = {
            "0": "0",
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            ".": ".",
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "/",
            "×": "*",
            "÷": "/",
            "(": "(",
            ")": ")",
            "Ans": "Ans",
        }
        if key in char_map:
            self.expr += char_map[key]
            return

        if key == "FRAC":
            self.expr += "/"
            return

        if key == "SQRT":
            self.expr += "sqrt("
            return

        if key == "x²":
            self.expr += "^2"
            return

        if key == "x³":
            self.expr += "^3"
            return

        if key == "xⁿ":
            self.expr += "^"
            return

        if key in ("sin", "cos", "tan"):
            if is_shift:
                self.expr += f"a{key}("
            elif is_alpha:
                pass
            else:
                self.expr += f"{key}("
            return

        if key == "log":
            self.expr += "log("
            return

        if key == "ln":
            self.expr += "ln("
            return

        if key == "Abs":
            self.expr += "abs("
            return

        if key == "(-)":
            self.expr += "-"
            return

    def execute_equals(self) -> None:
        """Evaluate the expression line and update Ans and history."""
        if not self.expr.strip():
            return
        res = safe_eval(self.expr, self.angle, self.variables)
        if isinstance(res, (int, float)):
            self.variables["Ans"] = float(res)
            exact, dec = to_exact_or_decimal(float(res))
            self.exact_result = exact
            self.result = exact if self.io_mode == "MthIO" else dec
            self.is_exact_active = self.io_mode == "MthIO"
            self.history.append((self.expr, self.result))
        else:
            self.result = str(res)

    def toggle_sd(self) -> None:
        """Toggle result between exact form and decimal."""
        try:
            val = self.variables["Ans"]
            exact, dec = to_exact_or_decimal(val)
            if self.is_exact_active:
                self.result = dec
                self.is_exact_active = False
            else:
                self.result = exact
                self.is_exact_active = True
        except Exception:
            pass

    def toggle_mixed(self) -> None:
        """Toggle fraction between improper (d/c) and mixed (ab/c)."""
        if "/" in self.result:
            if " " in self.result:
                # Mixed -> Improper
                parts = self.result.split(" ")
                whole = int(parts[0])
                num, den = map(int, parts[1].split("/"))
                improper_num = (abs(whole) * den + num) * (-1 if whole < 0 else 1)
                self.result = f"{improper_num}/{den}"
            else:
                # Improper -> Mixed
                self.result = to_mixed_fraction(self.result)

    def prime_factorise(self) -> None:
        """Prime factorise integer in Ans."""
        try:
            val = round(self.variables["Ans"])
            if val > 1:
                self.result = format_prime_factors(val)
        except Exception:
            pass

    def reset(self, all_settings: bool = True) -> None:
        """Reset calculator to default state."""
        self.mode = "COMP"
        self.stat_type = "1-VAR"
        self.angle = "DEG"
        self.io_mode = "MthIO"
        self.rounding_mode = "Norm"
        self.rounding_digits = 2
        self.frequency_table = False
        self.expr = ""
        self.result = "0"
        self.exact_result = "0"
        self.is_exact_active = False
        self.shift_active = False
        self.alpha_active = False
        if all_settings:
            for k in self.variables:
                self.variables[k] = 0.0
            self.stat_1var.clear()
            self.stat_2var.clear()
            self.history.clear()

    # -----------------------------------------------------------------------
    # Serialization & URL Fragment Sharing (#fx=...)
    # -----------------------------------------------------------------------

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "stat_type": self.stat_type,
            "angle": self.angle,
            "io_mode": self.io_mode,
            "rounding_mode": self.rounding_mode,
            "rounding_digits": self.rounding_digits,
            "frequency_table": self.frequency_table,
            "variables": self.variables,
            "stat_1var": self.stat_1var,
            "stat_2var": self.stat_2var,
            "expr": self.expr,
            "result": self.result,
            "history": self.history[-10:],
        }

    def from_dict(self, data: dict[str, object]) -> None:
        self.mode = _pick(data.get("mode"), MODES, "COMP")
        self.stat_type = str(data.get("stat_type", "1-VAR"))
        self.angle = _pick(data.get("angle"), ANGLE_UNITS, "DEG")
        self.io_mode = _pick(data.get("io_mode"), IO_MODES, "MthIO")
        self.rounding_mode = _pick(data.get("rounding_mode"), ROUNDING_MODES, "Norm")
        digits = data.get("rounding_digits", 2)
        self.rounding_digits = digits if isinstance(digits, int) else 2
        self.frequency_table = bool(data.get("frequency_table", False))

        vars_dict = data.get("variables")
        if isinstance(vars_dict, dict):
            for k, v in vars_dict.items():
                if k in self.variables:
                    self.variables[k] = float(v)

        s1 = data.get("stat_1var")
        if isinstance(s1, list):
            self.stat_1var = [(float(x[0]), int(x[1])) for x in s1 if len(x) >= MIN_ITEM_LEN]

        s2 = data.get("stat_2var")
        if isinstance(s2, list):
            self.stat_2var = [(float(p[0]), float(p[1])) for p in s2 if len(p) >= MIN_ITEM_LEN]

        self.expr = str(data.get("expr", ""))
        self.result = str(data.get("result", "0"))
        h = data.get("history")
        if isinstance(h, list):
            self.history = [(str(it[0]), str(it[1])) for it in h if len(it) >= MIN_ITEM_LEN]

    def encode_share_fragment(self) -> str:
        """Encode compact state as URL fragment string without '#'."""
        raw_json = json.dumps(self.to_dict(), separators=(",", ":"))
        compressed = zlib.compress(raw_json.encode("utf-8"), level=9)
        b64 = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
        fragment = f"{SHARE_PREFIX}{b64}"
        if len(fragment) > MAX_FRAGMENT:
            msg = f"Share payload exceeds maximum fragment length of {MAX_FRAGMENT}"
            raise ValueError(msg)
        return fragment

    def decode_share_fragment(self, fragment: str) -> None:
        """Decode URL fragment and restore calculator state."""
        clean = fragment.lstrip("#")
        if not clean.startswith(SHARE_PREFIX):
            msg = f"Fragment must start with '{SHARE_PREFIX}'"
            raise ValueError(msg)
        b64 = clean[len(SHARE_PREFIX) :]
        b64 += "=" * (-len(b64) % 4)
        compressed = base64.urlsafe_b64decode(b64)
        raw_json = zlib.decompress(compressed).decode("utf-8")
        data = json.loads(raw_json)
        self.from_dict(data)

    from_share_fragment = decode_share_fragment
