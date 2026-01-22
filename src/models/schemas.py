from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from croniter import croniter


class ExecutionType(str, Enum):
    SHELL = "shell"
    PYTHON = "python"
    NODE = "node"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class NotifyType(str, Enum):
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    DINGTALK = "dingtalk"


class UserSchema(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    totp_code: Optional[str] = None
    is_2fa_enabled: Optional[bool] = None
    totp_secret_key: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class NotificationSchema(BaseModel):
    notify_type: NotifyType
    config: dict

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict, info) -> dict:
        """验证通知配置参数"""
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
    id: int
    notify_type: NotifyType
    config: dict
    created_at: datetime
    updated_at: datetime


class TaskSchema(BaseModel):
    name: str
    description: Optional[str] = None
    cron_expression: str
    execution_type: ExecutionType
    command: str
    is_active: bool = True
    timeout: int = Field(default=300, ge=1, le=3600)  # 1秒到1小时
    retry_count: int = Field(default=0, ge=0, le=5)  # 最多重试5次
    retry_interval: int = Field(default=60, ge=1, le=600)  # 1秒到10分钟
    notification_ids: Optional[List[int]] = None  # 通知配置ID列表

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        """验证 cron 表达式，支持 6 位格式（秒 分 时 日 月 周）"""
        parts = v.strip().split()
        if len(parts) != 6:
            raise ValueError(
                "Cron expression must have 6 fields: second minute hour day month weekday"
            )
        try:
            # 使用 croniter 验证表达式的有效性
            croniter(v)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        return v


class TaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    cron_expression: str
    execution_type: str
    command: str
    is_active: bool
    timeout: int
    retry_count: int
    retry_interval: int
    notifications: Optional[List[NotificationResponse]] = None  # 关联的通知配置
    created_at: datetime
    updated_at: datetime


class TaskExecutionResponse(BaseModel):
    id: int
    task_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: ExecutionStatus
    output: Optional[str]
    error: Optional[str]
    retry_attempt: int
