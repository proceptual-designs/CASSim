"""Screen sizes every app shares (SDD-15 section 8.2): what counts as a phone or a narrow window,
how wide a dialog may be, and how big a touch target must be (section 8.3).

Plain numbers in and out, so the rules are tested without a browser. A size Flet does not know
yet (None or 0, before the first resize) counts as a computer's.
"""

from __future__ import annotations

from typing import Protocol

PHONE_SIDE = 600  # px: a window whose shorter side is under this is a phone (decision 0013)
NARROW_WIDTH = 900  # px: under this, Computer view stacks its columns as Handheld does
# An AlertDialog keeps 40 px either side of itself and pads its content by 24 px, so its content
# may be no wider than the window less 128 px, or it runs off a phone's screen.
DIALOG_MARGIN = 2 * 40 + 2 * 24
DIALOG_MIN = 200  # px: the narrowest a dialog's content gets (a 360 px phone leaves 232)
TOUCH_TARGET = 48  # px: the least a control takes by touch in Tablet and Handheld (Material)
POINTER_TARGET = 40  # px: the least in Computer view, where a mouse is more precise
DEFAULT_WIDTH = 1200.0  # px: the width assumed before Flet reports one


class Sized(Protocol):
    @property
    def width(self) -> float | None: ...

    @property
    def height(self) -> float | None: ...


def is_phone(width: float | None, height: float | None = None) -> bool:
    """A phone-sized window: its shorter known side is under `PHONE_SIDE` (so a phone held
    sideways is one too)."""
    sides = [side for side in (width, height) if side]
    return bool(sides) and min(sides) < PHONE_SIDE


def is_narrow(width: float | None) -> bool:
    """Too narrow for Computer view's columns side by side."""
    return bool(width) and float(width or 0) < NARROW_WIDTH


def page_is_phone(page: Sized) -> bool:
    return is_phone(getattr(page, "width", None), getattr(page, "height", None))


def dialog_width(page: Sized | float | None, preferred: float) -> float:
    """A dialog's content width: `preferred`, or what a narrow window leaves round it."""
    width = page if isinstance(page, int | float) or page is None else page.width
    room = float(width or DEFAULT_WIDTH) - DIALOG_MARGIN
    return max(float(DIALOG_MIN), min(preferred, room))


# The views every app may offer (SDD-15 section 8.1), by their ids in the CASSim menu
COMPUTER, TABLET, HANDHELD = "computer", "tablet", "handheld"
VIEWS = (COMPUTER, TABLET, HANDHELD)


def starting_view(width: float | None, height: float | None, saved: str | None = None) -> str:
    """The view to open in (SDD-15 sections 8.2 and 8.4): on a phone, Handheld upright and Tablet
    on its side, whatever was saved; elsewhere the saved Start in, or Computer."""
    if is_phone(width, height):
        return TABLET if width and height and width > height else HANDHELD
    return saved if saved in VIEWS else COMPUTER


def target(*, touch: bool) -> int:
    """The least size of a control: `TOUCH_TARGET` in Tablet and Handheld, else `POINTER_TARGET`."""
    return TOUCH_TARGET if touch else POINTER_TARGET
