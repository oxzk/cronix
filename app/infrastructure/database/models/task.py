"""tasks 表: 定时任务定义(命令可内联或引用脚本)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, TimestampMixin

DEFAULT_NOTIFICATION_CONFIG: dict = {"enabled": False, "events": [], "channels": []}


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("timeout IS NULL OR timeout > 0", name="timeout_positive"),
        CheckConstraint("max_retries >= 0", name="max_retries_non_negative"),
        CheckConstraint("retry_delay > 0", name="retry_delay_positive"),
        CheckConstraint("command IS NOT NULL OR script_id IS NOT NULL", name="command_or_script"),
        Index("ix_tasks_due", "enabled", "next_run_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("scripts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    cron: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    timeout: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_delay: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    notification_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=DEFAULT_NOTIFICATION_CONFIG, server_default=text("'{}'::jsonb")
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
