"""Admin templates use relative links, and every link still resolves.

The submission checker forbids root-absolute `href="/..."` in templates. Relative
links are only correct if they resolve from the URL the page is served at, so
these tests resolve each `href` against its page's own URL and follow it. That
catches a link that is relative but wrong on a nested route
(e.g. `pages` from `/admin/pages/home` would become `/admin/pages/pages`).
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
HREF = re.compile(r'href="([^"]+)"')


def _local_hrefs(html: str) -> list[str]:
    """Links inside <main> only: the shared base.html header links are the public
    site's relative paths and are out of scope for this test."""
    main = re.search(r"<main>(.*?)</main>", html, re.S).group(1)
    return [h for h in HREF.findall(main) if not h.startswith(("http", "#", "mailto:", "tel:"))]


def test_no_root_absolute_hrefs_in_any_template():
    offenders = [
        str(p.relative_to(TEMPLATES))
        for p in TEMPLATES.rglob("*.html")
        if re.search(r'(href|src)="/', p.read_text())
    ]
    assert offenders == []


def test_dashboard_links_resolve(client_as):
    manager = client_as("admin")
    url = "/admin/dashboard"
    links = _local_hrefs(manager.get(url).text)
    assert links, "dashboard should link to the pages list for a Manager"
    for href in links:
        assert manager.get(urljoin(url, href)).status_code == 200, href


def test_pages_list_links_resolve_including_nested_routes(client_as):
    manager = client_as("admin")
    url = "/admin/pages"
    links = _local_hrefs(manager.get(url).text)
    resolved = {urljoin(url, h) for h in links}
    assert "/admin/pages/new" in resolved
    assert "/admin/pages/home" in resolved  # a nested edit route, from a list row
    for target in resolved:
        assert manager.get(target).status_code == 200, target
