# Requirements traced here: NFR-REL-001
"""Saving and loading documents (FR-DOC-003, FR-DOC-004)."""

import json

import pytest

from cassim.core.settings import Angle
from cassim.device import runner, serialize
from cassim.device.document import Document, PageKind
from cassim.device.keys import Binding
from cassim.device.serialize import SCHEMA, DocumentFileError, dumps, loads, migrate, to_dict


def type_line(document: Document, text: str, *, enter: bool = True) -> None:
    calculator = document.current.calculator
    assert calculator is not None
    for char in text:
        calculator.perform(Binding("insert", char))
    if enter:
        calculator.perform(Binding("enter"))


def sample() -> Document:
    document = Document("Maths")
    document.set(angle="degree")
    type_line(document, "a:=5")
    calculator = document.current.calculator
    assert calculator is not None
    calculator.perform(Binding("template", "fraction"))
    calculator.perform(Binding("insert", "a"))
    calculator.perform(Binding("tab"))
    calculator.perform(Binding("insert", "2"))
    calculator.perform(Binding("enter"))
    document.add_page()
    type_line(document, "a+1")
    document.add_problem()
    type_line(document, "b:=7")
    type_line(document, "2+", enter=False)  # an unfinished entry
    return document


def test_round_trip_restores_pages_results_variables_and_settings() -> None:
    loaded = loads(dumps(sample()))
    assert loaded.name == "Maths"
    assert loaded.settings.angle == Angle.DEGREE
    assert [len(p.pages) for p in loaded.problems] == [2, 1]
    first = loaded.problems[0].pages[1].calculator
    assert first is not None
    assert first.history[0].result.text == "6"  # `a` came from the previous page
    fraction = loaded.problems[0].pages[0].calculator
    assert fraction is not None
    assert fraction.history[1].result.text == "5/2"
    second = loaded.problems[1].pages[0].calculator
    assert second is not None
    assert second.editor.linear() == "2+"
    assert loaded.problems[1].session.variables()[0].name == "b"
    assert loaded.problems[0].session.variables()[0].name == "a"  # not b: Problems stay apart


def test_templates_survive_so_recall_keeps_them() -> None:
    loaded = loads(dumps(sample()))
    calculator = loaded.problems[0].pages[0].calculator
    assert calculator is not None
    assert not isinstance(calculator.history[1].nodes[0], str)


def test_position_is_restored() -> None:
    document = sample()
    document.go(0, 1)
    loaded = loads(dumps(document))
    assert (loaded.problem, loaded.page) == (0, 1)


def test_file_is_plain_versioned_json() -> None:
    data = json.loads(dumps(sample()))
    assert data["format"] == "cassim-document"
    assert data["schema"] == SCHEMA
    assert to_dict(sample())["problems"][0]["pages"][0]["kind"] == PageKind.CALCULATOR.value


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        '{"format": "other", "schema": 1}',
        '{"format": "cassim-document", "schema": 99, "problems": []}',
        '{"format": "cassim-document", "schema": 1}',
        '{"format": "cassim-document", "schema": 1, "problems": [{"pages": [{"kind": "x"}]}]}',
    ],
)
def test_bad_files_are_refused_with_a_reason(text: str) -> None:
    with pytest.raises(DocumentFileError):
        loads(text)


def test_a_newer_schema_says_so() -> None:
    with pytest.raises(DocumentFileError, match="newer"):
        migrate({"format": "cassim-document", "schema": SCHEMA + 1})


def test_loading_does_not_leave_undo_history() -> None:
    assert not loads(dumps(sample())).undo()


def test_replay_steps_is_the_public_replay_interface() -> None:
    """Both loaders (`from_dict` here, `Runner.load` for a worker) drive `replay_steps`."""
    assert callable(serialize.replay_steps)
    assert not hasattr(serialize, "_steps")
    assert runner.replay_steps is serialize.replay_steps
