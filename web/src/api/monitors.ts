import { api } from './client'
import type { Monitor, MonitorCheck, MonitorCard, MonitorPayload, Page } from './types'

export function listMonitors(): Promise<MonitorCard[]> {
    return api.get<MonitorCard[]>('/api/v1/monitors')
}

export function createMonitor(payload: MonitorPayload): Promise<Monitor> {
    return api.post<Monitor>('/api/v1/monitors', payload)
}

export function updateMonitor(id: string, payload: Partial<MonitorPayload>): Promise<Monitor> {
    return api.patch<Monitor>(`/api/v1/monitors/${id}`, payload)
}

export function deleteMonitor(id: string): Promise<boolean> {
    return api.delete<boolean>(`/api/v1/monitors/${id}`)
}

export function checkMonitor(id: string): Promise<MonitorCheck> {
    return api.post<MonitorCheck>(`/api/v1/monitors/${id}/check`)
}

export function listMonitorChecks(id: string, page = 1, pageSize = 20): Promise<Page<MonitorCheck>> {
    return api.get<Page<MonitorCheck>>(
        `/api/v1/monitors/${id}/checks?page=${page}&page_size=${pageSize}`,
    )
}
