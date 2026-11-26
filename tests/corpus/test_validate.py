"""The calculator corpus files match corpus/schema.json (corpus/validate.py)."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")

VALIDATE = Path(__file__).resolve().parents[2] / "corpus" / "validate.py"


def test_seed_corpus_matches_the_schema(capsys: pytest.CaptureFixture[str]) -> None:
    spec = importlib.util.spec_from_file_location("corpus_validate", VALIDATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main([]) == 0, capsys.readouterr().out
