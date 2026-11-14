"""AuthService: 单管理员(argon2) + JWT(版本可撤销) + TOTP + 登录限流。"""

from __future__ import annotations

import secrets
import time
from collections import deque

from loguru import logger

from app.core import totp
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    TooManyAttemptsError,
    ValidationError,
)
from app.infrastructure.auth.jwt import JWTCodec, Principal
from app.infrastructure.auth.password import hash_password, verify_password
from app.infrastructure.database.models.system_setting import SystemSetting
from app.infrastructure.database.unit_of_work import UnitOfWork

MAX_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300
LOCK_SECONDS = 300


class AuthService:
    def __init__(self, session_factory, codec: JWTCodec) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory
        self._codec = codec
        self._failures: deque[float] = deque()
        self._locked_until = 0.0

    async def bootstrap(self) -> None:
        """首次启动创建管理员并生成随机初始密码(仅在本次启动日志打印一次)。"""
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.system_settings.by_key("auth", "admin") is not None:
                return
            initial_password = secrets.token_urlsafe(12)
            await uow.system_settings.add(
                SystemSetting(
                    scope="auth",
                    key="admin",
                    type="object",
                    value={
                        "username": "admin",
                        "password": hash_password(initial_password),
                        "token_version": 1,
                        "totp_enabled": False,
                        "totp_secret": "",
                    },
                    is_complete=True,
                    description="管理员账号",
                )
            )
        logger.warning(
            "首次启动已创建管理员账号 admin, 初始密码: {} (仅本次日志显示, 请登录后立即修改)",
            initial_password,
        )

    async def login(self, username: str, password: str, code: str | None = None) -> dict[str, str]:
        self._ensure_not_locked()
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
        if row is None:
            raise AuthenticationError("管理员账号未初始化")
        value = row.value or {}
        if username != value.get("username") or not verify_password(password, str(value.get("password") or "")):
            self._record_failure()
            raise AuthenticationError("用户名或密码错误")
        if value.get("totp_enabled"):
            secret = str(value.get("totp_secret") or "")
            if not code:
                raise AuthenticationError("需要动态验证码", code="totp_required")
            if not totp.verify(secret, code):
                self._record_failure()
                raise AuthenticationError("动态验证码错误")
        self._reset_failures()
        return self._codec.issue(username, self._version(value))

    async def authenticate(self, token: str, purpose: str = "access") -> Principal:
        principal = self._codec.decode(token, purpose)
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
        if row is None:
            raise AuthenticationError("管理员账号未初始化")
        current = self._version(row.value or {})
        if principal.token_version != current:
            raise AuthenticationError("登录已失效, 请重新登录")
        return Principal(username=principal.username, token_version=current)

    async def issue(self, username: str) -> dict[str, str]:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
        if row is None:
            raise NotFoundError("管理员账号未初始化")
        return self._codec.issue(username, self._version(row.value or {}))

    async def logout(self) -> None:
        """登出即提升令牌版本, 使已签发的 access/refresh 全部失效。"""
        await self._bump_version()

    async def verify_reauth(self, password: str, code: str | None = None) -> None:
        """危险操作前的再认证(密码 + 已启用时的 TOTP)。"""
        self._ensure_not_locked()
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
        if row is None:
            raise NotFoundError("管理员账号未初始化")
        value = row.value or {}
        if not verify_password(password, str(value.get("password") or "")):
            self._record_failure()
            raise AuthenticationError("密码错误")
        if value.get("totp_enabled"):
            if not code:
                raise ValidationError("请输入动态验证码")
            if not totp.verify(str(value.get("totp_secret") or ""), code):
                self._record_failure()
                raise AuthenticationError("动态验证码错误")
        self._reset_failures()

    # ---- TOTP ----

    async def totp_status(self) -> dict:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
        if row is None:
            raise NotFoundError("管理员账号未初始化")
        return {"enabled": bool((row.value or {}).get("totp_enabled"))}

    async def setup_totp(self) -> dict:
        """生成待确认密钥(不启用), 返回密钥与 otpauth URI。"""
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
            if row is None:
                raise NotFoundError("管理员账号未初始化")
            value = dict(row.value or {})
            if value.get("totp_enabled"):
                raise ConflictError("两步验证已启用, 请先关闭")
            secret = totp.generate_secret()
            row.value = {**value, "totp_secret": secret, "totp_enabled": False}
            username = str(value.get("username") or "admin")
        return {"secret": secret, "uri": totp.provisioning_uri(secret, username)}

    async def enable_totp(self, code: str) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
            if row is None:
                raise NotFoundError("管理员账号未初始化")
            value = dict(row.value or {})
            secret = str(value.get("totp_secret") or "")
            if not secret:
                raise ValidationError("请先获取 TOTP 密钥")
            if not totp.verify(secret, code):
                raise ValidationError("动态验证码错误")
            row.value = {
                **value,
                "totp_enabled": True,
                "token_version": self._version(value) + 1,
            }

    async def disable_totp(self, code: str) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
            if row is None:
                raise NotFoundError("管理员账号未初始化")
            value = dict(row.value or {})
            if not value.get("totp_enabled"):
                return
            if not totp.verify(str(value.get("totp_secret") or ""), code):
                raise ValidationError("动态验证码错误")
            row.value = {
                **value,
                "totp_enabled": False,
                "totp_secret": "",
                "token_version": self._version(value) + 1,
            }

    # ---- 内部 ----

    async def _bump_version(self) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("auth", "admin")
            if row is None:
                return
            value = dict(row.value or {})
            row.value = {**value, "token_version": self._version(value) + 1}

    @staticmethod
    def _version(value: dict) -> int:
        try:
            return int(value.get("token_version") or 1)
        except (TypeError, ValueError):
            return 1

    def _ensure_not_locked(self) -> None:
        now = time.monotonic()
        if now < self._locked_until:
            raise TooManyAttemptsError("尝试次数过多, 请稍后再试")

    def _record_failure(self) -> None:
        now = time.monotonic()
        while self._failures and now - self._failures[0] > ATTEMPT_WINDOW_SECONDS:
            self._failures.popleft()
        self._failures.append(now)
        if len(self._failures) >= MAX_ATTEMPTS:
            self._locked_until = now + LOCK_SECONDS
            self._failures.clear()

    def _reset_failures(self) -> None:
        self._failures.clear()
        self._locked_until = 0.0
