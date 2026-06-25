"""任务数据库模型。"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from cronix.core.database import Base, UTCDateTime
from cronix.utils.datetime import UTC_SERVER_DEFAULT, utc_now
from cronix.core.constants import TABLE_PREFIX


class Task(Base):
    """任务表。"""

    __tablename__ = f"{TABLE_PREFIX}tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    cron_expression = Column(String(100), nullable=False)
    command = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    timeout = Column(Integer, default=300, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    retry_interval = Column(Integer, default=60, nullable=False)
    notification_ids = Column(JSON, nullable=True)
    notify_strategy = Column(String(20), nullable=False, default="never")
    next_run_time = Column(UTCDateTime, nullable=True)
    created_at = Column(UTCDateTime, server_default=UTC_SERVER_DEFAULT, nullable=False)
    updated_at = Column(
        UTCDateTime,
        server_default=UTC_SERVER_DEFAULT,
        onupdate=utc_now,
        nullable=False,
    )
    executions = relationship(
        "TaskExecution",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}tasks_is_active", "is_active"),)
