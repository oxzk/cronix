"""SchedulerService: cron 调度循环 — tick 扫描到期任务, 提交执行并推进 next_run_at。"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta

from loguru import logger

from app.core.cron import advance_to_future, next_after
from app.core.utils import utc_now
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.runtime.enums import Trigger

RETENTION_DAYS = 3  # 每个任务的执行记录最多保留 3 天
CLEANUP_INTERVAL = timedelta(hours=1)


class SchedulerService:
    def __init__(
        self,
        session_factory,  # type: ignore[no-untyped-def]
        executions,  # type: ignore[no-untyped-def]
        runtime_state,  # type: ignore[no-untyped-def]
        tick_seconds: float = 1.0,
    ) -> None:
        self._session_factory = session_factory
        self._executions = executions
        self._runtime_state = runtime_state
        self._tick_seconds = tick_seconds
        self._loop_task: asyncio.Task | None = None
        self._last_cleanup: datetime = utc_now() - CLEANUP_INTERVAL  # 启动后首次 tick 立即清理

    async def start(self) -> None:
        await self._backfill()
        self._loop_task = asyncio.create_task(self._loop(), name="cronix-scheduler")
        logger.info(
            "调度器已启动",
            tick_seconds=self._tick_seconds,
            grace_seconds=self._runtime_state.misfire_grace_seconds,
        )

    async def stop(self) -> None:
        if self._loop_task is not None:
            self._loop_task.cancel()
            await asyncio.gather(self._loop_task, return_exceptions=True)
            self._loop_task = None
            logger.info("调度器已停止")

    async def _backfill(self) -> None:
        """为 next_run_at 为空的启用任务补算下次执行时间。"""
        async with UnitOfWork(self._session_factory) as uow:
            for task in await uow.tasks.list_enabled():
                if task.next_run_at is None:
                    task.next_run_at = next_after(task.cron, utc_now())

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("调度 tick 失败")
            await asyncio.sleep(self._tick_seconds)

    async def _tick(self) -> None:
        if self._runtime_state.maintenance:
            return
        now = utc_now()
        # 每轮实时读取宽限秒数, 修改基础配置后立即生效
        grace = self._runtime_state.misfire_grace_seconds
        submissions: list[tuple[uuid.UUID, datetime]] = []
        async with UnitOfWork(self._session_factory) as uow:
            for task in await uow.tasks.list_due(now):
                scheduled_at = task.next_run_at
                if scheduled_at is None:
                    continue
                task.next_run_at = advance_to_future(task.cron, scheduled_at, now)
                if (now - scheduled_at).total_seconds() > grace:
                    logger.warning(
                        f"任务 {task.name} 错过计划时间 {scheduled_at.isoformat()}, 已跳过(超出宽限 {grace}s)"
                    )
                    continue
                submissions.append((task.id, scheduled_at))
        for task_id, scheduled_at in submissions:
            try:
                await self._executions.run(task_id, Trigger.SCHEDULE, scheduled_at)
            except Exception:
                logger.exception("调度提交失败", task_id=str(task_id))

        # 每小时清理 3 天前的执行记录
        if now - self._last_cleanup >= CLEANUP_INTERVAL:
            self._last_cleanup = now
            async with UnitOfWork(self._session_factory) as uow:
                removed = await uow.task_runs.cleanup_before(
                    now - timedelta(days=RETENTION_DAYS), include_active=False
                )
            if removed:
                logger.info("清理过期执行记录", count=removed)
