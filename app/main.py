"""FastAPI 入口: uvicorn 目标 app.main:app。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import JWTAuthorizationMiddleware, LazyCORSMiddleware, RequestIDMiddleware
from app.api.v1.routes import router
from app.application.container import ApplicationContainer
from app.core.config import Settings, load_settings
from app.core.exceptions import NotFoundError

WEB_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


def mount_web(application: FastAPI) -> None:
    """托管 web/dist(SPA fallback); dist 不存在时为纯后端模式。"""
    index_file = WEB_DIST / "index.html"
    if not index_file.is_file():
        return
    assets = WEB_DIST / "assets"
    if assets.is_dir():
        application.mount("/assets", StaticFiles(directory=assets), name="assets")

    @application.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise NotFoundError("路径不存在")
        candidate = (WEB_DIST / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(WEB_DIST):
            return FileResponse(candidate)
        return FileResponse(index_file)


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        container = await ApplicationContainer.create(settings or load_settings())
        application.state.container = container
        try:
            yield
        finally:
            await container.shutdown()

    application = FastAPI(
        title="cronix",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        redirect_slashes=False,
    )
    # Starlette 中间件为 LIFO: CORS 最外层
    application.add_middleware(JWTAuthorizationMiddleware)
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(LazyCORSMiddleware)
    register_exception_handlers(application)
    application.include_router(router, prefix="/api/v1")
    mount_web(application)
    return application


app: Any = create_app()
