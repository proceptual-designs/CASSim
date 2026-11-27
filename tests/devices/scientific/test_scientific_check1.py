"""Emulator check 1 (2026-11-26 and 27): what the makers' own PC emulators showed, as tests.

Rows are named as in `docs/testing/emulator-scientific-results.md` and the evidence repository's
`docs/handoff/acceptance-cases.csv` (FX: the fx-82AU PLUS II 2nd edition emulator, SX: the SX-II
MATRIXn emulator). Each starts from Reset All, as the captures did, unless it says otherwise.
Decided by Simon on 2026-11-27 (decision 0041): follow the emulators by default; exact surds and
π, and TABLE, are CASSim extras that are off.

Requirements: FR-FX-CFG-001, FR-FX-CFG-003, FR-FX-CFG-006, FR-FX-CFG-007, FR-FX-DSP-005,
FR-FX-DSP-007, FR-FX-DSP-008, FR-FX-FNC-002, FR-FX-FNC-005, FR-FX-FNC-008, FR-FX-MOD-003,
FR-FX-MOD-004, FR-FX-STA-003, FR-FX-UI-008.
"""

from __future__ import annotations

import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific import layouts as L
from cassim.devices.scientific.state import ScientificState
from cassim.devices.scientific.tutorials import layout_state

S, A = k.SHIFT, k.ALPHA


def digits(text: str) -> tuple[str, ...]:
    return tuple(k.DOT if ch == "." else ch for ch in text)


def fresh(layout: L.Layout = L.FX82) -> ScientificState:
    """The calculator after SHIFT 9 3 = AC (Reset All)."""
    state = layout_state(layout)
    for key in (S, "9", "3", k.EQ, k.AC):
        state.press(key)
    return state


def on(state: ScientificState, *keys: str) -> str:
    for key in keys:
        state.press(key)
    return state.error if state.screen == "error" else state.answer_text()


def math_o(layout: L.Layout = L.FX82) -> ScientificState:
    """Reset All, then SETUP 1 1 (MthIO-MathO), as part B of the check."""
    state = fresh(layout)
    on(state, S, k.MODE, "1", "1")
    return state


@pytest.mark.parametrize("layout", [L.FX82, L.SX2])
def test_reset_defaults_are_mthio_lineo_and_norm2(layout: L.Layout) -> None:
    """A4, A7: input natural, output decimal; Norm 2 (0.005, not 5×10⁻³)."""
    state = fresh(layout)
    assert (state.setup.input, state.setup.output, state.setup.digits) == ("math", "line", 2)
    assert state.annunciators()["Math"]
    assert on(state, "1", k.DIV, "2", "0", "0", k.EQ) == "0.005"
    assert on(state, k.SD) == "1⌟200"  # S⇔D gives the fraction (stacked on the LCD)
    assert on(state, "1", k.DIV, "3", k.EQ) == "0.3333333333"


def test_number_formats_after_reset() -> None:
    """A4b to A6c."""
    state = fresh()
    assert on(state, "1", k.DIV, "2", *"0" * 10, k.EQ) == "5×10⁻¹¹"
    assert on(state, k.SD) == "5×10⁻¹¹"  # no fraction is offered
    assert on(state, *"123456789012", k.EQ) == "1.23456789×10¹¹"
    norm1 = fresh()
    on(norm1, S, k.MODE, "8", "1")
    assert on(norm1, "1", k.DIV, "2", "0", "0", k.EQ) == "5×10⁻³"
    fix = fresh()
    on(fix, S, k.MODE, "6", "3")
    assert on(fix, "2", k.DIV, "3", k.EQ) == "0.667"
    assert on(fix, k.SD) == "2⌟3"
    assert on(fix, "5", k.EQ) == "5.000"
    sci = fresh()
    on(sci, S, k.MODE, "7", "4")
    assert on(sci, "2", k.DIV, "3", k.EQ) == "6.667×10⁻¹"


def test_eng_after_reset() -> None:
    """A6: ENG pressed twice; A6b, A6c."""
    state = fresh()
    assert on(state, *"1234567", k.EQ) == "1234567"
    assert on(state, k.ENG) == "1.234567×10⁶"
    assert on(state, k.ENG) == "1234.567×10³"
    assert on(state, "1", "2", k.EQ, k.ENG) == "12×10⁰"
    assert on(state, "1", "2", k.EQ, S, k.ENG) == "0.012×10³"


def test_fractions_in_math_output() -> None:
    """B1, B2, B5, B5c."""
    state = math_o()
    third = (k.FRAC, "1", k.DOWN, "3", k.RIGHT, k.ADD, k.FRAC, "1", k.DOWN, "4", k.EQ)
    assert on(state, *third) == "7⌟12"
    assert on(state, k.SD) == "0.5833333333"
    mixed = (S, k.FRAC, "2", k.RIGHT, "1", k.DOWN, "3", k.RIGHT, k.ADD, k.FRAC, "5", k.DOWN, "6")
    assert on(state, *mixed, k.EQ) == "19⌟6"
    assert on(state, S, k.SD) == "3 1⌟6"
    assert on(state, *digits("0.25"), k.EQ) == "1⌟4"
    assert on(state, k.SD) == "0.25"
    assert on(state, *digits("0.123456789"), k.EQ) == "0.123456789"
    assert on(state, k.SD) == "0.123456789"
    sx = fresh(L.SX2)  # SX B1: a fraction typed in MthIO-LineO gives a fraction
    assert on(sx, *third) == "7⌟12"
    assert on(sx, *digits("0.25"), k.EQ) == "0.25"  # SX B5: typed as a decimal, a decimal


@pytest.mark.parametrize("layout", [L.FX82, L.SX2])
def test_surds_and_trig_are_decimals(layout: L.Layout) -> None:
    """B3, B3b, B4: no surds, even in MathO, and S⇔D leaves them."""
    state = math_o(layout)
    assert on(state, k.SQRT, "2", k.RIGHT, k.ADD, k.SQRT, "8", k.EQ) == "4.242640687"
    assert on(state, k.SD) == "4.242640687"
    assert on(state, k.SQRT, "1", "2", k.RIGHT, k.DIV, "3", k.EQ) == "1.154700538"
    assert on(state, k.SIN, "4", "5", k.RPAREN, k.EQ) == "0.7071067812"
    assert on(state, k.COS, "3", "0", k.RPAREN, k.EQ) == "0.8660254038"
    assert on(state, k.SIN, "5", "0", k.RPAREN, k.EQ) == "0.7660444431"


def test_exact_surds_extra() -> None:
    """Decision 0041: the surds extra gives exact surds and π in MathO only (as the fx-8200 AU,
    fx-991ES PLUS, HP 300s+ and TI MultiView models do), up to two terms."""
    state = math_o()
    state.setup.surds = True
    assert on(state, k.SQRT, "2", k.RIGHT, k.ADD, k.SQRT, "8", k.EQ) == "3√2"
    assert on(state, k.SD) == "4.242640687"
    assert on(state, k.SIN, "4", "5", k.RPAREN, k.EQ) == "(√2)⌟2"
    assert on(state, S, k.EXP, k.DIV, "2", k.EQ) == "π⌟2"
    line_o = fresh()
    line_o.setup.surds = True
    assert on(line_o, k.SQRT, "8", k.EQ) == "2.828427125"  # LineO stays decimal
    assert on(line_o, k.SD) == "2.828427125"


def test_sexagesimal() -> None:
    """B6, B6b."""
    state = fresh()
    assert on(state, "1", "2", k.DMS, "3", "4", k.DMS, "5", "6", k.DMS, k.EQ) == "12°34°56°"
    assert on(state, *digits("12.582"), k.EQ, k.DMS) == "12°34°55.2°"


def test_fact_factorial_and_combinations() -> None:
    """B7, B9, B8."""
    state = fresh()
    assert on(state, *"1050", k.EQ, S, k.DMS) == "2×3×5²×7"
    assert on(state, *"360", k.EQ, S, k.DMS) == "2³×3²×5"
    assert on(state, "5", S, k.XINV, k.EQ) == "120"
    assert on(state, "1", "0", S, k.DIV, "3", k.EQ) == "120"
    assert on(state, "1", "0", S, k.MUL, "3", k.EQ) == "720"
    assert on(state, k.ABS, k.NEG, "3", k.EQ) == "3"


@pytest.mark.parametrize("layout", [L.FX82, L.SX2])
def test_percent_is_a_hundredth(layout: L.Layout) -> None:
    """B10, B10b, B11: % is ÷100, so 250+15% is 250.15 (the manual adds 15% as 250+250×15%)."""
    state = fresh(layout)
    assert on(state, *"250", k.ADD, "1", "5", S, k.LPAREN, k.EQ) == "250.15"
    assert on(state, k.SD) == "5003⌟20"
    assert on(state, *"250", k.MUL, "1", "5", S, k.LPAREN, k.EQ) == "37.5"
    assert on(state, "1", k.ADD, k.ANS, k.EQ) == "38.5"
    increase = (*"250", k.ADD, *"250", k.MUL, "1", "5", S, k.LPAREN, k.EQ)
    assert on(state, *increase) == "287.5"


def test_percent_by_model() -> None:
    """Manual cross-check (D14): the EL-531 adds on (125 + 10 % is 137.5); so does the 10s."""
    el = fresh(L.EL531)
    el_keys = ("1", "2", "5", k.ADD, "1", "0", k.SHIFT, k.LPAREN, k.EQ)
    assert on(el, *el_keys) == "137.5"
    fx = fresh()
    assert on(fx, "1", "2", "5", k.ADD, "1", "0", S, k.LPAREN, k.EQ) == "125.1"


@pytest.mark.parametrize("layout", [L.FX82, L.SX2])
def test_hyp_opens_a_menu_and_the_trig_keys_pick_from_it(layout: L.Layout) -> None:
    """B12b (fx-82), SX B12: hyp shows 1 sinh … 6 tanh⁻¹. While it shows, hyp is lit and sin, cos
    and tan (and SHIFT and one) pick the hyperbolic function their new names show (FR-FX-UI-008);
    hyp again closes it."""
    state = fresh(layout)
    state.press(k.HYP)
    assert state.display().options[:2] == ("1:sinh", "2:cosh")
    assert state.hyp_waiting
    assert state.annunciators()["hyp"]
    assert on(state, "1", "1", k.RPAREN, k.EQ) == "1.175201194"
    assert not state.hyp_waiting
    assert on(state, k.HYP, "2", "1", k.DOT, "5", k.RPAREN, k.ADD, "2", k.EQ) == "4.352409615"
    assert on(state, k.HYP, k.COS, "0", k.RPAREN, k.EQ) == "1"  # cos picks cosh
    assert on(state, k.HYP, S, k.SIN, "7", k.EQ) == "2.644120761"  # SHIFT sin is sinh⁻¹
    state.press(k.HYP)
    state.press(k.HYP)
    assert not state.hyp_waiting
    assert state.screen == "calc"


@pytest.mark.parametrize("layout", [L.HP10S, L.EL531])
def test_hyp_is_a_toggle_on_the_linear_calculators(layout: L.Layout) -> None:
    """HP B12 (the hyp annunciator waits for a trig key) and EL B12 (a prefix key): hyp again
    cancels it."""
    state = fresh(layout)
    state.press(k.HYP)
    assert state.hyp_waiting
    state.press(k.HYP)
    assert not state.hyp_waiting
    assert on(state, k.HYP, k.SIN, "1", k.EQ) == "1.175201194"
    assert not state.hyp_waiting


def test_statistics() -> None:
    """C3, C4, C5, C7 (FR-FX-STA-003: the median of each half; n−1 for sx)."""

    def stat(state: ScientificState, menu: str, item: str) -> str:
        return on(state, S, "1", menu, item, k.EQ)

    def column(*numbers: str) -> list[str]:
        return [key for number in numbers for key in (*digits(number), k.EQ)]

    state = fresh()
    on(state, k.MODE, "2", "1", *column("4", "7", "9", "12", "14", "18", "21", "25"), k.AC)
    assert [stat(state, "5", n) for n in ("3", "4", "5")] == ["8", "13", "19.5"]
    state = fresh()
    on(state, k.MODE, "2", "1", *column("12", "15", "18", "22", "25"), k.AC)
    assert [stat(state, "4", n) for n in "1234"] == ["5", "18.4", "4.673328578", "5.224940191"]
    assert [stat(state, "5", n) for n in "12345"] == ["12", "25", "13.5", "18", "23.5"]
    assert [stat(state, "3", n) for n in "12"] == ["1802", "92"]
    reg = fresh()
    xs = column("2", "4", "6", "8", "10")
    on(reg, k.MODE, "2", "2", *xs, *(k.UP,) * 5, k.RIGHT, *column("5", "9", "12", "17", "20"), k.AC)
    assert [stat(reg, "5", n) for n in "123"] == ["1.2", "1.9", "0.9972413741"]
    assert on(reg, "7", S, "1", "5", "5", k.EQ) == "14.5"
    freq = fresh()
    on(freq, S, k.MODE, k.DOWN, "3", "1", k.MODE, "2", "1", *column("1", "2", "3", "4"))
    on(freq, k.UP, k.UP, k.UP, k.UP, k.RIGHT, *column("5", "12", "8", "3"), k.AC)
    assert stat(freq, "4", "2") == "2.321428571"


def test_verify_is_mode_3() -> None:
    """E1, E2: MODE 3 is VERIF; the relations are = ≠ > ≥ < ≤ on the fx-82's own menu."""
    state = fresh()
    state.press(k.MODE)
    assert state.display().options == ("1:COMP", "2:STAT", "3:VERIF")
    state.press("3")
    assert state.mode_name() == "VERIF"
    assert on(state, "4", S, "6", "1", k.SQRT, "1", "6", k.EQ) == "TRUE"
    assert on(state, S, k.EXP, k.REL_GT, "3", k.EQ) == "TRUE"
    assert on(state, "1", k.ADD, "2", k.REL_LT, "3", k.EQ) == "FALSE"


def test_table_is_an_extra_mode() -> None:
    """D (fx-82 and SX-II: no TABLE on their MODE menus); decision 0041: TABLE is MODE 4 when
    the extra is on."""
    assert "TABLE" not in L.FX82.modes
    assert L.modes_for(L.FX82, table=True) == ("COMP", "STAT", "VERIFY", "TABLE")
    assert L.modes_for(L.SX2, table=True)[-1] == "TABLE"
    assert L.modes_for(L.EL531, table=True) == L.EL531.modes


def test_other_functions() -> None:
    """U1, U3, U4, U5, F1, F3, G1."""
    state = fresh()
    assert on(state, S, k.ADD, "1", S, k.RPAREN, "1", k.RPAREN, k.EQ) == "r=1.414213562, θ=45"
    assert on(state, A, k.MUL, "1", "2", S, k.RPAREN, "1", "8", k.RPAREN, k.EQ) == "6"
    assert on(state, A, k.DIV, "4", S, k.RPAREN, "6", k.RPAREN, k.EQ) == "12"
    assert on(state, S, "0", "2", k.DIV, "3", k.RPAREN, k.EQ) == "0.6666666667"
    assert on(state, "5", S, k.RCL, k.NEG) == "5"
    assert state.display().text() == "Ans→A\n5"
    assert on(state, "7", k.MPLUS, k.RCL, k.MPLUS) == "7"
    assert on(state, "1", k.DIV, "0", k.EQ) == "Math ERROR"


@pytest.mark.parametrize("layout", L.LAYOUTS)
def test_every_layout_names_its_trig_keys_hyperbolic(layout: L.Layout) -> None:
    """FR-FX-UI-008: each calculator's sin, cos and tan keys (and their SHIFT legends) have
    hyperbolic names, in the key's own case (SIN becomes SINH on the SX-II)."""
    names = [L.hyperbolic_names(key) for key in layout.all_keys()]
    found = [name for name in names if name is not None]
    assert len(found) == 3
    for face, legend in found:
        assert face[:4].lower() in ("sinh", "cosh", "tanh")
        assert legend.lower().endswith("h⁻¹")
