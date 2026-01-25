// 通用类型定义
export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

// 统一响应格式
export interface ApiResponse<T> {
    code: number
    message: string
    data: T
}

// 分页响应包装
export interface PaginatedApiResponse<T> {
    code: number
    message: string
    data: {
        items: T[]
        total: number
        page: number
        page_size: number
        total_pages: number
    }
}

// 执行状态枚举
export enum ExecutionStatus {
    PENDING = 'pending',
    RUNNING = 'running',
    SUCCESS = 'success',
    FAILED = 'failed',
    TIMEOUT = 'timeout',
    CANCELLED = 'cancelled',
}

// 通知类型枚举
export enum NotifyType {
    WEBHOOK = 'webhook',
    TELEGRAM = 'telegram',
    DINGTALK = 'dingtalk',
}

// ==================== 认证相关 ====================
export interface UserSchema {
    username?: string
    password?: string
    totp_code?: string
    is_2fa_enabled?: boolean
    totp_secret_key?: string
}

export interface Token {
    access_token: string
    token_type: string
}

// ==================== 任务相关 ====================
export interface TaskSchema {
    name: string
    description?: string
    cron_expression: string
    command: string
    is_active?: boolean
    timeout?: number
    retry_count?: number
    retry_interval?: number
    notification_ids?: number[]
}

export interface NotificationResponse {
    id: number
    notify_type: NotifyType
    config: Record<string, any>
    created_at: string
    updated_at: string
}

export interface TaskResponse {
    id: number
    name: string
    description?: string | null
    cron_expression: string
    command: string
    is_active: boolean
    timeout: number
    retry_count: number
    retry_interval: number
    notifications?: NotificationResponse[] | null
    next_run_time?: string | null
    created_at: string
    updated_at: string
}

export interface TaskListParams {
    page?: number
    page_size?: number
    name?: string
    is_active?: boolean
}

// ==================== 执行记录相关 ====================
export interface TaskExecutionResponse {
    id: number
    task_id: number
    started_at: string
    finished_at: string | null
    status: ExecutionStatus
    output: string | null
    error: string | null
    retry_attempt: number
    duration: number | null
}

export interface TaskExecutionDetailResponse extends TaskExecutionResponse {
    task?: TaskResponse
}

export interface ExecutionListParams {
    task_id?: number
    status?: ExecutionStatus
    page?: number
    page_size?: number
}

// ==================== 脚本相关 ====================
export enum ScriptType {
    PYTHON = 'python',
    NODE = 'node',
    SHELL = 'shell',
}

export interface ScriptSchema {
    name: string
    type: ScriptType
    content: string
}

export interface ScriptResponse {
    name: string
    type: ScriptType
    content: string
    path: string
}

export interface ScriptListItem {
    name: string
    type: ScriptType
    path: string
}

export interface ScriptTreeNode {
    name: string
    type: 'file' | 'directory'
    path: string
    script_type?: ScriptType
    children?: ScriptTreeNode[]
}

// ==================== 设置相关 ====================
export interface NotificationConfigWebhook {
    url: string
}

export interface NotificationConfigTelegram {
    bot_token: string
    chat_id: string | number
}

export interface NotificationConfigDingtalk {
    webhook_url: string
    secret: string
}

export type NotificationConfig = NotificationConfigWebhook | NotificationConfigTelegram | NotificationConfigDingtalk

export interface NotificationSchema {
    notify_type: NotifyType
    config: NotificationConfig
}

export interface NotificationListItem {
    id: number
    notify_type: NotifyType
    [key: string]: any
}

export interface TwoFactorAuthInfo {
    totp_secret_key: string
    totp_uri: string
    is_2fa_enabled: boolean
}
