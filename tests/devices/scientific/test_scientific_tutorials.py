"""The interactive tutorials: every lesson runs to its answer on the real calculator.

Requirements: FR-FX-TUT-001 to -006.
Cited: FR-FX-TUT-001 FR-FX-TUT-002 FR-FX-TUT-003 FR-FX-TUT-004 FR-FX-TUT-005 FR-FX-TUT-006.
"""

from __future__ import annotations

import ast
import inspect

import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific import tutorials
from cassim.devices.scientific.examples import EXAMPLES, load_example
from cassim.devices.scientific.state import ScientificState
from cassim.devices.scientific.tutorials import (
    LESSONS,
    TutorialSession,
    expected_screens,
    run_lesson,
)


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda lesson: lesson.id)
def test_each_lesson_reaches_its_answer(lesson) -> None:
    """FR-FX-TUT-004: the answer a lesson promises is what the calculator gives."""
    state = run_lesson(lesson)
    assert state.answer_text() == lesson.answer
    screens = expected_screens(lesson)
    assert len(screens) == len(lesson.steps)


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda lesson: lesson.id)
def test_every_step_key_is_a_keypad_key(lesson) -> None:
    """The review found a lesson waiting for a key the keypad never sends (SD, not S<=>D)."""
    for step in lesson.steps:
        for key in step.keys:
            assert key in k.KEYS_BY_ID, (lesson.id, key)


def test_catalogue_answers_were_corrected() -> None:
    """The catalogue gave sx = 5.1769 and y = 1.3 + 1.88x; the calculator says otherwise."""
    by_id = tutorials.LESSONS_BY_ID
    assert run_lesson(by_id["stddev"]).answer_text() == "5.224940191"
    assert run_lesson(by_id["linreg"]).answer_text() == "14.5"


def test_guide_me_waits_for_the_right_key() -> None:
    """FR-FX-TUT-001 to -003: the next key is named; a wrong key hints and changes nothing."""
    session = TutorialSession(tutorials.LESSONS_BY_ID["reset"])
    assert session.target_key == k.SHIFT
    assert not session.press("7")
    assert "SHIFT" in session.hint()
    assert session.step_index == 0
    assert session.press(k.SHIFT)
    assert session.target_key == "9"
    assert session.press("9")
    assert session.step_index == 1
    assert session.history == ["SHIFT", "9"]


def test_back_and_remaining_keys() -> None:
    lesson = tutorials.LESSONS_BY_ID["fractions"]
    session = TutorialSession(lesson)
    for key in (k.FRAC, "2", k.DOWN):
        session.press(key)
    assert session.keys_done() == [k.FRAC, "2", k.DOWN]
    session.back()
    assert session.keys_done() == [k.FRAC, "2"]
    assert session.remaining_keys()[0] == k.DOWN
    session.restart()
    assert session.keys_done() == []
    assert len(session.remaining_keys()) == lesson.key_count


def test_expected_screen_follows_the_steps() -> None:
    session = TutorialSession(tutorials.LESSONS_BY_ID["stddev"])
    assert session.expected_screen().startswith("1:COMP")
    for key in session.remaining_keys():
        session.press(key)
    assert session.is_complete
    assert session.expected_screen().endswith("5.224940191")


def solve(*keys: str, start: tuple[str, ...] = ()) -> ScientificState:
    state = ScientificState()
    for key in (*start, *keys):
        state.press(key)
    return state


def test_test_me_challenges_can_be_solved() -> None:
    """FR-FX-TUT-005: each Test me problem is checked on the student's calculator."""
    by_id = tutorials.LESSONS_BY_ID
    stddev = solve(
        k.MODE, "2", "1", "3", k.EQ, "8", k.EQ, "1", "0", k.EQ, "1", "5", k.EQ, k.AC,
        k.SHIFT, "1", "4", "4", k.EQ,
    )  # fmt: skip
    assert by_id["stddev"].challenge.check(stddev)
    fractions = solve(k.FRAC, "5", k.DOWN, "6", k.RIGHT, k.SUB, k.FRAC, "1", k.DOWN, "4", k.EQ)
    assert by_id["fractions"].challenge.check(fractions)
    assert not by_id["fractions"].challenge.check(solve("7", k.EQ))
    prime = solve("3", "6", "0", k.EQ, k.SHIFT, k.DMS)
    assert by_id["prime"].challenge.check(prime)
    reset = solve(k.SHIFT, "9", "3", k.EQ, k.AC, start=by_id["reset"].start)
    assert by_id["reset"].challenge.check(reset)
    table = solve(
        k.MODE, "3", "2", k.ALPHA, k.RPAREN, k.ADD, "1", k.EQ, "0", k.EQ, "4", k.EQ, "1", k.EQ,
        k.DOWN, k.DOWN, k.DOWN, k.DOWN,
    )  # fmt: skip
    assert by_id["table"].challenge.check(table)


def test_tutorials_stay_on_the_device() -> None:
    """FR-FX-TUT-006: nothing in the tutorials can reach a network."""
    tree = ast.parse(inspect.getsource(tutorials))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (
            node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")]
        )
    }
    assert imported.isdisjoint({"urllib", "http", "socket", "requests", "js", "pyodide"})


@pytest.mark.parametrize("index", range(len(EXAMPLES)))
def test_examples_load(index: int) -> None:
    state = ScientificState()
    load_example(state, index)
    assert state.screen in ("calc", "stat_editor", "table_fx")
    assert state.display().text()
