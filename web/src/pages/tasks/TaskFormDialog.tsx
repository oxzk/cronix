import { useEffect, useMemo, useState } from 'react'
import { listScripts } from '@/api/scripts'
import { createTask, updateTask } from '@/api/tasks'
import type { Script, Task } from '@/api/types'
import { cronFieldCount, describeCron } from '@/lib/cron'
import { toNumber } from '@/lib/forms'
import { usePushoConfigured } from '@/hooks/use-pusho-configured'
import { FormField as Field, FormTextField as TextField } from '@/components/ui/form-field'
import { FormDialog } from '@/components/ui/form-dialog'
import { Input } from '@/components/ui/input'
import { JsonBlock } from '@/components/ui/json-block'
import { MultiSelect } from '@/components/ui/multi-select'
import { Select, SelectItem } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

const EVENT_OPTIONS = [
    { value: 'run.failed', label: '失败' },
    { value: 'run.timeout', label: '超时' },
    { value: 'run.completed', label: '成功' },
]

type CommandSource = 'inline' | 'script'

interface FieldErrors {
    name?: string
    cron?: string
    command?: string
    script?: string
}

export default function TaskFormDialog({
    open,
    task,
    onOpenChange,
    onSaved,
}: {
    open: boolean
    task: Task | null
    onOpenChange: (open: boolean) => void
    onSaved: () => void
}) {
    const [name, setName] = useState('')
    const [commandSource, setCommandSource] = useState<CommandSource>('inline')
    const [command, setCommand] = useState('')
    const [scriptId, setScriptId] = useState('')
    const [scripts, setScripts] = useState<Script[] | null>(null)
    const [cron, setCron] = useState('')
    const [enabled, setEnabled] = useState(true)
    const [timeout, setTimeoutValue] = useState('')
    const [maxRetries, setMaxRetries] = useState('0')
    const [retryDelay, setRetryDelay] = useState('5')
    const [notifyEvents, setNotifyEvents] = useState<string[]>([])
    const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
    const [error, setError] = useState<string | null>(null)
    const [submitting, setSubmitting] = useState(false)
    const pushoConfigured = usePushoConfigured(open)

    useEffect(() => {
        if (!open) return
        setError(null)
        setFieldErrors({})
        setName(task?.name ?? '')
        setCommandSource(task?.script_id ? 'script' : 'inline')
        setCommand(task?.command ?? '')
        setScriptId(task?.script_id ?? '')
        setCron(task?.cron ?? '')
        setEnabled(task?.enabled ?? true)
        setTimeoutValue(task?.timeout != null ? String(task.timeout) : '')
        setMaxRetries(String(task?.max_retries ?? 0))
        setRetryDelay(String(task?.retry_delay ?? 5))
        setNotifyEvents(
            task?.notification_config.enabled ? task.notification_config.events : [],
        )
    }, [open, task])

    useEffect(() => {
        if (!open) return
        let cancelled = false
        listScripts(1, 100)
            .then((page) => {
                if (!cancelled) setScripts(page.items)
            })
            .catch(() => {
                if (!cancelled) setScripts([])
            })
        return () => {
            cancelled = true
        }
    }, [open])

    const cronHint = useMemo(() => {
        const description = describeCron(cron)
        if (!description) return null
        return `${description}(按 UTC 计算)`
    }, [cron])

    const selectedScript = scripts?.find((script) => script.id === scriptId) ?? null

    const handleSubmit = async () => {
        const next: FieldErrors = {}
        if (!name.trim()) next.name = '任务名不能为空'
        if (!cron.trim()) next.cron = 'cron 表达式不能为空'
        else if (cronFieldCount(cron) !== 5) next.cron = 'cron 表达式必须为 5 段(分 时 日 月 周)'
        else if (!cronHint) next.cron = 'cron 表达式不合法'
        if (commandSource === 'inline' && !command.trim()) next.command = '命令不能为空'
        if (commandSource === 'script' && !scriptId) next.script = '请选择脚本'
        setFieldErrors(next)
        if (Object.keys(next).length > 0) return
        setError(null)
        setSubmitting(true)
        try {
            const timeoutNumber = toNumber(timeout, 0)
            const payload = {
                name: name.trim(),
                command: commandSource === 'inline' ? command.trim() : null,
                script_id: commandSource === 'script' ? scriptId : null,
                cron: cron.trim(),
                enabled,
                timeout: timeoutNumber > 0 ? timeoutNumber : null,
                max_retries: Math.max(0, toNumber(maxRetries, 0)),
                retry_delay: Math.max(1, toNumber(retryDelay, 5)),
                notification_config: {
                    enabled: notifyEvents.length > 0,
                    events: notifyEvents,
                },
            }
            if (task) {
                await updateTask(task.id, payload)
            } else {
                await createTask(payload)
            }
            onSaved()
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err))
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <FormDialog
            open={open}
            onOpenChange={onOpenChange}
            title={task ? '编辑任务' : '新建任务'}
            error={error}
            submitLabel={task ? '保存' : '创建'}
            submitting={submitting}
            onSubmit={() => void handleSubmit()}
            wide
        >
            <div className="grid grid-cols-2 gap-4">
                <Field label="任务名" required error={fieldErrors.name}>
                    <Input
                        value={name}
                        onChange={(event) => {
                            setName(event.target.value)
                            setFieldErrors((prev) => ({ ...prev, name: undefined }))
                        }}
                    />
                </Field>
                <Field
                    label="cron 表达式"
                    required
                    error={fieldErrors.cron}
                >
                    <Input
                        value={cron}
                        onChange={(event) => {
                            setCron(event.target.value)
                            setFieldErrors((prev) => ({ ...prev, cron: undefined }))
                        }}
                        className="font-mono"
                        placeholder="分 时 日 月 周, 例: */5 * * * *"
                    />
                </Field>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <Field label="命令来源">
                    <Select
                        value={commandSource}
                        onValueChange={(value) => {
                            setCommandSource(value as CommandSource)
                            setFieldErrors((prev) => ({ ...prev, command: undefined, script: undefined }))
                        }}
                    >
                        <SelectItem value="inline">内联命令</SelectItem>
                        <SelectItem value="script">脚本库</SelectItem>
                    </Select>
                </Field>
                <Field label="状态">
                    <Select
                        value={enabled ? 'enabled' : 'disabled'}
                        onValueChange={(value) => setEnabled(value === 'enabled')}
                    >
                        <SelectItem value="enabled">启用</SelectItem>
                        <SelectItem value="disabled">禁用</SelectItem>
                    </Select>
                </Field>
            </div>

            {commandSource === 'script' && (
                <Field
                    label="选择脚本"
                    required
                    error={fieldErrors.script}
                >
                    <Select
                        value={scriptId}
                        onValueChange={(value) => {
                            setScriptId(value)
                            setFieldErrors((prev) => ({ ...prev, script: undefined }))
                        }}
                        placeholder={
                            scripts === null
                                ? '加载中...'
                                : scripts.length === 0
                                  ? '脚本库为空, 请先在「脚本」页创建'
                                  : '请选择脚本(执行时实时读取最新内容)'
                        }
                        disabled={!scripts || scripts.length === 0}
                    >
                        {(scripts ?? []).map((script) => (
                            <SelectItem key={script.id} value={script.id}>
                                {script.name}
                            </SelectItem>
                        ))}
                    </Select>
                </Field>
            )}

            {commandSource === 'inline' ? (
                <TextField label="命令" required error={fieldErrors.command}>
                    <Textarea
                        value={command}
                        onChange={(event) => {
                            setCommand(event.target.value)
                            setFieldErrors((prev) => ({ ...prev, command: undefined }))
                        }}
                        rows={4}
                        placeholder="多行脚本也可, 经 sh -c 执行"
                    />
                </TextField>
            ) : (
                selectedScript && (
                    <div>
                        <p className="mb-1.5 text-sm font-medium text-slate-700">脚本预览</p>
                        <JsonBlock value={selectedScript.content} className="max-h-40" />
                    </div>
                )
            )}

            <div className="grid grid-cols-3 gap-4">
                <Field label="超时(秒)">
                    <Input
                        type="number"
                        min={1}
                        value={timeout}
                        onChange={(event) => setTimeoutValue(event.target.value)}
                        placeholder="留空用系统默认"
                    />
                </Field>
                <Field label="最大重试">
                    <Input
                        type="number"
                        min={0}
                        value={maxRetries}
                        onChange={(event) => setMaxRetries(event.target.value)}
                    />
                </Field>
                <Field label="重试间隔(秒)">
                    <Input
                        type="number"
                        min={1}
                        value={retryDelay}
                        onChange={(event) => setRetryDelay(event.target.value)}
                    />
                </Field>
            </div>

            <div className="relative rounded-lg border border-slate-200 px-3 pt-5 pb-3">
                <span className="absolute -top-2.5 left-3 bg-white px-1.5 text-sm font-medium text-slate-700">
                    执行通知
                </span>
                <MultiSelect
                    options={EVENT_OPTIONS}
                    value={notifyEvents}
                    onChange={setNotifyEvents}
                    placeholder="不通知"
                    disabled={!pushoConfigured}
                />
                {!pushoConfigured && (
                    <p className="mt-2 text-xs font-medium text-amber-600">
                        请先在设置页配置 Pusho 通知
                    </p>
                )}
            </div>
        </FormDialog>
    )
}
