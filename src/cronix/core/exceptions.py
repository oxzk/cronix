"""全局异常定义与处理注册模块。"""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException

from cronix.core.config import settings
from cronix.schemas import APIResponse
from cronix.utils.logger import logger


class AppError(Exception):
    """应用业务异常。"""

    def __init__(
        self,
        message: str,
        code: int | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any | None = None,
    ) -> None:
        """初始化应用业务异常。"""
        self.message = message
        self.code = code or status_code
        self.status_code = status_code
        self.data = data
        super().__init__(message)


class NotFoundError(AppError):
    """资源不存在异常。"""

    def __init__(self, message: str = "Resource not found") -> None:
        """初始化资源不存在异常。"""
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ExceptionHandlerRegistry:
    """FastAPI 全局异常处理器注册器。"""

    def __init__(self, app: FastAPI) -> None:
        """初始化异常处理器注册器。"""
        self._app = app

    def register(self) -> None:
        """注册全局异常处理器。"""

        @self._app.exception_handler(AppError)
        async def handle_app_error(_: Request, exception: AppError) -> JSONResponse:
            """处理应用业务异常。"""
            return JSONResponse(
                status_code=exception.status_code,
                content=jsonable_encoder(
                    APIResponse(
                        code=exception.code,
                        message=exception.message,
                        data=exception.data,
                    )
                ),
            )

        @self._app.exception_handler(RequestValidationError)
        async def handle_validation_error(
            _: Request,
            exception: RequestValidationError,
        ) -> JSONResponse:
            """处理请求参数校验异常。"""
            message = self._format_validation_message(exception)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder(
                    APIResponse(
                        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=message,
                        data={"errors": exception.errors()},
                    )
                ),
            )

        @self._app.exception_handler(HTTPException)
        async def handle_http_exception(
            request: Request,
            exception: HTTPException,
        ) -> JSONResponse:
            """处理 HTTP 异常。"""
            message, data = self._normalize_http_exception(request, exception)
            return JSONResponse(
                status_code=exception.status_code,
                content=jsonable_encoder(
                    APIResponse(
                        code=exception.status_code,
                        message=message,
                        data=data,
                    )
                ),
                headers=exception.headers,
            )

        @self._app.exception_handler(Exception)
        async def handle_exception(_: Request, exception: Exception) -> JSONResponse:
            """处理未捕获异常。"""
            trace_id = uuid.uuid4().hex
            logger.exception("Unhandled exception trace_id=%s", trace_id)
            message = f"System error: {exception}" if settings.app_debug else "Internal server error"
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder(
                    APIResponse(
                        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message=message,
                        data={"trace_id": trace_id},
                    )
                ),
            )

    def _normalize_http_exception(
        self,
        request: Request,
        exception: HTTPException,
    ) -> tuple[str, Any | None]:
        """规范化 HTTP 异常消息与附加数据。"""
        if isinstance(exception.detail, str):
            message = exception.detail or self._get_http_status_phrase(exception.status_code)
            return message, request.url.path

        message = self._get_http_status_phrase(exception.status_code)
        return message, {"detail": exception.detail, "path": request.url.path}

    def _get_http_status_phrase(self, status_code: int) -> str:
        """获取 HTTP 状态短语。"""
        try:
            return HTTPStatus(status_code).phrase
        except ValueError:
            return "HTTP Error"

    def _format_validation_message(self, exception: RequestValidationError) -> str:
        """格式化请求参数校验错误消息。"""
        errors = exception.errors()
        if not errors:
            return "Request validation failed"

        details = [self._format_validation_error(error) for error in errors[:3]]
        suffix = "; ".join(detail for detail in details if detail)
        if len(errors) > 3:
            suffix = f"{suffix}; and {len(errors) - 3} more errors"
        return f"Request validation failed: {suffix}" if suffix else "Request validation failed"

    def _format_validation_error(self, error: dict[str, Any]) -> str:
        """格式化单个请求参数校验错误。"""
        loc = error.get("loc")
        source, field = self._parse_validation_location(
            loc if isinstance(loc, (tuple, list)) else (),
        )
        error_type = str(error.get("type", ""))
        message = str(error.get("msg", ""))
        if error_type == "missing" or message == "Field required":
            return f"Missing {source}{field}" if field else f"Missing {source}"
        if field:
            return f"{source}{field}: {message}"
        return message or "Invalid parameter"

    def _parse_validation_location(
        self,
        loc: tuple[object, ...] | list[object],
    ) -> tuple[str, str]:
        """解析请求参数校验错误位置。"""
        source_map = {
            "query": "query parameter ",
            "path": "path parameter ",
            "body": "body field ",
            "header": "header ",
            "cookie": "cookie ",
        }
        parts = list(loc)
        source_key = str(parts[0]) if parts else ""
        source = source_map.get(source_key, "parameter ")
        field_parts = [str(part) for part in parts[1:]]
        return source, ".".join(field_parts)
