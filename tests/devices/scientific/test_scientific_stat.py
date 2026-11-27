"""STAT and TABLE modes, SETUP and CLR.

Requirements: FR-FX-MOD-002, FR-FX-MOD-003, FR-FX-CFG-001, FR-FX-CFG-002, FR-FX-CFG-005,
FR-FX-CFG-006, FR-FX-STA-001 to -006.
Cited: FR-FX-STA-001 FR-FX-STA-002 FR-FX-STA-003 FR-FX-STA-004 FR-FX-STA-005 FR-FX-STA-006.
"""

from __future__ import annotations

import math

import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific.engine import STAT_TYPES, StatType, one_var, regression
from cassim.devices.scientific.state import ScientificState

S, A = k.SHIFT, k.ALPHA


def press(*keys: str, state: ScientificState | None = None) -> ScientificState:
    state = state or ScientificState()
    for key in keys:
        state.press(key)
    return state


def table_state() -> ScientificState:
    """A calculator with the TABLE extra on (MODE 4; decision 0041)."""
    return ScientificState(allowed_modes=("COMP", "STAT", "VERIFY", "TABLE"))


def column(*numbers: str) -> list[str]:
    out: list[str] = []
    for number in numbers:
        for ch in number:
            out.append(k.DOT if ch == "." else k.NEG if ch == "-" else ch)
        out.append(k.EQ)
    return out


def _x(row: list) -> float:
    assert row[0] is not None
    return float(row[0])


def stat(state: ScientificState, menu: str, item: str) -> str:
    """SHIFT 1, a STAT submenu, an item, =; the answer."""
    press(S, "1", menu, item, k.EQ, state=state)
    return state.answer_text() if state.screen == "calc" else state.error


def one_var_state(*numbers: str) -> ScientificState:
    return press(k.MODE, "2", "1", *column(*numbers), k.AC)


def test_quartiles_follow_the_school_convention() -> None:
    """FR-FX-STA-003 (AGENTS.md): Q1 of {1,4,...,64} is 6.5 and Q3 is 42.5, not numpy's."""
    state = one_var_state("1", "4", "9", "16", "25", "36", "49", "64")
    assert stat(state, "5", "3") == "6.5"
    assert stat(state, "5", "5") == "42.5"
    assert stat(state, "5", "4") == "20.5"
    odd = one_var_state("2", "5", "6", "9", "11", "14", "20")  # median left out of both halves
    assert stat(odd, "5", "3") == "5"
    assert stat(odd, "5", "5") == "14"


def test_one_variable_summary() -> None:
    """FR-FX-STA-002: n, x̄, Σx, Σx², σx (n) and sx (n−1)."""
    state = one_var_state("12", "15", "18", "22", "25")
    assert stat(state, "4", "1") == "5"
    assert stat(state, "4", "2") == "18.4"
    assert stat(state, "4", "3") == "4.673328578"
    assert stat(state, "4", "4") == "5.224940191"
    assert stat(state, "3", "2") == "92"
    assert stat(state, "3", "1") == "1802"
    assert stat(state, "5", "1") == "12"
    assert stat(state, "5", "2") == "25"


def test_frequency_column() -> None:
    """FR-FX-CFG-005 and FR-FX-STA-001: SETUP ▼ STAT turns on FREQ."""
    state = press(S, k.MODE, k.DOWN, "3", "1")
    assert state.setup.frequency
    press(k.MODE, "2", "1", *column("1", "2", "3", "4"), state=state)
    assert state.stat_columns() == ("X", "FREQ")
    press(k.UP, k.UP, k.UP, k.UP, k.RIGHT, *column("5", "12", "8", "3"), k.AC, state=state)
    assert stat(state, "4", "1") == "28"
    assert stat(state, "4", "2") == "2.321428571"


def test_editor_rows() -> None:
    """FR-FX-STA-001: = moves down, DEL deletes a row, SHIFT DEL inserts one, AC leaves."""
    state = press(k.MODE, "2", "1", *column("5", "7", "9"))
    assert state.display().text() == "X\n2 7\n3 9\n4 "
    press(k.UP, k.UP, k.DEL, state=state)  # delete the 7
    assert [_x(row) for row in state.stat_rows] == [5, 9]
    press(S, k.DEL, *column("6"), state=state)  # insert a row above the 9
    assert [_x(row) for row in state.stat_rows] == [5, 6, 9]
    press("1", "2", k.AC, state=state)  # AC clears the entry first...
    assert state.screen == "stat_editor"
    state.press(k.AC)  # ...then leaves, keeping the data
    assert state.screen == "calc"
    assert state.annunciators()["STAT"]
    press(S, "1", "2", state=state)  # Data goes back to the table
    assert state.screen == "stat_editor"


def test_stat_menu_only_offers_reg_for_two_variables() -> None:
    """FR-FX-STA-006."""
    state = one_var_state("1", "2")
    state.press(S)
    state.press("1")
    assert state.display().options == ("1:Type", "2:Data", "3:Sum", "4:Var", "5:MinMax")
    two = press(k.MODE, "2", "2", S, "1")
    assert two.display().options[-2:] == ("5:Reg", "6:MinMax")  # as on the fx-82AU PLUS II
    assert press(S, "1").screen == "calc"  # no STAT menu outside STAT mode


def linreg_state() -> ScientificState:
    return press(
        k.MODE,
        "2",
        "2",
        *column("2", "4", "6", "8", "10"),
        *(k.UP,) * 5,
        k.RIGHT,
        *column("5", "9", "12", "17", "20"),
        k.AC,
    )


def test_linear_regression() -> None:
    """FR-FX-STA-004 and -005 (the catalogue's YT-6 numbers were wrong; these are checked)."""
    state = linreg_state()
    assert stat(state, "5", "1") == "1.2"
    assert stat(state, "5", "2") == "1.9"
    assert stat(state, "5", "3") == "0.9972413741"
    press("7", state=state)
    assert stat(state, "5", "5") == "14.5"
    press("1", "6", state=state)
    assert stat(state, "5", "4") == "7.789473684"
    assert stat(state, "4", "5") == "12.6"  # ȳ


DATA = [(1.0, 2.7, 1.0), (2.0, 7.4, 1.0), (3.0, 20.1, 1.0), (4.0, 54.6, 1.0), (5.0, 148.4, 1.0)]


@pytest.mark.parametrize("kind", STAT_TYPES[1:])
def test_every_regression_type(kind: StatType) -> None:
    """FR-FX-MOD-002: all seven two-variable types fit, predict and invert."""
    model = regression(kind, DATA)
    if kind != "_+CX2":
        assert -1 <= model.r <= 1
    y = model.predict_y(2.5)
    x = model.predict_x(y) if kind != "_+CX2" else model.predict_x(y, 1)
    if kind != "_+CX2":
        assert math.isclose(x, 2.5, rel_tol=1e-9)
    else:
        assert math.isclose(model.predict_y(x), y, rel_tol=1e-9)


def test_exponential_fit_is_exact_on_exponential_data() -> None:
    points = [(float(x), 3 * math.exp(0.5 * x), 1.0) for x in range(1, 6)]
    model = regression("e^X", points)
    assert math.isclose(model.a, 3)
    assert math.isclose(model.b, 0.5)
    assert math.isclose(model.r, 1)
    quad = regression("_+CX2", [(x, 1 + 2 * x + 3 * x * x, 1.0) for x in range(5)])
    assert [round(c, 9) for c in (quad.a, quad.b, quad.c)] == [1, 2, 3]


def test_quadratic_menu_on_the_keypad() -> None:
    state = press(
        k.MODE, "2", "3", *column("0", "1", "2", "3"), *(k.UP,) * 4, k.RIGHT,
        *column("1", "6", "17", "34"), k.AC,
    )  # fmt: skip
    assert stat(state, "5", "3") == "3"  # C
    press("6", state=state)
    assert stat(state, "5", "4") == "1"  # x̂₁ of y = 6


def test_one_var_needs_data() -> None:
    state = press(k.MODE, "2", "1", k.AC)
    assert stat(state, "4", "2") == "Math ERROR"
    with pytest.raises(Exception, match="Math"):
        one_var([])


def test_leaving_stat_clears_its_data() -> None:
    state = one_var_state("4", "5")
    press(k.MODE, "1", state=state)
    assert state.stat_rows == []


def test_table_mode() -> None:
    """FR-FX-MOD-003: f(X), Start, End, Step, then the table."""
    state = press(k.MODE, "4", A, k.RPAREN, k.X2, k.SUB, "3", k.EQ, state=table_state())
    assert state.display().text().startswith("Start?")
    press(k.NEG, "2", k.EQ, "2", k.EQ, k.EQ, state=state)  # step stays 1
    assert [float(x) for x, _ in state.table_rows] == [-2, -1, 0, 1, 2]
    assert state.display().text().splitlines()[1] == "1 −2 1"
    press(k.DOWN, k.DOWN, k.DOWN, state=state)
    assert state.display().text().splitlines()[1] == "2 −1 −2"
    state.press(k.AC)
    assert state.display().text() == "f(X)=\nX²−3"


def test_table_range_and_errors() -> None:
    keys = (k.MODE, "4", "1", k.DIV, A, k.RPAREN, k.EQ, k.NEG, "1", k.EQ, "1", k.EQ, k.EQ)
    state = press(*keys, state=table_state())
    assert [cell for _, cell in state.table_rows][1] == "ERROR"  # 1/0 at X = 0
    big = press(
        k.MODE, "4", A, k.RPAREN, k.EQ, "1", k.EQ, "1", "0", "0", k.EQ, k.EQ, state=table_state()
    )
    assert big.error == "Range ERROR"


def test_setup_menu() -> None:
    """FR-FX-CFG-001 and -002."""
    state = press(S, k.MODE)
    assert state.display().options[0] == "1:MthIO"
    state.press(k.DOWN)
    assert state.display().options == ("1:ab/c", "2:d/c", "3:STAT", "4:Disp", "5:CONT")
    press(k.UP, "4", state=state)
    assert state.setup.angle == "RAD"
    press(S, k.MODE, "2", state=state)
    assert state.setup.input == "line"
    assert not state.annunciators()["Math"]
    press(S, k.MODE, "1", "2", state=state)
    assert (state.setup.input, state.setup.output) == ("math", "line")
    press(S, k.MODE, "7", "4", state=state)
    assert (state.setup.disp, state.setup.digits) == ("Sci", 4)
    assert state.annunciators()["SCI"]


def test_clear() -> None:
    """FR-FX-CFG-006: CLR 1, 2 and 3, each confirmed with = (AC cancels)."""
    state = press(S, k.MODE, "4", "5", k.MPLUS, S, k.RCL, k.NEG)
    press(S, "9", "3", k.AC, state=state)
    assert state.setup.angle == "RAD"  # cancelled
    press(S, "9", "2", k.EQ, state=state)
    assert state.display().text() == "Clear Memory\nPress [AC] Key"
    assert float(state.variables["M"]) == 0
    assert state.setup.angle == "RAD"
    press(k.AC, "5", k.MPLUS, S, "9", "1", k.EQ, k.AC, state=state)
    assert state.setup.angle == "DEG"
    assert float(state.variables["M"]) == 5
    press(S, "9", "3", k.EQ, k.AC, state=state)
    assert float(state.variables["M"]) == 0
    assert state.mode == "COMP"


def test_setup_page_two_disp_and_contrast() -> None:
    """SETUP page 2 in the manuals' order; Disp 2 gives a decimal comma in answers (a dot is
    still typed); CONT changes the contrast with ◀ ▶."""
    state = press(S, k.MODE, k.DOWN, "4", "2", "1", k.DIV, "4", k.EQ)  # LineO: a decimal
    assert state.answer_text() == "0,25"
    press(S, k.MODE, k.DOWN, "5", k.RIGHT, k.RIGHT, k.AC, state=state)
    assert state.contrast == 2
    assert state.screen == "calc"


def test_two_variable_sums_of_cubes_and_fourth_powers() -> None:
    """The Sum menu for paired data also has Σx³, Σx²y and Σx⁴."""
    state = press(k.MODE, "2", "2", "1", k.EQ, "2", k.EQ, k.UP, k.UP, k.RIGHT, "3", k.EQ, "5", k.EQ)
    press(k.AC, S, "1", "3", state=state)
    assert state.display().options[5:] == ("6:Σx³", "7:Σx²y", "8:Σx⁴")
    press("6", k.EQ, state=state)
    assert state.answer_text() == "9"
    press(S, "1", "3", "7", k.EQ, state=state)
    assert state.answer_text() == "23"  # 1·3 + 4·5
    press(S, "1", "3", "8", k.EQ, state=state)
    assert state.answer_text() == "17"
