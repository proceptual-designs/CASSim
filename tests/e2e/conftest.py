"""Fixtures for browser tests: build a Flet static site, serve it, drive Edge/Chromium."""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Error, sync_playwright
from tools import webharness

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Use the installed Edge (no download), else Playwright's Chromium, else skip."""
    with sync_playwright() as p:
        for channel in ("msedge", "chrome", None):
            try:
                b = p.chromium.launch(headless=True, channel=channel)
            except Error:
                continue
            yield b
            b.close()
            return
    pytest.skip("no Chromium-family browser available")


@pytest.fixture(scope="session")
def build(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str], Path]:
    """Return a function that publishes a spike app once per session and serves it."""
    cache: dict[str, Path] = {}

    def _build(name: str) -> Path:
        if name not in cache:
            dist = tmp_path_factory.mktemp(f"dist-{name}")
            webharness.publish(ROOT / "spikes" / name, dist)
            cache[name] = dist
        return cache[name]

    return _build
