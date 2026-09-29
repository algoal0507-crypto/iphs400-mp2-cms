"""T03: publish pipeline. Extends the T00 publish tests (tests/test_t00.py) to
cover real Page content: draft exclusion, relative paths, and nav reachability.

Seam 2 per spec #1: render_site() reads only status='published' rows and
writes site/ with one file per published Page. No test reaches into the
database to check anything a visitor couldn't observe by reading the
exported HTML.
"""
from __future__ import annotations

import re

from app import db
from app.publish import render_site


def _set_page(slug, *, status, body_md=None):
    page = db.get_page_by_slug(slug)
    db.update_page(
        slug,
        title=page["title"],
        body_md=body_md if body_md is not None else f"Content for {slug}.",
        status=status,
        author_id=None,
    )


def _publish_all():
    for slug in db.PAGE_SLUGS:
        _set_page(slug, status="published")


def test_home_is_rendered_from_real_page_content(tmp_path):
    _publish_all()
    out = render_site(tmp_path / "site")
    html = (out / "index.html").read_text()
    assert "Content for home" in html


def test_other_published_pages_are_written(tmp_path):
    _publish_all()
    out = render_site(tmp_path / "site")
    assert "Content for menu" in (out / "menu.html").read_text()
    assert "Content for our-story" in (out / "our-story.html").read_text()


def test_draft_page_is_never_written_to_site(tmp_path):
    _set_page("home", status="published")
    _set_page("menu", status="draft")
    _set_page("our-story", status="published")

    out = render_site(tmp_path / "site")

    assert not (out / "menu.html").exists()
    for f in out.rglob("*.html"):
        assert "Content for menu" not in f.read_text()


def test_all_published_html_uses_relative_paths(tmp_path):
    _publish_all()
    out = render_site(tmp_path / "site")
    for f in out.rglob("*.html"):
        html = f.read_text()
        assert 'href="/' not in html
        assert 'src="/' not in html


def test_every_published_page_is_reachable_from_home(tmp_path):
    _publish_all()
    out = render_site(tmp_path / "site")

    home_html = (out / "index.html").read_text()
    hrefs = set(re.findall(r'href="([^"]+)"', home_html))
    assert {"menu.html", "our-story.html"} <= hrefs


def test_non_home_pages_link_back_to_home(tmp_path):
    _publish_all()
    out = render_site(tmp_path / "site")
    menu_html = (out / "menu.html").read_text()
    assert 'href="index.html"' in menu_html


def test_a_page_in_draft_is_excluded_but_others_still_publish(tmp_path):
    """Acceptance criterion: publishing with one page still in draft."""
    _set_page("home", status="published")
    _set_page("menu", status="draft")
    _set_page("our-story", status="published")

    out = render_site(tmp_path / "site")

    assert (out / "index.html").exists()
    assert (out / "our-story.html").exists()
    assert not (out / "menu.html").exists()


def test_unpublishing_then_republishing_removes_it_from_the_export(tmp_path):
    _publish_all()
    out_dir = tmp_path / "site"
    render_site(out_dir)
    assert (out_dir / "menu.html").exists()

    _set_page("menu", status="draft")
    render_site(out_dir)

    assert not (out_dir / "menu.html").exists()


def test_markdown_is_sanitized_in_the_export(tmp_path):
    _set_page(
        "home", status="published",
        body_md='<script>alert(1)</script><img src=x onerror="alert(2)">Tacos',
    )
    _set_page("menu", status="published")
    _set_page("our-story", status="published")

    out = render_site(tmp_path / "site")
    html = (out / "index.html").read_text()
    # The payload must not survive as a live tag/attribute. MarkdownIt is
    # built with html=False (see app/content.py), so raw HTML in the source
    # is escaped to inert text — "<script" and "onerror=" as literal,
    # non-executable characters is the expected, safe outcome.
    assert "<script>" not in html
    assert not re.search(r'<[^>]+\bonerror\s*=', html)
    assert "Tacos" in html


def test_a_page_slugged_index_is_rejected(client_as):
    """Regression: "index" would collide with home's exported index.html
    and silently overwrite it (see app/db.py's _RESERVED_SLUGS)."""
    manager = client_as("admin")
    response = manager.get("/admin/pages/new")
    csrf = response.cookies["csrf_token"]
    response = manager.post(
        "/admin/pages/new",
        data={"slug": "index", "title": "Index", "body_md": "x",
              "status": "published", "csrf_token": csrf},
    )
    assert response.status_code == 400
    assert db.get_page_by_slug("index") is None


def test_draft_home_falls_back_to_placeholder_with_nav_intact(tmp_path):
    """Regression: when Home itself is a draft, the placeholder fallback
    must still carry nav_links so Menu/Our Story stay reachable."""
    _set_page("home", status="draft")
    _set_page("menu", status="published")
    _set_page("our-story", status="published")

    out = render_site(tmp_path / "site")

    home_html = (out / "index.html").read_text()
    hrefs = set(re.findall(r'href="([^"]+)"', home_html))
    assert {"menu.html", "our-story.html"} <= hrefs


def test_a_freshly_created_extra_page_is_reachable_once_published(tmp_path):
    """Pages aren't limited to the seeded three (see CONTEXT.md)."""
    _publish_all()
    db.create_page(
        "events", title="Events", body_md="Coming soon.",
        status="published", author_id=None,
    )

    out = render_site(tmp_path / "site")

    assert (out / "events.html").exists()
    home_hrefs = set(re.findall(r'href="([^"]+)"', (out / "index.html").read_text()))
    assert "events.html" in home_hrefs
