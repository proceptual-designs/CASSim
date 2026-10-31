"""Back up the whole git history as a single ``git bundle`` file.

The repo lives outside OneDrive (syncing ``.git`` corrupts it), but a single bundle file
syncs safely, so writing one into a OneDrive folder gives an off-machine copy.

    uv run python tools/backup_bundle.py                # default destination
    uv run python tools/backup_bundle.py D:\\backups    # any folder
    git clone emcas-20261101-1530.bundle emcas-restored # restore

Only committed work is included; commit first. Untracked files (``references/``) are
not in git and need their own backup.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DEST = Path.home() / "OneDrive" / "emCAS-backups"
KEEP = 10


def git(*args: str) -> str:
    """Run git in the current repo and return stdout; raise on failure."""
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        msg = f"git {' '.join(args)} failed:\n{done.stderr.strip()}"
        raise SystemExit(msg)
    return done.stdout.strip()


def main() -> None:
    """Create a verified bundle and prune old ones."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("dest", nargs="?", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--keep", type=int, default=KEEP, help="bundles to retain")
    args = parser.parse_args()

    dirty = git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        print("note: uncommitted changes are NOT in the bundle", file=sys.stderr)

    args.dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    bundle = args.dest / f"emcas-{stamp}.bundle"
    git("bundle", "create", str(bundle), "--all")
    git("bundle", "verify", str(bundle))
    head = git("rev-parse", "--short", "HEAD")
    print(f"wrote {bundle} ({bundle.stat().st_size / 1e3:.0f} kB), head {head}")

    for old in sorted(args.dest.glob("emcas-*.bundle"))[: -args.keep]:
        old.unlink()
        print(f"pruned {old.name}")


if __name__ == "__main__":
    main()
