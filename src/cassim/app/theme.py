"""Built-in colour themes and their editable colour values."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace


@dataclass(frozen=True)
class Theme:
    background: str
    screen: str
    screen_text: str
    title_bar: str
    accent: str
    key: str
    key_text: str
    key_label: str
    modifier_on: str
    error: str
    selection: str
    # A keypad key's style (`digit`, `fn`, `nav`...) -> (fill, label colour); others use `key`.
    key_styles: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    shift_label: str = "#e8b04a"  # the shift layer's small label (ctrl uses `key_label`)
    ctrl_label_dark: str = "#a6d2ff"
    ctrl_label_light: str = "#245c96"
    shift_label_light: str = "#965200"
    shift_outline: str = "#aa6500"
    key_outline: str = "#3d8053"  # x, y, z and enter
    ctrl_on: str = "#c6ddf7"
    ctrl_on_text: str = "#143a60"
    key_edge: str = "#14161a"
    status_text: str = "#ffd479"
    home_card: str = "#2b2f36"
    panel_text: str = "#f2f4f7"
    panel_accent: str = "#a6d2ff"
    menu_accent: str = "#a6d2ff"
    title_text: str = "#ffffff"
    accent_text: str = "#ffffff"
    sheet_axis: str = "#4d5a49"
    sheet_grid: str = "#66725f"
    sheet_header: str = "#cfd8c7"
    sheet_edit: str = "#ffffff"
    menu_hint: str = "#a9c4e0"
    menu_disabled: str = "#7d8894"  # a menu placeholder for a command CASSim does not have yet
    attention: str = "#e53935"  # the dot on the CASSim button (SDD-15 section 3)
    warning: str = "#f5c518"  # the warning triangle; a lesson's "not yet" feedback
    success: str = "#22c55e"  # a lesson's "well done" feedback
    chip_edge: str = "#6b7482"  # the outline of a status chip
    line_highlight: str = "#2f3f55"  # the current line in a code view
    # Graphs page function colours in the device's order (f1 blue, f2 red, f3 black = the
    # screen text, then magenta, green, orange, brown), drawn on the screen colour.
    graph_blue: str = "#1f4fe0"
    graph_red: str = "#d01c1c"
    graph_magenta: str = "#c0189c"
    graph_green: str = "#1e7b1e"
    graph_orange: str = "#c25400"
    graph_brown: str = "#8b4513"
    # Data & Statistics plots, one colour per plotted series, in order
    plot_1: str = "#4f9dff"
    plot_2: str = "#ff6b6b"
    plot_3: str = "#5fd068"
    plot_4: str = "#ffb84d"
    plot_5: str = "#c77dff"
    plot_6: str = "#4dd0e1"
    shadow: str = "#000000"  # shadows and the dimmed layer behind a menu, used translucent
    pointer_fill: str = "#ffffff"  # the arrow the keypad's centre key moves
    pointer_edge: str = "#000000"
    on_error: str = "#ffffff"  # text on an error message's colour
    on_error_muted: str = "#ffd0cc"
    problem_text: str = "#ff8a80"  # what is wrong with a dialog's field
    code_background: str = "#282a36"  # behind the code editor (its Dracula colours)

    def key_colours(self, style: str) -> tuple[str, str]:
        return self.key_styles.get(style, (self.key, self.key_text))


DARK = Theme(
    background="#14161a",
    screen="#e6ecdf",
    screen_text="#10140c",
    title_bar="#2f4a63",
    accent="#2462a1",
    key="#2b2f36",
    key_text="#f2f4f7",
    key_label="#a6d2ff",
    modifier_on="#e0a030",
    error="#b3261e",
    selection="#bcd3f0",
    key_styles={
        "digit": ("#4a515c", "#ffffff"),
        "fn": ("#2b2f36", "#f2f4f7"),
        "nav": ("#dfe3e8", "#14161a"),
        "pad": ("#dfe3e8", "#14161a"),
        "enter": ("#dfe3e8", "#14161a"),
        "alpha": ("#cfd4db", "#14161a"),
        "ctrl": ("#2462a1", "#ffffff"),
    },
)

LIGHT = replace(
    DARK,
    background="#f1f3f5",
    key_edge="#f1f3f5",
    status_text="#364b60",
    home_card="#ffffff",
    panel_text="#14161a",
    panel_accent="#245c96",
    attention="#c62828",
    problem_text="#b3261e",
    warning="#965200",
    success="#1e7b1e",
    chip_edge="#7d8894",
    line_highlight="#dbe7f4",
)
HIGH_CONTRAST = replace(
    DARK,
    background="#000000",
    screen="#ffffff",
    screen_text="#000000",
    key="#000000",
    key_text="#ffffff",
    key_edge="#ffffff",
    status_text="#ffffff",
    home_card="#000000",
    attention="#ff5252",
    warning="#ffd600",
    success="#00e676",
    chip_edge="#ffffff",
    line_highlight="#003a70",
    key_styles={
        "digit": ("#000000", "#ffffff"),
        "fn": ("#000000", "#ffffff"),
        "nav": ("#ffffff", "#000000"),
        "pad": ("#ffffff", "#000000"),
        "enter": ("#ffffff", "#000000"),
        "alpha": ("#ffffff", "#000000"),
        "ctrl": ("#2462a1", "#ffffff"),
    },
)
THEMES: dict[str, Theme] = {"Dark": DARK, "Light": LIGHT, "High contrast": HIGH_CONTRAST}
THEME_NAMES = tuple(THEMES)  # the presets, in the order every Appearance dialog shows them
DEFAULT_THEME = "Dark"  # FR-THEME-001
COLOUR_FIELDS = tuple(item.name for item in fields(Theme) if item.name != "key_styles")
STYLE_FIELDS = tuple(f"{style}.{part}" for style in DARK.key_styles for part in ("fill", "text"))
THEME_FIELDS = (*COLOUR_FIELDS, *STYLE_FIELDS)
_HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")
SRGB_THRESHOLD = 0.04045


def theme_colours(theme: Theme) -> dict[str, str]:
    colours = {name: getattr(theme, name) for name in COLOUR_FIELDS}
    for style, (fill, text) in theme.key_styles.items():
        colours[f"{style}.fill"] = fill
        colours[f"{style}.text"] = text
    return colours


def valid_theme_overrides(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(name, str)
        and name in THEME_FIELDS
        and isinstance(colour, str)
        and _HEX.fullmatch(colour) is not None
        for name, colour in value.items()
    )


def themed(name: str, overrides: Mapping[str, str]) -> Theme:
    base = THEMES[name]
    colours = theme_colours(base)
    colours.update(overrides)
    styles = {
        style: (colours[f"{style}.fill"], colours[f"{style}.text"]) for style in base.key_styles
    }
    return replace(base, **{key: colours[key] for key in COLOUR_FIELDS}, key_styles=styles)


def luminance(colour: str) -> float:
    components = [int(colour[n : n + 2], 16) / 255 for n in (1, 3, 5)]
    linear = [
        v / 12.92 if v <= SRGB_THRESHOLD else ((v + 0.055) / 1.055) ** 2.4 for v in components
    ]
    return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


# The colours the Appearance dialog offers to pick from (`cassim.app.appearance`)
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

# Text on a colour of the user's own: near-black on a light one, white on a dark one
INK_ON_LIGHT = "#111111"
INK_ON_DARK = "#ffffff"
