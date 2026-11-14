import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStats } from '@/api/stats'
import { listRuns } from '@/api/runs'
import { usePolling } from '@/hooks/use-polling'
import { ErrorBanner } from '@/components/ui/error-banner'
import { getErrorMessage } from '@/lib/error'
import { formatDuration, formatTime, shortId } from '@/lib/utils'
import { statusDisplay } from '@/lib/status'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { TableSkeleton } from '@/components/ui/skeleton'
import {
    DataTable,
    DataTableBody,
    DataTableCell,
    DataTableHead,
    DataTableHeader,
    DataTableRow,
    TableCard,
} from '@/components/ui/table'
import type { Page, Run, Stats } from '@/api/types'

export default function DashboardPage() {
    const [stats, setStats] = useState<Stats | null>(null)
    const [failures, setFailures] = useState<Page<Run> | null>(null)
    const [error, setError] = useState<string | null>(null)

    const load = useCallback(async () => {
        try {
            const [nextStats, nextFailures] = await Promise.all([
                getStats(),
                listRuns(1, 5, { status: 3 }),
            ])
            setStats(nextStats)
            setFailures(nextFailures)
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [])

    useEffect(() => {
        void load()
    }, [load])

    usePolling(load, 10000)

    const cards = [
        { label: '任务总数', value: stats?.tasks_total },
        { label: '启用中', value: stats?.tasks_enabled },
        { label: '运行中', value: stats?.runs_running },
        { label: '24h 失败/超时', value: stats ? stats.runs_24h.failed + stats.runs_24h.timeout : undefined },
    ]

    return (
        <div>
            <PageHeader title="仪表盘" description="调度概览, 每 10 秒自动刷新" />
            <ErrorBanner message={error} />
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                {cards.map((card) => (
                    <div key={card.label} className="surface p-4">
                        <p className="text-xs text-slate-500">{card.label}</p>
                        <p className="mt-1 text-2xl font-semibold text-slate-900">
                            {card.value ?? <span className="inline-block h-7 w-12 animate-pulse rounded bg-slate-200/70" />}
                        </p>
                    </div>
                ))}
            </div>

            <h2 className="mt-8 mb-3 text-sm font-medium text-slate-700">即将执行</h2>
            <TableCard>
                {stats === null ? (
                    <div className="px-4 py-6">
                        <TableSkeleton rows={3} />
                    </div>
                ) : stats.next_runs.length === 0 ? (
                    <EmptyState title="暂无计划中的任务" description="启用任务后这里会显示即将执行的计划" />
                ) : (
                    <DataTable>
                        <DataTableHeader>
                            <DataTableRow>
                                <DataTableHead>任务</DataTableHead>
                                <DataTableHead>cron</DataTableHead>
                                <DataTableHead>下次执行(UTC)</DataTableHead>
                                <DataTableHead className="text-right">操作</DataTableHead>
                            </DataTableRow>
                        </DataTableHeader>
                        <DataTableBody>
                            {stats.next_runs.map((next) => (
                                <DataTableRow key={next.task_id}>
                                    <DataTableCell className="font-medium text-slate-900">
                                        {next.task_name}
                                    </DataTableCell>
                                    <DataTableCell className="font-mono text-xs text-slate-500">
                                        {next.cron}
                                    </DataTableCell>
                                    <DataTableCell className="text-slate-500">
                                        {formatTime(next.next_run_at)}
                                    </DataTableCell>
                                    <DataTableCell>
                                        <div className="text-right">
                                            <Link
                                                to="/tasks"
                                                className="text-xs text-slate-500 hover:text-slate-900"
                                            >
                                                查看
                                            </Link>
                                        </div>
                                    </DataTableCell>
                                </DataTableRow>
                            ))}
                        </DataTableBody>
                    </DataTable>
                )}
            </TableCard>

            <h2 className="mt-8 mb-3 text-sm font-medium text-slate-700">最近失败</h2>
            <TableCard>
                {failures === null ? (
                    <div className="px-4 py-6">
                        <TableSkeleton rows={3} />
                    </div>
                ) : failures.items.length === 0 ? (
                    <EmptyState title="24 小时内暂无失败记录" />
                ) : (
                    <DataTable>
                        <DataTableHeader>
                            <DataTableRow>
                                <DataTableHead>执行</DataTableHead>
                                <DataTableHead>任务</DataTableHead>
                                <DataTableHead>状态</DataTableHead>
                                <DataTableHead>开始时间</DataTableHead>
                                <DataTableHead className="text-right">耗时</DataTableHead>
                            </DataTableRow>
                        </DataTableHeader>
                        <DataTableBody>
                            {failures.items.map((run) => (
                                <DataTableRow key={run.id}>
                                    <DataTableCell>
                                        <Link
                                            to={`/runs/${run.id}`}
                                            className="font-mono text-xs text-slate-500 hover:text-slate-900"
                                        >
                                            {shortId(run.id)}
                                        </Link>
                                    </DataTableCell>
                                    <DataTableCell className="text-slate-900">
                                        {run.task_name ?? '-'}
                                    </DataTableCell>
                                    <DataTableCell>
                                        <Badge tone={statusDisplay(run.status).tone}>
                                            {statusDisplay(run.status).label}
                                        </Badge>
                                    </DataTableCell>
                                    <DataTableCell className="text-slate-500">
                                        {formatTime(run.started_at)}
                                    </DataTableCell>
                                    <DataTableCell className="text-right text-slate-500">
                                        {formatDuration(run.duration_ms)}
                                    </DataTableCell>
                                </DataTableRow>
                            ))}
                        </DataTableBody>
                    </DataTable>
                )}
            </TableCard>
        </div>
    )
}
