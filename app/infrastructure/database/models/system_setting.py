"""system_settings 表: (scope, key) 唯一的数据库配置。"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, TimestampMixin


class SystemSetting(TimestampMixin, Base):
    __tablename__ = "system_settings"
    __table_args__ = (UniqueConstraint("scope", "key", name="uq_system_settings_scope_key"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="object")
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
