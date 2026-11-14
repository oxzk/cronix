"""RuntimeLogger: 每条日志同时写 loguru 与运行日志缓冲, 以及递归脱敏工具。"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from app.runtime.execution.logs import RunLogBuffer

SENSITIVE_KEYS = {
    "password",
    "token",
    "api_key",
    "apikey",
    "secret",
    "cookie",
    "authorization",
    "bot_token",
    "access_token",
    "refresh_token",
}

_TEXT_PATTERN = re.compile(
    r"(?i)(bot_token|api[_-]?key|password|token|secret|authorization|cookie)"
    r"(\s*[\"'=:=]+\s*)([^\s\"'&]+)"
)
_TELEGRAM_URL_PATTERN = re.compile(r"(?i)(api\.telegram\.org/bot)[A-Za-z0-9:_-]+")
_BOT_TOKEN_PATTERN = re.compile(r"(?i)\bbot\d+:[A-Za-z0-9_-]{10,}\b")


def redact_text(text: str) -> str:
    """对文本中的 key=value / Telegram Bot Token 等敏感片段打码。"""

    def _replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}[REDACTED]"

    text = _TEXT_PATTERN.sub(_replace, text)
    text = _TELEGRAM_URL_PATTERN.sub(r"\1[REDACTED]", text)
    return _BOT_TOKEN_PATTERN.sub("bot[REDACTED]", text)


def redact(value: Any) -> Any:
    """递归脱敏: 命中敏感键的值替换为 [REDACTED]。"""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


class RuntimeLogger:
    """run 作用域日志: 输出到 loguru, 并在绑定 run_id 时写入内存缓冲。"""

    def __init__(self, run_logs: RunLogBuffer, run_id: str | None = None) -> None:
        self._run_logs = run_logs
        self._run_id = run_id

    def for_run(self, run_id: str) -> "RuntimeLogger":
        return RuntimeLogger(self._run_logs, run_id)

    def _write(self, level: str, message: str) -> None:
        message = redact_text(str(message))
        logger.log(level, message)
        if self._run_id is not None:
            self._run_logs.append(self._run_id, level, message)

    def debug(self, message: str) -> None:
        self._write("DEBUG", message)

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def success(self, message: str) -> None:
        self._write("SUCCESS", message)

    def warning(self, message: str) -> None:
        self._write("WARNING", message)

    def error(self, message: str) -> None:
        self._write("ERROR", message)
