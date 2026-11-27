# Requirements traced here: FR-PWA-004, FR-PROF-016, FR-DEV-008, NFR-LEG-002
"""The CASSim menu every app shares (SDD-15 section 4): its sections in a fixed order, items
greyed rather than hidden, ✓ and ● marks, the shell's own actions, and the update item."""

from types import SimpleNamespace
from typing import Any, cast

import flet as ft
import pytest

from cassim.app import about
from cassim.app.cassim_menu import (
    HOME_MENU,
    NOT_ON_A_PHONE,
    AppMenu,
    Item,
    Panel,
    View,
    cassim_button_content,
    cassim_sections,
    menu_bar_controls,
    needs_attention_tooltip,
)
from cassim.app.shell import BrowserOffers, Shell
from cassim.app.theme import DARK

VIEWS = (
    View("computer", "Computer", shortcut="Alt+Shift+C", phone=False),
    View("handheld", "Handheld", shortcut="Alt+Shift+H"),
)
APP = AppMenu(
    home=True,
    views=VIEWS,
    view="computer",
    panels=(Panel("keypad", "Keypad", shown=True),),
    cutout=True,
    shortcuts=True,
)


def labels(sections: tuple[tuple[Item, ...], ...]) -> list[list[str]]:
    return [[item.label for item in section] for section in sections]


def test_the_sections_are_in_the_fixed_order() -> None:
    """Navigate, View, Set up, the app, Help (SDD-15 section 4.1)."""
    assert labels(cassim_sections(BrowserOffers(), APP)) == [
        ["Home"],
        ["Computer view", "Handheld view", "Keypad", "Fullscreen"],
        ["Settings…", "Appearance…", "Keyboard shortcuts…"],
        ["Install CASSim…", "Check for updates", "Offline: unknown"],
        ["Help (wiki)…", "About CASSim…"],
    ]


@pytest.mark.parametrize(
    "offers",
    [
        BrowserOffers(),
        BrowserOffers(installable=True, can_fullscreen=True),
        BrowserOffers(offline_state="unavailable", offline_retry=True),
        BrowserOffers(update_ready=True, in_fullscreen=True, can_fullscreen=True),
    ],
)
def test_positions_never_move_whatever_the_browser_offers(offers: BrowserOffers) -> None:
    """An item that cannot be used is greyed, not left out, so the keys stay put."""
    actions = [[item.action for item in section] for section in cassim_sections(offers, APP)]
    assert actions == [
        ["home"],
        ["view:computer", "view:handheld", "panel:keypad", "fullscreen"],
        ["settings", "appearance", "shortcuts"],
        ["install", "update", "offline_status"],
        ["help", "about"],
    ]


def test_unavailable_items_are_greyed() -> None:
    (_, view, _, the_app, _) = cassim_sections(BrowserOffers(standalone=True), APP)
    assert not view[-1].enabled  # Fullscreen: the installed app already fills the screen
    assert not the_app[0].enabled  # Install: the browser has not offered it
    (_, view, _, the_app, _) = cassim_sections(
        BrowserOffers(installable=True, can_fullscreen=True), APP
    )
    assert view[-1].enabled
    assert the_app[0].enabled


def test_views_are_a_choice_and_panels_are_toggles() -> None:
    """● on the current view, ✓ on a panel that is shown; labels never swap (section 6)."""
    (_, view, *_) = cassim_sections(BrowserOffers(), APP)
    assert [(i.mark, i.on) for i in view[:3]] == [
        ("radio", True),
        ("radio", False),
        ("check", True),
    ]
    hidden = AppMenu(views=VIEWS, view="handheld", panels=(Panel("keypad", "Keypad", False),))
    (view, *_) = cassim_sections(BrowserOffers(), hidden)
    assert [(i.label, i.on) for i in view[:3]] == [
        ("Computer view", False),
        ("Handheld view", True),
        ("Keypad", False),
    ]


def test_a_view_shortcut_is_shown_and_a_phone_greys_computer_view() -> None:
    phone = AppMenu(views=VIEWS, view="handheld", phone=True)
    (view, *_) = cassim_sections(BrowserOffers(), phone)
    assert (view[0].enabled, view[0].hint, view[0].shortcut) == (
        False,
        NOT_ON_A_PHONE,
        "Alt+Shift+C",
    )
    assert view[1].enabled


@pytest.mark.parametrize("cutout", [True, False])
def test_an_installed_phone_has_avoid_cutout_in_place_of_fullscreen(cutout: bool) -> None:
    app = AppMenu(views=VIEWS, view="handheld", phone=True, cutout=cutout)
    (view, *_) = cassim_sections(BrowserOffers(installed=True, standalone=True), app)
    assert (view[-1].label, view[-1].mark, view[-1].on) == ("Avoid cutout", "check", not cutout)
    (view, *_) = cassim_sections(BrowserOffers(), app)  # not installed: Fullscreen
    assert view[-1].label == "Fullscreen"


def test_the_installed_app_offers_uninstall_in_the_same_place() -> None:
    (*_, the_app, _) = cassim_sections(BrowserOffers(installed=True), APP)
    assert (the_app[0].label, the_app[0].action, the_app[0].enabled) == (
        "Uninstall CASSim…",
        "uninstall",
        True,
    )


@pytest.mark.parametrize(
    ("offers", "label"),
    [
        (BrowserOffers(), "Check for updates"),
        (BrowserOffers(update_fetching=True), "Fetching update…"),
        (BrowserOffers(update_ready=True), "Reload to update"),
    ],
)
def test_one_update_item_with_three_states(offers: BrowserOffers, label: str) -> None:
    """FR-PWA-004: checking and reloading share one row."""
    items = [item for section in cassim_sections(offers, APP) for item in section]
    assert [(i.action, i.label) for i in items if i.action == "update"] == [("update", label)]


def test_offline_status_has_no_separate_retry_item() -> None:
    """Retry is offered in the offline status's notice, so the numbers do not shift."""
    offers = BrowserOffers(
        offline_state="unavailable", offline_message="Files incomplete.", offline_retry=True
    )
    (*_, the_app, _) = cassim_sections(offers, APP)
    assert (the_app[-1].label, the_app[-1].hint) == ("Offline: unavailable", "Files incomplete.")
    assert all(item.action != "retry_offline" for s in cassim_sections(offers, APP) for item in s)


def test_home_shows_its_subset() -> None:
    assert labels(cassim_sections(BrowserOffers(), HOME_MENU)) == [
        ["Appearance…"],
        ["Install CASSim…", "Check for updates", "Offline: unknown"],
        ["Help (wiki)…", "About CASSim…"],
    ]


def test_the_testing_site_uses_its_own_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(about.bundle, "SOURCE", "CASSim-calc")
    (*_, the_app, help_section) = cassim_sections(BrowserOffers(installed=True), APP)
    assert the_app[0].label == "Uninstall CASSimᵝ…"
    assert help_section[-1].label == "About CASSimᵝ…"


# ---- drawn in a menu bar ----------------------------------------------------------------------


def test_a_menu_bar_has_dividers_marks_and_greyed_items() -> None:
    run: list[str] = []
    controls = menu_bar_controls(cassim_sections(BrowserOffers(), APP), run.append, DARK)
    assert sum(isinstance(c, ft.Divider) for c in controls) == 4
    items = [c for c in controls if isinstance(c, ft.MenuItemButton)]
    marks = {
        cast("str", i.content): cast("Any", i.leading).content.value for i in items if i.leading
    }
    assert marks["Computer view"] == "●"
    assert marks["Handheld view"] == ""  # a blank of the same width keeps labels in line
    assert marks["Keypad"] == "✓"
    install = next(i for i in items if i.content == "Install CASSim…")
    assert install.on_click is None  # greyed
    about_item = next(i for i in items if i.content == "About CASSim…")
    cast("Any", about_item).on_click(None)
    assert run == ["about"]
    help_item = next(i for i in items if i.content == "Help (wiki)…")
    assert cast("ft.Text", help_item.trailing).value == "F1"


def test_the_cassim_button_shows_the_attention_dot() -> None:
    quiet = cassim_button_content(BrowserOffers(), DARK)
    assert isinstance(quiet, ft.Text)
    loud = cassim_button_content(BrowserOffers(update_ready=True), DARK)
    assert isinstance(loud, ft.Row)
    dot = loud.controls[-1]
    assert isinstance(dot, ft.Icon)
    assert dot.color == DARK.attention
    assert needs_attention_tooltip(BrowserOffers(update_ready=True)) == "CASSim menu: update ready"
    assert (
        needs_attention_tooltip(BrowserOffers(offline_state="unavailable"))
        == "CASSim menu: offline setup failed"
    )
    assert needs_attention_tooltip(BrowserOffers()) == "CASSim menu"


# ---- the shell does the shared items ------------------------------------------------------------


class RecordingShell(SimpleNamespace):
    def __init__(self, offers: BrowserOffers, *, unsaved: bool = False) -> None:
        super().__init__(offers=offers, done=[], has_unsaved=lambda: unsaved)

    def notice(self, title: str, message: str) -> None:
        self.done.append(("notice", title, message))

    def confirm(self, title: str, message: str, action: str, accept: Any) -> None:
        self.done.append(("confirm", title, action))

    def __getattr__(self, name: str) -> Any:
        return lambda *args: self.done.append((name, *args))


@pytest.mark.parametrize(
    ("action", "called"),
    [
        ("fullscreen", "toggle_fullscreen"),
        ("install", "install"),
        ("uninstall", "uninstall"),
        ("about", "about"),
    ],
)
def test_the_shell_does_the_shared_items(action: str, called: str) -> None:
    shell = RecordingShell(BrowserOffers())
    assert Shell.menu_action(cast("Shell", shell), action)
    assert shell.done == [(called,)]


def test_help_opens_the_app_page_and_unknown_actions_are_the_apps() -> None:
    shell = RecordingShell(BrowserOffers())
    assert Shell.menu_action(cast("Shell", shell), "help", "Scientific-calculator.html")
    assert shell.done == [("help", "Scientific-calculator.html")]
    assert not Shell.menu_action(cast("Shell", shell), "panel:tutorials")


def test_offline_status_offers_retry_only_when_setup_failed() -> None:
    failed = RecordingShell(
        BrowserOffers(
            offline_state="unavailable", offline_message="Files incomplete.", offline_retry=True
        )
    )
    Shell.show_offline_status(cast("Shell", failed))
    assert failed.done == [("confirm", "Offline status", "Retry")]
    ready = RecordingShell(BrowserOffers(offline_state="ready", offline_message="Ready."))
    Shell.show_offline_status(cast("Shell", ready))
    assert ready.done == [("notice", "Offline status", "Ready.")]


@pytest.mark.parametrize("fetching", [False, True])
def test_update_checks_until_an_update_is_ready(fetching: bool) -> None:
    """The Fetching Update row stays active and checks again."""
    shell = RecordingShell(BrowserOffers(update_fetching=fetching))
    Shell.activate_update(cast("Shell", shell))
    assert shell.done == [("check_for_updates",)]


def test_a_ready_update_reloads_at_once_with_nothing_unsaved() -> None:
    shell = RecordingShell(BrowserOffers(update_ready=True))
    Shell.activate_update(cast("Shell", shell))
    assert shell.done == [("reload_update",)]


def test_a_ready_update_asks_first_when_work_is_unsaved() -> None:
    """FR-PWA-004: a waiting update never reloads over unsaved work without asking, in any app."""
    shell = RecordingShell(BrowserOffers(update_ready=True), unsaved=True)
    Shell.activate_update(cast("Shell", shell))
    assert shell.done == [("confirm", "Reload CASSim?", "Reload")]
