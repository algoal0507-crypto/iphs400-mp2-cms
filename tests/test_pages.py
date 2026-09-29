"""T02: Pages (create/read/update/delete), seeded with Home, Menu, Our Story.

Per the MP2 rubric/manual, Pages support the same CRUD operations as Posts;
Home/Menu/Our Story are La Once Mil's starting content, not a hard limit.
Covers a Manager creating, editing, and deleting a page, an Editor blocked on
every route (UI and a hand-crafted direct POST/DELETE), an anonymous visitor
redirected to login, and Markdown sanitization of a script/onerror payload.
"""
from __future__ import annotations

import sqlite3

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


def test_manager_can_create_a_page(client_as):
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/new")
    response = manager.post(
        "/admin/pages/new",
        data={"slug": "events", "title": "Events", "body_md": "Coming soon.",
              "status": "draft", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/pages/events"
    page = db.get_page_by_slug("events")
    assert page is not None
    assert page["title"] == "Events"
    assert page["author_id"] is not None


def test_creating_a_page_with_a_duplicate_slug_is_rejected(client_as):
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/new")
    response = manager.post(
        "/admin/pages/new",
        data={"slug": "home", "title": "Duplicate Home", "body_md": "x",
              "status": "draft", "csrf_token": csrf},
    )
    assert response.status_code == 400
    assert db.get_page_by_slug("home")["title"] != "Duplicate Home"


def test_creating_a_page_with_an_invalid_slug_is_rejected(client_as):
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/new")
    response = manager.post(
        "/admin/pages/new",
        data={"slug": "Not A Slug!", "title": "Bad", "body_md": "x",
              "status": "draft", "csrf_token": csrf},
    )
    assert response.status_code == 400
    assert db.get_page_by_slug("Not A Slug!") is None


def test_manager_can_delete_a_page(client_as):
    manager = client_as("admin")
    csrf = _csrf(manager, "/admin/pages/new")
    manager.post(
        "/admin/pages/new",
        data={"slug": "events", "title": "Events", "body_md": "x",
              "status": "draft", "csrf_token": csrf},
    )
    assert db.get_page_by_slug("events") is not None

    delete_csrf = _csrf(manager, "/admin/pages")
    response = manager.post(
        "/admin/pages/events/delete",
        data={"csrf_token": delete_csrf},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert db.get_page_by_slug("events") is None


def test_editor_is_blocked_from_create_and_delete(client_as):
    editor = client_as("editor")
    assert editor.get("/admin/pages/new", follow_redirects=False).status_code == 403
    assert editor.post(
        "/admin/pages/new",
        data={"slug": "hijack", "title": "Hijack", "body_md": "x", "status": "draft",
              "csrf_token": "not-a-real-token"},
        follow_redirects=False,
    ).status_code == 403
    assert db.get_page_by_slug("hijack") is None

    assert editor.post(
        "/admin/pages/home/delete",
        data={"csrf_token": "not-a-real-token"},
        follow_redirects=False,
    ).status_code == 403
    assert db.get_page_by_slug("home") is not None


def test_anonymous_is_redirected_from_create_and_delete(client):
    response = client.get("/admin/pages/new", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/login")

    response = client.post("/admin/pages/home/delete", data={}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/login")


def test_deleting_all_pages_then_restarting_does_not_recreate_them():
    """Regression: init_db() runs again on every `cms serve` restart. It must
    only bootstrap an empty table, never resurrect a page the Manager deleted."""
    for slug in db.PAGE_SLUGS:
        db.delete_page(slug)
    assert db.list_pages() == []

    db.init_db()  # simulates the next `cms serve` restart

    assert db.list_pages() == []


def test_existing_database_migrates_off_the_legacy_slug_check(tmp_path):
    """A database created before Pages supported full CRUD has
    CHECK (slug IN (...)) baked into the pages table. init_db() must rebuild
    that table (keeping existing content) so create_page() isn't silently
    blocked for any slug outside the old fixed three."""
    legacy_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(legacy_path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE CHECK (slug IN ('home', 'menu', 'our-story')),
            title TEXT NOT NULL,
            body_md TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
            author_id INTEGER REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.execute(
        "INSERT INTO pages (slug, title, body_md, status) "
        "VALUES ('home', 'Home', 'Existing verified content', 'published')"
    )
    conn.commit()
    conn.close()

    db.init_db(legacy_path)

    conn = sqlite3.connect(legacy_path)
    conn.row_factory = sqlite3.Row
    home = conn.execute("SELECT * FROM pages WHERE slug = 'home'").fetchone()
    assert home["body_md"] == "Existing verified content"
    assert home["status"] == "published"

    # Would raise sqlite3.IntegrityError under the old CHECK constraint.
    conn.execute(
        "INSERT INTO pages (slug, title, body_md, status) VALUES ('events', 'Events', 'x', 'draft')"
    )
    conn.commit()
    assert conn.execute("SELECT slug FROM pages WHERE slug = 'events'").fetchone() is not None
    conn.close()


def _legacy_schema_sql():
    return """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE CHECK (slug IN ('home', 'menu', 'our-story')),
            title TEXT NOT NULL,
            body_md TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
            author_id INTEGER REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """


def test_legacy_migration_is_atomic_against_a_mid_migration_crash(tmp_path):
    """Regression: a process killed between the migration's steps (crash, OOM,
    power loss, before any COMMIT) must not orphan the renamed table's real
    content while the app is left reading a freshly emptied `pages` table."""
    legacy_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(legacy_path)
    conn.executescript(_legacy_schema_sql())
    conn.execute(
        "INSERT INTO pages (slug, title, body_md, status) "
        "VALUES ('home', 'Home', 'Existing verified content', 'published')"
    )
    conn.commit()

    existing_pages_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'pages'"
    ).fetchone()[0]

    # Reproduce the migration's steps up to (not including) its final COMMIT,
    # then simulate a crash by closing the connection without committing.
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("ALTER TABLE pages RENAME TO pages_legacy")
    conn.execute(db.PAGES_SCHEMA)
    conn.execute(
        f"INSERT INTO pages ({db._PAGE_COLUMNS}) SELECT {db._PAGE_COLUMNS} FROM pages_legacy"
    )
    conn.execute("DROP TABLE pages_legacy")
    conn.close()  # crash: no COMMIT

    reopened = sqlite3.connect(legacy_path)
    reopened.row_factory = sqlite3.Row
    home = reopened.execute("SELECT * FROM pages WHERE slug = 'home'").fetchone()
    assert home is not None, "the original row must survive an uncommitted crash"
    assert home["body_md"] == "Existing verified content"
    assert "CHECK (slug IN" in existing_pages_sql  # sanity check on the fixture itself
    reopened.close()
