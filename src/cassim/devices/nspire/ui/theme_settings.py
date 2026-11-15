"""Editable appearance presets in System Settings."""

from collections.abc import Callable

import flet as ft

from cassim.app.theme import THEME_FIELDS, THEMES, theme_colours, valid_theme_overrides
from cassim.devices.nspire.ui.state import System

PALETTE = (
    "#000000",
    "#14161a",
    "#2b2f36",
    "#4a515c",
    "#808080",
    "#cfd4db",
    "#f1f3f5",
    "#ffffff",
    "#143a60",
    "#245c96",
    "#2462a1",
    "#7fb2e8",
    "#a6d2ff",
    "#c6ddf7",
    "#27603c",
    "#3d8053",
    "#78b590",
    "#e8b04a",
    "#aa6500",
    "#965200",
    "#e0a030",
    "#b3261e",
    "#6a428a",
    "#f0d7b4",
)


def pick_colour(page: ft.Page, title: str, selected: Callable[[str], None]) -> None:
    def choose(colour: str) -> None:
        page.pop_dialog()
        selected(colour)
        page.update()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.CIRCLE,
                        icon_color=colour,
                        style=ft.ButtonStyle(side=ft.BorderSide(1, "#808080")),
                        tooltip=colour,
                        on_click=lambda _, value=colour: choose(value),
                    )
                    for colour in PALETTE
                ],
                wrap=True,
                width=220,
            ),
            actions=[ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog())],
        )
    )


def colour_rows(
    page: ft.Page, boxes: dict[str, ft.TextField]
) -> tuple[dict[str, ft.IconButton], list[ft.Control]]:
    swatches: dict[str, ft.IconButton] = {}

    def pick(name: str) -> None:
        def set_colour(colour: str) -> None:
            boxes[name].value = colour
            boxes[name].error = None
            swatches[name].icon_color = colour

        pick_colour(page, name.replace(".", " ").replace("_", " ").title(), set_colour)

    def typed(name: str) -> None:
        value = (boxes[name].value or "").strip()
        if valid_theme_overrides({name: value}):
            swatches[name].icon_color = value
            page.update()

    rows: list[ft.Control] = []
    for name in THEME_FIELDS:
        box = boxes[name]
        swatch = ft.IconButton(
            icon=ft.Icons.CIRCLE,
            icon_color=box.value,
            style=ft.ButtonStyle(side=ft.BorderSide(1, "#808080")),
            tooltip=f"Choose {box.label}",
            on_click=lambda _, key=name: pick(key),
        )
        swatches[name] = swatch
        box.on_change = lambda _, key=name: typed(key)
        rows.append(ft.Row([box, swatch], spacing=8, tight=True))
    return swatches, rows


def theme_settings_dialog(
    page: ft.Page, system: System, on_change: Callable[[], None]
) -> ft.AlertDialog:
    drafts = {name: dict(colours) for name, colours in system.theme_overrides.items()}
    selected = [system.theme_name]
    boxes = {
        name: ft.TextField(
            label=name.replace(".", " ").replace("_", " ").title(),
            value=value,
            width=220,
            dense=True,
        )
        for name, value in theme_colours(THEMES[selected[0]]).items()
    }
    choice = ft.Dropdown(
        label="Theme",
        value=selected[0],
        options=[ft.DropdownOption(key=name, text=name) for name in THEMES],
        width=220,
    )
    message = ft.Text(
        "Tap a swatch or type #RRGGBB. Custom colours may reduce contrast.",
        size=12,
    )
    swatches, rows = colour_rows(page, boxes)

    def show(name: str) -> None:
        values = theme_colours(THEMES[name])
        values.update(drafts.get(name, {}))
        for key, box in boxes.items():
            box.value = values[key]
            box.error = None
            swatches[key].icon_color = values[key]

    def collect() -> bool:
        values = {key: (box.value or "").strip() for key, box in boxes.items()}
        if not valid_theme_overrides(values):
            for name, box in boxes.items():
                box.error = None if valid_theme_overrides({name: values[name]}) else "Use #RRGGBB"
            page.update()
            return False
        defaults = theme_colours(THEMES[selected[0]])
        drafts[selected[0]] = {
            name: value for name, value in values.items() if value != defaults[name]
        }
        return True

    def change_choice(_: object) -> None:
        next_name = choice.value
        if next_name not in THEMES or not collect():
            choice.value = selected[0]
            page.update()
            return
        selected[0] = next_name
        show(next_name)
        page.update()

    def reset(_: object) -> None:
        drafts.pop(selected[0], None)
        show(selected[0])
        page.update()

    def save(_: object) -> None:
        if not collect():
            return
        system.theme_name = selected[0]
        system.theme_overrides = {name: values for name, values in drafts.items() if values}
        system.theme_error = ""
        page.pop_dialog()
        on_change()

    choice.on_select = change_choice
    show(selected[0])
    dialog = ft.AlertDialog(
        title=ft.Text("Appearance"),
        content=ft.Column(
            [ft.Container(height=6), choice, message, *rows],
            scroll=ft.ScrollMode.AUTO,
            height=min(450, max(180, (page.height or 700) - 200)),
            width=280,
            spacing=8,
        ),
        actions=[
            ft.TextButton("Reset preset", on_click=reset),
            ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
            ft.TextButton("Save", on_click=save),
        ],
    )
    page.show_dialog(dialog)
    return dialog
