"""First-visit mode and the Handheld fit (FR-DEV-004, NFR-PORT-003)."""

import pytest

from cassim.app.layout import (
    MAX_SCALE,
    MIN_SCALE,
    NARROW,
    handheld_plan,
    keypad_size,
    starting_mode,
)
from cassim.app.state import AppState, Mode

PAD = keypad_size(5, 8)  # the profile's keypad is five keys across


@pytest.mark.parametrize(
    ("width", "mode"),
    [
        (360, Mode.HANDHELD),
        (NARROW - 1, Mode.HANDHELD),
        (NARROW, Mode.COMPUTER),
        (1280, Mode.COMPUTER),
        (None, Mode.COMPUTER),
        (0, Mode.COMPUTER),
    ],
)
def test_first_visit_mode_follows_the_window(width: float | None, mode: Mode) -> None:
    assert starting_mode(width) is mode


def test_a_phone_in_landscape_starts_in_handheld_too() -> None:
    assert starting_mode(844, 390) is Mode.HANDHELD
    assert starting_mode(1280, 800) is Mode.COMPUTER
    assert starting_mode(768, 1024) is Mode.COMPUTER  # a tablet


def test_a_phone_in_portrait_stacks_the_keypad_under_the_screen() -> None:
    plan = handheld_plan(390, 844, 5, 8)
    assert not plan.side_by_side
    assert plan.width * plan.scale <= 390  # fits across
    assert plan.height * plan.scale <= 844  # and down


def test_a_phone_in_landscape_puts_the_keypad_beside_the_screen() -> None:
    plan = handheld_plan(844, 390, 5, 8)
    assert plan.side_by_side
    assert plan.width * plan.scale <= 844
    assert plan.height * plan.scale <= 390


def test_the_scale_is_clamped() -> None:
    assert handheld_plan(4000, 3000, 5, 8).scale == MAX_SCALE
    assert handheld_plan(50, 50, 5, 8).scale == MIN_SCALE


def test_an_unknown_window_size_uses_natural_size() -> None:
    plan = handheld_plan(None, None, 5, 8)
    assert (plan.scale, plan.side_by_side) == (1.0, False)


def test_narrower_than_the_keypad_scales_down() -> None:
    plan = handheld_plan(PAD[0] - 40, 2000, 5, 8)
    assert plan.scale < 1


def test_the_app_state_draws_everything_at_the_handheld_scale() -> None:
    state = AppState()
    assert (state.scale, state.px(44), state.math_size) == (1.0, 44, state.system.math_size)
    state.scale = 1.5
    assert state.px(44) == 66
    assert state.math_size == state.system.math_size * 1.5
