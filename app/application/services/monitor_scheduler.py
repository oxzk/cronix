"""MonitorSchedulerService: 按间隔触发监控检查, 定期清理历史。"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta

from loguru import logger

from app.core.utils import utc_now
from app.infrastructure.database.unit_of_work import UnitOfWork

RETENTION_DAYS = 3  # 每个监控最多保留 3 天检查记录
CLEANUP_INTERVAL = timedelta(hours=1)


class MonitorSchedulerService:
    def __init__(self, session_factory, monitors, runtime_state, tick_seconds: float = 1.0) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory
        self._monitors = monitors
        self._runtime_state = runtime_state
        self._tick_seconds = tick_seconds
        self._loop_task: asyncio.Task | None = None
        self._last_cleanup: datetime = utc_now() - CLEANUP_INTERVAL  # 启动后首次 tick 立即清理

    async def start(self) -> None:
        await self._backfill()
        self._loop_task = asyncio.create_task(self._loop(), name="cronix-monitor-scheduler")
        logger.info("监控调度器已启动", tick_seconds=self._tick_seconds)

    async def stop(self) -> None:
        if self._loop_task is not None:
            self._loop_task.cancel()
            await asyncio.gather(self._loop_task, return_exceptions=True)
            self._loop_task = None

    async def _backfill(self) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            for monitor in await uow.monitors.list_enabled():
                if monitor.next_check_at is None:
                    monitor.next_check_at = utc_now()

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("监控调度 tick 失败")
            await asyncio.sleep(self._tick_seconds)

    async def _tick(self) -> None:
        if self._runtime_state.maintenance:
            return
        now = utc_now()
        due_ids: list[uuid.UUID] = []
        async with UnitOfWork(self._session_factory) as uow:
            for monitor in await uow.monitors.list_due(now):
                monitor.next_check_at = now + timedelta(seconds=monitor.interval_seconds)
                due_ids.append(monitor.id)
        for monitor_id in due_ids:
            self._monitors.schedule_check(monitor_id)

        if now - self._last_cleanup >= CLEANUP_INTERVAL:
            self._last_cleanup = now
            async with UnitOfWork(self._session_factory) as uow:
                removed = await uow.monitor_checks.cleanup_before(now - timedelta(days=RETENTION_DAYS))
            if removed:
                logger.info("清理过期监控记录", count=removed)
