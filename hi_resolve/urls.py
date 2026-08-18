from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from hi_resolve.apps.auth.views import router as auth_router
from hi_resolve.apps.chats.views import router as chats_router
from hi_resolve.apps.generate.views import router as generate_router
from hi_resolve.settings import settings


def include_urls(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(chats_router)
    app.include_router(generate_router)
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    @app.get("/")
    async def index():
        return FileResponse(settings.static_dir / "index.html")

    @app.get("/health")
    async def health():
        return {"status": "ok"}
