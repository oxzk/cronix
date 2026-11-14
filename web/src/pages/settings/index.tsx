import { useCallback, useEffect, useState } from 'react'
import { CircleHelp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '@/auth/session-provider'
import { listSettings, putSetting } from '@/api/system-settings'
import { useToastAction } from '@/hooks/use-toast-action'
import { REDACTED } from '@/lib/constants'
import { getErrorMessage } from '@/lib/error'
import { toInt } from '@/lib/forms'
import { Button } from '@/components/ui/button'
import { ErrorBanner } from '@/components/ui/error-banner'
import { Field, Input } from '@/components/ui/input'
import { SecretInput } from '@/components/ui/secret-input'
import { Select, SelectItem } from '@/components/ui/select'
import { TableSkeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { TooltipTip } from '@/components/ui/tooltip'
import { BackupPanel } from '@/pages/settings/BackupPanel'
import { SettingCard } from '@/pages/settings/SettingCard'
import { TotpPanel } from '@/pages/settings/TotpPanel'

const LOG_LEVELS = ['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']

interface BaseForm {
    default_timeout: string
    max_concurrent_runs: string
    misfire_grace_seconds: string
    notify_timeout: string
}

export default function SettingsPage() {
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [base, setBase] = useState<BaseForm>({
        default_timeout: '120',
        max_concurrent_runs: '4',
        misfire_grace_seconds: '60',
        notify_timeout: '30',
    })
    const [pushoApiUrl, setPushoApiUrl] = useState('')
    const [pushoApiKey, setPushoApiKey] = useState('')
    const [pushoProject, setPushoProject] = useState('')
    const [logging, setLogging] = useState({
        level: 'INFO',
        retention: '7 days',
    })
    const [adminPassword, setAdminPassword] = useState('')
    const [adminPasswordConfirm, setAdminPasswordConfirm] = useState('')
    const [kryvaApiUrl, setKryvaApiUrl] = useState('https://kryva.oozuo.com')
    const [kryvaApiKey, setKryvaApiKey] = useState('')
    const [savedComplete, setSavedComplete] = useState<Record<string, boolean>>({})
    const [totpKey, setTotpKey] = useState(0)
    const { runKeyed, busy } = useToastAction()
    const toast = useToast()
    const { logout } = useSession()
    const navigate = useNavigate()

    const load = useCallback(async () => {
        try {
            const rows = await listSettings()
            const map = new Map(rows.map((row) => [`${row.scope}/${row.key}`, row.value]))
            setSavedComplete(
                Object.fromEntries(
                    rows.map((row) => [`${row.scope}/${row.key}`, row.is_complete]),
                ),
            )
            const baseValue = (map.get('system/base') ?? {}) as Record<string, unknown>
            setBase({
                default_timeout: String(baseValue.default_timeout ?? 120),
                max_concurrent_runs: String(baseValue.max_concurrent_runs ?? 4),
                misfire_grace_seconds: String(baseValue.misfire_grace_seconds ?? 60),
                notify_timeout: String(baseValue.notify_timeout ?? 30),
            })
            const pusho = (map.get('notification/pusho') ?? {}) as Record<string, unknown>
            setPushoApiUrl(String(pusho.api_url ?? ''))
            setPushoApiKey('')
            setPushoProject(String(pusho.project ?? ''))
            const loguru = (map.get('logging/loguru') ?? {}) as Record<string, unknown>
            setLogging({
                level: String(loguru.level ?? 'INFO'),
                retention: String(loguru.retention ?? '7 days'),
            })
            const kryva = (map.get('backup/kryva') ?? {}) as Record<string, unknown>
            setKryvaApiUrl(String(kryva.api_url ?? 'https://kryva.oozuo.com'))
            setKryvaApiKey('')
            setError(null)
        } catch (err) {
            setError(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        void load()
    }, [load])

    const kryvaComplete =
        Boolean(kryvaApiUrl.trim()) &&
        Boolean(kryvaApiKey.trim() || savedComplete['backup/kryva'])
    const pushoComplete =
        Boolean(pushoApiUrl.trim()) &&
        Boolean(pushoApiKey.trim() || savedComplete['notification/pusho']) &&
        Boolean(pushoProject.trim())

    const saveAll = () => {
        const passwordTouched = adminPassword.length > 0 || adminPasswordConfirm.length > 0
        if (passwordTouched) {
            if (adminPassword.length < 8) {
                toast.error('密码长度至少 8 位')
                return
            }
            if (adminPassword !== adminPasswordConfirm) {
                toast.error('两次输入的密码不一致')
                return
            }
        }
        void runKeyed(
            'all',
            async () => {
                const steps: Array<[string, () => Promise<unknown>]> = [
                    [
                        '基础配置',
                        () =>
                            putSetting('system', 'base', {
                                default_timeout: toInt(base.default_timeout, 120),
                                max_concurrent_runs: toInt(base.max_concurrent_runs, 4),
                                misfire_grace_seconds: toInt(base.misfire_grace_seconds, 60),
                                notify_timeout: toInt(base.notify_timeout, 30),
                            }),
                    ],
                ]
                steps.push(
                    [
                        'Pusho',
                        () =>
                            putSetting('notification', 'pusho', {
                                api_url: pushoApiUrl.trim(),
                                // 留空则不修改已保存的 Key
                                api_key: pushoApiKey.trim() || REDACTED,
                                project: pushoProject.trim(),
                            }),
                    ],
                    [
                        'Kryva',
                        () =>
                            putSetting('backup', 'kryva', {
                                api_url: kryvaApiUrl.trim(),
                                api_key: kryvaApiKey.trim() || REDACTED,
                                platform: 'cronix',
                            }),
                    ],
                    ['日志', () => putSetting('logging', 'loguru', { ...logging })],
                )

                const failures: string[] = []
                for (const [name, run] of steps) {
                    try {
                        await run()
                    } catch (err) {
                        failures.push(`${name}: ${getErrorMessage(err)}`)
                    }
                }
                if (failures.length > 0) {
                    throw new Error(failures.join('；'))
                }
                // 密码放最后: 改密会提升令牌版本, 其余配置需先保存完成
                if (passwordTouched) {
                    await putSetting('auth', 'admin', { password: adminPassword })
                }
            },
            { success: '设置已保存' },
        ).then((ok) => {
            if (!ok) return
            setSavedComplete((prev) => ({
                ...prev,
                'notification/pusho': pushoComplete,
                'backup/kryva': kryvaComplete,
            }))
            if (passwordTouched) {
                setAdminPassword('')
                setAdminPasswordConfirm('')
                // 改密会提升令牌版本, 旧会话已失效, 主动回登录页
                void logout().then(() => navigate('/login', { replace: true }))
            }
        })
    }

    if (loading) {
        return (
            <div>
                <h1 className="mb-5 text-xl font-semibold text-slate-900">设置</h1>
                <TableSkeleton rows={4} />
            </div>
        )
    }

    return (
        <div>
            <h1 className="mb-5 text-xl font-semibold text-slate-900">设置</h1>
            <ErrorBanner message={error} />

            <div className="space-y-6">
                <SettingCard
                    title="系统基础配置"
                    description="统一管理调度与超时参数, 保存后立即生效"
                    configured={savedComplete['system/base'] ?? true}
                >
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="默认超时(秒)">
                            <Input
                                type="number"
                                min={1}
                                value={base.default_timeout}
                                onChange={(event) =>
                                    setBase((prev) => ({ ...prev, default_timeout: event.target.value }))
                                }
                                placeholder="任务未单独设置超时时使用"
                            />
                        </Field>
                        <Field label="最大并发执行数">
                            <Input
                                type="number"
                                min={1}
                                value={base.max_concurrent_runs}
                                onChange={(event) =>
                                    setBase((prev) => ({ ...prev, max_concurrent_runs: event.target.value }))
                                }
                            />
                        </Field>
                        <Field label="错过宽限(秒)">
                            <Input
                                type="number"
                                min={0}
                                value={base.misfire_grace_seconds}
                                onChange={(event) =>
                                    setBase((prev) => ({ ...prev, misfire_grace_seconds: event.target.value }))
                                }
                                placeholder="超过计划时间这么久仍未触发则跳过该轮"
                            />
                        </Field>
                        <Field label="通知超时(秒)">
                            <Input
                                type="number"
                                min={1}
                                value={base.notify_timeout}
                                onChange={(event) =>
                                    setBase((prev) => ({ ...prev, notify_timeout: event.target.value }))
                                }
                                placeholder="Pusho 推送超时, 默认 30"
                            />
                        </Field>
                    </div>
                </SettingCard>

                <SettingCard
                    title="管理员密码与两步验证"
                    description="修改登录密码, 或开启动态验证码二次确认"
                    configured
                >
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="新密码">
                            <SecretInput
                                value={adminPassword}
                                onChange={(event) => setAdminPassword(event.target.value)}
                                autoComplete="new-password"
                                placeholder="至少 8 位, 留空表示不修改"
                            />
                        </Field>
                        <Field label="确认新密码">
                            <SecretInput
                                value={adminPasswordConfirm}
                                onChange={(event) => setAdminPasswordConfirm(event.target.value)}
                                autoComplete="new-password"
                            />
                        </Field>
                    </div>

                    <TotpPanel key={totpKey} />
                </SettingCard>

                <SettingCard
                    title="数据备份"
                    description="备份包含任务、执行记录、监控、脚本与系统设置"
                    configured={kryvaComplete}
                >
                    <BackupPanel
                        kryvaApiUrl={kryvaApiUrl}
                        onKryvaApiUrlChange={setKryvaApiUrl}
                        kryvaApiKey={kryvaApiKey}
                        onKryvaApiKeyChange={setKryvaApiKey}
                        kryvaConfigured={kryvaComplete}
                        onRestored={() => {
                            setTotpKey((key) => key + 1)
                            void load()
                        }}
                    />
                </SettingCard>

                <SettingCard
                    title="Pusho 通知"
                    description="任务与监控通知通过 Pusho 推送; 在 Pusho 控制台创建 API Key 与项目"
                    configured={pushoComplete}
                >
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="API 地址">
                            <Input
                                value={pushoApiUrl}
                                onChange={(event) => setPushoApiUrl(event.target.value)}
                                placeholder="https://pusho.example.com"
                                className="font-mono"
                            />
                        </Field>
                        <Field label="API Key">
                            <SecretInput
                                value={pushoApiKey}
                                onChange={(event) => setPushoApiKey(event.target.value)}
                                placeholder="留空则不修改"
                            />
                        </Field>
                        <Field label="项目名">
                            <Input
                                value={pushoProject}
                                onChange={(event) => setPushoProject(event.target.value)}
                                className="font-mono"
                                placeholder="Pusho 控制台中的项目(渠道预设)名称"
                            />
                        </Field>
                    </div>
                </SettingCard>

                <SettingCard
                    title="日志配置"
                    description="调整日志级别与保留时长, 保存后立即生效"
                    configured={savedComplete['logging/loguru'] ?? true}
                >
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="级别">
                            <Select
                                value={logging.level}
                                onValueChange={(value) => setLogging((prev) => ({ ...prev, level: value }))}
                            >
                                {LOG_LEVELS.map((level) => (
                                    <SelectItem key={level} value={level}>
                                        {level}
                                    </SelectItem>
                                ))}
                            </Select>
                        </Field>
                        <Field
                            label="保留"
                            labelSuffix={
                                <TooltipTip content="示例: 7 days / 30 days / 1 month">
                                    <button
                                        type="button"
                                        aria-label="保留时长示例"
                                        className="cursor-help text-slate-400 transition hover:text-slate-600"
                                    >
                                        <CircleHelp className="h-3.5 w-3.5" />
                                    </button>
                                </TooltipTip>
                            }
                        >
                            <Input
                                value={logging.retention}
                                onChange={(event) =>
                                    setLogging((prev) => ({ ...prev, retention: event.target.value }))
                                }
                            />
                        </Field>
                    </div>
                </SettingCard>
            </div>

            <div className="sticky bottom-4 mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <p className="text-xs text-slate-400">
                    全部配置保存后立即生效; 两步验证请在其区块内操作
                </p>
                <Button loading={busy('all')} onClick={saveAll}>
                    保存设置
                </Button>
            </div>
        </div>
    )
}
