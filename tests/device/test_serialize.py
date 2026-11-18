# Requirements traced here: NFR-REL-001
"""Saving and loading documents (FR-DOC-003, FR-DOC-004)."""

import json

import pytest

from cassim.core.settings import Angle
from cassim.device.keys import Binding
from cassim.devices.nspire import runner
from cassim.devices.nspire.document import Document, PageKind, loads
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.doc import serialize
from cassim.doc.serialize import SCHEMA, DocumentFileError, dumps, migrate, to_dict


def type_line(document: Document, text: str, *, enter: bool = True) -> None:
    calculator = calculator_of(document.current)
    assert calculator is not None
    for char in text:
        calculator.perform(Binding("insert", char))
    if enter:
        calculator.perform(Binding("enter"))


def sample() -> Document:
    document = Document("Maths")
    document.set(angle="degree")
    type_line(document, "a:=5")
    calculator = calculator_of(document.current)
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
    first = calculator_of(loaded.problems[0].pages[1])
    assert first is not None
    assert first.history[0].result.text == "6"  # `a` came from the previous page
    fraction = calculator_of(loaded.problems[0].pages[0])
    assert fraction is not None
    assert fraction.history[1].result.text == "5/2"
    second = calculator_of(loaded.problems[1].pages[0])
    assert second is not None
    assert second.editor.linear() == "2+"
    assert loaded.problems[1].session.variables()[0].name == "b"
    assert loaded.problems[0].session.variables()[0].name == "a"  # not b: Problems stay apart


def test_templates_survive_so_recall_keeps_them() -> None:
    loaded = loads(dumps(sample()))
    calculator = calculator_of(loaded.problems[0].pages[0])
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


def test_a_file_names_its_device_and_one_without_a_name_is_an_nspire_document() -> None:
    """FR-PROF-009: the device id travels in the file (decision 0032 item 4)."""
    data = to_dict(sample())
    assert data["device"] == "nspire"
    del data["device"]
    assert dumps(loads(json.dumps(data))) == dumps(sample())


def test_a_file_for_another_device_is_refused() -> None:
    """FR-PROF-009: a build that does not hold the device opens nothing."""
    data = to_dict(sample())
    data["device"] = "classpad"
    with pytest.raises(DocumentFileError, match="classpad"):
        loads(json.dumps(data))


def test_an_unknown_page_kind_is_not_a_page_type() -> None:
    """FR-PROF-006: page types are the ones the device registered."""
    with pytest.raises(ValueError, match="not a page type"):
        Document().add_page("abacus")


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


def test_rows_are_saved_as_runs_of_text() -> None:
    """Schema 2: a row is one string, or runs of text between templates, not one per character;
    an exact entry is only its row."""
    document = Document()
    type_line(document, "solve(x=4,x)")
    calculator = calculator_of(document.current)
    assert calculator is not None
    calculator.perform(Binding("insert", "3"))
    calculator.perform(Binding("template", "fraction"))
    calculator.perform(Binding("insert", "4"))
    calculator.perform(Binding("approximate"))
    page = to_dict(document)["problems"][0]["pages"][0]
    assert page["entries"][0] == "solve(x=4,x)"
    assert page["entries"][1] == {
        "nodes": [{"kind": "fraction", "slots": ["3", "4"]}],
        "approximate": True,
    }
    assert page["entry"] == ""
    assert "\n" not in dumps(document, compact=True)


def test_a_schema_1_file_still_opens() -> None:
    """Schema 1 wrote one string per character and every entry as an object."""
    old = {
        "format": "cassim-document",
        "schema": 1,
        "name": "Old",
        "problems": [
            {
                "pages": [
                    {
                        "kind": "calculator",
                        "entries": [
                            {"nodes": ["1", "+", "1"], "approximate": False},
                            {"nodes": [{"kind": "fraction", "slots": [["1"], ["4"]]}],
                             "approximate": True},
                        ],
                        "entry": ["2", "+"],
                    }
                ]
            }
        ],
    }  # fmt: skip
    loaded = loads(json.dumps(old))
    calculator = calculator_of(loaded.current)
    assert calculator is not None
    assert [entry.result.text for entry in calculator.history] == ["2", "0.25"]
    assert calculator.editor.linear() == "2+"


def test_schema_2_spreadsheets_start_with_no_split_statistics() -> None:
    old = {
        "format": "cassim-document",
        "schema": 2,
        "problems": [{"pages": [{"kind": "spreadsheet"}]}],
    }

    migrated = migrate(old)

    assert migrated["schema"] == SCHEMA
    assert migrated["problems"][0]["pages"][0]["split_statistics"] == []


def test_schema_3_graph_and_statistics_pages_get_save_defaults() -> None:
    old = {
        "format": "cassim-document",
        "schema": 3,
        "problems": [
            {
                "pages": [
                    {"kind": "graphs"},
                    {"kind": "statistics"},
                ]
            }
        ],
    }

    migrated = migrate(old)

    graph = migrated["problems"][0]["pages"][0]
    assert graph["window"] == [-10.0, 10.0, -20 / 3, 20 / 3]
    assert graph["show_axes"] is True
    assert graph["show_end_values"] is True
    assert graph["grid_style"] == "none"
    assert graph["functions"] == []
    assert graph["active"] == 0
    statistics = migrated["problems"][0]["pages"][1]
    assert statistics["x"] == ""
    assert statistics["y"] == ""
    assert statistics["plot"] == "dot"
    assert statistics["window"] is None


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


def test_open_and_save_use_only_the_native_format() -> None:
    """FR-DOC-006: Open and Save read and write `.cassim.json` only; `.tns` is never offered."""
    document = Document()
    assert serialize.file_name(document).endswith(".cassim.json")
    assert serialize.OPEN_EXTENSIONS == ("json",)
    assert "tns" not in serialize.OPEN_EXTENSIONS
    with pytest.raises(DocumentFileError):
        serialize.parse("*TIMLP0601")  # the start of a `.tns` file is not a CASSim document
