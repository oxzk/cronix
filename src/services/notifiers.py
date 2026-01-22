import aiohttp
import hashlib
import hmac
import base64
import time
from typing import Dict
from sqlalchemy import select
from src.utils import logger
from src.databases import db
from src.models import Notification


async def initialize_notifications():
    """Initialize default notification configurations for each type if not exists"""
    async for session in db.get_session():
        notification_types = [
            {
                "notify_type": "webhook",
                "config": {"url": "https://example.com/webhook"},
            },
            {
                "notify_type": "telegram",
                "config": {"bot_token": "", "chat_id": ""},
            },
            {
                "notify_type": "dingtalk",
                "config": {"webhook_url": "", "secret": ""},
            },
        ]

        for notification_data in notification_types:
            result = await session.execute(
                select(Notification).where(
                    Notification.notify_type == notification_data["notify_type"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                notification = Notification(
                    notify_type=notification_data["notify_type"],
                    config=notification_data["config"],
                )
                session.add(notification)

        await session.commit()


async def send_notification(notify_type: str, config: Dict, message: str) -> None:
    """Send notification based on type"""
    try:
        if notify_type == "webhook":
            url = config.get("url")
            if not url:
                raise ValueError("Webhook notification requires 'url' in config")
            await send_webhook(url, message)
        elif notify_type == "telegram":
            bot_token = config.get("bot_token")
            chat_id = config.get("chat_id")
            if not bot_token or not chat_id:
                raise ValueError(
                    "Telegram notification requires 'bot_token' and 'chat_id' in config"
                )
            await send_telegram(bot_token, chat_id, message)
        elif notify_type == "dingtalk":
            webhook_url = config.get("webhook_url")
            secret = config.get("secret")
            if not webhook_url or not secret:
                raise ValueError(
                    "DingTalk notification requires 'webhook_url' and 'secret' in config"
                )
            await send_dingtalk(webhook_url, secret, message)
        else:
            raise ValueError(f"Unknown notification type: {notify_type}")
    except Exception as e:
        logger.error(f"Notification failed: {e}", exc_info=True)
        raise


async def send_webhook(url: str, message: str) -> str:
    """Send webhook notification"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"message": message}, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            return await response.text()


async def send_telegram(bot_token: str, chat_id: str, message: str) -> dict:
    """Send Telegram notification"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            return await response.json()


async def send_dingtalk(webhook_url: str, secret: str, message: str) -> dict:
    """Send DingTalk notification"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = f"{timestamp}\n{secret}"
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(
        secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")

    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={"msgtype": "text", "text": {"content": message}},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            return await response.json()
