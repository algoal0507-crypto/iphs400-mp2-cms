"""The FastAPI application.

T00 (already done): the admin console answers at /admin and the public site
answers at /. That is the whole skeleton — it exists so you can prove the stack
runs before you build anything on it.

Add your routes in their own modules (app/routes/posts.py and so on) and include
them here. Keep this file small.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from app import publish, settings, urls
from app.auth import require_role

templates = urls.install(Jinja2Templates(directory=str(settings.TEMPLATES)))


def create_app() -> FastAPI:
    # No generated API docs: they would list every admin route to anyone who asks.
    app = FastAPI(title="IPHS 400 MP2 CMS", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def admin_response_headers(request: Request, call_next):
        """Admin and login pages: not framed, not cached, not sniffed."""
        response = await call_next(request)
        path = request.url.path
        if path == "/admin" or path.startswith("/admin/") or path.rstrip("/") in ("/login", "/logout"):
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            if path not in ("/admin/style.css", "/admin/preview.js"):  # the two asset files may be cached
                response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/admin")
    def admin_home(request: Request):
        _, error = require_role(request)
        if error is not None:
            return error
        return templates.TemplateResponse(
            request, "admin/hello.html", {"title": "Admin"}
        )

    @app.get("/admin/style.css")
    def admin_stylesheet():
        # Same stylesheet the exported site ships; admin pages link it relatively.
        return Response(publish.CSS, media_type="text/css")

    @app.get("/admin/preview.js")
    def admin_preview_script():
        return Response((settings.TEMPLATES / "admin" / "preview.js").read_text(),
                        media_type="text/javascript")

    @app.get("/")
    def public_home(request: Request):
        return templates.TemplateResponse(
            request, "public/home.html",
            {"title": settings.SITE_TITLE, "items": []},
        )

    from app.routes import admin, auth, pages, posts, users
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(pages.router)
    app.include_router(posts.router)
    app.include_router(users.router)
    return app


app = create_app()
