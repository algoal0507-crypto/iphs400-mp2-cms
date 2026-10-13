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

# Sourced from notes/restaurant-research.md (Michelin Guide, retrieved
# 2026-09-29). No verified phone number exists, so none is shown; photos are
# clearly labeled placeholders rather than invented facts.
HOME_BODY = """\
## Visit La Once Mil

**Address:** Monte Everest 780, Lomas de Chapultepec, Miguel Hidalgo, CP 11000, \
Mexico City

**Hours:** Monday-Friday 12:00 PM-11:30 PM · Saturday-Sunday 11:00 AM-11:30 PM

[Get directions](https://maps.google.com/?q=Monte+Everest+780+Lomas+de+Chapultepec+Ciudad+de+Mexico)

Walk-ins only — no reservations, first come, first served.

One MICHELIN Star, awarded 2026, attributed to this address.

[PLACEHOLDER: storefront photo]
"""

MENU_BODY = """\
## Menu

Gourmet tacos elevating traditional street-taco formats. No prices are listed — \
see `notes/restaurant-research.md`: no verified peso pricing exists yet.

- **Carne asada** — grilled beef taco
- **Arrachera** — skirt steak taco
- **Picaña (trompo)** — top sirloin taco, cooked on the trompo
- **A5 Wagyu** — hand-pressed tortilla, spicy soy salsa (signature dish)
- **Lechón (carnitas)** — 12-hour cooked suckling pig
- **Rib eye** — grilled rib eye taco
- **Bass al pastor** — fish prepared al pastor style
- **Vegan options** — available, ask your server
- **Tostadas** — including tuna/ceviche
- **Quesadillas**
- **Noodle soup**
- **Caesar salad**

### Salsas

From mild ("salsa cruda") to very spicy ("martajada," made with árbol and morita \
chiles).

### Desserts

Sorbets, ice creams, and meringues.

[PLACEHOLDER: menu photo]
"""

OUR_STORY_BODY = """\
## Our Story

La Once Mil is a taquería at Monte Everest 780 in Lomas de Chapultepec, Mexico \
City, opened in 2024 by chef César de la Parra together with Enrique Glennie and \
Jimena Gutiérrez. The name comes from 11000, the postal code of the neighborhood \
where the restaurant began.

In 2026, La Once Mil became the first — and so far only — taquería to receive a \
Michelin star, awarded to this Lomas de Chapultepec address specifically.

The idea behind the menu is simple: take the traditional street-taco format most \
people know as fast, inexpensive food, and elevate it with high-quality \
ingredients — from A5 wagyu to 12-hour-cooked lechón — while keeping the \
counter-service, walk-in-only spirit of a real taquería.

[PLACEHOLDER: chef/kitchen photo]
"""

PAGE_CONTENT = {
    "home": HOME_BODY,
    "menu": MENU_BODY,
    "our-story": OUR_STORY_BODY,
}

# News. The Michelin item is the one real, dated item (CONTEXT.md, "Michelin
# item"): the Guide's own page attributes the star to the Lomas de
# Chapultepec address, and the article cited below is dated 24 Aug 2026, which
# is the post's date. Everything else is invented sample content and carries a
# visible [DEMO CONTENT] label.
# (slug, title, created_at, status, body_md)
NEWS_POSTS = [
    (
        "michelin-star",
        "La Once Mil holds one Michelin star",
        "2026-08-24 12:00:00",
        "published",
        "The MICHELIN Guide lists La Once Mil at Monte Everest 780, Lomas de "
        "Chapultepec, with **One MICHELIN Star**, awarded at the Guide's 2026 "
        "Mexico ceremony in Guadalajara.\n\n"
        "Source: MICHELIN Guide, article dated 24 Aug 2026.",
    ),
    (
        "seasonal-menu-update",
        "Seasonal menu update",
        "2026-09-01 12:00:00",
        "published",
        "**[DEMO CONTENT]** Invented sample announcement for the class project; "
        "it does not come from La Once Mil.\n\n"
        "New seasonal tacos are coming to the menu.",
    ),
    (
        "holiday-hours",
        "Holiday hours",
        "2026-09-15 12:00:00",
        "draft",
        "**[DEMO CONTENT]** Invented sample draft for the class project; it does "
        "not come from La Once Mil.\n\n"
        "Hours may change around the holidays.",
    ),
]


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

    manager = db.get_user_by_email(DEMO_MANAGER_EMAIL)
    for slug, body_md in PAGE_CONTENT.items():
        page = db.get_page_by_slug(slug)
        if page is not None and not page["body_md"]:
            db.update_page(
                slug, title=db.PAGE_TITLES[slug], body_md=body_md,
                status="published", author_id=manager["id"],
            )
            print(f"Seeded permanent page: {slug}")

    for slug, title, created_at, status, body_md in NEWS_POSTS:
        created = db.create_post(
            slug, title=title, body_md=body_md,
            author_id=manager["id"], created_at=created_at,
        )
        if created:
            if status == "published":
                db.set_post_status(slug, "published", published_at=created_at)
            print(f"Seeded News post: {slug} ({status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
