import logging
import sys
from pathlib import Path
from datetime import datetime
from src.config import settings


class Logger:
    """统一的日志管理类"""

    def __init__(self):
        self.logger = logging.getLogger("Cronix")
        self.logger.setLevel(logging.DEBUG if settings.app_debug else logging.INFO)

        # 避免重复添加 handler
        if not self.logger.handlers:
            # 控制台输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(
                logging.DEBUG if settings.app_debug else logging.INFO
            )

            # 文件输出
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.ERROR)

            # 格式化
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """调试信息"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """一般信息"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """警告信息"""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """错误信息"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """严重错误"""
        self.logger.critical(message, exc_info=exc_info)


# 全局 logger 实例
logger = Logger()
