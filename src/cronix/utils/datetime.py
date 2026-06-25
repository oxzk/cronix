"""日期时间工具函数。"""

from datetime import datetime, timezone

from sqlalchemy import text


def utc_now() -> datetime:
    """获取带 UTC 时区信息的当前时间。"""
    return datetime.now(timezone.utc)


# TiDB/MySQL 兼容的当前时间默认值
# 使用 text() 而不是 func，因为 TiDB 不支持 func.utc_timestamp()
# CURRENT_TIMESTAMP 在连接时区为 UTC 时返回 UTC 时间
UTC_SERVER_DEFAULT = text("CURRENT_TIMESTAMP")
"""数据库 UTC 当前时间默认值。"""
