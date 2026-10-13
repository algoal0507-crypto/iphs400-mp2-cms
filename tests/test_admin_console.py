"""T05: admin dashboard, filterable content list, live Markdown preview.

All assertions go through HTTP: what a signed-in user can see.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

import pytest

from app import db


def _csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def _seed():
    """News: 2 drafts + 1 published. Pages: home published, the other two draft."""
    uid = db.get_user_by_email("admin@example.test")["id"]
    db.create_post("draft-a", title="Draft A", body_md="a", author_id=uid)
    db.create_post("draft-b", title="Draft B", body_md="b", author_id=uid)
    db.create_post("live-c", title="Live C", body_md="c", author_id=uid)
    db.set_post_status("live-c", "published")
    # init_db already creates the three starting Pages; set their statuses.
    for slug, status in (("home", "published"), ("menu", "draft"), ("our-story", "draft")):
        db.update_page(slug, title=slug.title(), body_md="x", status=status, author_id=uid)


def _count(html: str, label: str) -> int:
    match = re.search(rf'data-count="{label}">(\d+)<', html)
    assert match, f"no count for {label!r} on the page"
    return int(match.group(1))


def _preview_url(page_path: str, html: str) -> str:
    """Where the page's preview script posts, resolved the way a browser would."""
    match = re.search(r'data-preview-url="([^"]+)"', html)
    assert match, "form has no data-preview-url"
    assert not match.group(1).startswith("/"), "admin links must be relative"
    return urljoin(page_path, match.group(1))


def _rows(html: str) -> list[str]:
    return re.findall(r'data-row="([^"]+)"', html)


def test_manager_dashboard_counts_news_and_page_status(client_as):
    admin = client_as("admin")
    _seed()
    html = admin.get("/admin/dashboard").text
    assert _count(html, "news-draft") == 2
    assert _count(html, "news-published") == 1
    # The status sits in a badge inside the row, so read to the end of the row.
    assert re.search(r'data-page="home"[^>]*>(?:(?!</li>).)*published', html, re.S)
    assert re.search(r'data-page="menu"[^>]*>(?:(?!</li>).)*draft', html, re.S)
    assert 'data-page="our-story"' in html


def test_editor_dashboard_has_news_counts_but_no_pages(client_as):
    _seed()
    html = client_as("editor").get("/admin/dashboard").text
    assert _count(html, "news-draft") == 2
    assert "data-page=" not in html
    assert "/admin/pages" not in html


def test_content_list_shows_everything_to_the_manager(client_as):
    admin = client_as("admin")
    _seed()
    rows = _rows(admin.get("/admin/content").text)
    assert sorted(rows) == ["page:home", "page:menu", "page:our-story",
                            "post:draft-a", "post:draft-b", "post:live-c"]


@pytest.mark.parametrize("query,expected", [
    ("type=news", {"post:draft-a", "post:draft-b", "post:live-c"}),
    ("type=pages", {"page:home", "page:menu", "page:our-story"}),
    ("status=published", {"post:live-c", "page:home"}),
    ("status=draft", {"post:draft-a", "post:draft-b", "page:menu", "page:our-story"}),
    ("type=news&status=published", {"post:live-c"}),
    ("type=pages&status=draft", {"page:menu", "page:our-story"}),
])
def test_content_list_filters_by_type_and_status(client_as, query, expected):
    admin = client_as("admin")
    _seed()
    assert set(_rows(admin.get(f"/admin/content?{query}").text)) == expected


def test_unknown_filter_values_are_ignored(client_as):
    admin = client_as("admin")
    _seed()
    response = admin.get("/admin/content?type=bogus&status=bogus")
    assert response.status_code == 200
    assert len(_rows(response.text)) == 6


def test_editor_content_list_is_news_only(client_as):
    _seed()
    editor = client_as("editor")
    assert sorted(_rows(editor.get("/admin/content").text)) == [
        "post:draft-a", "post:draft-b", "post:live-c"]
    # Asking for pages directly does not widen the scope.
    assert not any(r.startswith("page:") for r in _rows(editor.get("/admin/content?type=pages").text))


def test_content_list_and_dashboard_require_login(client):
    for path in ("/admin/content", "/admin/dashboard"):
        assert client.get(path, follow_redirects=False).status_code in (302, 303)


@pytest.mark.parametrize("path,role", [
    ("/admin/pages/new", "admin"),
    ("/admin/posts/new", "editor"),
    ("/admin/posts/new", "admin"),
])
def test_new_content_forms_have_a_live_preview(client_as, path, role):
    html = client_as(role).get(path).text
    assert 'id="preview"' in html
    assert _preview_url(path, html) == "/admin/preview"


def test_edit_forms_have_a_live_preview(client_as):
    admin = client_as("admin")
    _seed()
    for path in ("/admin/pages/home", "/admin/posts/draft-a"):
        html = admin.get(path).text
        assert 'id="preview"' in html
        assert _preview_url(path, html) == "/admin/preview"


def test_preview_endpoint_renders_and_sanitizes(client_as):
    editor = client_as("editor")
    csrf = _csrf(editor, "/admin/posts/new")
    response = editor.post("/admin/preview", data={
        "body_md": "# Hi\n\n<script>alert(1)</script> <img src=x onerror=alert(1)>",
        "csrf_token": csrf,
    })
    assert response.status_code == 200
    assert "<h1>Hi</h1>" in response.text
    assert "<script" not in response.text.lower()
    assert "<img" not in response.text.lower()


def test_preview_endpoint_requires_login_and_csrf(client, client_as):
    assert client.post("/admin/preview", data={"body_md": "x"},
                       follow_redirects=False).status_code in (302, 303)
    editor = client_as("editor")
    assert editor.post("/admin/preview",
                       data={"body_md": "x", "csrf_token": "wrong"}).status_code == 403


def test_preview_script_is_served_and_linked_relatively(client_as):
    admin = client_as("admin")
    html = admin.get("/admin/pages/home").text
    src = re.search(r'<script src="([^"]+)"', html).group(1)
    assert not src.startswith("/")
    response = admin.get(urljoin("/admin/pages/home", src))
    assert response.status_code == 200 and "fetch(" in response.text


def test_preview_rejects_oversized_input(client_as):
    editor = client_as("editor")
    csrf = _csrf(editor, "/admin/posts/new")
    response = editor.post("/admin/preview", data={"body_md": "x" * 200_001, "csrf_token": csrf})
    assert response.status_code == 413
