from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from croniter import croniter


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
        """Validate notification configuration parameters"""
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
    command: str
    is_active: bool = True
    timeout: int = Field(default=300, ge=1, le=3600)  # 1 second to 1 hour
    retry_count: int = Field(default=0, ge=0, le=5)  # Maximum 5 retries
    retry_interval: int = Field(default=60, ge=1, le=600)  # 1 second to 10 minutes
    notification_ids: Optional[List[int]] = None  # Notification configuration ID list

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        """Validate cron expression, supports standard 5-field format (minute hour day month weekday)"""
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have 5 fields: minute hour day month weekday"
            )
        try:
            # Use croniter to validate expression validity
            croniter(v)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        return v


class TaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    cron_expression: str
    command: str
    is_active: bool
    timeout: int
    retry_count: int
    retry_interval: int
    notifications: Optional[List[NotificationResponse]] = (
        None  # Associated notification configurations
    )
    next_run_time: Optional[datetime] = None
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
    duration: Optional[int] = None


class TaskExecutionDetailResponse(BaseModel):
    id: int
    task_id: int
    task: Optional[TaskResponse]
    started_at: datetime
    finished_at: Optional[datetime]
    status: ExecutionStatus
    output: Optional[str]
    error: Optional[str]
    retry_attempt: int
    duration: Optional[int] = None
