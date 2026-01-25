import { get, put } from './request'
import type {
  TwoFactorAuthInfo,
  NotificationSchema,
  NotificationResponse,
  UserSchema,
} from './types'

/**
 * 获取 2FA 配置信息
 */
export async function getTwoFactorAuthInfo(): Promise<TwoFactorAuthInfo> {
  return await get<TwoFactorAuthInfo>('/settings/2fa')
}

/**
 * 获取通知配置列表
 */
export async function getNotifications(): Promise<any> {
  return await get<any>('/settings/notifications')
}

/**
 * 更新通知配置
 */
export async function updateNotification(notificationId: number, data: NotificationSchema): Promise<NotificationResponse> {
  return await put<NotificationResponse>(`/settings/notifications/${notificationId}`, data)
}

/**
 * 更新用户设置（密码、2FA 配置）
 */
export async function updateUserSettings(data: UserSchema): Promise<{ message: string; updated_fields: string[] }> {
  return await put<{ message: string; updated_fields: string[] }>('/settings/user', data)
}
