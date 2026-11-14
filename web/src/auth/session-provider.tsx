import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { me } from '@/api/auth'
import { AUTH_EXPIRED_EVENT, logoutRequest } from '@/api/client'

interface Session {
    loading: boolean
    authenticated: boolean
    username: string | null
    login: () => void
    logout: () => Promise<void>
}

const SessionContext = createContext<Session | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
    const [loading, setLoading] = useState(true)
    const [authenticated, setAuthenticated] = useState(false)
    const [username, setUsername] = useState<string | null>(null)
    const identityRequest = useRef(0)

    const loadIdentity = useCallback(async () => {
        const requestId = ++identityRequest.current
        try {
            const data = await me()
            if (requestId !== identityRequest.current) return
            setUsername(data.username)
            setAuthenticated(true)
        } catch {
            if (requestId !== identityRequest.current) return
            setUsername(null)
            setAuthenticated(false)
        } finally {
            if (requestId === identityRequest.current) setLoading(false)
        }
    }, [])

    useEffect(() => {
        void loadIdentity()
    }, [loadIdentity])

    useEffect(() => {
        const onExpired = () => {
            identityRequest.current += 1
            setAuthenticated(false)
            setUsername(null)
            setLoading(false)
        }
        window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
        return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
    }, [])

    const value = useMemo<Session>(
        () => ({
            loading,
            authenticated,
            username,
            login: () => {
                setAuthenticated(true)
                void loadIdentity()
            },
            logout: () => {
                identityRequest.current += 1
                setAuthenticated(false)
                setUsername(null)
                setLoading(false)
                return logoutRequest()
            },
        }),
        [loading, authenticated, username, loadIdentity],
    )

    return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): Session {
    const context = useContext(SessionContext)
    if (!context) throw new Error('useSession 必须在 SessionProvider 内使用')
    return context
}
