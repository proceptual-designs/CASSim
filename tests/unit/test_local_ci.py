"""The local CI runner: CI's browser list, the recorded pass and the pre-push check."""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
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


def test_a_second_run_cannot_take_the_lock_until_the_first_ends(tmp_path: Path) -> None:
    lock = tmp_path / "shared" / "local_ci.lock"
    with local_ci.machine_lock(lock), lock.open("a+b") as second:
        assert not local_ci._try_lock(second)
    with lock.open("a+b") as second:
        assert local_ci._try_lock(second)
        local_ci._unlock(second)


def test_a_waiting_run_names_the_holder_and_starts_when_it_ends(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lock = tmp_path / "local_ci.lock"
    first = contextlib.ExitStack()
    first.enter_context(local_ci.machine_lock(lock))
    naps: list[float] = []

    def first_run_ends(seconds: float) -> None:
        naps.append(seconds)
        first.close()

    with local_ci.machine_lock(lock, poll=0.01, sleep=first_run_ends):
        assert naps == [0.01]
    out = capsys.readouterr().out
    assert f"waiting for the run in {Path.cwd()}" in out
    assert f"process {os.getpid()}" in out


def test_a_run_that_dies_does_not_leave_the_lock_held(tmp_path: Path) -> None:
    lock = tmp_path / "local_ci.lock"
    script = (
        "import os, sys; from pathlib import Path; from tools import local_ci\n"
        "lock = local_ci.machine_lock(Path(sys.argv[1])); lock.__enter__(); os._exit(1)\n"
    )
    root = Path(__file__).parents[2]
    died = subprocess.run((sys.executable, "-c", script, str(lock)), cwd=root, check=False)
    assert died.returncode == 1
    with local_ci.machine_lock(lock, sleep=_no_waiting):
        pass


def _no_waiting(seconds: float) -> None:
    raise AssertionError(f"the lock was still held (asked to wait {seconds} s)")


def test_the_lock_is_outside_every_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert local_ci.lock_file() == tmp_path / "CASSim" / "local_ci.lock"


def test_deleting_a_remote_branch_is_not_checked(repo: Path) -> None:
    assert local_ci.verify_push([f"(delete) {'0' * 40} refs/heads/x {'1' * 40}"]) == []
