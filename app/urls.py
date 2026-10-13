"""Relative URLs for admin pages, which are served at nested routes.

The exported public site is flat, so fixed names like "style.css" work there.
Admin routes nest (/login, /admin/pages/home), so a link is computed from the
request's own path, the way a browser will resolve it: relative to the
*directory* of the current URL.
"""
from __future__ import annotations

import posixpath

from jinja2 import pass_context
from starlette.templating import Jinja2Templates


def relative_url(from_path: str, to_path: str) -> str:
    """The relative reference that, resolved from `from_path`, yields `to_path`."""
    base = from_path if from_path.endswith("/") else posixpath.dirname(from_path)
    return posixpath.relpath(to_path, base or "/")


@pass_context
def _rel(context, to_path: str) -> str:
    return relative_url(context["request"].url.path, to_path)


def _shell_context(request) -> dict:
    """What the shared admin header needs on every screen: who is signed in."""
    from app import auth, settings  # lazy: app.auth imports app.db at load time

    user = auth.current_user(request)
    # Only what the header shows: never hand templates the whole user row.
    return {
        "site_title": settings.SITE_TITLE,
        "nav_user": {"email": user["email"]} if user is not None else None,
        "nav_is_manager": user is not None and user["role"] == "admin",
    }


def install(templates: Jinja2Templates) -> Jinja2Templates:
    """Expose `rel('/admin/dashboard')` and the admin header data to templates."""
    templates.env.globals["rel"] = _rel
    templates.context_processors.append(_shell_context)
    return templates
