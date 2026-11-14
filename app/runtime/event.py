"""EventBus: 进程内 pub/sub, 构造注入, handler 异常隔离。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Awaitable, Callable

from loguru import logger

from app.core.utils import utc_now
from app.runtime.logger import redact

EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True)
class Event:
    type: str
    timestamp: datetime = field(default_factory=utc_now)
    run_id: str | None = None
    task_id: str | None = None
    monitor_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        self._handlers.append(handler)

    async def emit(self, event: Event) -> None:
        safe = replace(event, data=redact(event.data))
        for handler in tuple(self._handlers):
            try:
                async with asyncio.timeout(30):
                    await handler(safe)
            except Exception:
                logger.exception("事件处理器执行失败", event_type=event.type)
