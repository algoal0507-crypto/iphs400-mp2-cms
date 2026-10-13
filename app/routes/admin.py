"""Dashboard, filterable content list, and the Markdown preview endpoint.

The Editor sees the same screens scoped to what they can act on: News only,
enforced here in code rather than by hiding rows in the template.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from app import auth, content, db, settings, urls

router = APIRouter()
templates = urls.install(Jinja2Templates(directory=str(settings.TEMPLATES)))

TYPES = ("news", "pages")
STATUSES = ("draft", "published")
MAX_PREVIEW_CHARS = 200_000


def _is_manager(user) -> bool:
    return user["role"] == "admin"


@router.get("/admin/dashboard")
def admin_dashboard(request: Request):
    user, error = auth.require_role(request)
    if error is not None:
        return error
    posts = db.list_posts()
    context = {
        "title": "Dashboard",
        "role_label": "Manager" if _is_manager(user) else "Editor",
        "email": user["email"],
        "news_counts": {s: sum(1 for p in posts if p["status"] == s) for s in STATUSES},
        "pages": db.list_pages() if _is_manager(user) else None,
    }
    return auth.render_with_csrf(templates, request, "admin/dashboard.html", context)


@router.get("/admin/content")
def content_list(request: Request, kind: str = Query("", alias="type"), status: str = ""):
    user, error = auth.require_role(request)
    if error is not None:
        return error
    kind = kind if kind in TYPES else ""
    status = status if status in STATUSES else ""
    if not _is_manager(user):
        kind = "news"  # Editors have no Page rows, whatever the query says.

    rows = []
    if kind in ("", "news"):
        rows += [{"kind": "post", "slug": p["slug"], "title": p["title"], "status": p["status"],
                  "href": f"/admin/posts/{p['slug']}"} for p in db.list_posts()]
    if kind in ("", "pages"):
        rows += [{"kind": "page", "slug": p["slug"], "title": p["title"], "status": p["status"],
                  "href": f"/admin/pages/{p['slug']}"} for p in db.list_pages()]
    if status:
        rows = [r for r in rows if r["status"] == status]
    # Editors can open drafts only; published posts are Manager-only (see posts.py).
    for r in rows:
        r["can_open"] = _is_manager(user) or r["status"] == "draft"

    return auth.render_with_csrf(
        templates, request, "admin/content_list.html",
        {"title": "Content", "rows": rows, "type": kind, "status": status,
         "is_manager": _is_manager(user)},
    )


@router.post("/admin/preview")
def preview(request: Request, body_md: str = Form(""), csrf_token: str | None = Form(None)):
    user, error = auth.require_role(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    if len(body_md) > MAX_PREVIEW_CHARS:
        return PlainTextResponse("Too long to preview.", status_code=413)
    return HTMLResponse(content.render_markdown(content.sanitize_markdown_source(body_md)))
