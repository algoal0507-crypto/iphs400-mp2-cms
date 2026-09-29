"""Page editing: create, read, update, delete.

Manager (admin) only — the Editor must be blocked in code, not just by hiding
the link, on every route here, including a hand-crafted POST. Home, Menu, and
Our Story are La Once Mil's starting content (see db.PAGE_SLUGS), not a limit:
per the MP2 rubric/manual, Pages support the same create/read/update/delete
operations as Posts.

Route order matters: /admin/pages/new must be declared before the
/admin/pages/{slug} routes, or FastAPI would match "new" as a slug.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, content, db, settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))


def _require_manager(request: Request):
    """(user, None) if the caller may manage pages, else (None, response)."""
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


@router.get("/admin/pages/new")
def page_new_form(request: Request):
    user, error = _require_manager(request)
    if error is not None:
        return error
    return auth.render_with_csrf(
        templates, request, "admin/page_new.html",
        {"title": "New page", "error": None,
         "values": {"slug": "", "title": "", "body_md": "", "status": "draft"}},
    )


@router.post("/admin/pages/new")
def page_new_submit(
    request: Request,
    slug: str = Form(...),
    title: str = Form(...),
    body_md: str = Form(""),
    status: str = Form("draft"),
    csrf_token: str | None = Form(None),
):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    if status not in ("draft", "published"):
        status = "draft"

    values = {"slug": slug, "title": title, "body_md": body_md, "status": status}

    if not db.slug_is_valid(slug):
        return auth.render_with_csrf(
            templates, request, "admin/page_new.html",
            {"title": "New page", "values": values,
             "error": "Slug must be lowercase letters, numbers, and hyphens only."},
            status_code=400,
        )

    created = db.create_page(
        slug, title=title,
        body_md=content.sanitize_markdown_source(body_md),
        status=status, author_id=user["id"],
    )
    if not created:
        return auth.render_with_csrf(
            templates, request, "admin/page_new.html",
            {"title": "New page", "values": values,
             "error": f'A page with the slug "{slug}" already exists.'},
            status_code=400,
        )
    return RedirectResponse(f"/admin/pages/{slug}", status_code=303)


@router.get("/admin/pages/{slug}")
def page_edit_form(request: Request, slug: str):
    user, error = _require_manager(request)
    if error is not None:
        return error
    page = db.get_page_by_slug(slug)
    if page is None:
        return PlainTextResponse("Not found.", status_code=404)
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
    if db.get_page_by_slug(slug) is None:
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


@router.post("/admin/pages/{slug}/delete")
def page_delete(request: Request, slug: str, csrf_token: str | None = Form(None)):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if db.get_page_by_slug(slug) is None:
        return PlainTextResponse("Not found.", status_code=404)
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)

    db.delete_page(slug)
    return RedirectResponse("/admin/pages", status_code=303)
