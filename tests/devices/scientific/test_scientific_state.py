# Requirements traced here: FR-FX-MOD-001, FR-FX-DSP-001, FR-FX-MEM-001, FR-FX-SHR-001
"""Unit tests for ScientificState: input routing, Ans chaining, memory and sharing."""

from cassim.devices.scientific.state import ScientificState


def test_state_initial_defaults() -> None:
    state = ScientificState()
    assert state.mode == "COMP"
    assert state.angle_unit == "DEG"
    assert state.mthio is True
    assert state.expr == ""
    assert state.result == "0"
    assert state.variables["Ans"] == 0.0


def test_arithmetic_sequence() -> None:
    state = ScientificState()
    state.press("2")
    state.press("+")
    state.press("3")
    assert state.expr == "2+3"
    state.press("=")
    assert state.result == "5"
    assert state.variables["Ans"] == 5.0
    assert len(state.history) == 1
    assert state.history[0] == ("2+3", "5")


def test_ans_chaining() -> None:
    state = ScientificState()
    state.press("1")
    state.press("0")
    state.press("=")
    assert state.result == "10"
    assert state.variables["Ans"] == 10.0

    # Chaining with operator
    state.press("+")
    assert state.expr == "Ans+"
    state.press("5")
    state.press("=")
    assert state.result == "15"
    assert state.variables["Ans"] == 15.0


def test_shift_and_alpha_modifiers() -> None:
    state = ScientificState()
    assert not state.shift_active
    assert not state.alpha_active

    state.press("SHIFT")
    assert state.shift_active
    assert not state.alpha_active

    state.press("ALPHA")
    assert not state.shift_active
    assert state.alpha_active

    state.press("ALPHA")
    assert not state.alpha_active


def test_memory_m_plus_and_m_minus() -> None:
    state = ScientificState()
    # Store 40 into M
    state.press("4")
    state.press("0")
    state.press("M+")
    assert state.variables["M"] == 40.0

    # Subtract 15 from M
    state.press("1")
    state.press("5")
    state.press("SHIFT")
    state.press("M+")  # Triggers M-
    assert state.variables["M"] == 25.0


def test_clear_and_del() -> None:
    state = ScientificState()
    state.press("1")
    state.press("2")
    state.press("3")
    assert state.expr == "123"

    state.press("DEL")
    assert state.expr == "12"

    state.press("AC")
    assert state.expr == ""
    assert state.result == "0"


def test_sd_toggle() -> None:
    state = ScientificState()
    state.press("1")
    state.press("/")
    state.press("2")
    state.press("=")
    assert state.result == "1/2"

    state.press("S<=>D")
    assert state.result == "0.5"

    state.press("S<=>D")
    assert state.result == "1/2"


def test_url_fragment_roundtrip_sharing() -> None:
    state = ScientificState()
    state.mode = "STAT"
    state.angle_unit = "RAD"
    state.stat_1var = [(10.0, 1), (20.0, 2), (30.0, 1)]
    state.variables["A"] = 42.0
    state.history = [("sin(1)", "0.84147")]

    fragment = state.encode_share_fragment()
    assert fragment.startswith("fx=")
    assert len(fragment) < 2000

    new_state = ScientificState()
    new_state.from_share_fragment(fragment)

    assert new_state.mode == "STAT"
    assert new_state.angle_unit == "RAD"
    assert new_state.stat_1var == [(10.0, 1), (20.0, 2), (30.0, 1)]
    assert new_state.variables["A"] == 42.0
    assert new_state.history == [("sin(1)", "0.84147")]
