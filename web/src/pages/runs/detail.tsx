import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { getRun } from '@/api/runs'
import { usePolling } from '@/hooks/use-polling'
import { ErrorBanner } from '@/components/ui/error-banner'
import { getErrorMessage } from '@/lib/error'
import { formatDuration, formatTime } from '@/lib/utils'
import { isTerminalStatus, statusDisplay, triggerLabel } from '@/lib/status'
import { Badge } from '@/components/ui/badge'
import { JsonBlock } from '@/components/ui/json-block'
import { PageHeader } from '@/components/ui/page-header'
import { TableSkeleton } from '@/components/ui/skeleton'
import { LogView } from '@/pages/runs/LogView'
import type { Run } from '@/api/types'

export default function RunDetailPage() {
    const { id } = useParams<{ id: string }>()
    const [run, setRun] = useState<Run | null>(null)
    const [error, setError] = useState<string | null>(null)

    const load = useCallback(async () => {
        if (!id) return
        try {
            const result = await getRun(id)
            setRun(result)
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [id])

    useEffect(() => {
        void load()
    }, [load])

    // 未终态时轮询刷新状态
    const active = !run || !isTerminalStatus(run.status)
    usePolling(load, 3000, active)

    if (error) {
        return (
            <div>
                <PageHeader
                    title="执行详情"
                    actions={
                        <Link
                            to="/runs"
                            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3.5 text-sm font-medium text-slate-900 hover:bg-slate-50"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            返回列表
                        </Link>
                    }
                />
                <ErrorBanner message={error} />
            </div>
        )
    }

    if (!run) {
        return (
            <div>
                <PageHeader title="执行详情" />
                <TableSkeleton rows={4} />
            </div>
        )
    }

    const display = statusDisplay(run.status)
    const fields = [
        { label: '触发方式', value: triggerLabel(run.trigger) },
        { label: '尝试次数', value: `第 ${run.attempt} 次` },
        { label: '计划时间', value: formatTime(run.scheduled_at) },
        { label: '开始时间', value: formatTime(run.started_at) },
        { label: '结束时间', value: formatTime(run.completed_at) },
        { label: '耗时', value: formatDuration(run.duration_ms) },
    ]
    // 退出码 0 是成功默认值, 不展示; 仅异常退出时显示
    if (run.exit_code != null && run.exit_code !== 0) {
        fields.push({ label: '退出码', value: String(run.exit_code) })
    }

    return (
        <div>
            <PageHeader
                title={
                    <span className="flex flex-wrap items-baseline gap-2">
                        执行详情
                        <span className="text-sm font-normal text-slate-400">{run.task_name ?? '-'}</span>
                    </span>
                }
                actions={
                    <Link
                        to="/runs"
                        className="inline-flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3.5 text-sm font-medium text-slate-900 hover:bg-slate-50"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        返回列表
                    </Link>
                }
            />

            <div className="surface p-5">
                <div className="mb-4 flex items-center gap-3">
                    <h2 className="text-sm font-medium text-slate-700">执行状态</h2>
                    <Badge tone={display.tone}>{display.label}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-x-8 gap-y-3 lg:grid-cols-4">
                    {fields.map((field) => (
                        <div key={field.label}>
                            <p className="text-xs text-slate-400">{field.label}</p>
                            <p className="mt-0.5 truncate text-sm text-slate-900">{field.value}</p>
                        </div>
                    ))}
                </div>
                {run.error_message && (
                    <div className="mt-4">
                        <p className="mb-1.5 text-xs text-slate-400">错误</p>
                        <JsonBlock value={run.error_message} />
                    </div>
                )}
            </div>

            <h2 className="mt-6 mb-3 text-sm font-medium text-slate-700">运行日志</h2>
            <LogView runId={run.id} terminal={isTerminalStatus(run.status)} />
        </div>
    )
}
