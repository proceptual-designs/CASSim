"""Keypad layouts: other calculators' keys in front of the same calculator.

Requirements: FR-FX-UI-005.
Cited: FR-FX-UI-005 FR-FX-TUT-001 FR-FX-TUT-002 FR-FX-MOD-002.
"""

from __future__ import annotations

import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific import layouts as L
from cassim.devices.scientific.editor import TOKENS
from cassim.devices.scientific.state import ScientificState
from cassim.devices.scientific.tutorials import LESSONS, lesson_layout, run_lesson, wording

SPECIALS = {k.HOME, k.END, "DATA"}


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
    assert L.press(times, shift=True, alpha=False) == [k.SHIFT]  # →HEX: not in CASSim fx


def test_normalize() -> None:
    assert L.normalize([k.SHIFT, k.SHIFT, k.XINV]) == [k.XINV]
    assert L.normalize([k.SHIFT, k.ALPHA, k.NEG]) == [k.ALPHA, k.NEG]
    assert L.normalize([k.SHIFT, "9"]) == [k.SHIFT, "9"]


@pytest.mark.parametrize(
    ("layout", "keys", "words"),
    [
        (L.FX82, [k.SHIFT, "9"], "SHIFT then 9"),
        (L.SX2, [k.SHIFT, "9"], "2nd then 9"),
        (L.EL531, [k.SHIFT, "9"], "2ndF then MODE"),  # CA
        (L.HP10S, [k.SHIFT, "9"], "SHIFT then DEL"),  # CLR
        (L.FX82, [k.SHIFT, k.XINV], "x!"),
        (L.SX2, [k.SHIFT, k.MODE], "2nd then MODE"),
        (L.EL531, [k.SHIFT, k.MODE], "SET UP"),
        (L.EL531, [k.ALPHA, k.RPAREN], "ALPHA then RCL"),  # X
        (L.HP10S, [k.SHIFT, "1", "4"], "SHIFT then 2"),  # S-VAR
    ],
)
def test_describe(layout: L.Layout, keys: list[str], words: str) -> None:
    assert L.describe(layout, keys) == words


def test_lesson_wording_follows_the_layout() -> None:
    assert wording("Press {SHIFT 9} to open CLR.", L.SX2) == "Press 2nd then 9 to open CLR."
    assert wording("Press {SD}.", L.SX2) == "Press F↔D."


EXPECTED_LAYOUT = {
    "sx2": {"table": "fx82"},
    "el531": {"fractions": "fx82", "percent": "fx82", "prime": "fx82", "table": "fx82"},
    "hp10s": {
        "fivenum": "fx82",
        "linreg": "fx82",
        "fractions": "fx82",
        "percent": "fx82",
        "prime": "fx82",
        "table": "fx82",
    },
}


@pytest.mark.parametrize("layout", L.LAYOUTS[1:], ids=lambda layout: layout.id)
def test_lessons_run_on_their_layout_unless_it_lacks_something(layout: L.Layout) -> None:
    """FR-FX-UI-005: a lesson runs on the chosen keys; one needing a missing mode or key runs on
    the fx-82 keys (TABLE everywhere but the fx-82; S⇔D and FACT on the linear calculators)."""
    for lesson in LESSONS:
        expected = EXPECTED_LAYOUT[layout.id].get(lesson.id, layout.id)
        assert lesson_layout(lesson, layout).id == expected, lesson.id


@pytest.mark.parametrize("layout", L.LAYOUTS, ids=lambda layout: layout.id)
@pytest.mark.parametrize("lesson", LESSONS, ids=lambda lesson: lesson.id)
def test_pressing_the_layout_keys_runs_the_lesson(layout: L.Layout, lesson) -> None:
    """Playing a lesson on a layout's own keys gives the same calculator as the canonical keys."""
    use = lesson_layout(lesson, layout)
    canonical = [key for step in lesson.steps for key in step.keys]
    steps = L.plan(use, canonical)
    assert steps is not None
    state = ScientificState()
    state.use_layout(use.modes, linear=use.linear)
    lesson.prepare(state)
    for step in steps:
        for key in step.presses:
            for c in L.press(key, shift=state.shift, alpha=state.alpha):
                state.press(c)
    reference = run_lesson(lesson)
    assert float(state.variables["Ans"]) == pytest.approx(float(reference.variables["Ans"]))
    assert state.mode == reference.mode
    assert state.stat_rows == reference.stat_rows


def test_mode_menu_lists_only_the_layouts_modes() -> None:
    state = ScientificState()
    state.use_layout(L.EL531.modes, linear=L.EL531.linear)
    state.press(k.MODE)
    assert state.display().options == ("1:COMP", "2:STAT")
    assert state.setup.input == "line"
    state.press(k.AC)
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
