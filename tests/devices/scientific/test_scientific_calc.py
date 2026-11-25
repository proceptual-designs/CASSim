"""Calculations typed on the keypad, checked on the answer line.

Requirements: FR-FX-MOD-001, FR-FX-DSP-003, FR-FX-DSP-005 to -009, FR-FX-FNC-001 to -009,
FR-FX-CFG-002 to -004, FR-FX-MEM-001 to -003.
Cited: FR-FX-CFG-003 FR-FX-CFG-004 FR-FX-DSP-006 FR-FX-MEM-001 FR-FX-MEM-002 FR-FX-MEM-003
FR-FX-FNC-002 FR-FX-FNC-004 FR-FX-FNC-007.
"""

from __future__ import annotations

import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific.state import ScientificState

S, A = k.SHIFT, k.ALPHA


def press(*keys: str, state: ScientificState | None = None) -> ScientificState:
    state = state or ScientificState()
    for key in keys:
        state.press(key)
    return state


def answer(*keys: str, state: ScientificState | None = None) -> str:
    state = press(*keys, state=state)
    if state.screen == "error":
        return state.error
    return state.answer_text()


def digits(text: str) -> tuple[str, ...]:
    return tuple(k.DOT if ch == "." else ch for ch in text)


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        # arithmetic and priority (FR-FX-MOD-001)
        (("2", k.ADD, "3", k.MUL, "4", k.EQ), "14"),
        ((k.NEG, "2", k.X2, k.EQ), "−4"),  # x² before the sign
        (("1", k.DIV, "2", S, k.EXP, k.EQ), "0.1591549431"),  # 1÷2π: implied × first
        (("2", k.LPAREN, "3", k.ADD, "4", k.EQ), "14"),  # missing ) at the end is fine
        (("0", k.DOT, "1", k.ADD, "0", k.DOT, "2", k.EQ), "3⌟10"),
        # templates (FR-FX-DSP-003)
        ((k.FRAC, "2", k.DOWN, "3", k.RIGHT, k.ADD, k.FRAC, "3", k.DOWN, "4", k.EQ), "17⌟12"),
        (("2", k.FRAC, "3", k.EQ), "2⌟3"),  # a number before the key becomes the numerator
        ((S, k.FRAC, "2", k.RIGHT, "1", k.DOWN, "3", k.EQ), "7⌟3"),
        ((k.SQRT, "1", "8", k.EQ), "3√2"),
        ((S, k.SQRT, "2", "7", k.EQ), "3"),
        ((S, k.POW, "4", k.RIGHT, "8", "1", k.EQ), "3"),
        (("2", k.POW, "1", "0", k.EQ), "1024"),
        ((k.ABS, k.NEG, "5", k.EQ), "5"),
        ((k.LOGAB, "2", k.RIGHT, "8", k.EQ), "3"),
        # powers, roots, logs (FR-FX-FNC-003, -004)
        (("5", k.X3, k.EQ), "125"),
        (("4", k.XINV, k.EQ), "1⌟4"),
        ((k.LOG, "1", "0", "0", "0", k.EQ), "3"),
        ((S, k.LOG, "3", k.EQ), "1000"),
        ((k.LN, A, k.EXP, k.EQ), "1"),
        ((S, k.LN, "1", k.EQ), "2.718281828"),
        (("1", "2", k.EXP, "3", k.EQ), "12000"),
        ((k.EXP, "3", k.EQ), "1000"),
        # trigonometry (FR-FX-FNC-001, -002)
        ((k.SIN, "3", "0", k.EQ), "1⌟2"),
        ((k.COS, "4", "5", k.EQ), "(√2)⌟2"),
        ((S, k.TAN, "1", k.EQ), "45"),
        ((S, k.SIN, "0", k.DOT, "5", k.EQ), "30"),
        ((k.SIN, "2", "0", k.EQ), "0.3420201433"),
        ((k.HYP, k.SIN, "1", k.EQ), "1.175201194"),
        ((k.HYP, S, k.COS, "1", k.EQ), "0"),
        # combinatorics and number theory (FR-FX-FNC-005, -007)
        (("5", S, k.MUL, "2", k.EQ), "20"),
        (("5", S, k.DIV, "2", k.EQ), "10"),
        (("6", S, k.XINV, k.EQ), "720"),
        ((A, k.MUL, "1", "2", S, k.RPAREN, "1", "8", k.EQ), "6"),
        ((A, k.DIV, "4", S, k.RPAREN, "6", k.EQ), "12"),
        # percentages (FR-FX-FNC-008)
        (("2", "0", "0", k.ADD, "1", "0", S, k.LPAREN, k.EQ), "220"),
        (("8", "0", k.SUB, "2", "5", S, k.LPAREN, k.EQ), "60"),
        (("1", "5", "0", "0", k.MUL, "1", "2", S, k.LPAREN, k.EQ), "180"),
        # coordinates (FR-FX-FNC-006)
        ((S, k.ADD, "1", S, k.RPAREN, "1", k.EQ), "r=√2, θ=45"),
        ((S, k.SUB, "2", S, k.RPAREN, "6", "0", k.EQ), "X=1, Y=√3"),
        # errors
        (("1", k.DIV, "0", k.EQ), "Math ERROR"),
        (("2", k.ADD, k.ADD, k.EQ), "Syntax ERROR"),
        (("7", "0", S, k.XINV, k.EQ), "Math ERROR"),  # 70! is too big
    ],
)
def test_answers(keys: tuple[str, ...], expected: str) -> None:
    assert answer(*keys) == expected


def test_angle_units() -> None:
    """FR-FX-CFG-002: Rad and Gra, and the DRG▶ suffixes."""
    rad = press(S, k.MODE, "4")
    assert answer(k.SIN, S, k.EXP, k.DIV, "6", k.EQ, state=rad) == "1⌟2"
    assert answer(S, k.SIN, "1", k.EQ, state=rad) == "π⌟2"
    assert rad.annunciators()["R"]
    gra = press(S, k.MODE, "5")
    assert answer(k.SIN, "1", "0", "0", k.EQ, state=gra) == "1"
    deg = ScientificState()
    keys = (k.SIN, k.LPAREN, S, k.EXP, k.DIV, "2", k.RPAREN, S, k.ANS, "2", k.EQ)
    assert answer(*keys, state=deg) == "1"  # sin((π÷2)ʳ) in degrees


def test_dms() -> None:
    """FR-FX-DSP-008: entering ° ' " and showing an answer in them."""
    state = press("1", "2", k.DMS, "3", "4", k.DMS, "5", "6", k.DMS, k.EQ)
    assert state.answer_text() == "12.58222222"
    state.press(k.DMS)
    assert state.answer_text() == "12°34°56°"
    assert answer("2", k.DOT, "2", "5", k.EQ, k.DMS) == "2°15°0°"


def test_fact() -> None:
    """FR-FX-DSP-009."""
    assert answer("1", "0", "5", "0", k.EQ, S, k.DMS) == "2×3×5²×7"
    assert answer("3", "6", "0", S, k.DMS) == "2³×3²×5"  # calculates first
    assert answer("1", k.DOT, "5", k.EQ, S, k.DMS) == "Math ERROR"


def test_sd_toggles_exact_and_decimal() -> None:
    """FR-FX-DSP-005 and -006."""
    state = press(k.SQRT, "2", k.EQ)
    assert state.answer_text() == "√2"
    state.press(k.SD)
    assert state.answer_text() == "1.414213562"
    state.press(k.SD)
    assert state.answer_text() == "√2"
    state = press("7", k.FRAC, "4", k.EQ)
    state.press(S)
    state.press(k.SD)
    assert state.answer_text() == "1 3⌟4"
    state.press(S)
    state.press(k.SD)
    assert state.answer_text() == "7⌟4"
    state = press("0", k.DOT, "7", "5", k.EQ)
    assert state.answer_text() == "3⌟4"
    state.press(k.SD)
    assert state.answer_text() == "0.75"


def test_eng() -> None:
    """FR-FX-DSP-007: ENG moves the exponent down by 3, SHIFT ENG up by 3."""
    state = press("1", "2", "3", "4", "5", k.EQ, k.ENG)
    assert state.answer_text() == "12.345×10³"
    state.press(k.ENG)
    assert state.answer_text() == "12345×10⁰"
    state.press(S)
    state.press(k.ENG)
    assert state.answer_text() == "12.345×10³"
    state.press(S)
    state.press(k.ENG)
    assert state.answer_text() == "0.012345×10⁶"


@pytest.mark.parametrize(
    ("setup", "keys", "expected"),
    [
        ((), ("1", k.DIV, "3", k.SD), "0.3333333333"),
        ((S, k.MODE, "6", "2"), ("1", k.DIV, "3", k.SD), "0.33"),  # Fix 2
        ((S, k.MODE, "7", "3"), ("1", "2", "3", "4", "5", k.EQ), "1.23×10⁴"),  # Sci 3
        ((), ("0", k.DOT, "0", "0", "1", k.SD), "1×10⁻³"),  # Norm 1
        ((S, k.MODE, "8", "2"), ("0", k.DOT, "0", "0", "1", k.SD), "0.001"),  # Norm 2
        ((), ("9", k.EXP, "1", "0", k.EQ), "9×10¹⁰"),
        ((S, k.MODE, k.DOWN, "1"), ("7", k.FRAC, "4", k.EQ), "1 3⌟4"),  # ab/c
        ((S, k.MODE, "2"), ("1", k.DIV, "4", k.EQ), "0.25"),  # LineIO: decimals
        ((S, k.MODE, "2"), (k.FRAC, "1", k.RIGHT, "4", k.EQ), "1⌟4"),  # ...unless a fraction
        ((S, k.MODE, "1", "2"), (k.SQRT, "2", k.EQ), "1.414213562"),  # MathIO LineO
    ],
)
def test_number_formats(setup: tuple[str, ...], keys: tuple[str, ...], expected: str) -> None:
    """FR-FX-CFG-001, -003, -004."""
    assert answer(*setup, *keys) == expected


def test_rnd() -> None:
    """FR-FX-FNC-009: Rnd( rounds to the display setting."""
    state = press(S, k.MODE, "6", "2")
    assert answer(S, "0", "1", k.DIV, "3", k.RPAREN, k.MUL, "3", k.SD, state=state) == "0.99"


def test_random() -> None:
    """FR-FX-FNC-005: Ran# has three places; RanInt# stays in its range."""
    state = ScientificState()
    for _ in range(20):
        press(S, k.DOT, k.EQ, state=state)
        number = float(state.variables["Ans"])  # 0.007 is shown as 7×10⁻³ in Norm 1
        assert 0 <= number < 1
        assert abs(number * 1000 - round(number * 1000)) < 1e-9
        roll = int(answer(A, k.DOT, "1", S, k.RPAREN, "6", k.EQ, state=state))
        assert 1 <= roll <= 6


def test_memories() -> None:
    """FR-FX-MEM-001 to -003: Ans, STO/RCL, ALPHA variables, M+ and M−."""
    state = press("1", "2", k.MUL, "3", k.EQ, S, k.RCL, k.NEG)  # 36 → A
    assert state.display().text() == "Ans→A\n36"
    assert answer("2", A, k.NEG, k.EQ, state=state) == "72"
    assert answer(k.ADD, "1", k.EQ, state=state) == "73"  # Ans+1
    assert answer(k.RCL, k.NEG, state=state) == "36"
    state = press("5", k.MPLUS, "2", k.MPLUS, "1", S, k.MPLUS)
    assert state.annunciators()["M"]
    assert answer(A, k.MPLUS, k.EQ, state=state) == "6"


def test_history_replay() -> None:
    """FR-FX-DSP-004: ▲ ▼ show earlier calculations; ◀ edits one."""
    state = press("1", k.ADD, "1", k.EQ, "2", k.MUL, "5", k.EQ)
    state.press(k.UP)
    assert state.display().text() == "1+1\n2"
    assert state.annunciators()["▼"]
    state.press(k.DOWN)
    assert state.display().text() == "2×5\n10"
    state.press(k.LEFT)
    state.press("0")
    state.press(k.EQ)
    assert state.answer_text() == "100"


def test_cursor_editing() -> None:
    """FR-FX-DSP-004: the cursor moves through slots and DEL removes what is before it."""
    state = press(k.FRAC, "1", k.DOWN, "2", k.UP, "3")
    assert state.display().text() == "(13)⌟2"
    state.press(k.DEL)
    state.press(k.DEL)
    state.press(k.DOWN)
    state.press(k.DEL)
    state.press(k.DEL)
    assert state.display().text() == ""


def test_error_screen_goes_back_to_the_entry() -> None:
    state = press("2", k.ADD, k.ADD, k.EQ)
    assert state.display().text().startswith("Syntax ERROR")
    state.press(k.LEFT)
    assert state.display().text() == "2++"
    state.press(k.DEL)
    state.press("3")
    state.press(k.EQ)
    assert state.answer_text() == "5"


def test_verify() -> None:
    """FR-FX-MOD-004: relations give TRUE or FALSE, only in VERIFY mode."""
    state = press(k.MODE, "4")
    assert answer("1", k.ADD, "1", S, "6", "1", "2", k.EQ, state=state) == "TRUE"
    assert answer(k.SQRT, "2", k.RIGHT, k.REL_LT, "1", k.DOT, "5", k.EQ, state=state) == "TRUE"
    assert answer("3", k.REL_GT, "4", k.EQ, state=state) == "FALSE"
    assert answer("1", k.REL_EQ, "1", k.EQ) == "Syntax ERROR"


def test_off_and_on() -> None:
    state = press("5", S, k.AC)
    assert state.display().kind == "off"
    state.press("7")
    assert state.display().kind == "off"
    state.press(k.ON)
    assert state.display().kind == "calc"


def test_input_is_limited() -> None:
    state = ScientificState()
    for _ in range(150):
        state.press("9")
    assert len(state.display().text()) == 99
