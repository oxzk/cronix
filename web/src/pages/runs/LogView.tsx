import { useCallback, useEffect, useState } from 'react'
import { getRunLogs } from '@/api/runs'
import { usePolling } from '@/hooks/use-polling'
import { cn } from '@/lib/utils'
import type { LogEntry } from '@/api/types'

const LEVEL_COLORS: Record<string, string> = {
    TRACE: 'text-slate-500',
    DEBUG: 'text-slate-400',
    INFO: 'text-slate-300',
    SUCCESS: 'text-emerald-400',
    WARNING: 'text-amber-400',
    ERROR: 'text-rose-400',
    CRITICAL: 'text-rose-300',
}

/** 运行日志: 终态取一次快照; 运行中每 2s 轮询直到终态 */
export function LogView({ runId, terminal }: { runId: string; terminal: boolean }) {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [persisted, setPersisted] = useState(false)

    const load = useCallback(async () => {
        try {
            const data = await getRunLogs(runId)
            setLogs(data.logs)
            setPersisted(data.persisted)
        } catch {
            // 单次失败下次轮询重试
        }
    }, [runId])

    const done = terminal || persisted

    useEffect(() => {
        void load()
    }, [load])

    usePolling(load, 2000, !done)

    return (
        <div className="overflow-hidden rounded-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50/60 px-4 py-2">
                <span className="flex items-center gap-2 text-xs text-slate-500">
                    <span
                        className={cn(
                            'h-1.5 w-1.5 rounded-full',
                            done ? 'bg-slate-300' : 'animate-pulse bg-emerald-500',
                        )}
                    />
                    {done ? '已结束' : '实时输出(每 2 秒刷新)'}
                </span>
            </div>
            <div className="max-h-[60vh] overflow-auto bg-slate-900 p-4">
                {logs.length === 0 ? (
                    <p className="font-mono text-[13px] text-slate-500">暂无输出</p>
                ) : (
                    <div className="font-mono text-[13px] leading-6">
                        {logs.map((entry, index) => (
                            <div key={index} className="whitespace-pre-wrap break-all">
                                <span className="text-slate-500">[{entry.timestamp.slice(11, 19)}]</span>{' '}
                                <span
                                    className={cn(
                                        'inline-block w-14 font-medium',
                                        LEVEL_COLORS[entry.level] ?? 'text-slate-400',
                                    )}
                                >
                                    {entry.level}
                                </span>{' '}
                                <span className="text-slate-200">{entry.message}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
