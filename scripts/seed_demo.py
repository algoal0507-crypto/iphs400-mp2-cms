#!/usr/bin/env python3
"""Create demo data so a grader (and you) can use the CMS immediately.

    uv run python scripts/seed_demo.py

T00 has nothing to seed. As you build content types, extend this so it creates:
  - one admin and one editor (passwords read from .env, never hard-coded)
  - a few posts and pages, at least one draft and one published

The rubric expects this to run clean on a fresh clone with .env.example values
(item E4), because the database itself is never committed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db  # noqa: E402

DEMO_MANAGER_EMAIL = "manager@laoncemil.test"
DEMO_EDITOR_EMAIL = "editor@laoncemil.test"


def main() -> int:
    admin_pw = os.environ.get("CMS_ADMIN_PASSWORD")
    editor_pw = os.environ.get("CMS_EDITOR_PASSWORD")
    if not admin_pw or not editor_pw:
        print("Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env "
              "(copy .env.example).")
        return 1

    db.init_db()
    if db.get_user_by_email(DEMO_MANAGER_EMAIL) is None:
        db.create_user(DEMO_MANAGER_EMAIL, admin_pw, "admin")
        print(f"Created Demo Manager ({DEMO_MANAGER_EMAIL}).")
    else:
        print(f"Demo Manager ({DEMO_MANAGER_EMAIL}) already exists.")

    if db.get_user_by_email(DEMO_EDITOR_EMAIL) is None:
        db.create_user(DEMO_EDITOR_EMAIL, editor_pw, "editor")
        print(f"Created Demo Editor ({DEMO_EDITOR_EMAIL}).")
    else:
        print(f"Demo Editor ({DEMO_EDITOR_EMAIL}) already exists.")

    # TODO (later tickets): seed News drafts/published items and Pages.
    return 0


if __name__ == "__main__":
    sys.exit(main())
