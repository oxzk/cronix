import { useEffect, useRef } from 'react'

/** 固定间隔轮询: 回调变化不重建定时器, enabled 控制启停。 */
export function usePolling(
    callback: () => void | Promise<void>,
    intervalMs: number,
    enabled = true,
): void {
    const saved = useRef(callback)
    useEffect(() => {
        saved.current = callback
    }, [callback])

    useEffect(() => {
        if (!enabled) return
        const timer = window.setInterval(() => void saved.current(), intervalMs)
        return () => window.clearInterval(timer)
    }, [intervalMs, enabled])
}
