"""T09 follow-up: the public copy reads like a restaurant site, not a project.

Checked on the exported HTML a visitor gets, from the real seed content, and on
the one-off refresh that fixes content already saved in an existing database.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from app import db
from app.publish import render_site

SEED_PATH = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo.py"
# Things only the project team should ever see.
INTERNAL = re.compile(r"notes/|\.md\b|research|ticket|rubric|placeholder text|TODO|T0\d\b", re.I)
PRICE = re.compile(r"\$\s?\d|\d\s?(?:MXN|pesos|USD|EUR)|MX\$|€", re.I)


def _seed_module(monkeypatch):
    monkeypatch.setenv("CMS_ADMIN_PASSWORD", "seed-admin-pw")
    monkeypatch.setenv("CMS_EDITOR_PASSWORD", "seed-editor-pw")
    spec = importlib.util.spec_from_file_location("seed_demo_copy_test", SEED_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def seed(monkeypatch):
    module = _seed_module(monkeypatch)
    assert module.main() == 0
    return module


@pytest.fixture
def site(seed, tmp_path):
    return render_site(tmp_path / "site")


def _visible(html):
    return re.sub(r"<[^>]+>", " ", html)


def test_no_page_repeats_its_title_as_a_second_heading(site):
    for page in site.glob("*.html"):
        html = page.read_text()
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1).strip().lower()
        headings = [h.strip().lower() for h in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", html, re.S)]
        assert h1 not in headings, (page.name, h1)
        assert len(re.findall(r"<h1\b", html)) == 1, page.name


def test_no_internal_notes_or_filenames_on_any_public_page(site):
    for page in site.glob("*.html"):
        text = _visible(page.read_text())
        # The footer legitimately names the course project.
        text = text.replace("A student prototype for IPHS 400 Mini-Project #2. Not affiliated with or endorsed by La Once Mil.", "")
        assert not INTERNAL.search(text), (page.name, INTERNAL.search(text).group(0))


def test_the_student_disclaimer_stays_on_every_page(site):
    for page in site.glob("*.html"):
        assert "Not affiliated with or endorsed by La Once Mil" in page.read_text(), page.name


def test_menu_is_sectioned_with_distinct_dish_names_and_no_invented_prices(site):
    html = (site / "menu.html").read_text()
    sections = [h.strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)]
    assert sections[:2] == ["Tacos", "Beyond tacos"] and {"Salsas", "Desserts"} <= set(sections)
    dishes = re.findall(r"<li>\s*<strong>(.*?)</strong>", html, re.S)
    assert {"Carne asada", "A5 Wagyu", "Lechón (carnitas)"} <= set(dishes)
    assert not PRICE.search(_visible(html))


def test_menu_dishes_say_only_what_the_research_supports(site):
    text = _visible((site / "menu.html").read_text())
    for invented in ("Grilled", "ask your server", "Our signature", "Prices aren't", "Fish prepared"):
        assert invented not in text, invented
    assert "Signature dish" in text  # the A5 wagyu, per the research


def test_menu_page_is_scoped_for_menu_styling_and_news_is_not(site, seed):
    assert 'class="page page-menu"' in (site / "menu.html").read_text()
    assert "page-menu" not in (site / "our-story.html").read_text()
    assert "page-menu" not in (site / "news.html").read_text()


def test_manager_edits_the_menu_in_the_admin_and_the_export_follows(client_as, seed, tmp_path):
    admin = client_as("admin")
    form = admin.get("/admin/pages/menu")
    assert form.status_code == 200 and "## Tacos" in form.text and "- **Carne asada**" in form.text
    body = db.get_page_by_slug("menu")["body_md"] + "\n## Specials\n\n- **Birria**\n  Weekends only\n"
    saved = admin.post("/admin/pages/menu", follow_redirects=False, data={
        "title": "Menu", "body_md": body, "status": "published",
        "csrf_token": form.cookies.get("csrf_token")})
    assert saved.status_code in (200, 303)
    html = (render_site(tmp_path / "out") / "menu.html").read_text()
    assert "Specials" in html and "Birria" in html and "Weekends only" in html


def test_menu_still_a_plain_markdown_page(seed):
    body = db.get_page_by_slug("menu")["body_md"]
    assert body.lstrip().startswith("Gourmet tacos") and "## Tacos" in body and "- **Carne asada**" in body


# --- Refreshing content already saved in an existing database ----------------

def _save(slug, body):
    page = db.get_page_by_slug(slug)
    db.update_page(slug, title=page["title"], body_md=body, status=page["status"],
                   author_id=page["author_id"])


def test_refresh_replaces_the_untouched_old_menu_and_story(seed):
    _save("menu", seed.LEGACY_MENU_BODY)
    _save("our-story", seed.LEGACY_OUR_STORY_BODY)
    assert seed.refresh_public_copy() == 2
    assert db.get_page_by_slug("menu")["body_md"] == seed.MENU_BODY
    assert db.get_page_by_slug("our-story")["body_md"] == seed.OUR_STORY_BODY


def test_refresh_keeps_other_saved_edits_and_only_removes_the_known_problems(seed):
    edited = seed.LEGACY_MENU_BODY.replace("Sorbets, ice creams, and meringues.",
                                           "Sorbets, ice creams, meringues, and flan.") + "\nOpen late on Fridays.\n"
    _save("menu", edited)
    seed.refresh_public_copy()
    body = db.get_page_by_slug("menu")["body_md"]
    assert "flan" in body and "Open late on Fridays." in body       # the Manager's edits survive
    assert not body.lstrip().startswith("## Menu")                  # duplicate heading gone
    assert "notes/restaurant-research.md" not in body               # internal note gone
    assert "Carne asada" in body                                    # the rest untouched


def test_refresh_is_safe_to_run_twice_and_leaves_clean_content_alone(seed):
    before = {s: db.get_page_by_slug(s)["body_md"] for s in ("home", "menu", "our-story")}
    assert seed.refresh_public_copy() == 0
    assert {s: db.get_page_by_slug(s)["body_md"] for s in before} == before


def test_refresh_does_not_touch_status_title_or_author(seed):
    _save("menu", seed.LEGACY_MENU_BODY)
    page = db.get_page_by_slug("menu")
    seed.refresh_public_copy()
    after = db.get_page_by_slug("menu")
    assert (after["title"], after["status"], after["author_id"]) == (page["title"], page["status"], page["author_id"])


def test_refresh_handles_heading_case_spacing_and_a_reworded_note(seed):
    body = "## our story  \n\nWe opened. See `notes/other-file.md` for details behind this.\n\nMore."
    _save("our-story", body)
    seed.refresh_public_copy()
    got = db.get_page_by_slug("our-story")["body_md"]
    assert got.startswith("We opened.") and "notes/" not in got and "More." in got


def test_refresh_promotes_old_sub_headings_after_dropping_the_title_heading(seed):
    _save("menu", "## Menu\n\nIntro.\n\n### Salsas\n\nMild.\n\n### Desserts\n\nSorbets.\n")
    seed.refresh_public_copy()
    body = db.get_page_by_slug("menu")["body_md"]
    assert "## Salsas" in body and "### Salsas" not in body and body.startswith("Intro.")


def test_refresh_leaves_a_draft_pages_status_alone_and_an_untitled_start_unchanged(seed):
    page = db.get_page_by_slug("menu")
    db.update_page("menu", title="Menu", body_md="Just text, no heading.", status="draft",
                   author_id=page["author_id"])
    seed.refresh_public_copy()
    after = db.get_page_by_slug("menu")
    assert after["status"] == "draft" and after["body_md"] == "Just text, no heading."
