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
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
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


def test_browser_shortcut_guards_cover_each_bundled_device() -> None:
    bundle = publish.bundles()["all"]
    app_shortcuts = publish.computer_shortcuts(bundle)
    assert "ctrl+s" in app_shortcuts
    assert "ctrl+r" in app_shortcuts
    assert "ctrl+=" in app_shortcuts
    assert set(app_shortcuts) >= publish.ALWAYS_BLOCK_BROWSER_SHORTCUTS
    assert "ctrl+p" not in app_shortcuts
    assert "F5" not in app_shortcuts


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


@pytest.mark.parametrize("bundle_name", ["tin", "pseudo", "sci"])
def test_single_app_icons_carry_their_home_symbol(tmp_path: Path, bundle_name: str) -> None:
    """A single-app site's icon has its Home symbol where the testing icon has β, so each
    installed app is told apart from the all-in-one app and from the others."""
    bundle = publish.bundles()[bundle_name]
    publish.write_icons(tmp_path, bundle)
    icon = Image.open(tmp_path / "icons/icon-192.png").convert("RGB")
    plain = publish.draw_icon(192).convert("RGB")
    beta = publish.draw_icon(192, beta=True).convert("RGB")
    assert ImageChops.difference(icon, plain).getbbox()
    assert ImageChops.difference(icon, beta).getbbox()
    others = {
        name: publish.draw_icon(192, mark=name).convert("RGB")
        for name in publish.ICON_MARKS
        if name != bundle.devices[0]
    }
    assert all(ImageChops.difference(icon, other).getbbox() for other in others.values())


FLET_ICON_FILES = (  # the names Flet's web client ships its own artwork under
    "favicon.png",
    "icons/icon-192.png",
    "icons/icon-512.png",
    "icons/icon-maskable-192.png",
    "icons/icon-maskable-512.png",
    "icons/apple-touch-icon-192.png",
    "icons/loading-animation.png",
)


def close_to(image: Image.Image, expected: Image.Image) -> bool:
    """The same artwork, allowing for small differences between font-rendering versions."""
    diff = ImageChops.difference(image.convert("RGB"), expected.convert("RGB")).convert("L")
    return ImageStat.Stat(diff).mean[0] < 2


def drawn(filename: str, size: int, mark: str = "") -> Image.Image:
    """The icon as `write_icons` makes `filename`: the iOS icon is the artwork on the theme
    colour, as iOS paints transparent corners black. Compared with its transparent corners, it
    starts 0.75 from the limit, and a Linux font rendering took it over (batch PR #187)."""
    icon = publish.draw_icon(size, mark=mark)
    if "apple-touch" not in filename:
        return icon
    touch = Image.new("RGBA", (size, size), publish.THEME)
    touch.paste(icon, (0, 0), icon)
    return touch


@pytest.mark.parametrize("bundle_name", ["all", "tin"])
def test_every_icon_flet_ships_is_replaced_by_the_bundles_own(
    tmp_path: Path, bundle_name: str
) -> None:
    """FR-PWA-001: the tab icon, the installed icons, the iOS icon and the loading image are all
    the bundle's artwork, so no Flet icon is left in a site."""
    bundle = publish.bundles()[bundle_name]
    publish.write_icons(tmp_path, bundle)
    mark = "" if bundle_name == "all" else bundle.devices[0]
    for filename in FLET_ICON_FILES:
        image = Image.open(tmp_path / filename)
        assert image.width == image.height
        if "maskable" not in filename:  # the maskable ones hold the artwork at a smaller scale
            assert close_to(image, drawn(filename, image.width, mark)), filename
    touch = Image.open(tmp_path / "icons/apple-touch-icon-192.png").convert("RGBA")
    # Opaque: iOS paints transparent corners black.
    assert touch.getchannel("A").getextrema() == (255, 255)


def test_a_local_run_has_the_plain_cassim_icons() -> None:
    """FR-PWA-001: `cassim` and `cassim --web` run from the source tree, where nothing draws
    icons, so the plain artwork is committed in the app's assets (`--dev-icons` redraws it)."""
    for filename in FLET_ICON_FILES:
        image = Image.open(publish.APP_ASSETS / filename)
        if "maskable" not in filename:
            assert close_to(image, drawn(filename, image.width)), filename
    window = Image.open(publish.APP_ASSETS / publish.WINDOW_ICON)
    assert window.format == "ICO"
    assert {size[0] for size in window.info["sizes"]} == set(publish.WINDOW_ICON_SIZES)
    assert close_to(window, publish.draw_icon(window.width))


def test_dev_icons_command_writes_the_window_icon(tmp_path: Path) -> None:
    publish.write_dev_icons(tmp_path)
    assert (tmp_path / "favicon.png").is_file()
    assert Image.open(tmp_path / publish.WINDOW_ICON).format == "ICO"


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


def test_a_download_with_the_wrong_hash_is_refused() -> None:
    """NFR-MAINT-005: a wheel that does not match its recorded SHA-256 never reaches a site."""
    good = hashlib.sha256(b"wheel").hexdigest()
    assert publish.verified(b"wheel", good, "a.whl") == b"wheel"
    with pytest.raises(RuntimeError, match="SHA-256 is"):
        publish.verified(b"tampered", good, "a.whl")


def test_pyodide_wheel_is_checked_against_the_pyodide_lock(tmp_path: Path) -> None:
    """NFR-MAINT-005: a Pyodide package is checked on download and again when the cache is used."""
    lock = {
        "packages": {"six": {"file_name": "six.whl", "sha256": hashlib.sha256(b"six").hexdigest()}}
    }
    with (
        patch.object(publish, "WHEELS", tmp_path),
        patch.object(publish, "lock_file", return_value=lock),
        patch.object(publish, "pyodide_version", return_value="1.0"),
        patch.object(publish, "download_pyodide", return_value=b"other"),
        pytest.raises(RuntimeError, match="SHA-256 is"),
    ):
        publish.pyodide_wheel(tmp_path, "six")
    assert not (tmp_path / "six.whl").exists()
    with (
        patch.object(publish, "WHEELS", tmp_path),
        patch.object(publish, "lock_file", return_value=lock),
        patch.object(publish, "pyodide_version", return_value="1.0"),
        patch.object(publish, "download_pyodide", return_value=b"six"),
    ):
        assert publish.pyodide_wheel(tmp_path, "six").read_bytes() == b"six"
        (tmp_path / "six.whl").write_bytes(b"changed on disk")
        with pytest.raises(RuntimeError, match="SHA-256 is"):
            publish.pyodide_wheel(tmp_path, "six")


def test_pypi_wheels_have_hashes_in_uv_lock() -> None:
    """NFR-MAINT-005: every wheel the build takes from PyPI can be checked against uv.lock."""
    lock = publish.tomllib.loads((publish.ROOT / "uv.lock").read_text(encoding="utf-8"))
    names = {
        wheel["url"].rsplit("/", 1)[-1]
        for package in lock["package"]
        for wheel in package.get("wheels", [])
    }
    for prefix in (
        f"flet-{publish.flet_version()}-",
        f"repath-{publish.REPATH_VERSION}-",
        f"openpyxl-{publish.package_version('openpyxl')}-",
        f"et_xmlfile-{publish.package_version('et_xmlfile')}-",
    ):
        found = [name for name in names if name.startswith(prefix)]
        assert found, prefix
        assert len(publish.locked_wheel_sha256(found[0])) == 64
    with pytest.raises(RuntimeError, match="not in uv"):
        publish.locked_wheel_sha256("nothing-0.0-py3-none-any.whl")
