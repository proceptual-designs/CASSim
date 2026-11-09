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
INSTALL_ROW = 0.7  # height of the Install button above the keys, in key heights
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


DEFAULT_RATIO = 0.8  # the keypad's scale relative to the screen's until the splitter is used
MIN_SHARE, MAX_SHARE = 0.15, 0.8  # the splitter's range: the keypad's share of the room
MIN_ZOOM, MAX_ZOOM = 0.5, 2.0
SPLITTER = 10  # px: the draggable bar between the screen and the keypad
MIN_PART_SCALE = 0.2


@dataclass(frozen=True)
class Sizing:
    """The user's choices: the keypad's share of the room (None: the default ratio) and a zoom."""

    share: float | None = None
    zoom: float = 1.0
    bar: float = BAR_H  # the toolbar's height above the calculator (0 when it is empty)


@dataclass(frozen=True)
class HandheldPlan:
    side_by_side: bool  # keypad beside the screen (landscape) instead of under it
    scale: float  # of the screen
    pad_scale: float  # of the keypad
    share: float  # the keypad's share of the room along the split, as drawn
    extent: float  # the room along the split in px, for turning a drag into a share


def clamp_share(share: float) -> float:
    return max(MIN_SHARE, min(MAX_SHARE, share))


def handheld_plan(
    viewport_w: float | None,
    viewport_h: float | None,
    width_units: float,
    height_units: float,
    sizing: Sizing = Sizing(),  # noqa: B008 - frozen, so one shared default is safe
) -> HandheldPlan:
    """The arrangement and scales for the window. The screen matters more than the keys, so by
    default the keypad is drawn at `DEFAULT_RATIO` of the screen's scale, the pair as large as the
    window allows. Once the splitter is used the keypad has a fixed share of the room instead, and
    each part scales to its own space. `zoom` then enlarges or shrinks both, so they may no longer
    fit the window."""
    zoom = max(MIN_ZOOM, min(MAX_ZOOM, sizing.zoom))
    pad_w0, pad_h0 = keypad_size(width_units, height_units)
    ratio = DEFAULT_RATIO
    pad_w, pad_h = round(pad_w0 * ratio), round(pad_h0 * ratio)
    portrait = (max(SCREEN_W, pad_w), SCREEN_H + GAP + SPLITTER + pad_h)
    landscape = (SCREEN_W + GAP + SPLITTER + pad_w, max(SCREEN_H, pad_h))
    if not viewport_w or not viewport_h:  # the window size is not known yet
        return HandheldPlan(False, zoom, zoom * ratio, 0.5, 1.0)
    room_w = max(viewport_w - 2 * MARGIN, 1)
    room_h = max(viewport_h - 2 * MARGIN - sizing.bar, 1)

    def fit(size: tuple[int, int]) -> float:
        return min(room_w / size[0], room_h / size[1])

    side = fit(landscape) > fit(portrait)
    if side:
        extent, pad0, screen0, across, pad_across, screen_across = (
            room_w - GAP - SPLITTER, pad_w0, SCREEN_W, room_h, pad_h0, SCREEN_H,
        )  # fmt: skip
    else:
        extent, pad0, screen0, across, pad_across, screen_across = (
            room_h - GAP - SPLITTER, pad_h0, SCREEN_H, room_w, pad_w0, SCREEN_W,
        )  # fmt: skip
    extent = max(extent, 1)
    if sizing.share is None:
        fitted = max(MIN_SCALE, min(MAX_SCALE, fit(landscape if side else portrait)))
        share = pad0 * fitted * ratio / extent
        return HandheldPlan(side, fitted * zoom, fitted * ratio * zoom, share, extent)
    share = clamp_share(sizing.share)
    pad_px = share * extent
    scale = min((extent - pad_px) / screen0, across / screen_across)
    pad_scale = min(pad_px / pad0, across / pad_across)
    top = MAX_SCALE
    return HandheldPlan(
        side,
        max(MIN_PART_SCALE, min(top, scale)) * zoom,
        max(MIN_PART_SCALE, min(top, pad_scale)) * zoom,
        share,
        extent,
    )


def computer_screen_height(viewport_h: float | None) -> float:
    """The Computer-mode screen fills the window below the toolbar (at least 300 px)."""
    return max(300.0, (viewport_h or 800) - BAR_H - 2 * MARGIN - 8)
