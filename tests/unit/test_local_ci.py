"""The local CI runner: CI's browser list, the recorded pass and the pre-push check."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from tools import local_ci


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args), cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "a.txt").write_text("one\n", encoding="utf-8")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-q", "-m", "one")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_browser_group_runs_ci_list_or_whole_suite() -> None:
    *_, listed = local_ci.browser_steps(full=False)
    *_, whole = local_ci.browser_steps(full=True)
    assert listed[-len(local_ci.BROWSER_TESTS) :] == local_ci.BROWSER_TESTS
    assert whole[-1] == "tests/e2e"


def test_ci_workflow_calls_local_ci_for_each_group() -> None:
    workflow = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")
    for group in local_ci.GROUPS:
        assert f"tools.local_ci {group}" in text


def test_a_recorded_tree_lets_its_commit_be_pushed(repo: Path) -> None:
    head = _git(repo, "rev-parse", "HEAD")
    line = f"refs/heads/x {head} refs/heads/x {'0' * 40}"
    assert local_ci.verify_push([line]) == [head]
    local_ci.record_pass()
    assert local_ci.verify_push([line]) == []


def test_the_same_tree_under_a_new_commit_still_counts(repo: Path) -> None:
    local_ci.record_pass()
    _git(repo, "commit", "-q", "--allow-empty", "-m", "same tree")
    head = _git(repo, "rev-parse", "HEAD")
    assert local_ci.verify_push([f"r {head} r {'0' * 40}"]) == []


def test_changed_content_needs_a_new_pass(repo: Path) -> None:
    local_ci.record_pass()
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "two")
    head = _git(repo, "rev-parse", "HEAD")
    assert local_ci.verify_push([f"r {head} r {'0' * 40}"]) == [head]


def test_deleting_a_remote_branch_is_not_checked(repo: Path) -> None:
    assert local_ci.verify_push([f"(delete) {'0' * 40} refs/heads/x {'1' * 40}"]) == []
