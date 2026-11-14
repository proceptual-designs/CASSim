# Requirements traced here: FR-DEV-005
"""The pointer the keypad's centre key steers like a joystick: no GUI needed."""

import pytest

from cassim.device.pointer import DEAD, HIDE, SPEED, Pointer


def armed(width: float = 320.0, height: float = 200.0) -> Pointer:
    pointer = Pointer(width, height)
    pointer.press()
    return pointer


def test_it_is_hidden_until_used_and_first_shows_at_the_centre():
    pointer = Pointer(320, 200)
    assert not pointer.visible
    assert pointer.click() is None  # hidden: the key does its usual select
    assert not pointer.step(0.1)
    pointer.press()
    assert pointer.visible
    assert (pointer.x, pointer.y) == (160, 100)


def test_a_press_inside_the_dead_zone_does_not_move_it():
    pointer = armed()
    pointer.drag(DEAD / 2, 0)
    assert pointer.velocity() == (0.0, 0.0)
    assert not pointer.step(0.1)
    assert (pointer.x, pointer.y) == (160, 100)


def test_holding_off_centre_keeps_it_moving_faster_with_more_travel():
    pointer = armed()
    pointer.drag(0.3, 0)
    slow = pointer.velocity()[0]
    pointer.drag(1.5, 0)  # past full travel: full speed, no more
    assert pointer.velocity() == pytest.approx((SPEED * 320, 0.0))
    assert 0 < slow < SPEED * 320
    pointer.drag(0.3, 0)
    for _ in range(5):  # the finger stays still, the pointer keeps going
        assert pointer.step(0.05)
    assert pointer.x == pytest.approx(160 + 5 * 0.05 * slow)
    assert pointer.y == 100


def test_it_moves_in_the_direction_of_the_travel():
    pointer = armed()
    pointer.drag(-0.6, 0.8)  # a whole key width, down and to the left
    vx, vy = pointer.velocity()
    assert vx < 0 < vy
    assert vy / vx == pytest.approx(-0.8 / 0.6)


def test_it_stops_at_the_screen_edges():
    pointer = armed()
    pointer.drag(1, 0)
    for _ in range(40):
        pointer.step(0.1)
    assert pointer.x == 319
    pointer.drag(0, -1)
    for _ in range(40):
        pointer.step(0.1)
    assert (pointer.x, pointer.y) == (319, 0)
    pointer.step(HIDE * 2)  # still pushing against the edge: still in use
    assert pointer.visible


def test_it_hides_a_while_after_it_stops():
    pointer = armed()
    pointer.drag(0.5, 0)
    pointer.step(0.1)
    pointer.release()
    assert not pointer.step(HIDE / 2)
    assert pointer.visible
    assert pointer.click() is not None  # a click keeps it showing a while longer
    assert not pointer.step(HIDE * 0.9)
    assert pointer.step(HIDE * 0.2)  # changed: it hid
    assert not pointer.visible


def test_a_held_finger_keeps_it_showing():
    pointer = armed()
    pointer.step(HIDE * 3)
    assert pointer.visible


def test_a_click_gives_its_place_and_a_hidden_one_does_not():
    pointer = armed()
    pointer.drag(1, 1)
    pointer.step(0.05)
    place = pointer.click()
    assert place == (pointer.x, pointer.y)
    pointer.hide()
    assert pointer.click() is None


def test_it_comes_back_where_it_was_and_stays_on_a_smaller_screen():
    pointer = armed()
    pointer.drag(1, 1)
    pointer.step(0.1)
    pointer.release()
    where = (pointer.x, pointer.y)
    pointer.hide()
    pointer.press()
    assert (pointer.x, pointer.y) == where
    pointer.resize(100, 80)
    assert (pointer.x, pointer.y) == (99, 79)
