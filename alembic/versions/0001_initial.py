"""initial: tasks / task_runs / scripts / monitors / monitor_checks / system_settings

Revision ID: 0001
Revises:
Create Date: 2026-11-07

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "scripts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scripts")),
        sa.UniqueConstraint("name", name=op.f("uq_scripts_name")),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("command", sa.Text(), nullable=True),
        sa.Column("script_id", sa.Uuid(), nullable=True),
        sa.Column("cron", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("timeout", sa.Integer(), nullable=True),
        sa.Column("max_retries", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("retry_delay", sa.Integer(), server_default=sa.text("5"), nullable=False),
        sa.Column("notification_config", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["script_id"], ["scripts.id"], name=op.f("fk_tasks_script_id_scripts"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
        sa.CheckConstraint("timeout IS NULL OR timeout > 0", name=op.f("ck_tasks_timeout_positive")),
        sa.CheckConstraint("max_retries >= 0", name=op.f("ck_tasks_max_retries_non_negative")),
        sa.CheckConstraint("retry_delay > 0", name=op.f("ck_tasks_retry_delay_positive")),
        sa.CheckConstraint(
            "command IS NOT NULL OR script_id IS NOT NULL", name=op.f("ck_tasks_command_or_script")
        ),
    )
    op.create_index(op.f("ix_tasks_enabled"), "tasks", ["enabled"])
    op.create_index(op.f("ix_tasks_next_run_at"), "tasks", ["next_run_at"])
    op.create_index(op.f("ix_tasks_script_id"), "tasks", ["script_id"])
    op.create_index("ix_tasks_due", "tasks", ["enabled", "next_run_at"])

    op.create_table(
        "task_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("trigger", sa.Integer(), nullable=False),
        sa.Column("status", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.BigInteger(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("logs", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_task_runs_task_id_tasks"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_runs")),
        sa.CheckConstraint("trigger IN (0, 1)", name=op.f("ck_task_runs_trigger_valid")),
        sa.CheckConstraint("status IN (0, 1, 2, 3, 4, 5)", name=op.f("ck_task_runs_status_valid")),
        sa.CheckConstraint("attempt >= 1", name=op.f("ck_task_runs_attempt_positive")),
        sa.CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0", name=op.f("ck_task_runs_duration_non_negative")
        ),
    )
    op.create_index(op.f("ix_task_runs_task_id"), "task_runs", ["task_id"])
    op.create_index(op.f("ix_task_runs_trigger"), "task_runs", ["trigger"])
    op.create_index(op.f("ix_task_runs_status"), "task_runs", ["status"])
    op.create_index(op.f("ix_task_runs_created_at"), "task_runs", ["created_at"])
    op.create_index("ix_task_runs_task_created", "task_runs", ["task_id", "created_at"])

    op.create_table(
        "monitors",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("config", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), server_default=sa.text("60"), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), server_default=sa.text("10"), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("notification_config", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.Integer(), nullable=True),
        sa.Column("last_latency_ms", sa.Integer(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_issue_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_monitors")),
        sa.CheckConstraint("interval_seconds > 0", name=op.f("ck_monitors_interval_positive")),
        sa.CheckConstraint("timeout_seconds > 0", name=op.f("ck_monitors_timeout_positive")),
        sa.CheckConstraint(
            "last_status IS NULL OR last_status IN (1, 2)", name=op.f("ck_monitors_last_status_valid")
        ),
        sa.CheckConstraint(
            "kind IN ('http', 'redis', 'mysql', 'postgresql', 'mongo', 'rabbitmq')",
            name=op.f("ck_monitors_kind_valid"),
        ),
    )
    op.create_index(op.f("ix_monitors_enabled"), "monitors", ["enabled"])
    op.create_index(op.f("ix_monitors_next_check_at"), "monitors", ["next_check_at"])
    op.create_index("ix_monitors_due", "monitors", ["enabled", "next_check_at"])

    op.create_table(
        "monitor_checks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("monitor_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["monitor_id"], ["monitors.id"], name=op.f("fk_monitor_checks_monitor_id_monitors"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_monitor_checks")),
        sa.CheckConstraint("status IN (1, 2)", name=op.f("ck_monitor_checks_status_valid")),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name=op.f("ck_monitor_checks_latency_non_negative")
        ),
    )
    op.create_index(op.f("ix_monitor_checks_monitor_id"), "monitor_checks", ["monitor_id"])
    op.create_index(op.f("ix_monitor_checks_checked_at"), "monitor_checks", ["checked_at"])
    op.create_index("ix_monitor_checks_monitor_checked", "monitor_checks", ["monitor_id", "checked_at"])

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("type", sa.String(30), server_default=sa.text("'object'"), nullable=False),
        sa.Column("value", JSONB(), nullable=False),
        sa.Column("is_complete", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_settings")),
        sa.UniqueConstraint("scope", "key", name=op.f("uq_system_settings_scope_key")),
    )
    op.create_index(op.f("ix_system_settings_scope"), "system_settings", ["scope"])


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("monitor_checks")
    op.drop_table("monitors")
    op.drop_table("task_runs")
    op.drop_table("tasks")
    op.drop_table("scripts")
