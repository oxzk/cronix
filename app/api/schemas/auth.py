"""认证相关模式。"""

from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    username: str


class TotpStatusResponse(BaseModel):
    enabled: bool


class TotpSetupResponse(BaseModel):
    secret: str
    uri: str


class TotpCodeRequest(BaseModel):
    code: str
