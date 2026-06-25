"""FastAPI 主应用程序。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cronix.core.requester import requester
from cronix.core.config import settings
from cronix.core.constants import __VERSION__
from cronix.core.database import db
from cronix.core.exceptions import ExceptionHandlerRegistry
from cronix.middleware import AuthMiddleware
from cronix.routes import (
    auth_router,
    executions_router,
    settings_router,
    stats_router,
    tasks_router,
)
from cronix.schemas import APIResponse
from cronix.services.auth import initialize_admin_user
from cronix.services.scheduler import scheduler_service
from cronix.utils.logger import logger

PUBLIC_DIR = Path(__file__).resolve().parents[3] / "public"
INDEX_HTML = PUBLIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动阶段初始化数据库和后台服务。
    logger.info("Application starting...")
    await db.connect()

    # 确保存在可登录的管理员账户。
    await initialize_admin_user()

    try:
        await scheduler_service.start()
        logger.info("Scheduler started")
        yield
    finally:
        # 关闭阶段停止后台任务并释放连接。
        logger.info("Application shutting down...")
        await scheduler_service.stop()
        await requester.close()
        await db.close()
        logger.info("Application stopped")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=None,
    redirect_slashes=False,
    debug=settings.app_debug,
    version=__VERSION__,
)

# 注册全局异常处理器。
exception_registry = ExceptionHandlerRegistry(app)
exception_registry.register()

# 认证中间件，对 /api 业务接口做 JWT 授权校验。
# 先于 CORS 注册，保证 CORS 作为最外层处理预检请求。
app.add_middleware(AuthMiddleware)

# CORS 中间件最后注册，作为最外层处理预检请求。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


for router in [
    auth_router,
    tasks_router,
    settings_router,
    executions_router,
    stats_router,
]:
    app.include_router(router, prefix="/api")


@app.get("/health", response_model=APIResponse[dict[str, str]])
def health() -> APIResponse[dict[str, str]]:
    """健康检查。"""
    return APIResponse.ok(
        {
            "name": settings.app_name,
            "version": __VERSION__,
            "status": "running",
        }
    )


if INDEX_HTML.exists():
    app.mount("/assets", StaticFiles(directory=PUBLIC_DIR / "assets"), name="assets")


if INDEX_HTML.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        """返回前端单页应用入口。"""
        requested_file = PUBLIC_DIR / full_path
        if full_path and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(INDEX_HTML)
