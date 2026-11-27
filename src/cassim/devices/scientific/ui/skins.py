"""CASSim Scientific's own colours for each of CASSim's themes (SDD-14 section 5): the
calculator's body, screen and keys. The page, the menu bar, its chips and the panel text come
from the shared theme, so Home's and every app's choice applies here (SDD-15 section 7.2)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cassim.app.appearance import Appearance


@dataclass(frozen=True)
class Skin:
    page: str  # behind the calculator
    chassis: str
    chassis_edge: str
    badge: str
    badge_sub: str
    lcd: str
    lcd_text: str
    lcd_dim: str  # an unlit status indicator
    lcd_edge: str
    lcd_select: str  # the selected cell's fill (its text is `lcd`)
    fn: tuple[str, str]  # (fill, label)
    num: tuple[str, str]
    nav: tuple[str, str]
    delete: tuple[str, str]
    clear: tuple[str, str]
    equals: tuple[str, str]
    key_edge: str
    shift: str  # SHIFT's label and its yellow legends
    alpha: str  # ALPHA's label and its red legends
    target: str  # the tutorial's next key
    shift_key: str  # SHIFT's own label on its key
    alpha_key: str
    panel: str
    panel_text: str
    panel_muted: str
    panel_edge: str
    bar: str
    bar_text: str
    chip: str


SLATE = Skin(
    page="#14161a",
    chassis="#1e2229",
    chassis_edge="#363c48",
    badge="#cbd5e1",
    badge_sub="#8a94a6",
    lcd="#dce5d3",
    lcd_text="#121810",
    lcd_dim="#bcc6b2",
    lcd_edge="#0d0f12",
    lcd_select="#121810",
    fn=("#282c35", "#f0f2f5"),
    num=("#363c48", "#ffffff"),
    nav=("#3b4250", "#f0f2f5"),
    delete=("#43a047", "#ffffff"),
    clear=("#2e7d32", "#ffffff"),
    equals=("#4a5568", "#ffffff"),
    key_edge="#14161a",
    shift="#e5a93c",
    alpha="#ef7b7b",
    target="#38bdf8",
    shift_key="#e5a93c",
    alpha_key="#ef7b7b",
    panel="#1b1f26",
    panel_text="#f2f4f7",
    panel_muted="#a3adbd",
    panel_edge="#363c48",
    bar="#14161a",
    bar_text="#f2f4f7",
    chip="#2b2f36",
)

STUDIO_LIGHT = Skin(
    page="#f1f3f5",
    chassis="#e9ecef",
    chassis_edge="#ced4da",
    badge="#343a40",
    badge_sub="#5c656e",
    lcd="#e8edf2",
    lcd_text="#1a202c",
    lcd_dim="#c8d0d9",
    lcd_edge="#adb5bd",
    lcd_select="#1a202c",
    fn=("#495057", "#ffffff"),
    num=("#f8f9fa", "#1a202c"),
    nav=("#dee2e6", "#1a202c"),
    delete=("#2e7d32", "#ffffff"),
    clear=("#1b5e20", "#ffffff"),
    equals=("#343a40", "#ffffff"),
    key_edge="#adb5bd",
    shift="#965200",
    alpha="#b42318",
    target="#0284c7",
    shift_key="#ffc966",
    alpha_key="#ffa8a8",
    panel="#ffffff",
    panel_text="#14161a",
    panel_muted="#5c656e",
    panel_edge="#ced4da",
    bar="#14161a",
    bar_text="#f2f4f7",
    chip="#2b2f36",
)

CLASSROOM = Skin(
    page="#000000",
    chassis="#121316",
    chassis_edge="#ffffff",
    badge="#ffffff",
    badge_sub="#ffffff",
    lcd="#f4f6f8",
    lcd_text="#000000",
    lcd_dim="#d0d4d8",
    lcd_edge="#ffffff",
    lcd_select="#000000",
    fn=("#ffffff", "#000000"),
    num=("#ffffff", "#000000"),
    nav=("#ffffff", "#000000"),
    delete=("#37474f", "#ffffff"),
    clear=("#c62828", "#ffffff"),
    equals=("#0050b3", "#ffffff"),
    key_edge="#000000",
    shift="#ffb020",
    alpha="#7cc0ff",
    target="#38bdf8",
    shift_key="#8a5a00",
    alpha_key="#0050b3",
    panel="#000000",
    panel_text="#ffffff",
    panel_muted="#e0e0e0",
    panel_edge="#ffffff",
    bar="#000000",
    bar_text="#ffffff",
    chip="#000000",
)

SKINS: dict[str, Skin] = {"Dark": SLATE, "Light": STUDIO_LIGHT, "High contrast": CLASSROOM}


def skin_for(appearance: Appearance) -> Skin:
    """The calculator's colours for the shared theme, with the parts outside the calculator
    (page, menu bar, chips, panel text) taken from the theme and its customised colours."""
    theme = appearance.theme
    return replace(
        SKINS.get(appearance.theme_name, SLATE),
        page=theme.background,
        bar=theme.background,
        bar_text=theme.panel_text,
        chip=theme.home_card,
        panel_text=theme.panel_text,
    )
