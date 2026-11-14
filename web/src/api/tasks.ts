import { api } from './client'
import type { Page, Run, Task, TaskPayload } from './types'

export function listTasks(page = 1, pageSize = 20): Promise<Page<Task>> {
    return api.get<Page<Task>>(`/api/v1/tasks?page=${page}&page_size=${pageSize}`)
}

export function getTask(id: string): Promise<Task> {
    return api.get<Task>(`/api/v1/tasks/${id}`)
}

export function createTask(payload: TaskPayload): Promise<Task> {
    return api.post<Task>('/api/v1/tasks', payload)
}

export function updateTask(id: string, payload: Partial<TaskPayload>): Promise<Task> {
    return api.patch<Task>(`/api/v1/tasks/${id}`, payload)
}

export function deleteTask(id: string): Promise<boolean> {
    return api.delete<boolean>(`/api/v1/tasks/${id}`)
}

export function runTask(id: string): Promise<Run> {
    return api.post<Run>(`/api/v1/tasks/${id}/run`)
}

export function cancelTask(id: string): Promise<number> {
    return api.post<number>(`/api/v1/tasks/${id}/cancel`)
}
