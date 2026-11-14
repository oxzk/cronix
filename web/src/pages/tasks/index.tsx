import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { History, Pencil, Play, Plus, Square, Trash2 } from 'lucide-react'
import { ErrorBanner } from '@/components/ui/error-banner'
import { cancelTask, deleteTask, listTasks, runTask, updateTask } from '@/api/tasks'
import { DEFAULT_PAGE_SIZE as PAGE_SIZE } from '@/lib/constants'
import { useToastAction } from '@/hooks/use-toast-action'
import { getErrorMessage } from '@/lib/error'
import { formatTime } from '@/lib/utils'
import { statusDisplay } from '@/lib/status'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { Pagination } from '@/components/ui/pagination'
import { TableSkeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import {
    DataTable,
    DataTableBody,
    DataTableCell,
    DataTableHead,
    DataTableHeader,
    DataTableRow,
    TableCard,
} from '@/components/ui/table'
import { TooltipTip } from '@/components/ui/tooltip'
import TaskFormDialog from '@/pages/tasks/TaskFormDialog'
import type { Page, Task } from '@/api/types'

export default function TasksPage() {
    const [page, setPage] = useState(1)
    const [data, setData] = useState<Page<Task> | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [formOpen, setFormOpen] = useState(false)
    const [editing, setEditing] = useState<Task | null>(null)
    const [deleting, setDeleting] = useState<Task | null>(null)
    const { runKeyed, busy } = useToastAction()

    const load = useCallback(async () => {
        try {
            const result = await listTasks(page, PAGE_SIZE)
            setData(result)
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [page])

    useEffect(() => {
        void load()
    }, [load])

    const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

    const handleToggle = (task: Task) =>
        runKeyed(`${task.id}:toggle`, () => updateTask(task.id, { enabled: !task.enabled }), {
            success: task.enabled ? '任务已停用' : '任务已启用',
        }).then(load)

    const handleRun = (task: Task) =>
        runKeyed(`${task.id}:run`, () => runTask(task.id), { success: '已触发执行' }).then(
            (ok) => {
                if (ok) void load()
            },
        )

    const handleCancel = (task: Task) =>
        runKeyed(`${task.id}:cancel`, () => cancelTask(task.id), { success: '已请求取消' }).then(
            (ok) => {
                if (ok) void load()
            },
        )

    const handleDelete = async () => {
        if (!deleting) return
        const ok = await runKeyed(deleting.id, () => deleteTask(deleting.id), { success: '任务已删除' })
        if (ok) {
            setDeleting(null)
            void load()
        }
    }

    return (
        <div>
            <PageHeader
                title="任务"
                description="Shell 定时任务, cron 按 UTC 计算"
                actions={
                    <Button
                        onClick={() => {
                            setEditing(null)
                            setFormOpen(true)
                        }}
                    >
                        <Plus className="h-4 w-4" />
                        新建任务
                    </Button>
                }
            />
            <ErrorBanner message={error} />

            {data === null ? (
                <TableSkeleton rows={5} />
            ) : data.items.length === 0 ? (
                <TableCard>
                    <EmptyState title="还没有任务" description="创建第一个定时任务开始使用">
                        <Button
                            className="mt-2"
                            onClick={() => {
                                setEditing(null)
                                setFormOpen(true)
                            }}
                        >
                            新建任务
                        </Button>
                    </EmptyState>
                </TableCard>
            ) : (
                <>
                    <TableCard>
                        <DataTable>
                            <DataTableHeader>
                                <DataTableRow>
                                    <DataTableHead>名称</DataTableHead>
                                    <DataTableHead>cron</DataTableHead>
                                    <DataTableHead>启用</DataTableHead>
                                    <DataTableHead>上次执行</DataTableHead>
                                    <DataTableHead>下次执行</DataTableHead>
                                    <DataTableHead className="text-right">操作</DataTableHead>
                                </DataTableRow>
                            </DataTableHeader>
                            <DataTableBody>
                                {data.items.map((task) => (
                                    <DataTableRow key={task.id}>
                                        <DataTableCell className="font-medium whitespace-nowrap text-slate-900">
                                            {task.name}
                                        </DataTableCell>
                                        <DataTableCell className="font-mono text-xs whitespace-nowrap text-slate-500">
                                            {task.cron}
                                        </DataTableCell>
                                        <DataTableCell>
                                            <Switch
                                                checked={task.enabled}
                                                disabled={busy(`${task.id}:toggle`)}
                                                onCheckedChange={() => void handleToggle(task)}
                                            />
                                        </DataTableCell>
                                        <DataTableCell className="whitespace-nowrap">
                                            {task.last_status != null ? (
                                                <Badge tone={statusDisplay(task.last_status).tone}>
                                                    {statusDisplay(task.last_status).label}
                                                </Badge>
                                            ) : (
                                                <span className="text-xs text-slate-400">未执行</span>
                                            )}
                                            <span className="mt-0.5 block text-xs text-slate-400">
                                                {formatTime(task.last_run_at)}
                                            </span>
                                        </DataTableCell>
                                        <DataTableCell className="whitespace-nowrap text-slate-500">
                                            {task.enabled ? formatTime(task.next_run_at) : '-'}
                                        </DataTableCell>
                                        <DataTableCell>
                                            <div className="flex items-center justify-end gap-0.5">
                                                <TooltipTip content="执行记录">
                                                    <Link
                                                        to={`/runs?task_id=${task.id}`}
                                                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
                                                    >
                                                        <History className="h-4 w-4" />
                                                    </Link>
                                                </TooltipTip>
                                                {task.running_count > 0 ? (
                                                    <TooltipTip content="取消运行">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            loading={busy(`${task.id}:cancel`)}
                                                            onClick={() => void handleCancel(task)}
                                                        >
                                                            <Square className="h-4 w-4" />
                                                        </Button>
                                                    </TooltipTip>
                                                ) : (
                                                    <TooltipTip content="立即运行">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            loading={busy(`${task.id}:run`)}
                                                            onClick={() => void handleRun(task)}
                                                        >
                                                            <Play className="h-4 w-4" />
                                                        </Button>
                                                    </TooltipTip>
                                                )}
                                                <TooltipTip content="编辑">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => {
                                                            setEditing(task)
                                                            setFormOpen(true)
                                                        }}
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                </TooltipTip>
                                                <TooltipTip content="删除">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => setDeleting(task)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </TooltipTip>
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

            <TaskFormDialog
                open={formOpen}
                task={editing}
                onOpenChange={setFormOpen}
                onSaved={() => {
                    setFormOpen(false)
                    void load()
                }}
            />

            <ConfirmDialog
                open={deleting !== null}
                title={deleting ? `删除任务「${deleting.name}」` : '删除任务'}
                loading={deleting ? busy(deleting.id) : false}
                onConfirm={() => void handleDelete()}
                onOpenChange={(open) => {
                    if (!open) setDeleting(null)
                }}
            />
        </div>
    )
}
