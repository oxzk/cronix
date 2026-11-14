"""异常渲染: 统一错误信封。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions import AppException
from app.core.monitoring import CONNECTION_URL_PATTERN, REDACTED


def _error_body(code: str, message: str, details: Any = None) -> dict:  # type: ignore[type-arg]
    return {"success": False, "error": {"code": code, "message": message, "details": details}}


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = CONNECTION_URL_PATTERN.sub(REDACTED, str(exc.errors()[:3]))
        return JSONResponse(
            status_code=422,
            content=_error_body("validation_error", "请求参数不合法", details),
        )

    @application.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常")
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", "服务器内部错误", None),
        )
