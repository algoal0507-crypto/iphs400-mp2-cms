"""SQLite connection and the users table.

One file, gitignored, rebuilt by `scripts/seed_demo.py`. See ADR-002 for why
there is no ORM here.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app import auth, settings

# The Manager edits these three fixed permanent pages; nothing ever creates or
# deletes a row here (see CONTEXT.md's "Permanent pages" entry). This tuple is
# the single source of truth — the schema's CHECK constraint is generated
# from it below, so the two can't drift apart.
PAGE_SLUGS = ("home", "menu", "our-story")
PAGE_TITLES = {"home": "Home", "menu": "Menu", "our-story": "Our Story"}

_PAGE_SLUGS_SQL = ", ".join(f"'{slug}'" for slug in PAGE_SLUGS)

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE CHECK (slug IN ({_PAGE_SLUGS_SQL})),
    title TEXT NOT NULL,
    body_md TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    author_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path | None = None) -> None:
    conn = get_connection(path)
    try:
        conn.executescript(SCHEMA)
        for slug in PAGE_SLUGS:
            conn.execute(
                "INSERT OR IGNORE INTO pages (slug, title) VALUES (?, ?)",
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
