import { useCallback, useEffect, useState } from 'react'
import { History, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { checkMonitor, deleteMonitor, listMonitors } from '@/api/monitors'
import type { MonitorCard, MonitorRecentCheck } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { Skeleton } from '@/components/ui/skeleton'
import { TooltipTip } from '@/components/ui/tooltip'
import { useToastAction } from '@/hooks/use-toast-action'
import { usePolling } from '@/hooks/use-polling'
import { ErrorBanner } from '@/components/ui/error-banner'
import { useToast } from '@/components/ui/toast'
import { getErrorMessage } from '@/lib/error'
import { cn, formatRelativeTime, formatTime } from '@/lib/utils'
import MonitorFormDialog from '@/pages/monitors/MonitorFormDialog'
import { MonitorChecksDialog } from '@/pages/monitors/MonitorChecksDialog'

const STRIPE_BLOCKS = 20

function StatusChip({ status }: { status: number | null }) {
    const label = status === 1 ? '正常' : status === 2 ? '异常' : '未知'
    const tone = status === 1 ? 'success' : status === 2 ? 'danger' : 'default'
    return <Badge tone={tone}>{label}</Badge>
}

function Metric({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs text-slate-400">{label}</p>
            <p className="mt-0.5 text-sm font-medium text-slate-900">{value}</p>
        </div>
    )
}

function HealthStripe({ checks }: { checks: MonitorRecentCheck[] }) {
    const blocks: (MonitorRecentCheck | null)[] = [
        ...Array.from({ length: Math.max(0, STRIPE_BLOCKS - checks.length) }, () => null),
        ...checks,
    ].slice(-STRIPE_BLOCKS)
    return (
        <div className="flex w-full items-center justify-between gap-1">
            {blocks.map((check, index) => {
                if (!check) {
                    return (
                        <span
                            key={index}
                            className="h-2.5 w-2.5 shrink-0 rounded-full bg-slate-300/70 transition-transform duration-150 hover:scale-125"
                        />
                    )
                }
                const tooltip = `${formatTime(check.checked_at)} · ${check.status === 1 ? '正常' : '异常'}${
                    check.latency_ms != null ? ` · ${check.latency_ms}ms` : ''
                }${check.error_message ? ` · ${check.error_message}` : ''}`
                return (
                    <TooltipTip key={index} content={tooltip}>
                        <span
                            className={cn(
                                'h-2.5 w-2.5 shrink-0 rounded-full transition-transform duration-150 hover:z-10 hover:scale-125',
                                check.status === 1
                                    ? 'bg-gradient-to-b from-emerald-400 to-emerald-500'
                                    : 'bg-gradient-to-b from-rose-400 to-rose-500',
                            )}
                        />
                    </TooltipTip>
                )
            })}
        </div>
    )
}

function MonitorCardView({
    monitor,
    busy,
    onCheck,
    onHistory,
    onEdit,
    onDelete,
}: {
    monitor: MonitorCard
    busy: (key: string) => boolean
    onCheck: (monitor: MonitorCard) => void
    onHistory: (monitor: MonitorCard) => void
    onEdit: (monitor: MonitorCard) => void
    onDelete: (monitor: MonitorCard) => void
}) {
    return (
        <div className="surface flex flex-col p-4">
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900" title={monitor.name}>
                        {monitor.name}
                    </p>
                    <div className="mt-1 flex items-center gap-1.5">
                        <Badge>{monitor.kind.toUpperCase()}</Badge>
                        <span className="text-xs text-slate-400">每 {monitor.interval_seconds}s</span>
                    </div>
                </div>
                <StatusChip status={monitor.last_status} />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
                <Metric
                    label="响应耗时"
                    value={monitor.last_latency_ms != null ? `${monitor.last_latency_ms} ms` : '-'}
                />
                <Metric
                    label="可用率(24h)"
                    value={monitor.uptime_24h != null ? `${monitor.uptime_24h} %` : '-'}
                />
                <Metric
                    label="最近检查"
                    value={monitor.last_checked_at ? formatRelativeTime(monitor.last_checked_at) : '-'}
                />
                <Metric
                    label="最近异常"
                    value={monitor.last_issue_at ? formatRelativeTime(monitor.last_issue_at) : '从未'}
                />
            </div>

            <div className="mt-4">
                <HealthStripe checks={monitor.recent_checks} />
            </div>

            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2.5">
                <span className="text-xs text-slate-400">
                    {monitor.enabled
                        ? `下次检查 ${formatTime(monitor.next_check_at)}`
                        : '已停用'}
                </span>
                <div className="flex items-center gap-0.5">
                    <TooltipTip content="立即检查">
                        <Button
                            variant="ghost"
                            size="icon"
                            loading={busy(`${monitor.id}:check`)}
                            onClick={() => onCheck(monitor)}
                        >
                            <RefreshCw className="h-4 w-4" />
                        </Button>
                    </TooltipTip>
                    <TooltipTip content="检查历史">
                        <Button variant="ghost" size="icon" onClick={() => onHistory(monitor)}>
                            <History className="h-4 w-4" />
                        </Button>
                    </TooltipTip>
                    <TooltipTip content="编辑">
                        <Button variant="ghost" size="icon" onClick={() => onEdit(monitor)}>
                            <Pencil className="h-4 w-4" />
                        </Button>
                    </TooltipTip>
                    <TooltipTip content="删除">
                        <Button variant="ghost" size="icon" onClick={() => onDelete(monitor)}>
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </TooltipTip>
                </div>
            </div>
        </div>
    )
}

export default function MonitorsPage() {
    const [cards, setCards] = useState<MonitorCard[] | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [formOpen, setFormOpen] = useState(false)
    const [editing, setEditing] = useState<MonitorCard | null>(null)
    const [deleting, setDeleting] = useState<MonitorCard | null>(null)
    const [historyMonitor, setHistoryMonitor] = useState<MonitorCard | null>(null)
    const { runKeyed, busy } = useToastAction()
    const toast = useToast()

    const load = useCallback(async () => {
        try {
            setCards(await listMonitors())
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        }
    }, [])

    useEffect(() => {
        void load()
    }, [load])

    usePolling(load, 10000)

    const handleCheck = (monitor: MonitorCard) =>
        runKeyed(`${monitor.id}:check`, async () => {
            const result = await checkMonitor(monitor.id)
            if (result.status === 1) {
                toast.success('检查通过', `耗时 ${result.latency_ms ?? '-'}ms`)
            } else {
                toast.error(
                    '检查异常',
                    result.error_message ?? `耗时 ${result.latency_ms ?? '-'}ms`,
                )
            }
        }).then((ok) => {
            if (ok) void load()
        })

    const handleDelete = async () => {
        if (!deleting) return
        const ok = await runKeyed(deleting.id, () => deleteMonitor(deleting.id), { success: '监控已删除' })
        if (ok) {
            setDeleting(null)
            void load()
        }
    }

    return (
        <div>
            <PageHeader
                title="监控"
                description="服务可用性与响应耗时监控, 每 10 秒自动刷新"
                actions={
                    <Button
                        onClick={() => {
                            setEditing(null)
                            setFormOpen(true)
                        }}
                    >
                        <Plus className="h-4 w-4" />
                        新建监控
                    </Button>
                }
            />
            <ErrorBanner message={error} />

            {cards === null ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {Array.from({ length: 3 }, (_, index) => (
                        <div key={index} className="surface space-y-4 p-4">
                            <Skeleton className="h-4 w-32" />
                            <div className="grid grid-cols-2 gap-3">
                                <Skeleton className="h-8" />
                                <Skeleton className="h-8" />
                                <Skeleton className="h-8" />
                                <Skeleton className="h-8" />
                            </div>
                            <Skeleton className="h-6" />
                        </div>
                    ))}
                </div>
            ) : cards.length === 0 ? (
                <div className="surface">
                    <EmptyState title="还没有监控项" description="创建第一个监控开始探测服务状态">
                        <Button
                            className="mt-2"
                            onClick={() => {
                                setEditing(null)
                                setFormOpen(true)
                            }}
                        >
                            新建监控
                        </Button>
                    </EmptyState>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {cards.map((monitor) => (
                        <MonitorCardView
                            key={monitor.id}
                            monitor={monitor}
                            busy={busy}
                            onCheck={(item) => void handleCheck(item)}
                            onHistory={setHistoryMonitor}
                            onEdit={(item) => {
                                setEditing(item)
                                setFormOpen(true)
                            }}
                            onDelete={setDeleting}
                        />
                    ))}
                </div>
            )}

            <MonitorFormDialog
                open={formOpen}
                monitor={editing}
                onOpenChange={setFormOpen}
                onSaved={() => {
                    setFormOpen(false)
                    void load()
                }}
            />

            <MonitorChecksDialog
                monitor={historyMonitor}
                open={historyMonitor !== null}
                onOpenChange={(open) => {
                    if (!open) setHistoryMonitor(null)
                }}
            />

            <ConfirmDialog
                open={deleting !== null}
                title={deleting ? `删除监控「${deleting.name}」` : '删除监控'}
                loading={deleting ? busy(deleting.id) : false}
                onConfirm={() => void handleDelete()}
                onOpenChange={(open) => {
                    if (!open) setDeleting(null)
                }}
            />
        </div>
    )
}
