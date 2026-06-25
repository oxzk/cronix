"""认证安全工具：密码哈希与 JWT 令牌。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from cronix.core.config import settings


class Security:
    """认证安全工具集。

    提供密码哈希校验与 JWT 令牌签发/解析。JWT 固定使用 HS256 算法。
    """

    JWT_ALGORITHM = "HS256"

    @staticmethod
    def hash_password(password: str) -> str:
        """对明文密码进行 bcrypt 哈希。

        Args:
            password: 明文密码。

        Returns:
            哈希后的密码字符串。
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """校验明文密码与哈希是否匹配。

        Args:
            plain_password: 明文密码。
            hashed_password: 已存储的哈希密码。

        Returns:
            匹配返回 True，否则返回 False。
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    @classmethod
    def create_access_token(
        cls, subject: str, expires_delta: timedelta | None = None
    ) -> str:
        """生成 JWT 访问令牌。

        Args:
            subject: 令牌主体（通常为用户名），写入 ``sub`` 声明。
            expires_delta: 自定义有效期；不传时使用配置默认值。

        Returns:
            编码后的 JWT 字符串。
        """
        expire_delta = expires_delta or timedelta(hours=settings.jwt_expire_hours)
        expire = datetime.now(timezone.utc) + expire_delta
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, settings.secret_key, algorithm=cls.JWT_ALGORITHM)

    @classmethod
    def decode_access_token(cls, token: str) -> dict[str, Any]:
        """解码并校验 JWT 访问令牌。

        Args:
            token: JWT 字符串。

        Returns:
            令牌载荷。

        Raises:
            jwt.ExpiredSignatureError: 令牌已过期。
            jwt.InvalidTokenError: 令牌无效。
        """
        return jwt.decode(
            token, settings.secret_key, algorithms=[cls.JWT_ALGORITHM]
        )
