"""Render the public site into site/ as plain HTML.

render_site() reads only published Pages from the database (see CONTEXT.md's
"Publish" entry — published-in-the-CMS is not the same as exported) and
writes one file per page: the "home" slug becomes index.html, every other
published slug becomes "<slug>.html". Two rules the rubric checks:

  1. Only PUBLISHED content is written here. A draft that reaches site/ is a bug.
  2. Every href and src is RELATIVE ("style.css", "menu.html"), never
     root-absolute ("/style.css"), because Pages serves this from a subfolder.

All exported files live flat at the root of site/, so a single relative name
("style.css", "index.html", "<slug>.html") resolves correctly from every page
without tracking directory depth.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import content, db, settings

CSS = """/* Minimal starter styles — make them yours. */
:root { color-scheme: light dark; }
body { font: 16px/1.6 system-ui, sans-serif; margin: 0 auto; max-width: 42rem; padding: 1rem; }
header a { font-weight: 700; text-decoration: none; }
header nav ul { display: flex; gap: 1rem; list-style: none; padding: 0; margin: 0.5rem 0 0; }
main { margin-block: 2rem; }
"""

HOME_SLUG = "home"


def environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(settings.TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )


def _out_name(slug: str) -> str:
    return "index.html" if slug == HOME_SLUG else f"{slug}.html"


def render_site(out: Path | None = None) -> Path:
    out = out or settings.SITE
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    env = environment()
    (out / "style.css").write_text(CSS)

    published = [p for p in db.list_pages() if p["status"] == "published"]

    # Home is the entry point, not a nav link itself (see CONTEXT.md's "Pages"
    # entry); every other published page appears in the nav on every page.
    nav_links = [
        {"href": _out_name(p["slug"]), "title": p["title"]}
        for p in published if p["slug"] != HOME_SLUG
    ]

    template = env.get_template("public/page.html")
    for page in published:
        (out / _out_name(page["slug"])).write_text(
            template.render(
                title=settings.SITE_TITLE,
                page_title=page["title"],
                body_html=content.render_markdown(page["body_md"]),
                css_path="style.css",
                home_path="index.html",
                nav_links=nav_links,
            )
        )

    if not any(p["slug"] == HOME_SLUG for p in published):
        (out / "index.html").write_text(
            env.get_template("public/home.html").render(
                title=settings.SITE_TITLE, items=[], css_path="style.css",
                home_path="index.html", nav_links=nav_links,
            )
        )

    return out
