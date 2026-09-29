"""T02: permanent pages (Home, Menu, Our Story).

Covers a Manager saving a page, an Editor blocked on both the edit-form UI
route and a hand-crafted direct POST, an anonymous visitor redirected to
login, and Markdown sanitization of a script/onerror payload.
"""
from __future__ import annotations

from app import db


def _csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def test_manager_can_edit_a_permanent_page(client_as):
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/home")
    response = manager.post(
        "/admin/pages/home",
        data={
            "title": "Home",
            "body_md": "Visit us at Monte Everest 780, Lomas de Chapultepec.",
            "status": "published",
            "csrf_token": csrf,
        },
    )
    assert response.status_code == 200
    page = db.get_page_by_slug("home")
    assert page["status"] == "published"
    assert "Monte Everest 780" in page["body_md"]
    assert page["author_id"] is not None


def test_editor_is_blocked_from_edit_form(client_as):
    editor = client_as("editor")
    response = editor.get("/admin/pages/home", follow_redirects=False)
    assert response.status_code == 403


def test_editor_is_blocked_from_pages_list(client_as):
    editor = client_as("editor")
    response = editor.get("/admin/pages", follow_redirects=False)
    assert response.status_code == 403


def test_editor_is_blocked_from_a_direct_post(client_as):
    """A forged POST with no prior UI visit must still be rejected by role,
    not merely by a missing CSRF token."""
    editor = client_as("editor")
    response = editor.post(
        "/admin/pages/home",
        data={"title": "Hijacked", "body_md": "x", "status": "published",
              "csrf_token": "not-even-a-real-token"},
        follow_redirects=False,
    )
    assert response.status_code == 403
    assert db.get_page_by_slug("home")["title"] != "Hijacked"


def test_anonymous_is_redirected_to_login(client):
    response = client.get("/admin/pages/home", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/login")

    response = client.post(
        "/admin/pages/home",
        data={"title": "x", "body_md": "x", "status": "draft"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].endswith("/login")


def test_saved_markdown_is_sanitized(client_as):
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/menu")
    payload = '<script>alert(1)</script><img src=x onerror="alert(2)">Tacos al pastor'
    response = manager.post(
        "/admin/pages/menu",
        data={"title": "Menu", "body_md": payload, "status": "draft", "csrf_token": csrf},
    )
    assert response.status_code == 200

    page = db.get_page_by_slug("menu")
    assert "<script" not in page["body_md"]
    assert "onerror" not in page["body_md"]
    assert "Tacos al pastor" in page["body_md"]

    assert "<script" not in response.text
    assert "onerror" not in response.text


def test_saving_plain_text_does_not_corrupt_it(client_as):
    """Regression: sanitizing raw Markdown must not HTML-entity-encode
    ordinary characters (e.g. "&" -> "&amp;"), which would corrupt the
    stored text on every save/reload round trip."""
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/menu")
    manager.post(
        "/admin/pages/menu",
        data={"title": "Menu", "body_md": "Tacos & salsa, \"al pastor\"",
              "status": "draft", "csrf_token": csrf},
    )
    page = db.get_page_by_slug("menu")
    assert page["body_md"] == 'Tacos & salsa, "al pastor"'
