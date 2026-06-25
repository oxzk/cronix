"""任务调度服务。"""

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import json
from datetime import datetime
import os
import signal
from typing import Dict

from croniter import croniter

from cronix.core.database import db
from cronix.utils.datetime import utc_now
from cronix.models import Task, TaskExecution
from cronix.repositories import ExecutionRepository, NotificationRepository, TaskRepository
from cronix.schemas import ExecutionStatus
from cronix.services.notifier import notifier_service
from cronix.utils.logger import logger


@dataclass
class RunningTaskState:
    """运行中任务的进程内状态。"""

    task: asyncio.Task
    execution_id: int | None = None
    process: asyncio.subprocess.Process | None = None


class SchedulerService:
    """任务调度服务。"""

    def __init__(self):
        """初始化调度服务运行态。"""
        self._notifier_service = notifier_service
        self.running_tasks: Dict[int, RunningTaskState] = {}
        self._scheduler_task: asyncio.Task | None = None
        self.should_stop = False

    async def start(self) -> None:
        """以后台任务方式启动调度循环。"""
        if self._scheduler_task is not None and not self._scheduler_task.done():
            return

        await self.cleanup_orphan_executions()
        self.should_stop = False
        self._scheduler_task = asyncio.create_task(self._schedule_loop())

    async def stop(self) -> None:
        """停止调度器并取消运行中的任务。"""
        logger.info("Stopping scheduler...")
        self.should_stop = True

        if self._scheduler_task is not None and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._scheduler_task
        self._scheduler_task = None

        # 停止服务前逐个取消仍在运行的任务。
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)

        logger.info("Scheduler stopped")

    async def cancel_task(self, task_id: int) -> bool:
        """取消运行中的任务。"""
        running_task = self.running_tasks.get(task_id)
        if running_task is None:
            return False

        # 先终止子进程组，再取消协程，避免 shell 派生进程残留。
        await self._terminate_process(task_id, running_task.process)
        running_task.task.cancel()
        with suppress(asyncio.CancelledError):
            await running_task.task

        self.running_tasks.pop(task_id, None)
        logger.info(f"Task {task_id} cancelled successfully")
        return True

    def get_running_tasks(self) -> list[int]:
        """获取所有运行中的任务 ID。"""
        return list(self.running_tasks.keys())

    async def execute_task_now(self, task_id: int) -> None:
        """手动触发一次任务执行。"""
        async for session in db.get_session():
            repo = TaskRepository(session)
            task = await repo.get_by_id(task_id)
            if not task:
                return

        if task_id not in self.running_tasks:
            coro = asyncio.create_task(self._execute_task(task))
            self.running_tasks[task_id] = RunningTaskState(task=coro)

    async def cleanup_orphan_executions(self) -> None:
        """启动时将遗留 RUNNING 执行记录标记为 CANCELLED。"""
        async for session in db.get_session():
            repo = ExecutionRepository(session)
            await repo.cancel_orphan_running(
                finished_at=utc_now(),
                error="Server restarted, execution state unknown",
            )
            # session 由 get_session() 自动 commit
        logger.info("Cleaned up orphan RUNNING execution records")

    async def _schedule_loop(self) -> None:
        """运行带指数退避的主调度循环。"""
        consecutive_errors = 0

        while not self.should_stop:
            try:
                async for session in db.get_session():
                    repo = TaskRepository(session)

                    # 只查询已经到达计划运行时间的任务。
                    current_time = utc_now()
                    tasks = await repo.get_due_tasks(current_time)

                    for task in tasks:
                        if task.id not in self.running_tasks:
                            scheduled_at = task.next_run_time or current_time
                            task.next_run_time = self._calculate_next_run_time(
                                task.cron_expression,
                                scheduled_at,
                                current_time,
                            )
                            await repo.update(task)
                            coro = asyncio.create_task(self._execute_task(task))
                            self.running_tasks[task.id] = RunningTaskState(task=coro)

                # 新建任务可能没有 next_run_time，需要补算下一次运行时间。
                async for session in db.get_session():
                    repo = TaskRepository(session)
                    tasks_no_time = await repo.get_active_without_next_run_time()
                    for task in tasks_no_time:
                        await self._update_next_run_time(
                            task.id,
                            task.cron_expression,
                            utc_now(),
                            utc_now(),
                        )

                # 清理已经完成的内存任务引用。
                finished = [
                    tid for tid, state in self.running_tasks.items() if state.task.done()
                ]
                for tid in finished:
                    del self.running_tasks[tid]

                consecutive_errors = 0
                await asyncio.sleep(30)

            except Exception as e:
                consecutive_errors += 1
                wait = min(30 * (2**consecutive_errors), 300)
                logger.error(
                    f"Scheduler error (attempt {consecutive_errors}, "
                    f"next retry in {wait}s): {e}",
                    exc_info=True,
                )
                await asyncio.sleep(wait)

    async def _run_process(self, task: Task):
        """异步执行任务命令。"""
        process = await asyncio.create_subprocess_shell(
            task.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        running_task = self.running_tasks.get(task.id)
        if running_task is not None:
            running_task.process = process

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=task.timeout
            )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            await self._terminate_process(task.id, process)
            raise
        finally:
            running_task = self.running_tasks.get(task.id)
            if running_task is not None and running_task.process is process:
                running_task.process = None

        return type(
            "ProcessResult",
            (),
            {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace") if stdout else "",
                "stderr": stderr.decode("utf-8", errors="replace") if stderr else "",
            },
        )()

    async def _terminate_process(
        self,
        task_id: int,
        process: asyncio.subprocess.Process | None,
    ) -> None:
        """终止任务子进程组。"""
        if process is None or process.returncode is not None:
            return

        try:
            # create_subprocess_shell 使用 start_new_session 后可按进程组清理派生进程。
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except Exception as exc:
            logger.warning(f"Failed to terminate process group for task {task_id}: {exc}")

        try:
            await asyncio.wait_for(process.wait(), timeout=5)
            return
        except asyncio.TimeoutError:
            logger.warning(f"Process group for task {task_id} did not exit, killing")

        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except Exception as exc:
            logger.error(f"Failed to kill process group for task {task_id}: {exc}")

        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(process.wait(), timeout=5)

    async def _update_execution_status(
        self,
        execution_id: int,
        status: str,
        output: str = None,
        error: str = None,
    ) -> None:
        """更新执行记录状态。"""
        async for session in db.get_session():
            repo = ExecutionRepository(session)
            execution = await repo.get_by_id(execution_id)
            if execution:
                execution.finished_at = utc_now()
                execution.status = status
                if output is not None:
                    execution.output = output
                if error is not None:
                    execution.error = error
                if execution.started_at:
                    duration = (
                        execution.finished_at - execution.started_at
                    ).total_seconds()
                    execution.duration = int(duration)
                await repo.update(execution)
                # session 由 get_session() 自动 commit

    def _calculate_next_run_time(
        self,
        cron_expression: str,
        base_time: datetime,
        minimum_time: datetime | None = None,
    ) -> datetime:
        """按计划时间计算下一次运行时间。"""
        cron = croniter(cron_expression, base_time)
        next_run_time = cron.get_next(datetime)
        if minimum_time is None:
            return next_run_time

        # 服务停顿或任务长时间未调度时，跳过已经过期的计划点，避免恢复后重复补跑。
        while next_run_time <= minimum_time:
            next_run_time = cron.get_next(datetime)
        return next_run_time

    async def _update_next_run_time(
        self,
        task_id: int,
        cron_expression: str,
        base_time: datetime,
        minimum_time: datetime | None = None,
    ) -> None:
        """更新任务下一次运行时间。"""
        try:
            async for session in db.get_session():
                repo = TaskRepository(session)
                task = await repo.get_by_id(task_id)
                if task:
                    task.next_run_time = self._calculate_next_run_time(
                        cron_expression,
                        base_time,
                        minimum_time,
                    )
                    await repo.update(task)
                    # session 由 get_session() 自动 commit
        except Exception as e:
            logger.error(f"Error updating next_run_time for task {task_id}: {e}")

    async def _execute_task(self, task: Task) -> None:
        """执行单个任务并按配置重试。"""
        max_attempts = task.retry_count + 1

        for attempt in range(max_attempts):
            execution_id = None
            try:
                # 每次尝试都创建独立执行记录，便于审计重试过程。
                async for session in db.get_session():
                    repo = ExecutionRepository(session)
                    execution = TaskExecution(
                        task_id=task.id,
                        started_at=utc_now(),
                        status=ExecutionStatus.RUNNING.value,
                        retry_attempt=attempt,
                    )
                    created_execution = await repo.create(execution)
                    # session 由 get_session() 自动 commit
                    execution_id = created_execution.id
                    running_task = self.running_tasks.get(task.id)
                    if running_task is not None:
                        running_task.execution_id = execution_id

                # 异步执行命令，避免阻塞调度循环。
                proc_result = await self._run_process(task)

                status = (
                    ExecutionStatus.SUCCESS.value
                    if proc_result.returncode == 0
                    else ExecutionStatus.FAILED.value
                )

                await self._update_execution_status(
                    execution_id, status, proc_result.stdout, proc_result.stderr
                )

                if status == ExecutionStatus.SUCCESS.value:
                    await self._send_notifications(task, status, proc_result.stdout)
                    return

                # 失败后按任务重试配置决定是否再次执行。
                if attempt < task.retry_count:
                    logger.warning(
                        f"Task {task.id} failed, retrying in {task.retry_interval}s "
                        f"(attempt {attempt + 1}/{task.retry_count})"
                    )
                    await asyncio.sleep(task.retry_interval)
                    continue

                # 重试次数耗尽后发送失败通知。
                logger.error(f"Task {task.id} failed, max retries reached")
                await self._send_notifications(task, status, proc_result.stdout)
                return

            except asyncio.TimeoutError:
                if execution_id:
                    await self._update_execution_status(
                        execution_id,
                        ExecutionStatus.TIMEOUT.value,
                        error=f"Task execution timeout after {task.timeout} seconds",
                    )

                if attempt < task.retry_count:
                    logger.warning(
                        f"Task {task.id} timeout, retrying in {task.retry_interval}s "
                        f"(attempt {attempt + 1}/{task.retry_count})"
                    )
                    await asyncio.sleep(task.retry_interval)
                    continue

                logger.error(f"Task {task.id} timeout, max retries reached")
                await self._send_notifications(
                    task, ExecutionStatus.TIMEOUT.value, ""
                )
                return

            except asyncio.CancelledError:
                logger.info(f"Task {task.id} execution was cancelled")
                if execution_id:
                    await self._update_execution_status(
                        execution_id,
                        ExecutionStatus.CANCELLED.value,
                        error="Task cancelled by user",
                    )
                raise

            except Exception as e:
                if execution_id:
                    await self._update_execution_status(
                        execution_id, ExecutionStatus.FAILED.value, error=str(e)
                    )

                if attempt < task.retry_count:
                    logger.warning(
                        f"Task {task.id} error: {e}, retrying in {task.retry_interval}s "
                        f"(attempt {attempt + 1}/{task.retry_count})"
                    )
                    await asyncio.sleep(task.retry_interval)
                    continue

                logger.error(
                    f"Task {task.id} error: {e}, max retries reached", exc_info=True
                )
                await self._send_notifications(
                    task, ExecutionStatus.FAILED.value, ""
                )
                return

    async def _send_notifications(self, task: Task, status: str, output: str) -> None:
        """根据通知策略发送任务通知。"""
        notify_strategy = getattr(task, "notify_strategy", "never")

        should_notify = False
        if notify_strategy == "always":
            should_notify = True
        elif notify_strategy == "on_failure":
            should_notify = status in ["failed", "timeout", "cancelled"]

        if not should_notify:
            return

        if not task.notification_ids:
            return

        async for session in db.get_session():
            repo = NotificationRepository(session)
            notifications = await repo.get_by_ids(task.notification_ids)

            message = (
                f"Task Execution Report\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Task: {task.name}\n"
                f"ID: {task.id}\n"
                f"Status: {status}\n"
                f"Output:\n{output}"
            )

            for notif in notifications:
                try:
                    config = (
                        notif.config
                        if isinstance(notif.config, dict)
                        else json.loads(notif.config)
                    )
                    await self._notifier_service.send_notification(notif.notify_type, config, message)
                    logger.info(
                        f"Notification sent for task {task.id} via {notif.notify_type}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notification for task {task.id} "
                        f"via {notif.notify_type}: {e}",
                        exc_info=True,
                    )


scheduler_service = SchedulerService()
"""全局任务调度服务实例。"""
