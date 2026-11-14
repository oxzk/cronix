import { useCallback, useState } from 'react'
import { useToast } from '@/components/ui/toast'
import { getErrorMessage } from '@/lib/error'

interface RunOptions {
    success?: string
    error?: string
}

/** 包装异步操作: toast 成功/错误反馈 + per-key busy 状态 */
export function useToastAction() {
    const toast = useToast()
    const [busyKeys, setBusyKeys] = useState<Record<string, boolean>>({})

    const runKeyed = useCallback(
        async (key: string, action: () => Promise<unknown>, options?: RunOptions): Promise<boolean> => {
            setBusyKeys((prev) => ({ ...prev, [key]: true }))
            try {
                await action()
                if (options?.success) toast.success(options.success)
                return true
            } catch (error) {
                toast.error(options?.error ?? '操作失败', getErrorMessage(error))
                return false
            } finally {
                setBusyKeys((prev) => {
                    const next = { ...prev }
                    delete next[key]
                    return next
                })
            }
        },
        [toast],
    )

    const busy = useCallback((key: string) => Boolean(busyKeys[key]), [busyKeys])

    return { runKeyed, busy }
}
