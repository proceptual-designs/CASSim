"""CASSim Scientific keys: every key does something, and the computer keyboard reaches them.

Requirements: FR-FX-DSP-004, FR-FX-UI-004 (keyboard), FR-FX-TUT-001.
"""

from __future__ import annotations

import pytest

from cassim.app.keyboard import key_name
from cassim.devices.scientific import DEVICE
from cassim.devices.scientific import keys as k
from cassim.devices.scientific.layout import to_text
from cassim.devices.scientific.state import ScientificState


def _snapshot(state: ScientificState) -> tuple[object, ...]:
    return (
        state.display().text(),
        to_text(state.display().input, cursor=True),
        tuple(sorted(state.annunciators().items())),
        state.screen,
        state.menu,
        state.hyp,
        state.mode,
    )


LAYERS = [
    (spec.id, layer)
    for spec in k.ALL_KEYS
    for layer, label in (("plain", spec.label), ("shift", spec.shift), ("alpha", spec.alpha))
    if label
    and not (layer != "plain" and spec.id in (k.SHIFT, k.ALPHA))
    # INS and STAT act in the STAT editor (tested in test_scientific_stat.py)
    and (spec.id, layer) not in ((k.DEL, "shift"), ("1", "shift"))
]


@pytest.mark.parametrize(("key", "layer"), LAYERS)
def test_every_labelled_key_does_something(key: str, layer: str) -> None:
    """The review found √, x², MODE, the D-pad, RCL and most SHIFT keys silently ignored: every
    label printed on the keypad must now change what the calculator shows or holds."""
    state = ScientificState()
    for setup in ("1", "2", k.ADD, "3", k.EQ, "7"):  # an answer and a new entry to act on
        state.press(setup)
    if key in (k.UP, k.DOWN):
        state.press(k.EQ)  # ▲ ▼ recall history after an answer
        if key == k.DOWN:
            state.press(k.UP)
    before = _snapshot(state)
    if layer == "shift":
        state.press(k.SHIFT)
    elif layer == "alpha":
        state.press(k.ALPHA)
    state.press(key)
    assert _snapshot(state) != before, f"{layer} {key} changed nothing"


def test_the_keypad_names_each_key_once() -> None:
    ids = [spec.id for spec in k.ALL_KEYS]
    assert len(ids) == len(set(ids))
    assert len(ids) == 50


def test_every_keyboard_binding_presses_real_keys() -> None:
    specials = {k.HOME, k.END, k.REL_EQ, k.REL_LT, k.REL_GT}
    for name, binding in k.COMPUTER.items():
        if binding.action == "copy":
            continue
        assert binding.action == "place", name
        for key in k.sequence(binding):
            assert key in k.KEYS_BY_ID or key in specials, (name, key)


@pytest.mark.parametrize(
    ("raw", "mods", "expected"),
    [
        ("Slash", {"ctrl": True}, (k.FRAC,)),
        ("F1", {}, (k.SHIFT,)),
        ("F2", {}, (k.ALPHA,)),
        ("m", {"ctrl": True}, (k.MODE,)),
        ("s", {}, (k.SIN,)),
        ("s", {"shift": True}, (k.SHIFT, k.SIN)),
        ("1", {"shift": True}, (k.SHIFT, k.XINV)),  # ! is x!
        ("5", {"shift": True}, (k.SHIFT, k.LPAREN)),  # % is SHIFT (
        ("6", {"shift": True}, (k.POW,)),  # ^
        ("Enter", {}, (k.EQ,)),
        ("Numpad Enter", {}, (k.EQ,)),
        ("Backspace", {}, (k.DEL,)),
        ("Escape", {}, (k.AC,)),
        ("Arrow Up", {}, (k.UP,)),
        ("x", {}, (k.ALPHA, k.RPAREN)),
    ],
)
def test_browser_key_events_reach_the_keypad(
    raw: str, mods: dict[str, bool], expected: tuple[str, ...]
) -> None:
    """FR-FX-UI-004: the key names Flet sends map to the keys a student would press."""
    name = key_name(raw, **mods)
    assert name is not None
    assert k.sequence(k.COMPUTER[name]) == expected


def test_only_command_shortcuts_are_kept_from_the_browser() -> None:
    """The published page blocks the browser's default for the profile's shortcuts; typed
    characters must still reach text fields, so only multi-character names are listed."""
    assert DEVICE.profile.computer == k.COMMANDS
    assert all(len(name) > 1 for name in k.COMMANDS)
    assert "F1" in k.COMMANDS
    assert "ctrl+/" in k.COMMANDS
    assert "s" not in k.COMMANDS


def test_tab_is_not_bound() -> None:
    """Tab moves the browser's focus; binding it as well made Enter press a focused button."""
    assert "Tab" not in k.COMPUTER
    assert "shift+Tab" not in k.COMPUTER


def test_the_device_uses_its_id_for_storage() -> None:
    """Decision 0032 item 9: a device's keys live under its own prefix."""
    assert DEVICE.storage == "scientific."
    assert DEVICE.help.endswith(".html")
