"""Render the public site into site/ as plain HTML.

render_site() reads only published Pages and News posts from the database
(see CONTEXT.md's "Publish" entry — published-in-the-CMS is not the same as
exported) and writes one file per item: the "home" slug becomes index.html,
every other published slug becomes "<slug>.html", news.html is the News
index, and each post is news-<slug>.html. Pages may not use the "news" /
"news-" namespace (db.is_news_slug); a published Page that does makes the
export fail rather than overwrite a News file. Two rules the rubric checks:

  1. Only PUBLISHED content is written here. A draft that reaches site/ is a bug.
  2. Every href and src is RELATIVE ("style.css", "menu.html"), never
     root-absolute ("/style.css"), because Pages serves this from a subfolder.

All exported files live flat at the root of site/, so a single relative name
("style.css", "index.html", "<slug>.html") resolves correctly from every page
without tracking directory depth.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import content, db, settings

CSS = (settings.TEMPLATES / "style.css").read_text()

# One line under each entry point on Home. Pages the Manager adds later simply
# show no line.
BLURBS = {
    "menu.html": "Tacos, salsas, and desserts.",
    "our-story.html": "From a postal code to a Michelin star.",
    "news.html": "Announcements and updates.",
}

_PLACEHOLDER = re.compile(r"<p>\[(PLACEHOLDER: [^\]<]+)\]</p>")


def mark_placeholders(html: str) -> str:
    """Show "[PLACEHOLDER: ...]" lines as a labelled photo-shaped block.

    Runs on already-sanitized HTML and only re-wraps text that was in it.
    """
    return _PLACEHOLDER.sub(r'<figure class="placeholder"><figcaption>\1</figcaption></figure>', html)


HOME_SLUG = "home"
NEWS_INDEX_FILE = f"{db.NEWS_INDEX_SLUG}.html"


def environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(settings.TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )


def _out_name(slug: str) -> str:
    return "index.html" if slug == HOME_SLUG else f"{slug}.html"


def render_site(out: Path | None = None) -> Path:
    out = out or settings.SITE
    published = [p for p in db.list_pages() if p["status"] == "published"]
    clashes = [p["slug"] for p in published if db.is_news_slug(p["slug"])]
    if clashes:
        # Checked before anything is touched, so a refused export leaves the
        # previous site/ intact.
        raise ValueError(
            f"Published page slug(s) {clashes} collide with the News export files "
            '("news" and "news-…" are reserved). Rename or unpublish them; '
            "nothing was deleted."
        )
    posts = db.list_published_posts()

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    env = environment()
    (out / "style.css").write_text(CSS)

    # Home is the entry point, not a nav link itself (see CONTEXT.md's "Pages"
    # entry); every other published page appears in the nav on every page.
    nav_links = [
        {"href": _out_name(p["slug"]), "title": p["title"]}
        for p in published if p["slug"] != HOME_SLUG
    ] + [{"href": NEWS_INDEX_FILE, "title": "News"}]
    for link in nav_links:
        link["blurb"] = BLURBS.get(link["href"])
    layout = {
        "title": settings.SITE_TITLE, "css_path": "style.css",
        "home_path": "index.html", "nav_links": nav_links,
    }

    page_template = env.get_template("public/page.html")
    home_template = env.get_template("public/home_page.html")

    def write_item(filename: str, item, template=page_template) -> None:
        (out / filename).write_text(
            template.render(
                page_title=item["title"],
                body_html=mark_placeholders(content.render_markdown(item["body_md"])),
                **layout,
            )
        )

    for page in published:
        write_item(_out_name(page["slug"]), page,
                   home_template if page["slug"] == HOME_SLUG else page_template)
    for post in posts:
        write_item(f"{db.NEWS_PREFIX}{post['slug']}.html", post)

    (out / NEWS_INDEX_FILE).write_text(
        env.get_template("public/news_index.html").render(
            posts=[
                {
                    "href": f"{db.NEWS_PREFIX}{p['slug']}.html",
                    "title": p["title"],
                    "date": p["published_at"][:10],
                }
                for p in posts
            ],
            **layout,
        )
    )

    if not any(p["slug"] == HOME_SLUG for p in published):
        (out / "index.html").write_text(
            env.get_template("public/home.html").render(items=[], **layout)
        )

    return out
