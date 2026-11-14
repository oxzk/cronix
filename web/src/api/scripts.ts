import { api } from './client'
import type { Page, Script, ScriptPayload, ScriptTestResult } from './types'

export function listScripts(page = 1, pageSize = 20): Promise<Page<Script>> {
    return api.get<Page<Script>>(`/api/v1/scripts?page=${page}&page_size=${pageSize}`)
}

export function createScript(payload: ScriptPayload): Promise<Script> {
    return api.post<Script>('/api/v1/scripts', payload)
}

export function updateScript(id: string, payload: Partial<ScriptPayload>): Promise<Script> {
    return api.patch<Script>(`/api/v1/scripts/${id}`, payload)
}

export function deleteScript(id: string): Promise<boolean> {
    return api.delete<boolean>(`/api/v1/scripts/${id}`)
}

export function testScript(id: string): Promise<ScriptTestResult> {
    return api.post<ScriptTestResult>(`/api/v1/scripts/${id}/test`)
}
