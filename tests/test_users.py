"""T06: user management. Manager-only; deactivation takes effect immediately.

HTTP seam only (spec #1, Testing Decisions): everything is asserted through
status codes, redirects, and page content. State is observed through the user
list page, logging in, and what each account can reach.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import DEMO_USERS

ADMIN = DEMO_USERS["admin"]["email"]
EDITOR = DEMO_USERS["editor"]["email"]


def _csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def _create(client, email="new@example.test", password="a-long-enough-pw", role="editor", **extra):
    csrf = _csrf(client, "/admin/users/new")
    return client.post(
        "/admin/users/new",
        data={"email": email, "password": password, "role": role, "csrf_token": csrf, **extra},
        follow_redirects=False,
    )


def _login(email, password):
    c = TestClient(create_app())
    csrf = _csrf(c, "/login")
    response = c.post("/login", data={"email": email, "password": password, "csrf_token": csrf},
                      follow_redirects=False)
    return c, response


def _listing(admin):
    return admin.get("/admin/users").text


def _emails(admin):
    return re.findall(r'data-user="([^"]+)"', _listing(admin))


def _row(admin, email):
    match = re.search(rf'<li data-user="{re.escape(email)}">(.*?)</li>', _listing(admin), re.S)
    assert match, f"{email} not in user list"
    return match.group(1)


def _user_id(admin, email):
    """The id a real browser would submit: read off the user list's own forms."""
    match = re.search(r"/admin/users/(\d+)/role", _row(admin, email))
    assert match, f"no controls for {email}"
    return int(match.group(1))


def _post(client, path, form_page="/admin/users", **data):
    csrf = _csrf(client, form_page)
    return client.post(path, data={"csrf_token": csrf, **data}, follow_redirects=False)


# --- Manager: create ---------------------------------------------------------

def test_manager_creates_a_user_who_can_then_log_in(client_as):
    admin = client_as("admin")
    assert _create(admin, role="editor").status_code == 303
    row = _row(admin, "new@example.test")
    assert "Editor" in row and "active" in row and "deactivated" not in row
    assert "a-long-enough-pw" not in _listing(admin)
    _, response = _login("new@example.test", "a-long-enough-pw")
    assert response.status_code == 303


def test_user_list_shows_users_to_the_manager(client_as):
    emails = _emails(client_as("admin"))
    assert ADMIN in emails and EDITOR in emails


def test_created_user_can_log_in_with_different_email_case(client_as):
    _create(client_as("admin"), email="Mixed@Example.test")
    _, response = _login("  MIXED@example.test ", "a-long-enough-pw")
    assert response.status_code == 303


@pytest.mark.parametrize("kwargs,reason", [
    ({"email": "not-an-email"}, "bad email"),
    ({"password": "short"}, "short password"),
    ({"role": "superuser"}, "unknown role"),
    ({"email": EDITOR}, "duplicate email"),
])
def test_create_rejects_bad_input(client_as, kwargs, reason):
    admin = client_as("admin")
    before = _emails(admin)
    response = _create(admin, **kwargs)
    assert response.status_code == 400, reason
    assert _emails(admin) == before


# --- Manager: role change ----------------------------------------------------

def test_manager_changes_a_users_role(client_as):
    admin = client_as("admin")
    uid = _user_id(admin, EDITOR)
    assert _post(admin, f"/admin/users/{uid}/role", role="admin").status_code == 303
    assert "Manager" in _row(admin, EDITOR)
    assert _post(admin, f"/admin/users/{uid}/role", role="editor").status_code == 303
    assert "Editor" in _row(admin, EDITOR)


def test_role_change_takes_effect_on_the_users_next_request(client_as):
    editor = client_as("editor")
    assert editor.get("/admin/users").status_code == 403
    admin = client_as("admin")
    _post(admin, f"/admin/users/{_user_id(admin, EDITOR)}/role", role="admin")
    assert editor.get("/admin/users").status_code == 200


def test_role_change_rejects_unknown_role(client_as):
    admin = client_as("admin")
    uid = _user_id(admin, EDITOR)
    assert _post(admin, f"/admin/users/{uid}/role", role="root").status_code == 400
    assert "Editor" in _row(admin, EDITOR)


def _promote_editor_and_get_admin_id(client_as):
    """The Manager's own row has no controls; a second Manager can see its id."""
    admin = client_as("admin")
    _post(admin, f"/admin/users/{_user_id(admin, EDITOR)}/role", role="admin")
    peer = client_as("editor")
    return admin, _user_id(peer, ADMIN)


def test_manager_cannot_change_their_own_role(client_as):
    admin, uid = _promote_editor_and_get_admin_id(client_as)
    assert _post(admin, f"/admin/users/{uid}/role", role="editor").status_code == 400
    assert admin.get("/admin/users").status_code == 200  # still a Manager


# --- Manager: deactivate -----------------------------------------------------

def test_manager_deactivates_a_user(client_as):
    admin = client_as("admin")
    uid = _user_id(admin, EDITOR)
    assert _post(admin, f"/admin/users/{uid}/deactivate").status_code == 303
    assert "deactivated" in _row(admin, EDITOR)


def test_manager_cannot_deactivate_themselves(client_as):
    admin, uid = _promote_editor_and_get_admin_id(client_as)
    assert _post(admin, f"/admin/users/{uid}/deactivate").status_code == 400
    assert admin.get("/admin/users").status_code == 200  # session still valid


def test_deactivated_user_login_is_refused_with_a_clear_message(client_as):
    admin = client_as("admin")
    _post(admin, f"/admin/users/{_user_id(admin, EDITOR)}/deactivate")
    c, response = _login(EDITOR, DEMO_USERS["editor"]["password"])
    assert response.status_code == 401
    assert "deactivated" in response.text.lower()
    assert "session" not in c.cookies


def test_wrong_password_for_a_deactivated_user_does_not_reveal_deactivation(client_as):
    admin = client_as("admin")
    _post(admin, f"/admin/users/{_user_id(admin, EDITOR)}/deactivate")
    _, response = _login(EDITOR, "wrong-password")
    assert response.status_code == 401
    assert "deactivated" not in response.text.lower()


def test_deactivated_users_existing_session_stops_working_on_next_request(client_as):
    editor = client_as("editor")
    assert editor.get("/admin/dashboard").status_code == 200
    admin = client_as("admin")
    _post(admin, f"/admin/users/{_user_id(admin, EDITOR)}/deactivate")
    after = editor.get("/admin/dashboard", follow_redirects=False)
    assert after.status_code in (302, 303) and after.headers["location"].endswith("/login")
    assert editor.get("/admin/posts", follow_redirects=False).status_code in (302, 303)


# --- Editor and anonymous are blocked, including direct requests -------------

def test_editor_cannot_reach_any_user_route(client_as):
    admin = client_as("admin")
    uid = _user_id(admin, EDITOR)  # any real id; the Editor's own works
    before = _emails(admin)
    editor = client_as("editor")
    csrf = _csrf(editor, "/admin/posts/new")
    assert editor.get("/admin/users").status_code in (302, 403)
    assert editor.get("/admin/users/new").status_code in (302, 403)
    for path, data in [
        ("/admin/users/new", {"email": "x@example.test", "password": "a-long-enough-pw", "role": "admin"}),
        (f"/admin/users/{uid}/role", {"role": "admin"}),
        (f"/admin/users/{uid}/deactivate", {}),
    ]:
        response = editor.post(path, data={**data, "csrf_token": csrf}, follow_redirects=False)
        assert response.status_code in (302, 403), path
    assert _emails(admin) == before
    row = _row(admin, EDITOR)
    assert "Editor" in row and "deactivated" not in row
    assert editor.get("/admin/dashboard").status_code == 200  # not deactivated


def test_editor_gets_no_users_link_on_the_dashboard(client_as):
    assert "/admin/users" not in client_as("editor").get("/admin/dashboard").text


def test_manager_dashboard_links_to_users_relatively(client_as):
    html = client_as("admin").get("/admin/dashboard").text
    assert re.search(r'href="users"', html)


def test_anonymous_is_redirected_from_user_routes(client):
    for path in ("/admin/users", "/admin/users/new"):
        assert client.get(path, follow_redirects=False).status_code in (302, 303)
    assert client.post("/admin/users/new", data={}, follow_redirects=False).status_code in (302, 303)


def test_user_routes_require_a_csrf_token(client_as):
    admin = client_as("admin")
    uid = _user_id(admin, EDITOR)
    before = _emails(admin)
    for path, data in [
        ("/admin/users/new", {"email": "y@example.test", "password": "a-long-enough-pw", "role": "editor"}),
        (f"/admin/users/{uid}/role", {"role": "admin"}),
        (f"/admin/users/{uid}/deactivate", {}),
    ]:
        assert admin.post(path, data=data, follow_redirects=False).status_code == 403, path
    assert _emails(admin) == before
    row = _row(admin, EDITOR)
    assert "Editor" in row and "deactivated" not in row


def test_unknown_user_id_is_404(client_as):
    admin = client_as("admin")
    assert _post(admin, "/admin/users/9999/deactivate").status_code == 404


def test_huge_user_id_is_404(client_as):
    admin = client_as("admin")
    assert _post(admin, "/admin/users/99999999999999999999/deactivate").status_code == 404
