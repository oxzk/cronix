import { useCallback, useEffect, useState } from 'react'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { deleteScript, listScripts } from '@/api/scripts'
import type { Page, Script } from '@/api/types'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
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
import { TooltipTip } from '@/components/ui/tooltip'
import { useToastAction } from '@/hooks/use-toast-action'
import { ErrorBanner } from '@/components/ui/error-banner'
import { DEFAULT_PAGE_SIZE as PAGE_SIZE } from '@/lib/constants'
import { getErrorMessage } from '@/lib/error'
import { formatTime } from '@/lib/utils'
import ScriptFormDialog from '@/pages/scripts/ScriptFormDialog'

export default function ScriptsPage() {
    const [page, setPage] = useState(1)
    const [data, setData] = useState<Page<Script> | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [formOpen, setFormOpen] = useState(false)
    const [editing, setEditing] = useState<Script | null>(null)
    const [deleting, setDeleting] = useState<Script | null>(null)
    const { runKeyed, busy } = useToastAction()

    const load = useCallback(async () => {
        try {
            setData(await listScripts(page, PAGE_SIZE))
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [page])

    useEffect(() => {
        void load()
    }, [load])

    const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

    const handleDelete = async () => {
        if (!deleting) return
        const ok = await runKeyed(deleting.id, () => deleteScript(deleting.id), { success: '脚本已删除' })
        if (ok) {
            setDeleting(null)
            void load()
        }
    }

    return (
        <div>
            <PageHeader
                title="脚本"
                description="可复用的 Shell 脚本; 任务可引用脚本作为命令来源"
                actions={
                    <Button
                        onClick={() => {
                            setEditing(null)
                            setFormOpen(true)
                        }}
                    >
                        <Plus className="h-4 w-4" />
                        新建脚本
                    </Button>
                }
            />
            <ErrorBanner message={error} />

            {data === null ? (
                <TableSkeleton rows={5} />
            ) : data.items.length === 0 ? (
                <TableCard>
                    <EmptyState title="还没有脚本" description="创建脚本后可被任务引用, 或直接测试运行">
                        <Button
                            className="mt-2"
                            onClick={() => {
                                setEditing(null)
                                setFormOpen(true)
                            }}
                        >
                            新建脚本
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
                                    <DataTableHead>描述</DataTableHead>
                                    <DataTableHead>代码</DataTableHead>
                                    <DataTableHead>更新时间</DataTableHead>
                                    <DataTableHead className="text-right">操作</DataTableHead>
                                </DataTableRow>
                            </DataTableHeader>
                            <DataTableBody>
                                {data.items.map((script) => (
                                    <DataTableRow key={script.id}>
                                        <DataTableCell className="font-medium whitespace-nowrap text-slate-900">
                                            {script.name}
                                        </DataTableCell>
                                        <DataTableCell className="max-w-56">
                                            <span className="block truncate text-slate-500">
                                                {script.description || '-'}
                                            </span>
                                        </DataTableCell>
                                        <DataTableCell className="max-w-64">
                                            <span className="block truncate font-mono text-xs text-slate-400">
                                                {script.content.split('\n')[0]}
                                            </span>
                                        </DataTableCell>
                                        <DataTableCell className="whitespace-nowrap text-slate-500">
                                            {formatTime(script.updated_at)}
                                        </DataTableCell>
                                        <DataTableCell>
                                            <div className="flex items-center justify-end gap-0.5">
                                                <TooltipTip content="编辑">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => {
                                                            setEditing(script)
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
                                                        onClick={() => setDeleting(script)}
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

            <ScriptFormDialog
                open={formOpen}
                script={editing}
                onOpenChange={setFormOpen}
                onSaved={() => {
                    setFormOpen(false)
                    void load()
                }}
            />

            <ConfirmDialog
                open={deleting !== null}
                title={deleting ? `删除脚本「${deleting.name}」` : '删除脚本'}
                loading={deleting ? busy(deleting.id) : false}
                onConfirm={() => void handleDelete()}
                onOpenChange={(open) => {
                    if (!open) setDeleting(null)
                }}
            />
        </div>
    )
}
