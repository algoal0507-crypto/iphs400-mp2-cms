"""T07: access control and CSRF, swept over every route the app really has.

The route list is read from the running app (`app.openapi()`), not typed out here,
so a route added later fails `test_every_route_is_classified` until someone decides
who may use it. Everything is asserted through HTTP: status codes, redirects, and
what the user and content lists show afterwards.

Roles (CONTEXT.md): the Manager is `admin`, the Editor is `editor`.
"""
from __future__ import annotations

import re
import time
import zlib

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import create_app
from tests.conftest import DEMO_USERS

ADMIN = DEMO_USERS["admin"]
EDITOR = DEMO_USERS["editor"]

# --- The route table -----------------------------------------------------------

PUBLIC = {  # reachable by anyone; the login form and the two asset files it needs
    ("GET", "/"), ("GET", "/login"), ("POST", "/login"),
    ("GET", "/admin/style.css"), ("GET", "/admin/preview.js"),
}
ANY_SIGNED_IN = {  # Manager and Editor (the Editor only on drafts, see posts tests)
    ("GET", "/admin"), ("GET", "/admin/dashboard"), ("GET", "/admin/content"),
    ("GET", "/admin/posts"), ("GET", "/admin/posts/new"), ("POST", "/admin/posts/new"),
    ("GET", "/admin/posts/{slug}"), ("POST", "/admin/posts/{slug}"),
    ("POST", "/admin/posts/{slug}/delete"), ("POST", "/admin/preview"), ("POST", "/logout"),
}
MANAGER_ONLY = {
    ("GET", "/admin/pages"), ("GET", "/admin/pages/new"), ("POST", "/admin/pages/new"),
    ("GET", "/admin/pages/{slug}"), ("POST", "/admin/pages/{slug}"),
    ("POST", "/admin/pages/{slug}/delete"),
    ("POST", "/admin/posts/{slug}/publish"), ("POST", "/admin/posts/{slug}/unpublish"),
    ("GET", "/admin/users"), ("GET", "/admin/users/new"), ("POST", "/admin/users/new"),
    ("POST", "/admin/users/{user_id}/role"), ("POST", "/admin/users/{user_id}/deactivate"),
}


def _documented_routes() -> set[tuple[str, str]]:
    paths = create_app().openapi()["paths"]
    return {(method.upper(), path) for path, methods in paths.items() for method in methods}


def _registered_routes() -> set[tuple[str, str]]:
    """Every route the app really has, including ones hidden from the schema."""
    found = set()
    for route in create_app().routes:
        for r in getattr(getattr(route, "original_router", None), "routes", [route]):
            for method in getattr(r, "methods", None) or ():
                if method not in ("HEAD", "OPTIONS") and hasattr(r, "path"):
                    found.add((method, r.path))
    return found


def _app_routes() -> set[tuple[str, str]]:
    return _documented_routes() | _registered_routes()


def test_every_route_is_classified():
    known = PUBLIC | ANY_SIGNED_IN | MANAGER_ONLY
    unclassified = sorted(_app_routes() - known)
    assert not unclassified, f"Decide who may use these routes, then add them to the table: {unclassified}"
    assert not sorted(known - _app_routes()), "The table lists routes the app no longer has."


def test_no_route_is_hidden_from_the_schema():
    assert _documented_routes() == _registered_routes()


# --- Setup helpers (not assertions) --------------------------------------------

@pytest.fixture
def content():
    """One draft post and one published post, so slug routes have something real."""
    db.create_post("draft-one", title="Draft one", body_md="d", author_id=None)
    db.create_post("pub-one", title="Pub one", body_md="p", author_id=None)
    db.set_post_status("pub-one", "published", published_at="2026-10-01 12:00:00")


FORM = {  # one payload that satisfies every form; extra fields are ignored
    "title": "Changed", "slug": "brand-new", "body_md": "changed", "status": "published",
    "email": "intruder@example.test", "password": "a-long-enough-pw", "role": "admin",
}


def _fill(path: str, *, post_slug="draft-one") -> str:
    user_ids = {e: db.get_user_by_email(e)["id"] for e in (ADMIN["email"], EDITOR["email"])}
    if path.startswith("/admin/pages/"):
        return path.replace("{slug}", "home")
    return (path.replace("{slug}", post_slug)
                .replace("{user_id}", str(user_ids[EDITOR["email"]])))


def _csrf(client) -> str:
    client.get("/login")  # any page that sets the cookie
    return client.cookies.get("csrf_token")


def _send(client, method, path, *, token="auto", data=None):
    data = dict(FORM if data is None else data)
    if method == "GET":
        return client.get(path, follow_redirects=False)
    if token == "auto":
        token = _csrf(client)
    if token is not None:
        data["csrf_token"] = token
    return client.post(path, data=data, follow_redirects=False)


def _strip(html: str) -> str:
    return re.sub(r'name="csrf_token" value="[^"]*"', "", html)


def _state(client_as) -> str:
    """What the Manager sees: every content row and every user, tokens removed."""
    admin = client_as("admin")
    return _strip(admin.get("/admin/content").text + admin.get("/admin/users").text)


def _is_redirect_to_login(response) -> bool:
    return response.status_code in (302, 303) and response.headers["location"].endswith("/login")


ADMIN_ROUTES = sorted(r for r in PUBLIC | ANY_SIGNED_IN | MANAGER_ONLY
                      if r[1].startswith("/admin") and r not in PUBLIC)
EDITOR_BLOCKED = sorted(MANAGER_ONLY)
CSRF_ROUTES = sorted(r for r in ANY_SIGNED_IN | MANAGER_ONLY | PUBLIC if r[0] == "POST")


# --- Anonymous visitors: always sent to the login page -------------------------

@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_anonymous_is_redirected_to_login_on_every_admin_route(client, content, method, path):
    response = _send(client, method, _fill(path), token=None)
    assert _is_redirect_to_login(response), (method, path, response.status_code)
    assert "Welcome" not in response.text and "<h1>" not in response.text


@pytest.mark.parametrize("method,path", [r for r in ADMIN_ROUTES if r[0] == "POST"])
def test_anonymous_is_redirected_even_with_a_valid_looking_token(client, content, method, path):
    response = _send(client, method, _fill(path))  # token and cookie both present
    assert _is_redirect_to_login(response), (method, path, response.status_code)


# --- The Editor: blocked by direct request on every Manager-only route ---------

@pytest.mark.parametrize("method,path", EDITOR_BLOCKED)
def test_editor_is_blocked_on_every_manager_only_route(client_as, content, method, path):
    before = _state(client_as)
    editor = client_as("editor")
    response = _send(editor, method, _fill(path, post_slug="draft-one"))
    assert response.status_code == 403 or _is_redirect_to_login(response), (method, path, response.status_code)
    assert "intruder@example.test" not in response.text
    assert _state(client_as) == before, f"{method} {path} changed something for an Editor"


@pytest.mark.parametrize("method,path", sorted(r for r in ANY_SIGNED_IN if r != ("POST", "/logout")))
def test_the_routes_the_editor_may_use_are_not_blocked(client_as, content, method, path):
    editor = client_as("editor")
    response = _send(editor, method, _fill(path), data={**FORM, "slug": "editor-draft"})
    assert response.status_code in (200, 303, 400) and not _is_redirect_to_login(response), (method, path)


def test_the_editor_cannot_touch_a_published_post(client_as, content):
    editor = client_as("editor")
    assert editor.get("/admin/posts/pub-one", follow_redirects=False).status_code in (302, 303, 403)
    for tail in ("", "/delete"):
        response = _send(editor, "POST", f"/admin/posts/pub-one{tail}")
        assert response.status_code in (302, 303, 403), tail
    assert "Pub one" in client_as("admin").get("/admin/posts").text


def test_the_manager_can_use_every_route_in_the_table(client_as, content):
    admin = client_as("admin")
    # Deletes go last so the other routes still have something to act on.
    for method, path in sorted(ANY_SIGNED_IN | MANAGER_ONLY, key=lambda r: (r[1].endswith("/delete"), r)):
        if (method, path) in {("POST", "/logout")}:
            continue
        response = _send(admin, method, _fill(path), data={**FORM, "slug": f"mgr-{zlib.crc32(path.encode()) % 9999}"})
        assert response.status_code in (200, 303, 400) and not _is_redirect_to_login(response), (method, path, response.status_code)


# --- CSRF: every state-changing POST needs a matching token --------------------

def _poster_for(client_as, method, path):
    if path == "/login":
        return TestClient(create_app())
    return client_as("admin")


@pytest.mark.parametrize("method,path", CSRF_ROUTES)
def test_post_without_a_csrf_token_is_rejected_and_changes_nothing(client_as, content, method, path):
    before = _state(client_as)
    client = _poster_for(client_as, method, path)
    client.get("/login")  # make sure a csrf cookie exists, so only the form field is missing
    assert _send(client, method, _fill(path), token=None).status_code == 403, "missing token"
    assert _send(client, method, _fill(path), token="not-the-cookie-value").status_code == 403, "wrong token"
    assert _send(client, method, _fill(path), token="").status_code == 403, "empty token"
    assert _state(client_as) == before, f"{method} {path} changed something without a valid token"


@pytest.mark.parametrize("method,path", CSRF_ROUTES)
def test_post_with_a_token_but_no_csrf_cookie_is_rejected(client_as, content, method, path):
    client = _poster_for(client_as, method, path)
    token = _csrf(client)
    client.cookies.delete("csrf_token")
    assert _send(client, method, _fill(path), token=token).status_code == 403


@pytest.mark.parametrize("method,path", [r for r in CSRF_ROUTES if "{" in r[1]])
def test_a_missing_token_gives_the_same_answer_whether_or_not_the_item_exists(client_as, content, method, path):
    """The token is checked before the item is looked up, so a tokenless request
    cannot be used to find out which users or slugs exist."""
    admin = client_as("admin")
    real = _send(admin, method, _fill(path), token=None).status_code
    missing_path = (path.replace("{slug}", "no-such-slug-at-all").replace("{user_id}", "987654"))
    assert _send(admin, method, missing_path, token=None).status_code == real == 403


# --- Other verbs and the cookie that carries the session -----------------------

@pytest.mark.parametrize("who", ["anonymous", "editor", "admin"])
@pytest.mark.parametrize("verb", ["PUT", "PATCH", "DELETE"])
def test_no_route_accepts_put_patch_or_delete(client, client_as, content, who, verb):
    actor = client if who == "anonymous" else client_as(who)
    before = _state(client_as)
    for _, path in ADMIN_ROUTES + [("POST", "/login"), ("POST", "/logout")]:
        response = actor.request(verb, _fill(path), data=FORM, follow_redirects=False)
        assert response.status_code in (302, 303, 401, 403, 404, 405), (who, verb, path, response.status_code)
    assert _state(client_as) == before


def test_login_sets_an_httponly_samesite_session_cookie(client):
    token = _csrf(client)
    response = client.post("/login", data={"email": ADMIN["email"], "password": ADMIN["password"],
                                           "csrf_token": token}, follow_redirects=False)
    cookie = next(c for c in response.headers.get_list("set-cookie") if c.startswith("session="))
    assert "httponly" in cookie.lower() and "samesite=lax" in cookie.lower()


def test_the_csrf_cookie_is_httponly_and_samesite(client):
    cookie = next(c for c in client.get("/login").headers.get_list("set-cookie") if c.startswith("csrf_token="))
    assert "httponly" in cookie.lower() and "samesite=lax" in cookie.lower()


# --- Login: no hint about which accounts exist ---------------------------------

def _login(email, password):
    client = TestClient(create_app())
    return client.post("/login", data={"email": email, "password": password, "csrf_token": _csrf(client)},
                       follow_redirects=False)


def test_unknown_email_and_wrong_password_look_identical():
    unknown = _login("nobody@example.test", "whatever-password")
    wrong = _login(ADMIN["email"], "whatever-password")
    assert unknown.status_code == wrong.status_code == 401
    assert _strip(unknown.text).replace("nobody@example.test", "") == _strip(wrong.text).replace(ADMIN["email"], "")


def test_unknown_email_takes_about_as_long_as_a_wrong_password():
    """Password hashing is slow on purpose; skipping it for unknown emails would
    let timing reveal which accounts exist."""
    def best(email):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            _login(email, "whatever-password")
            times.append(time.perf_counter() - start)
        return min(times)

    assert best("nobody@example.test") > 0.5 * best(ADMIN["email"])


def test_oversized_login_fields_get_the_same_refusal_as_any_wrong_login():
    for email, password in [(ADMIN["email"], "x" * 200_000), ("a" * 5000 + "@example.test", "x")]:
        response = _login(email, password)
        assert response.status_code == 401 and "Invalid email or password" in response.text
        assert "session=" not in "".join(response.headers.get_list("set-cookie"))


# --- Limits on what the Manager can submit -------------------------------------

@pytest.mark.parametrize("field,value", [("email", "a" * 300 + "@example.test"), ("password", "p" * 5000)],
                         ids=["long-email", "long-password"])
def test_user_creation_rejects_oversized_input(client_as, field, value):
    admin = client_as("admin")
    before = _state(client_as)
    response = _send(admin, "POST", "/admin/users/new", data={**FORM, field: value})
    assert response.status_code == 400
    assert _state(client_as) == before


# --- Things a browser should not be allowed to do with these pages -------------

def _protected(response, *, cacheable=False):
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert headers.get("x-frame-options", "").upper() == "DENY"
    assert headers.get("x-content-type-options", "").lower() == "nosniff"
    assert cacheable or "no-store" in headers.get("cache-control", "")


@pytest.mark.parametrize("path", ["/login", "/admin/dashboard", "/admin/users", "/admin/posts/new"])
def test_admin_pages_cannot_be_framed_cached_or_sniffed(client_as, path):
    _protected(client_as("admin").get(path))


def test_the_protective_headers_also_ride_on_redirects_and_errors(client, client_as, content):
    _protected(client.get("/admin/dashboard", follow_redirects=False))              # redirect to login
    _protected(client_as("editor").get("/admin/users"))                             # 403
    _protected(client_as("admin").get("/admin/posts/no-such-post"))                 # 404
    _protected(client.get("/login/", follow_redirects=False))                       # slash redirect
    _protected(client.get("/admin/style.css"), cacheable=True)                      # asset files


def test_the_editor_with_a_bad_token_is_refused_on_the_routes_the_editor_may_use(client_as, content):
    before = _state(client_as)
    editor = client_as("editor")
    editor.get("/login")
    for method, path in sorted(r for r in ANY_SIGNED_IN if r[0] == "POST" and r != ("POST", "/logout")):
        assert _send(editor, method, _fill(path), token=None).status_code == 403, path
        assert _send(editor, method, _fill(path), token="forged").status_code == 403, path
    assert _state(client_as) == before


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_the_api_docs_are_not_served(client, path):
    assert client.get(path, follow_redirects=False).status_code == 404
