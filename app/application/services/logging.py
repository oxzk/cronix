"""LoggingService: 拥有 loguru sink id, 支持配置热切换。"""

from __future__ import annotations

from app.core.config import LoggingSettings
from app.infrastructure.logging.loguru import close_logging, configure_logging


class LoggingService:
    def __init__(self, settings: LoggingSettings) -> None:
        self._sink_ids = configure_logging(settings)

    def reload(self, values: dict) -> LoggingSettings:
        """应用新的日志配置(热更新)。"""
        new = LoggingSettings.model_validate(values)
        close_logging(self._sink_ids)
        self._sink_ids = configure_logging(new, reset=True)
        return new

    def close(self) -> None:
        close_logging(self._sink_ids)
        self._sink_ids = []
