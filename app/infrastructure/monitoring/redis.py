"""Redis 检查器: 使用连接 URL 执行 PING。"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.infrastructure.monitoring.base import BaseChecker, CheckResult, MonitorStatus


class RedisChecker(BaseChecker):
    kind = "redis"

    async def check(self, config: dict, timeout: int) -> CheckResult:
        client = None
        try:
            client = aioredis.Redis.from_url(
                config["url"],
                socket_timeout=timeout,
                socket_connect_timeout=timeout,
            )
            await client.ping()
            return CheckResult(MonitorStatus.UP)
        except Exception as exc:
            return CheckResult(
                MonitorStatus.DOWN, "driver_error", f"{type(exc).__name__}: {exc}"
            )
        finally:
            if client is not None:
                await client.aclose()
