# Requirements traced here: NFR-PORT-003
"""The screen sizes every app shares (SDD-15 section 8.2): phone, narrow, dialog width and touch
targets, in one place (`cassim.app.sizes`)."""

from types import SimpleNamespace

import pytest

from cassim.app import sizes


@pytest.mark.parametrize(
    ("width", "height", "phone"),
    [
        (390, 844, True),  # a phone upright
        (844, 390, True),  # and on its side
        (768, 1024, False),  # a tablet
        (1280, 800, False),
        (599, None, True),
        (600, None, False),
        (None, None, False),  # before Flet knows: a computer
        (0, 0, False),
    ],
)
def test_a_phone_is_a_short_side_under_600(
    width: float | None, height: float | None, *, phone: bool
) -> None:
    assert sizes.is_phone(width, height) is phone
    assert sizes.page_is_phone(SimpleNamespace(width=width, height=height)) is phone


def test_narrow_is_under_900_wide() -> None:
    assert sizes.is_narrow(899)
    assert not sizes.is_narrow(900)
    assert not sizes.is_narrow(None)


def test_a_dialog_fits_the_window() -> None:
    """The content width is what the dialog would like, less on a small window, never under
    200 px, and leaves room for the dialog's own margins (a 360 px phone has 232 px)."""
    assert sizes.dialog_width(1280, 420) == 420
    assert sizes.dialog_width(360, 420) == 360 - sizes.DIALOG_MARGIN
    assert sizes.dialog_width(250, 420) == sizes.DIALOG_MIN
    assert sizes.dialog_width(None, 420) == 420
    assert sizes.dialog_width(SimpleNamespace(width=500, height=800), 420) == 500 - 128


def test_touch_targets_are_48_px_and_40_by_mouse() -> None:
    """SDD-15 section 8.3 (Material): 48 px in Tablet and Handheld, 40 px in Computer view."""
    assert sizes.target(touch=True) == 48
    assert sizes.target(touch=False) == 40
