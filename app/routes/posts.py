"""News posts: create, read, update, publish, delete.

Editor and Manager both reach these routes, but what they may do differs and
is enforced here in code, never by hiding links. A post's status is never read
from a form field: new and edited posts keep their current status, and only
the Manager-only publish/unpublish routes change it, so a hand-crafted POST
cannot publish anything.

Route order matters: /admin/posts/new must be declared before the
/admin/posts/{slug} routes, or FastAPI would match "new" as a slug.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, content, db, settings, urls

router = APIRouter()
templates = urls.install(Jinja2Templates(directory=str(settings.TEMPLATES)))


def _require_staff(request: Request):
    """(user, None) for any logged-in Editor or Manager, else (None, response)."""
    return auth.require_role(request)


def _require_manager(request: Request):
    """(user, None) if the caller is the Manager, else (None, response)."""
    return auth.require_role(request, "admin")


def _editor_locked_out(user, post) -> bool:
    """An Editor may only touch drafts; a published post is Manager-only."""
    return user["role"] != "admin" and post["status"] == "published"


@router.get("/admin/posts")
def posts_list(request: Request):
    user, error = _require_staff(request)
    if error is not None:
        return error
    return auth.render_with_csrf(
        templates, request, "admin/posts_list.html",
        {"title": "News", "posts": db.list_posts(), "is_manager": user["role"] == "admin"},
    )


@router.get("/admin/posts/new")
def post_new_form(request: Request):
    user, error = _require_staff(request)
    if error is not None:
        return error
    return auth.render_with_csrf(
        templates, request, "admin/post_new.html",
        {"title": "New News post", "error": None,
         "values": {"slug": "", "title": "", "body_md": ""}},
    )


@router.post("/admin/posts/new")
def post_new_submit(
    request: Request,
    slug: str = Form(...),
    title: str = Form(...),
    body_md: str = Form(""),
    csrf_token: str | None = Form(None),
):
    user, error = _require_staff(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)

    values = {"slug": slug, "title": title, "body_md": body_md}
    if not db.slug_is_valid(slug):
        return auth.render_with_csrf(
            templates, request, "admin/post_new.html",
            {"title": "New News post", "values": values,
             "error": "Slug must be lowercase letters, numbers, and hyphens only "
                      '(and cannot be "new" or "index").'},
            status_code=400,
        )
    if not title.strip():
        return auth.render_with_csrf(
            templates, request, "admin/post_new.html",
            {"title": "New News post", "values": values, "error": "A title is required."},
            status_code=400,
        )
    created = db.create_post(
        slug, title=title.strip(),
        body_md=content.sanitize_markdown_source(body_md),
        author_id=user["id"],
    )
    if not created:
        return auth.render_with_csrf(
            templates, request, "admin/post_new.html",
            {"title": "New News post", "values": values,
             "error": f'A News post with the slug "{slug}" already exists.'},
            status_code=400,
        )
    return RedirectResponse(f"/admin/posts/{slug}", status_code=303)


@router.get("/admin/posts/{slug}")
def post_edit_form(request: Request, slug: str):
    user, error = _require_staff(request)
    if error is not None:
        return error
    post = db.get_post_by_slug(slug)
    if post is None:
        return PlainTextResponse("Not found.", status_code=404)
    if _editor_locked_out(user, post):
        return PlainTextResponse("Forbidden.", status_code=403)
    return auth.render_with_csrf(
        templates, request, "admin/post_edit.html",
        {"title": f"Edit {post['title']}", "post": post, "is_manager": user["role"] == "admin",
         "preview_html": content.render_markdown(post["body_md"]), "saved": False},
    )


@router.post("/admin/posts/{slug}")
def post_edit_submit(
    request: Request,
    slug: str,
    title: str = Form(...),
    body_md: str = Form(""),
    csrf_token: str | None = Form(None),
):
    user, error = _require_staff(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    existing = db.get_post_by_slug(slug)
    if existing is None:
        return PlainTextResponse("Not found.", status_code=404)
    if _editor_locked_out(user, existing):
        return PlainTextResponse("Forbidden.", status_code=403)

    if not title.strip():
        return auth.render_with_csrf(
            templates, request, "admin/post_edit.html",
            {"title": f"Edit {existing['title']}", "post": existing,
             "is_manager": user["role"] == "admin",
             "preview_html": content.render_markdown(existing["body_md"]), "saved": False,
             "error": "A title is required."},
            status_code=400,
        )

    db.update_post(
        slug, title=title.strip(),
        body_md=content.sanitize_markdown_source(body_md),
        author_id=user["id"],
    )
    post = db.get_post_by_slug(slug)
    return auth.render_with_csrf(
        templates, request, "admin/post_edit.html",
        {"title": f"Edit {post['title']}", "post": post, "is_manager": user["role"] == "admin",
         "preview_html": content.render_markdown(post["body_md"]), "saved": True},
    )


def _change_status(request: Request, slug: str, csrf_token: str | None, status: str):
    user, error = _require_manager(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    if db.get_post_by_slug(slug) is None:
        return PlainTextResponse("Not found.", status_code=404)
    db.set_post_status(slug, status)
    return RedirectResponse(f"/admin/posts/{slug}", status_code=303)


@router.post("/admin/posts/{slug}/publish")
def post_publish(request: Request, slug: str, csrf_token: str | None = Form(None)):
    return _change_status(request, slug, csrf_token, "published")


@router.post("/admin/posts/{slug}/unpublish")
def post_unpublish(request: Request, slug: str, csrf_token: str | None = Form(None)):
    return _change_status(request, slug, csrf_token, "draft")


@router.post("/admin/posts/{slug}/delete")
def post_delete(request: Request, slug: str, csrf_token: str | None = Form(None)):
    user, error = _require_staff(request)
    if error is not None:
        return error
    if not auth.csrf_is_valid(request, csrf_token):
        return PlainTextResponse("Invalid CSRF token.", status_code=403)
    post = db.get_post_by_slug(slug)
    if post is None:
        return PlainTextResponse("Not found.", status_code=404)
    if _editor_locked_out(user, post):
        return PlainTextResponse("Forbidden.", status_code=403)

    db.delete_post(slug)
    return RedirectResponse("/admin/posts", status_code=303)
