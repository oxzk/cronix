"""认证路由。"""

from __future__ import annotations

from fastapi import APIRouter

from cronix.core.dependencies import AuthServiceDep, CurrentUserDep
from cronix.schemas import APIResponse, LoginSchema, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(login_data: LoginSchema, service: AuthServiceDep):
    """用户名密码登录，成功后返回 JWT 访问令牌。"""
    data = await service.login(login_data)
    return APIResponse.ok(data, "Login successful")


@router.get("/me", response_model=APIResponse[UserResponse])
async def me(current_user: CurrentUserDep):
    """获取当前登录用户信息。

    用户由 ``AuthMiddleware`` 校验令牌后写入 ``request.state``，
    经 ``CurrentUserDep`` 注入。
    """
    return APIResponse.ok(UserResponse.model_validate(current_user))

