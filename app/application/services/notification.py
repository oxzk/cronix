"""NotificationService: 执行终态与监控状态变化 → Pusho 推送。"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Literal

from loguru import logger

from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.http.pusho import PushoClient
from app.runtime.event import Event
from app.runtime.logger import redact_text

TERMINAL_EVENTS = {"run.completed", "run.failed", "run.timeout"}
MONITOR_EVENTS = {"monitor.down", "monitor.up"}
STATUS_LABELS = {0: "排队", 1: "运行中", 2: "成功", 3: "失败", 4: "已取消", 5: "超时"}


class NotificationService:
    """接收任务与监控事件并通过 Pusho 发送通知."""

    def __init__(
        self,
        session_factory,  # type: ignore[no-untyped-def]
        runtime_state,  # type: ignore[no-untyped-def]
    ) -> None:
        self._session_factory = session_factory
        self._runtime_state = runtime_state

    # ---- 事件入口 ----

    async def handle_event(self, event: Event) -> None:
        if event.type in TERMINAL_EVENTS and event.task_id is not None:
            asyncio.create_task(self._dispatch(event), name=f"cronix-notify-{event.run_id}")
            return
        if event.type in MONITOR_EVENTS and event.monitor_id is not None:
            asyncio.create_task(
                self._dispatch_monitor(event), name=f"cronix-notify-monitor-{event.monitor_id}"
            )

    # ---- 任务执行通知 ----

    async def _dispatch(self, event: Event) -> None:
        try:
            async with UnitOfWork(self._session_factory) as uow:
                task = await uow.tasks.get(uuid.UUID(event.task_id))
                if task is None:
                    return
                config = task.notification_config or {}
                task_name = task.name
            if not config.get("enabled"):
                return
            if event.type not in (config.get("events") or []):
                return

            pusho = await self._pusho_config()
            if not pusho["api_key"] or not pusho["project"]:
                logger.debug("Pusho 未配置, 跳过通知", task_id=event.task_id)
                return
            payload = self._task_payload(event, task_name)
            await self._send(
                pusho,
                title=f"cronix · 任务{payload['status_label']}",
                content=self._task_text(payload),
                idempotency_key=f"cronix-run-{event.run_id}-{event.type.split('.')[-1]}",
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                f"通知发送失败: {type(exc).__name__}: {redact_text(str(exc))}",
                run_id=event.run_id,
            )

    @staticmethod
    def _task_payload(event: Event, task_name: str) -> dict:  # type: ignore[type-arg]
        status = event.data.get("status")
        return {
            "event": event.type,
            "task_id": event.task_id,
            "task_name": task_name,
            "run_id": event.run_id,
            "status": status,
            "status_label": STATUS_LABELS.get(status if isinstance(status, int) else -1, str(status)),
            "exit_code": event.data.get("exit_code"),
            "error_code": event.data.get("error_code"),
            "error_message": event.data.get("error_message"),
            "duration_ms": event.data.get("duration_ms"),
            "timestamp": event.timestamp.isoformat(),
        }

    @staticmethod
    def _task_text(payload: dict) -> str:  # type: ignore[type-arg]
        lines = [
            f"任务: {payload['task_name']}",
            f"事件: {payload['event']}",
        ]
        if payload.get("exit_code") is not None:
            lines.append(f"退出码: {payload['exit_code']}")
        if payload.get("error_message"):
            lines.append(f"错误: {payload['error_message']}")
        lines.append(f"耗时: {payload['duration_ms']}ms")
        lines.append(f"时间: {_format_time(payload['timestamp'])}")
        return "\n".join(lines)

    # ---- 监控状态通知 ----

    async def _dispatch_monitor(self, event: Event) -> None:
        """按监控通知配置发送异常或恢复消息."""
        try:
            async with UnitOfWork(self._session_factory) as uow:
                monitor = await uow.monitors.get(uuid.UUID(event.monitor_id))
                if monitor is None:
                    return
                config = monitor.notification_config or {}
                monitor_name = monitor.name
                kind = monitor.kind
            if not config.get("enabled"):
                return
            if event.type not in (config.get("events") or []):
                return

            pusho = await self._pusho_config()
            if not pusho["api_key"] or not pusho["project"]:
                logger.debug("Pusho 未配置, 跳过通知", monitor_id=event.monitor_id)
                return
            payload = {
                "event": event.type,
                "monitor_id": event.monitor_id,
                "monitor_name": monitor_name,
                "kind": kind,
                "status": event.data.get("status"),
                "latency_ms": event.data.get("latency_ms"),
                "error_code": event.data.get("error_code"),
                "error_message": event.data.get("error_message"),
                "consecutive_failures": event.data.get("consecutive_failures"),
                "timestamp": event.timestamp.isoformat(),
            }
            await self._send(
                pusho,
                # 完整标题由正文模板提供, 避免 Pusho 再拼接一层标题格式.
                title="",
                content=self._monitor_text(payload),
                content_type="markdown",
                idempotency_key=(
                    f"cronix-monitor-{event.monitor_id}-{int(event.timestamp.timestamp())}"
                ),
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                f"监控通知发送失败: {type(exc).__name__}: {redact_text(str(exc))}",
                monitor_id=event.monitor_id,
            )

    @staticmethod
    def _monitor_text(payload: dict) -> str:  # type: ignore[type-arg]
        """生成监控异常或恢复通知的完整 Markdown 模板."""
        is_down = payload["event"] == "monitor.down"
        lines = [
            "🔴 *cronix · 监控异常*" if is_down else "🟢 *cronix · 监控恢复*",
            "",
            _markdown_bold(payload["monitor_name"]),
            "",
            "━━━━━━━━━━━━━━",
            "",
        ]
        if is_down:
            if payload.get("error_message"):
                lines.append(f"⚠️ 原因：{_escape_markdown(payload['error_message'])}")
        elif payload.get("latency_ms") is not None:
            lines.append(f"📶 响应：`{payload['latency_ms']} ms`")
        lines.append(f"📅 时间：`{_format_time(payload['timestamp'])}`")
        return "\n".join(lines)

    # ---- 渠道 ----

    async def _pusho_config(self) -> dict:  # type: ignore[type-arg]
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("notification", "pusho")
        value = (row.value if row else {}) or {}
        return {
            "api_url": str(value.get("api_url") or "").rstrip("/"),
            "api_key": str(value.get("api_key") or ""),
            "project": str(value.get("project") or ""),
        }

    async def _send(
        self,
        config: dict,  # type: ignore[type-arg]
        *,
        title: str,
        content: str,
        idempotency_key: str,
        content_type: Literal["text", "markdown"] = "text",
    ) -> None:
        """按指定内容格式发送通知并应用运行时超时配置."""
        if not config["api_url"]:
            return
        client = PushoClient(config["api_url"], config["api_key"])
        await client.send(
            project=config["project"],
            title=title,
            content=content,
            content_type=content_type,
            timeout=self._runtime_state.notify_timeout,
            idempotency_key=idempotency_key,
        )


def _markdown_bold(text: str) -> str:
    """使用 Telegram 旧版 Markdown 加粗监控名称并保留字面星号."""
    # 旧版 Markdown 不允许在加粗实体内转义, 遇到星号需闭合实体后再开启.
    return r"\*".join(f"*{part}*" if part else "" for part in text.split("*"))


def _escape_markdown(text: str) -> str:
    """转义原因文本中的 Markdown 标记, 保持错误信息原样展示."""
    return text.translate(str.maketrans({char: "\\" + char for char in "_*`["}))


def _format_time(timestamp: str) -> str:
    try:
        return datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return timestamp
