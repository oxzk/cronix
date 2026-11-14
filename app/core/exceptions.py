"""应用异常层级: 稳定错误码 + HTTP 状态, 由 exception_handlers 统一渲染。"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    code: str = "app_error"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    code = "not_found"
    status_code = 404


class ValidationError(AppException):
    code = "validation_error"
    status_code = 422


class AuthenticationError(AppException):
    code = "authentication_error"
    status_code = 401


class ConflictError(AppException):
    code = "conflict_error"
    status_code = 409


class RuntimeInitializationError(AppException):
    code = "runtime_initialization_error"
    status_code = 500


class TooManyAttemptsError(AppException):
    code = "too_many_attempts"
    status_code = 429


class ServiceUnavailableError(AppException):
    code = "service_unavailable"
    status_code = 503
