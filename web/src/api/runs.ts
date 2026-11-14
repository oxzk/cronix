import { api } from './client'
import type { LogsResponse, Page, Run } from './types'

interface RunFilters {
    task_id?: string
    status?: number
    trigger?: number
}

export function listRuns(page = 1, pageSize = 20, filters: RunFilters = {}): Promise<Page<Run>> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (filters.task_id) params.set('task_id', filters.task_id)
    if (filters.status != null) params.set('status', String(filters.status))
    if (filters.trigger != null) params.set('trigger', String(filters.trigger))
    return api.get<Page<Run>>(`/api/v1/runs?${params.toString()}`)
}

export function getRun(id: string): Promise<Run> {
    return api.get<Run>(`/api/v1/runs/${id}`)
}

export function getRunLogs(id: string): Promise<LogsResponse> {
    return api.get<LogsResponse>(`/api/v1/runs/${id}/logs`)
}

export function cancelRun(id: string): Promise<boolean> {
    return api.post<boolean>(`/api/v1/runs/${id}/cancel`)
}

export function deleteRun(id: string): Promise<boolean> {
    return api.delete<boolean>(`/api/v1/runs/${id}`)
}
