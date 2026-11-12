"""The help site built from `docs/wiki/` (tools/wiki_site.py)."""

import re
from pathlib import Path

import pytest
from tools import wiki_site


def test_every_wiki_page_builds_and_every_link_resolves(tmp_path: Path) -> None:
    written = wiki_site.build(tmp_path / "wiki")
    names = {p.name for p in written}
    sources = [p for p in wiki_site.SOURCE.glob("*.md") if not p.stem.startswith("_")]
    assert len(written) == len(sources)
    assert "index.html" in names
    assert (tmp_path / "wiki" / "style.css").exists()
    for page in written:
        text = page.read_text(encoding="utf-8")
        assert "[[" not in text
        for href in re.findall(r'href="([^"]+)"', text):
            if not href.startswith(("http:", "https:", "#")):
                assert (tmp_path / "wiki" / href).exists(), f"{page.name}: {href}"


def test_the_current_page_is_marked_in_the_navigation(tmp_path: Path) -> None:
    wiki_site.build(tmp_path)
    text = (tmp_path / "Getting-started.html").read_text(encoding="utf-8")
    assert 'href="Getting-started.html" aria-current="page"' in text
    assert "<title>Getting started · CASSim help</title>" in text


def test_wiki_links_with_and_without_a_label() -> None:
    known = {"index.html", "The-two-views.html"}
    assert wiki_site.link_wiki_pages("[[Home]]", known) == "[Home](index.html)"
    assert (
        wiki_site.link_wiki_pages("[[views|The two views]]", known) == "[views](The-two-views.html)"
    )


def test_a_link_to_a_missing_page_stops_the_build() -> None:
    with pytest.raises(ValueError, match="Nowhere"):
        wiki_site.link_wiki_pages("see [[Nowhere]]", {"index.html"})
