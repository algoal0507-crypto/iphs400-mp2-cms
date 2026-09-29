"""T01: login and sessions.

Covers login success (both seeded roles), a wrong password, logout-then-
blocked, and a deactivated user being refused — plus the CSRF and password
storage protections the security checklist requires now, not deferred to the
audit ticket.
"""
from __future__ import annotations

from tests.conftest import DEMO_USERS


def _csrf_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def test_login_success_reaches_themed_landing(client):
    for role, user in DEMO_USERS.items():
        csrf = _csrf_login_page(client)
        response = client.post(
            "/login",
            data={"email": user["email"], "password": user["password"], "csrf_token": csrf},
            follow_redirects=False,
        )
        assert response.status_code == 303
        dashboard = client.get(response.headers["location"])
        assert dashboard.status_code == 200
        assert role in dashboard.text.lower() or user["email"] in dashboard.text
        client.post("/logout", data={"csrf_token": client.cookies["csrf_token"]})


def test_wrong_password_is_refused_with_no_session(client):
    csrf = _csrf_login_page(client)
    response = client.post(
        "/login",
        data={
            "email": DEMO_USERS["admin"]["email"],
            "password": "not-the-password",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "session" not in client.cookies
    assert "invalid" in response.text.lower()


def test_logout_then_admin_route_is_blocked(client):
    csrf = _csrf_login_page(client)
    login = client.post(
        "/login",
        data={
            "email": DEMO_USERS["admin"]["email"],
            "password": DEMO_USERS["admin"]["password"],
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert login.status_code == 303

    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200

    logout_csrf = client.cookies["csrf_token"]
    logout = client.post("/logout", data={"csrf_token": logout_csrf}, follow_redirects=False)
    assert logout.status_code == 303

    blocked = client.get("/admin/dashboard", follow_redirects=False)
    assert blocked.status_code == 303
    assert blocked.headers["location"].endswith("/login")


def test_deactivated_user_login_is_refused(client, deactivate_user):
    deactivate_user(DEMO_USERS["editor"]["email"])
    csrf = _csrf_login_page(client)
    response = client.post(
        "/login",
        data={
            "email": DEMO_USERS["editor"]["email"],
            "password": DEMO_USERS["editor"]["password"],
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "session" not in client.cookies


def test_login_without_csrf_token_is_rejected(client):
    _csrf_login_page(client)
    response = client.post(
        "/login",
        data={
            "email": DEMO_USERS["admin"]["email"],
            "password": DEMO_USERS["admin"]["password"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 403
    assert "session" not in client.cookies


def test_passwords_are_stored_as_argon2_hashes_only():
    from app import db

    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (DEMO_USERS["admin"]["email"],),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["password_hash"] != DEMO_USERS["admin"]["password"]
    assert row["password_hash"].startswith("$argon2")
