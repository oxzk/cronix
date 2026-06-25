"""认证授权中间件。"""

from __future__ import annotations

import jwt
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from cronix.core.database import db
from cronix.core.security import Security
from cronix.repositories import UserRepository
from cronix.schemas import APIResponse


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 认证中间件。

    仅对 ``/api`` 前缀的请求做令牌校验，校验通过后将用户写入
    ``request.state.user`` 供下游路由使用。
    """

    # 无需认证的 API 路径。
    EXCLUDED_PATHS = {"/api/auth/login"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """对受保护请求执行令牌校验。"""
        # 放行 CORS 预检请求。
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # 仅对 /api 前缀的业务接口进行认证。
        if not path.startswith("/api") or path in self.EXCLUDED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return self._unauthorized("Missing or invalid authorization header")

        token = auth_header[len("Bearer ") :].strip()
        try:
            payload = Security.decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return self._unauthorized("Token has expired")
        except jwt.InvalidTokenError:
            return self._unauthorized("Could not validate credentials")

        username = payload.get("sub")
        if not username:
            return self._unauthorized("Could not validate credentials")

        # 校验用户仍然存在，防止令牌签发后账户被删除。
        user = None
        async for session in db.get_session():
            repo = UserRepository(session)
            user = await repo.get_by_username(username)

        if user is None:
            return self._unauthorized("User no longer exists")

        request.state.user = user
        return await call_next(request)

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        """构建统一格式的 401 响应。"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=jsonable_encoder(
                APIResponse(code=status.HTTP_401_UNAUTHORIZED, message=message)
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
