"""system_settings 仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.system_setting import SystemSetting


class SystemSettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_key(self, scope: str, key: str) -> SystemSetting | None:
        stmt = select(SystemSetting).where(SystemSetting.scope == scope, SystemSetting.key == key)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_all(self) -> list[SystemSetting]:
        stmt = select(SystemSetting).order_by(SystemSetting.scope.asc(), SystemSetting.key.asc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, setting: SystemSetting) -> SystemSetting:
        self._session.add(setting)
        await self._session.flush()
        return setting
