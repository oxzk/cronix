"""应用配置。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（src 的父目录）
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """应用配置，通过环境变量或 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 数据库配置。
    database_url: str = Field(
        default="mysql+aiomysql://user:password@localhost:3306/cronix",
        description="SQLAlchemy 异步数据库连接地址",
    )
    database_ssl: bool = Field(default=True, description="数据库连接是否启用 SSL")

    # 应用配置。
    app_name: str = "Cronix"
    app_debug: bool = False

    # 认证配置。
    secret_key: str = Field(
        default="change-me-in-production-please-use-a-random-secret",
        description="JWT 签名密钥，生产环境务必通过环境变量覆盖",
    )
    jwt_expire_hours: int = Field(
        default=24, description="访问令牌有效期（小时）"
    )

    # 跨域配置。
    cors_origins: List[str] = ["*"]

    # HTTP 重试配置。
    http_retry_attempts: int = 3
    http_retry_delay_seconds: float = 0.5
    http_retry_backoff: float = 2.0

    @field_validator("http_retry_attempts")
    @classmethod
    def validate_http_retry_attempts(cls, value: int) -> int:
        """校验 HTTP 最大尝试次数。"""
        if value < 1:
            raise ValueError("http_retry_attempts must be greater than or equal to 1")
        return value

    @field_validator("http_retry_delay_seconds")
    @classmethod
    def validate_http_retry_delay_seconds(cls, value: float) -> float:
        """校验 HTTP 首次重试等待秒数。"""
        if value < 0:
            raise ValueError("http_retry_delay_seconds must be greater than or equal to 0")
        return value

    @field_validator("http_retry_backoff")
    @classmethod
    def validate_http_retry_backoff(cls, value: float) -> float:
        """校验 HTTP 重试退避倍率。"""
        if value < 1:
            raise ValueError("http_retry_backoff must be greater than or equal to 1")
        return value


settings = Settings()
