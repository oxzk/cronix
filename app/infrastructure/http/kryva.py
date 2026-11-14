"""Kryva 文件客户端: 备份上传与下载(Bearer API Key)。"""

from __future__ import annotations

from pathlib import Path

import httpx

from app.core.exceptions import ValidationError

TIMEOUT_SECONDS = 600.0


class KryvaClient:
    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key

    def _endpoint(self, path: str) -> str:
        return f"{self._api_url}/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def upload(self, platform: str, filename: str, path: Path) -> None:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            with path.open("rb") as stream:
                response = await client.post(
                    self._endpoint("/api/v1/files/upload"),
                    headers=self._headers(),
                    data={"platform": platform},
                    files={"file": (filename, stream, "application/gzip")},
                )
            await self._raise_for_status(response)

    async def list_files(self, platform: str, page: int = 1, page_size: int = 20) -> dict:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                self._endpoint("/v1/files"),
                headers=self._headers(),
                params={"platform": platform, "page": page, "pageSize": page_size},
            )
            await self._raise_for_status(response)
        payload = response.json()
        if payload.get("code") not in (0, None):
            raise ValidationError(f"Kryva 列表失败: {payload.get('message') or 'unknown'}")
        return payload.get("data") or {}

    async def download(self, platform: str, filename: str, destination: Path) -> bool:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            async with client.stream(
                "GET",
                self._endpoint("/api/v1/files/download"),
                headers=self._headers(),
                params={"platform": platform, "filename": filename},
            ) as response:
                if response.status_code == 404:
                    return False
                await self._raise_for_status(response)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("wb") as output:
                    async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                        if chunk:
                            output.write(chunk)
        return True

    async def _raise_for_status(self, response: httpx.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        if response.status_code == 401:
            raise ValidationError("Kryva API Key 无效")
        await response.aread()
        detail = response.text.strip()[:300]
        suffix = f": {detail}" if detail else ""
        raise ValidationError(f"Kryva 请求失败(HTTP {response.status_code}){suffix}")
