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

USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    active INTEGER NOT NULL DEFAULT 1
);
"""

PAGES_SCHEMA = """
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

SCHEMA = USERS_SCHEMA + PAGES_SCHEMA

SLUG_PATTERN = "^[a-z0-9]+(-[a-z0-9]+)*$"

# "index" is reserved: app/publish.py exports the "home" page to index.html,
# so a page slugged "index" would silently overwrite the real homepage on
# export.
_RESERVED_SLUGS = frozenset({"index"})

_PAGE_COLUMNS = "id, slug, title, body_md, status, author_id, created_at, updated_at"


def _migrate_legacy_page_slug_check(conn: sqlite3.Connection, existing_pages_sql: str | None) -> None:
    """A database created before Pages supported full CRUD has
    `CHECK (slug IN ('home', 'menu', 'our-story'))` baked into the `pages`
    table — `CREATE TABLE IF NOT EXISTS` never touches an existing table, so
    that CHECK would otherwise survive forever and silently block creating
    any other page. Rebuild the table from PAGES_SCHEMA, keeping every row.

    This runs as one explicit transaction (isolation_level=None plus our own
    BEGIN/COMMIT) rather than relying on the connection's default autocommit
    handling or `executescript()`: `executescript()` implicitly commits
    pending work before it runs, and under the default isolation level a DDL
    statement like ALTER/CREATE/DROP TABLE can commit independently of a
    later `conn.commit()`. Either would let a crash between steps (process
    killed, power loss) orphan the renamed table with real content in it
    while the app reads a freshly emptied `pages` table — confirmed with a
    crash simulation (kill before the final commit, reopen, check for data
    loss) before writing it this way.
    """
    if existing_pages_sql is None or "CHECK (slug IN" not in existing_pages_sql:
        return

    previous_isolation_level = conn.isolation_level
    conn.isolation_level = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("ALTER TABLE pages RENAME TO pages_legacy")
        conn.execute(PAGES_SCHEMA)
        conn.execute(
            f"INSERT INTO pages ({_PAGE_COLUMNS}) "
            f"SELECT {_PAGE_COLUMNS} FROM pages_legacy"
        )
        conn.execute("DROP TABLE pages_legacy")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.isolation_level = previous_isolation_level


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path | None = None) -> None:
    """Create the schema and, only the first time the `pages` table is
    created, seed the starting Pages. Pages are freely creatable/deletable
    (see PAGE_SLUGS' docstring) and `init_db` runs again on every `cms serve`
    restart, so this keys off whether the table already existed — not
    whether it's currently empty — or deleting every page would make the
    next restart look identical to a brand-new database and recreate them.
    """
    conn = get_connection(path)
    try:
        existing_pages_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'pages'"
        ).fetchone()
        conn.executescript(SCHEMA)
        _migrate_legacy_page_slug_check(conn, existing_pages_row[0] if existing_pages_row else None)
        if existing_pages_row is None:
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
    return slug not in _RESERVED_SLUGS and re.fullmatch(SLUG_PATTERN, slug) is not None


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
