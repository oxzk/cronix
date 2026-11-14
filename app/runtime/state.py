"""运行时基础配置(system/base)的实时状态, 支持监听变更。"""

from __future__ import annotations

from typing import Callable

from loguru import logger

from app.core.config import RuntimeSettings

Listener = Callable[[RuntimeSettings], None]


class RuntimeState:
    """持有当前生效的 RuntimeSettings; 服务通过属性实时读取, 变更时通知监听者。"""

    def __init__(self, settings: RuntimeSettings) -> None:
        self._settings = settings
        self._listeners: list[Listener] = []
        self._maintenance = False

    @property
    def maintenance(self) -> bool:
        return self._maintenance

    def set_maintenance(self, enabled: bool) -> None:
        self._maintenance = enabled
        logger.warning("维护模式%s", "开启" if enabled else "关闭")

    @property
    def settings(self) -> RuntimeSettings:
        return self._settings

    @property
    def default_timeout(self) -> int:
        return self._settings.default_timeout

    @property
    def max_concurrent_runs(self) -> int:
        return self._settings.max_concurrent_runs

    @property
    def shutdown_timeout(self) -> int:
        return self._settings.shutdown_timeout

    @property
    def misfire_grace_seconds(self) -> int:
        return self._settings.misfire_grace_seconds

    @property
    def notify_timeout(self) -> int:
        return self._settings.notify_timeout

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def apply(self, values: dict) -> RuntimeSettings:
        """应用新的基础配置并通知监听者(立即生效)。"""
        self._settings = RuntimeSettings.model_validate(values)
        logger.info("基础配置已实时生效", max_concurrent_runs=self._settings.max_concurrent_runs)
        for listener in tuple(self._listeners):
            try:
                listener(self._settings)
            except Exception:
                logger.exception("运行时配置监听器执行失败")
        return self._settings
