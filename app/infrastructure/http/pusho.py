"""Pusho 客户端: 通过 /v1/messages 推送消息(Bearer API Key)。"""

from __future__ import annotations

from typing import Literal

import httpx

from app.core.exceptions import ValidationError

MAX_CONTENT_CHARS = 10_000
MAX_TITLE_CHARS = 200


class PushoClient:
    """封装 Pusho 消息接口及内容格式参数."""

    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key

    async def send(
        self,
        *,
        project: str,
        title: str,
        content: str,
        content_type: Literal["text", "markdown"] = "text",
        timeout: int = 30,
        idempotency_key: str | None = None,
    ) -> dict:
        """向指定项目推送文本或 Markdown 消息."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key[:128]
        body = {
            "project": project,
            "title": title[:MAX_TITLE_CHARS],
            "content": content[:MAX_CONTENT_CHARS],
            "content_type": content_type,
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self._api_url}/v1/messages", headers=headers, json=body
                )
        except httpx.HTTPError as exc:
            raise ValidationError(f"Pusho 请求失败: {type(exc).__name__}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code >= 400 or payload.get("code") not in (0, None):
            message = str(payload.get("message") or f"HTTP {response.status_code}")
            raise ValidationError(f"Pusho 推送失败: {message}")
        return payload.get("data") or {}
