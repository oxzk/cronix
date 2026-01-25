// API 基础配置
export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'

// API 路径前缀
export const API_PREFIX = '/api'

// 完整的 API 基础 URL
export const getBaseUrl = () => {
  return `${API_BASE_URL}${API_PREFIX}`
}
