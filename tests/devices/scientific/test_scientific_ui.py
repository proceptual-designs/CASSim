# Requirements traced here: FR-FX-UI-001, FR-FX-UI-002, FR-FX-UI-003, FR-FX-TUT-001
"""Unit and headless UI tests for CASSim fx Flet view and user interactions."""

from collections.abc import Callable
from types import SimpleNamespace

from cassim.devices.scientific.ui import mount
from cassim.devices.scientific.ui.app import ScientificApp


class DummyPage:
    def __init__(self) -> None:
        self.views: list[object] = []
        self.dialog: object = None

    def update(self) -> None:
        pass

    def show_dialog(self, dlg: object) -> None:
        self.dialog = dlg

    def pop_dialog(self) -> None:
        self.dialog = None


class DummyShell:
    def __init__(self) -> None:
        self.page = DummyPage()
        self.update_label = "Check for Updates"
        self.changed = lambda: None
        self.home: Callable[[], None] | None = lambda: None
        self.notices: list[tuple[str, str]] = []

    def notice(self, title: str, message: str) -> None:
        self.notices.append((title, message))

    def activate_update(self) -> None:
        pass

    def help(self) -> None:
        pass

    def about(self) -> None:
        pass

    async def pick_file(self, *args: object, **kwargs: object) -> str | None:
        return None

    async def save_file(self, *args: object, **kwargs: object) -> None:
        pass

    def copy(self, text: str) -> None:
        pass

    def link(self, fragment: str) -> str:
        return f"https://example.test/#/{fragment}"


def test_mount_scientific_app() -> None:
    shell = DummyShell()
    app = mount(shell)  # ty: ignore[invalid-argument-type]
    assert isinstance(app, ScientificApp)
    assert len(shell.page.views) == 1
    assert app.menu_visible is True
    assert app.tutorials_visible is True
    assert app.state.mode == "COMP"
    assert app.lcd_result.value == "0"


def test_toggle_menu_bar() -> None:
    shell = DummyShell()
    app = mount(shell)  # ty: ignore[invalid-argument-type]

    # Toggle menu off
    app.toggle_menu_bar(SimpleNamespace())
    assert app.menu_visible is False
    assert app.top_menu_bar.visible is False
    assert app.restore_menu_button.visible is True

    # Toggle menu back on
    app.toggle_menu_bar(SimpleNamespace())
    assert app.menu_visible is True
    assert app.top_menu_bar.visible is True
    assert app.restore_menu_button.visible is False


def test_toggle_tutorials() -> None:
    shell = DummyShell()
    app = mount(shell)  # ty: ignore[invalid-argument-type]

    # Toggle off
    app.toggle_tutorials(SimpleNamespace())
    assert app.tutorials_visible is False
    assert app.tutorial_sidebar.visible is False

    # Toggle on
    app.toggle_tutorials(SimpleNamespace())
    assert app.tutorials_visible is True
    assert app.tutorial_sidebar.visible is True


def test_keypad_click_and_calculation() -> None:
    shell = DummyShell()
    app = mount(shell)  # ty: ignore[invalid-argument-type]

    app.on_key_press("4")
    app.on_key_press("*")
    app.on_key_press("5")
    app.on_key_press("=")

    assert app.state.result == "20"
    assert app.lcd_result.value == "20"


def test_cycle_mode_and_angle() -> None:
    shell = DummyShell()
    app = mount(shell)  # ty: ignore[invalid-argument-type]

    # Cycle mode COMP -> STAT -> TABLE -> COMP
    assert app.state.mode == "COMP"
    app.cycle_mode(SimpleNamespace())
    assert app.state.mode == "STAT"
    app.cycle_mode(SimpleNamespace())
    assert app.state.mode == "TABLE"
    app.cycle_mode(SimpleNamespace())
    assert app.state.mode == "COMP"

    # Cycle angle DEG -> RAD -> GRA -> DEG
    assert app.state.angle_unit == "DEG"
    app.cycle_angle(SimpleNamespace())
    assert app.state.angle_unit == "RAD"
    app.cycle_angle(SimpleNamespace())
    assert app.state.angle_unit == "GRA"
    app.cycle_angle(SimpleNamespace())
    assert app.state.angle_unit == "DEG"


def test_load_examples() -> None:
    shell = DummyShell()
    app = mount(shell)  # ty: ignore[invalid-argument-type]

    app.load_example("sin(30)")
    assert app.state.result in ("0.5", "1/2")

    app.load_stat_example()
    assert app.state.mode == "STAT"
    assert len(app.state.stat_1var) == 5

    app.load_dms_example()
    assert app.state.expr == "12°34'56\""
    assert app.state.result == "12.58222222"

    app.load_prime_example()
    assert app.state.result == "2³×3²×5"
