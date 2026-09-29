"""Permanent-page editing: Home, Menu, Our Story.

Manager (admin) only, per CONTEXT.md's "Permanent pages" entry — the Editor
must be blocked in code, not just by hiding the link, on every route here,
including a hand-crafted POST.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, content, db, settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))


def _require_manager(request: Request):
    """(user, None) if the caller may edit permanent pages, else (None, response)."""
    user = auth.current_user(request)
    if user is None:
        return None, RedirectResponse("/login", status_code=303)
    if user["role"] != "admin":
        return None, PlainTextResponse("Forbidden.", status_code=403)
    return user, None


@router.get("/admin/pages")
def pages_list(request: Request):
    user, error = _require_manager(request)
    if error is not None:
        return error
    return auth.render_with_csrf(
        templates, request, "admin/pages_list.html",
        {"title": "Pages", "pages": db.list_pages()},
    )


@router.get("/admin/pages/{slug}")
def page_edit_form(request: Request, slug: str):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if slug not in db.PAGE_SLUGS:
        return PlainTextResponse("Not found.", status_code=404)
    page = db.get_page_by_slug(slug)
    return auth.render_with_csrf(
        templates, request, "admin/page_edit.html",
        {"title": f"Edit {page['title']}", "page": page,
         "preview_html": content.render_markdown(page["body_md"]), "saved": False},
    )


@router.post("/admin/pages/{slug}")
def page_edit_submit(
    request: Request,
    slug: str,
    title: str = Form(...),
    body_md: str = Form(""),
    status: str = Form("draft"),
    csrf_token: str | None = Form(None),
):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if slug not in db.PAGE_SLUGS:
        return PlainTextResponse("Not found.", status_code=404)
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    if status not in ("draft", "published"):
        status = "draft"

    db.update_page(
        slug,
        title=title,
        body_md=content.sanitize_markdown_source(body_md),
        status=status,
        author_id=user["id"],
    )

    page = db.get_page_by_slug(slug)
    return auth.render_with_csrf(
        templates, request, "admin/page_edit.html",
        {"title": f"Edit {page['title']}", "page": page,
         "preview_html": content.render_markdown(page["body_md"]), "saved": True},
    )
