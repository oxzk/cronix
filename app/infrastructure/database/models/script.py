"""scripts 表: 可复用 Shell 脚本。"""

from __future__ import annotations

import uuid

from sqlalchemy import String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, TimestampMixin


class Script(TimestampMixin, Base):
    __tablename__ = "scripts"
    __table_args__ = (UniqueConstraint("name", name="uq_scripts_name"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
