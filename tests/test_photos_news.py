"""Follow-up to #10: the three site photos, the Madrid and Michelin News posts, and
the Instagram links. Checked on the exported site and on the seed/refresh helpers.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

import pytest

from app import db
from app.publish import render_site
from tests.test_public_copy import _save, seed, site  # noqa: F401  (fixtures)

ROOT = Path(__file__).resolve().parents[1]
INSTAGRAM = "https://www.instagram.com/tacoslaoncemil/"
MADRID_SOURCE = ("https://www.mateoandco.es/2026/09/14/la-once-mil-la-taqueria-que-cambio-la-manera-"
                 "de-comer-tacos-en-cdmx-llega-a-madrid-de-la-mano-de-los-33/")
MICHELIN_SOURCE = ("https://guide.michelin.com/us/en/article/michelin-guide-ceremony/"
                   "every-michelin-starred-restaurant-in-mexico-for-2026-and-the-year-s-key-trends")
ORIGINALS = ("IMG_8489.jpg", "IMG_8452.jpg", "portrait.png")


def _html(site, name):
    return (site / name).read_text()


def _imgs(html):
    return re.findall(r"<img\b[^>]*>", html)


def _attr(tag, name):
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return m.group(1) if m else None


def _jpeg_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    i = 2
    while i < len(data):
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    raise AssertionError(f"no size in {path}")


# --- Photos: files ------------------------------------------------------------------

def test_the_originals_are_kept_and_are_not_published(site):
    for name in ORIGINALS:
        assert (ROOT / "assets" / "images" / name).is_file(), name
    published = {p.name for p in (site / "images").rglob("*") if p.is_file()}
    assert not published & set(ORIGINALS)  # the screenshots (with their controls) never ship
    assert {"home-480.jpg", "home-800.jpg", "home-1200.jpg", "menu-800.jpg", "our-story-800.jpg"} <= published


@pytest.mark.parametrize("stem,original_size", [("home", (1206, 1456)), ("menu", (1206, 1190)),
                                                ("our-story", (1176, 1330))])
def test_web_copies_keep_the_cropped_proportions(site, stem, original_size):
    """Nothing is stretched: every size has the same width:height as the crop."""
    want = original_size[0] / original_size[1]
    sizes = sorted((site / "images").glob(f"{stem}-*.jpg"))
    assert len(sizes) == 3
    for path in sizes:
        w, h = _jpeg_size(path)
        assert abs(w / h - want) < 0.01, (path.name, w, h)


def test_every_image_on_every_page_is_complete_relative_and_exists(site):
    count = 0
    for page in site.glob("*.html"):
        for tag in _imgs(page.read_text()):
            count += 1
            src = _attr(tag, "src")
            assert src and not src.startswith(("/", "http")), tag
            assert (site / src).is_file(), (page.name, src)
            for part in (_attr(tag, "srcset") or "").split(","):
                url = part.strip().split(" ")[0]
                assert url and not url.startswith(("/", "http")) and (site / url).is_file(), url
            assert (_attr(tag, "alt") or "").strip(), f"no alt text: {tag}"
            assert _attr(tag, "width") and _attr(tag, "height"), f"no size: {tag}"
    assert count == 3  # one photo each on Home, Menu, and Our Story


# --- Photos: placement --------------------------------------------------------------

def test_home_photo_sits_in_the_hero_beside_the_introduction(site):
    html = _html(site, "index.html")
    hero = re.search(r'<section class="hero">.*?</section>', html, re.S).group(0)
    assert "<h1" in hero and "<img" in hero
    assert 'srcset="images/home-480.jpg 480w, images/home-800.jpg 800w, images/home-1200.jpg 1200w"' in hero
    assert 'loading="lazy"' not in hero  # above the fold


def test_menu_photo_is_above_the_dish_sections(site):
    html = _html(site, "menu.html")
    img, first_section = html.find("<img"), html.find("<h2")
    assert 0 < img < first_section
    assert 'srcset="images/menu-480.jpg 480w' in html


def test_our_story_portrait_has_a_neutral_caption_and_no_identity(site):
    html = _html(site, "our-story.html")
    figure = re.search(r"<figure class=\"photo[^\"]*\">.*?</figure>", html, re.S).group(0)
    alt = _attr(_imgs(figure)[0], "alt")
    assert "portrait" in alt.lower()
    for name in ("César", "Cesar", "de la Parra", "chef", "Glennie", "owner"):
        assert name.lower() not in figure.lower(), name  # no identity from appearance
    assert "subject not identified" in figure.lower()


def test_the_portrait_stands_alone_after_the_text_not_beside_the_names(site):
    html = _html(site, "our-story.html")
    assert html.find("<figure") > html.find("keeping the spirit of a taquería")  # after every paragraph
    assert "float" not in (site / "style.css").read_text().split(".page-our-story")[-1][:400]


def test_food_photos_describe_the_food_in_their_alt_text(site):
    assert "tacos" in _attr(_imgs(_html(site, "index.html"))[0], "alt").lower()
    assert "taco" in _attr(_imgs(_html(site, "menu.html"))[0], "alt").lower()


def test_no_placeholder_blocks_remain_on_the_three_pages(site):
    for name in ("index.html", "menu.html", "our-story.html"):
        assert "PLACEHOLDER" not in _html(site, name), name


def test_an_unknown_photo_marker_falls_back_to_a_labelled_placeholder(tmp_path, seed):
    page = db.get_page_by_slug("menu")
    _save("menu", page["body_md"].replace("[PHOTO: menu]", "[PHOTO: no-such-photo]"))
    html = _html(render_site(tmp_path / "out"), "menu.html")
    assert "<img" not in html and 'class="placeholder"' in html and "no-such-photo" in html


def test_photo_markers_cannot_smuggle_markup(tmp_path, seed):
    _save("menu", "Intro.\n\n[PHOTO: menu\"><script>alert(1)</script>]\n")
    html = _html(render_site(tmp_path / "out"), "menu.html")
    assert "<script>alert(1)" not in html


def test_photo_sources_are_recorded_honestly():
    credits = (ROOT / "assets" / "images" / "CREDITS.md").read_text()
    for name in ORIGINALS:
        assert name in credits
    assert "permission" in credits.lower() and "not recorded" in credits.lower()
    assert "not identified" in credits.lower()


# --- Instagram ----------------------------------------------------------------------

def test_home_has_a_follow_on_instagram_button_in_the_hero(site):
    hero = re.search(r'<section class="hero">.*?</section>', _html(site, "index.html"), re.S).group(0)
    assert re.search(rf'<a [^>]*href="{re.escape(INSTAGRAM)}"[^>]*>\s*Follow on Instagram\s*</a>', hero)


def test_every_public_page_has_an_instagram_link_in_the_footer(site):
    for page in site.glob("*.html"):
        footer = re.search(r"<footer.*?</footer>", page.read_text(), re.S).group(0)
        assert re.search(rf'<a [^>]*href="{re.escape(INSTAGRAM)}"[^>]*rel="noopener noreferrer"[^>]*>Instagram</a>', footer), page.name
        assert "not affiliated" in footer.lower()  # the disclaimer stays


# --- News ---------------------------------------------------------------------------

def _post(site, slug):
    return _html(site, f"news-{slug}.html")


def test_one_michelin_post_says_first_star_and_never_first_taqueria(site):
    michelin = [p for p in site.glob("news-*.html") if "Michelin" in p.read_text()
                and "Madrid" not in p.read_text() and "Seasonal" not in p.read_text()]
    assert [p.name for p in michelin] == ["news-michelin-star.html"]
    text = re.sub(r"<[^>]+>", " ", _post(site, "michelin-star"))
    assert "La Once Mil earns its first Michelin star" in text
    assert "new one-star restaurant" in text and "May 20, 2026" in text
    assert MICHELIN_SOURCE in _post(site, "michelin-star")
    for banned in ("first taquería", "first taqueria", "only taquería", "only taqueria", "so far only"):
        assert banned not in text, banned


def test_madrid_post_has_the_official_facts_and_a_source_link(site):
    html = _post(site, "madrid-opening")
    text = re.sub(r"<[^>]+>", " ", html)
    assert "La Once Mil arrives in Madrid" in text
    for fact in ("September 22, 2026", "Plaza de las Salesas 11", "Los 33", "September 14, 2026"):
        assert fact in text, fact
    assert MADRID_SOURCE in html
    assert "company news" in text.lower()  # not a second visiting location


def test_event_dates_and_publication_dates_are_shown_separately(site):
    for slug, event in (("michelin-star", "May 20, 2026"), ("madrid-opening", "September 22, 2026")):
        html = _post(site, slug)
        published = re.search(r'Published <time datetime="(\d{4}-\d{2}-\d{2})">', html).group(1)
        assert published == "2026-10-13"
        assert event in html and event != published
    index = _html(site, "news.html")
    assert index.count("2026-10-13") >= 2


def test_both_posts_are_published_and_listed_with_demo_posts_labelled(site):
    index = _html(site, "news.html")
    assert "La Once Mil arrives in Madrid" in index and "La Once Mil earns its first Michelin star" in index
    for demo in site.glob("news-seasonal*.html"):
        assert "[DEMO CONTENT]" in demo.read_text()
    assert not list(site.glob("news-holiday*.html"))  # the draft is never exported


def test_home_visiting_information_stays_on_mexico_city(site):
    home = re.sub(r"<[^>]+>", " ", _html(site, "index.html"))
    assert "Madrid" not in home and "Salesas" not in home
    assert "Monte Everest 780" in home


# --- Keeping saved content and re-running safely ------------------------------------

def test_refresh_updates_an_old_michelin_post_in_place_without_a_duplicate(seed):
    db.delete_post("michelin-star")
    db.create_post("michelin-star", title=seed.LEGACY_MICHELIN_TITLE, body_md=seed.LEGACY_MICHELIN_BODY,
                   author_id=None, created_at="2026-08-24 12:00:00")
    db.set_post_status("michelin-star", "published", published_at="2026-08-24 12:00:00")
    assert seed.refresh_news() == 1
    post = db.get_post_by_slug("michelin-star")
    assert post["title"] == "La Once Mil earns its first Michelin star" and post["status"] == "published"
    assert post["published_at"].startswith("2026-10-13")
    assert [p["slug"] for p in db.list_posts() if "michelin" in p["title"].lower()] == ["michelin-star"]
    assert seed.refresh_news() == 0


def test_refresh_leaves_an_edited_michelin_post_alone(seed):
    edited = "We got a Michelin star!"
    db.update_post("michelin-star", title="Our own title", body_md=edited, author_id=None)
    seed.refresh_news()
    post = db.get_post_by_slug("michelin-star")
    assert post["title"] == "Our own title" and post["body_md"] == edited


def test_seed_news_with_only_the_real_posts_creates_exactly_those_two(tmp_path, monkeypatch, seed):
    for post in db.list_posts():
        db.delete_post(post["slug"])
    seed.seed_news(seed.REAL_NEWS)
    assert sorted(p["slug"] for p in db.list_posts()) == ["madrid-opening", "michelin-star"]
    assert all(p["status"] == "published" for p in db.list_posts())
    seed.seed_news(seed.REAL_NEWS)  # safe to run again
    assert len(db.list_posts()) == 2


def test_seed_never_republishes_a_post_the_manager_unpublished(seed):
    db.set_post_status("madrid-opening", "draft")
    seed.seed_news(seed.REAL_NEWS)
    assert db.get_post_by_slug("madrid-opening")["status"] == "draft"


def test_refresh_swaps_old_placeholders_for_photos_and_keeps_edits(seed):
    _save("home", seed.HOME_BODY + "\n[PLACEHOLDER: storefront photo]\n")
    _save("menu", seed.MENU_BODY.replace("[PHOTO: menu]\n\n", "").replace(
        "\n## Tacos", "\n## Tacos", 1).rstrip("\n") + "\n\n[PLACEHOLDER: menu photo]\n" + "\nOpen late on Fridays.\n")
    _save("our-story", seed.OUR_STORY_BODY.replace("\n[PHOTO: our-story]\n", "") + "\n[PLACEHOLDER: chef/kitchen photo]\n")
    assert seed.refresh_public_copy() == 3
    assert "PLACEHOLDER" not in db.get_page_by_slug("home")["body_md"]
    menu = db.get_page_by_slug("menu")["body_md"]
    assert "[PHOTO: menu]" in menu and menu.index("[PHOTO: menu]") < menu.index("## Tacos")
    assert "Open late on Fridays." in menu and "PLACEHOLDER" not in menu
    story = db.get_page_by_slug("our-story")["body_md"]
    assert story.rstrip().endswith("[PHOTO: our-story]") and "PLACEHOLDER" not in story
    assert seed.refresh_public_copy() == 0


def test_refresh_does_not_force_a_photo_back_after_the_manager_removed_it(seed):
    without = seed.MENU_BODY.replace("[PHOTO: menu]\n\n", "")
    _save("menu", without)
    assert seed.refresh_public_copy() == 0
    assert db.get_page_by_slug("menu")["body_md"] == without


# --- Review follow-ups -----------------------------------------------------------------

def test_publish_copies_only_the_registered_files_and_ignores_strays(tmp_path, monkeypatch, seed):
    assets = tmp_path / "assets"
    (assets / "images" / "web").mkdir(parents=True)
    from app import settings
    from app.publish import PHOTOS
    for ph in PHOTOS.values():
        for w in ph.widths:
            (assets / "images" / "web" / f"{ph.stem}-{w}.jpg").write_bytes(b"x")
    (assets / "images" / "web" / ".DS_Store").write_bytes(b"junk")
    (assets / "images" / "web" / "notes.txt").write_text("stray")
    monkeypatch.setattr(settings, "ASSETS", assets)
    out = render_site(tmp_path / "out")
    assert sorted(p.name for p in (out / "images").iterdir()) == sorted(
        f"{ph.stem}-{w}.jpg" for ph in PHOTOS.values() for w in ph.widths)


def test_publish_refuses_to_export_broken_image_links_and_keeps_the_old_site(tmp_path, monkeypatch, seed):
    from app import settings
    out = render_site(tmp_path / "site")
    before = (out / "index.html").read_text()
    monkeypatch.setattr(settings, "ASSETS", tmp_path / "no-assets-here")
    with pytest.raises(ValueError, match="home-480.jpg"):
        render_site(out)
    assert (out / "index.html").read_text() == before  # the previous export is untouched


def test_the_home_photo_belongs_to_the_hero_not_to_page_text(tmp_path, seed):
    page = db.get_page_by_slug("home")
    _save("home", page["body_md"] + "\n[PHOTO: home]\n")
    html = _html(render_site(tmp_path / "out"), "index.html")
    assert len(_imgs(html)) == 1  # only the hero's
    assert 'class="placeholder"' in html


@pytest.mark.parametrize("marker", ['[PHOTO: menu" onerror="alert(1)]', "[PHOTO: menu' onload='x()]",
                                    "[PHOTO: ../../etc/passwd]", "[PHOTO: menu&quot; onerror=1]"])
def test_odd_photo_markers_become_a_labelled_placeholder_never_a_tag_or_path(tmp_path, seed, marker):
    _save("menu", f"Intro.\n\n{marker}\n")
    html = _html(render_site(tmp_path / "out"), "menu.html")
    assert not _imgs(html)
    assert 'class="placeholder"' in html
    assert not re.search(r"<[a-z]+[^>]*\bon\w+=", html) and "etc/passwd" not in re.sub(r"<figcaption>.*?</figcaption>", "", html, flags=re.S)


def test_the_hero_photo_is_loaded_first_and_the_others_lazily(site):
    assert 'fetchpriority="high"' in _imgs(_html(site, "index.html"))[0]
    assert 'loading="lazy"' in _imgs(_html(site, "menu.html"))[0]
    assert 'loading="lazy"' in _imgs(_html(site, "our-story.html"))[0]
