"""应用配置: pydantic-settings, 环境变量无前缀, 嵌套分隔符 __。"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """数据库配置, 将 PostgreSQL 地址统一为 asyncpg 驱动."""

    url: str = "postgresql+asyncpg://cronix:cronix@127.0.0.1:5432/cronix"
    ssl: bool = False

    @field_validator("url")
    @classmethod
    def _normalize_url(cls, value: str) -> str:
        """转换 PostgreSQL URL 前缀并拒绝不支持的数据库驱动."""
        if value.startswith(("postgresql://", "postgres://")):
            value = "postgresql+asyncpg://" + value.split("://", 1)[1]
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE__URL 仅支持 postgresql://, postgres:// 或 postgresql+asyncpg://")
        return value


class JWTSettings(BaseModel):
    """JWT 配置。"""

    secret: str
    access_expire_minutes: int = Field(default=30, gt=0)
    refresh_expire_days: int = Field(default=30, gt=0)

    @field_validator("secret")
    @classmethod
    def _secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT secret 长度必须 ≥ 32 字符")
        return value


class RuntimeSettings(BaseModel):
    """运行时配置(system/base, 重启生效)。"""

    default_timeout: int = Field(default=120, gt=0)
    max_concurrent_runs: int = Field(default=4, gt=0)
    shutdown_timeout: int = Field(default=30, gt=0)
    misfire_grace_seconds: int = Field(default=60, ge=0)
    notify_timeout: int = Field(default=30, gt=0)


class SystemBaseSettings(RuntimeSettings):
    """system_settings 中 system/base 行的结构, 与 RuntimeSettings 字段一致。"""


class LoggingSettings(BaseModel):
    """日志配置(热更新)。控制台+文件固定开启, 目录固定 data/logs、每日 00:00 滚动、不压缩。"""

    level: str = "INFO"
    retention: str = "7 days"

    @field_validator("level")
    @classmethod
    def _valid_level(cls, value: str) -> str:
        upper = value.upper()
        if upper not in {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"非法日志级别: {value}")
        return upper


class Settings(BaseSettings):
    """根配置: 仅在 lifespan 中实例化一次。"""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings  # 必填
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError("CORS_ALLOW_ORIGINS 必须是 JSON 数组")
            value = parsed
        if isinstance(value, list) and "*" in value:
            raise ValueError("CORS_ALLOW_ORIGINS 不允许使用 * (凭据模式下不安全)")
        return value


def load_settings() -> Settings:
    return Settings()
