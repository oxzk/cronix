from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import uvicorn
from src.config import settings
from src.databases import db
from src.routes import auth_router, tasks_router, settings_router
from src.services.scheduler import scheduler
from src.services.auth import initialize_admin_user
from src.services.notifiers import initialize_notifications
from src.utils import logger
from src.middleware import AuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting...")
    await db.connect()

    # Initialize admin user
    await initialize_admin_user()

    # Initialize notification configurations
    await initialize_notifications()

    asyncio.create_task(scheduler.start())
    logger.info("Scheduler started")
    yield
    # Shutdown
    logger.info("Application shutting down...")
    await scheduler.stop()
    await db.disconnect()
    logger.info("Application stopped")


app = FastAPI(
    title=settings.app_name, lifespan=lifespan, docs_url=None, openapi_url=None
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(
        f"Global exception: {type(exc).__name__}: {str(exc)} - Path: {request.url.path}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.app_debug else "An unexpected error occurred",
        },
    )


app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(settings_router)


@app.get("/")
def root() -> dict:
    from src import __version__

    return {
        "name": settings.app_name,
        "version": __version__,
        "status": "running",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_debug,
    )
