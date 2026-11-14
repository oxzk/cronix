"""MonitorService: 监控 CRUD、周期检查、卡片聚合、状态翻转事件。"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import replace
from datetime import timedelta
from typing import Any

from loguru import logger

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.monitoring import (
    SUPPORTED_KINDS,
    merge_redacted,
    redact_connection_error,
    validate_config,
)
from app.core.utils import utc_now
from app.infrastructure.database.models.monitor import Monitor
from app.infrastructure.database.models.monitor_check import MonitorCheck
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.monitoring.base import CheckResult, MonitorStatus
from app.infrastructure.monitoring.registry import get_checker
from app.runtime.event import Event, EventBus

MAX_CONCURRENT_CHECKS = 8
MIN_INTERVAL_SECONDS = 5
MAX_INTERVAL_SECONDS = 86400
MAX_TIMEOUT_SECONDS = 60

MONITOR_NOTIFICATION_EVENTS = {"monitor.down", "monitor.up"}


class MonitorService:
    def __init__(self, session_factory, events: EventBus) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory
        self._events = events
        self._slots = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)
        self._jobs: set[asyncio.Task] = set()  # type: ignore[type-arg]
        self._locks: dict[uuid.UUID, asyncio.Lock] = {}

    # ---- 查询 ----

    async def list_cards(self) -> list[dict]:
        since = utc_now() - timedelta(hours=24)
        async with UnitOfWork(self._session_factory) as uow:
            monitors = await uow.monitors.list_all()
            uptime_rows = await uow.monitor_checks.uptime_since(since)
            recent = await uow.monitor_checks.recent_checks(30)
        cards: list[dict] = []
        for monitor in monitors:
            total, up = uptime_rows.get(monitor.id, (0, 0))
            uptime = round(up / total * 100, 2) if total else None
            cards.append(
                {
                    "id": monitor.id,
                    "name": monitor.name,
                    "kind": monitor.kind,
                    "config": monitor.config or {},
                    "interval_seconds": monitor.interval_seconds,
                    "timeout_seconds": monitor.timeout_seconds,
                    "enabled": monitor.enabled,
                    "notification_config": monitor.notification_config or {},
                    "next_check_at": monitor.next_check_at,
                    "last_status": monitor.last_status,
                    "last_latency_ms": monitor.last_latency_ms,
                    "last_checked_at": monitor.last_checked_at,
                    "last_issue_at": monitor.last_issue_at,
                    "consecutive_failures": monitor.consecutive_failures,
                    "created_at": monitor.created_at,
                    "updated_at": monitor.updated_at,
                    "uptime_24h": uptime,
                    "recent_checks": recent.get(monitor.id, []),
                }
            )
        return cards

    async def get(self, monitor_id: uuid.UUID) -> Monitor:
        async with UnitOfWork(self._session_factory) as uow:
            monitor = await uow.monitors.get(monitor_id)
        if monitor is None:
            raise NotFoundError("监控项不存在")
        return monitor

    async def list_checks(
        self, monitor_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[MonitorCheck], int]:
        async with UnitOfWork(self._session_factory) as uow:
            monitor = await uow.monitors.get(monitor_id)
            if monitor is None:
                raise NotFoundError("监控项不存在")
            return await uow.monitor_checks.list_paginated(monitor_id, page, page_size)

    # ---- 写 ----

    async def create(self, values: dict) -> Monitor:
        name = self._clean_name(values)
        kind = self._clean_kind(values)
        config = validate_config(kind, values.get("config") or {})
        interval = self._interval(values)
        timeout = self._timeout(values)
        enabled = bool(values.get("enabled", True))
        notification = self._normalize_notification(values.get("notification_config"))
        monitor = Monitor(
            name=name,
            kind=kind,
            config=config,
            interval_seconds=interval,
            timeout_seconds=timeout,
            enabled=enabled,
            notification_config=notification,
            next_check_at=utc_now() if enabled else None,
        )
        async with UnitOfWork(self._session_factory) as uow:
            await uow.monitors.add(monitor)
        logger.info("监控项已创建", monitor_id=str(monitor.id), name=name, kind=kind)
        return monitor

    async def update(self, monitor_id: uuid.UUID, values: dict) -> Monitor:
        reschedule = False
        async with UnitOfWork(self._session_factory) as uow:
            monitor = await uow.monitors.get(monitor_id)
            if monitor is None:
                raise NotFoundError("监控项不存在")
            if "name" in values:
                monitor.name = self._clean_name(values)
            previous_kind = monitor.kind
            if "kind" in values:
                kind = self._clean_kind(values)
                if kind != monitor.kind:
                    if "config" not in values:
                        raise ValidationError("修改监控类型时必须提供对应的连接配置")
                    monitor.kind = kind
                    reschedule = True
            if "config" in values:
                saved = monitor.config if monitor.kind == previous_kind else None
                merged = merge_redacted(monitor.kind, saved, values.get("config") or {})
                monitor.config = validate_config(monitor.kind, merged)
                reschedule = True
            if "interval_seconds" in values:
                interval = self._interval(values)
                if interval != monitor.interval_seconds:
                    reschedule = True
                monitor.interval_seconds = interval
            if "timeout_seconds" in values:
                monitor.timeout_seconds = self._timeout(values)
            if "enabled" in values:
                enabled = bool(values.get("enabled"))
                if enabled != monitor.enabled:
                    reschedule = True
                monitor.enabled = enabled
            if "notification_config" in values:
                monitor.notification_config = self._normalize_notification(values.get("notification_config"))
            if not monitor.enabled:
                monitor.next_check_at = None
            elif reschedule:
                monitor.next_check_at = utc_now()
        return monitor

    async def delete(self, monitor_id: uuid.UUID) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            monitor = await uow.monitors.get(monitor_id)
            if monitor is None:
                raise NotFoundError("监控项不存在")
            await uow.monitors.delete(monitor)
        logger.info("监控项已删除", monitor_id=str(monitor_id))

    # ---- 检查 ----

    async def check_now(self, monitor_id: uuid.UUID) -> dict:
        lock = self._locks.setdefault(monitor_id, asyncio.Lock())
        if lock.locked():
            # 同一监控避免并发检查(定时与手动重叠会导致重复状态翻转)
            raise ConflictError("该监控正在检查中")
        async with self._slots:
            async with lock:
                return await self._run_check(monitor_id)

    def schedule_check(self, monitor_id: uuid.UUID) -> None:
        task = asyncio.create_task(self._guarded_check(monitor_id), name=f"cronix-monitor-{monitor_id}")
        self._jobs.add(task)
        task.add_done_callback(self._jobs.discard)

    async def close(self) -> None:
        jobs = list(self._jobs)
        for job in jobs:
            job.cancel()
        if jobs:
            _, pending = await asyncio.wait(jobs, timeout=5)
            for job in pending:
                job.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

    async def _guarded_check(self, monitor_id: uuid.UUID) -> None:
        try:
            await self.check_now(monitor_id)
        except asyncio.CancelledError:
            raise
        except ConflictError:
            logger.debug("监控检查重叠, 已跳过", monitor_id=str(monitor_id))
        except Exception:
            logger.exception("监控检查失败", monitor_id=str(monitor_id))

    async def _run_check(self, monitor_id: uuid.UUID) -> dict:
        """执行监控检查, 保存结果并发布状态变化事件."""
        async with UnitOfWork(self._session_factory) as uow:
            monitor = await uow.monitors.get(monitor_id)
            if monitor is None:
                raise NotFoundError("监控项不存在")
            kind = monitor.kind
            config = dict(monitor.config or {})
            timeout = monitor.timeout_seconds

        checker = get_checker(kind)
        started = time.perf_counter()
        try:
            async with asyncio.timeout(timeout):
                validated = validate_config(kind, config)
                result = await checker.check(validated, timeout)
        except TimeoutError:
            result = CheckResult(MonitorStatus.DOWN, "timeout", f"检查超时（{timeout}s）")
        except ValidationError as exc:
            result = CheckResult(MonitorStatus.DOWN, "config_error", str(exc))
        except Exception as exc:
            result = CheckResult(MonitorStatus.DOWN, "internal_error", f"{type(exc).__name__}: {exc}")
        result = replace(
            result,
            error_message=redact_connection_error(kind, config, result.error_message),
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        checked_at = utc_now()

        transition: str | None = None
        event_data: dict[str, Any] = {}
        async with UnitOfWork(self._session_factory) as uow:
            monitor = await uow.monitors.get(monitor_id)
            if monitor is None:
                raise NotFoundError("监控项不存在")
            previous = monitor.last_status
            check = MonitorCheck(
                monitor_id=monitor_id,
                status=int(result.status),
                latency_ms=latency_ms,
                error_code=result.error_code,
                error_message=result.error_message,
                checked_at=checked_at,
            )
            await uow.monitor_checks.add(check)
            monitor.last_status = int(result.status)
            monitor.last_latency_ms = latency_ms
            monitor.last_checked_at = checked_at
            if result.status == MonitorStatus.DOWN:
                monitor.consecutive_failures = (monitor.consecutive_failures or 0) + 1
                monitor.last_issue_at = checked_at
                if previous != int(MonitorStatus.DOWN):
                    transition = "monitor.down"
            else:
                monitor.consecutive_failures = 0
                if previous == int(MonitorStatus.DOWN):
                    transition = "monitor.up"
            monitor.next_check_at = checked_at + timedelta(seconds=monitor.interval_seconds)
            event_data = {
                "monitor_name": monitor.name,
                "kind": monitor.kind,
                "status": int(result.status),
                "latency_ms": latency_ms,
                "error_code": result.error_code,
                "error_message": result.error_message,
                "consecutive_failures": monitor.consecutive_failures,
            }
            check_id = check.id

        if transition is not None:
            await self._events.emit(Event(transition, monitor_id=str(monitor_id), data=event_data))

        return {
            "id": check_id,
            "monitor_id": monitor_id,
            "status": int(result.status),
            "latency_ms": latency_ms,
            "error_code": result.error_code,
            "error_message": result.error_message,
            "checked_at": checked_at,
        }

    # ---- 校验 ----

    @staticmethod
    def _clean_name(values: dict) -> str:
        name = str(values.get("name") or "").strip()
        if not name:
            raise ValidationError("监控名称不能为空")
        if len(name) > 255:
            raise ValidationError("监控名称不能超过 255 字符")
        return name

    @staticmethod
    def _clean_kind(values: dict) -> str:
        kind = str(values.get("kind") or "").strip()
        if kind not in SUPPORTED_KINDS:
            raise ValidationError(f"不支持的监控类型: {kind}")
        return kind

    @staticmethod
    def _interval(values: dict) -> int:
        try:
            interval = int(values.get("interval_seconds") or 60)
        except (TypeError, ValueError) as exc:
            raise ValidationError("检查间隔必须是整数") from exc
        if not MIN_INTERVAL_SECONDS <= interval <= MAX_INTERVAL_SECONDS:
            raise ValidationError(f"检查间隔必须在 {MIN_INTERVAL_SECONDS}-{MAX_INTERVAL_SECONDS} 秒之间")
        return interval

    @staticmethod
    def _timeout(values: dict) -> int:
        try:
            timeout = int(values.get("timeout_seconds") or 10)
        except (TypeError, ValueError) as exc:
            raise ValidationError("超时必须是整数") from exc
        if not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
            raise ValidationError(f"超时必须在 1-{MAX_TIMEOUT_SECONDS} 秒之间")
        return timeout

    @staticmethod
    def _normalize_notification(raw: object) -> dict:
        cfg = raw if isinstance(raw, dict) else {}
        events = [e for e in (cfg.get("events") or []) if e in MONITOR_NOTIFICATION_EVENTS]
        return {"enabled": bool(cfg.get("enabled", False)), "events": events}
