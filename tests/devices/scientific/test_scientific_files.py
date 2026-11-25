"""Saving, opening and sharing CASSim Scientific calculators.

Requirements: FR-FX-SHR-001 to -006, FR-PROF-009, NFR-SEC-001.
Cited: FR-FX-SHR-001 FR-FX-SHR-002 FR-FX-SHR-003 FR-FX-SHR-004 FR-FX-SHR-005 FR-FX-SHR-006.
"""

from __future__ import annotations

import base64
import json
import zlib

import pytest

from cassim.app.main import shared_device, startup_device
from cassim.devices.scientific import keys as k
from cassim.devices.scientific.state import DocumentFileError, ScientificState
from cassim.doc import serialize, share


def press(*keys: str, state: ScientificState | None = None) -> ScientificState:
    state = state or ScientificState()
    for key in keys:
        state.press(key)
    return state


def column(*numbers: str) -> list[str]:
    out: list[str] = []
    for number in numbers:
        out.extend(k.DOT if ch == "." else ch for ch in number)
        out.append(k.EQ)
    return out


def test_the_file_envelope_is_the_cassim_one() -> None:
    """Decision 0032 item 4: every CASSim file has the same format, schema and a device."""
    from cassim.devices.scientific import state as module  # noqa: PLC0415

    assert module.FORMAT == serialize.FORMAT
    assert module.SCHEMA == serialize.SCHEMA
    assert module.SHARE_PREFIX == share.PREFIX
    assert module.MAX_FRAGMENT == share.MAX_FRAGMENT
    data = json.loads(ScientificState().dumps("Test"))
    assert (data["format"], data["device"], data["name"]) == (
        "cassim-document",
        "scientific",
        "Test",
    )


def test_a_file_round_trip_keeps_everything() -> None:
    """FR-FX-SHR-006 (and the autosave of FR-FX-SHR-001 uses the same text)."""
    state = press(
        k.SHIFT, k.MODE, "4", "7", k.MPLUS, k.SQRT, "2", k.EQ, k.SHIFT, k.RCL, k.NEG,
        k.MODE, "2", "1", *column("3", "1.5", "8"),
    )  # fmt: skip
    text = state.dumps("Lesson 4")
    again = ScientificState()
    assert again.loads(text) == "Lesson 4"
    assert again.setup.angle == "RAD"
    assert float(again.variables["M"]) == 7
    assert again.variables["A"] == state.variables["A"]  # √2 stays exact
    assert again.stat_rows == state.stat_rows
    assert again.mode == "STAT"
    assert again.screen == "stat_editor"


def test_history_is_worked_out_again() -> None:
    """A file holds entries, not answers: opening it recalculates them."""
    state = press("2", k.ADD, "3", k.EQ, "4", k.MUL, "5", k.EQ)
    again = ScientificState()
    again.loads(state.dumps())
    assert again.display().text() == "4×5\n20"
    again.press(k.UP)
    assert again.display().text() == "2+3\n5"
    assert [entry.value for entry in again.history] == [entry.value for entry in state.history]
    assert again.variables["Ans"] == state.variables["Ans"]


def test_share_link_round_trip_and_budget() -> None:
    """FR-FX-SHR-002, -004 and -005: a teacher's 25-row bivariate set fits a link."""
    keys = [k.MODE, "2", "2"]
    for i in range(25):
        keys.extend(column(str(10 + i)))
    keys.extend([k.UP] * 25 + [k.RIGHT])
    for i in range(25):
        keys.extend(column(str(30 + 2 * i + i % 3)))
    state = press(*keys)
    fragment = state.share_fragment("Heights")
    assert fragment.startswith("doc=")
    assert len(fragment) < 2000
    opened = ScientificState()
    assert opened.open_fragment(fragment)
    assert opened.stat_rows == state.stat_rows
    assert opened.mode == "STAT"
    small = press("2", k.FRAC, "3", k.EQ).share_fragment()
    assert 80 <= len(small) <= 300


def test_a_share_link_opens_this_device_from_home() -> None:
    """FR-PROF-015: the shell sends a link naming the device to it."""
    fragment = ScientificState().share_fragment()
    assert shared_device(fragment) == "scientific"
    assert startup_device(f"/{fragment}", "all", ("nspire", "pseudocode", "scientific")) == (
        "scientific"
    )
    assert startup_device("/scientific", "all", ("nspire", "scientific")) == "scientific"


def test_table_function_travels_in_a_link() -> None:
    state = press(
        k.MODE, "3", "2", k.ALPHA, k.RPAREN, k.X2, k.SUB, "3", k.ALPHA, k.RPAREN, k.ADD, "1"
    )
    opened = ScientificState()
    opened.open_fragment(state.share_fragment())
    assert opened.screen == "table_fx"
    assert opened.display().text() == "f(X)=\n2X²−3X+1"


def _fragment(document: object) -> str:
    packed = zlib.compress(json.dumps(document).encode())
    return "doc=" + base64.urlsafe_b64encode(packed).decode().rstrip("=")


def test_another_devices_file_is_refused() -> None:
    """FR-PROF-009: nothing changes and the device is named."""
    state = press("4", k.EQ)
    with pytest.raises(DocumentFileError, match="nspire"):
        state.loads(json.dumps({"format": "cassim-document", "schema": 5, "problems": []}))
    assert state.answer_text() == "4"


@pytest.mark.parametrize(
    "calculator",
    [
        {"entry": ["__import__('os')"]},  # not a key: entries are key ids, never code
        {"entry": [{"t": "frac", "s": [["1"]]}]},  # a fraction with one slot
        {"variables": {"A": [[4, 0, "1"]]}},  # 4 is not square-free... but is accepted below
        {"variables": {"A": True}},
        {"variables": {"A": 1e300}},
        {"stat": [[1, 2, 3]]},  # 1-VAR has one column
        {"entry": ["9"] * 200},
    ],
)
def test_damaged_documents_are_refused(calculator: dict[str, object]) -> None:
    """NFR-SEC-001, FR-FX-SHR-003: a link or file is data; anything else is refused."""
    document = {
        "format": "cassim-document",
        "schema": 5,
        "device": "scientific",
        "calculator": calculator,
    }
    state = ScientificState()
    if calculator.get("variables") == {"A": [[4, 0, "1"]]}:
        state.loads(json.dumps(document))  # √4 is read as the number 2
        assert float(state.variables["A"]) == 2
        return
    with pytest.raises(DocumentFileError):
        state.loads(json.dumps(document))


def test_a_damaged_link_is_refused() -> None:
    with pytest.raises(DocumentFileError):
        ScientificState().open_fragment("doc=not-base64!!")
    assert not ScientificState().open_fragment("something-else")
    bomb = _fragment({"pad": "x" * 300_000})
    with pytest.raises(DocumentFileError):
        ScientificState().open_fragment(bomb)
