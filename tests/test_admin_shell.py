"""T08: admin pages load their stylesheet and header link from any route depth.

`base.html` is shared with the exported public site, where flat relative names
(`style.css`, `index.html`) are right. Under `/admin/...` and `/login` they 404,
so the admin shell computes relative links from the request's own path instead.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

import pytest

from app.urls import relative_url

STYLESHEET = re.compile(r'<link rel="stylesheet" href="([^"]+)"')
HEADER_LINK = re.compile(r"<header>\s*<a href=\"([^\"]+)\"")


@pytest.mark.parametrize("from_path, to_path, expected", [
    ("/login", "/admin/style.css", "admin/style.css"),          # top-level route
    ("/admin", "/admin/style.css", "admin/style.css"),          # /admin has no trailing slash
    ("/admin/dashboard", "/admin/style.css", "style.css"),      # sibling
    ("/admin/pages/home", "/admin/style.css", "../style.css"),  # nested
    ("/admin/pages/home", "/admin/dashboard", "../dashboard"),
    ("/admin/pages/", "/admin/dashboard", "../dashboard"),      # trailing slash = a directory
])
def test_relative_url_matches_browser_resolution(from_path, to_path, expected):
    assert relative_url(from_path, to_path) == expected
    assert urljoin(from_path, expected) == to_path


def test_helper_never_returns_a_root_absolute_url():
    assert not relative_url("/admin/pages/home", "/admin/dashboard").startswith("/")


ADMIN_URLS = ["/admin", "/admin/dashboard", "/admin/pages", "/admin/pages/new", "/admin/pages/home"]


@pytest.mark.parametrize("url", ADMIN_URLS)
def test_admin_page_stylesheet_resolves(client_as, url):
    manager = client_as("admin")
    page = manager.get(url)
    assert page.status_code == 200
    href = STYLESHEET.search(page.text).group(1)
    assert not href.startswith("/")
    css = manager.get(urljoin(url, href))
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")


@pytest.mark.parametrize("url", ["/admin", "/admin/dashboard", "/admin/pages", "/admin/pages/new", "/admin/pages/home"])
def test_admin_header_link_reaches_the_dashboard(client_as, url):
    manager = client_as("admin")
    href = HEADER_LINK.search(manager.get(url).text).group(1)
    assert not href.startswith("/")
    assert urljoin(url, href) == "/admin/dashboard"
    assert manager.get(urljoin(url, href)).status_code == 200


def test_login_page_stylesheet_resolves(client):
    page = client.get("/login")
    href = STYLESHEET.search(page.text).group(1)
    assert client.get(urljoin("/login", href)).status_code == 200


def test_public_export_still_uses_flat_names(tmp_path, monkeypatch):
    from app import db, publish, settings
    monkeypatch.setattr(settings, "SITE", tmp_path / "site")
    db.update_page("home", title="Home", body_md="hi", status="published", author_id=None)
    out = publish.render_site()
    html = (out / "index.html").read_text()
    assert 'href="style.css"' in html
    assert 'href="index.html"' in html
    assert not re.search(r'(href|src)="/', html)


def test_list_and_dashboard_links_survive_a_trailing_slash(client_as):
    """Review finding: bare `pages/new` would 404 if the list were served at
    `/admin/pages/`; links computed from the request path do not."""
    from tests.test_admin_links import _local_hrefs

    manager = client_as("admin")
    for url in ("/admin/pages/", "/admin/dashboard/"):
        page = manager.get(url, follow_redirects=False)
        if page.status_code in (301, 302, 303, 307, 308):
            continue  # the app redirects to the canonical URL; links are tested there
        for href in _local_hrefs(page.text):
            assert manager.get(urljoin(url, href)).status_code == 200, (url, href)
