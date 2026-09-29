"""SQLite connection and the users table.

One file, gitignored, rebuilt by `scripts/seed_demo.py`. See ADR-002 for why
there is no ORM here.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app import auth, settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    active INTEGER NOT NULL DEFAULT 1
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
