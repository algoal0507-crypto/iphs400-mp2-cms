"""T09: visual design. Observed the way a visitor or the Manager would see it:
the exported HTML/CSS in site/ and the rendered admin pages.

Not tested here: how it looks. That is checked in a browser at phone and
desktop widths (screenshots under docs/screenshots/).
"""
from __future__ import annotations

import re

import pytest

from app import db
from app.publish import render_site

HOME_BODY = (
    "## Visit\n\n**Address:** Monte Everest 780\n\n[Get directions](https://maps.example.test/x)\n\n"
    "[PLACEHOLDER: storefront photo]\n"
)


@pytest.fixture
def site(tmp_path):
    for slug in db.PAGE_SLUGS:
        page = db.get_page_by_slug(slug)
        db.update_page(slug, title=page["title"],
                       body_md=HOME_BODY if slug == "home" else f"Body of {slug}.",
                       status="published", author_id=None)
    return render_site(tmp_path / "site")


def _html(site, name):
    return (site / name).read_text()


# --- Public site -------------------------------------------------------------

def test_home_has_a_hero_then_visiting_info_then_entry_points(site):
    html = _html(site, "index.html")
    hero, visit, entries = html.find('class="hero"'), html.find("Monte Everest 780"), html.find('class="entry-points"')
    assert -1 < hero < visit < entries
    assert html.count("<h1") == 1  # the hero heading; no stray "Home" title


@pytest.mark.parametrize("target", ["menu.html", "our-story.html", "news.html"])
def test_home_entry_points_link_to_every_section(site, target):
    entries = re.search(r'class="entry-points".*?</section>', _html(site, "index.html"), re.S).group(0)
    assert f'href="{target}"' in entries


def test_other_pages_keep_their_own_title_heading(site):
    assert "<h1>Menu</h1>" in _html(site, "menu.html")


def test_placeholders_render_as_labelled_blocks(site):
    html = _html(site, "index.html")
    assert re.search(r'class="placeholder"[^>]*>\s*(<[^>]+>\s*)*PLACEHOLDER: storefront photo', html)


def test_only_the_registered_web_photos_are_shipped(site):
    """Photos are allowed now (see tests/test_photos_news.py); this guards that nothing
    else is: no originals, no other formats, and every <img> is one of ours."""
    from app.publish import PHOTOS
    shipped = {p.name for p in site.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}}
    expected = {f"{ph.stem}-{w}.jpg" for ph in PHOTOS.values() for w in ph.widths}
    assert shipped == expected
    for page in site.glob("*.html"):
        for tag in re.findall(r"<img\b[^>]*>", page.read_text()):
            assert 'src="images/' in tag and 'alt="' in tag, tag


def test_pages_load_nothing_from_other_sites(site):
    for page in site.glob("*.html"):
        html = page.read_text()
        for tag in re.findall(r"<(?:link|script|img|iframe)\b[^>]*>", html):
            assert "http" not in tag and 'src="/' not in tag and 'href="/' not in tag, tag
    css = _html(site, "style.css")
    assert "@import" not in css and "url(http" not in css and "//" not in re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def test_footer_says_this_is_not_the_restaurants_site(site):
    for name in ("index.html", "menu.html", "news.html"):
        assert "not affiliated" in _html(site, name).lower()


def test_stylesheet_is_responsive_and_uses_the_palette(site):
    css = _html(site, "style.css")
    assert "@media" in css
    assert "--ivory" in css and "--burgundy" in css and "--charcoal" in css
    assert 'name="viewport"' in _html(site, "index.html")


def test_news_posts_and_index_use_the_shared_layout(site):
    db.create_post("hello", title="Hello", body_md="Hi.", author_id=None)
    db.set_post_status("hello", "published", published_at="2026-10-01 12:00:00")
    render_site(site)
    index = _html(site, "news.html")
    assert 'class="post-list"' in index and "2026-10-01" in index
    assert "<h1>Hello</h1>" in _html(site, "news-hello.html")


# --- Admin console -----------------------------------------------------------

def test_admin_nav_is_the_same_on_every_screen_and_role_aware(client_as):
    admin = client_as("admin")
    for path in ("/admin/dashboard", "/admin/content", "/admin/posts", "/admin/users"):
        html = admin.get(path).text
        assert 'class="admin-nav"' in html, path
        for label in ("Dashboard", "Content", "News", "Pages", "Users", "Log out"):
            assert label in html, (path, label)


def test_editor_nav_has_no_manager_links(client_as):
    editor = client_as("editor")
    for path in ("/admin/dashboard", "/admin/content", "/admin/posts"):
        nav = re.search(r'class="admin-nav".*?</nav>', editor.get(path).text, re.S).group(0)
        assert "Log out" in nav and "News" in nav
        assert "Users" not in nav and "Pages" not in nav, path


def test_login_page_has_no_admin_nav(client):
    html = client.get("/login").text
    assert 'class="admin-nav"' not in html and "Log out" not in html


def test_dashboard_shows_cards(client_as):
    html = client_as("admin").get("/admin/dashboard").text
    assert html.count('class="card') >= 3
    assert 'data-count="news-draft"' in html  # existing hooks survive


def test_admin_forms_use_styled_buttons(client_as):
    html = client_as("admin").get("/admin/posts/new").text
    assert re.search(r'<button[^>]*class="[^"]*\bbtn\b', html)


def test_admin_stylesheet_is_the_public_stylesheet(client_as, site):
    assert client_as("admin").get("/admin/style.css").text == _html(site, "style.css")


# --- Review follow-ups -------------------------------------------------------

def test_admin_pages_never_expose_the_password_hash(client_as):
    admin = client_as("admin")
    for path in ("/admin/dashboard", "/admin/users", "/admin/content"):
        html = admin.get(path).text
        assert "argon2" not in html and "password_hash" not in html, path


def test_every_page_has_a_skip_link_to_main_content(site):
    html = _html(site, "index.html")
    assert 'class="skip-link" href="#main"' in html and 'id="main"' in html


def test_placeholder_markup_cannot_smuggle_html(tmp_path):
    db.update_page("home", title="Home", body_md="[PLACEHOLDER: <img src=x onerror=alert(1)>]",
                   status="published", author_id=None)
    html = (render_site(tmp_path / "site") / "index.html").read_text()
    assert not re.search(r"<img[^>]*(src=x|onerror)", html)  # no live tag or event attribute
    assert "&lt;img src=x onerror=alert(1)&gt;" in html       # it stays escaped text in the caption
