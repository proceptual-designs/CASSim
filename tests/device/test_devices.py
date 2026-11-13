# Requirements traced here: FR-PROF-001, FR-PROF-002, FR-PROF-008
"""The device registry (decision 0032)."""

import importlib.util
import subprocess
import sys

import pytest

from cassim import bundle, devices


def test_every_device_in_the_bundle_loads_and_names_itself() -> None:
    for device_id in bundle.DEVICES:
        device = devices.load(device_id)
        assert device.id == device_id
        assert device.pages.device == device_id
        assert device.pages.default.new is not None


def test_the_nspire_is_the_first_device() -> None:
    """FR-PROF-002."""
    nspire = devices.load("nspire")
    assert nspire.title == "TI-Nspire CX CAS"
    assert str(nspire.pages.default.kind) == "calculator"
    assert nspire.engine is not None
    assert importlib.util.find_spec(nspire.engine.module) is not None
    assert nspire.storage == "cassim."


def test_an_unknown_device_is_refused() -> None:
    with pytest.raises(ValueError, match="abacus"):
        devices.load("abacus")


def test_every_device_has_a_site() -> None:
    """FR-PROF-008: each device can be published alone, on its own site."""
    assert set(bundle.DEVICES) <= set(devices.SITES)
    for site in devices.SITES.values():
        assert site.url == f"https://cassim-{site.bundle}.pages.dev/"


def test_a_device_imports_without_flet() -> None:
    """The engine worker and the CLI load a device where Flet is not installed."""
    code = (
        "import sys; sys.modules['flet'] = None\n"
        "from cassim import bundle, devices\n"
        "for name in bundle.DEVICES: devices.load(name)\n"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
