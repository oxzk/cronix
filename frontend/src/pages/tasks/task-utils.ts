import type { NotificationSetting, NotifyStrategy, Task, TaskPayload } from "@/types";

export const defaultTaskPayload: TaskPayload = {
  name: "",
  description: "",
  cron_expression: "*/5 * * * *",
  command: "",
  is_active: true,
  timeout: 300,
  retry_count: 0,
  retry_interval: 60,
  notification_ids: null,
  notify_strategy: "never",
};

export const notifyStrategyOptions: Array<{ value: NotifyStrategy; label: string }> = [
  { value: "never", label: "不通知" },
  { value: "always", label: "每次完成后通知" },
  { value: "on_failure", label: "仅失败时通知" },
];

/**
 * 构建任务更新请求数据。
 */
export function buildTaskPayload(task: Task, isActive: boolean): TaskPayload {
  return {
    name: task.name,
    description: task.description || null,
    cron_expression: task.cron_expression,
    command: task.command,
    is_active: isActive,
    timeout: task.timeout,
    retry_count: task.retry_count,
    retry_interval: task.retry_interval,
    notification_ids: task.notification_ids ?? null,
    notify_strategy: task.notify_strategy,
  };
}

/**
 * 任务弹窗初始数据。
 */
export function toTaskDialogPayload(task: Task | null): TaskPayload {
  if (!task) return defaultTaskPayload;
  return {
    name: task.name,
    description: task.description || "",
    cron_expression: task.cron_expression,
    command: task.command,
    is_active: task.is_active,
    timeout: task.timeout,
    retry_count: task.retry_count,
    retry_interval: task.retry_interval,
    notification_ids: task.notification_ids ?? null,
    notify_strategy: task.notify_strategy,
  };
}

/**
 * 规范化通知 ID 列表。
 */
export function normalizeNotificationIds(notificationIds: number[] | null | undefined): number[] | null {
  return notificationIds?.length ? notificationIds : null;
}

/**
 * 格式化通知名称。
 */
export function formatNotificationName(notification: NotificationSetting): string {
  if (notification.notify_type === "webhook") return "Webhook";
  if (notification.notify_type === "telegram") return "Telegram";
  return "钉钉";
}
