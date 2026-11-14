/** 表单值解析工具(统一各表单的 number/string/boolean 转换)。 */

export function asString(value: unknown, fallback = ''): string {
    if (value == null) return fallback
    return String(value)
}

export function asNumber(value: unknown, fallback: number): number {
    const parsed = typeof value === 'number' ? value : Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
}

export function asBoolean(value: unknown): boolean {
    return Boolean(value)
}

export function toInt(value: string, fallback: number): number {
    return Math.trunc(asNumber(value, fallback))
}

export function toNumber(value: string, fallback: number): number {
    return asNumber(value, fallback)
}
