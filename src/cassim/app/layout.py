"""Where things go for the window we are in: first-visit mode and the Handheld fit (FR-DEV-004).

Plain numbers in, plain numbers out, so the rules are tested without a browser. Handheld mode draws
the 320x240 screen and the keypad at their natural size and scales the whole thing to the window:
the keypad under the screen in portrait, beside it in landscape (NFR-PORT-003).
"""

from __future__ import annotations

from dataclasses import dataclass

from cassim.app.state import Mode

NARROW = 600  # px: a short side below this starts a first visit in Handheld (decision 0013 item 3)
MARGIN = 12  # px kept clear round the scaled calculator
GAP = 12  # px between the screen and the keypad
SCREEN_W, SCREEN_H = 320, 240  # the handheld's pixels
KEY_W, KEY_H, KEY_GAP = 60, 40, 4  # one key unit; the keypad is 5 units across
MIN_SCALE, MAX_SCALE = 0.4, 2.5
BAR_H = 44  # the toolbar row above the calculator


def starting_mode(width: float | None, height: float | None = None) -> Mode:
    """The mode for a first visit: Handheld when the window's short side is phone-sized (so a
    phone in landscape too), else Computer."""
    sides = [side for side in (width, height) if side]
    return Mode.HANDHELD if sides and min(sides) < NARROW else Mode.COMPUTER


def key_span(units: float, size: int = KEY_W) -> float:
    """Pixels for a key `units` wide (or tall), so that keys and their gaps line up across rows:
    two half keys and the gap between them are one key."""
    return units * (size + KEY_GAP) - KEY_GAP


def keypad_size(width_units: float, height_units: float) -> tuple[int, int]:
    return round(key_span(width_units)), round(key_span(height_units, KEY_H))


@dataclass(frozen=True)
class HandheldPlan:
    side_by_side: bool  # keypad beside the screen (landscape) instead of under it
    width: int  # the natural size of the arranged calculator
    height: int
    scale: float


def handheld_plan(
    viewport_w: float | None, viewport_h: float | None, width_units: float, height_units: float
) -> HandheldPlan:
    """The arrangement and scale that make the calculator as large as the window allows. The
    keypad's size is in key units (`keypad_units`)."""
    pad_w, pad_h = keypad_size(width_units, height_units)
    portrait = (max(SCREEN_W, pad_w), SCREEN_H + GAP + pad_h)
    landscape = (SCREEN_W + GAP + pad_w, max(SCREEN_H, pad_h))
    if not viewport_w or not viewport_h:  # the window size is not known yet
        return HandheldPlan(False, *portrait, 1.0)
    room_w = max(viewport_w - 2 * MARGIN, 1)
    room_h = max(viewport_h - 2 * MARGIN - BAR_H, 1)

    def fit(size: tuple[int, int]) -> float:
        return min(room_w / size[0], room_h / size[1])

    side = fit(landscape) > fit(portrait)
    width, height = landscape if side else portrait
    scale = max(MIN_SCALE, min(MAX_SCALE, fit(landscape if side else portrait)))
    return HandheldPlan(side, width, height, scale)


def computer_screen_height(viewport_h: float | None) -> float:
    """The Computer-mode screen fills the window below the toolbar (at least 300 px)."""
    return max(300.0, (viewport_h or 800) - BAR_H - 2 * MARGIN - 8)
