"""monitors 表: 监控项定义与最近检查聚合。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, TimestampMixin

DEFAULT_MONITOR_NOTIFICATION_CONFIG: dict = {"enabled": False, "events": [], "channels": []}


class Monitor(TimestampMixin, Base):
    __tablename__ = "monitors"
    __table_args__ = (
        CheckConstraint("interval_seconds > 0", name="interval_positive"),
        CheckConstraint("timeout_seconds > 0", name="timeout_positive"),
        CheckConstraint("last_status IS NULL OR last_status IN (1, 2)", name="last_status_valid"),
        CheckConstraint(
            "kind IN ('http', 'redis', 'mysql', 'postgresql', 'mongo', 'rabbitmq')",
            name="kind_valid",
        ),
        Index("ix_monitors_due", "enabled", "next_check_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    notification_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=DEFAULT_MONITOR_NOTIFICATION_CONFIG,
        server_default=text("'{}'::jsonb"),
    )
    next_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_status: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 up / 2 down
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_issue_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
