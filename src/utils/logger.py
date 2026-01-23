import logging
import sys
from pathlib import Path
from datetime import datetime
from src.config import settings


class Logger:
    """Unified logging management class"""

    def __init__(self):
        self.logger = logging.getLogger("Cronix")
        self.logger.setLevel(logging.DEBUG if settings.app_debug else logging.INFO)

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            # Console output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(
                logging.DEBUG if settings.app_debug else logging.INFO
            )

            # File output
            log_dir = Path("data/logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.ERROR)

            # Formatting
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Debug information"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """General information"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Warning information"""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Error information"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """Critical error"""
        self.logger.critical(message, exc_info=exc_info)


# Global logger instance
logger = Logger()
