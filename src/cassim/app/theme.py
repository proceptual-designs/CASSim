"""Colours for the views. Dark is the default (SRS); a user-editable config file is M2e."""

from dataclasses import dataclass


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
)
