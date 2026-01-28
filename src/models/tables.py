from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Index,
    TIMESTAMP,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

TABLE_PREFIX = "cm_"

Base = declarative_base()


class User(Base):
    __tablename__ = f"{TABLE_PREFIX}users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="User ID")
    username = Column(String(50), unique=True, nullable=False, comment="Username")
    password = Column(String(255), nullable=False, comment="Password hash")
    is_2fa_enabled = Column(
        Boolean, default=False, nullable=False, comment="Whether 2FA is enabled"
    )
    totp_secret_key = Column(
        String(32), nullable=True, comment="TOTP secret key for 2FA"
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="Creation timestamp",
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}users_username", "username"),)


class Notification(Base):
    __tablename__ = f"{TABLE_PREFIX}notifications"

    id = Column(
        Integer, primary_key=True, autoincrement=True, comment="Notification ID"
    )
    notify_type = Column(
        String(20),
        nullable=False,
        unique=True,
        comment="Notification type (webhook/telegram/dingtalk)",
    )
    config = Column(JSONB, nullable=False, comment="Notification configuration (JSON)")
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="Creation timestamp",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}notifications_type", "notify_type"),)


class Task(Base):
    __tablename__ = f"{TABLE_PREFIX}tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Task ID")
    name = Column(String(100), nullable=False, comment="Task name")
    description = Column(Text, comment="Task description")
    cron_expression = Column(
        String(100),
        nullable=False,
        comment="Cron expression (5-field format: minute hour day month weekday)",
    )
    command = Column(Text, nullable=False, comment="Command to execute")
    is_active = Column(Boolean, default=True, comment="Whether task is active")
    timeout = Column(
        Integer,
        default=300,
        nullable=False,
        comment="Timeout in seconds (default: 300)",
    )
    retry_count = Column(
        Integer, default=0, nullable=False, comment="Number of retries (default: 0)"
    )
    retry_interval = Column(
        Integer,
        default=60,
        nullable=False,
        comment="Retry interval in seconds (default: 60)",
    )
    notification_ids = Column(
        ARRAY(Integer),
        nullable=True,
        comment="List of notification IDs (null = no notifications)",
    )
    notify_strategy = Column(
        String(20),
        nullable=False,
        default="never",
        comment="Notification strategy (never/always/on_failure)",
    )
    next_run_time = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Next scheduled execution time",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="Creation timestamp",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}tasks_is_active", "is_active"),)


class TaskExecution(Base):
    __tablename__ = f"{TABLE_PREFIX}task_executions"

    id = Column(
        Integer, primary_key=True, autoincrement=True, comment="Execution record ID"
    )
    task_id = Column(
        Integer,
        ForeignKey(f"{TABLE_PREFIX}tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="Associated task ID",
    )
    started_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="Execution start time",
    )
    finished_at = Column(TIMESTAMP(timezone=True), comment="Execution finish time")
    status = Column(
        String(20),
        comment="Execution status (pending/running/success/failed/timeout/cancelled)",
    )
    output = Column(Text, comment="Execution output")
    error = Column(Text, comment="Error message")
    retry_attempt = Column(
        Integer, default=0, nullable=False, comment="Current retry attempt number"
    )
    duration = Column(
        Integer,
        nullable=True,
        comment="Execution duration in seconds",
    )

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}task_executions_task_id", "task_id"),
        Index(
            f"idx_{TABLE_PREFIX}task_executions_started_at",
            "started_at",
            postgresql_ops={"started_at": "DESC"},
        ),
    )


class Dependency(Base):
    __tablename__ = f"{TABLE_PREFIX}dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Dependency ID")
    dependency_type = Column(
        String(20),
        nullable=False,
        comment="Dependency type (python/node)",
    )
    package_name = Column(String(255), nullable=False, comment="Package name")
    version = Column(String(50), nullable=True, comment="Package version (optional)")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="Installation status (pending/installing/installed/failed)",
    )
    installed_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Installation completion time",
    )
    error_message = Column(
        Text, nullable=True, comment="Error message if installation failed"
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="Creation timestamp",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}dependencies_type", "dependency_type"),
        Index(f"idx_{TABLE_PREFIX}dependencies_status", "status"),
        Index(
            f"idx_{TABLE_PREFIX}dependencies_type_package",
            "dependency_type",
            "package_name",
            unique=True,
        ),
    )
