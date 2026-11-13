# Requirements traced here: FR-PROF-008
"""Bundles in `tools.publish` (decision 0032 item 8): what each build holds, without building."""

from pathlib import Path

from tools import publish


def test_all_and_one_bundle_per_built_device() -> None:
    found = publish.bundles()
    assert found["all"].product == "CASSim"
    assert found["tin"].devices == ("nspire",)
    assert found["tin"].product == "CASSim-TIN"


def test_the_engine_packages_come_from_the_devices() -> None:
    assert publish.bundles()["tin"].engine_packages == ["sympy", "mpmath"]


def test_a_bundle_copies_only_its_devices_and_writes_its_own_list(tmp_path: Path) -> None:
    """FR-PROF-008: a bundle holds nothing another device needs."""
    devices = publish.ROOT / "src" / "cassim" / "devices"
    fake = devices / "zzspike"
    fake.mkdir()
    try:
        (fake / "__init__.py").write_text("", encoding="utf-8")
        publish.copy_package(tmp_path, publish.bundles()["tin"], ui=False)
    finally:
        (fake / "__init__.py").unlink()
        fake.rmdir()
    copied = tmp_path / "cassim"
    assert (copied / "devices" / "nspire" / "keymap.py").exists()
    assert not (copied / "devices" / "zzspike").exists()
    assert not (copied / "devices" / "nspire" / "ui").exists()
    assert not (copied / "app").exists()
    text = (copied / "bundle.py").read_text(encoding="utf-8")
    assert "NAME = 'tin'" in text
    assert "DEVICES = ('nspire',)" in text


def test_the_ui_build_keeps_the_views(tmp_path: Path) -> None:
    publish.copy_package(tmp_path, publish.bundles()["all"], ui=True)
    assert (tmp_path / "cassim" / "devices" / "nspire" / "ui" / "app.py").exists()
    assert (tmp_path / "cassim" / "app" / "main.py").exists()
