"""Colours for the views. Dark is the default (SRS); a user-editable config file is M2e."""

from collections.abc import Mapping
from dataclasses import dataclass, field


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
    key_styles: Mapping[str, tuple[str, str]] = field(default_factory=dict, compare=False)
    shift_label: str = "#e8b04a"  # the shift layer's small label (ctrl uses `key_label`)
    menu_hint: str = "#a9c4e0"

    def key_colours(self, style: str) -> tuple[str, str]:
        return self.key_styles.get(style, (self.key, self.key_text))


DARK = Theme(
    background="#14161a",
    screen="#e6ecdf",
    screen_text="#10140c",
    title_bar="#2f4a63",
    accent="#4da3ff",
    key="#2b2f36",
    key_text="#f2f4f7",
    key_label="#7fb2e8",
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
        "ctrl": ("#3f7fc4", "#ffffff"),
    },
)
