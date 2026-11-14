"""认证路由: login 公开; refresh/me/totp 需令牌; logout 清除 Cookie。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.cookies import set_auth_cookies
from app.api.dependencies import Container, CurrentUser
from app.api.schemas.auth import (
    LoginRequest,
    MeResponse,
    TokenResponse,
    TotpCodeRequest,
    TotpSetupResponse,
    TotpStatusResponse,
)
from app.api.schemas.response import SuccessResponse
from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    body: LoginRequest, container: Container, request: Request, response: Response
) -> Any:
    tokens = await container.auth.login(body.username.strip(), body.password, body.code)
    set_auth_cookies(request, response, tokens, container.settings.jwt)
    return SuccessResponse(data=TokenResponse(**tokens))


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh(
    container: Container, current_user: CurrentUser, request: Request, response: Response
) -> Any:
    tokens = await container.auth.issue(current_user.username)
    set_auth_cookies(request, response, tokens, container.settings.jwt)
    return SuccessResponse(data=TokenResponse(**tokens))


@router.post("/logout", response_model=SuccessResponse[bool])
async def logout(container: Container, response: Response) -> Any:
    # 提升令牌版本, 使已签发的 access/refresh 全部失效
    await container.auth.logout()
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
    return SuccessResponse(data=True)


@router.get("/me", response_model=SuccessResponse[MeResponse])
async def me(current_user: CurrentUser) -> Any:
    return SuccessResponse(data=MeResponse(username=current_user.username))


@router.get("/totp", response_model=SuccessResponse[TotpStatusResponse])
async def totp_status(container: Container) -> Any:
    data = await container.auth.totp_status()
    return SuccessResponse(data=TotpStatusResponse(**data))


@router.post("/totp/setup", response_model=SuccessResponse[TotpSetupResponse])
async def totp_setup(container: Container) -> Any:
    data = await container.auth.setup_totp()
    return SuccessResponse(data=TotpSetupResponse(**data))


@router.post("/totp/enable", response_model=SuccessResponse[bool])
async def totp_enable(
    body: TotpCodeRequest,
    container: Container,
    current_user: CurrentUser,
    request: Request,
    response: Response,
) -> Any:
    await container.auth.enable_totp(body.code)
    # 启用会提升令牌版本, 立即为当前会话换发新令牌
    tokens = await container.auth.issue(current_user.username)
    set_auth_cookies(request, response, tokens, container.settings.jwt)
    return SuccessResponse(data=True)


@router.post("/totp/disable", response_model=SuccessResponse[bool])
async def totp_disable(
    body: TotpCodeRequest,
    container: Container,
    current_user: CurrentUser,
    request: Request,
    response: Response,
) -> Any:
    await container.auth.disable_totp(body.code)
    tokens = await container.auth.issue(current_user.username)
    set_auth_cookies(request, response, tokens, container.settings.jwt)
    return SuccessResponse(data=True)
