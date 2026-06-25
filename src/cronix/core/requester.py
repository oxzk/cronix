"""异步 HTTP 请求基础模块。

本模块封装 httpx 会话、默认请求参数和重试请求流程。
"""

from __future__ import annotations

from typing import Any

import httpx

from cronix.core.config import settings
from cronix.utils.retry import async_retry
from cronix.utils.logger import logger


class RetryableRequestError(Exception):
    """可重试 HTTP 请求异常。"""


class BaseRequester:
    """管理可复用异步 HTTP 会话并提供统一请求流程。"""

    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0

    def __init__(self) -> None:
        """初始化请求器运行态。"""
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """获取或创建 httpx 客户端会话。"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.DEFAULT_TIMEOUT,
                verify=False,
            )
        return self._client

    async def close(self) -> None:
        """关闭 HTTP 客户端会话。"""
        if self._client is not None:
            client = self._client
            self._client = None
            await client.aclose()

    async def fetch(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        method: str = "GET",
        retries: int = DEFAULT_RETRIES,
        **kwargs: Any,
    ) -> httpx.Response:
        """发送 HTTP 请求，并对异常或 5xx 响应执行重试。

        参数:
            url:     请求地址。
            data:    表单请求数据。
            method:  HTTP 方法。
            retries: 失败后的重试次数，不包含首次请求。
            **kwargs: 传递给 httpx 的额外参数。

        返回:
            httpx 原生响应对象。
        """
        request_method = method.upper()
        request_kwargs = self._build_request_kwargs(data=data, **kwargs)

        attempts = max(1, retries + 1)
        request_with_retry = async_retry(
            attempts=attempts,
            delay_seconds=settings.http_retry_delay_seconds,
            backoff=settings.http_retry_backoff,
            retry_exceptions=(
                httpx.TimeoutException,
                httpx.NetworkError,
                RetryableRequestError,
            ),
        )(self._request_once)
        try:
            return await request_with_retry(request_method, url, request_kwargs)
        except Exception as exc:
            logger.error(f"Request failed after {attempts} attempts: {exc}")
            raise

    async def _request_once(
        self,
        method: str,
        url: str,
        request_kwargs: dict[str, Any],
    ) -> httpx.Response:
        """执行单次 HTTP 请求。"""
        logger.debug(f"{method} {url}")
        response = await self.client.request(
            method,
            url,
            **request_kwargs,
        )

        if response.status_code >= 500:
            error_text = response.text[:200]
            raise RetryableRequestError(
                f"Request returned HTTP {response.status_code}: {method} {url}: {error_text}"
            )

        if response.status_code >= 400:
            logger.warning(
                f"Request returned HTTP {response.status_code}: {method} {url}: {response.text[:200]}"
            )

        return response

    def _build_request_kwargs(
        self,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """构建 httpx 请求参数。"""
        request_kwargs = dict(kwargs)

        if data is not None:
            request_kwargs["data"] = data

        request_kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return request_kwargs

    async def get_json(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        method: str = "GET",
        retries: int = DEFAULT_RETRIES,
        **kwargs: Any,
    ) -> Any:
        """发送 HTTP 请求并解析 JSON 响应。"""
        response = await self.fetch(
            url=url,
            data=data,
            method=method,
            retries=retries,
            **kwargs,
        )
        return response.json()

    async def get_text(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        method: str = "GET",
        retries: int = DEFAULT_RETRIES,
        **kwargs: Any,
    ) -> str:
        """发送 HTTP 请求并返回文本响应。"""
        response = await self.fetch(
            url=url,
            data=data,
            method=method,
            retries=retries,
            **kwargs,
        )
        return response.text


requester = BaseRequester()
"""全局共享 HTTP 请求器实例。"""
