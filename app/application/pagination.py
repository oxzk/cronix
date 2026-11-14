"""分页参数解析。"""

from __future__ import annotations

MAX_PAGE_SIZE = 100


def parse_pagination(page: int, page_size: int) -> tuple[int, int]:
    """返回 (page, page_size), 均收敛到合法区间。"""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    return page, page_size
