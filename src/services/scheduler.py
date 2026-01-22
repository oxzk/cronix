import asyncio
import subprocess
import shutil
import textwrap
from datetime import datetime, timezone
from croniter import croniter
from typing import Dict, Optional
import json
from sqlalchemy import select
from src.databases import db
from src.models import Task, TaskExecution, Notification
from src.models.schemas import ExecutionStatus
from src.services.notifiers import send_notification
from src.utils import logger


class TaskScheduler:
    def __init__(self):
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.running_processes: Dict[int, subprocess.Popen] = {}  # 存储正在运行的进程
        self.should_stop = False
        self._uv_available: Optional[bool] = None

    def _check_uv_available(self) -> bool:
        """检查 uv 是否可用"""
        if self._uv_available is None:
            self._uv_available = shutil.which("uv") is not None
            if self._uv_available:
                logger.info("UV detected, will use 'uv python run' for Python tasks")
            else:
                logger.info("UV not found, will use 'python' for Python tasks")
        return self._uv_available

    async def start(self) -> None:
        """Start the scheduler"""
        self.should_stop = False
        await self._schedule_loop()

    async def stop(self) -> None:
        """Stop the scheduler and cancel all running tasks"""
        logger.info("Stopping scheduler...")
        self.should_stop = True

        # Cancel all running tasks
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)

        logger.info("Scheduler stopped")

    async def cancel_task(self, task_id: int) -> bool:
        """取消正在运行的任务"""
        if task_id in self.running_tasks:
            # 取消 asyncio 任务
            self.running_tasks[task_id].cancel()

            # 终止进程（如果存在）
            if task_id in self.running_processes:
                try:
                    process = self.running_processes[task_id]
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()  # 强制杀死
                    del self.running_processes[task_id]
                except Exception as e:
                    logger.error(f"Error terminating process for task {task_id}: {e}")

            # 更新执行记录
            try:
                async for session in db.get_session():
                    result = await session.execute(
                        select(TaskExecution)
                        .where(TaskExecution.task_id == task_id)
                        .where(TaskExecution.status == ExecutionStatus.RUNNING.value)
                        .order_by(TaskExecution.started_at.desc())
                        .limit(1)
                    )
                    execution = result.scalar_one_or_none()
                    if execution:
                        execution.finished_at = datetime.now(timezone.utc)
                        execution.status = ExecutionStatus.CANCELLED.value
                        execution.error = "Task cancelled by user"
                        await session.commit()
            except Exception as e:
                logger.error(f"Error updating execution record: {e}")

            del self.running_tasks[task_id]
            logger.info(f"Task {task_id} cancelled successfully")
            return True
        return False

    def get_running_tasks(self) -> list[int]:
        """获取所有正在运行的任务 ID"""
        return list(self.running_tasks.keys())

    async def _schedule_loop(self) -> None:
        """Main scheduling loop"""
        while not self.should_stop:
            try:
                async for session in db.get_session():
                    result = await session.execute(
                        select(Task).where(Task.is_active == True)
                    )
                    tasks = result.scalars().all()
                    current_time = datetime.now(timezone.utc)

                    for task in tasks:
                        if await self._should_run(task, current_time):
                            if task.id not in self.running_tasks:
                                task_coro = asyncio.create_task(
                                    self._execute_task(task)
                                )
                                self.running_tasks[task.id] = task_coro

                    # Clean up finished tasks
                    finished = [
                        tid for tid, t in self.running_tasks.items() if t.done()
                    ]
                    for tid in finished:
                        del self.running_tasks[tid]

                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                await asyncio.sleep(30)

    def _run_process(
        self, task: Task, cmd: list | str, shell: bool = False
    ) -> subprocess.CompletedProcess:
        """运行进程并管理其生命周期"""
        process = subprocess.Popen(
            cmd,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.running_processes[task.id] = process
        try:
            stdout, stderr = process.communicate(timeout=task.timeout)
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        finally:
            if task.id in self.running_processes:
                del self.running_processes[task.id]

    def _get_command(self, task: Task) -> tuple[list | str, bool]:
        """根据任务类型获取命令和是否使用 shell"""
        if task.execution_type == "shell":
            return task.command, True
        elif task.execution_type == "python":
            cleaned_command = textwrap.dedent(task.command).strip()
            if self._check_uv_available():
                return ["uv", "python", "run", "-c", cleaned_command], False
            else:
                return ["python", "-c", cleaned_command], False
        elif task.execution_type == "node":
            return ["node", "-e", task.command], False
        else:
            raise ValueError(f"Unknown execution type: {task.execution_type}")

    async def _update_execution_status(
        self,
        execution_id: int,
        status: str,
        output: str = None,
        error: str = None,
    ) -> None:
        """更新执行记录状态"""
        async for session in db.get_session():
            result = await session.execute(
                select(TaskExecution).where(TaskExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            if execution:
                execution.finished_at = datetime.now(timezone.utc)
                execution.status = status
                if output is not None:
                    execution.output = output
                if error is not None:
                    execution.error = error
                await session.commit()

    def _cleanup_process(self, task_id: int) -> None:
        """清理正在运行的进程"""
        if task_id in self.running_processes:
            try:
                self.running_processes[task_id].kill()
                del self.running_processes[task_id]
            except Exception:
                pass

    async def _handle_retry(self, task: Task, retry_attempt: int, reason: str) -> None:
        """处理任务重试逻辑"""
        if retry_attempt < task.retry_count:
            logger.warning(
                f"Task {task.id} {reason}, retrying in {task.retry_interval}s "
                f"(attempt {retry_attempt + 1}/{task.retry_count})"
            )
            await asyncio.sleep(task.retry_interval)
            await self._execute_task(task, retry_attempt + 1)
        else:
            logger.error(f"Task {task.id} {reason}, max retries reached", exc_info=True)

    async def _should_run(self, task: Task, current_time: datetime) -> bool:
        """Check if task should run based on cron expression"""
        try:
            cron = croniter(task.cron_expression, current_time)
            prev_run = cron.get_prev(datetime)

            # Check if there's a recent execution
            async for session in db.get_session():
                result = await session.execute(
                    select(TaskExecution)
                    .where(TaskExecution.task_id == task.id)
                    .order_by(TaskExecution.started_at.desc())
                    .limit(1)
                )
                last_exec = result.scalar_one_or_none()

                if last_exec is None:
                    return True

                # Run if the previous cron time is after the last execution
                return prev_run > last_exec.started_at
        except Exception as e:
            logger.error(f"Error checking cron for task {task.id}: {e}", exc_info=True)
            return False

    async def _execute_task(self, task: Task, retry_attempt: int = 0) -> None:
        """Execute a single task"""
        execution_id = None
        try:
            # Create execution record
            async for session in db.get_session():
                execution = TaskExecution(
                    task_id=task.id,
                    started_at=datetime.now(timezone.utc),
                    status=ExecutionStatus.RUNNING.value,
                    retry_attempt=retry_attempt,
                )
                session.add(execution)
                await session.commit()
                await session.refresh(execution)
                execution_id = execution.id

            # Execute command
            cmd, shell = self._get_command(task)
            proc_result = self._run_process(task, cmd, shell)

            status = (
                ExecutionStatus.SUCCESS.value
                if proc_result.returncode == 0
                else ExecutionStatus.FAILED.value
            )

            # Update execution record
            await self._update_execution_status(
                execution_id, status, proc_result.stdout, proc_result.stderr
            )

            # Retry logic if failed
            if (
                status == ExecutionStatus.FAILED.value
                and retry_attempt < task.retry_count
            ):
                await self._handle_retry(task, retry_attempt, "failed")
                return

            # Send notifications
            await self._send_notifications(task, status, proc_result.stdout)

        except subprocess.TimeoutExpired:
            self._cleanup_process(task.id)
            if execution_id:
                await self._update_execution_status(
                    execution_id,
                    ExecutionStatus.TIMEOUT.value,
                    error=f"Task execution timeout after {task.timeout} seconds",
                )
            await self._handle_retry(task, retry_attempt, "timeout")

        except asyncio.CancelledError:
            logger.info(f"Task {task.id} execution was cancelled")
            self._cleanup_process(task.id)
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
            await self._handle_retry(task, retry_attempt, f"error: {e}")

    async def _send_notifications(self, task: Task, status: str, output: str) -> None:
        """发送任务通知"""
        if not task.notification_ids:
            return  # 没有配置通知，直接返回

        async for session in db.get_session():
            # 获取通知配置详情
            result = await session.execute(
                select(Notification).where(Notification.id.in_(task.notification_ids))
            )
            notifications = result.scalars().all()

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
                    await send_notification(notif.notify_type, config, message)
                    logger.info(
                        f"Notification sent for task {task.id} via {notif.notify_type}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notification for task {task.id} "
                        f"via {notif.notify_type}: {e}",
                        exc_info=True,
                    )


scheduler = TaskScheduler()
