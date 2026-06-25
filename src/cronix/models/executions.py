"""任务执行记录数据库模型。"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from cronix.core.database import Base, UTCDateTime
from cronix.utils.datetime import UTC_SERVER_DEFAULT
from cronix.core.constants import TABLE_PREFIX


class TaskExecution(Base):
    """任务执行记录表。"""

    __tablename__ = f"{TABLE_PREFIX}task_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(
        Integer,
        ForeignKey(f"{TABLE_PREFIX}tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at = Column(UTCDateTime, server_default=UTC_SERVER_DEFAULT)
    finished_at = Column(UTCDateTime, nullable=True)
    status = Column(String(20))
    output = Column(Text)
    error = Column(Text)
    retry_attempt = Column(Integer, default=0, nullable=False)
    duration = Column(Integer, nullable=True)
    task = relationship("Task", back_populates="executions", lazy="selectin")

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}task_executions_task_id", "task_id"),
        Index(f"idx_{TABLE_PREFIX}task_executions_started_at", "started_at"),
    )
