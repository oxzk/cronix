export interface Page<T> {
    items: T[]
    total: number
    page: number
    page_size: number
}

interface NotificationConfig {
    enabled: boolean
    events: string[]
}

export interface Task {
    id: string
    name: string
    command: string | null
    script_id: string | null
    script_name: string | null
    cron: string
    enabled: boolean
    timeout: number | null
    max_retries: number
    retry_delay: number
    running_count: number
    notification_config: NotificationConfig
    next_run_at: string | null
    last_run_at: string | null
    last_status: number | null
    created_at: string
    updated_at: string
}

export interface TaskPayload {
    name: string
    command: string | null
    script_id: string | null
    cron: string
    enabled: boolean
    timeout: number | null
    max_retries: number
    retry_delay: number
    notification_config: NotificationConfig
}

export interface Run {
    id: string
    task_id: string
    task_name: string | null
    trigger: number
    status: number
    attempt: number
    scheduled_at: string | null
    started_at: string | null
    completed_at: string | null
    duration_ms: number | null
    exit_code: number | null
    error_code: string | null
    error_message: string | null
    created_at: string
}

export interface LogEntry {
    timestamp: string
    level: string
    message: string
}

export interface LogsResponse {
    run_id: string
    persisted: boolean
    logs: LogEntry[]
}

interface NextRun {
    task_id: string
    task_name: string
    cron: string
    next_run_at: string | null
}

export interface Stats {
    tasks_total: number
    tasks_enabled: number
    runs_running: number
    runs_24h: {
        total: number
        completed: number
        failed: number
        timeout: number
        cancelled: number
    }
    next_runs: NextRun[]
}

export interface SystemSetting {
    scope: string
    key: string
    type: string
    value: Record<string, unknown>
    is_complete: boolean
    description: string | null
    updated_at: string
}

// ---- 脚本 ----

export interface Script {
    id: string
    name: string
    description: string | null
    content: string
    created_at: string
    updated_at: string
}

export interface ScriptPayload {
    name: string
    description: string | null
    content: string
}

export interface ScriptTestResult {
    exit_code: number | null
    stdout: string
    stderr: string
    duration_ms: number
    timed_out: boolean
}

// ---- 监控 ----

export type MonitorKind = 'http' | 'redis' | 'mysql' | 'postgresql' | 'mongo' | 'rabbitmq'

interface MonitorNotificationConfig {
    enabled: boolean
    events: string[]
}

export interface Monitor {
    id: string
    name: string
    kind: MonitorKind
    config: Record<string, unknown>
    interval_seconds: number
    timeout_seconds: number
    enabled: boolean
    notification_config: MonitorNotificationConfig
    next_check_at: string | null
    last_status: number | null
    last_latency_ms: number | null
    last_checked_at: string | null
    last_issue_at: string | null
    consecutive_failures: number
    created_at: string
    updated_at: string
}

export interface MonitorRecentCheck {
    status: number
    checked_at: string
    latency_ms: number | null
    error_message: string | null
}

export interface MonitorCard extends Monitor {
    uptime_24h: number | null
    recent_checks: MonitorRecentCheck[]
}

export interface MonitorPayload {
    name: string
    kind: MonitorKind
    config: Record<string, unknown>
    interval_seconds: number
    timeout_seconds: number
    enabled: boolean
    notification_config: MonitorNotificationConfig
}

export interface MonitorCheck {
    id: string
    monitor_id: string
    status: number
    latency_ms: number | null
    error_code: string | null
    error_message: string | null
    checked_at: string
}

// ---- 备份 ----

export interface BackupInfo {
    filename: string
    size: number
    created_at: string
}

export interface BackupCreateResult extends BackupInfo {
    uploaded: boolean
}

export interface BackupUploadResult {
    filename: string
    platform: string
}

export interface BackupRestoreResult {
    filename: string
    safety_backup: string
    tables: Record<string, number>
}

export interface KryvaBackupInfo {
    filename: string
    size: number
    created_at: string
}
