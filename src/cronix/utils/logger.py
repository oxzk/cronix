"""日志工具模块。"""

from __future__ import annotations

import inspect
import logging
import sys
from types import FrameType
from typing import Any

from cronix.core.config import settings

NOISY_LOGGERS = ["asyncio", "aiomysql", "sqlalchemy.engine", "sqlalchemy.pool"]


class AppLogFormatter(logging.Formatter):
    """应用日志格式化器。"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录并补齐应用上下文。"""
        if not hasattr(record, "app_name"):
            record.app_name = settings.app_name
        if not hasattr(record, "log_source"):
            record.log_source = record.module or record.filename
        return super().format(record)


class Logger:
    """应用日志器。"""

    def __init__(self) -> None:
        """初始化应用日志器。"""
        self.logger = logging.getLogger(settings.app_name)
        self.configure()

    def configure(self) -> None:
        """配置无文件写入的控制台日志处理器。"""
        level = logging.DEBUG if settings.app_debug else logging.INFO
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

        self.logger.setLevel(level)
        self.logger.propagate = False

        formatter = AppLogFormatter(
            "%(asctime)s - %(levelname)s - [%(app_name)s - %(log_source)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if self.logger.handlers:
            for handler in self.logger.handlers:
                handler.setLevel(level)
                handler.setFormatter(formatter)
            return

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        for name in NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录调试日志。"""
        self._emit("debug", message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录普通信息日志。"""
        self._emit("info", message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录警告日志。"""
        self._emit("warning", message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录错误日志。"""
        self._emit("error", message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录严重错误日志。"""
        self._emit("critical", message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录异常日志并附带堆栈。"""
        self._emit("exception", message, *args, **kwargs)

    def log(self, level: str, message: str, *args: Any, **kwargs: Any) -> None:
        """记录指定级别的日志。"""
        self._emit(level, message, *args, **kwargs)

    def _emit(self, level: str, message: str, *args: Any, **kwargs: Any) -> None:
        """带调用来源上下文记录日志。"""
        extra = dict(kwargs.pop("extra", {}) or {})
        extra.setdefault("app_name", settings.app_name)
        extra.setdefault("log_source", self._resolve_log_source())
        kwargs["extra"] = extra
        getattr(self.logger, level, self.logger.info)(message, *args, **kwargs)

    def _resolve_log_source(self) -> str:
        """解析日志调用来源。"""
        frame = inspect.currentframe()
        caller = self._walk_frame(frame, 3)
        if caller is None:
            return "unknown"
        instance = caller.f_locals.get("self")
        if instance is not None and instance.__class__ is not Logger:
            return instance.__class__.__name__
        cls = caller.f_locals.get("cls")
        if isinstance(cls, type):
            return cls.__name__
        module_name = caller.f_globals.get("__name__")
        if isinstance(module_name, str) and module_name:
            return module_name
        return caller.f_code.co_filename.replace("\\", "/").rsplit("/", 1)[-1]

    def _walk_frame(self, frame: FrameType | None, depth: int) -> FrameType | None:
        """向上查找调用栈。"""
        current = frame
        for _ in range(depth):
            if current is None:
                return None
            current = current.f_back
        return current


logger = Logger()
