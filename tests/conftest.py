"""Shared test fixtures.

`client` gives you the app. `client_as(role)` gives you a client that is logged
in as a seeded user of that role — it works as soon as your login route exists,
so access-control tests stay one line:

    def test_editor_cannot_manage_users(client_as):
        assert client_as("editor").get("/admin/users").status_code in (302, 403)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import db, settings
from app.main import create_app

# Matches scripts/seed_demo.py. Passwords come from the environment there; in
# tests they are fixed and meaningless.
DEMO_USERS = {
    "admin": {"email": "admin@example.test", "password": "test-admin-pw", "role": "admin"},
    "editor": {"email": "editor@example.test", "password": "test-editor-pw", "role": "editor"},
}


@pytest.fixture(autouse=True)
def _seeded_database(tmp_path, monkeypatch):
    """Every test gets its own SQLite file, seeded with the two demo users."""
    monkeypatch.setattr(settings, "DATABASE_PATH", tmp_path / "test.db")
    db.init_db()
    for user in DEMO_USERS.values():
        db.create_user(user["email"], user["password"], user["role"])


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def deactivate_user():
    """Return a factory: deactivate_user("editor@example.test")."""

    def _deactivate(email: str) -> None:
        db.set_active(email, active=False)

    return _deactivate


@pytest.fixture
def client_as():
    """Return a factory: client_as("editor") -> a logged-in TestClient."""

    def _login(role: str) -> TestClient:
        user = DEMO_USERS[role]
        c = TestClient(create_app())
        login_page = c.get("/login")
        if login_page.status_code == 404:
            pytest.skip("No /login route yet — build the login ticket first.")
        response = c.post("/login", data={
            "email": user["email"],
            "password": user["password"],
            "csrf_token": login_page.cookies.get("csrf_token"),
        }, follow_redirects=False)
        assert response.status_code in (200, 302, 303), (
            f"Login as {role} failed with {response.status_code}")
        return c

    return _login
