import { get } from './request'
import type { TaskExecutionResponse, TaskExecutionDetailResponse, ExecutionListParams } from './types'

/**
 * 获取执行记录列表（支持分页和筛选）
 */
export async function getExecutions(
    params?: ExecutionListParams,
): Promise<{
    items: TaskExecutionDetailResponse[]
    total: number
    page: number
    page_size: number
    total_pages: number
}> {
    return await get<{
        items: TaskExecutionDetailResponse[]
        total: number
        page: number
        page_size: number
        total_pages: number
    }>('/executions', params)
}

/**
 * 获取单个执行记录详情
 */
export async function getExecution(executionId: number): Promise<TaskExecutionDetailResponse> {
    return await get<TaskExecutionDetailResponse>(`/executions/${executionId}`)
}
