"""Run the CI checks locally, record a pass, and check pushes against it.

`uv run python -m tools.local_ci` runs exactly what GitHub CI runs: the `python` group (Ruff,
Ty, pytest with coverage, the coverage floors and the traceability check) and the `browser` group
(the Playwright tests CI selects). CI calls this module too, so the two cannot drift apart.

When every group passes on a clean working tree, the commit's tree hash is recorded in the git
directory. The pre-push hook (`--verify-push`, installed by `uv run pre-commit install`) refuses
to push a commit whose tree has not passed. Merging or rebasing to the same content keeps the
pass, since the tree is the same.

    uv run python -m tools.local_ci                 # both groups, then record the pass
    uv run python -m tools.local_ci python          # one group (CI runs one group a job)
    uv run python -m tools.local_ci --full-e2e      # the whole browser suite, not CI's list
    uv run python -m tools.local_ci --status        # has HEAD's tree passed?
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# CI installs the locked environment with the web group (Flet) first; a fresh worktree needs it
SYNC = ("uv", "sync", "--locked", "--group", "web")

PYTHON_STEPS: tuple[tuple[str, ...], ...] = (
    SYNC,
    ("uv", "run", "ruff", "format", "--check"),
    ("uv", "run", "ruff", "check"),
    ("uv", "run", "ty", "check"),
    (
        "uv",
        "run",
        "pytest",
        "-m",
        "not e2e",
        "--cov=cassim",
        "--cov-branch",
        "--cov-report=json",
    ),
    ("uv", "run", "python", "-m", "tools.coverage_check"),
    ("uv", "run", "python", "-m", "tools.traceability", "--check"),
)

# The browser tests CI runs. Keep fresh installs, broken caches and touch contexts separate
# (TESTING.md); the whole suite is `--full-e2e`.
BROWSER_TESTS: tuple[str, ...] = (
    "tests/e2e/test_pwa.py::test_loads_and_works_offline",
    "tests/e2e/test_pwa.py::test_root_hosted_site_works_offline",
    "tests/e2e/test_pwa.py::test_redirected_index_allows_online_and_offline_launch",
    "tests/e2e/test_pwa.py::test_cas_after_host_failure_and_offline",
    "tests/e2e/test_pwa.py::test_cached_navigation_offers_and_applies_update",
    "tests/e2e/test_pwa.py::test_failed_precache_is_reported_and_can_be_retried",
    "tests/e2e/test_pwa.py::test_incomplete_update_leaves_working_cache",
    "tests/e2e/test_pwa.py::test_missing_cached_file_is_reported_and_repaired",
    "tests/e2e/test_theme_browser.py::test_saved_custom_theme_is_applied_after_reload",
    "tests/e2e/test_autosave_browser.py::test_the_document_comes_back_after_a_reload",
    "tests/e2e/test_key_repeat_browser.py",
    "tests/e2e/test_sheet_browser.py::test_right_click_context_menus",
    "tests/e2e/test_sheet_browser.py::test_long_press_still_opens_the_cell_menu",
)

GROUPS = ("python", "browser")
STAMP_NAME = "cassim-local-ci"
SKIP_VARIABLE = "CASSIM_SKIP_LOCAL_CI"


def browser_steps(*, full: bool) -> tuple[tuple[str, ...], ...]:
    tests = ("tests/e2e",) if full else BROWSER_TESTS
    return (SYNC, ("uv", "run", "pytest", "-m", "e2e", *tests))


def _git(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, capture_output=True, text=True).stdout.strip()


def _stamp_file() -> Path:
    return Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir")) / STAMP_NAME


def _passed_trees() -> set[str]:
    try:
        lines = _stamp_file().read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return set()
    return {line.split()[0] for line in lines if line.strip()}


def _tree(commit: str) -> str:
    return _git("rev-parse", f"{commit}^{{tree}}")


def _clean() -> bool:
    return not _git("status", "--porcelain", "--untracked-files=no")


def _run(steps: tuple[tuple[str, ...], ...]) -> bool:
    for step in steps:
        print(f"\n$ {' '.join(step)}", flush=True)
        if subprocess.run(step, check=False).returncode != 0:
            print(f"\nlocal_ci: failed: {' '.join(step)}", file=sys.stderr)
            return False
    return True


def run_groups(groups: tuple[str, ...], *, full_e2e: bool) -> bool:
    for group in groups:
        steps = PYTHON_STEPS if group == "python" else browser_steps(full=full_e2e)
        if not _run(steps):
            return False
    return True


def record_pass() -> str:
    tree = _tree("HEAD")
    if tree not in _passed_trees():
        with _stamp_file().open("a", encoding="utf-8") as stamp:
            stamp.write(f"{tree} {_git('rev-parse', 'HEAD')}\n")
    return tree


def verify_push(lines: list[str]) -> list[str]:
    """Return the local commits being pushed whose trees have not passed.

    `lines` are git's pre-push lines, `<local ref> <local sha> <remote ref> <remote sha>`.
    """
    passed = _passed_trees()
    missing = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4 or set(parts[1]) == {"0"}:
            continue  # a malformed line, or a deleted ref
        if _tree(parts[1]) not in passed:
            missing.append(parts[1])
    return missing


def _push_lines() -> list[str]:
    # pre-commit passes the refs in variables; a plain git hook passes them on stdin
    local = os.environ.get("PRE_COMMIT_TO_REF")
    if local:
        remote = os.environ.get("PRE_COMMIT_REMOTE_BRANCH", "unknown")
        return [f"local {local} {remote} {'0' * 40}"]
    return sys.stdin.read().splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.local_ci", description=__doc__)
    parser.add_argument("groups", nargs="*", choices=GROUPS, help="default: both")
    parser.add_argument("--full-e2e", action="store_true", help="run the whole browser suite")
    parser.add_argument("--status", action="store_true", help="say whether HEAD has passed")
    parser.add_argument(
        "--verify-push", action="store_true", help="pre-push hook: refuse untested commits"
    )
    args = parser.parse_args(argv)

    if args.verify_push:
        if os.environ.get(SKIP_VARIABLE):
            print(f"local_ci: {SKIP_VARIABLE} is set; push not checked", file=sys.stderr)
            return 0
        missing = verify_push(_push_lines())
        for commit in missing:
            print(
                f"local_ci: {commit[:12]} has not passed `uv run python -m tools.local_ci`",
                file=sys.stderr,
            )
        return 1 if missing else 0
    if args.status:
        passed = _tree("HEAD") in _passed_trees()
        print("HEAD has passed local CI" if passed else "HEAD has not passed local CI")
        return 0 if passed else 1

    groups = tuple(args.groups) or GROUPS
    head, clean_before = _git("rev-parse", "HEAD"), _clean()
    if not run_groups(groups, full_e2e=args.full_e2e):
        return 1
    if set(groups) != set(GROUPS):
        print("\nlocal_ci: passed (one group only, so no pass is recorded)")
    elif not (clean_before and _clean() and _git("rev-parse", "HEAD") == head):
        print("\nlocal_ci: passed, but the working tree has changes, so no pass is recorded")
    else:
        print(f"\nlocal_ci: passed; recorded tree {record_pass()[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
