"""JWT 编解码: HS256, access/refresh 双 token。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import JWTSettings
from app.core.exceptions import AuthenticationError
from app.core.utils import utc_now


@dataclass(frozen=True)
class Principal:
    username: str
    token_version: int = 0


class JWTCodec:
    def __init__(self, settings: JWTSettings) -> None:
        self._secret = settings.secret
        self._access_expire_minutes = settings.access_expire_minutes
        self._refresh_expire_days = settings.refresh_expire_days

    def issue(self, username: str, token_version: int) -> dict[str, str]:
        now = utc_now()
        access = self._encode(username, "access", token_version, now + timedelta(minutes=self._access_expire_minutes))
        refresh = self._encode(username, "refresh", token_version, now + timedelta(days=self._refresh_expire_days))
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    def decode(self, token: str, purpose: str) -> Principal:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("令牌无效或已过期") from exc
        if payload.get("type") != purpose:
            raise AuthenticationError("令牌类型不匹配")
        username = payload.get("sub")
        if not username:
            raise AuthenticationError("令牌缺少主体")
        try:
            version = int(payload.get("ver", 0))
        except (TypeError, ValueError):
            version = 0
        return Principal(username=str(username), token_version=version)

    def _encode(self, username: str, token_type: str, token_version: int, expires_at: datetime) -> str:
        payload = {
            "sub": username,
            "type": token_type,
            "ver": token_version,
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")
