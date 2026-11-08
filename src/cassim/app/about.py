"""The text of the About dialog (NFR-LEG-002, NFR-LEG-003, NFR-SEC-001). Plain data, no Flet."""

from __future__ import annotations

import platform
from dataclasses import dataclass
from importlib import metadata

DISCLAIMER = (
    "CASSim is an independent educational simulator. It is not affiliated with, endorsed by or "
    "sponsored by Texas Instruments. It is not an approved exam calculator and must not be used "
    "in assessments that require an approved device. TI-Nspire is a trademark of Texas "
    "Instruments."
)

PRIVACY = (
    "CASSim has no server, no telemetry and no analytics. Your documents stay in this browser, "
    "or in the link or file you choose to share. Opening a shared link or file never runs "
    "Python or a program by itself."
)

LICENCE = (
    "CASSim is released under the Unlicense: free and unencumbered software in the public domain."
)

SOURCE_URL = "https://github.com/simonjtyler/CASSim"


@dataclass(frozen=True)
class Notice:
    name: str
    licence: str
    use: str


# Third-party notices that ship with the build (NFR-LEG-003).
NOTICES = (
    Notice("Flet", "Apache-2.0", "the user interface"),
    Notice("Pyodide", "MPL-2.0", "Python in the browser"),
    Notice("SymPy", "BSD-3-Clause", "computer algebra"),
    Notice("SciPy", "BSD-3-Clause", "numerical methods"),
    Notice("NumPy", "BSD-3-Clause", "numerical arrays"),
    Notice("Noto Sans Symbols 2", "SIL OFL 1.1", "arrow and shape glyphs"),
)


def _version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "not available"


def versions() -> list[tuple[str, str]]:
    """Name and version pairs for the About dialog."""
    return [
        ("CASSim", _version("cassim")),
        ("Python", platform.python_version()),
        ("Flet", _version("flet")),
        ("SymPy", _version("sympy")),
    ]


def build_info() -> str:
    return "\n".join(f"{name} {version}" for name, version in versions())
