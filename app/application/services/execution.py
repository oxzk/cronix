"""ExecutionService: 手动/调度统一提交入口, 并发信号量 + 重试链 + 取消 + 启动恢复。"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from app.core.config import RuntimeSettings
from app.core.exceptions import ConflictError, NotFoundError, RuntimeInitializationError
from app.core.utils import utc_now
from app.infrastructure.database.models.task_run import TaskRun
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.runtime.enums import ExecutionStatus, Trigger
from app.runtime.execution.lifecycle import ExecutionLifecycle, RunPlan
from app.runtime.execution.logs import RunLogBuffer


@dataclass
class _Job:
    task_id: uuid.UUID
    task: asyncio.Task  # type: ignore[type-arg]


class _DynamicLimiter:
    """并发上限可实时调整的限流器(替代固定容量的 Semaphore)。"""

    def __init__(self, limit: int) -> None:
        self._limit = max(1, limit)
        self._active = 0
        self._condition = asyncio.Condition()
        self._wake_task: asyncio.Task | None = None

    async def acquire(self) -> None:
        async with self._condition:
            while self._active >= self._limit:
                await self._condition.wait()
            self._active += 1

    async def release(self) -> None:
        async with self._condition:
            self._active = max(0, self._active - 1)
            self._condition.notify()

    def set_limit(self, limit: int) -> None:
        self._limit = max(1, limit)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 无运行中的事件循环(退出/测试场景): 新上限在下次 acquire 时自然生效
            return
        # 上限提高时唤醒等待中的提交
        self._wake_task = loop.create_task(self._wake_all())

    async def _wake_all(self) -> None:
        async with self._condition:
            self._condition.notify_all()


class ExecutionService:
    def __init__(
        self,
        session_factory,  # type: ignore[no-untyped-def]
        run_logs: RunLogBuffer,
        runtime_state,  # type: ignore[no-untyped-def]
    ) -> None:
        self._session_factory = session_factory
        self._run_logs = run_logs
        self._runtime_state = runtime_state
        self._slots = _DynamicLimiter(runtime_state.max_concurrent_runs)
        runtime_state.subscribe(self._on_runtime_change)
        self._submission = asyncio.Lock()
        self._jobs: dict[uuid.UUID, _Job] = {}
        self._lifecycle: ExecutionLifecycle | None = None

    def _on_runtime_change(self, settings: RuntimeSettings) -> None:
        self._slots.set_limit(settings.max_concurrent_runs)

    def attach_lifecycle(self, lifecycle: ExecutionLifecycle) -> None:
        self._lifecycle = lifecycle

    def _require_lifecycle(self) -> ExecutionLifecycle:
        if self._lifecycle is None:
            raise RuntimeInitializationError("执行生命周期未初始化")
        return self._lifecycle

    # ---- 提交 ----

    async def run(
        self, task_id: uuid.UUID, trigger: Trigger, scheduled_at: datetime | None = None
    ) -> TaskRun:
        async with self._submission:
            async with UnitOfWork(self._session_factory) as uow:
                task = await uow.tasks.get(task_id)
                if task is None:
                    raise NotFoundError("任务不存在")
                run = TaskRun(
                    task_id=task_id,
                    trigger=int(trigger),
                    status=int(ExecutionStatus.PENDING),
                    attempt=1,
                    scheduled_at=scheduled_at,
                )
                await uow.task_runs.add(run)
            job = _Job(
                task_id=task_id,
                task=asyncio.create_task(self._execute(run.id, task_id, 1, trigger), name=f"cronix-{run.id}"),
            )
            self._jobs[run.id] = job
        return run

    async def _execute(self, run_id: uuid.UUID, task_id: uuid.UUID, attempt: int, trigger: Trigger) -> None:
        lifecycle = self._require_lifecycle()
        try:
            while True:
                await self._slots.acquire()
                try:
                    plan = await self._build_plan(run_id, task_id, attempt)
                    if plan is None:
                        return
                    status = await lifecycle.run(plan)
                finally:
                    await self._slots.release()
                if status in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
                    return
                info = await self._retry_info(task_id)
                if info is None or attempt > info[0]:
                    return
                # 重试等待不占用并发槽位
                await asyncio.sleep(info[1])
                new_run_id = await self._create_retry_run(task_id, attempt + 1, trigger)
                job = self._jobs.pop(run_id, None)
                if job is not None:
                    self._jobs[new_run_id] = job
                run_id = new_run_id
                attempt += 1
        except asyncio.CancelledError:
            await self._mark_cancelled_if_pending(run_id)
            raise
        finally:
            self._jobs.pop(run_id, None)

    # ---- 取消/恢复/关闭 ----

    async def cancel(self, run_id: uuid.UUID) -> None:
        job = self._jobs.get(run_id)
        if job is None:
            async with UnitOfWork(self._session_factory) as uow:
                run = await uow.task_runs.get(run_id)
            if run is None:
                raise NotFoundError("执行记录不存在")
            raise ConflictError("执行已结束或不在运行队列中, 无法取消")
        job.task.cancel()

    async def cancel_for_task(self, task_id: uuid.UUID) -> int:
        tasks = [
            job.task
            for job in list(self._jobs.values())
            if job.task_id == task_id and not job.task.done()
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.wait(tasks, timeout=5)
        return len(tasks)

    async def cancel_all(self) -> None:
        """取消所有在跑任务并等待收尾(恢复备份前使用)。"""
        tasks = [job.task for job in list(self._jobs.values())]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.wait(tasks, timeout=self._runtime_state.shutdown_timeout)

    async def recover(self) -> None:
        """启动恢复: 孤儿 RUNNING → failed_interrupted, 遗留 PENDING → cancelled。"""
        async with UnitOfWork(self._session_factory) as uow:
            interrupted = await uow.task_runs.recover_interrupted()
            cancelled = await uow.task_runs.cancel_pending_all()
        if interrupted or cancelled:
            logger.info(f"启动恢复: 中断 {interrupted} 条, 取消排队 {cancelled} 条")

    async def close(self) -> None:
        tasks = [job.task for job in list(self._jobs.values())]
        for task in tasks:
            task.cancel()
        if tasks:
            _, pending = await asyncio.wait(
                tasks, timeout=self._runtime_state.shutdown_timeout
            )
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        self._jobs.clear()

    # ---- 查询 ----

    async def get_logs(self, run_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
        async with UnitOfWork(self._session_factory) as uow:
            run = await uow.task_runs.get(run_id)
        if run is None:
            raise NotFoundError("执行记录不存在")
        if ExecutionStatus(run.status).is_terminal:
            return {"run_id": str(run_id), "persisted": True, "logs": list(run.logs or [])}
        return {
            "run_id": str(run_id),
            "persisted": False,
            "logs": self._run_logs.snapshot(str(run_id)),
        }

    async def list_runs(
        self,
        page: int,
        page_size: int,
        *,
        task_id: uuid.UUID | None = None,
        status: int | None = None,
        trigger: int | None = None,
    ) -> tuple[list[tuple[TaskRun, str | None]], int]:
        async with UnitOfWork(self._session_factory) as uow:
            return await uow.task_runs.list_paginated(
                page, page_size, task_id=task_id, status=status, trigger=trigger
            )

    async def delete_run(self, run_id: uuid.UUID) -> None:
        """删除已结束的执行记录; 未结束的需先取消。"""
        async with UnitOfWork(self._session_factory) as uow:
            run = await uow.task_runs.get(run_id)
            if run is None:
                raise NotFoundError("执行记录不存在")
            if not ExecutionStatus(run.status).is_terminal:
                raise ConflictError("执行未结束, 请先取消后再删除")
            await uow.task_runs.delete(run)

    async def get_run(self, run_id: uuid.UUID) -> tuple[TaskRun, str | None]:
        async with UnitOfWork(self._session_factory) as uow:
            run = await uow.task_runs.get(run_id)
            if run is None:
                raise NotFoundError("执行记录不存在")
            task = await uow.tasks.get(run.task_id)
        return run, (task.name if task is not None else None)

    # ---- 内部 ----

    async def on_running(self, run_id: uuid.UUID) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            await uow.task_runs.set_running(run_id, utc_now())

    async def on_terminal(self, run_id: uuid.UUID, payload: dict) -> None:  # type: ignore[type-arg]
        async with UnitOfWork(self._session_factory) as uow:
            await uow.task_runs.set_terminal(
                run_id,
                {
                    "status": payload["status"],
                    "exit_code": payload.get("exit_code"),
                    "error_code": payload.get("error_code"),
                    "error_message": payload.get("error_message"),
                    "duration_ms": payload.get("duration_ms"),
                    "started_at": payload.get("started_at"),
                    "completed_at": payload.get("completed_at"),
                    "logs": payload.get("logs") or [],
                },
            )
            run = await uow.task_runs.get(run_id)
            if run is None:
                return
            task = await uow.tasks.get(run.task_id)
            if task is not None:
                task.last_run_at = payload.get("completed_at")
                task.last_status = int(payload["status"])

    async def _build_plan(self, run_id: uuid.UUID, task_id: uuid.UUID, attempt: int) -> RunPlan | None:
        async with UnitOfWork(self._session_factory) as uow:
            run = await uow.task_runs.get(run_id)
            task = await uow.tasks.get(task_id)
            if run is None or task is None:
                logger.warning("任务或执行记录已不存在, 跳过执行", run_id=str(run_id))
                return None
            command = task.command or ""
            if task.script_id is not None:
                script = await uow.scripts.get(task.script_id)
                if script is None:
                    logger.warning(
                        "任务引用的脚本不存在, 使用内联命令兜底",
                        task_id=str(task_id),
                        script_id=str(task.script_id),
                    )
                else:
                    command = script.content
            return RunPlan(
                run_id=run_id,
                task_id=task_id,
                task_name=task.name,
                command=command,
                timeout=task.timeout,
                attempt=attempt,
            )

    async def _retry_info(self, task_id: uuid.UUID) -> tuple[int, int] | None:
        async with UnitOfWork(self._session_factory) as uow:
            task = await uow.tasks.get(task_id)
        if task is None:
            return None
        return task.max_retries, task.retry_delay

    async def _create_retry_run(self, task_id: uuid.UUID, attempt: int, trigger: Trigger) -> uuid.UUID:
        async with UnitOfWork(self._session_factory) as uow:
            run = TaskRun(task_id=task_id, trigger=int(trigger), status=int(ExecutionStatus.PENDING), attempt=attempt)
            await uow.task_runs.add(run)
            return run.id

    async def _mark_cancelled_if_pending(self, run_id: uuid.UUID) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            run = await uow.task_runs.get(run_id)
            if run is None or ExecutionStatus(run.status).is_terminal:
                return
            run.status = int(ExecutionStatus.CANCELLED)
            run.error_code = "cancelled"
            run.error_message = "执行被取消"
