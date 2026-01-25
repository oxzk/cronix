import { get, post, put, del } from './request'
import type { TaskSchema, TaskResponse, TaskListParams } from './types'

/**
 * 获取任务列表（分页）
 */
export async function getTasks(
    params?: TaskListParams,
): Promise<{ items: TaskResponse[]; total: number; page: number; page_size: number; total_pages: number }> {
    return await get<{ items: TaskResponse[]; total: number; page: number; page_size: number; total_pages: number }>(
        '/tasks',
        params,
    )
}

/**
 * 获取单个任务
 */
export async function getTask(taskId: number): Promise<TaskResponse> {
    return await get<TaskResponse>(`/tasks/${taskId}`)
}

/**
 * 创建任务
 */
export async function createTask(task: TaskSchema): Promise<TaskResponse> {
    return await post<TaskResponse>('/tasks', task)
}

/**
 * 更新任务
 */
export async function updateTask(taskId: number, task: Partial<TaskSchema>): Promise<TaskResponse> {
    return await put<TaskResponse>(`/tasks/${taskId}`, task)
}

/**
 * 删除任务
 */
export async function deleteTask(taskId: number): Promise<void> {
    return del<void>(`/tasks/${taskId}`)
}

/**
 * 取消运行中的任务
 */
export async function cancelTask(taskId: number): Promise<{ message: string }> {
    return await post<{ message: string }>(`/tasks/${taskId}/cancel`)
}

/**
 * 获取正在运行的任务列表
 */
export async function getRunningTasks(): Promise<number[]> {
    return await get<number[]>('/tasks/running/list')
}

/**
 * 手动执行任务
 */
export async function executeTask(taskId: number): Promise<{ message: string }> {
    return await post<{ message: string }>(`/tasks/${taskId}/execute`)
}
