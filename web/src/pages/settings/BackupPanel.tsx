import { useCallback, useEffect, useState } from 'react'
import { RotateCcw, Trash2, Upload } from 'lucide-react'
import {
    createBackup,
    deleteBackup,
    listBackups,
    listKryvaBackups,
    restoreBackup,
    restoreRemoteBackup,
    uploadBackup,
} from '@/api/backups'
import type { BackupInfo, KryvaBackupInfo, Page } from '@/api/types'
import { useToastAction } from '@/hooks/use-toast-action'
import { getErrorMessage } from '@/lib/error'
import { formatBytes, formatTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { ErrorBanner } from '@/components/ui/error-banner'
import { Field, Input } from '@/components/ui/input'
import { OtpInput } from '@/components/ui/otp-input'
import { FormDialog } from '@/components/ui/form-dialog'
import { Pagination } from '@/components/ui/pagination'
import { SecretInput } from '@/components/ui/secret-input'
import { Select, SelectItem } from '@/components/ui/select'
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
import { useToast } from '@/components/ui/toast'
import { TooltipTip } from '@/components/ui/tooltip'

const REMOTE_PAGE_SIZE = 20

function localValue(filename: string): string {
    return `local:${filename}`
}

function kryvaValue(filename: string): string {
    return `kryva:${filename}`
}

/** 数据备份面板: 本地备份/恢复 + Kryva 存储与远端备份列表。 */
export function BackupPanel({
    kryvaApiUrl,
    onKryvaApiUrlChange,
    kryvaApiKey,
    onKryvaApiKeyChange,
    kryvaConfigured,
    onRestored,
}: {
    kryvaApiUrl: string
    onKryvaApiUrlChange: (value: string) => void
    kryvaApiKey: string
    onKryvaApiKeyChange: (value: string) => void
    kryvaConfigured: boolean
    onRestored?: () => void
}) {
    const [backups, setBackups] = useState<BackupInfo[] | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
    const [restoreOpen, setRestoreOpen] = useState(false)
    const [restoreChoice, setRestoreChoice] = useState('')
    const [restorePassword, setRestorePassword] = useState('')
    const [restoreCode, setRestoreCode] = useState('')
    const [restoreError, setRestoreError] = useState<string | null>(null)
    const [restoring, setRestoring] = useState(false)
    const [remote, setRemote] = useState<Page<KryvaBackupInfo> | null>(null)
    const [remotePage, setRemotePage] = useState(1)
    const [remoteError, setRemoteError] = useState<string | null>(null)
    // 恢复下拉使用的历史备份(取前 100 条, 不受列表分页影响)
    const [restoreRemoteOptions, setRestoreRemoteOptions] = useState<KryvaBackupInfo[]>([])
    const { runKeyed, busy } = useToastAction()
    const toast = useToast()

    const reload = useCallback(async () => {
        try {
            setBackups(await listBackups())
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
            setBackups([])
        }
    }, [])

    const reloadRemote = useCallback(async () => {
        if (!kryvaConfigured) {
            setRemote(null)
            setRemoteError(null)
            return
        }
        try {
            setRemote(await listKryvaBackups(remotePage, REMOTE_PAGE_SIZE))
            setRemoteError(null)
        } catch (err) {
            setRemoteError(getErrorMessage(err))
            setRemote(null)
        }
    }, [kryvaConfigured, remotePage])

    useEffect(() => {
        void reload()
    }, [reload])

    useEffect(() => {
        void reloadRemote()
    }, [reloadRemote])

    const backupAction = () =>
        void runKeyed('backup:create-upload', () => createBackup(true), {
            success: '备份已创建并上传到 Kryva',
        }).then((ok) => {
            if (ok) {
                void reload()
                void reloadRemote()
            }
        })

    const uploadAction = (filename: string) =>
        void runKeyed(`backup:${filename}:upload`, () => uploadBackup(filename), {
            success: '已上传到 Kryva',
        }).then((ok) => {
            if (ok) void reloadRemote()
        })

    const openRestore = (choice = '') => {
        setRestoreOpen(true)
        setRestoreChoice(choice)
        setRestorePassword('')
        setRestoreCode('')
        setRestoreError(null)
        // 打开时刷新历史备份列表
        void reload()
        void reloadRemote()
        if (kryvaConfigured) {
            void listKryvaBackups(1, 100)
                .then((data) => setRestoreRemoteOptions(data.items))
                .catch(() => setRestoreRemoteOptions([]))
        } else {
            setRestoreRemoteOptions([])
        }
    }

    const closeRestore = () => {
        setRestoreOpen(false)
        setRestoreChoice('')
        setRestorePassword('')
        setRestoreCode('')
        setRestoreError(null)
    }

    const confirmRestore = async () => {
        if (!restoreChoice) {
            setRestoreError('请选择要恢复的备份')
            return
        }
        if (!restorePassword) {
            setRestoreError('请输入管理员密码')
            return
        }
        const [kind, ...rest] = restoreChoice.split(':')
        const filename = rest.join(':')
        setRestoring(true)
        setRestoreError(null)
        try {
            const auth = { password: restorePassword, code: restoreCode.trim() || undefined }
            const result =
                kind === 'kryva'
                    ? await restoreRemoteBackup(filename, auth)
                    : await restoreBackup(filename, auth)
            toast.success('数据已恢复', `已自动备份当前数据: ${result.safety_backup}`)
            closeRestore()
            await reload()
            void reloadRemote()
            onRestored?.()
        } catch (err) {
            setRestoreError(getErrorMessage(err))
        } finally {
            setRestoring(false)
        }
    }

    const confirmDelete = async () => {
        if (!deleteTarget) return
        const ok = await runKeyed(
            `backup:${deleteTarget}:delete`,
            () => deleteBackup(deleteTarget),
            { success: '备份已删除' },
        )
        if (ok) {
            setDeleteTarget(null)
            void reload()
        }
    }

    const remoteTotalPages = remote ? Math.max(1, Math.ceil(remote.total / REMOTE_PAGE_SIZE)) : 1
    const localOptions = backups ?? []
    const remoteOptions = restoreRemoteOptions

    return (
        <div className="space-y-4">
            <ErrorBanner message={error} />

            <div className="space-y-3 rounded-lg border border-slate-200 px-3 py-3">
                <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">Kryva 存储</p>
                <div className="grid grid-cols-2 gap-4">
                    <Field label="API 地址">
                        <Input
                            value={kryvaApiUrl}
                            onChange={(event) => onKryvaApiUrlChange(event.target.value)}
                            placeholder="https://kryva.example.com"
                            className="font-mono"
                        />
                    </Field>
                    <Field label="API Key">
                        <SecretInput
                            value={kryvaApiKey}
                            onChange={(event) => onKryvaApiKeyChange(event.target.value)}
                            placeholder="留空则不修改"
                        />
                    </Field>
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
                <Button
                    variant="secondary"
                    disabled={!kryvaConfigured}
                    loading={busy('backup:create-upload')}
                    onClick={backupAction}
                >
                    备份并上传
                </Button>
                <Button variant="danger" disabled={!kryvaConfigured} onClick={() => openRestore()}>
                    恢复数据
                </Button>
            </div>

            {backups === null ? (
                <TableSkeleton rows={3} />
            ) : backups.length === 0 ? null : (
                <TableCard>
                    <DataTable>
                        <DataTableHeader>
                            <DataTableRow>
                                <DataTableHead>本地备份</DataTableHead>
                                <DataTableHead>大小</DataTableHead>
                                <DataTableHead>创建时间</DataTableHead>
                                <DataTableHead className="text-right">操作</DataTableHead>
                            </DataTableRow>
                        </DataTableHeader>
                        <DataTableBody>
                            {backups.map((item) => (
                                <DataTableRow key={item.filename}>
                                    <DataTableCell className="max-w-72 truncate font-mono text-xs text-slate-500">
                                        {item.filename}
                                    </DataTableCell>
                                    <DataTableCell className="whitespace-nowrap text-slate-500">
                                        {formatBytes(item.size)}
                                    </DataTableCell>
                                    <DataTableCell className="whitespace-nowrap text-slate-500">
                                        {formatTime(item.created_at)}
                                    </DataTableCell>
                                    <DataTableCell>
                                        <div className="flex items-center justify-end gap-0.5">
                                            <TooltipTip content="上传到 Kryva">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    disabled={!kryvaConfigured}
                                                    loading={busy(`backup:${item.filename}:upload`)}
                                                    onClick={() => uploadAction(item.filename)}
                                                >
                                                    <Upload className="h-4 w-4" />
                                                </Button>
                                            </TooltipTip>
                                            <TooltipTip content="恢复此备份">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    disabled={!kryvaConfigured}
                                                    onClick={() => openRestore(localValue(item.filename))}
                                                >
                                                    <RotateCcw className="h-4 w-4" />
                                                </Button>
                                            </TooltipTip>
                                            <TooltipTip content="删除">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => setDeleteTarget(item.filename)}
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
            )}

            {kryvaConfigured && (
                <div className="space-y-3 border-t border-slate-100 pt-4">
                    <p className="text-sm font-medium text-slate-700">Kryva 备份</p>
                    <ErrorBanner message={remoteError} />
                    {remote === null ? (
                        <TableSkeleton rows={2} />
                    ) : remote.items.length === 0 ? (
                        <p className="text-xs text-slate-400">Kryva 上暂无备份</p>
                    ) : (
                        <TableCard>
                            <DataTable>
                                <DataTableHeader>
                                    <DataTableRow>
                                        <DataTableHead>备份文件</DataTableHead>
                                        <DataTableHead>大小</DataTableHead>
                                        <DataTableHead>创建时间</DataTableHead>
                                        <DataTableHead className="text-right">操作</DataTableHead>
                                    </DataTableRow>
                                </DataTableHeader>
                                <DataTableBody>
                                    {remote.items.map((item) => (
                                        <DataTableRow key={item.filename}>
                                            <DataTableCell className="max-w-72 truncate font-mono text-xs text-slate-500">
                                                {item.filename}
                                            </DataTableCell>
                                            <DataTableCell className="whitespace-nowrap text-slate-500">
                                                {formatBytes(item.size)}
                                            </DataTableCell>
                                            <DataTableCell className="whitespace-nowrap text-slate-500">
                                                {formatTime(item.created_at)}
                                            </DataTableCell>
                                            <DataTableCell>
                                                <div className="flex items-center justify-end">
                                                    <TooltipTip content="从 Kryva 恢复">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => openRestore(kryvaValue(item.filename))}
                                                        >
                                                            <RotateCcw className="h-4 w-4" />
                                                        </Button>
                                                    </TooltipTip>
                                                </div>
                                            </DataTableCell>
                                        </DataTableRow>
                                    ))}
                                </DataTableBody>
                            </DataTable>
                        </TableCard>
                    )}
                    {remote && remote.total > 0 && (
                        <Pagination
                            page={remotePage}
                            totalPages={remoteTotalPages}
                            pageSize={REMOTE_PAGE_SIZE}
                            total={remote.total}
                            onChange={setRemotePage}
                        />
                    )}
                </div>
            )}

            <FormDialog
                open={restoreOpen}
                onOpenChange={(open) => {
                    if (!open) closeRestore()
                }}
                title="恢复备份"
                error={restoreError}
                submitLabel="恢复"
                submitting={restoring}
                onSubmit={() => void confirmRestore()}
            >
                <div className="rounded-md bg-rose-50 px-3 py-2 text-xs leading-relaxed text-rose-700">
                    恢复将覆盖当前全部数据(含账号与设置), 执行前会自动备份当前数据。
                </div>
                <Field label="选择备份" required>
                    <Select
                        value={restoreChoice}
                        onValueChange={setRestoreChoice}
                        placeholder="请选择历史备份"
                    >
                        {localOptions.map((item) => (
                            <SelectItem key={localValue(item.filename)} value={localValue(item.filename)}>
                                本地 · {item.filename}
                            </SelectItem>
                        ))}
                        {remoteOptions.map((item) => (
                            <SelectItem key={kryvaValue(item.filename)} value={kryvaValue(item.filename)}>
                                Kryva · {item.filename}
                            </SelectItem>
                        ))}
                    </Select>
                </Field>
                <Field label="管理员密码" required>
                    <SecretInput
                        value={restorePassword}
                        onChange={(event) => setRestorePassword(event.target.value)}
                        autoComplete="current-password"
                    />
                </Field>
                <Field label="动态验证码">
                    <OtpInput value={restoreCode} onValueChange={setRestoreCode} />
                </Field>
            </FormDialog>

            <ConfirmDialog
                open={deleteTarget !== null}
                title={deleteTarget ? `删除备份 ${deleteTarget}` : '删除备份'}
                loading={deleteTarget ? busy(`backup:${deleteTarget}:delete`) : false}
                onConfirm={() => void confirmDelete()}
                onOpenChange={(open) => {
                    if (!open) setDeleteTarget(null)
                }}
            />
        </div>
    )
}
