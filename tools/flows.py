"""Scripted exam-style flows: a student's whole session, key by key (M2 exit criterion).

`corpus/flows/*.yaml` holds each flow as data. `run_flow` plays one through the app's own state
(`AppState`, the same code the GUI drives), typing characters and pressing keys as a student does,
so it covers the keymaps, the editor, the history, Ans and recall, undo, problems and the engine
together. `tests/e2e/test_flows_browser.py` plays the flows marked `browser: true` in the real
static site and reads the results from the console.

    python -m tools.flows            # run every flow headless and print the outcome

Step kinds (any step may add `expect`, `error` or `entry`):
- `type: TEXT`   type the text (`{R}` is the Right arrow, to leave an exponent), then Enter
                 (`enter: false` leaves it in the entry line);
                 `approx: true` ends with Ctrl+Enter instead.
- `keys: "Up ctrl+Enter"`   press keys, space separated; `Up`, `Down`, `Left`, `Right` are arrows.
- `keypad: "6 times 7 enter"`   press the on-screen keypad (handheld; headless only).
- `action: add_problem`   a document action by name (headless only).
- `settings: {angle: degree}`   change Document Settings (headless only).
- `expect: TEXT`   the last result equals this (read as maths, so `x=3 or x=1` matches
                   `x=1 or x=3`);
                   `compare: text` demands the same text, `compare: numeric` (with `tol`) a number.
- `error: true`   the last result is an error or the error dialog is showing (`error_contains`
                   names it; press any key to dismiss the dialog).
- `entry: TEXT`   the entry line now reads this.
- `variable: {name: a, text: "5", problem: 1}`   a variable in a Problem (default: the current one).

Expected values come from simulator-captured corpus cases where one exists (the step's `from` names
it); the rest are worked by hand and say so (`hand: true` on the flow).
"""

from __future__ import annotations

import io
import sys
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from cassim.core.session import Session, same_value
from cassim.core.settings import PRESETS, Settings, updated
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.state import AppState

FLOWS = Path(__file__).parents[1] / "corpus" / "flows"
DEFAULT_TOLERANCE = 1.0e-7

type Flow = dict[str, Any]
type Step = dict[str, Any]

_ARROWS = {"Up": "Arrow Up", "Down": "Arrow Down", "Left": "Arrow Left", "Right": "Arrow Right"}
_MODIFIERS = {"ctrl": "ctrl", "alt": "alt", "shift": "shift", "meta": "meta"}
# US-layout shifted characters and the key that makes them (the browser has no other way to type
# them: Flutter reports the key, not the character; decisions 0015 and 0024).
SHIFTED = {
    **dict(zip("!@#$%^&*()", "1234567890", strict=True)),
    "_": "-",
    "+": "=",
    "{": "[",
    "}": "]",
    ":": ";",
    '"': "'",
    "<": ",",
    ">": ".",
    "?": "/",
    "|": "\\",
    "~": "`",
}


@dataclass(frozen=True, slots=True)
class Outcome:
    flow_id: str
    passed: bool
    reason: str = ""


def load_flows() -> Iterator[Flow]:
    for path in sorted(FLOWS.glob("*.yaml")):
        yield from yaml.safe_load(path.read_text(encoding="utf-8"))["flows"]


def flow_settings(flow: Flow) -> Settings:
    return updated(PRESETS[flow.get("course", "methods")], flow.get("settings", {}))


RIGHT = "{R}"  # in typed text: the Right arrow, which a student presses to leave an exponent


def split_text(text: str) -> list[str]:
    """The keys of a typed text: each character, with `{R}` as the Right arrow. A `^` opens an
    exponent and everything after it goes in until Right is pressed, as on the handheld."""
    pieces: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith(RIGHT, index):
            pieces.append(RIGHT)
            index += len(RIGHT)
        else:
            pieces.append(text[index])
            index += 1
    return pieces


def parse_keys(spec: str) -> list[tuple[str, dict[str, bool]]]:
    """`"Up ctrl+Enter"` as (key, modifiers) pairs for `AppState.key_event`."""
    pressed: list[tuple[str, dict[str, bool]]] = []
    for token in spec.split():
        *mods, key = token.split("+") if token != "+" and not token.endswith("++") else [token]
        pressed.append((_ARROWS.get(key, key), {_MODIFIERS[m]: True for m in mods}))
    return pressed


def playwright_key(key: str, mods: dict[str, bool]) -> str:
    """The same key as Playwright spells it (`Arrow Up` is `ArrowUp`, `ctrl` is `Control`)."""
    names = {"ctrl": "Control", "alt": "Alt", "shift": "Shift", "meta": "Meta"}
    return "+".join([*(names[m] for m in mods), key.replace(" ", "")])


def matches(expected: str, actual: str, settings: Settings, compare: str, tol: float) -> bool:
    """Is `actual` what the flow expects? Both are read as maths with CAS on, so the order of
    `or` branches and the way a fraction is written do not matter."""
    if compare == "text":
        return actual == expected
    reader = Session(Settings(angle=settings.angle))
    wanted, got = reader.eval(expected), reader.eval(actual)
    if wanted.value is None or got.value is None:
        return actual == expected
    return same_value(got.value, wanted.value, tol if compare == "numeric" else None)


class Player:
    """Plays steps into an `AppState`."""

    def __init__(self, flow: Flow) -> None:
        self.flow = flow
        self.state = AppState()
        self.state.document.use(flow_settings(flow))
        self.settings = flow_settings(flow)

    @property
    def calculator(self):  # noqa: ANN201
        calculator = calculator_of(self.state.document.current)
        assert calculator is not None
        return calculator

    def last(self) -> tuple[str, str | None]:
        """The last result's text and its error, if it has one."""
        calculator = self.calculator
        if calculator.error is not None:  # a dialog (a syntax error) waiting for a key
            return "", calculator.error
        history = calculator.history
        return (history[-1].result.text, history[-1].result.error) if history else ("", None)

    def press(self, spec: str) -> None:
        for key, mods in parse_keys(spec):
            self.state.key_event(key, **mods)

    def play(self, step: Step) -> str | None:
        """Do one step and check what it expects; a failure's reason, or None."""
        if "type" in step:
            self.press_text(step["type"])
            if step.get("enter", True):
                self.press("ctrl+Enter" if step.get("approx") else "Enter")
        if "keys" in step:
            self.press(step["keys"])
        if "keypad" in step:
            for name in step["keypad"].split():
                self.state.press_keypad(name)
        if "action" in step:
            self.state.run_action(step["action"])
        if "settings" in step:
            self.settings = updated(self.settings, step["settings"])
            self.state.document.use(replace(self.settings))
        return self.check(step)

    def press_text(self, text: str) -> None:
        for piece in split_text(text):
            if piece == RIGHT:
                self.state.key_event("Arrow Right")
            else:
                self.state.key_event(piece, shift=piece.isupper())

    def check(self, step: Step) -> str | None:
        label = step.get("type") or step.get("keys") or step.get("keypad") or step.get("action", "")
        text, error = self.last()
        if step.get("error"):
            wanted = step.get("error_contains", "")
            if error is None or wanted not in error:
                return f"{label}: expected an error {wanted!r}, got {error or text!r}"
        if "expect" in step:
            if error is not None:
                return f"{label}: {error}"
            compare = step.get("compare", "canonical")
            if not matches(
                str(step["expect"]),
                text,
                self.settings,
                compare,
                step.get("tol", DEFAULT_TOLERANCE),
            ):
                return f"{label}: got {text}, expected {step['expect']}"
        if "entry" in step and self.calculator.editor.linear() != step["entry"]:
            return f"{label}: entry line reads {self.calculator.editor.linear()!r}"
        if "variable" in step:
            return self.check_variable(label, step["variable"])
        return None

    def check_variable(self, label: str, wanted: dict[str, Any]) -> str | None:
        document = self.state.document
        number = int(wanted["problem"]) - 1 if "problem" in wanted else document.problem
        problem = document.problems[number]
        rows = {row.name: row.text for row in problem.session.variables()}
        if rows.get(wanted["name"]) != str(wanted["text"]):
            return (
                f"{label}: {wanted['name']} is {rows.get(wanted['name'])!r}, not {wanted['text']!r}"
            )
        return None


def run_flow(flow: Flow) -> Outcome:
    player = Player(flow)
    for step in flow["steps"]:
        if failure := player.play(step):
            return Outcome(flow["id"], passed=False, reason=failure)
    return Outcome(flow["id"], passed=True)


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    outcomes = [run_flow(flow) for flow in load_flows()]
    for outcome in outcomes:
        print(("pass  " if outcome.passed else "FAIL  ") + outcome.flow_id, outcome.reason)
    failed = sum(not o.passed for o in outcomes)
    print(f"{len(outcomes) - failed} of {len(outcomes)} flows pass")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
