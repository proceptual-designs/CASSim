# Requirements traced here: FR-FX-TUT-001, FR-FX-TUT-002, FR-FX-TUT-003
"""Unit tests for CASSim fx interactive tutorial session runner."""

from cassim.devices.scientific.tutorials import (
    CORE_LESSONS,
    TutorialSession,
)


def test_core_lessons_catalog() -> None:
    assert len(CORE_LESSONS) >= 6
    for lesson in CORE_LESSONS:
        assert lesson.id
        assert lesson.title
        assert lesson.category
        assert len(lesson.steps) > 0
        for step in lesson.steps:
            assert step.key
            assert step.instruction
            assert step.detail or step.expected_screen


def test_tutorial_session_step_advancement() -> None:
    lesson = CORE_LESSONS[0]  # Mixed fractions lesson
    session = TutorialSession(lesson=lesson)

    assert session.current_step_index == 0
    assert not session.is_complete

    # First step
    step1 = session.current_step
    assert step1 is not None

    # Wrong key press does not advance
    wrong_key = "AC" if step1.key != "AC" else "0"
    assert not session.press(wrong_key)
    assert session.current_step_index == 0
    assert f"[{wrong_key}]" in session.history

    # Correct key advances
    assert session.press(step1.key)
    assert session.current_step_index == 1
    assert not session.is_complete


def test_tutorial_completion_flow() -> None:
    lesson = CORE_LESSONS[0]
    session = TutorialSession(lesson=lesson)

    for step in lesson.steps:
        assert not session.is_complete
        assert session.press(step.key)

    assert session.is_complete
    assert session.current_step is None

    # Further key presses do nothing when complete
    assert not session.press("=")


def test_tutorial_back_skip_reset() -> None:
    lesson = CORE_LESSONS[0]
    session = TutorialSession(lesson=lesson)

    # Advance one step
    session.advance()
    assert session.current_step_index == 1

    # Back
    session.back()
    assert session.current_step_index == 0

    # Back at beginning stays 0
    session.back()
    assert session.current_step_index == 0

    # Reset
    session.advance()
    session.advance()
    assert session.current_step_index == 2
    session.reset()
    assert session.current_step_index == 0
    assert len(session.history) == 0
