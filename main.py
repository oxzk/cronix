from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import os
from pathlib import Path
from src.config import settings
from src.databases import db
from src.routes import (
    auth_router,
    tasks_router,
    settings_router,
    executions_router,
    scripts_router,
    stats_router,
    dependencies_router,
)
from src.services.scheduler import scheduler
from src.services.auth import initialize_admin_user
from src.services.notifiers import initialize_notifications
from src.utils import logger, error_response, success_response
from src.middleware import AuthMiddleware
from src import __version__


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
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=None,
    # openapi_url=None,
    redirect_slashes=False,
    debug=settings.app_debug,
    version=__version__,
)

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)


# Global exception handler for all exceptions
@app.exception_handler(StarletteHTTPException)
@app.exception_handler(RequestValidationError)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Unified exception handler for all exceptions"""

    # Handle HTTP exceptions
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=exc.detail,
                code=exc.status_code,
            ),
        )

    # Handle validation errors
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Validation error", code=422, data={"errors": exc.errors()}
            ),
        )

    # Handle all other exceptions
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)} - Path: {request.url.path}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="Internal server error",
            code=500,
            data={
                "error": (
                    str(exc) if settings.app_debug else "An unexpected error occurred"
                )
            },
        ),
    )


for router in [
    auth_router,
    tasks_router,
    settings_router,
    executions_router,
    scripts_router,
    stats_router,
    dependencies_router,
]:
    app.include_router(router, prefix="/api")


@app.get("/robots.txt")
async def robots_file():
    return PlainTextResponse("User-agent: *\nDisallow: /")


@app.get("/info")
async def info(request: Request):
    headers = {key: value for key, value in request.headers.items()}
    client_host = request.client.host if request.client else None
    client_port = request.client.port if request.client else None

    return success_response(
        data={
            "client": {
                "host": client_host,
                "port": client_port,
            },
            "url": str(request.url),
            "base_url": str(request.base_url),
            "headers": headers,
        }
    )


@app.get("/health")
def health() -> dict:

    return success_response(
        data={
            "name": settings.app_name,
            "version": __version__,
            "status": "running",
        }
    )


# app.mount("/assets", StaticFiles(directory="public/assets"), name="assets")


# @app.get("/")
# def index():
#     return FileResponse("public/index.html")


# @app.get("/{path:path}")
# def spa(path: str):
#     return FileResponse("public/index.html")
