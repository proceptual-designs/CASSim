"""Clicking the title-bar status cycles the settings (Rad/Deg, Auto/Approx, Real/Rect/Polar)."""

from collections.abc import Callable, Iterator

import flet as ft
import pytest

from cassim.app.theme import DARK
from cassim.core.settings import next_choice
from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.views import STATUS_FIELDS, CalculatorView


def walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    children: list[ft.Control] = []
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        children.append(content)
    children.extend(getattr(control, "controls", None) or [])
    for child in children:
        yield from walk(child)


class Harness:
    """A view wired like the app: a click on a field changes the document and redraws."""

    def __init__(self) -> None:
        self.state = AppState(mode=Mode.HANDHELD)
        self.view = CalculatorView(self.state, DARK, on_setting=self.cycle)
        self.view.refresh()

    def cycle(self, name: str) -> None:
        self.state.document.set(**{name: next_choice(self.state.document.settings, name)})
        self.view.refresh()

    def words(self) -> list[str]:
        return [c.value for c in walk(self.view.status) if isinstance(c, ft.Text) and c.value]

    def click(self, word: str) -> None:
        for control in walk(self.view.status):
            if (
                isinstance(control, ft.Container)
                and isinstance(control.content, ft.Text)
                and control.content.value == word
            ):
                handler: Callable[[object], object] | None = control.on_click  # ty: ignore[invalid-assignment]
                assert handler is not None
                handler(None)
                return
        raise AssertionError(f"no clickable {word} in {self.words()}")

    def run(self, text: str) -> str:
        for ch in text:
            self.state.key_event(ch)
        self.state.key_event("Enter")
        return self.state.screen().lines[-1].text


def test_status_shows_each_setting_as_its_own_clickable_field() -> None:
    h = Harness()
    assert h.words() == ["RAD", "AUTO", "REAL"]
    clickable = [c for c in walk(h.view.status) if isinstance(c, ft.Container) and c.on_click]
    assert len(clickable) == len(STATUS_FIELDS) == 3


def test_angle_toggles_both_ways_and_changes_results() -> None:
    h = Harness()
    h.click("RAD")
    assert h.words()[0] == "DEG"
    assert h.run("sin(90)") == "1"
    h.click("DEG")
    assert h.words()[0] == "RAD"


def test_calculation_mode_toggles_and_approximates() -> None:
    h = Harness()
    h.click("AUTO")
    assert h.words()[1] == "APPROX"
    assert "." in h.run("1/3")
    h.click("APPROX")
    assert h.words()[1] == "AUTO"


def test_domain_cycles_real_rect_polar() -> None:
    h = Harness()
    seen = []
    for _ in range(4):
        seen.append(h.words()[2])
        h.click(h.words()[2])
    assert seen == ["REAL", "RECT", "POLAR", "REAL"]


def test_click_applies_to_every_problem() -> None:
    h = Harness()
    h.state.document.add_problem()
    h.click("RAD")
    assert {p.session.settings.angle for p in h.state.document.problems} == {"degree"}


def test_extra_status_words_are_not_clickable() -> None:
    h = Harness()
    h.state.caps = True
    h.view.refresh()
    assert h.words() == ["CAPS", "RAD", "AUTO", "REAL"]
    caps = h.view.status.controls[0]
    assert isinstance(caps, ft.Text)
    assert caps.size == pytest.approx(h.state.px(12) * 0.65)
    clickable = [c for c in walk(h.view.status) if isinstance(c, ft.Container) and c.on_click]
    assert len(clickable) == 3
