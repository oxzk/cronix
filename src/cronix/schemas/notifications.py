"""通知相关数据结构。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class NotifyType(str, Enum):
    """通知渠道类型。"""

    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    DINGTALK = "dingtalk"


class NotifyStrategy(str, Enum):
    """通知发送策略。"""

    NEVER = "never"
    ALWAYS = "always"
    ON_FAILURE = "on_failure"


class NotificationSchema(BaseModel):
    """通知配置请求数据。"""

    notify_type: NotifyType
    config: dict

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict, info) -> dict:
        """校验通知配置参数。"""
        notify_type = info.data.get("notify_type")

        if notify_type == NotifyType.WEBHOOK:
            if "url" not in v:
                raise ValueError("Webhook notification requires 'url' in config")
            if not isinstance(v["url"], str) or not v["url"].startswith(
                ("http://", "https://")
            ):
                raise ValueError("Webhook 'url' must be a valid HTTP/HTTPS URL")

        elif notify_type == NotifyType.TELEGRAM:
            if "bot_token" not in v:
                raise ValueError("Telegram notification requires 'bot_token' in config")
            if "chat_id" not in v:
                raise ValueError("Telegram notification requires 'chat_id' in config")
            if not isinstance(v["bot_token"], str) or not v["bot_token"]:
                raise ValueError("Telegram 'bot_token' must be a non-empty string")
            if not isinstance(v["chat_id"], (str, int)) or not v["chat_id"]:
                raise ValueError(
                    "Telegram 'chat_id' must be a non-empty string or integer"
                )

        elif notify_type == NotifyType.DINGTALK:
            if "webhook_url" not in v:
                raise ValueError(
                    "DingTalk notification requires 'webhook_url' in config"
                )
            if "secret" not in v:
                raise ValueError("DingTalk notification requires 'secret' in config")
            if not isinstance(v["webhook_url"], str) or not v["webhook_url"].startswith(
                ("http://", "https://")
            ):
                raise ValueError(
                    "DingTalk 'webhook_url' must be a valid HTTP/HTTPS URL"
                )
            if not isinstance(v["secret"], str) or not v["secret"]:
                raise ValueError("DingTalk 'secret' must be a non-empty string")

        return v


class NotificationResponse(BaseModel):
    """通知配置响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    notify_type: NotifyType
    config: dict
    created_at: datetime
    updated_at: datetime
