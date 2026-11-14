"""执行生命周期: PENDING 之后的运行态 → 终态, 终态先持久化(shielded)后发事件。"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from loguru import logger

from app.core.utils import utc_now
from app.runtime.enums import ExecutionStatus
from app.runtime.event import Event, EventBus
from app.runtime.execution.context import ExecutionContext
from app.runtime.execution.logs import RunLogBuffer
from app.runtime.executor.shell import ShellExecutor
from app.runtime.logger import RuntimeLogger
from app.runtime.state import RuntimeState

RunningCallback = Callable[[uuid.UUID], Awaitable[None]]
TerminalCallback = Callable[[uuid.UUID, dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class RunPlan:
    run_id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    command: str
    timeout: int | None
    attempt: int


class ExecutionLifecycle:
    """持久化留在应用层(注入回调), 运行时只关心执行与事件。"""

    def __init__(
        self,
        events: EventBus,
        run_logs: RunLogBuffer,
        runtime_logger: RuntimeLogger,
        runtime_state: RuntimeState,
        on_running: RunningCallback,
        on_terminal: TerminalCallback,
    ) -> None:
        self._events = events
        self._run_logs = run_logs
        self._runtime_logger = runtime_logger
        self._runtime_state = runtime_state
        self._on_running = on_running
        self._on_terminal = on_terminal

    async def run(self, plan: RunPlan) -> ExecutionStatus:
        started_at = utc_now()
        # 每次执行实时读取默认超时, system/base 修改后立即生效
        timeout = plan.timeout or self._runtime_state.default_timeout
        run_logger = self._runtime_logger.for_run(str(plan.run_id))
        ctx = ExecutionContext(
            run_id=plan.run_id,
            task_id=plan.task_id,
            task_name=plan.task_name,
            command=plan.command,
            logger=run_logger,
        )
        status = ExecutionStatus.FAILED
        exit_code: int | None = None
        error_code: str | None = None
        error_message: str | None = None
        cancelled = False

        try:
            await self._on_running(plan.run_id)
        except Exception:
            logger.exception("运行状态持久化失败", run_id=str(plan.run_id))

        try:
            run_logger.info(f"第 {plan.attempt} 次尝试开始执行(超时 {timeout}s)")
            await self._events.emit(
                Event(
                    "run.started",
                    run_id=str(plan.run_id),
                    task_id=str(plan.task_id),
                    data={"task_name": plan.task_name, "attempt": plan.attempt, "timeout": timeout},
                )
            )
            async with asyncio.timeout(timeout):
                result = await ShellExecutor().run(ctx)
            exit_code = result.exit_code
            if exit_code == 0:
                status = ExecutionStatus.COMPLETED
            else:
                status = ExecutionStatus.FAILED
                error_code = "non_zero_exit"
                error_message = f"命令退出码 {exit_code}"
        except TimeoutError:
            status = ExecutionStatus.TIMEOUT
            error_code = "timeout"
            error_message = f"执行超时({timeout}s)"
        except asyncio.CancelledError:
            status = ExecutionStatus.CANCELLED
            error_code = "cancelled"
            error_message = "执行被取消"
            cancelled = True

        duration_ms = int((utc_now() - started_at).total_seconds() * 1000)
        run_logger.info(f"执行结束: {status.code}")
        logs = self._run_logs.pop(str(plan.run_id))
        payload: dict[str, Any] = {
            "status": int(status),
            "exit_code": exit_code,
            "error_code": error_code,
            "error_message": error_message,
            "duration_ms": duration_ms,
            "started_at": started_at,
            "completed_at": utc_now(),
            "logs": logs,
        }

        finalize_task = asyncio.create_task(self._finalize(plan, payload))
        try:
            await asyncio.shield(finalize_task)
        except asyncio.CancelledError:
            if not finalize_task.done():
                await finalize_task
            raise
        if cancelled:
            raise asyncio.CancelledError
        return status

    async def _finalize(self, plan: RunPlan, payload: dict[str, Any]) -> None:
        status = ExecutionStatus(int(payload["status"]))
        try:
            await self._on_terminal(plan.run_id, payload)
        except Exception:
            logger.exception("终态持久化失败", run_id=str(plan.run_id))
        await self._events.emit(
            Event(
                status.event_name,
                run_id=str(plan.run_id),
                task_id=str(plan.task_id),
                data={
                    "task_name": plan.task_name,
                    "attempt": plan.attempt,
                    "status": int(status),
                    "exit_code": payload.get("exit_code"),
                    "error_code": payload.get("error_code"),
                    "error_message": payload.get("error_message"),
                    "duration_ms": payload.get("duration_ms"),
                },
            )
        )
