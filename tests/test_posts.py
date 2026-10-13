"""T04: News posts. Editor drafts; only the Manager publishes.

Seam 1 (HTTP): role checks on every route, including hand-crafted POSTs.
Seam 2 (export): render_site() writes news.html and news-<slug>.html for
published posts only.
"""
from __future__ import annotations

import re

import pytest

from app import db
from app.publish import render_site


def _csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def _new_post(client, slug="spring-menu", title="Spring menu", body="Hello.", **extra):
    csrf = _csrf(client, "/admin/posts/new")
    return client.post(
        "/admin/posts/new",
        data={"slug": slug, "title": title, "body_md": body, "csrf_token": csrf, **extra},
        follow_redirects=False,
    )


def test_editor_creates_a_news_post_as_a_draft(client_as):
    editor = client_as("editor")
    response = _new_post(editor)
    assert response.status_code == 303
    post = db.get_post_by_slug("spring-menu")
    assert post["status"] == "draft"
    assert post["author_id"] is not None


def test_editor_cannot_create_a_published_post_by_forging_status(client_as):
    editor = client_as("editor")
    _new_post(editor, status="published")
    assert db.get_post_by_slug("spring-menu")["status"] == "draft"


def _edit(client, slug, **data):
    csrf = _csrf(client, f"/admin/posts/{slug}")
    return client.post(
        f"/admin/posts/{slug}",
        data={"title": "Spring menu", "body_md": "Updated.", "csrf_token": csrf, **data},
        follow_redirects=False,
    )


def test_editor_edits_a_draft_and_it_stays_a_draft_on_every_save(client_as):
    editor = client_as("editor")
    _new_post(editor)
    first = _edit(editor, "spring-menu", body_md="First edit.", status="published")
    second = _edit(editor, "spring-menu", body_md="Second edit.", status="published")
    assert first.status_code == 200 and second.status_code == 200
    post = db.get_post_by_slug("spring-menu")
    assert post["body_md"] == "Second edit."
    assert post["status"] == "draft"


def _action(client, slug, action, *, csrf=None):
    csrf = csrf or _csrf(client, f"/admin/posts/{slug}")
    return client.post(
        f"/admin/posts/{slug}/{action}", data={"csrf_token": csrf}, follow_redirects=False
    )


def test_editor_cannot_publish_via_a_direct_post(client_as):
    editor = client_as("editor")
    _new_post(editor)
    response = _action(editor, "spring-menu", "publish")
    assert response.status_code == 403
    assert db.get_post_by_slug("spring-menu")["status"] == "draft"


def test_editor_cannot_publish_even_with_a_forged_csrf_token(client_as):
    editor = client_as("editor")
    _new_post(editor)
    response = _action(editor, "spring-menu", "publish", csrf="not-a-real-token")
    assert response.status_code == 403
    assert db.get_post_by_slug("spring-menu")["status"] == "draft"


def test_manager_can_publish_and_unpublish_any_post(client_as):
    _new_post(client_as("editor"))
    manager = client_as("admin")
    assert _action(manager, "spring-menu", "publish").status_code == 303
    assert db.get_post_by_slug("spring-menu")["status"] == "published"
    assert _action(manager, "spring-menu", "unpublish").status_code == 303
    assert db.get_post_by_slug("spring-menu")["status"] == "draft"


def _published_post(client_as, slug="spring-menu"):
    _new_post(client_as("editor"), slug=slug)
    manager = client_as("admin")
    _action(manager, slug, "publish")
    return manager


def test_editor_cannot_open_or_modify_a_published_post(client_as):
    _published_post(client_as)
    editor = client_as("editor")
    assert editor.get("/admin/posts/spring-menu").status_code == 403
    csrf = _csrf(editor, "/admin/posts/new")  # a valid token, so only the role check can refuse
    response = editor.post(
        "/admin/posts/spring-menu",
        data={"title": "Hijacked", "body_md": "x", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 403
    post = db.get_post_by_slug("spring-menu")
    assert post["title"] == "Spring menu"
    assert post["status"] == "published"


def test_manager_edit_keeps_a_published_post_published(client_as):
    manager = _published_post(client_as)
    response = _edit(manager, "spring-menu", body_md="Manager edit.")
    assert response.status_code == 200
    post = db.get_post_by_slug("spring-menu")
    assert post["body_md"] == "Manager edit."
    assert post["status"] == "published"


def test_manager_can_delete_any_post(client_as):
    manager = _published_post(client_as)
    response = _action(manager, "spring-menu", "delete")
    assert response.status_code == 303
    assert db.get_post_by_slug("spring-menu") is None


def test_editor_cannot_delete_a_published_post(client_as):
    _published_post(client_as)
    editor = client_as("editor")
    csrf = _csrf(editor, "/admin/posts/new")
    response = _action(editor, "spring-menu", "delete", csrf=csrf)
    assert response.status_code == 403
    assert db.get_post_by_slug("spring-menu") is not None


def test_editor_can_delete_their_own_draft(client_as):
    editor = client_as("editor")
    _new_post(editor)
    assert _action(editor, "spring-menu", "delete").status_code == 303
    assert db.get_post_by_slug("spring-menu") is None


def test_anonymous_visitor_is_sent_to_login_from_every_posts_route(client):
    for method, path in [
        ("get", "/admin/posts"), ("get", "/admin/posts/new"),
        ("post", "/admin/posts/new"), ("get", "/admin/posts/x"),
        ("post", "/admin/posts/x"), ("post", "/admin/posts/x/publish"),
        ("post", "/admin/posts/x/unpublish"), ("post", "/admin/posts/x/delete"),
    ]:
        kwargs = {"data": {"slug": "x", "title": "x", "body_md": "x"}} if method == "post" else {}
        response = getattr(client, method)(path, follow_redirects=False, **kwargs)
        assert response.status_code == 303, (method, path)
        assert response.headers["location"] == "/login"


def test_posts_list_shows_posts_to_both_roles(client_as):
    _new_post(client_as("editor"), title="Spring menu")
    for role in ("editor", "admin"):
        response = client_as(role).get("/admin/posts")
        assert response.status_code == 200
        assert "Spring menu" in response.text


def _new_page(client, slug):
    csrf = _csrf(client, "/admin/pages/new")
    return client.post(
        "/admin/pages/new",
        data={"slug": slug, "title": "T", "body_md": "b", "status": "draft", "csrf_token": csrf},
        follow_redirects=False,
    )


def test_manager_cannot_create_a_page_in_the_news_namespace(client_as):
    manager = client_as("admin")
    for slug in ("news", "news-archive"):
        assert _new_page(manager, slug).status_code == 400
        assert db.get_page_by_slug(slug) is None
    assert _new_page(manager, "newsroom").status_code == 303  # not a "news-" prefix


def test_a_post_slug_must_be_well_formed_and_unique(client_as):
    editor = client_as("editor")
    assert _new_post(editor, slug="Bad Slug").status_code == 400
    assert _new_post(editor, slug="ok-slug").status_code == 303
    assert _new_post(editor, slug="ok-slug").status_code == 400


def test_existing_pages_in_the_news_namespace_are_reported_not_deleted():
    conn = db.get_connection()
    conn.execute("INSERT INTO pages (slug, title, status) VALUES ('news', 'Old', 'published')")
    conn.execute("INSERT INTO pages (slug, title) VALUES ('news-old', 'Old 2')")
    conn.commit()
    conn.close()
    conflicts = [p["slug"] for p in db.pages_conflicting_with_news()]
    assert conflicts == ["news", "news-old"]
    assert db.get_page_by_slug("news") is not None
    assert db.get_page_by_slug("news-old") is not None


# ---- Seam 2: export -------------------------------------------------------

def _post(slug, *, title=None, body="Body.", status="published", created_at=None):
    """created_at doubles as the publish date, which is what the export shows."""
    assert db.create_post(
        slug, title=title or slug.title(), body_md=body, author_id=None, created_at=created_at
    )
    if status == "published":
        db.set_post_status(slug, "published", published_at=created_at)


def test_only_published_posts_are_exported(tmp_path):
    _post("open-late", body="We open late.")
    _post("secret-draft", status="draft", body="Not yet.")
    out = render_site(tmp_path / "site")
    assert "We open late." in (out / "news-open-late.html").read_text()
    assert not (out / "news-secret-draft.html").exists()
    index = (out / "news.html").read_text()
    assert "Open-Late" in index and "Secret-Draft" not in index
    assert "Not yet." not in "".join(p.read_text() for p in out.glob("*.html"))


def test_news_index_is_newest_first_and_linked_from_home(tmp_path):
    _post("older", created_at="2026-05-01 10:00:00")
    _post("newest", created_at="2026-08-24 10:00:00")
    _post("middle", created_at="2026-07-01 10:00:00")
    out = render_site(tmp_path / "site")
    index = (out / "news.html").read_text()
    assert index.index("Newest") < index.index("Middle") < index.index("Older")
    assert 'href="news-newest.html"' in index
    home = (out / "index.html").read_text()
    assert 'href="news.html"' in home


def test_news_index_exists_and_is_linked_with_no_published_posts(tmp_path):
    out = render_site(tmp_path / "site")
    assert (out / "news.html").exists()
    assert 'href="news.html"' in (out / "index.html").read_text()


def test_unpublishing_and_exporting_again_removes_the_old_file(tmp_path, client_as):
    _post("spring-menu", body="Spring.")
    site = tmp_path / "site"
    render_site(site)
    assert (site / "news-spring-menu.html").exists()
    assert _action(client_as("admin"), "spring-menu", "unpublish").status_code == 303
    render_site(site)  # same directory as before
    assert not (site / "news-spring-menu.html").exists()
    assert "Spring-Menu" not in (site / "news.html").read_text()


def test_exported_news_html_uses_only_relative_links(tmp_path):
    _post("one")
    out = render_site(tmp_path / "site")
    for name in ("news.html", "news-one.html", "index.html"):
        html = (out / name).read_text()
        assert not re.search(r'(?:href|src)="/', html), name


def test_a_script_payload_in_a_post_body_does_not_reach_the_export(tmp_path):
    _post("xss", body='<script>alert(1)</script><img src=x onerror="alert(2)">hi')
    html = (render_site(tmp_path / "site") / "news-xss.html").read_text()
    assert "<script" not in html.lower()
    assert "<img" not in html.lower()


def test_export_refuses_a_published_page_that_collides_with_news(tmp_path):
    conn = db.get_connection()
    conn.execute("INSERT INTO pages (slug, title, status) VALUES ('news', 'Old', 'published')")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="news"):
        render_site(tmp_path / "site")
    assert db.get_page_by_slug("news") is not None  # reported, never deleted


# ---- Seed content ---------------------------------------------------------

def _run_seed(monkeypatch):
    import importlib.util
    from pathlib import Path

    monkeypatch.setenv("CMS_ADMIN_PASSWORD", "seed-admin-pw")
    monkeypatch.setenv("CMS_EDITOR_PASSWORD", "seed-editor-pw")
    path = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo.py"
    spec = importlib.util.spec_from_file_location("seed_demo_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main() == 0


def test_seed_publishes_a_dated_michelin_item_and_labels_demo_news(tmp_path, monkeypatch):
    _run_seed(monkeypatch)
    out = render_site(tmp_path / "site")
    index = (out / "news.html").read_text()
    assert "Michelin" in index and "2026-08-24" in index
    michelin = next(out.glob("news-*michelin*.html")).read_text()
    assert "Lomas de Chapultepec" in michelin
    assert "[DEMO CONTENT]" not in michelin  # the real item is not labelled demo
    demo_pages = [p.read_text() for p in out.glob("news-*.html") if "michelin" not in p.name]
    assert demo_pages and all("[DEMO CONTENT]" in html for html in demo_pages)


def test_seed_includes_a_draft_that_is_not_exported_and_is_safe_to_rerun(tmp_path, monkeypatch):
    _run_seed(monkeypatch)
    _run_seed(monkeypatch)  # second run must not duplicate or fail
    drafts = [p for p in db.list_posts() if p["status"] == "draft"]
    assert drafts
    out = render_site(tmp_path / "site")
    for draft in drafts:
        assert not (out / f"news-{draft['slug']}.html").exists()


# ---- Review findings ------------------------------------------------------

def test_a_failed_export_leaves_the_previous_site_untouched(tmp_path):
    site = tmp_path / "site"
    render_site(site)
    good_index = (site / "index.html").read_text()
    conn = db.get_connection()
    conn.execute("INSERT INTO pages (slug, title, status) VALUES ('news-old', 'Old', 'published')")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError):
        render_site(site)
    assert (site / "index.html").read_text() == good_index


def test_manager_cannot_publish_a_page_in_the_news_namespace(client_as):
    conn = db.get_connection()
    conn.execute("INSERT INTO pages (slug, title) VALUES ('news-old', 'Old')")
    conn.commit()
    conn.close()
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/news-old")
    response = manager.post(
        "/admin/pages/news-old",
        data={"title": "Old", "body_md": "b", "status": "published", "csrf_token": csrf},
    )
    assert response.status_code == 400
    assert db.get_page_by_slug("news-old")["status"] == "draft"


def test_pages_list_warns_about_pages_in_the_news_namespace(client_as):
    conn = db.get_connection()
    conn.execute("INSERT INTO pages (slug, title) VALUES ('news-old', 'Old')")
    conn.commit()
    conn.close()
    response = client_as("admin").get("/admin/pages")
    assert "news-old" in response.text and "reserved" in response.text


def test_a_post_cannot_take_the_slug_of_a_static_admin_route(client_as):
    editor = client_as("editor")
    assert _new_post(editor, slug="new").status_code == 400
    assert db.get_post_by_slug("new") is None


def test_a_blank_title_is_rejected_on_create_and_edit(client_as):
    editor = client_as("editor")
    assert _new_post(editor, slug="blank", title="   ").status_code == 400
    assert db.get_post_by_slug("blank") is None
    _new_post(editor)
    assert _edit(editor, "spring-menu", title="   ").status_code == 400
    assert db.get_post_by_slug("spring-menu")["title"] == "Spring menu"


def test_the_public_date_and_order_follow_the_publish_date_not_the_draft_date(tmp_path, client_as):
    _post("drafted-early", status="draft", created_at="2026-03-01 09:00:00")
    _post("published-mid", created_at="2026-07-01 09:00:00")
    _action(client_as("admin"), "drafted-early", "publish")  # published now, after the other
    out = render_site(tmp_path / "site")
    index = (out / "news.html").read_text()
    assert index.index("Drafted-Early") < index.index("Published-Mid")
    assert "2026-03-01" not in index
    _action(client_as("admin"), "drafted-early", "unpublish")
    assert db.get_post_by_slug("drafted-early")["published_at"] is None
