import { post } from './request'
import type { UserSchema, Token } from './types'

/**
 * 用户登录
 */
export async function login(credentials: UserSchema): Promise<Token> {
  return await post<Token>('/auth/login', credentials)
}

/**
 * 登出（清除本地存储的 token）
 */
export function logout(): void {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('isAuthenticated')
}

/**
 * 保存 token 到本地存储
 */
export function saveToken(token: string): void {
  localStorage.setItem('auth_token', token)
  localStorage.setItem('isAuthenticated', 'true')
  // 触发自定义事件，通知 App 组件认证状态已改变
  window.dispatchEvent(new Event('authChange'))
}

/**
 * 检查是否已认证
 */
export function isAuthenticated(): boolean {
  return localStorage.getItem('isAuthenticated') === 'true' && !!localStorage.getItem('auth_token')
}
