import { api } from './client'
import type { SystemSetting } from './types'

export function listSettings(): Promise<SystemSetting[]> {
    return api.get<SystemSetting[]>('/api/v1/system-settings')
}

export function putSetting(scope: string, key: string, value: Record<string, unknown>): Promise<SystemSetting> {
    return api.put<SystemSetting>(`/api/v1/system-settings/${scope}/${key}`, { value })
}
