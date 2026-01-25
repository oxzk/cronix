import asyncio
import subprocess
from datetime import datetime, timezone
from croniter import croniter
from typing import Dict
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
        self.running_processes: Dict[int, subprocess.Popen] = (
            {}
        )  # Store running processes
        self.should_stop = False

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
        """Cancel a running task"""
        if task_id in self.running_tasks:
            # Cancel asyncio task
            self.running_tasks[task_id].cancel()

            # Terminate process (if exists)
            if task_id in self.running_processes:
                try:
                    process = self.running_processes[task_id]
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()  # Force kill
                    del self.running_processes[task_id]
                except Exception as e:
                    logger.error(f"Error terminating process for task {task_id}: {e}")

            # Update execution record
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
        """Get all running task IDs"""
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

    def _run_process(self, task: Task) -> subprocess.CompletedProcess:
        """Run process and manage its lifecycle"""
        process = subprocess.Popen(
            task.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.running_processes[task.id] = process
        try:
            stdout, stderr = process.communicate(timeout=task.timeout)
            return subprocess.CompletedProcess(
                args=task.command,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        finally:
            if task.id in self.running_processes:
                del self.running_processes[task.id]

    async def _update_execution_status(
        self,
        execution_id: int,
        status: str,
        output: str = None,
        error: str = None,
    ) -> None:
        """Update execution record status"""
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
                # Calculate duration in seconds
                if execution.started_at:
                    duration = (
                        execution.finished_at - execution.started_at
                    ).total_seconds()
                    execution.duration = int(duration)
                await session.commit()

    async def _update_next_run_time(self, task_id: int, cron_expression: str) -> None:
        """Update task's next run time"""
        try:
            async for session in db.get_session():
                result = await session.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    cron = croniter(cron_expression, datetime.now(timezone.utc))
                    task.next_run_time = cron.get_next(datetime)
                    await session.commit()
        except Exception as e:
            logger.error(f"Error updating next_run_time for task {task_id}: {e}")

    def _cleanup_process(self, task_id: int) -> None:
        """Clean up running process"""
        if task_id in self.running_processes:
            try:
                self.running_processes[task_id].kill()
                del self.running_processes[task_id]
            except Exception:
                pass

    async def _handle_retry(self, task: Task, retry_attempt: int, reason: str) -> None:
        """Handle task retry logic"""
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
            proc_result = self._run_process(task)

            status = (
                ExecutionStatus.SUCCESS.value
                if proc_result.returncode == 0
                else ExecutionStatus.FAILED.value
            )

            # Update execution record and next_run_time
            await self._update_execution_status(
                execution_id, status, proc_result.stdout, proc_result.stderr
            )

            # Update next_run_time after successful execution
            if status == ExecutionStatus.SUCCESS.value:
                await self._update_next_run_time(task.id, task.cron_expression)

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
        """Send task notifications"""
        if not task.notification_ids:
            return  # No notifications configured, return early

        async for session in db.get_session():
            # Get notification configuration details
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
