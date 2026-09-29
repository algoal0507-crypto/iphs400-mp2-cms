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


def install(templates: Jinja2Templates) -> Jinja2Templates:
    """Expose `rel('/admin/dashboard')` to templates rendered with a request."""
    templates.env.globals["rel"] = _rel
    return templates
