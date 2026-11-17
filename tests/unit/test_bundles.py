# Requirements traced here: FR-PROF-008
"""Bundles in `tools.publish` (decision 0032 item 8): what each build holds, without building."""

import hashlib
import json
import urllib.error
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image, ImageChops, ImageDraw, ImageFont
from tools import publish


def test_pyodide_download_retries_transient_server_failure() -> None:
    """FR-PWA-002: a temporary CDN failure must not break an offline build."""
    error = urllib.error.HTTPError("https://example.test", 503, "timeout", Message(), None)
    with (
        patch.object(
            publish.urllib.request, "urlopen", side_effect=[error, BytesIO(b"wheel")]
        ) as fetch,
        patch.object(publish.time, "sleep") as sleep,
    ):
        assert publish.download_pyodide("https://example.test") == b"wheel"
    assert fetch.call_count == 2
    sleep.assert_called_once_with(1)


@pytest.mark.parametrize(("code", "attempts"), [(404, 1), (503, 3)])
def test_pyodide_download_reports_persistent_failure(code: int, attempts: int) -> None:
    error = urllib.error.HTTPError("https://example.test", code, "failure", Message(), None)
    with (
        patch.object(publish.urllib.request, "urlopen", side_effect=error) as fetch,
        patch.object(publish.time, "sleep"),
        pytest.raises(urllib.error.HTTPError, match=str(code)),
    ):
        publish.download_pyodide("https://example.test")
    assert fetch.call_count == attempts


def test_all_and_one_bundle_per_built_device() -> None:
    found = publish.bundles()
    assert found["all"].product == "CASSim"
    assert publish.product_for_site(found["all"], "CASSim-calc") == "CASSimᵝ"
    assert publish.product_for_site(found["all"], "CASSim-app") == "CASSim"
    assert found["tin"].devices == ("nspire",)
    assert found["tin"].product == "CASSim-TIN"
    assert publish.product_for_site(found["tin"], "CASSim-TIN") == "CASSim-TIN"


def test_beta_bundle_marks_its_icons_without_changing_stable_artwork(tmp_path: Path) -> None:
    stable_dir = tmp_path / "stable"
    beta_dir = tmp_path / "beta"
    stable_dir.mkdir()
    beta_dir.mkdir()
    all_bundle = publish.bundles()["all"]
    stable = publish.Bundle("all", "CASSim", all_bundle.devices, "CASSim-app")
    beta = publish.Bundle("all", "CASSimᵝ", all_bundle.devices, "CASSim-calc")
    publish.write_icons(stable_dir, stable)
    publish.write_icons(beta_dir, beta)

    for filename, size in (
        ("favicon.png", 64),
        ("icons/icon-192.png", 192),
        ("icons/icon-512.png", 512),
    ):
        expected = BytesIO()
        publish.draw_icon(size).save(expected, format="PNG")
        stable_image = (stable_dir / filename).read_bytes()
        beta_image = (beta_dir / filename).read_bytes()
        assert stable_image == expected.getvalue()
        assert stable_image != beta_image

    assert (stable_dir / "icons/icon-maskable-512.png").read_bytes() != (
        beta_dir / "icons/icon-maskable-512.png"
    ).read_bytes()


def test_icon_font_draws_beta_not_a_missing_glyph() -> None:
    font = ImageFont.truetype(publish.ICON_FONT, 96)
    beta = Image.new("L", (160, 160))
    missing = Image.new("L", (160, 160))
    ImageDraw.Draw(beta).text((10, 10), "β", fill=255, font=font)
    ImageDraw.Draw(missing).text((10, 10), "\u2603", fill=255, font=font)  # not in the subset
    assert beta.getbbox() is not None
    assert ImageChops.difference(beta, missing).getbbox() is not None

    stable = publish.draw_icon(192)
    marked = publish.draw_icon(192, beta=True)
    assert ImageChops.difference(stable.convert("RGB"), marked.convert("RGB")).getbbox()


def test_the_engine_packages_come_from_the_devices() -> None:
    assert publish.bundles()["tin"].engine_packages == ["sympy", "mpmath"]


def test_a_bundle_copies_only_its_devices_and_writes_its_own_list(tmp_path: Path) -> None:
    """FR-PROF-008: a bundle holds nothing another device needs."""
    devices = publish.ROOT / "src" / "cassim" / "devices"
    fake = devices / "zzspike"
    fake.mkdir()
    try:
        (fake / "__init__.py").write_text("", encoding="utf-8")
        publish.copy_package(tmp_path, publish.bundles()["tin"], ui=False, source="CASSim-TIN")
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
    assert "SOURCE = 'CASSim-TIN'" in text


def test_the_ui_build_keeps_the_views(tmp_path: Path) -> None:
    publish.copy_package(tmp_path, publish.bundles()["all"], ui=True)
    assert (tmp_path / "cassim" / "devices" / "nspire" / "ui" / "app.py").exists()
    assert (tmp_path / "cassim" / "app" / "main.py").exists()


def test_unused_rive_initializer_is_removed_or_build_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-PWA-002: unexpected generated code must not silently restore external requests."""
    monkeypatch.setattr(publish, "flet_version", lambda: "1.0.5")
    (tmp_path / "index.html").write_text('flet.webRenderer="canvaskit"', encoding="utf-8")
    main = tmp_path / "main.dart.js"
    original = 'case 0:s=3\nreturn A.p(A.b2F("wasm/rive_native.js","RiveNative"),$async$b34)'
    main.write_text(original, encoding="utf-8")
    publish.disable_unused_rive(tmp_path)
    assert "rive_native.js" not in main.read_text(encoding="utf-8")
    with pytest.raises(SystemExit, match="Rive initializer changed"):
        publish.disable_unused_rive(tmp_path)
    monkeypatch.setattr(publish, "flet_version", lambda: "1.1.0")
    with pytest.raises(SystemExit, match="Review Rive initialization"):
        publish.disable_unused_rive(tmp_path)


def test_offline_manifest_hashes_the_published_files(tmp_path: Path) -> None:
    """FR-PWA-002/004: each installation is verified against its own build."""
    (tmp_path / "index.html").write_text("app", encoding="utf-8")
    (tmp_path / "flutter_service_worker.js").write_text("old", encoding="utf-8")
    publish.add_offline_cache(tmp_path, "test")
    files = json.loads((tmp_path / "precache.json").read_text(encoding="utf-8"))
    worker = (tmp_path / "flutter_service_worker.js").read_text(encoding="utf-8")
    assert "flutter_service_worker.js" not in files
    assert hashlib.sha256(b"app").hexdigest() in worker
    first = json.loads((tmp_path / "version.json").read_text(encoding="utf-8"))
    (tmp_path / "index.html").write_text("new app", encoding="utf-8")
    publish.add_offline_cache(tmp_path, "test")
    second = json.loads((tmp_path / "version.json").read_text(encoding="utf-8"))
    assert first != second


def test_missing_bootstrap_assets_reject_offline_build(tmp_path: Path) -> None:
    """FR-PWA-002: a partial build must not be presented as an offline installation."""
    with pytest.raises(SystemExit, match="missing required assets"):
        publish.check_offline_assets(tmp_path)
