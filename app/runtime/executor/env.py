"""子进程环境变量脱敏: 剥离应用自身的敏感配置, 避免被任务/脚本读取。"""

from __future__ import annotations

import os
import re

_SENSITIVE_KEY = re.compile(
    r"(?i)(secret|token|password|passwd|api[_-]?key|apikey|credential|private[_-]?key)"
)
_SENSITIVE_PREFIXES = ("DATABASE__", "JWT__", "CRONIX_", "KRYVA_")


def sanitized_environment() -> dict[str, str]:
    """返回去除数据库/JWT/各类密钥后的环境变量副本(保留 PATH 等常规变量)。"""
    environment: dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith(_SENSITIVE_PREFIXES):
            continue
        if _SENSITIVE_KEY.search(key):
            continue
        environment[key] = value
    return environment
