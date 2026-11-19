"""The all-in-one Home shell.

FR-PROF-010, FR-PROF-011, FR-PROF-012, FR-PROF-013, FR-PROF-014, FR-PROF-015,
FR-PROF-016, FR-PROF-017, FR-PROF-018, NFR-PERF-007.
"""

from __future__ import annotations

import asyncio
import base64
import json
import zlib
from types import SimpleNamespace
from typing import Any, cast

import flet as ft
import pytest
from tests.app.test_splitter_drag import handheld_app

from cassim.app.home import WELCOME, Home, HomeChoice, home_choices
from cassim.app.main import LAST_DEVICE_KEY, Application, shared_device, startup_device
from cassim.app.shell import BrowserOffers
from cassim.app.theme import DARK, LIGHT
from cassim.devices.nspire.ui.app import cassim_items


def fragment(device: str) -> str:
    raw = json.dumps({"device": device, "name": "Shared"}).encode()
    return "/" + "doc=" + base64.urlsafe_b64encode(zlib.compress(raw)).decode().rstrip("=")


def test_home_lists_all_choices_and_only_enables_bundled_apps() -> None:
    choices = home_choices(("nspire", "pseudocode"))
    assert [choice.title for choice in choices] == [
        "Nspire",
        "Classpad",
        "Prime",
        "Pseudocode & Python",
        "Scientific",
    ]
    assert [choice.available for choice in choices] == [True, False, False, True, False]


def test_home_uses_the_published_app_icon() -> None:
    """FR-PWA-001: Home and the installed app use the same bundle-specific icon artwork."""
    mark = Home._mark()
    assert isinstance(mark, ft.Image)
    assert mark.src == "icons/icon-192.png"


def test_light_home_cards_are_not_coloured_like_dark_keypad_keys() -> None:
    """FR-PROF-011/017: the Home cards follow the shell theme instead of the keypad."""
    shell = FakeShell()
    home = Home(cast(Any, shell), lambda _item: None)
    home.card_width = 560
    choice = HomeChoice("nspire", "Nspire", "Handheld graphing and CAS", True)

    home.theme = DARK
    dark = cast(ft.Button, home._card(choice))
    home.theme = LIGHT
    light = cast(ft.Button, home._card(choice))

    assert dark.style is not None
    assert light.style is not None
    assert dark.style.bgcolor == DARK.home_card
    assert light.style.bgcolor == LIGHT.home_card
    assert light.style.bgcolor != DARK.key
    assert WELCOME == "Hi! Choose a CAS calculator or algorithm tool to start."


def test_startup_resumes_a_valid_device_and_repairs_missing_or_invalid_preferences() -> None:
    devices = ("nspire", "pseudocode")
    assert startup_device("/", "pseudocode", "all", devices) == "pseudocode"
    assert startup_device("/", None, "all", devices) is None
    assert startup_device("/", "removed", "all", devices) is None


def test_single_device_bundles_bypass_home() -> None:
    assert startup_device("/", None, "tin", ("nspire",)) == "nspire"
    assert startup_device("/", "classpad", "tin", ("nspire",)) == "nspire"


def test_share_link_selects_its_device_before_the_remembered_preference() -> None:
    route = fragment("pseudocode")
    assert shared_device(route) == "pseudocode"
    assert startup_device(route, "nspire", "all", ("nspire", "pseudocode")) == "pseudocode"


def test_debug_route_still_opens_the_first_device_for_existing_e2e_flows() -> None:
    assert startup_device("/debug", None, "all", ("nspire",)) == "nspire"


class FakePage(SimpleNamespace):
    def __init__(self) -> None:
        super().__init__(controls=[])

    def run_task(self, handler: Any, *args: object) -> None:
        asyncio.run(handler(*args))


class FakeShell:
    def __init__(self, saved: str | None = None) -> None:
        self.saved = saved
        self.writes: list[tuple[str, str]] = []
        self.route = "/"
        self.page: ft.Page = cast("ft.Page", FakePage())
        self.available_devices: tuple[str, ...] = ()
        self.home: Any = None
        self.device: object | None = None

    async def read_global(self, key: str) -> str | None:
        assert key == LAST_DEVICE_KEY
        return self.saved

    def write_global(self, key: str, value: str) -> None:
        self.writes.append((key, value))

    def select(self, device: object) -> None:
        self.device = device


class FakeHome:
    started = 0

    def __init__(self, shell: FakeShell, choose: Any) -> None:
        self.shell = shell
        self.choose = choose

    async def start(self) -> None:
        FakeHome.started += 1


class FakeMounted:
    def __init__(self) -> None:
        self.options: dict[str, object] | None = None
        self.unmounted = 0

    async def start(self, **options: object) -> None:
        self.options = options

    def unmount(self) -> None:
        self.unmounted += 1


def test_first_visit_draws_home_without_loading_a_device(monkeypatch: pytest.MonkeyPatch) -> None:
    shell = FakeShell()
    monkeypatch.setattr("cassim.app.main.Home", FakeHome)
    monkeypatch.setattr("cassim.app.main.devices.load", lambda _: pytest.fail("device loaded"))
    monkeypatch.setattr("cassim.app.main.import_module", lambda _: pytest.fail("UI imported"))
    app = Application(shell.page, shell=cast(Any, shell), available=("nspire",))
    FakeHome.started = 0

    asyncio.run(app.start())

    assert FakeHome.started == 1
    assert app.active is None


def test_selecting_an_app_loads_only_its_ui_and_remembers_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shell = FakeShell("nspire")
    mounted = FakeMounted()
    device = SimpleNamespace(id="nspire", ui="cassim.devices.nspire.ui")
    monkeypatch.setattr("cassim.app.main.devices.load", lambda item: device)
    monkeypatch.setattr(
        "cassim.app.main.import_module",
        lambda name: SimpleNamespace(mount=lambda selected: mounted),
    )
    app = Application(shell.page, options={"view": "computer"}, shell=cast(Any, shell))

    asyncio.run(app.open_device("nspire"))

    assert shell.device is device
    assert mounted.options == {"view": "computer"}
    assert shell.writes == [(LAST_DEVICE_KEY, "nspire")]


def test_a_direct_debug_launch_is_also_remembered(monkeypatch: pytest.MonkeyPatch) -> None:
    shell = FakeShell()
    shell.route = "/debug"
    mounted = FakeMounted()
    device = SimpleNamespace(id="nspire", ui="cassim.devices.nspire.ui")
    monkeypatch.setattr("cassim.app.main.devices.load", lambda _item: device)
    monkeypatch.setattr(
        "cassim.app.main.import_module",
        lambda _name: SimpleNamespace(mount=lambda _shell: mounted),
    )
    app = Application(shell.page, shell=cast(Any, shell), available=("nspire",))

    asyncio.run(app.start())

    assert shell.writes == [(LAST_DEVICE_KEY, "nspire")]


def test_home_menu_action_is_only_added_for_the_all_in_one_app() -> None:
    regular = cassim_items(handheld=True, offers=BrowserOffers())
    with_home = cassim_items(handheld=True, offers=BrowserOffers(), home=True)
    assert all(item.arg != "home" for item in regular)
    assert with_home[0].label == "Home"
    assert with_home[0].arg == "home"


def test_single_device_controller_does_not_offer_home() -> None:
    shell = FakeShell()
    app = Application(
        shell.page,
        shell=cast(Any, shell),
        bundle_name="tin",
        available=("nspire",),
    )
    assert shell.home is None
    assert app.bundle_name == "tin"


def test_nspire_dispatches_home_without_importing_app_selection() -> None:
    app, _ = handheld_app()
    selected: list[bool] = []
    app.shell.home = lambda: selected.append(True)

    app.show_dialog("home")

    assert selected == [True]
