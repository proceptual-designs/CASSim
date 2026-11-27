"""The CASSim menu, built once for Home and every app (SDD-15 section 4).

`cassim_sections` returns the menu as data: five sections in a fixed order (navigate, view,
set up, the app, help), each a tuple of `Item`s. An item that cannot be used now is greyed,
never left out, so positions (and the Nspire's menu numbers) do not move; only what is fixed
for the app (Home in this bundle, a keypad, keyboard shortcuts) can leave an item out. Each app
draws the data its own way: `menu_bar_controls` for a Flet menu bar (Home, Pseudocode,
Scientific), the Nspire as a numbered device-style panel. A chosen item's `action` goes first to
`Shell.menu_action`, which does the ones every app shares, and else to the app.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import flet as ft

from cassim.app import about

if TYPE_CHECKING:
    from cassim.app.shell import BrowserOffers
    from cassim.app.theme import Theme

Mark = Literal["", "check", "radio"]
MARKS = {"check": "✓", "radio": "●"}  # drawn before the label when the item is on
NOT_ON_A_PHONE = "Not on a phone"
OFFLINE_LABELS = {
    "checking": "Offline: preparing",
    "ready": "Offline: ready",
    "unavailable": "Offline: unavailable",
    "update_failed": "Update failed",
    "unsupported": "Offline: unknown",
}
# The actions `Shell.menu_action` does for every app; the rest are the app's own.
SHELL_ACTIONS = frozenset(
    {"fullscreen", "install", "uninstall", "update", "offline_status", "help", "about"}
)


@dataclass(frozen=True)
class Item:
    """One menu item. `mark` makes it a toggle (✓, `check`) or one of a choice (●, `radio`),
    drawn when `on`. `shortcut` is a key name (Ctrl+O); `hint` explains a greyed item."""

    label: str
    action: str
    enabled: bool = True
    mark: Mark = ""
    on: bool = False
    shortcut: str = ""
    hint: str = ""


Section = tuple[Item, ...]


@dataclass(frozen=True)
class View:
    """One of the app's views (Computer, Tablet, Handheld). Its action is `view:<id>`."""

    id: str
    label: str
    shortcut: str = ""
    phone: bool = True  # usable on a phone


@dataclass(frozen=True)
class Panel:
    """A panel the app can show or hide (Keypad, Tutorials). Its action is `panel:<id>`."""

    id: str
    label: str
    shown: bool
    enabled: bool = True
    hint: str = ""


@dataclass(frozen=True)
class AppMenu:
    """What an app puts in the CASSim menu: facts fixed for the app, and its current state.
    `view` is the current view's id; `cutout` is whether the app draws under a phone's camera
    cutout (None: the app has no cutout setting); `shortcuts` and `settings` say whether the app
    has those dialogs; `fullscreen` is False on Home, which has no View section."""

    home: bool = False
    views: tuple[View, ...] = ()
    view: str = ""
    panels: tuple[Panel, ...] = ()
    phone: bool = False
    cutout: bool | None = None
    shortcuts: bool = False
    settings: bool = True
    fullscreen: bool = True


HOME_MENU = AppMenu(settings=False, fullscreen=False)


def offline_label(offers: BrowserOffers) -> str:
    return OFFLINE_LABELS.get(offers.offline_state, OFFLINE_LABELS["unsupported"])


def cassim_sections(offers: BrowserOffers, app: AppMenu) -> tuple[Section, ...]:
    """The menu's sections, in the fixed order; empty ones are left out (Home has no View)."""
    product = about.product_name()
    phone = app.phone
    navigate = (Item("Home", "home"),) if app.home else ()
    show: list[Item] = [
        Item(
            f"{v.label} view",
            f"view:{v.id}",
            enabled=v.phone or not phone,
            mark="radio",
            on=v.id == app.view,
            shortcut=v.shortcut,
            hint="" if v.phone or not phone else NOT_ON_A_PHONE,
        )
        for v in app.views
    ]
    show += [
        Item(p.label, f"panel:{p.id}", enabled=p.enabled, mark="check", on=p.shown, hint=p.hint)
        for p in app.panels
    ]
    if app.cutout is not None and phone and offers.installed:
        show.append(Item("Avoid cutout", "cutout", mark="check", on=not app.cutout))
    elif app.fullscreen:
        show.append(
            Item(
                "Fullscreen",
                "fullscreen",
                enabled=offers.can_fullscreen and (offers.in_fullscreen or not offers.standalone),
                mark="check",
                on=offers.in_fullscreen,
            )
        )
    set_up = (
        *((Item("Settings…", "settings"),) if app.settings else ()),
        Item("Appearance…", "appearance"),
        *((Item("Keyboard shortcuts…", "shortcuts"),) if app.shortcuts else ()),
    )
    install = (
        Item(f"Uninstall {product}…", "uninstall")
        if offers.installed
        else Item(f"Install {product}…", "install", enabled=offers.installable)
    )
    the_app = (
        install,
        Item(offers.update_label, "update"),
        Item(offline_label(offers), "offline_status", hint=offers.offline_message),
    )
    help_section = (
        Item("Help (wiki)…", "help", shortcut="F1"),
        Item(f"About {product}…", "about"),
    )
    return tuple(
        section for section in (navigate, tuple(show), set_up, the_app, help_section) if section
    )


def needs_attention_tooltip(offers: BrowserOffers) -> str:
    """The CASSim button's tooltip: why it carries the attention dot, if it does."""
    if offers.update_ready:
        return "CASSim menu: update ready"
    if offers.needs_attention:
        return "CASSim menu: offline setup failed"
    return "CASSim menu"


def cassim_button_content(
    offers: BrowserOffers, theme: Theme, colour: str | None = None
) -> ft.Control:
    """The CASSim menu button's label, with the attention dot when an update is ready or
    offline setup failed (SDD-15 section 3)."""
    label = ft.Text(about.product_name(), color=colour)
    if not offers.needs_attention:
        return label
    dot = ft.Icon(ft.Icons.CIRCLE, size=8, color=theme.attention, semantics_label="attention")
    return ft.Row([label, dot], spacing=4, tight=True)


def menu_bar_controls(
    sections: Sequence[Section], run: Callable[[str], None], theme: Theme
) -> list[ft.Control]:
    """The items of a Flet `SubmenuButton`, with a divider between sections. Marked items show
    ✓ or ● before the label when on, and a blank of the same width when off, so labels line up."""
    marked = any(item.mark for section in sections for item in section)
    controls: list[ft.Control] = []
    for number, section in enumerate(sections):
        if number:
            controls.append(ft.Divider(height=1, thickness=1))
        controls.extend(_menu_bar_item(item, run, theme, marked=marked) for item in section)
    return controls


def _menu_bar_item(
    item: Item, run: Callable[[str], None], theme: Theme, *, marked: bool
) -> ft.MenuItemButton:
    leading = None
    if marked:
        glyph = MARKS[item.mark] if item.mark and item.on else ""
        leading = ft.Container(ft.Text(glyph, size=13), width=16)
    trailing = ft.Text(item.shortcut, size=12, color=theme.menu_hint) if item.shortcut else None
    action = item.action
    return ft.MenuItemButton(
        content=item.label,
        leading=leading,
        trailing=trailing,
        on_click=(lambda _: run(action)) if item.enabled else None,  # None draws it greyed
        tooltip=item.hint or None,
        semantic_label=f"{item.label}, {'on' if item.on else 'off'}" if item.mark else None,
        data=action,
    )


def fill_cassim_menu(
    menu: ft.SubmenuButton,
    offers: BrowserOffers,
    app: AppMenu,
    run: Callable[[str], None],
    theme: Theme,
) -> None:
    """Draw the CASSim menu into a menu bar's button: its label (with the attention dot), its
    tooltip and its items. Called again whenever what the menu shows changes."""
    menu.content = cassim_button_content(offers, theme)
    menu.tooltip = needs_attention_tooltip(offers)
    menu.controls = menu_bar_controls(cassim_sections(offers, app), run, theme)
