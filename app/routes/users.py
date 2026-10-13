"""User management: create, change role, deactivate. Manager (admin) only.

The Editor is blocked in code on every route here, including a hand-crafted
POST. A user is deactivated, never deleted, so their authorship of News and
Pages is kept. Deactivation and role changes apply on the user's very next
request, because auth.current_user re-reads the user row every time.

A Manager cannot change their own role or deactivate themselves, so the
console can't be left with no way in.

Route order matters: /admin/users/new before /admin/users/{user_id}/...
"""
from __future__ import annotations

import re
import sqlite3

from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, db, settings, urls

router = APIRouter()
templates = urls.install(Jinja2Templates(directory=str(settings.TEMPLATES)))

ROLES = ("admin", "editor")
MIN_PASSWORD_LENGTH = 12
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _require_manager(request: Request):
    return auth.require_role(request, "admin")


def _render_list(request: Request, user, *, error: str | None = None, status_code: int = 200):
    return auth.render_with_csrf(
        templates, request, "admin/users_list.html",
        {"title": "Users", "users": db.list_users(), "me": user, "roles": ROLES, "error": error},
        status_code=status_code,
    )


def _render_new(request: Request, values: dict, error: str | None, status_code: int = 200):
    return auth.render_with_csrf(
        templates, request, "admin/user_new.html",
        {"title": "New user", "values": values, "roles": ROLES, "error": error},
        status_code=status_code,
    )


@router.get("/admin/users")
def users_list(request: Request):
    user, error = _require_manager(request)
    if error is not None:
        return error
    return _render_list(request, user)


@router.get("/admin/users/new")
def user_new_form(request: Request):
    user, error = _require_manager(request)
    if error is not None:
        return error
    return _render_new(request, {"email": "", "role": "editor"}, None)


@router.post("/admin/users/new")
def user_new_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    role: str = Form(""),
    csrf_token: str | None = Form(None),
):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)

    email = email.strip().lower()
    values = {"email": email, "role": role}
    problem = None
    if len(email) > auth.MAX_EMAIL_LENGTH or not _EMAIL_RE.fullmatch(email):
        problem = "Enter a valid email address."
    elif len(password) < MIN_PASSWORD_LENGTH:
        problem = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    elif len(password) > auth.MAX_PASSWORD_LENGTH:
        problem = f"Password must be at most {auth.MAX_PASSWORD_LENGTH} characters."
    elif role not in ROLES:
        problem = "Choose a role."
    elif db.get_user_by_email(email) is not None:
        problem = f"A user with the email {email} already exists."
    if problem:
        return _render_new(request, values, problem, status_code=400)

    try:
        db.create_user(email, password, role)
    except sqlite3.IntegrityError:  # lost a race with another submit of the same email
        return _render_new(request, values, f"A user with the email {email} already exists.",
                           status_code=400)
    return RedirectResponse("/admin/users", status_code=303)


def _target(user_id: int):
    if not 0 < user_id < 2**63:  # beyond SQLite's INTEGER range
        return None
    return db.get_user_by_id(user_id)


@router.post("/admin/users/{user_id}/role")
def user_change_role(
    request: Request, user_id: int,
    role: str = Form(""), csrf_token: str | None = Form(None),
):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    target = _target(user_id)
    if target is None:
        return PlainTextResponse("Not found.", status_code=404)
    if role not in ROLES:
        return _render_list(request, user, error="Choose a valid role.", status_code=400)
    if target["id"] == user["id"]:
        return _render_list(request, user, error="You cannot change your own role.", status_code=400)
    db.set_role(user_id, role)
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/deactivate")
def user_deactivate(request: Request, user_id: int, csrf_token: str | None = Form(None)):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    target = _target(user_id)
    if target is None:
        return PlainTextResponse("Not found.", status_code=404)
    if target["id"] == user["id"]:
        return _render_list(request, user, error="You cannot deactivate your own account.",
                            status_code=400)
    db.set_active_by_id(user_id, active=False)
    return RedirectResponse("/admin/users", status_code=303)
