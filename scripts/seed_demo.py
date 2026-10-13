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
import re
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
"""

# The page title is the <h1> on the public page, so a body never starts with
# a heading that repeats it. No prices: no verified peso pricing exists
# (see notes/restaurant-research.md; that note stays in the project notes, not
# on the public page).
MENU_BODY = """\
Gourmet tacos that elevate traditional street-taco formats.

[PHOTO: menu]

## Tacos

- **Carne asada**
  Beef
- **Arrachera**
  Skirt steak taco
- **Picaña (trompo)**
  Top sirloin taco, cooked on the trompo
- **A5 Wagyu**
  Hand-pressed tortilla, spicy soy salsa. Signature dish
- **Lechón (carnitas)**
  12-hour cooked suckling pig
- **Rib eye**
  Beef
- **Bass al pastor**
- **Vegan options**
  Available

## Beyond tacos

- **Tostadas**
  Including tuna and ceviche
- **Quesadillas**
- **Noodle soup**
- **Caesar salad**

## Salsas

- **Salsa cruda**
  Mild
- **Martajada**
  Very spicy, made with árbol and morita chiles

## Desserts

- **Sorbets**
- **Ice creams**
- **Meringues**
"""

OUR_STORY_BODY = """\
La Once Mil is a taquería at Monte Everest 780 in Lomas de Chapultepec, Mexico \
City, opened in 2024 by chef César de la Parra together with Enrique Glennie and \
Jimena Gutiérrez. The name comes from 11000, the postal code of the neighborhood \
where the restaurant began.

La Once Mil received one MICHELIN star in 2026.

The idea behind the menu is simple: take the traditional street-taco format most \
people know as fast, inexpensive food, and elevate it with high-quality \
ingredients — from A5 wagyu to 12-hour-cooked lechón — while keeping the \
spirit of a taquería.

[PHOTO: our-story]
"""

# The text these two pages shipped with before the T09 copy fix. Kept so an
# existing database can be brought up to date: a page whose body is still
# exactly this is replaced; a page someone has edited only loses the two known
# problems below, and keeps everything else they changed.
LEGACY_MENU_BODY = """\
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

LEGACY_OUR_STORY_BODY = """\
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
# The two real News posts. A post's date in the list and on its page is when it was
# published on THIS site (published_at, here 2026-10-13); the date of the event is in
# the text. Sources were read on 2026-10-13: the Madrid press release is the
# official announcement (in Spanish), and the Michelin article is dated 20 May 2026.
MICHELIN_SOURCE = ("https://guide.michelin.com/us/en/article/michelin-guide-ceremony/"
                   "every-michelin-starred-restaurant-in-mexico-for-2026-and-the-year-s-key-trends")
MADRID_SOURCE = ("https://www.mateoandco.es/2026/09/14/la-once-mil-la-taqueria-que-cambio-la-manera-"
                 "de-comer-tacos-en-cdmx-llega-a-madrid-de-la-mano-de-los-33/")
PUBLISHED_AT = "2026-10-13 12:00:00"

MICHELIN_BODY = (
    "Michelin announced La Once Mil as a **new one-star restaurant** in its Mexico "
    "selection on **May 20, 2026**. The Guide lists it under Mexico City.\n\n"
    "- **Event date:** May 20, 2026, when the MICHELIN Guide Mexico 2026 selection was revealed\n"
    f"- **Source:** [MICHELIN Guide, \"Every MICHELIN-Starred Restaurant in Mexico for 2026, "
    f"Plus the Year's Key Trends\"]({MICHELIN_SOURCE}), dated 20 May 2026\n"
)
MADRID_BODY = (
    "The official announcement of September 14, 2026 gave **September 22, 2026** as the "
    "opening date of La Once Mil in Madrid, at **Plaza de las Salesas 11**, in "
    "collaboration with **Los 33**, its local partner.\n\n"
    "- **Opening date:** September 22, 2026\n"
    "- **Address:** Plaza de las Salesas 11, Madrid\n"
    "- **With:** Los 33\n"
    "- **Hours announced:** Tuesday to Saturday, 1:00 pm to 1:00 am; Sunday, 1:00 pm to "
    "7:00 pm. Dine-in only, no takeaway.\n"
    "- **Announced:** September 14, 2026\n"
    f"- **Source:** [Official announcement (press release, in Spanish)]({MADRID_SOURCE})\n\n"
    "This is company news. The visiting information on Home is for the Mexico City "
    "restaurant only.\n"
)

# What the Michelin post said before 2026-10-13. refresh_news() recognises it so an
# existing database gets the new post in place (no duplicate) unless it was edited.
LEGACY_MICHELIN_TITLE = "La Once Mil holds one Michelin star"
LEGACY_MICHELIN_BODY = (
    "The MICHELIN Guide lists La Once Mil at Monte Everest 780, Lomas de "
    "Chapultepec, with **One MICHELIN Star**, awarded at the Guide's 2026 "
    "Mexico ceremony in Guadalajara.\n\n"
    "Source: MICHELIN Guide, article dated 24 Aug 2026."
)
LEGACY_MICHELIN_PUBLISHED_AT = "2026-08-24 12:00:00"

# (slug, title, created_at, status, body_md); the list order is the id order, so with the
# same publish time the later entry (Madrid) is listed first.
REAL_NEWS = [
    ("michelin-star", "La Once Mil earns its first Michelin star", PUBLISHED_AT, "published", MICHELIN_BODY),
    ("madrid-opening", "La Once Mil arrives in Madrid", PUBLISHED_AT, "published", MADRID_BODY),
]

# Invented sample posts, always labelled as demo content (CONTEXT.md).
DEMO_NEWS = [
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

NEWS_POSTS = REAL_NEWS + DEMO_NEWS


# Wording decided for Our Story after review: the "first and only" claim is not in our
# sources, and the closing clause now reads "while keeping the spirit of a taquería." Matching ignores how the text was wrapped or
# spaced, and a replacement only happens where the old text is still there, so a
# Manager's own rewording is never overwritten.
def _loose(text: str) -> "re.Pattern[str]":
    return re.compile(r"\s+".join(re.escape(word) for word in text.split()))


_WORDING_FIXES = {
    "our-story": [
        (_loose("In 2026, La Once Mil became the first — and so far only — taquería to receive a "
                "Michelin star, awarded to this Lomas de Chapultepec address specifically."),
         "La Once Mil received one MICHELIN star in 2026."),
        # Both earlier versions of the closing clause (the original and the interim one).
        (_loose("while keeping the counter-service, walk-in-only spirit of a real taquería."),
         "while keeping the spirit of a taquería."),
        (_loose("while keeping the taquería, walk-in-only spirit of a real taquería."),
         "while keeping the spirit of a taquería."),
    ],
}

# A sentence that points at a project file, e.g. "... see `notes/foo.md`: ...".
_INTERNAL_NOTE = re.compile(r" ?[^.\n]*`notes/[^`\n]*`[^.\n]*\.")


def _drop_line(body: str, line: str) -> str:
    """Remove every line that is exactly `line`, keeping the rest of the text as it was."""
    kept = [l for l in body.split("\n") if l.strip() != line]
    out = "\n".join(kept)
    return out.rstrip("\n") + "\n" if body.endswith("\n") else out


def _fix_home_photo(body: str) -> str:
    # The Home photo now sits in the hero (a template), so the placeholder is dropped.
    return _drop_line(body, "[PLACEHOLDER: storefront photo]")


def _fix_menu_photo(body: str) -> str:
    # Only when the old placeholder is still there, so a photo the Manager removed stays removed.
    if "[PLACEHOLDER: menu photo]" not in body:
        return body
    body = _drop_line(body, "[PLACEHOLDER: menu photo]")
    if "[PHOTO: menu]" not in body:
        first, sep, rest = body.partition("\n\n")
        body = f"{first}\n\n[PHOTO: menu]\n\n{rest}" if sep else f"{body.rstrip()}\n\n[PHOTO: menu]\n"
    return body


def _fix_story_photo(body: str) -> str:
    if "[PLACEHOLDER: chef/kitchen photo]" not in body:
        return body
    body = _drop_line(body, "[PLACEHOLDER: chef/kitchen photo]")
    # At the end, as the placeholder was: the portrait stands alone rather than sitting
    # beside the paragraph that names people.
    return body if "[PHOTO: our-story]" in body else f"{body.rstrip()}\n\n[PHOTO: our-story]\n"


_PHOTO_FIXES = {"home": _fix_home_photo, "menu": _fix_menu_photo, "our-story": _fix_story_photo}


def refresh_public_copy() -> int:
    """Fix the duplicate-heading and internal-note problems in saved pages.

    A page whose body is still exactly what we first seeded is replaced.
    Anything the Manager has edited keeps their edits and only loses the two
    known problems: a first line that repeats the page title as a heading, and
    a sentence pointing at a `notes/` file, plus the agreed Our Story wording
    (_WORDING_FIXES), each only where the old text is still there. Returns how many pages changed;
    safe to run any number of times.
    """
    fresh = {"menu": (LEGACY_MENU_BODY, MENU_BODY),
             "our-story": (LEGACY_OUR_STORY_BODY, OUR_STORY_BODY)}
    changed = 0
    for page in db.list_pages():
        slug, body = page["slug"], page["body_md"]
        if slug in fresh and body == fresh[slug][0]:
            new = fresh[slug][1]
        else:
            new = _INTERNAL_NOTE.sub("", body)
            first, _, rest = new.partition("\n")
            if first.startswith("#") and first.lstrip("#").strip().lower() == page["title"].lower():
                # The title is already the page's <h1>, so what were sub-headings
                # under it become the page's top-level sections.
                new = re.sub(r"(?m)^### ", "## ", rest.lstrip("\n"))
        for pattern, replacement in _WORDING_FIXES.get(slug, []):
            new = pattern.sub(replacement, new)
        if slug in _PHOTO_FIXES:
            new = _PHOTO_FIXES[slug](new)
        if new != body:
            db.update_page(slug, title=page["title"], body_md=new,
                           status=page["status"], author_id=page["author_id"])
            print(f"Updated public copy: {slug}")
            changed += 1
    return changed


def refresh_news() -> int:
    """Bring an existing Michelin post up to date in place (never a duplicate).

    Only a post that still says exactly what the old seed said is rewritten; one the
    Manager has edited is left alone. Status is not touched. Returns posts changed.
    """
    changed = 0
    slug, title, when, _, body = REAL_NEWS[0]
    post = db.get_post_by_slug(slug)
    if post and post["title"] == LEGACY_MICHELIN_TITLE and post["body_md"] == LEGACY_MICHELIN_BODY:
        db.update_post(slug, title=title, body_md=body, author_id=post["author_id"])
        if post["status"] == "published" and post["published_at"] == LEGACY_MICHELIN_PUBLISHED_AT:
            db.set_post_status(slug, "published", published_at=when)
        print(f"Updated News post: {slug}")
        changed += 1
    return changed


def seed_news(items=None) -> None:
    """Create any of `items` (default: all seed News) that do not exist yet.

    A post that exists is never rewritten or re-published, except by refresh_news().
    A post the Manager deleted is created again on the next run (as with every seed item).
    Pass REAL_NEWS to add just the two real posts and no demo posts.
    """
    manager = db.get_user_by_email(DEMO_MANAGER_EMAIL)
    for slug, title, created_at, status, body_md in (NEWS_POSTS if items is None else items):
        created = db.create_post(
            slug, title=title, body_md=body_md,
            author_id=manager["id"] if manager else None, created_at=created_at,
        )
        if created:
            if status == "published":
                db.set_post_status(slug, "published", published_at=created_at)
            print(f"Seeded News post: {slug} ({status})")
    refresh_news()


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

    refresh_public_copy()

    seed_news()
    return 0


if __name__ == "__main__":
    sys.exit(main())
