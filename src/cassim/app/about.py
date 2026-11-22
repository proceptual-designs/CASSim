"""The text of the About dialog (NFR-LEG-002, NFR-LEG-003, NFR-SEC-001). Plain data, no Flet."""

from __future__ import annotations

import platform
from dataclasses import dataclass
from importlib import metadata

from cassim import bundle

DISCLAIMER = (
    "CASSim is a simulator of handheld computer algebra systems (CAS) for educational purposes. "
    "It is not affiliated with, endorsed by, or sponsored by any company, corporation, or "
    "curriculum authority.\n"
    "It is not an approved exam calculator and must not be used in assessments that require an "
    "approved device."
)

PRIVACY = (
    "CASSim has no server, telemetry, or analytics. Your documents stay in this browser, or in "
    "the link or file you choose to share. Opening a shared link or file never runs Python or a "
    "program automatically."
)

LICENCE = (
    "CASSim is vibe-coded and is released under the Unlicense as free and unencumbered software "
    "in the public domain."
)

# The help pages: `docs/wiki/`, built by `tools.wiki_site` and deployed to their own site.
WIKI_URL = "https://cassim-wiki.pages.dev/"


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
    Notice("Noto Sans, Math, Symbols 2 and SC", "SIL OFL 1.1", "glyphs the browser lacks"),
    Notice("Roboto Mono", "Apache-2.0", "the code editor"),
)

UNKNOWN = "not available"

# Shown in this order; the distribution each is read from when the build did not record it.
SHOWN = (("CASSim", "cassim"), ("Flet", "flet"), ("SymPy", "sympy"), ("mpmath", "mpmath"))


def product_name() -> str:
    """The all-in-one testing site marks its product as beta; stable/device sites do not."""
    return "CASSimᵝ" if bundle.SOURCE == "CASSim-calc" else "CASSim"


def _version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return UNKNOWN


def versions(shipped: dict[str, str] | None = None) -> list[tuple[str, str]]:
    """Name and version pairs for the About dialog: what the build recorded (`bundle.VERSIONS`),
    else the installed packages (the desktop app and the tests)."""
    shipped = bundle.VERSIONS if shipped is None else shipped
    found = [("CASSim", shipped.get("CASSim") or _version("cassim"))]
    found.append(("Python", platform.python_version()))
    if "Pyodide" in shipped:
        found.append(("Pyodide", shipped["Pyodide"]))
    found += [(name, shipped.get(name) or _version(dist)) for name, dist in SHOWN[1:]]
    return found


def build_info() -> str:
    return f"Source: {bundle.SOURCE}\n" + "\n".join(
        f"{name} {version}" for name, version in versions()
    )
