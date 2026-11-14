"""loguru 配置: stderr + 每日 00:00 滚动文件(固定 data/logs, 不压缩), 输出前统一脱敏。"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.core.config import LoggingSettings
from app.runtime.logger import redact, redact_text

LOG_DIRECTORY = Path("data/logs")

_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{extra[request_id]} | {name}:{function}:{line} - {message}"
)


def _patch(record: dict) -> None:  # type: ignore[type-arg]
    record["extra"]["request_id"] = record["extra"].get("request_id") or "-"
    record["message"] = redact_text(str(record["message"]))
    record["extra"] = redact(record["extra"])


def configure_logging(settings: LoggingSettings, *, reset: bool = False) -> list[int]:
    """(重新)配置 sink: 控制台与文件固定开启, 返回本批次 sink id。"""
    if reset:
        logger.remove()
    logger.configure(patcher=_patch, extra={"request_id": "-"})
    sink_ids: list[int] = []
    sink_ids.append(
        logger.add(
            sys.stderr,
            level=settings.level,
            format=_FORMAT,
            backtrace=False,
            diagnose=False,
            enqueue=True,  # 异步写日志, 避免高输出任务阻塞事件循环
        )
    )
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    sink_ids.append(
        logger.add(
            LOG_DIRECTORY / "cronix_{time:YYYY-MM-DD}.log",
            level=settings.level,
            format=_FORMAT,
            rotation="00:00",
            retention=settings.retention,
            encoding="utf-8",
            backtrace=False,
            diagnose=False,
            enqueue=True,
        )
    )
    return sink_ids


def close_logging(sink_ids: list[int]) -> None:
    for sink_id in sink_ids:
        try:
            logger.remove(sink_id)
        except ValueError:
            pass
