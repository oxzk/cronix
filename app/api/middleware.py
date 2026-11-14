"""中间件: JWT 鉴权(纯 ASGI) + RequestID。"""

from __future__ import annotations

import json
import uuid
from typing import Any

from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE
from app.core.exceptions import AppException, AuthenticationError, ServiceUnavailableError

PUBLIC_PATHS = {"/api/v1/health", "/api/v1/auth/login", "/api/v1/auth/logout"}
REFRESH_PATH = "/api/v1/auth/refresh"


class JWTAuthorizationMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        # 仅 API 需要鉴权; SPA 页面与静态资源保持公开(生产由后端托管 dist)
        if path.startswith("/api/") and path not in PUBLIC_PATHS:
            # 维护模式先于鉴权判断, 避免请求阻塞在恢复事务的锁上
            container = scope["app"].state.container
            runtime_state = getattr(container, "runtime_state", None)
            if runtime_state is not None and runtime_state.maintenance:
                await self._send_error(
                    send, ServiceUnavailableError("系统维护中(数据恢复进行中), 请稍后重试")
                )
                return
            try:
                principal = await self._authenticate(scope, path)
            except AppException as exc:
                await self._send_error(send, exc)
                return
            scope.setdefault("state", {})["user"] = principal
        await self.app(scope, receive, send)

    async def _authenticate(self, scope: Scope, path: str) -> Any:
        container = scope["app"].state.container
        purpose = "refresh" if path == REFRESH_PATH else "access"
        header = self._header(scope)
        if header.startswith("Bearer "):
            token = header[len("Bearer "):].strip()
        else:
            cookie_name = REFRESH_COOKIE if purpose == "refresh" else ACCESS_COOKIE
            token = self._cookie(scope, cookie_name)
        if not token:
            raise AuthenticationError("缺少访问令牌或登录已过期")
        return await container.auth.authenticate(token, purpose)

    @staticmethod
    def _header(scope: Scope) -> str:
        for name, value in scope["headers"]:
            if name == b"authorization":
                return value.decode("latin-1")
        return ""

    @staticmethod
    def _cookie(scope: Scope, cookie_name: str) -> str:
        for name, value in scope["headers"]:
            if name == b"cookie":
                for pair in value.decode("latin-1").split(";"):
                    key, separator, cookie_value = pair.strip().partition("=")
                    if separator and key == cookie_name:
                        return cookie_value
        return ""

    async def _send_error(self, send: Send, exc: AppException) -> None:
        body = json.dumps(
            {
                "success": False,
                "error": {"code": exc.code, "message": exc.message, "details": exc.details},
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode("latin-1")),
        ]
        await send({"type": "http.response.start", "status": exc.status_code, "headers": headers})
        await send({"type": "http.response.body", "body": body})


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        with logger.contextualize(request_id=request_id):
            await self.app(scope, receive, send_with_request_id)


class LazyCORSMiddleware:
    """首次请求时从容器读取 CORS 配置构建 CORSMiddleware。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._inner: CORSMiddleware | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if self._inner is None:
            origins = scope["app"].state.container.settings.cors_allow_origins
            self._inner = CORSMiddleware(
                self.app,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        await self._inner(scope, receive, send)
