"""HTTP 检查器: 请求并校验状态码。"""

from __future__ import annotations

import httpx

from app.infrastructure.monitoring.base import BaseChecker, CheckResult, MonitorStatus


class HttpChecker(BaseChecker):
    kind = "http"

    async def check(self, config: dict, timeout: int) -> CheckResult:
        method = str(config.get("method") or "GET")
        expected = int(config.get("expected_status") or 200)
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                verify=bool(config.get("verify_tls", True)),
                follow_redirects=False,
            ) as client:
                response = await client.request(
                    method, str(config["url"]), headers=config.get("headers") or {}
                )
        except httpx.HTTPError as exc:
            return CheckResult(
                MonitorStatus.DOWN, "network_error", f"{type(exc).__name__}: {exc}"
            )
        except Exception as exc:
            return CheckResult(
                MonitorStatus.DOWN, "driver_error", f"{type(exc).__name__}: {exc}"
            )
        if response.status_code != expected:
            return CheckResult(
                MonitorStatus.DOWN,
                "http_status",
                f"HTTP {response.status_code} (期望 {expected})",
            )
        return CheckResult(MonitorStatus.UP)
