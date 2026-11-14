"""monitor_checks 表: 每次探测的结果。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"
    __table_args__ = (
        CheckConstraint("status IN (1, 2)", name="status_valid"),
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="latency_non_negative"),
        Index("ix_monitor_checks_monitor_checked", "monitor_id", "checked_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    monitor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 up / 2 down
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"), index=True
    )
