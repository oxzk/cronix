"""通知配置数据库模型。"""

from __future__ import annotations

from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.dialects.mysql import JSON

from cronix.core.database import Base, UTCDateTime
from cronix.utils.datetime import UTC_SERVER_DEFAULT, utc_now
from cronix.core.constants import TABLE_PREFIX


class Notification(Base):
    """通知配置表。"""

    __tablename__ = f"{TABLE_PREFIX}notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notify_type = Column(String(20), nullable=False, unique=True)
    config = Column(JSON, nullable=False)
    created_at = Column(UTCDateTime, server_default=UTC_SERVER_DEFAULT, nullable=False)
    updated_at = Column(
        UTCDateTime,
        server_default=UTC_SERVER_DEFAULT,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}notifications_type", "notify_type"),)
