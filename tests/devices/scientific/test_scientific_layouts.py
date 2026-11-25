"""Keypad layouts: other calculators' keys in front of the same calculator.

Requirements: FR-FX-UI-005.
Cited: FR-FX-UI-005 FR-FX-TUT-001 FR-FX-TUT-002 FR-FX-MOD-002.
"""

from __future__ import annotations

import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific import layouts as L
from cassim.devices.scientific.editor import TOKENS
from cassim.devices.scientific.state import SHARP_KEYS, ScientificState
from cassim.devices.scientific.tutorials import layout_state, lessons_for, run_lesson, wording

SPECIALS = {k.HOME, k.END, "DATA", *SHARP_KEYS}


def _valid(key: str) -> bool:
    if key.startswith("TOK:"):
        return key[4:] in TOKENS
    if key.startswith("STATSUB:"):
        return key.split(":")[1] in "123456"
    return key in k.KEYS_BY_ID or key in SPECIALS


@pytest.mark.parametrize("layout", L.LAYOUTS, ids=lambda layout: layout.id)
def test_every_layer_presses_real_keys(layout: L.Layout) -> None:
    ids = [key.id for key in layout.all_keys()]
    assert len(ids) == len(set(ids)), "a layout names each key once"
    for key in layout.all_keys():
        for layer in (key.plain, key.shift, key.alpha):
            assert all(_valid(c) for c in layer), (layout.id, key.id, layer)
        assert bool(key.shift) == bool(key.shift_label) or key.shift == (), key.id
    assert sum(1 for key in layout.all_keys() if key.plain == (k.SHIFT,)) == 1
    assert sum(1 for key in layout.all_keys() if key.plain == (k.ALPHA,)) == 1


@pytest.mark.parametrize("layout", L.LAYOUTS, ids=lambda layout: layout.id)
def test_every_layout_reaches_the_essentials(layout: L.Layout) -> None:
    essentials = [
        *k.DIGITS, k.DOT, k.ADD, k.SUB, k.MUL, k.DIV, k.EQ, k.AC, k.DEL, k.MODE,
        k.UP, k.DOWN, k.LEFT, k.RIGHT, k.LPAREN, k.RPAREN, k.SIN, k.COS, k.TAN,
    ]  # fmt: skip
    for key in essentials:
        assert L.plan(layout, [key]) is not None, (layout.id, key)
    assert L.plan(layout, [k.SHIFT, k.MODE]) is not None  # SETUP


def test_names_are_classes_of_calculator() -> None:
    """Each layout is named for its class of calculator, not one model."""
    assert [layout.title for layout in L.LAYOUTS] == [
        "Casio fx-82 series",
        "Abacus SX-II series",
        "Sharp EL-531 series",
        "HP 10s series",
    ]
    assert L.DEFAULT is L.FX82


def test_press_follows_the_waiting_modifier() -> None:
    nine = L.FX82.key("9")
    assert L.press(nine, shift=False, alpha=False) == ["9"]
    assert L.press(nine, shift=True, alpha=False) == ["9"]  # SHIFT is already waiting: CLR
    shift = L.FX82.key("SHIFT")
    assert L.press(shift, shift=True, alpha=False) == [k.SHIFT]  # again: cancels
    sharp_square = L.EL531.key(k.X2)
    assert L.press(sharp_square, shift=True, alpha=False) == [k.SHIFT, k.XINV]  # x⁻¹
    times = L.EL531.key(k.MUL)
    assert L.press(times, shift=True, alpha=False) == [k.SHIFT]  # →HEX: not in CASSim Scientific


def test_normalize() -> None:
    assert L.normalize([k.SHIFT, k.SHIFT, k.XINV]) == [k.XINV]
    assert L.normalize([k.SHIFT, k.ALPHA, k.NEG]) == [k.ALPHA, k.NEG]
    assert L.normalize([k.SHIFT, "9"]) == [k.SHIFT, "9"]


@pytest.mark.parametrize(
    ("layout", "keys", "words"),
    [
        (L.FX82, [k.SHIFT, "9"], "SHIFT then 9"),
        (L.SX2, [k.SHIFT, "9"], "2nd then 9"),
        (L.EL531, ["CA"], "2ndF then MODE"),
        (L.HP10S, [k.SHIFT, k.MODE], "SHIFT then MODE"),  # CLR
        (L.FX82, [k.SHIFT, k.XINV], "x!"),
        (L.SX2, [k.SHIFT, k.MODE], "2nd then MODE"),
        (L.EL531, [k.SHIFT, k.MODE], "SET UP"),
        (L.EL531, [k.ALPHA, k.RPAREN], "ALPHA then RCL"),  # X
        (L.HP10S, [k.SHIFT, "2"], "SHIFT then 2"),  # S-VAR
        (L.HP10S, [k.SHIFT, k.XINV], "SHIFT then x⁻¹"),  # x!
        (L.EL531, [k.RCL, "TOK:x̄"], "RCL then 4"),  # RCL x̄, no ALPHA
        (L.EL531, ["STOXY", k.NEG], "STO then yˣ"),  # STO A
    ],
)
def test_describe(layout: L.Layout, keys: list[str], words: str) -> None:
    assert L.describe(layout, keys) == words


def test_lesson_wording_follows_the_layout() -> None:
    assert wording("Press {SHIFT 9} to open CLR.", L.SX2) == "Press 2nd then 9 to open CLR."
    assert wording("Press {SD}.", L.SX2) == "Press F↔D."


@pytest.mark.parametrize(
    ("layout", "lesson"),
    [
        pytest.param(layout, lesson, id=f"{layout.id}-{lesson.id}")
        for layout in L.LAYOUTS
        for lesson in lessons_for(layout)
    ],
)
def test_pressing_the_layout_keys_runs_the_lesson(layout, lesson) -> None:
    """Playing a lesson on a layout's own keys gives the same calculator as its canonical keys:
    every lesson can be pressed on the calculator it is for."""
    canonical = [key for step in lesson.steps for key in step.keys]
    steps = L.plan(layout, canonical)
    assert steps is not None
    state = layout_state(layout)
    lesson.prepare(state)
    for step in steps:
        for key in step.presses:
            waiting = state.sto or state.rcl
            for c in L.press(key, shift=state.shift, alpha=state.alpha, waiting=waiting):
                state.press(c)
    reference = run_lesson(lesson, layout)
    assert float(state.variables["Ans"]) == pytest.approx(float(reference.variables["Ans"]))
    assert state.mode == reference.mode
    assert state.stat_rows == reference.stat_rows


def test_mode_menu_lists_only_the_layouts_modes() -> None:
    state = layout_state(L.EL531)
    state.press(k.MODE)
    assert state.display().options == ("0:NORMAL", "1:STAT")
    assert state.setup.input == "line"
    state.press(k.AC)
    sx = layout_state(L.SX2)
    sx.press(k.MODE)
    assert sx.display().options == ("1:COMP", "2:STAT", "3:VERIFY")
    state.use_layout(L.FX82.modes, linear=False)
    assert state.setup.input == "math"
    state.press(k.MODE)
    assert len(state.display().options) == 4


def test_leaving_a_mode_the_layout_lacks() -> None:
    state = ScientificState()
    for key in (k.MODE, "3"):
        state.press(key)
    assert state.mode == "TABLE"
    state.use_layout(L.SX2.modes, linear=False)
    assert state.mode == "COMP"


def test_data_key_adds_rows() -> None:
    """The EL-531's DATA and the 10s's DT: x (or x,y) becomes a new row."""
    state = ScientificState()
    for key in (k.MODE, "2", "2", k.AC):
        state.press(key)
    for key in ("3", k.SHIFT, k.RPAREN, "7", "DATA", "5", k.SHIFT, k.RPAREN, "9", "DATA"):
        state.press(key)
    assert state.display().text() == "DATA SET=\n2"
    assert [[float(c) for c in row if c is not None] for row in state.stat_rows] == [
        [3, 7],
        [5, 9],
    ]
    outside = ScientificState()
    for key in ("4", "DATA"):
        outside.press(key)
    assert float(outside.variables["M"]) == 4


def test_token_and_statsub_keys() -> None:
    state = ScientificState()
    for key in (k.MODE, "2", "1", "4", k.EQ, "6", k.EQ, k.AC, "TOK:x̄", k.EQ):
        state.press(key)
    assert state.answer_text() == "5"
    state.press("STATSUB:4")
    assert state.display().options[:2] == ("1:n", "2:x̄")
    comp = ScientificState()
    comp.press("STATSUB:4")
    assert comp.screen == "calc"  # nothing outside STAT


# ---- each calculator's own key sequences (layouts.Dialect), from the makers' manuals ----------


def keys_on(layout: L.Layout, *keys: str) -> ScientificState:
    state = layout_state(layout)
    for key in keys:
        state.press(key)
    return state


def test_hp10s_mode_pages_and_clr() -> None:
    """HP 10s+ user guide: MODE shows COMP, SD, REG; MODE again Deg, Rad, Gra; again Fix, Sci,
    Norm; again Disp. SHIFT MODE is CLR (1 Scl or Mcl, 2 Mode, 3 All, then =)."""
    state = keys_on(L.HP10S, k.MODE)
    assert state.display().options == ("1:COMP", "2:SD", "3:REG")
    state.press(k.MODE)
    assert state.display().options == ("1:Deg", "2:Rad", "3:Gra")
    state.press("2")
    assert state.setup.angle == "RAD"
    fix = keys_on(L.HP10S, k.MODE, k.MODE, k.MODE, "1", "3", "2", k.DIV, "3", k.EQ)
    assert fix.answer_text() == "0.667"
    cleared = keys_on(L.HP10S, "5", k.SHIFT, k.RCL, k.NEG, k.MODE, k.MODE, "2")
    cleared.press(k.SHIFT)
    cleared.press(k.MODE)
    assert cleared.display().options == ("1:Mcl", "2:Mode", "3:All")
    for key in ("2", k.EQ):
        cleared.press(key)
    assert cleared.setup == cleared.default_setup()
    assert float(cleared.variables["A"]) == 5
    assert cleared.screen == "calc"


def test_hp10s_sd_and_reg_with_dt() -> None:
    """SD: x DT, x ; f DT, DT DT repeats; S-SUM and S-VAR pages. REG Lin: x , y DT."""
    sd = keys_on(L.HP10S, k.MODE, "2", "1", "2", "DATA", "1", "5", "DATA")
    assert sd.display().text() == "n=\n2"
    for key in ("DATA", k.SHIFT, "1", "3", k.EQ):
        sd.press(key)
    assert sd.answer_text() == "3"  # DT on its own entered 15 again
    freq = keys_on(L.HP10S, k.MODE, "2", "4", "TOK:;", "3", "DATA", k.SHIFT, "2", "1", k.EQ)
    assert freq.answer_text() == "4"
    assert float(freq.stat_rows[0][-1] or 0) == 3
    reg = keys_on(L.HP10S, k.MODE, "3", "1")
    for x, y in (("1", "3"), ("2", "5"), ("3", "8"), ("4", "9")):
        for key in (x, k.SHIFT, k.RPAREN, y, "DATA"):
            reg.press(key)
    for key in (k.SHIFT, "2", k.RIGHT, k.RIGHT, "2", k.EQ):
        reg.press(key)
    assert reg.answer_text() == "2.1"  # B


def test_hp10s_percent_and_fractions() -> None:
    """A × B SHIFT % is B% of A, and + then adds it on; a b/c marks a fraction and switches an
    answer between a fraction and a decimal."""
    state = keys_on(L.HP10S, "2", "5", "0", k.MUL, "1", "5", k.SHIFT, k.LPAREN, k.EQ)
    assert state.answer_text() == "37.5"
    state.press(k.ADD)
    assert state.answer_text() == "287.5"
    ratio = keys_on(L.HP10S, "6", "6", k.SUB, "6", "0", k.SHIFT, k.LPAREN, k.EQ)
    assert ratio.answer_text() == "10"  # 66 is 10% more than 60
    frac = keys_on(L.HP10S, "2", k.FRAC, "3", k.ADD, "3", k.FRAC, "4", k.EQ)
    assert frac.answer_text() == "1⌟5⌟12"
    frac.press(k.FRAC)
    assert frac.answer_text() == "1.416666667"
    assert keys_on(L.HP10S, "3", k.FRAC, "1", k.FRAC, "2", k.EQ).answer_text() == "3⌟1⌟2"


def test_el531_keys() -> None:
    """EL-531TH operation guide: MODE 1 0 is SD, x (x,y) f DATA, RCL and a statistics key;
    125 + 10 2ndF % is 137.5; DRG cycles the angle unit; SET UP 0 0 is FIX and SET UP 1 n is
    TAB n; STO then a letter key."""
    sd = keys_on(L.EL531, k.MODE, "1", "0", "3", "0", "STOXY", "2", "DATA", "4", "0", "DATA")
    assert sd.display().text() == "DATA SET=\n2"
    sd.press(k.RCL)
    sd.press("TOK:n")
    assert sd.answer_text() == "3"
    percent = keys_on(L.EL531, "1", "2", "5", k.ADD, "1", "0", k.SHIFT, k.LPAREN, k.EQ)
    assert percent.answer_text() == "137.5"
    drg = keys_on(L.EL531, "DRG")
    assert drg.setup.angle == "RAD"
    convert = keys_on(L.EL531, "9", "0", "DRGCONV")
    assert convert.setup.angle == "RAD"
    assert convert.answer_text() == "1.570796327"
    fix = keys_on(L.EL531, k.SHIFT, k.MODE, "0", "0", k.SHIFT, k.MODE, "1", "3")
    for key in ("1", "0", "0", "0", "0", k.DIV, "8", k.DOT, "1", k.EQ):
        fix.press(key)
    assert fix.answer_text() == "1234.568"
    stored = keys_on(L.EL531, "1", "2", "STOXY", k.NEG, "2", k.ALPHA, k.NEG, k.EQ)
    assert stored.answer_text() == "24"
    cleared = keys_on(L.EL531, "5", "STOXY", k.NEG, "MCLR", "0")
    assert float(cleared.variables["A"]) == 0


def test_letter_keys_after_sto_and_rcl() -> None:
    """On the EL-531 the letters are above other keys: after STO or RCL the key alone sends its
    letter (or statistic), with no ALPHA."""
    power = L.EL531.key(k.POW)
    assert L.press(power, shift=False, alpha=False) == [k.POW]
    assert L.press(power, shift=False, alpha=False, waiting=True) == [k.NEG]  # A
    four = L.EL531.key("4")
    assert L.press(four, shift=False, alpha=False, waiting=True) == ["TOK:x̄"]


def test_sx2_hyp_menu_verify_order_and_norm2() -> None:
    """SX-II MATRIXn manual: HYP opens a menu (2 is cosh, 4 is sinh⁻¹); VERIFY's menu is
    = ≠ > < ≥ ≤; Norm 2 is the default."""
    state = keys_on(L.SX2, k.HYP, "2", "0", k.RPAREN, k.EQ)
    assert state.answer_text() == "1"
    assert keys_on(L.SX2).setup.digits == 2
    verify = keys_on(L.SX2, k.MODE, "3", k.SHIFT, "6")
    assert verify.display().options[3] == "4:<"
    casio = keys_on(L.FX82, k.MODE, "4", k.SHIFT, "6")
    assert casio.display().options[3] == "4:≥"


def test_mode_names_follow_the_calculator() -> None:
    """The menu bar's mode chip uses the calculator's own names."""
    assert keys_on(L.HP10S, k.MODE, "2").mode_name() == "SD"
    assert keys_on(L.HP10S, k.MODE, "3", "1").mode_name() == "REG"
    assert keys_on(L.EL531).mode_name() == "NORMAL"
    assert keys_on(L.EL531, k.MODE, "1", "0").mode_name() == "STAT"
    assert keys_on(L.SX2, k.MODE, "3").mode_name() == "VERIF"
    assert keys_on(L.FX82, k.MODE, "2", "1", k.AC).mode_name() == "STAT"  # AC keeps STAT
    assert "MODE 0" in keys_on(L.EL531).mode_help()
    assert "MODE 1" in keys_on(L.HP10S).mode_help()


def test_el531_eng_display_and_hp_third_sum_page() -> None:
    """SET UP 0 2 is the EL-531's ENG display (TAB places); the HP's S-SUM has a third page
    in REG mode (Σx³, Σx²y, Σx⁴)."""
    eng = keys_on(L.EL531, k.SHIFT, k.MODE, "1", "2", k.SHIFT, k.MODE, "0", "2")
    for key in ("1", "2", "3", "4", "5", k.EQ):
        eng.press(key)
    assert eng.answer_text() == "12.35×10³"
    hp = keys_on(L.HP10S, k.MODE, "3", "1", "2", k.SHIFT, k.RPAREN, "5", "DATA")
    for key in (k.SHIFT, "1", k.RIGHT, k.RIGHT):
        hp.press(key)
    assert hp.display().options == ("1:Σx³", "2:Σx²y", "3:Σx⁴")
    hp.press("2")
    hp.press(k.EQ)
    assert hp.answer_text() == "20"
