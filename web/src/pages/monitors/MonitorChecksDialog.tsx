import { useCallback, useEffect, useState } from 'react'
import { listMonitorChecks } from '@/api/monitors'
import type { Monitor, MonitorCard, MonitorCheck, Page } from '@/api/types'
import { AppDialog } from '@/components/ui/app-dialog'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/empty-state'
import { ErrorBanner } from '@/components/ui/error-banner'
import { Pagination } from '@/components/ui/pagination'
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
import { DEFAULT_PAGE_SIZE as PAGE_SIZE } from '@/lib/constants'
import { getErrorMessage } from '@/lib/error'
import { formatDuration, formatTime } from '@/lib/utils'

export function MonitorChecksDialog({
    monitor,
    open,
    onOpenChange,
}: {
    monitor: Monitor | MonitorCard | null
    open: boolean
    onOpenChange: (open: boolean) => void
}) {
    const [page, setPage] = useState(1)
    const [data, setData] = useState<Page<MonitorCheck> | null>(null)
    const [error, setError] = useState<string | null>(null)

    const load = useCallback(async () => {
        if (!monitor) return
        try {
            setData(await listMonitorChecks(monitor.id, page, PAGE_SIZE))
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [monitor, page])

    useEffect(() => {
        if (!open) {
            setPage(1)
            return
        }
        void load()
    }, [open, page, load])

    const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

    return (
        <AppDialog
            open={open}
            onOpenChange={onOpenChange}
            title={`检查历史${monitor ? ` · ${monitor.name}` : ''}`}
            wide
        >
            <ErrorBanner message={error} />
            {data === null ? (
                <TableSkeleton rows={4} />
            ) : data.items.length === 0 ? (
                <EmptyState title="暂无检查记录" description="等待首次检查或点击「立即检查」" />
            ) : (
                <TableCard>
                    <DataTable>
                        <DataTableHeader>
                            <DataTableRow>
                                <DataTableHead>状态</DataTableHead>
                                <DataTableHead>耗时</DataTableHead>
                                <DataTableHead>错误</DataTableHead>
                                <DataTableHead className="text-right">检查时间</DataTableHead>
                            </DataTableRow>
                        </DataTableHeader>
                        <DataTableBody>
                            {data.items.map((check) => (
                                <DataTableRow key={check.id}>
                                    <DataTableCell>
                                        <Badge tone={check.status === 1 ? 'success' : 'danger'}>
                                            {check.status === 1 ? '正常' : '异常'}
                                        </Badge>
                                    </DataTableCell>
                                    <DataTableCell className="text-slate-500">
                                        {formatDuration(check.latency_ms)}
                                    </DataTableCell>
                                    <DataTableCell className="max-w-72">
                                        <span className="block truncate text-xs text-slate-500" title={check.error_message ?? ''}>
                                            {check.error_message ?? '-'}
                                        </span>
                                    </DataTableCell>
                                    <DataTableCell className="text-right whitespace-nowrap text-slate-500">
                                        {formatTime(check.checked_at)}
                                    </DataTableCell>
                                </DataTableRow>
                            ))}
                        </DataTableBody>
                    </DataTable>
                </TableCard>
            )}
            {data && data.total > PAGE_SIZE && (
                <div className="mt-4">
                    <Pagination
                        page={page}
                        totalPages={totalPages}
                        pageSize={PAGE_SIZE}
                        total={data.total}
                        onChange={setPage}
                    />
                </div>
            )}
        </AppDialog>
    )
}
