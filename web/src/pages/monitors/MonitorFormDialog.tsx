import { useEffect, useState } from 'react'
import { createMonitor, updateMonitor } from '@/api/monitors'
import type { Monitor, MonitorCard, MonitorKind } from '@/api/types'
import { asBoolean, asNumber, asString } from '@/lib/forms'
import { REDACTED } from '@/lib/constants'
import { usePushoConfigured } from '@/hooks/use-pusho-configured'
import { FormField as Field, FormTextField as TextField } from '@/components/ui/form-field'
import { FormDialog } from '@/components/ui/form-dialog'
import { Input } from '@/components/ui/input'
import { MultiSelect } from '@/components/ui/multi-select'
import { SecretInput } from '@/components/ui/secret-input'
import { Select, SelectItem } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { TooltipTip } from '@/components/ui/tooltip'

const KIND_OPTIONS: { value: MonitorKind; label: string }[] = [
    { value: 'http', label: 'HTTP' },
    { value: 'redis', label: 'Redis' },
    { value: 'mysql', label: 'MySQL' },
    { value: 'postgresql', label: 'PostgreSQL' },
    { value: 'mongo', label: 'MongoDB' },
    { value: 'rabbitmq', label: 'RabbitMQ' },
]

const DEFAULT_CONFIGS: Record<MonitorKind, Record<string, unknown>> = {
    http: { method: 'GET', url: '', headers: {}, expected_status: 200, verify_tls: true },
    redis: { url: '' },
    mysql: { url: '' },
    postgresql: { url: '', ssl: false },
    mongo: { url: '' },
    rabbitmq: { url: '' },
}

const CONNECTION_URLS: Record<Exclude<MonitorKind, 'http'>, { example: string; schemes: string[] }> = {
    redis: { example: 'redis://:password@localhost:6379/0', schemes: ['redis', 'rediss'] },
    mysql: { example: 'mysql://user:password@localhost:3306/database', schemes: ['mysql'] },
    postgresql: {
        example: 'postgresql://user:password@localhost:5432/database',
        schemes: ['postgres', 'postgresql'],
    },
    mongo: {
        example: 'mongodb://user:password@localhost:27017/database?authSource=admin',
        schemes: ['mongodb', 'mongodb+srv'],
    },
    rabbitmq: { example: 'amqp://user:password@localhost:5672/%2F', schemes: ['amqp', 'amqps'] },
}

const MONITOR_EVENTS = [
    { value: 'monitor.down', label: '异常' },
    { value: 'monitor.up', label: '恢复' },
]

export default function MonitorFormDialog({
    open,
    monitor,
    onOpenChange,
    onSaved,
}: {
    open: boolean
    monitor: Monitor | MonitorCard | null
    onOpenChange: (open: boolean) => void
    onSaved: () => void
}) {
    const [name, setName] = useState('')
    const [kind, setKind] = useState<MonitorKind>('http')
    const [config, setConfig] = useState<Record<string, unknown>>({})
    const [headersText, setHeadersText] = useState('')
    const [interval, setIntervalValue] = useState('60')
    const [timeout, setTimeoutValue] = useState('10')
    const [enabled, setEnabled] = useState(true)
    const [notifyEvents, setNotifyEvents] = useState<string[]>([])
    const [fieldErrors, setFieldErrors] = useState<Record<string, string | undefined>>({})
    const [error, setError] = useState<string | null>(null)
    const [submitting, setSubmitting] = useState(false)
    const pushoConfigured = usePushoConfigured(open)

    useEffect(() => {
        if (!open) return
        setError(null)
        setFieldErrors({})
        if (monitor) {
            setName(monitor.name)
            setKind(monitor.kind)
            if (monitor.kind === 'http') {
                setConfig({ ...DEFAULT_CONFIGS.http, ...monitor.config })
            } else {
                setConfig({
                    url: asString(monitor.config.url),
                    ...(monitor.kind === 'postgresql'
                        ? { ssl: asBoolean(monitor.config.ssl) }
                        : {}),
                })
            }
            setHeadersText(
                monitor.kind === 'http'
                    ? JSON.stringify((monitor.config as Record<string, unknown>).headers ?? {}, null, 2)
                    : '',
            )
            setIntervalValue(String(monitor.interval_seconds))
            setTimeoutValue(String(monitor.timeout_seconds))
            setEnabled(monitor.enabled)
            setNotifyEvents(
                monitor.notification_config.enabled ? monitor.notification_config.events : [],
            )
        } else {
            setName('')
            setKind('http')
            setConfig({ ...DEFAULT_CONFIGS.http })
            setHeadersText('{}')
            setIntervalValue('60')
            setTimeoutValue('10')
            setEnabled(true)
            setNotifyEvents([])
        }
    }, [open, monitor])

    const update = (key: string, value: unknown) => setConfig((prev) => ({ ...prev, [key]: value }))

    const handleKindChange = (value: string) => {
        const next = value as MonitorKind
        setKind(next)
        setConfig({ ...DEFAULT_CONFIGS[next] })
        setHeadersText(next === 'http' ? '{}' : '')
        setFieldErrors({})
    }

    const urlValue = asString(config.url)
    const urlVisible = urlValue === REDACTED ? '' : urlValue
    const connectionExample = kind === 'http' ? '' : CONNECTION_URLS[kind].example

    const handleSubmit = async () => {
        const next: Record<string, string | undefined> = {}
        if (!name.trim()) next.name = '监控名称不能为空'
        const url = urlValue.trim()
        if (!url) next.url = kind === 'http' ? '地址(URL)不能为空' : '连接 URL 不能为空'
        if (kind !== 'http' && url) {
            if (url === REDACTED) {
                if (!monitor) next.url = '请输入完整连接 URL'
            } else {
                const schemes = CONNECTION_URLS[kind].schemes
                if (!schemes.some((scheme) => url.toLowerCase().startsWith(`${scheme}://`))) {
                    next.url = `URL 协议必须为 ${schemes.join(' / ')}`
                }
            }
        }
        const finalConfig: Record<string, unknown> =
            kind === 'http'
                ? { ...config }
                : kind === 'postgresql'
                  ? { url, ssl: asBoolean(config.ssl) }
                  : { url }
        if (kind === 'http') {
            try {
                finalConfig.headers = headersText.trim() ? JSON.parse(headersText) : {}
            } catch {
                next.headers = '请求头必须是合法 JSON'
            }
        }
        setFieldErrors(next)
        if (Object.keys(next).length > 0) return
        setError(null)
        setSubmitting(true)
        try {
            const payload = {
                name: name.trim(),
                kind,
                config: finalConfig,
                interval_seconds: Math.max(5, asNumber(interval, 60)),
                timeout_seconds: Math.min(60, Math.max(1, asNumber(timeout, 10))),
                enabled,
                notification_config: {
                    enabled: notifyEvents.length > 0,
                    events: notifyEvents,
                },
            }
            if (monitor) {
                await updateMonitor(monitor.id, payload)
            } else {
                await createMonitor(payload)
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
            title={monitor ? '编辑监控' : '新建监控'}
            error={error}
            submitLabel={monitor ? '保存' : '创建'}
            submitting={submitting}
            onSubmit={() => void handleSubmit()}
            wide
        >
            <div className="grid grid-cols-2 gap-4">
                <Field label="名称" required error={fieldErrors.name}>
                    <Input
                        value={name}
                        onChange={(event) => {
                            setName(event.target.value)
                            setFieldErrors((prev) => ({ ...prev, name: undefined }))
                        }}
                    />
                </Field>
                <Field label="类型" required>
                    <Select value={kind} onValueChange={handleKindChange} disabled={Boolean(monitor)}>
                        {KIND_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                                {option.label}
                            </SelectItem>
                        ))}
                    </Select>
                </Field>
            </div>

            <div className="rounded-lg border border-slate-200 p-4">
                <p className="mb-3 text-xs font-medium tracking-wide text-slate-400 uppercase">连接配置</p>
                {kind === 'http' ? (
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="方法">
                            <Select
                                value={asString(config.method, 'GET')}
                                onValueChange={(value) => update('method', value)}
                            >
                                {['GET', 'HEAD', 'POST'].map((method) => (
                                    <SelectItem key={method} value={method}>
                                        {method}
                                    </SelectItem>
                                ))}
                            </Select>
                        </Field>
                        <Field label="期望状态码">
                            <Input
                                type="number"
                                value={asString(config.expected_status, '200')}
                                onChange={(event) => update('expected_status', asNumber(event.target.value, 200))}
                            />
                        </Field>
                        <Field label="地址(URL)" required className="col-span-2" error={fieldErrors.url}>
                            <Input
                                value={asString(config.url)}
                                onChange={(event) => {
                                    update('url', event.target.value)
                                    setFieldErrors((prev) => ({ ...prev, url: undefined }))
                                }}
                                placeholder="https://example.com/health"
                                className="font-mono"
                            />
                        </Field>
                        <TextField
                            label="请求头(JSON)"
                            className="col-span-2"
                            error={fieldErrors.headers}
                        >
                            <Textarea
                                value={headersText}
                                onChange={(event) => {
                                    setHeadersText(event.target.value)
                                    setFieldErrors((prev) => ({ ...prev, headers: undefined }))
                                }}
                                rows={3}
                                placeholder="留空或 {} 表示不附加"
                            />
                        </TextField>
                        <label className="flex items-center justify-between text-sm text-slate-700">
                            校验 TLS 证书
                            <Switch
                                checked={asBoolean(config.verify_tls ?? true)}
                                onCheckedChange={(checked) => update('verify_tls', checked)}
                            />
                        </label>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <Field label="连接 URL" required error={fieldErrors.url}>
                            <SecretInput
                                value={urlVisible}
                                onChange={(event) => {
                                    update('url', event.target.value)
                                    setFieldErrors((prev) => ({ ...prev, url: undefined }))
                                }}
                                placeholder={
                                    urlValue === REDACTED
                                        ? '已保存, 输入完整 URL 覆盖'
                                        : connectionExample
                                }
                                className="font-mono"
                            />
                        </Field>
                        {kind === 'postgresql' && (
                            <Field label="使用 SSL">
                                <div className="flex h-9 items-center">
                                    <TooltipTip content="开启后使用 SSL, 不校验服务端证书">
                                        <span className="inline-flex">
                                            <Switch
                                                checked={asBoolean(config.ssl)}
                                                onCheckedChange={(checked) => update('ssl', checked)}
                                            />
                                        </span>
                                    </TooltipTip>
                                </div>
                            </Field>
                        )}
                    </div>
                )}
            </div>

            <div className="grid grid-cols-2 gap-4">
                <Field label="检查间隔(秒)">
                    <Input
                        type="number"
                        min={5}
                        value={interval}
                        onChange={(event) => setIntervalValue(event.target.value)}
                        placeholder="5-86400"
                    />
                </Field>
                <Field label="超时(秒)">
                    <Input
                        type="number"
                        min={1}
                        max={60}
                        value={timeout}
                        onChange={(event) => setTimeoutValue(event.target.value)}
                        placeholder="1-60"
                    />
                </Field>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2.5">
                <div>
                    <p className="text-sm font-medium text-slate-700">启用监控</p>
                    <p className="text-xs text-slate-400">停用后不再周期检查, 立即检查仍可用</p>
                </div>
                <Switch checked={enabled} onCheckedChange={setEnabled} />
            </div>

            <div className="relative space-y-3 rounded-lg border border-slate-200 px-3 pt-5 pb-3">
                <span className="absolute -top-2.5 left-3 bg-white px-1.5 text-sm font-medium text-slate-700">
                    状态通知
                </span>
                <MultiSelect
                    options={MONITOR_EVENTS}
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
