"""Copy `docs/wiki/*.md` to the GitHub wiki and push.

    python -m tools.sync_wiki [--dry-run]

The wiki is a separate git repository (`<repo>.wiki.git`) that GitHub creates when the first page
is saved in the web UI, so create a "Home" page there once, by hand. After that this script is the
only way pages should change: the files in `docs/wiki/` are the source of truth. Pages not in
`docs/wiki/` are deleted from the wiki.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "wiki"
WIKI_URL = "https://github.com/simonjtyler/CASSim.wiki.git"


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show the changes, do not push")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        wiki = Path(tmp) / "wiki"
        subprocess.run(["git", "clone", "--quiet", WIKI_URL, str(wiki)], check=True)
        for old in wiki.glob("*.md"):
            old.unlink()
        for page in sorted(SOURCE.glob("*.md")):
            shutil.copy(page, wiki / page.name)
        git("add", "-A", cwd=wiki)
        changes = git("status", "--short", cwd=wiki)
        if not changes:
            print("wiki is up to date")
            return
        print(changes, end="")
        if args.dry_run:
            return
        git("commit", "-m", "Sync from docs/wiki", cwd=wiki)
        git("push", "--quiet", cwd=wiki)
        print("pushed")


if __name__ == "__main__":
    main()
