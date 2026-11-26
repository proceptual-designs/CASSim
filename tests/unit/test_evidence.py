"""The evidence folder is optional and found by environment variable or beside the repository."""

from pathlib import Path

import pytest
from tools import evidence


def test_root_comes_from_the_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(evidence.ENV, str(tmp_path))
    assert evidence.evidence_root() == tmp_path


def test_a_missing_folder_means_no_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(evidence.ENV, str(tmp_path / "absent"))
    assert evidence.evidence_root() is None
    assert evidence.evidence_path("corpus/shots/a.jpg") == evidence.ROOT / "corpus/shots/a.jpg"


def test_a_file_in_the_evidence_folder_is_preferred(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shot = tmp_path / "corpus" / "shots" / "a.jpg"
    shot.parent.mkdir(parents=True)
    shot.write_bytes(b"")
    monkeypatch.setenv(evidence.ENV, str(tmp_path))
    assert evidence.evidence_path("corpus/shots/a.jpg") == shot
    assert evidence.evidence_path("references") == evidence.ROOT / "references"
