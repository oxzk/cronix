import { useEffect, useState } from 'react'
import { listSettings } from '@/api/system-settings'

/** Pusho 通知配置是否完整; 不完整时事件不可选。 */
export function usePushoConfigured(active: boolean): boolean {
    const [configured, setConfigured] = useState(false)

    useEffect(() => {
        if (!active) return
        let cancelled = false
        listSettings()
            .then((rows) => {
                if (cancelled) return
                const pusho = rows.find(
                    (row) => row.scope === 'notification' && row.key === 'pusho',
                )
                setConfigured(Boolean(pusho?.is_complete))
            })
            .catch(() => {
                if (!cancelled) setConfigured(false)
            })
        return () => {
            cancelled = true
        }
    }, [active])

    return configured
}
