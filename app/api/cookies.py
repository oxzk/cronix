"""认证 Cookie 下发工具(login/refresh/TOTP/恢复共用)。"""

from __future__ import annotations

from typing import Any

from fastapi import Request, Response

from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE


def set_auth_cookies(
    request: Request, response: Response, tokens: dict[str, str], jwt_settings: Any
) -> None:
    """同时下发 HttpOnly Cookie(浏览器)与响应体令牌(API 客户端)。"""
    secure = request.url.scheme == "https"
    response.set_cookie(
        ACCESS_COOKIE,
        tokens["access_token"],
        max_age=jwt_settings.access_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens["refresh_token"],
        max_age=jwt_settings.refresh_expire_days * 86400,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
