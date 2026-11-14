import cronstrue from 'cronstrue/i18n'

const CRON_FIELDS = 5

export function cronFieldCount(expr: string): number {
    const trimmed = expr.trim()
    return trimmed ? trimmed.split(/\s+/).length : 0
}

/** cron 中文描述; 仅接受 5 段标准表达式, 不合法返回 null */
export function describeCron(expr: string): string | null {
    const trimmed = expr.trim()
    if (!trimmed || cronFieldCount(trimmed) !== CRON_FIELDS) return null
    try {
        return cronstrue.toString(trimmed, { locale: 'zh_CN' })
    } catch {
        return null
    }
}
