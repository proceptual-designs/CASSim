"""Dialogs that build a command from named fields (FR-CALC-005, FR-DEV-007).

On the handheld many menu items with several arguments (Normal Cdf…, Create Matrix…, Derivative at
a Point…) open a dialog: the user fills in labelled boxes and the command is pasted, sometimes run
at once. A `Wizard` is that dialog as data. The profile supplies them; the GUI draws the fields and
calls `bindings` with what was typed. Nothing here knows which device it belongs to.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from cassim.device.editor import MARK as CURSOR
from cassim.device.keys import Binding

__all__ = ["CURSOR", "Field", "Wizard"]


@dataclass(frozen=True)
class Field:
    """One box of a dialog. `choices` makes it a drop-down of (value, label) pairs; `whole`
    requires a whole number in that range; `toggle` makes a checkbox with values "0" and "1"."""

    name: str
    label: str
    default: str = ""
    choices: tuple[tuple[str, str], ...] = ()
    whole: tuple[int, int] | None = None
    toggle: bool = False

    def problem(self, value: str) -> str | None:
        """Why `value` will not do, or None."""
        if self.toggle and value not in ("0", "1"):
            return f"{self.label}: choose whether to enable this option"
        if self.choices and value not in {choice for choice, _ in self.choices}:
            return f"{self.label}: choose one of the options"
        if self.whole is None:
            return None
        low, high = self.whole
        if not value.strip().lstrip("-").isdigit() or not low <= int(value) <= high:
            return f"{self.label}: a whole number from {low} to {high}"
        return None


@dataclass(frozen=True)
class Wizard:
    """A dialog that pastes `text` (a `str.format` pattern over the field names) or, if `build`
    is given, what it returns; a `CURSOR` in it is where the cursor is left. `template` pastes a
    2D template instead (`matrix:{rows},{cols}`); `steps` replays key actions, for a template
    with text round it. `run` presses Enter afterwards, as the handheld does for the
    distribution dialogs.

    A *live* dialog (Finance Solver) also has `calculate(values, field)`, which returns the values
    with `field` worked out from the others (or raises `ValueError` with a message for the user).
    The GUI calls it when Enter is pressed in a box or Calculate is clicked. Values may carry
    extra keys, such as which field was solved last, for `build` to read."""

    title: str
    fields: tuple[Field, ...]
    text: str = ""
    template: str = ""
    run: bool = False
    build: Callable[[Mapping[str, str]], str] | None = None
    steps: Callable[[Mapping[str, str]], list[Binding]] | None = None  # key actions to replay
    calculate: Callable[[Mapping[str, str], str], dict[str, str]] | None = None
    copies: tuple[tuple[str, str], ...] = ()  # (source, target): typing in source sets target
    # Variables a live dialog leaves behind after each calculation: name -> number, from the values
    store: Callable[[Mapping[str, str]], dict[str, float]] | None = None
    # Checks across the fields (Window Settings: XMin below XMax); messages for the user
    check: Callable[[Mapping[str, str]], list[str]] | None = None
    # Key actions Esc replays: the dialog before this one, such as the Data Input Method box
    # (emulator run 6, R6-C3). Empty: Esc just closes, like Cancel.
    back: tuple[Binding, ...] = ()

    def defaults(self) -> dict[str, str]:
        return {field.name: field.default for field in self.fields}

    def problems(self, values: Mapping[str, str]) -> list[str]:
        found = (field.problem(values.get(field.name, "").strip()) for field in self.fields)
        problems = [problem for problem in found if problem]
        if not problems and self.check is not None:
            problems = self.check({name: value.strip() for name, value in values.items()})
        return problems

    def bindings(self, values: Mapping[str, str]) -> list[Binding]:
        """The key actions that paste the command (and run it). Check `problems` first."""
        filled = {field.name: "" for field in self.fields}
        filled.update((name, value.strip()) for name, value in values.items())
        if self.template:
            return [Binding("template", self.template.format_map(filled))]
        if self.steps is not None:
            return [*self.steps(filled), *([Binding("enter")] if self.run else [])]
        text = self.build(filled) if self.build is not None else self.text.format_map(filled)
        if not text:
            return []  # nothing to paste (a live dialog closed before any calculation)
        bindings = [Binding("insert_linear", text)]
        if self.run:
            bindings.append(Binding("enter"))
        return bindings
