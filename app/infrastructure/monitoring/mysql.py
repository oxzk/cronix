"""MySQL 检查器: 通过 SQLAlchemy 执行 SELECT 1。"""

from __future__ import annotations

import ssl

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.monitoring import mysql_connection_options
from app.infrastructure.monitoring.base import BaseChecker, CheckResult, MonitorStatus


def _aiomysql_url(url: str) -> str:
    """参考 DatabaseSettings: 将 MySQL URL 前缀统一为 aiomysql 驱动。"""
    if url.startswith("mysql://"):
        return "mysql+aiomysql://" + url.split("://", 1)[1]
    return url


class MysqlChecker(BaseChecker):
    kind = "mysql"

    async def check(self, config: dict, timeout: int) -> CheckResult:
        engine: AsyncEngine | None = None
        try:
            connect_args: dict[str, object] = {"connect_timeout": timeout}
            # URL 里的 ssl=true 会被 SQLAlchemy 当字符串传给驱动, 用 SSLContext 覆盖。
            if mysql_connection_options(config["url"])["ssl"]:
                connect_args["ssl"] = ssl.create_default_context()
            engine = create_async_engine(
                _aiomysql_url(config["url"]), connect_args=connect_args
            )
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return CheckResult(MonitorStatus.UP)
        except Exception as exc:
            return CheckResult(
                MonitorStatus.DOWN, "driver_error", f"{type(exc).__name__}: {exc}"
            )
        finally:
            if engine is not None:
                await engine.dispose()
