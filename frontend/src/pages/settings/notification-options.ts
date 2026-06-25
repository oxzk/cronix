import type { JsonRecord, NotificationPayload, NotificationSetting, NotifyType } from "@/types";

export interface NotificationField {
  /**
   * 配置字段键名。
   */
  key: string;
  /**
   * 配置字段名称。
   */
  label: string;
  /**
   * 输入框类型。
   */
  type?: "text" | "password" | "url";
  /**
   * 输入框占位文本。
   */
  placeholder?: string;
}

export interface NotificationOption {
  /**
   * 通知渠道类型。
   */
  type: NotifyType;
  /**
   * 通知渠道名称。
   */
  label: string;
  /**
   * 通知渠道说明。
   */
  description: string;
  /**
   * 通知渠道字段。
   */
  fields: NotificationField[];
}

export const notificationOptions: NotificationOption[] = [
  {
    type: "webhook",
    label: "Webhook",
    description: "HTTP 回调通知",
    fields: [{ key: "url", label: "Webhook URL", type: "url", placeholder: "https://example.com/webhook" }],
  },
  {
    type: "telegram",
    label: "Telegram",
    description: "Bot 消息通知",
    fields: [
      { key: "bot_token", label: "Bot Token", type: "password" },
      { key: "chat_id", label: "Chat ID" },
    ],
  },
  {
    type: "dingtalk",
    label: "钉钉",
    description: "钉钉机器人通知",
    fields: [
      { key: "webhook_url", label: "Webhook URL", type: "url", placeholder: "https://oapi.dingtalk.com/robot/send?access_token=..." },
      { key: "secret", label: "加签密钥", type: "password" },
    ],
  },
];

/**
 * 建立通知配置索引。
 */
export function indexNotifications(notifications: NotificationSetting[]): Partial<Record<NotifyType, NotificationSetting>> {
  return Object.fromEntries(notifications.map((notification) => [notification.notify_type, notification])) as Partial<Record<NotifyType, NotificationSetting>>;
}

/**
 * 创建空通知草稿。
 */
export function createEmptyNotificationDrafts(): Record<NotifyType, Record<string, string>> {
  return Object.fromEntries(
    notificationOptions.map((option) => [option.type, Object.fromEntries(option.fields.map((field) => [field.key, ""]))]),
  ) as Record<NotifyType, Record<string, string>>;
}

/**
 * 从后端配置创建通知草稿。
 */
export function createNotificationDrafts(notifications: NotificationSetting[]): Record<NotifyType, Record<string, string>> {
  const drafts = createEmptyNotificationDrafts();
  for (const notification of notifications) {
    const option = notificationOptions.find((item) => item.type === notification.notify_type);
    if (!option) continue;
    for (const field of option.fields) {
      drafts[notification.notify_type][field.key] = readConfigValue(notification.config, field.key);
    }
  }
  return drafts;
}

/**
 * 构建通知保存请求。
 */
export function buildNotificationPayload(type: NotifyType, draft: Record<string, string>): NotificationPayload {
  return {
    notify_type: type,
    config: Object.fromEntries(Object.entries(draft).map(([key, value]) => [key, value.trim()])),
  };
}

/**
 * 读取通知渠道名称。
 */
export function readNotificationLabel(type: NotifyType): string {
  return notificationOptions.find((option) => option.type === type)?.label ?? type;
}

/**
 * 读取 JSON 配置字段。
 */
function readConfigValue(config: JsonRecord, key: string): string {
  const value = config[key];
  if (typeof value === "number") return String(value);
  if (typeof value === "string") return value;
  return "";
}
