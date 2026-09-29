"""SQLite connection and the users table.

One file, gitignored, rebuilt by `scripts/seed_demo.py`. See ADR-002 for why
there is no ORM here.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from app import auth, settings

# La Once Mil's initial Pages (see notes/restaurant-research.md); this is
# seed content, not a limit. Per the MP2 rubric/manual ("Pages: same fields
# and operations as posts, plus public navigation"), Pages support full
# create/read/update/delete like Posts — the Manager can add or remove pages
# beyond this starting set.
PAGE_SLUGS = ("home", "menu", "our-story")
PAGE_TITLES = {"home": "Home", "menu": "Menu", "our-story": "Our Story"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    body_md TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    author_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SLUG_PATTERN = "^[a-z0-9]+(-[a-z0-9]+)*$"


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path | None = None) -> None:
    """Create the schema and, only on a brand-new database, seed the
    starting Pages. Pages are freely creatable/deletable (see PAGE_SLUGS'
    docstring), so this must not resurrect a page the Manager deleted —
    it only bootstraps an empty table, never re-inserts into a populated one.
    """
    conn = get_connection(path)
    try:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0] == 0:
            for slug in PAGE_SLUGS:
                conn.execute(
                    "INSERT INTO pages (slug, title) VALUES (?, ?)",
                    (slug, PAGE_TITLES[slug]),
                )
        conn.commit()
    finally:
        conn.close()


def create_user(email: str, password: str, role: str, *, active: bool = True) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, role, active) VALUES (?, ?, ?, ?)",
            (email, auth.hash_password(password), role, int(active)),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_email(email: str) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def set_active(email: str, *, active: bool) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET active = ? WHERE email = ?", (int(active), email)
        )
        conn.commit()
    finally:
        conn.close()


def get_page_by_slug(slug: str) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM pages WHERE slug = ?", (slug,)
        ).fetchone()
    finally:
        conn.close()


def list_pages() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM pages ORDER BY slug").fetchall()
    finally:
        conn.close()


def update_page(slug: str, *, title: str, body_md: str, status: str, author_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE pages
               SET title = ?, body_md = ?, status = ?, author_id = ?,
                   updated_at = datetime('now')
               WHERE slug = ?""",
            (title, body_md, status, author_id, slug),
        )
        conn.commit()
    finally:
        conn.close()


def slug_is_valid(slug: str) -> bool:
    return re.fullmatch(SLUG_PATTERN, slug) is not None


def create_page(slug: str, *, title: str, body_md: str, status: str, author_id: int) -> bool:
    """Insert a new page. Returns False if the slug is already taken."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO pages (slug, title, body_md, status, author_id) VALUES (?, ?, ?, ?, ?)",
            (slug, title, body_md, status, author_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_page(slug: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM pages WHERE slug = ?", (slug,))
        conn.commit()
    finally:
        conn.close()
