"""First-visit mode and the Handheld fit (FR-DEV-004, NFR-PORT-003)."""

import pytest

from cassim.app.layout import (
    DEFAULT_RATIO,
    KEY_GAP,
    MAX_SCALE,
    MAX_SHARE,
    MAX_ZOOM,
    MIN_SCALE,
    MIN_SHARE,
    MIN_ZOOM,
    NARROW,
    Sizing,
    computer_screen_height,
    handheld_plan,
    key_span,
    keypad_size,
    starting_mode,
)
from cassim.app.state import AppState, Mode, System
from cassim.device.keys import keypad_units
from cassim.devices.nspire import keymap as nspire

UNITS = keypad_units(nspire.KEYPAD)  # five keys across
PAD = keypad_size(*UNITS)


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
    plan = handheld_plan(390, 844, *UNITS)
    assert not plan.side_by_side
    assert max(320 * plan.scale, PAD[0] * plan.pad_scale) <= 390  # fits across
    assert plan.scale * 240 + PAD[1] * plan.pad_scale <= 844  # and down


def test_a_phone_in_landscape_puts_the_keypad_beside_the_screen() -> None:
    plan = handheld_plan(844, 390, *UNITS)
    assert plan.side_by_side
    assert plan.scale * 320 + PAD[0] * plan.pad_scale <= 844
    assert max(240 * plan.scale, PAD[1] * plan.pad_scale) <= 390


def test_the_scale_is_clamped() -> None:
    assert handheld_plan(4000, 3000, *UNITS).scale == MAX_SCALE
    assert handheld_plan(50, 50, *UNITS).scale == MIN_SCALE


def test_an_unknown_window_size_uses_natural_size() -> None:
    plan = handheld_plan(None, None, *UNITS)
    assert (plan.scale, plan.side_by_side) == (1.0, False)


def test_narrower_than_the_keypad_scales_down() -> None:
    plan = handheld_plan(PAD[0] - 40, 2000, *UNITS)
    assert plan.scale < 1


def test_the_app_state_draws_everything_at_the_handheld_scale() -> None:
    state = AppState()
    assert (state.scale, state.px(44), state.math_size) == (1.0, 44, state.system.math_size)
    state.scale = 1.5
    assert state.px(44) == 66
    assert state.math_size == state.system.math_size * 1.5


def test_half_keys_and_their_gap_make_one_key() -> None:
    assert key_span(0.5) * 2 + KEY_GAP == key_span(1)
    assert key_span(5 / 9) * 9 + 8 * KEY_GAP == pytest.approx(key_span(5))


def test_the_computer_screen_fills_the_window_height() -> None:
    assert computer_screen_height(900) > computer_screen_height(700) >= 300
    assert computer_screen_height(None) > 300
    assert computer_screen_height(200) == 300


def test_the_keypad_is_drawn_smaller_than_the_screen_by_default() -> None:
    plan = handheld_plan(844, 390, *UNITS)
    assert plan.pad_scale == pytest.approx(plan.scale * DEFAULT_RATIO)


def test_the_splitter_can_take_the_keypad_from_small_to_large() -> None:
    """A dragged share moves each part over a wide range, not a few pixels (the splitter bug)."""
    small = handheld_plan(1000, 600, *UNITS, Sizing(MIN_SHARE))
    large = handheld_plan(1000, 600, *UNITS, Sizing(MAX_SHARE))
    assert small.side_by_side == large.side_by_side
    assert large.pad_scale > 2 * small.pad_scale
    assert small.scale > large.scale


def test_a_share_fills_the_room_along_the_split() -> None:
    plan = handheld_plan(1000, 600, *UNITS, Sizing(0.4))
    assert plan.share == pytest.approx(0.4)
    assert plan.side_by_side
    pad_w, _ = PAD
    screen = plan.scale * 320
    assert screen + plan.pad_scale * pad_w <= plan.extent + 1


def test_the_splitter_starts_from_the_share_drawn() -> None:
    auto = handheld_plan(1000, 600, *UNITS)
    again = handheld_plan(1000, 600, *UNITS, Sizing(auto.share))
    assert again.pad_scale == pytest.approx(auto.pad_scale, rel=0.02)


def test_the_share_and_zoom_are_clamped() -> None:
    assert handheld_plan(844, 390, *UNITS, Sizing(9)).share == MAX_SHARE
    assert handheld_plan(844, 390, *UNITS, Sizing(0.001)).share == MIN_SHARE
    fit = handheld_plan(844, 390, *UNITS).scale
    assert handheld_plan(844, 390, *UNITS, Sizing(zoom=9)).scale == pytest.approx(fit * MAX_ZOOM)
    assert handheld_plan(844, 390, *UNITS, Sizing(zoom=0.1)).scale == pytest.approx(fit * MIN_ZOOM)


def test_the_sizes_are_kept_with_the_system_settings() -> None:
    system = System(keypad_share=0.6, zoom=1.25)
    assert System.loads(system.dumps()).zoom == 1.25
    assert System.loads(system.dumps()).keypad_share == 0.6
    assert System.loads('{"start_mode": "handheld", "math_size": 20, "zoom": 99}').zoom == 1.0
