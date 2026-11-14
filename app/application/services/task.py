"""TaskService: 任务 CRUD(命令可内联或引用脚本)、cron 校验、next_run_at 维护。"""

from __future__ import annotations

import uuid

from loguru import logger

from app.core.cron import next_after, validate_cron
from app.core.exceptions import NotFoundError, ValidationError
from app.core.utils import utc_now
from app.infrastructure.database.models.task import Task
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.runtime.enums import Trigger

NOTIFICATION_EVENTS = {"run.failed", "run.timeout", "run.completed"}


class TaskService:
    def __init__(self, session_factory, executions) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory
        self._executions = executions

    async def list_paginated(
        self, page: int, page_size: int
    ) -> tuple[list[tuple[Task, str | None, int]], int]:
        async with UnitOfWork(self._session_factory) as uow:
            tasks, total = await uow.tasks.list_paginated(page, page_size)
            names = await uow.scripts.names_by_ids(
                {task.script_id for task in tasks if task.script_id is not None}
            )
            counts = await uow.task_runs.count_active_by_task({task.id for task in tasks})
        return [
            (task, names.get(task.script_id), counts.get(task.id, 0)) for task in tasks
        ], total

    async def get(self, task_id: uuid.UUID) -> tuple[Task, str | None, int]:
        async with UnitOfWork(self._session_factory) as uow:
            task = await uow.tasks.get(task_id)
            if task is None:
                raise NotFoundError("任务不存在")
            script_name = await self._script_name(uow, task.script_id)
            active = (await uow.task_runs.count_active_by_task({task.id})).get(task.id, 0)
        return task, script_name, active

    async def create(self, values: dict) -> tuple[Task, str | None]:
        name = self._clean_required(values, "name", "任务名")
        cron = str(values.get("cron") or "").strip()
        validate_cron(cron)
        enabled = bool(values.get("enabled", True))
        timeout = self._optional_positive(values, "timeout", "超时")
        max_retries = self._non_negative(values, "max_retries", "最大重试次数")
        retry_delay = self._positive(values, "retry_delay", "重试间隔")
        notification = self._normalize_notification(values.get("notification_config"))
        script_id = self._parse_script_id(values)
        command = str(values.get("command") or "").strip()
        if script_id is None and not command:
            raise ValidationError("命令不能为空")

        task = Task(
            name=name,
            command=command or None,
            script_id=script_id,
            cron=cron,
            enabled=enabled,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            notification_config=notification,
            next_run_at=next_after(cron, utc_now()) if enabled else None,
        )
        async with UnitOfWork(self._session_factory) as uow:
            script_name = await self._script_name(uow, script_id)
            await uow.tasks.add(task)
        logger.info("任务已创建", task_id=str(task.id), name=name)
        return task, script_name, 0

    async def update(self, task_id: uuid.UUID, values: dict) -> tuple[Task, str | None, int]:
        cron_changed = False
        enabled_changed = False
        async with UnitOfWork(self._session_factory) as uow:
            task = await uow.tasks.get(task_id)
            if task is None:
                raise NotFoundError("任务不存在")
            if "name" in values:
                task.name = self._clean_required(values, "name", "任务名")
            if "command" in values:
                command = str(values.get("command") or "").strip()
                task.command = command or None
            if "script_id" in values:
                task.script_id = self._parse_script_id(values)
            if "cron" in values:
                cron = str(values.get("cron") or "").strip()
                validate_cron(cron)
                cron_changed = task.cron != cron
                task.cron = cron
            if "enabled" in values:
                enabled = bool(values.get("enabled"))
                enabled_changed = task.enabled != enabled
                task.enabled = enabled
            if "timeout" in values:
                task.timeout = self._optional_positive(values, "timeout", "超时")
            if "max_retries" in values:
                task.max_retries = self._non_negative(values, "max_retries", "最大重试次数")
            if "retry_delay" in values:
                task.retry_delay = self._positive(values, "retry_delay", "重试间隔")
            if "notification_config" in values:
                task.notification_config = self._normalize_notification(values.get("notification_config"))
            if task.script_id is None and not task.command:
                raise ValidationError("命令不能为空")
            script_name = await self._script_name(uow, task.script_id)
            active = (await uow.task_runs.count_active_by_task({task.id})).get(task.id, 0)
            if not task.enabled:
                task.next_run_at = None
            elif cron_changed or enabled_changed:
                task.next_run_at = next_after(task.cron, utc_now())
        return task, script_name, active

    async def delete(self, task_id: uuid.UUID) -> None:
        # 先取消并等待在跑任务收尾, 再删除任务(避免孤儿进程/悬空写入)
        await self._executions.cancel_for_task(task_id)
        async with UnitOfWork(self._session_factory) as uow:
            task = await uow.tasks.get(task_id)
            if task is None:
                raise NotFoundError("任务不存在")
            await uow.tasks.delete(task)
        logger.info("任务已删除", task_id=str(task_id))

    async def run_now(self, task_id: uuid.UUID) -> object:
        return await self._executions.run(task_id, Trigger.MANUAL)

    async def cancel(self, task_id: uuid.UUID) -> int:
        return await self._executions.cancel_for_task(task_id)

    # ---- 内部 ----

    @staticmethod
    async def _script_name(uow: UnitOfWork, script_id: uuid.UUID | None) -> str | None:
        if script_id is None:
            return None
        script = await uow.scripts.get(script_id)
        if script is None:
            raise NotFoundError("脚本不存在")
        return script.name

    @staticmethod
    def _parse_script_id(values: dict) -> uuid.UUID | None:
        raw = values.get("script_id")
        if raw is None or raw == "":
            return None
        try:
            return uuid.UUID(str(raw))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValidationError("script_id 不合法") from exc

    @staticmethod
    def _clean_required(values: dict, field: str, label: str) -> str:
        text = str(values.get(field) or "").strip()
        if not text:
            raise ValidationError(f"{label}不能为空")
        return text

    @staticmethod
    def _optional_positive(values: dict, field: str, label: str) -> int | None:
        raw = values.get(field)
        if raw is None:
            return None
        try:
            number = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{label}必须是正整数") from exc
        if number <= 0:
            raise ValidationError(f"{label}必须大于 0")
        return number

    @staticmethod
    def _non_negative(values: dict, field: str, label: str) -> int:
        try:
            number = int(values.get(field) or 0)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{label}必须是非负整数") from exc
        if number < 0:
            raise ValidationError(f"{label}不能为负数")
        return number

    @staticmethod
    def _positive(values: dict, field: str, label: str) -> int:
        try:
            number = int(values.get(field) or 0)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{label}必须是正整数") from exc
        if number <= 0:
            raise ValidationError(f"{label}必须大于 0")
        return number

    @staticmethod
    def _normalize_notification(raw: object) -> dict:
        cfg = raw if isinstance(raw, dict) else {}
        events = [e for e in (cfg.get("events") or []) if e in NOTIFICATION_EVENTS]
        return {
            "enabled": bool(cfg.get("enabled", False)),
            "events": events,
        }
