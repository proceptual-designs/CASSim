"""FR-GRAPH-002: Window / Zoom windows against the emulator captures (graphs D7, D8, D29)."""

import math

import pytest

from cassim.graph.sampling import Window
from cassim.graph.zoom import (
    DECIMAL,
    QUADRANT_1,
    STANDARD,
    TRIG,
    parse_window_value,
    window_text,
    zoom_about,
    zoom_box,
    zoom_data,
    zoom_fit,
    zoom_square,
)


def texts(window: Window) -> list[str]:
    return [
        window_text(value) for value in (window.x_min, window.x_max, window.y_min, window.y_max)
    ]


def test_preset_windows_match_window_settings_after_each_zoom() -> None:
    assert texts(STANDARD) == ["-10", "10", "-6.6666666666667", "6.6666666666667"]
    assert texts(QUADRANT_1) == ["-4", "20", "-2.6666666666667", "13.333333333333"]
    assert texts(TRIG) == ["-2·π", "2·π", "-4.1887902047864", "4.1887902047864"]
    assert texts(DECIMAL) == ["-32", "32", "-21.3", "21.3"]


def test_zoom_in_and_out_halve_and_double_about_the_chosen_point() -> None:
    zoomed = zoom_about(STANDARD, -0.63, -1.385, 0.5)
    assert zoomed.x_max - zoomed.x_min == pytest.approx(10)
    assert (zoomed.x_min + zoomed.x_max) / 2 == pytest.approx(-0.63)
    # graphs2 D8: Out from the Box window about its clicked point
    box = Window(-2.7044025157233, 3.9622641509434, -0.9433962264151, 4.0880503144654)
    out = zoom_about(box, 0.6289308176100, 1.904592381630, 2)
    assert out.x_min == pytest.approx(-6.0377358490567)
    assert out.x_max == pytest.approx(7.2955974842767)
    assert out.y_max - out.y_min == pytest.approx(10.062893081761)


def test_zoom_box_takes_the_two_corners_in_either_order() -> None:
    window = zoom_box((2.0125786163522, 1.7610062893082), (1.3836477987421, 2.3899371069182))
    assert texts(window) == [
        "1.3836477987421",
        "2.0125786163522",
        "1.7610062893082",
        "2.3899371069182",
    ]
    with pytest.raises(ValueError, match="minimums"):
        zoom_box((1, 1), (1, 2))


def test_zoom_square_keeps_x_and_centres_y() -> None:
    """graphs2 D8: after Fit, y -6.9004..27.9044 becomes y -1.3217..5.3449 on a 3:2 screen."""
    window = Window(-5, 5, -6.9004012506668, 27.904413757335)
    square = zoom_square(window, 318, 212)
    assert (square.x_min, square.x_max) == (-5, 5)
    assert square.y_min == pytest.approx(-1.3217330703775, abs=1e-9)
    assert square.y_max == pytest.approx(5.3449335962892, abs=1e-9)
    above = zoom_square(Window(-5, 5, 100, 110), 300, 150)
    assert (above.y_min, above.y_max) == (102.5, 107.5)


def test_zoom_fit_keeps_x_and_pads_the_sampled_y_range() -> None:
    """graphs4 D8: x^2 on the Standard window gives about -10.0012 to 110.0198."""
    fitted = zoom_fit(STANDARD, [lambda x: x * x], 318)
    assert (fitted.x_min, fitted.x_max) == (-10, 10)
    assert fitted.y_min == pytest.approx(-10.0012137898067, rel=1e-3)
    assert fitted.y_max == pytest.approx(110.0197745302515, rel=1e-3)


def test_zoom_fit_skips_undefined_values_and_keeps_an_empty_window() -> None:
    fitted = zoom_fit(STANDARD, [math.log], 200)
    assert fitted.y_max == pytest.approx(math.log(10) + 0.1 * (math.log(10) - math.log(0.1)))
    assert zoom_fit(STANDARD, [], 200) == STANDARD
    flat = zoom_fit(STANDARD, [lambda _x: 2.0], 200)
    assert flat.y_min < 2 < flat.y_max


def test_zoom_data_pads_the_data_range_by_a_tenth() -> None:
    """graphs5 D29: data x 1..8 and y 2.1..16.1 give x 0.3..8.7 and y 0.7..17.5."""
    points = [(1, 2.1), (2, 3.9), (3, 6.2), (8, 16.1)]
    window = zoom_data(STANDARD, points)
    assert window.x_min == pytest.approx(0.3)
    assert window.x_max == pytest.approx(8.7)
    assert window.y_min == pytest.approx(0.7)
    assert window.y_max == pytest.approx(17.5)


def test_zoom_data_without_data_grows_the_window_by_one() -> None:
    """graphs2 D8: Data after Trig with no data gives x +-7.2831853071796."""
    assert texts(zoom_data(TRIG, [])) == [
        "-7.2831853071796",
        "7.2831853071796",
        "-5.1887902047864",
        "5.1887902047864",
    ]
    single = zoom_data(STANDARD, [(2, 3)])
    assert single.x_min < 2 < single.x_max


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("-10", -10),
        ("6.6666666666667", 6.6666666666667),
        ("-2·π", -2 * math.pi),
        ("π", math.pi),
        ("pi/2", math.pi / 2),
        ("3.1ᴇ2", 310),
        ("−4", -4),
        ("+1.5*2", 3),
    ],
)
def test_window_values_parse_back(text: str, value: float) -> None:
    assert parse_window_value(text) == pytest.approx(value)


@pytest.mark.parametrize("text", ["", "x", "1/0", "2**3", "abs(2)", "1e999", "(", "'a'"])
def test_bad_window_values_are_refused(text: str) -> None:
    with pytest.raises(ValueError, match=r"number|empty"):
        parse_window_value(text)


def test_small_values_use_the_exponent_marker() -> None:
    assert window_text(1.5e-7) == "1.5ᴇ-07"
    assert window_text(-math.pi) == "-π"


def test_zoom_fit_covers_every_graph_over_the_window() -> None:
    """Emulator run 7, R7-B4: x², 2·sin(x) and x+1 on x 0 to 10 give y about -12.2008 to
    110.2088, x kept."""
    window = Window(0, 10, -1.6666666666667, 5)
    fitted = zoom_fit(window, [lambda x: x * x, lambda x: 2 * math.sin(x), lambda x: x + 1], 318)
    assert (fitted.x_min, fitted.x_max) == (0, 10)
    assert fitted.y_min == pytest.approx(-12.2007997411759, abs=0.01)
    assert fitted.y_max == pytest.approx(110.208827088125, abs=0.01)
