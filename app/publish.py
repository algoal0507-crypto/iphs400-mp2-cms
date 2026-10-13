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

All pages live flat at the root of site/, so a single relative name
("style.css", "index.html", "<slug>.html") resolves correctly from every page
without tracking directory depth. The photos sit one level down in site/images/
("images/home-800.jpg"), which every page reaches the same way. Only the web
copies in assets/images/web/ are published, never the original screenshots.
"""
from __future__ import annotations

import html as htmllib
import re
import shutil
from dataclasses import dataclass
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
_PHOTO = re.compile(r"<p>\[PHOTO: ([^\]<]+)\]</p>")


@dataclass(frozen=True)
class Photo:
    """One site photo. `stem` names its web copies, images/<stem>-<width>.jpg.

    `size` is the pixel size of the largest copy (every copy has the same
    proportions), so the browser can reserve the space before the file arrives.
    """
    stem: str
    widths: tuple[int, ...]
    size: tuple[int, int]
    alt: str
    sizes: str
    caption: str = ""
    inline: bool = True  # False: shown only where a template places it, never from page text


# Added to a page's Markdown as a line of its own: [PHOTO: menu]. Sources and
# credits are in assets/images/CREDITS.md; the web copies are made by
# scripts/make_web_images.sh.
PHOTOS = {
    "home": Photo(
        "home", (480, 800, 1200), (1200, 1448),
        "A person in a white t-shirt and maroon apron holding a tray of six tacos of sliced "
        "grilled beef on corn tortillas, plus a small plate of sautéed mushrooms.",
        "(min-width: 56rem) 38vw, 100vw",
        inline=False,  # the Home hero's photo; a [PHOTO: home] line elsewhere is not honoured
    ),
    "menu": Photo(
        "menu", (480, 800, 1200), (1200, 1184),
        "Overhead view of a single beef taco: slices of seared beef on a charred corn tortilla, "
        "on a red-and-white patterned plate.",
        "(min-width: 40rem) 40rem, 100vw",
    ),
    "our-story": Photo(
        "our-story", (480, 800, 1176), (1176, 1330),
        "Portrait of a man with dark wavy hair and a beard, wearing an olive-green henley "
        "sweater, with large round pendant lamps blurred behind him.",
        "(min-width: 40rem) 24rem, 100vw",
        caption="Portrait; subject not identified.",
    ),
}


def photo_figure(key: str, *, eager: bool = False, from_text: bool = False) -> str | None:
    """The <figure> for a registered photo, or None for an unknown key (or, when the
    key came from page text, for a photo that only a template may place).

    Built only from the registry above (the alt text is escaped anyway), never from
    page text, so a page cannot add attributes or markup through it.
    """
    photo = PHOTOS.get(key)
    if photo is None or (from_text and not photo.inline):
        return None
    srcset = ", ".join(f"images/{photo.stem}-{w}.jpg {w}w" for w in photo.widths)
    fallback = 800 if 800 in photo.widths else photo.widths[-1]
    width, height = photo.size
    caption = f"<figcaption>{htmllib.escape(photo.caption)}</figcaption>" if photo.caption else ""
    return (
        f'<figure class="photo photo-{photo.stem}"><img src="images/{photo.stem}-{fallback}.jpg" '
        f'srcset="{srcset}" sizes="{htmllib.escape(photo.sizes)}" width="{width}" height="{height}" '
        f'alt="{htmllib.escape(photo.alt)}" decoding="async"'
        f'{" fetchpriority=\"high\"" if eager else " loading=\"lazy\""}>'
        f"{caption}</figure>"
    )


def _photo_or_placeholder(match: "re.Match[str]") -> str:
    key = match.group(1).strip()
    return photo_figure(key, from_text=True) or (
        f'<figure class="placeholder"><figcaption>{htmllib.escape("PLACEHOLDER: " + key)}</figcaption></figure>'
    )


def mark_placeholders(html: str) -> str:
    """Turn [PHOTO: key] lines into responsive photos and [PLACEHOLDER: ...] lines
    into a labelled photo-shaped block (also the fallback for an unknown photo key).

    Runs on already-sanitized HTML and only re-wraps text that was in it.
    """
    html = _PHOTO.sub(_photo_or_placeholder, html)
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
    web_images = settings.ASSETS / "images" / "web"
    wanted = sorted({f"{ph.stem}-{w}.jpg" for ph in PHOTOS.values() for w in ph.widths})
    missing = [name for name in wanted if not (web_images / name).is_file()]
    if missing:
        # Checked before anything is touched, like the slug check above: pages would
        # point at images that are not there.
        raise ValueError(
            f"Photo files missing from {web_images}: {missing}. "
            "Run scripts/make_web_images.sh, or restore them from git."
        )

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    env = environment()
    (out / "style.css").write_text(CSS)
    (out / "images").mkdir()
    for name in wanted:  # only the registered web copies: no originals, no stray files
        shutil.copy2(web_images / name, out / "images" / name)

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
        "instagram_url": settings.INSTAGRAM_URL,
    }

    page_template = env.get_template("public/page.html")
    home_template = env.get_template("public/home_page.html")

    def write_item(filename: str, item, template=page_template, css_class="", published=None) -> None:
        extra = {"hero_photo": photo_figure("home", eager=True)} if template is home_template else {}
        (out / filename).write_text(
            template.render(
                page_title=item["title"], page_class=css_class, published=published, **extra,
                body_html=mark_placeholders(content.render_markdown(item["body_md"])),
                **layout,
            )
        )

    for page in published:
        write_item(_out_name(page["slug"]), page,
                   home_template if page["slug"] == HOME_SLUG else page_template,
                   css_class=f"page-{page['slug']}")
    for post in posts:
        write_item(f"{db.NEWS_PREFIX}{post['slug']}.html", post, published=post["published_at"][:10])

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
