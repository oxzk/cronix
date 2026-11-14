import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

const fmt = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
})

/** UTC 时间戳 → Asia/Shanghai 展示 */
export function formatTime(iso: string | null | undefined): string {
    if (!iso) return '-'
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return '-'
    const parts = fmt.formatToParts(date)
    const get = (type: string) => parts.find((part) => part.type === type)?.value ?? ''
    return `${get('year')}-${get('month')}-${get('day')} ${get('hour')}:${get('minute')}:${get('second')}`
}

export function formatDuration(ms: number | null | undefined): string {
    if (ms == null) return '-'
    if (ms < 1000) return `${ms}ms`
    const seconds = ms / 1000
    if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)}s`
    const minutes = Math.floor(seconds / 60)
    const rest = Math.round(seconds % 60)
    if (minutes < 60) return `${minutes}m ${String(rest).padStart(2, '0')}s`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ${String(minutes % 60).padStart(2, '0')}m`
}

export function shortId(id: string): string {
    return id.slice(0, 8)
}

export function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    const units = ['KB', 'MB', 'GB']
    let value = bytes / 1024
    let index = 0
    while (value >= 1024 && index < units.length - 1) {
        value /= 1024
        index += 1
    }
    return `${value.toFixed(value < 10 ? 1 : 0)} ${units[index]}`
}

/** UTC 时间戳 → 中文相对时间 */
export function formatRelativeTime(iso: string | null | undefined): string {
    if (!iso) return '-'
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return '-'
    const diff = Date.now() - date.getTime()
    if (diff < 0) return '刚刚'
    const seconds = Math.floor(diff / 1000)
    if (seconds < 60) return '刚刚'
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes} 分钟前`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} 小时前`
    const days = Math.floor(hours / 24)
    return `${days} 天前`
}
