"""Build the help site (the wiki) from `docs/wiki/*.md` into static HTML.

    python -m tools.wiki_site [--dist DIR]

`docs/wiki/` is the source of truth. Each page becomes `<name>.html` (`Home.md` becomes
`index.html`), `_Sidebar.md` becomes the navigation on every page, and `[[Page name]]` or
`[[text|Page name]]` links to `Page-name.html`. A link to a page that does not exist stops the
build. The site is deployed to its own Cloudflare Pages project, and the app's Help link points
at it (`cassim.app.about.WIKI_URL`).
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "wiki"
DEFAULT_DIST = ROOT / "build" / "wiki"
SIDEBAR = "_Sidebar"
WIKI_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

CSS = """
:root { color-scheme: dark; --bg: #1e1e1e; --fg: #e6e6e6; --muted: #a0a0a0;
  --accent: #6aa9ff; --line: #3a3a3a; --code: #2a2a2a; }
@media (prefers-color-scheme: light) {
  :root { color-scheme: light; --bg: #ffffff; --fg: #1e1e1e; --muted: #5a5a5a;
    --accent: #1f5fbf; --line: #d8d8d8; --code: #f2f2f2; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.wrap { display: flex; gap: 32px; max-width: 1100px; margin: 0 auto; padding: 24px 16px; }
nav { flex: 0 0 220px; font-size: 15px; }
nav ul { list-style: none; padding: 0; margin: 0; }
nav li { margin: 4px 0; }
nav a[aria-current] { font-weight: 600; color: var(--fg); }
main { flex: 1; min-width: 0; }
a { color: var(--accent); }
h1, h2, h3 { line-height: 1.25; }
code { background: var(--code); padding: 1px 4px; border-radius: 4px; }
pre { background: var(--code); padding: 12px; overflow-x: auto; border-radius: 6px; }
pre code { padding: 0; }
table { border-collapse: collapse; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: 4px 10px; text-align: left; }
blockquote { margin: 0; padding: 4px 16px; border-left: 4px solid var(--accent);
  color: var(--muted); }
@media (max-width: 720px) { .wrap { flex-direction: column; gap: 8px; }
  nav { flex: none; border-bottom: 1px solid var(--line); padding-bottom: 8px; } }
"""

PAGE = """<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · CASSim help</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="wrap">
<nav aria-label="Help pages">{nav}</nav>
<main>{body}</main>
</div>
</body>
</html>
"""


def file_name(page: str) -> str:
    """The HTML file for a page name or file stem: `Getting started` -> `Getting-started.html`."""
    stem = page.strip().replace(" ", "-")
    return "index.html" if stem == "Home" else f"{stem}.html"


def link_wiki_pages(text: str, known: set[str]) -> str:
    """Turn `[[Page]]` and `[[text|Page]]` into Markdown links; unknown pages raise ValueError."""

    def replace(match: re.Match[str]) -> str:
        first, second = match.group(1).strip(), match.group(2)
        label, target = (first, second.strip()) if second else (first, first)
        name = file_name(target)
        if name not in known:
            raise ValueError(f"[[{target}]] links to a page that does not exist")
        return f"[{label}]({name})"

    return WIKI_LINK.sub(replace, text)


def title_of(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def build(dist: Path = DEFAULT_DIST, source: Path = SOURCE) -> list[Path]:
    """Write the site into `dist` (replaced) and return the pages written."""
    pages = sorted(p for p in source.glob("*.md") if not p.stem.startswith("_"))
    known = {file_name(p.stem) for p in pages}
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    sidebar = source / f"{SIDEBAR}.md"
    nav_md = link_wiki_pages(sidebar.read_text(encoding="utf-8"), known) if sidebar.exists() else ""

    dist = dist.resolve()
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    (dist / "style.css").write_text(CSS.lstrip(), encoding="utf-8", newline="\n")
    written = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        name = file_name(page.stem)
        nav = md.render(nav_md).replace(f'href="{name}"', f'href="{name}" aria-current="page"')
        out = dist / name
        out.write_text(
            PAGE.format(
                title=html.escape(title_of(text, page.stem.replace("-", " "))),
                nav=nav,
                body=md.render(link_wiki_pages(text, known)),
            ),
            encoding="utf-8",
            newline="\n",
        )
        written.append(out)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    written = build(args.dist)
    print(f"built {args.dist.resolve()} : {len(written)} pages")


if __name__ == "__main__":
    main()
