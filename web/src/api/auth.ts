import { api } from './client'

interface TokenPair {
    access_token: string
    refresh_token: string
    token_type: string
}

interface TotpStatus {
    enabled: boolean
}

export interface TotpSetup {
    secret: string
    uri: string
}

export async function login(username: string, password: string, code?: string): Promise<TokenPair> {
    const body: Record<string, string> = { username, password }
    if (code) body.code = code
    const tokens = await api.post<TokenPair>('/api/v1/auth/login', body, { skipAuth: true })
    api.setAccessToken(tokens.access_token)
    return tokens
}

export function me(): Promise<{ username: string }> {
    return api.get<{ username: string }>('/api/v1/auth/me')
}

export function getTotpStatus(): Promise<TotpStatus> {
    return api.get<TotpStatus>('/api/v1/auth/totp')
}

export function setupTotp(): Promise<TotpSetup> {
    return api.post<TotpSetup>('/api/v1/auth/totp/setup')
}

export function enableTotp(code: string): Promise<boolean> {
    return api.post<boolean>('/api/v1/auth/totp/enable', { code })
}

export function disableTotp(code: string): Promise<boolean> {
    return api.post<boolean>('/api/v1/auth/totp/disable', { code })
}
