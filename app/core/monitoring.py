"""监控配置模型: HTTP 参数 / 服务连接 URL 与 SSL。"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar, Literal
from urllib.parse import parse_qs, unquote, unquote_plus, urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError as PydanticValidationError,
    field_validator,
)

from app.core.exceptions import ValidationError

SUPPORTED_KINDS = {"http", "redis", "mysql", "postgresql", "mongo", "rabbitmq"}
REDACTED = "[REDACTED]"
CONNECTION_URL_PATTERN = re.compile(
    r"\b(?:rediss?|mysql|postgres(?:ql)?|mongodb(?:\+srv)?|amqps?)"
    r"(?:\+\w+)?://[^\s\"'<>]+",
    re.IGNORECASE,
)


class HttpConfig(BaseModel):
    method: Literal["GET", "HEAD", "POST"] = "GET"
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    expected_status: int = 200
    verify_tls: bool = True

    @field_validator("url")
    @classmethod
    def _url_scheme(cls, value: str) -> str:
        url = value.strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("url 必须以 http(s):// 开头")
        return url

    @field_validator("expected_status")
    @classmethod
    def _status_range(cls, value: int) -> int:
        if not 100 <= value <= 599:
            raise ValueError("expected_status 必须在 100-599 之间")
        return value


class ConnectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schemes: ClassVar[tuple[str, ...]] = ()

    url: str

    @field_validator("url")
    @classmethod
    def _connection_url(cls, value: str) -> str:
        url = value.strip()
        if not url:
            raise ValueError("连接 URL 不能为空")
        if any(character.isspace() for character in url):
            raise ValueError("连接 URL 不能包含空格")
        if not any(url.lower().startswith(f"{scheme}://") for scheme in cls.schemes):
            raise ValueError(f"URL 协议必须为 {' / '.join(cls.schemes)}")
        return url


class RedisConfig(ConnectionConfig):
    schemes = ("redis", "rediss")


class MysqlConfig(ConnectionConfig):
    schemes = ("mysql",)


class PostgresqlConfig(ConnectionConfig):
    schemes = ("postgres", "postgresql")
    ssl: bool = False


class MongoConfig(ConnectionConfig):
    schemes = ("mongodb", "mongodb+srv")


class RabbitmqConfig(ConnectionConfig):
    schemes = ("amqp", "amqps")


CONFIG_MODELS: dict[str, type[BaseModel]] = {
    "http": HttpConfig,
    "redis": RedisConfig,
    "mysql": MysqlConfig,
    "postgresql": PostgresqlConfig,
    "mongo": MongoConfig,
    "rabbitmq": RabbitmqConfig,
}


def mysql_connection_options(url: str) -> dict[str, Any]:
    """aiomysql 不接受 DSN, 把 URL 拆成连接参数 (不做格式校验)。"""
    parts = urlsplit(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    return {
        "host": parts.hostname,
        "port": parts.port or 3306,
        "user": unquote(parts.username or ""),
        "password": unquote(parts.password or ""),
        "db": unquote(parts.path.removeprefix("/")) or None,
        "charset": query.get("charset", ["utf8mb4"])[0] or "utf8mb4",
        "ssl": query.get("ssl", ["false"])[0].lower() in {"true", "1"},
    }


def validate_config(kind: str, config: dict) -> dict:
    """按 kind 校验并补默认值, 返回规范化配置。"""
    if kind not in CONFIG_MODELS:
        raise ValidationError(f"不支持的监控类型: {kind}")
    if not isinstance(config, dict):
        raise ValidationError("监控配置必须是对象")
    try:
        return CONFIG_MODELS[kind].model_validate(config).model_dump()
    except PydanticValidationError as exc:
        errors = exc.errors(include_input=False, include_context=False, include_url=False)[:3]
        raise ValidationError(f"监控配置不合法: {errors}") from None


def redact_config(kind: str, config: dict | None) -> dict:
    """服务连接 URL 可能包含账号、密码或查询凭据, 响应整体脱敏。"""
    data = dict(config or {})
    if kind == "http":
        return data
    result: dict = {"url": REDACTED if data.get("url") else ""}
    if kind == "postgresql":
        result["ssl"] = data.get("ssl", False)
    return result


def merge_redacted(kind: str, old: dict | None, new: dict) -> dict:
    """编辑时未修改 URL 的占位符沿用已保存的 URL。"""
    merged = dict(new)
    if kind != "http" and merged.get("url") == REDACTED:
        merged["url"] = str((old or {}).get("url") or "")
    return merged


def redact_connection_error(kind: str, config: dict, message: str | None) -> str | None:
    """在历史记录、事件和响应共用错误文案前清除连接凭据。"""
    if kind == "http" or not message:
        return message
    url = str(config.get("url") or "")
    sensitive = {url, unquote(url)}
    try:
        parts = urlsplit(url)
        for value in (parts.username, parts.password):
            if value:
                sensitive.update((value, unquote(value)))
        for item in parts.query.split("&"):
            _, separator, value = item.partition("=")
            if separator and value:
                sensitive.update((value, unquote_plus(value)))
    except ValueError:
        pass
    sensitive.discard("")
    for value in tuple(sensitive):
        sensitive.update(
            (
                repr(value)[1:-1],
                json.dumps(value, ensure_ascii=False)[1:-1],
                json.dumps(value, ensure_ascii=True)[1:-1],
            )
        )
    patterns = [re.escape(value) for value in sorted(sensitive, key=len, reverse=True)]
    if patterns:
        message = re.sub("|".join(patterns), REDACTED, message, flags=re.IGNORECASE)
    return CONNECTION_URL_PATTERN.sub(REDACTED, message)
