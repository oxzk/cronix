import { get, post, put, del } from './request'
import type {
  ScriptSchema,
  ScriptResponse,
  ScriptListItem,
  ScriptTreeNode,
} from './types'

/**
 * 获取脚本列表（树形结构）
 */
export async function getScripts(): Promise<ScriptTreeNode[]> {
  return await get<ScriptTreeNode[]>('/scripts')
}

/**
 * 获取单个脚本
 */
export async function getScript(scriptName: string): Promise<ScriptResponse> {
  return await get<ScriptResponse>(`/scripts/${scriptName}`)
}

/**
 * 创建脚本
 */
export async function createScript(script: ScriptSchema): Promise<ScriptResponse> {
  return await post<ScriptResponse>('/scripts', script)
}

/**
 * 更新脚本
 */
export async function updateScript(scriptName: string, script: ScriptSchema): Promise<ScriptResponse> {
  return await put<ScriptResponse>(`/scripts/${scriptName}`, script)
}

/**
 * 删除脚本
 */
export async function deleteScript(scriptName: string): Promise<void> {
  return del<void>(`/scripts/${scriptName}`)
}
