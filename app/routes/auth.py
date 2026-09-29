"""Login, logout, and the one protected landing route T01 needs.

Later tickets add real admin routes; they should follow the same pattern —
`auth.read_session` to find the user, redirect to /login if there isn't one.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, db, settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))


_current_user = auth.current_user


def _render_with_csrf(request: Request, template_name: str, context: dict, *, status_code: int = 200):
    return auth.render_with_csrf(templates, request, template_name, context, status_code=status_code)


@router.get("/login")
def login_form(request: Request):
    if _current_user(request) is not None:
        return RedirectResponse("/admin/dashboard", status_code=303)
    return _render_with_csrf(request, "admin/login.html", {"title": "Log in", "error": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str | None = Form(None),
):
    if not auth.csrf_is_valid(request, csrf_token):
        return _rejected(request, "Your session expired. Please try again.", status_code=403)

    user = db.get_user_by_email(email)
    if user is None or not user["active"] or not auth.verify_password(password, user["password_hash"]):
        return _rejected(request, "Invalid email or password.", status_code=401)

    response = RedirectResponse("/admin/dashboard", status_code=303)
    auth.set_session_cookie(response, user["id"])
    return response


def _rejected(request: Request, message: str, *, status_code: int):
    return _render_with_csrf(
        request, "admin/login.html", {"title": "Log in", "error": message}, status_code=status_code
    )


@router.post("/logout")
def logout(request: Request, csrf_token: str | None = Form(None)):
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    response = RedirectResponse("/login", status_code=303)
    auth.clear_session_cookie(response)
    return response


@router.get("/admin/dashboard")
def admin_dashboard(request: Request):
    user = _current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    role_label = "Manager" if user["role"] == "admin" else "Editor"
    return _render_with_csrf(
        request, "admin/dashboard.html",
        {"title": "Dashboard", "role_label": role_label, "email": user["email"]},
    )
