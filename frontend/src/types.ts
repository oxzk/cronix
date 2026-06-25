export type JsonRecord = Record<string, unknown>;

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface User {
  id: number;
  username: string;
}

export interface SettingsUser extends User {
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TaskStats {
  total_tasks: number;
  active_tasks: number;
  inactive_tasks: number;
  total_executions: number;
  success_executions: number;
  failed_executions: number;
  running_executions: number;
  success_rate: number | null;
}

export type NotifyStrategy = "never" | "always" | "on_failure";

export type NotifyType = "webhook" | "telegram" | "dingtalk";

export interface NotificationSetting {
  id: number;
  notify_type: NotifyType;
  config: JsonRecord;
  created_at: string;
  updated_at: string;
}

export interface NotificationPayload {
  notify_type: NotifyType;
  config: JsonRecord;
}

export interface TaskPayload {
  name: string;
  description?: string | null;
  cron_expression: string;
  command: string;
  is_active: boolean;
  timeout: number;
  retry_count: number;
  retry_interval: number;
  notification_ids?: number[] | null;
  notify_strategy: NotifyStrategy;
}

export interface Task extends TaskPayload {
  id: number;
  next_run_time: string | null;
  created_at: string;
  updated_at: string;
}

export type ExecutionStatus = "pending" | "running" | "success" | "failed" | "timeout" | "cancelled";

export interface Execution {
  id: number;
  task_id: number;
  task: Task | null;
  started_at: string;
  finished_at: string | null;
  status: ExecutionStatus;
  output: string | null;
  error: string | null;
  retry_attempt: number;
  duration: number | null;
}
