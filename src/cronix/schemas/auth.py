"""认证相关数据结构。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginSchema(BaseModel):
    """登录请求数据。"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


class UserResponse(BaseModel):
    """用户信息响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class TokenResponse(BaseModel):
    """登录令牌响应数据。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="令牌有效期（秒）")
    user: UserResponse
