"""Start a Flet web server for a spike in a child process and always stop its whole tree."""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@contextlib.contextmanager
def server(script: Path, port: int, *args: str) -> Generator[str]:
    """Run `script server <port> args...` (the script calls `ft.run(..., port=port)`)."""
    proc = subprocess.Popen(
        [sys.executable, str(script), "server", str(port), *args],
        cwd=ROOT,
        env={**os.environ, "FLET_FORCE_WEB_SERVER": "true"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(120):
            with contextlib.suppress(OSError), socket.create_connection(("127.0.0.1", port), 0.5):
                break
            time.sleep(0.5)
        yield f"http://127.0.0.1:{port}/"
    finally:
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
