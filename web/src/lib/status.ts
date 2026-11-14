type Tone = 'default' | 'success' | 'warning' | 'danger'

interface StatusDisplay {
    code: string
    label: string
    tone: Tone
}

const STATUS_MAP: Record<number, StatusDisplay> = {
    0: { code: 'pending', label: '排队', tone: 'default' },
    1: { code: 'running', label: '运行中', tone: 'success' },
    2: { code: 'completed', label: '成功', tone: 'success' },
    3: { code: 'failed', label: '失败', tone: 'danger' },
    4: { code: 'cancelled', label: '已取消', tone: 'default' },
    5: { code: 'timeout', label: '超时', tone: 'warning' },
}

export function statusDisplay(status: number): StatusDisplay {
    return STATUS_MAP[status] ?? { code: 'unknown', label: '未知', tone: 'default' }
}

const TRIGGER_MAP: Record<number, string> = { 0: '手动', 1: '调度' }

export function triggerLabel(trigger: number): string {
    return TRIGGER_MAP[trigger] ?? '未知'
}

export function isTerminalStatus(status: number): boolean {
    return status >= 2 && status <= 5
}
