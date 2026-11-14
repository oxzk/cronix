import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { ApiError } from '@/lib/error'

export const AUTH_EXPIRED_EVENT = 'cronix:auth-expired'

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]'])

/** 开发时把 localhost / 127.0.0.1 对齐到页面主机, 保证刷新 Cookie 同站可发送。 */
function resolveBaseUrl(): string {
    const configured = (import.meta.env.VITE_API_BASE_URL ?? '').trim()
    if (!configured) return ''
    if (!import.meta.env.DEV) {
        try {
            // 防止开发环境的回环地址被打进生产包; 生产默认同源。
            if (LOOPBACK_HOSTS.has(new URL(configured).hostname)) return ''
        } catch {
            return configured.replace(/\/+$/, '')
        }
        return configured.replace(/\/+$/, '')
    }
    try {
        const api = new URL(configured)
        const page = new URL(window.location.origin)
        if (
            LOOPBACK_HOSTS.has(api.hostname) &&
            LOOPBACK_HOSTS.has(page.hostname) &&
            api.hostname !== page.hostname
        ) {
            api.hostname = page.hostname
        }
        return api.toString().replace(/\/+$/, '')
    } catch {
        return configured.replace(/\/+$/, '')
    }
}

const API_BASE_URL = resolveBaseUrl()

interface Envelope<T> {
    success?: boolean
    data?: T
    error?: { code?: string; message?: string; details?: unknown }
}

interface RequestOptions {
    skipAuth?: boolean
    retryOn401?: boolean
}

/** Axios 请求客户端: Bearer 鉴权、统一信封解析、401 单飞刷新与重试。 */
class ApiClient {
    private readonly http: AxiosInstance
    private accessToken: string | null = null
    private sessionVersion = 0
    private refreshAllowed = true
    private refreshPromise: Promise<boolean> | null = null
    private refreshController: AbortController | null = null

    constructor(baseURL: string) {
        this.http = axios.create({
            baseURL,
            withCredentials: true,
            headers: { Accept: 'application/json' },
        })
    }

    /** access token 只保存在内存; 页面重载后使用 HttpOnly refresh Cookie 恢复。 */
    setAccessToken(token: string | null): void {
        this.sessionVersion += 1
        this.accessToken = token?.trim() || null
        this.refreshAllowed = this.accessToken !== null
        this.refreshController?.abort()
        this.refreshController = null
        this.refreshPromise = null
    }

    get<T>(path: string, options?: RequestOptions): Promise<T> {
        return this.request<T>('GET', path, undefined, options)
    }

    post<T>(path: string, data?: unknown, options?: RequestOptions): Promise<T> {
        return this.request<T>('POST', path, data, options)
    }

    put<T>(path: string, data?: unknown, options?: RequestOptions): Promise<T> {
        return this.request<T>('PUT', path, data, options)
    }

    patch<T>(path: string, data?: unknown, options?: RequestOptions): Promise<T> {
        return this.request<T>('PATCH', path, data, options)
    }

    delete<T>(path: string, options?: RequestOptions): Promise<T> {
        return this.request<T>('DELETE', path, undefined, options)
    }

    /** 退出登录: 立即清除内存 token, 再清除服务端 HttpOnly Cookie。 */
    async logout(): Promise<void> {
        const token = this.accessToken
        this.setAccessToken(null)
        try {
            await this.http.post('/api/v1/auth/logout', undefined, {
                headers: token ? { Authorization: `Bearer ${token}` } : undefined,
            })
        } catch {
            // 静默失败, 本地会话态仍会清除
        }
    }

    private async request<T>(
        method: string,
        path: string,
        data?: unknown,
        options: RequestOptions = {},
        retried = false,
        sessionVersion = this.sessionVersion,
    ): Promise<T> {
        if (!options.skipAuth) {
            if (!this.accessToken && !(await this.singleFlightRefresh())) {
                this.expireSession(sessionVersion)
                throw new ApiError(401, 'auth_expired', '登录已过期, 请重新登录')
            }
            this.ensureCurrentSession(sessionVersion)
        }

        const token = options.skipAuth ? null : this.accessToken
        let response: AxiosResponse<Envelope<T>>
        try {
            response = await this.http.request<Envelope<T>>({
                method,
                url: path,
                data,
                headers: token ? { Authorization: `Bearer ${token}` } : undefined,
                validateStatus: () => true,
            })
        } catch (error) {
            throw new ApiError(
                0,
                'network_error',
                error instanceof Error ? error.message : '网络请求失败',
            )
        }

        if (!options.skipAuth) {
            this.ensureCurrentSession(sessionVersion)
            if (response.status === 401) {
                if (options.retryOn401 !== false && !retried) {
                    // 其他请求已刷新时直接使用新 token, 避免迟到的 401 再次刷新。
                    const alreadyRefreshed = this.accessToken !== null && this.accessToken !== token
                    if (alreadyRefreshed || (await this.singleFlightRefresh())) {
                        return this.request<T>(method, path, data, options, true, sessionVersion)
                    }
                }
                this.expireSession(sessionVersion)
            }
        }

        const envelope = response.data
        if (response.status < 200 || response.status >= 300 || !envelope?.success) {
            throw new ApiError(
                response.status,
                envelope?.error?.code ?? 'http_error',
                envelope?.error?.message ?? `请求失败(${response.status})`,
                envelope?.error?.details,
            )
        }
        return envelope.data as T
    }

    private ensureCurrentSession(sessionVersion: number): void {
        if (sessionVersion !== this.sessionVersion) {
            throw new ApiError(401, 'auth_expired', '登录状态已变更, 请重试')
        }
    }

    private expireSession(sessionVersion: number): void {
        if (sessionVersion !== this.sessionVersion) return
        this.setAccessToken(null)
        window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT))
    }

    private async refreshSession(sessionVersion: number, signal: AbortSignal): Promise<boolean> {
        try {
            // 刷新接口只使用 refresh Cookie, 不能携带 access token。
            const response = await this.http.post<Envelope<{ access_token: string }>>(
                '/api/v1/auth/refresh',
                undefined,
                { signal, validateStatus: () => true },
            )
            const token = response.data?.data?.access_token
            if (
                response.status < 200 ||
                response.status >= 300 ||
                !response.data?.success ||
                typeof token !== 'string' ||
                !token.trim() ||
                sessionVersion !== this.sessionVersion ||
                !this.refreshAllowed
            ) {
                return false
            }
            this.accessToken = token.trim()
            return true
        } catch {
            return false
        }
    }

    private singleFlightRefresh(): Promise<boolean> {
        // 会话已明确失效或退出后不再自动刷新, 等待用户重新登录。
        if (!this.refreshAllowed) return Promise.resolve(false)
        if (this.refreshPromise) return this.refreshPromise

        const controller = new AbortController()
        this.refreshController = controller
        const promise: Promise<boolean> = this.refreshSession(
            this.sessionVersion,
            controller.signal,
        ).finally(() => {
            if (this.refreshPromise === promise) {
                this.refreshPromise = null
                this.refreshController = null
            }
        })
        this.refreshPromise = promise
        return promise
    }
}

export const api = new ApiClient(API_BASE_URL)

/** 退出登录: 清除服务端 HttpOnly Cookie。 */
export async function logoutRequest(): Promise<void> {
    await api.logout()
}