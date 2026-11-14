"""TOTP (RFC 6238): 无第三方依赖的 6 位动态码, 30 秒步长, SHA1。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time
from urllib.parse import quote, urlencode

DIGITS = 6
PERIOD = 30
WINDOW = 1


def generate_secret() -> str:
    """生成 base32 密钥(20 字节熵)。"""
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode(padded.upper())


def hotp(secret: str, counter: int) -> str:
    digest = hmac.new(_decode_secret(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**DIGITS)
    return f"{value:0{DIGITS}d}"


def verify(secret: str, code: str, *, window: int = WINDOW, now: float | None = None) -> bool:
    """校验动态码, 允许前后 window 个时间步的时钟漂移。"""
    code = (code or "").strip()
    if not secret or len(code) != DIGITS or not code.isdigit():
        return False
    counter = int((now if now is not None else time.time()) // PERIOD)
    for offset in range(-window, window + 1):
        if hmac.compare_digest(hotp(secret, counter + offset), code):
            return True
    return False


def provisioning_uri(secret: str, account: str, issuer: str = "cronix") -> str:
    label = quote(f"{issuer}:{account}", safe="")
    params = urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": DIGITS,
            "period": PERIOD,
        }
    )
    return f"otpauth://totp/{label}?{params}"
