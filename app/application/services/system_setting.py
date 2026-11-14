"""SystemSettingService: 双轨配置 — bootstrap 种子 / logging 热更新 / system base 重启生效。"""

from __future__ import annotations

import re

from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from app.core.config import LoggingSettings, RuntimeSettings, Settings, SystemBaseSettings
from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.auth.password import hash_password
from app.infrastructure.database.models.system_setting import SystemSetting
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.runtime.state import RuntimeState


class SystemSettingService:
    def __init__(self, session_factory, logging_service) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory
        self._logging = logging_service
        self._runtime_state: RuntimeState | None = None

    def attach_runtime_state(self, runtime_state: RuntimeState) -> None:
        self._runtime_state = runtime_state

    # ---- 启动 ----

    async def bootstrap(self, settings: Settings) -> None:
        """首启种子: 之后 .env 不再生效(日志除外)。"""
        defaults: list[tuple[str, str, dict, str]] = [
            (
                "system",
                "base",
                SystemBaseSettings(**settings.runtime.model_dump()).model_dump(),
                "系统基础配置(实时生效)",
            ),
            (
                "notification",
                "pusho",
                {"api_url": "", "api_key": "", "project": ""},
                "Pusho 推送配置",
            ),
            (
                "backup",
                "kryva",
                {
                    "api_url": "https://kryva.oozuo.com",
                    "api_key": "",
                    "platform": "cronix",
                },
                "Kryva 备份存储配置",
            ),
            ("logging", "loguru", settings.logging.model_dump(mode="json"), "日志配置(热更新)"),
        ]
        async with UnitOfWork(self._session_factory) as uow:
            for scope, key, value, description in defaults:
                if await uow.system_settings.by_key(scope, key) is None:
                    await uow.system_settings.add(
                        SystemSetting(
                            scope=scope,
                            key=key,
                            type="object",
                            value=value,
                            is_complete=self._is_complete(scope, key, value),
                            description=description,
                        )
                    )
        logger.info("system_settings 种子检查完成")

    async def refresh_completeness(self) -> None:
        """恢复备份后按当前字段回填完整性标记。"""
        async with UnitOfWork(self._session_factory) as uow:
            rows = await uow.system_settings.list_all()
            for row in rows:
                row.is_complete = self._is_complete(
                    row.scope, row.key, dict(row.value or {})
                )

    async def load_logging(self, settings: Settings) -> LoggingSettings:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("logging", "loguru")
        if row is None:
            return settings.logging
        return self._validate(LoggingSettings, row.value)

    async def load_system(self, settings: Settings) -> Settings:
        """system/base 覆盖 runtime 配置(重启生效)。"""
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("system", "base")
        if row is None:
            return settings
        value = dict(row.value or {})
        # 兼容旧备份/旧数据: webhook_timeout -> notify_timeout
        if "webhook_timeout" in value and "notify_timeout" not in value:
            value["notify_timeout"] = value["webhook_timeout"]
        base = self._validate(SystemBaseSettings, value)
        return settings.model_copy(
            update={"runtime": RuntimeSettings.model_validate(base.model_dump())}
        )

    # ---- 读写 ----

    async def list_all(self) -> list[dict]:
        async with UnitOfWork(self._session_factory) as uow:
            rows = await uow.system_settings.list_all()
        results: list[dict] = []
        for row in rows:
            if row.scope == "auth":
                continue  # 管理员凭据(哈希)永不下发
            value = dict(row.value or {})
            if row.scope == "notification" and row.key == "pusho" and value.get("api_key"):
                value["api_key"] = "[REDACTED]"
            if row.scope == "backup" and row.key == "kryva" and value.get("api_key"):
                value["api_key"] = "[REDACTED]"
            results.append(
                {
                    "scope": row.scope,
                    "key": row.key,
                    "type": row.type,
                    "value": value,
                    "is_complete": bool(row.is_complete),
                    "description": row.description,
                    "updated_at": row.updated_at,
                }
            )
        return results

    async def put(self, scope: str, key: str, value: dict) -> SystemSetting:
        """更新配置; logging / system/base 均立即生效。"""
        if scope == "system" and key == "base":
            validated = self._validate(SystemBaseSettings, value).model_dump()
        elif scope == "logging" and key == "loguru":
            validated = self._validate(LoggingSettings, value).model_dump(mode="json")
        elif scope == "notification" and key == "pusho":
            validated = self._validate_pusho(value)
        elif scope == "auth" and key == "admin":
            validated = self._validate_admin_password(value)
        elif scope == "backup" and key == "kryva":
            validated = self._validate_kryva(value)
        else:
            raise ValidationError(f"不支持的配置项: {scope}/{key}")

        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key(scope, key)
            if row is None:
                raise NotFoundError(f"配置项不存在: {scope}/{key}")
            if scope == "auth" and key == "admin":
                old = dict(row.value or {})
                try:
                    version = int(old.get("token_version") or 1)
                except (TypeError, ValueError):
                    version = 1
                row.value = {
                    **old,
                    "username": str(old.get("username") or "admin"),
                    "password": hash_password(validated["password"]),
                    # 改密后旧令牌全部失效, 需重新登录
                    "token_version": version + 1,
                }
            else:
                if scope == "notification" and key == "pusho" and validated.get("api_key") == "[REDACTED]":
                    # 占位符: 保留已存的旧值
                    validated["api_key"] = str((row.value or {}).get("api_key") or "")
                if scope == "backup" and key == "kryva" and validated.get("api_key") == "[REDACTED]":
                    validated["api_key"] = str((row.value or {}).get("api_key") or "")
                row.value = validated
            row.is_complete = self._is_complete(scope, key, dict(row.value or {}))

        if scope == "logging" and key == "loguru":
            self._logging.reload(validated)
            logger.info("日志配置已热更新")
        if scope == "system" and key == "base" and self._runtime_state is not None:
            self._runtime_state.apply(validated)
        if scope == "auth" and key == "admin":
            # 响应中不回显密码哈希
            row.value = {**(row.value or {}), "password": "[REDACTED]"}
            logger.info("管理员密码已更新")
        return row

    # ---- 内部 ----

    @staticmethod
    def _is_complete(scope: str, key: str, value: dict) -> bool:
        """按配置项要求判断必填字段是否齐全。"""
        if scope == "notification" and key == "pusho":
            fields = ("api_url", "api_key", "project")
        elif scope == "backup" and key == "kryva":
            fields = ("api_url", "api_key")
        elif scope == "auth" and key == "admin":
            fields = ("username", "password")
        else:
            return True
        return all(bool(str(value.get(field) or "").strip()) for field in fields)

    @staticmethod
    def _validate(model, value: dict):  # type: ignore[no-untyped-def]
        try:
            return model.model_validate(value)
        except PydanticValidationError as exc:
            raise ValidationError(f"配置不合法: {exc.errors()[:3]}") from exc

    @staticmethod
    def _validate_pusho(value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValidationError("Pusho 配置必须是对象")
        unknown = set(value) - {"api_url", "api_key", "project"}
        if unknown:
            raise ValidationError(f"Pusho 配置存在未知字段: {sorted(unknown)}")
        api_url = str(value.get("api_url") or "").strip().rstrip("/")
        if api_url and not api_url.startswith(("http://", "https://")):
            raise ValidationError("Pusho API 地址必须以 http(s):// 开头")
        project = str(value.get("project") or "").strip()
        if project and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", project):
            raise ValidationError("Pusho 项目名需以字母开头, 仅含字母/数字/下划线/连字符, 最长 64")
        return {
            "api_url": api_url,
            "api_key": str(value.get("api_key") or "").strip(),
            "project": project,
        }

    @staticmethod
    def _validate_kryva(value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValidationError("Kryva 配置必须是对象")
        unknown = set(value) - {"api_url", "api_key", "platform"}
        if unknown:
            raise ValidationError(f"Kryva 配置存在未知字段: {sorted(unknown)}")
        api_url = str(value.get("api_url") or "").strip() or "https://kryva.oozuo.com"
        if not api_url.startswith(("http://", "https://")):
            raise ValidationError("Kryva API 地址必须以 http(s):// 开头")
        platform = str(value.get("platform") or "").strip() or "cronix"
        if len(platform) > 100:
            raise ValidationError("存储标识不能超过 100 字符")
        return {
            "api_url": api_url.rstrip("/"),
            "api_key": str(value.get("api_key") or "").strip(),
            "platform": platform,
        }

    @staticmethod
    def _validate_admin_password(value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValidationError("管理员密码配置必须是对象")
        unknown = set(value) - {"password"}
        if unknown:
            raise ValidationError(f"管理员密码配置存在未知字段: {sorted(unknown)}")
        password = str(value.get("password") or "")
        if len(password) < 8:
            raise ValidationError("密码长度至少 8 位")
        if len(password) > 128:
            raise ValidationError("密码长度不能超过 128 位")
        return {"password": password}
