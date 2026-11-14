import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Eye, Square, Trash2 } from 'lucide-react'
import { cancelRun, deleteRun, listRuns } from '@/api/runs'
import { getTask, listTasks } from '@/api/tasks'
import { useToastAction } from '@/hooks/use-toast-action'
import { usePolling } from '@/hooks/use-polling'
import { ErrorBanner } from '@/components/ui/error-banner'
import { DEFAULT_PAGE_SIZE as PAGE_SIZE } from '@/lib/constants'
import { getErrorMessage } from '@/lib/error'
import { formatDuration, formatTime, shortId } from '@/lib/utils'
import { isTerminalStatus, statusDisplay, triggerLabel } from '@/lib/status'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { Pagination } from '@/components/ui/pagination'
import { Select, SelectItem } from '@/components/ui/select'
import { TableSkeleton } from '@/components/ui/skeleton'
import { TooltipTip } from '@/components/ui/tooltip'
import {
    DataTable,
    DataTableBody,
    DataTableCell,
    DataTableHead,
    DataTableHeader,
    DataTableRow,
    TableCard,
} from '@/components/ui/table'
import type { Page, Run } from '@/api/types'

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const STATUS_OPTIONS = [
    { value: 'all', label: '全部状态' },
    { value: '0', label: '排队' },
    { value: '1', label: '运行中' },
    { value: '2', label: '成功' },
    { value: '3', label: '失败' },
    { value: '4', label: '已取消' },
    { value: '5', label: '超时' },
]

export default function RunsPage() {
    const [searchParams, setSearchParams] = useSearchParams()
    const rawTaskParam = searchParams.get('task_id')
    const taskParam = rawTaskParam && UUID_PATTERN.test(rawTaskParam) ? rawTaskParam : 'all'
    const [page, setPage] = useState(1)
    const [statusFilter, setStatusFilter] = useState('all')
    const [taskFilter, setTaskFilter] = useState(taskParam)
    const [tasks, setTasks] = useState<Array<{ id: string; name: string }>>([])
    const [data, setData] = useState<Page<Run> | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [deleting, setDeleting] = useState<Run | null>(null)
    const { runKeyed, busy } = useToastAction()

    useEffect(() => {
        let cancelled = false
        const loadOptions = async () => {
            try {
                const result = await listTasks(1, 100)
                const items = result.items.map((task) => ({ id: task.id, name: task.name }))
                if (taskParam !== 'all' && !items.some((item) => item.id === taskParam)) {
                    try {
                        const task = await getTask(taskParam)
                        items.unshift({ id: task.id, name: task.name })
                    } catch {
                        items.unshift({ id: taskParam, name: '已删除任务' })
                    }
                }
                if (!cancelled) setTasks(items)
            } catch {
                if (!cancelled) setTasks([])
            }
        }
        void loadOptions()
        return () => {
            cancelled = true
        }
    }, [taskParam])

    // 支持 /runs?task_id=xxx 深链(任务列表跳转过来)
    useEffect(() => {
        setTaskFilter(taskParam)
        setPage(1)
    }, [taskParam])

    const load = useCallback(async () => {
        try {
            const status = statusFilter === 'all' ? undefined : Number(statusFilter)
            const taskId = taskFilter === 'all' ? undefined : taskFilter
            const result = await listRuns(page, PAGE_SIZE, { status, task_id: taskId })
            setData(result)
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [page, statusFilter, taskFilter])

    useEffect(() => {
        void load()
    }, [load])

    // 存在未终态记录时轮询刷新
    const hasActive = data?.items.some((run) => !isTerminalStatus(run.status)) ?? false
    usePolling(load, 3000, hasActive)

    const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

    const handleCancel = (run: Run) =>
        runKeyed(run.id, () => cancelRun(run.id), { success: '已请求取消' }).then(load)

    const handleDelete = async () => {
        if (!deleting) return
        const ok = await runKeyed(deleting.id, () => deleteRun(deleting.id), {
            success: '执行记录已删除',
        })
        if (ok) {
            setDeleting(null)
            void load()
        }
    }

    return (
        <div>
            <PageHeader
                title="执行记录"
                description="手动与调度触发的执行历史"
                actions={
                    <div className="flex items-center gap-2">
                        <Select
                            value={taskFilter}
                            onValueChange={(value) => {
                                setPage(1)
                                setTaskFilter(value)
                                setSearchParams(value === 'all' ? {} : { task_id: value })
                            }}
                            className="w-44"
                        >
                            <SelectItem value="all">全部任务</SelectItem>
                            {tasks.map((task) => (
                                <SelectItem key={task.id} value={task.id}>
                                    {task.name}
                                </SelectItem>
                            ))}
                        </Select>
                        <Select
                            value={statusFilter}
                            onValueChange={(value) => {
                                setPage(1)
                                setStatusFilter(value)
                            }}
                            className="w-36"
                        >
                            {STATUS_OPTIONS.map((option) => (
                                <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                </SelectItem>
                            ))}
                        </Select>
                    </div>
                }
            />
            <ErrorBanner message={error} />

            {data === null ? (
                <TableSkeleton rows={6} />
            ) : data.items.length === 0 ? (
                <TableCard>
                    <EmptyState title="暂无执行记录" description="运行一次任务后会出现在这里" />
                </TableCard>
            ) : (
                <>
                    <TableCard>
                        <DataTable>
                            <DataTableHeader>
                                <DataTableRow>
                                    <DataTableHead>执行</DataTableHead>
                                    <DataTableHead>任务</DataTableHead>
                                    <DataTableHead>触发</DataTableHead>
                                    <DataTableHead>状态</DataTableHead>
                                    <DataTableHead>第几次</DataTableHead>
                                    <DataTableHead>开始时间</DataTableHead>
                                    <DataTableHead className="text-right">操作</DataTableHead>
                                </DataTableRow>
                            </DataTableHeader>
                            <DataTableBody>
                                {data.items.map((run) => (
                                    <DataTableRow key={run.id}>
                                        <DataTableCell>
                                            <Link
                                                to={`/runs/${run.id}`}
                                                className="font-mono text-xs text-slate-500 hover:text-slate-900"
                                            >
                                                {shortId(run.id)}
                                            </Link>
                                        </DataTableCell>
                                        <DataTableCell className="font-medium whitespace-nowrap text-slate-900">
                                            {run.task_name ?? '-'}
                                        </DataTableCell>
                                        <DataTableCell className="text-xs whitespace-nowrap text-slate-500">
                                            {triggerLabel(run.trigger)}
                                        </DataTableCell>
                                        <DataTableCell>
                                            <Badge tone={statusDisplay(run.status).tone}>
                                                {statusDisplay(run.status).label}
                                            </Badge>
                                        </DataTableCell>
                                        <DataTableCell className="text-xs text-slate-500">
                                            第 {run.attempt} 次
                                        </DataTableCell>
                                        <DataTableCell className="whitespace-nowrap">
                                            <span className="text-slate-500">{formatTime(run.started_at)}</span>
                                            <span className="mt-0.5 block text-xs text-slate-400">
                                                {formatDuration(run.duration_ms)}
                                            </span>
                                        </DataTableCell>
                                        <DataTableCell>
                                            <div className="flex items-center justify-end gap-0.5">
                                                <TooltipTip content="详情">
                                                    <Link
                                                        to={`/runs/${run.id}`}
                                                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
                                                    >
                                                        <Eye className="h-4 w-4" />
                                                    </Link>
                                                </TooltipTip>
                                                {!isTerminalStatus(run.status) ? (
                                                    <TooltipTip content="取消">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            loading={busy(run.id)}
                                                            onClick={() => void handleCancel(run)}
                                                        >
                                                            <Square className="h-4 w-4" />
                                                        </Button>
                                                    </TooltipTip>
                                                ) : (
                                                    <TooltipTip content="删除">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => setDeleting(run)}
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                    </TooltipTip>
                                                )}
                                            </div>
                                        </DataTableCell>
                                    </DataTableRow>
                                ))}
                            </DataTableBody>
                        </DataTable>
                    </TableCard>
                    <div className="mt-1">
                        <Pagination
                            page={page}
                            totalPages={totalPages}
                            pageSize={PAGE_SIZE}
                            total={data.total}
                            onChange={setPage}
                        />
                    </div>
                </>
            )}

            <ConfirmDialog
                open={deleting !== null}
                title={deleting ? `删除执行记录 ${shortId(deleting.id)}` : '删除执行记录'}
                loading={deleting ? busy(deleting.id) : false}
                onConfirm={() => void handleDelete()}
                onOpenChange={(open) => {
                    if (!open) setDeleting(null)
                }}
            />
        </div>
    )
}
