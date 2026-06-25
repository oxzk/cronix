"""API 响应数据结构。

本模块只定义统一 JSON API 响应和分页响应使用的数据结构。
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """标准 API 响应模型。"""

    code: int
    message: str
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "ok") -> "APIResponse[T]":
        """创建成功响应。"""
        return cls(code=0, message=message, data=data)


class PageQuery(BaseModel):
    """分页查询参数。"""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=200, description="Items per page")

    @property
    def skip(self) -> int:
        """分页查询跳过数量。"""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型。"""

    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
