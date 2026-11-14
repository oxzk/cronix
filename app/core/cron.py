"""cron 表达式: 仅支持 5 段标准 cron(分钟粒度), 计算一律基于 UTC。"""

from __future__ import annotations

from datetime import datetime

from croniter import croniter

from app.core.exceptions import ValidationError

CRON_FIELDS = 5


def validate_cron(expr: str) -> None:
    """校验 cron 表达式, 不合法抛 ValidationError。"""
    fields = expr.split()
    if len(fields) != CRON_FIELDS:
        raise ValidationError(f"cron 表达式必须为 {CRON_FIELDS} 段(分 时 日 月 周), 当前 {len(fields)} 段")
    try:
        croniter(expr)
    except (ValueError, KeyError) as exc:
        raise ValidationError(f"cron 表达式不合法: {expr}({exc})") from exc


def next_after(expr: str, base: datetime) -> datetime:
    """base(UTC aware) 之后下一次触发时间(UTC aware)。"""
    validate_cron(expr)
    return croniter(expr, base).get_next(datetime)


def advance_to_future(expr: str, base: datetime, now: datetime) -> datetime:
    """返回 now 之后的下一个触发时间。

    直接以 max(base, now) 为基准计算, 避免 next_run_at 很旧时逐轮推进造成长时间阻塞。
    """
    reference = base if base > now else now
    return next_after(expr, reference)
