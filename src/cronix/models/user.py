"""用户数据库模型。"""

from __future__ import annotations

from sqlalchemy import Column, Index, Integer, String

from cronix.core.database import Base, UTCDateTime
from cronix.utils.datetime import UTC_SERVER_DEFAULT, utc_now
from cronix.core.constants import TABLE_PREFIX


class User(Base):
    """用户表。"""

    __tablename__ = f"{TABLE_PREFIX}users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column(UTCDateTime, server_default=UTC_SERVER_DEFAULT, nullable=False)
    updated_at = Column(
        UTCDateTime,
        server_default=UTC_SERVER_DEFAULT,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}users_username", "username"),)
