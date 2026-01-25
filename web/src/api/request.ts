import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getBaseUrl } from './config'
import { message } from '../lib/message'

export interface RequestConfig {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
    params?: Record<string, any>
    data?: any
}

export class ApiError extends Error {
    status: number
    data?: any

    constructor(message: string, status: number, data?: any) {
        super(message)
        this.status = status
        this.data = data
        this.name = 'ApiError'
    }
}

/**
 * ApiClient - 封装 axios 的 HTTP 请求客户端
 */
class ApiClient {
    private client: AxiosInstance
    private static instance: ApiClient | null = null

    constructor(baseURL?: string) {
        this.client = axios.create({
            baseURL: baseURL || getBaseUrl(),
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 60000, // 60秒超时
        })

        this.setupInterceptors()
    }

    /**
     * 获取单例实例
     */
    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient()
        }
        return ApiClient.instance
    }

    /**
     * 设置请求和响应拦截器
     */
    private setupInterceptors(): void {
        // 请求拦截器
        this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
            const token = this.getToken()
            if (token && config.headers) {
                config.headers.Authorization = `Bearer ${token}`
            }
            if (config.url) {
                config.url = config.url.replace(/^\/+/, '')
            }
            return config
        })

        // 响应拦截器
        this.client.interceptors.response.use(
            (response) => {
                if (response.status === 204) return undefined
                const data = response.data as any
                if (data?.code !== undefined && data.code !== 200) {
                    const errorMessage = data?.message || '请求失败'
                    message.error(errorMessage)
                    throw new ApiError(errorMessage, response.status, data)
                }
                return data?.data
            },
            (error: AxiosError) => {
                const responseData = error.response?.data as any
                const errorMessage =
                    error.code === 'ECONNABORTED'
                        ? '请求超时，请稍后重试'
                        : error.response
                          ? responseData?.detail || responseData?.message || '请求失败'
                          : error.request
                            ? '网络错误，请检查网络连接'
                            : error.message || '请求配置错误'

                message.error(errorMessage)
                throw new ApiError(errorMessage, error.response?.status || 0, error.response?.data)
            },
        )
    }

    /**
     * 获取认证 token
     */
    private getToken(): string | null {
        return localStorage.getItem('auth_token')
    }

    /**
     * 基础请求方法
     */
    private async request<T>(path: string, config: RequestConfig = {}): Promise<T> {
        const { method = 'GET', params, data } = config
        const response = await this.client.request<T>({ url: path, method, params, data })
        return response as T
    }

    /**
     * GET 请求
     */
    public get<T>(path: string, params?: Record<string, any>): Promise<T> {
        return this.request<T>(path, { method: 'GET', params })
    }

    /**
     * POST 请求
     */
    public post<T>(path: string, data?: any): Promise<T> {
        return this.request<T>(path, { method: 'POST', data })
    }

    /**
     * PUT 请求
     */
    public put<T>(path: string, data?: any): Promise<T> {
        return this.request<T>(path, { method: 'PUT', data })
    }

    /**
     * DELETE 请求
     */
    public delete<T>(path: string): Promise<T> {
        return this.request<T>(path, { method: 'DELETE' })
    }

    /**
     * PATCH 请求
     */
    public patch<T>(path: string, data?: any): Promise<T> {
        return this.request<T>(path, { method: 'PATCH', data })
    }

    /**
     * 获取原始 axios 实例（用于特殊场景）
     */
    public getClient(): AxiosInstance {
        return this.client
    }
}

// 导出单例实例
const apiClient = ApiClient.getInstance()

// 导出便捷方法，保持向后兼容
export const get = <T>(path: string, params?: Record<string, any>): Promise<T> => apiClient.get<T>(path, params)

export const post = <T>(path: string, data?: any): Promise<T> => apiClient.post<T>(path, data)

export const put = <T>(path: string, data?: any): Promise<T> => apiClient.put<T>(path, data)

export const del = <T>(path: string): Promise<T> => apiClient.delete<T>(path)

// 导出类本身，方便需要时创建新实例
export { ApiClient }
export default apiClient
