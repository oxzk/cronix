import { useState } from 'react'
import { message } from '../components/ui/message'

/**
 * 通用异步操作 Hook
 */
export function useAsync<T = any>() {
    const [loading, setLoading] = useState(false)

    const execute = async (
        asyncFn: () => Promise<T>,
        options?: {
            onSuccess?: (data: T) => void
            onError?: (error: any) => void
            successMessage?: string
            errorMessage?: string
        },
    ): Promise<T | undefined> => {
        try {
            setLoading(true)
            const result = await asyncFn()

            if (options?.successMessage) {
                message.success(options.successMessage)
            }

            options?.onSuccess?.(result)
            return result
        } catch (error: any) {
            const errorMsg = options?.errorMessage || error.message || '操作失败'
            message.error(errorMsg)
            options?.onError?.(error)
        } finally {
            setLoading(false)
        }
    }

    return { loading, execute }
}
