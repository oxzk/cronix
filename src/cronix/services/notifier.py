"""通知服务。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Dict

from cronix.core.requester import requester
from cronix.utils.logger import logger


class NotifierService:
    """通知发送服务。"""

    async def send_notification(self, notify_type: str, config: Dict, message: str) -> None:
        """按通知类型发送消息。"""
        try:
            if notify_type == "webhook":
                url = config.get("url")
                if not url:
                    raise ValueError("Webhook notification requires 'url' in config")
                await self._send_webhook(url, message)
            elif notify_type == "telegram":
                bot_token = config.get("bot_token")
                chat_id = config.get("chat_id")
                if not bot_token or not chat_id:
                    raise ValueError(
                        "Telegram notification requires 'bot_token' and 'chat_id' in config"
                    )
                await self._send_telegram(bot_token, chat_id, message)
            elif notify_type == "dingtalk":
                webhook_url = config.get("webhook_url")
                secret = config.get("secret")
                if not webhook_url or not secret:
                    raise ValueError(
                        "DingTalk notification requires 'webhook_url' and 'secret' in config"
                    )
                await self._send_dingtalk(webhook_url, secret, message)
            else:
                raise ValueError(f"Unknown notification type: {notify_type}")
        except Exception as e:
            logger.error(f"Notification failed: {e}", exc_info=True)
            raise

    async def _send_webhook(self, url: str, message: str) -> str:
        """发送 Webhook 通知。"""
        return await requester.get_text(
            url=url,
            method="POST",
            json={"message": message},
            timeout=10,
        )

    async def _send_telegram(self, bot_token: str, chat_id: str, message: str) -> dict:
        """发送 Telegram 通知。"""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        return await requester.get_json(
            url=url,
            method="POST",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )

    async def _send_dingtalk(self, webhook_url: str, secret: str, message: str) -> dict:
        """发送钉钉通知。"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))

        url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        return await requester.get_json(
            url=url,
            method="POST",
            json={"msgtype": "text", "text": {"content": message}},
            timeout=10,
        )


notifier_service = NotifierService()
"""全局通知服务实例。"""
