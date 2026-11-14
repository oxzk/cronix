import { useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import type { TotpSetup } from '@/api/auth'
import { disableTotp, enableTotp, getTotpStatus, setupTotp } from '@/api/auth'
import { useToastAction } from '@/hooks/use-toast-action'
import { Button } from '@/components/ui/button'
import { JsonBlock } from '@/components/ui/json-block'
import { OtpInput } from '@/components/ui/otp-input'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/components/ui/toast'

type TotpMode = 'idle' | 'setup' | 'disable'

/** 两步验证(TOTP)面板: 独立加载/配置, 不参与页面统一保存。 */
export function TotpPanel() {
    const [enabled, setEnabled] = useState(false)
    const [mode, setMode] = useState<TotpMode>('idle')
    const [setup, setSetup] = useState<TotpSetup | null>(null)
    const [code, setCode] = useState('')
    const { runKeyed, busy } = useToastAction()
    const toast = useToast()

    useEffect(() => {
        getTotpStatus()
            .then((status) => setEnabled(status.enabled))
            .catch(() => undefined)
    }, [])

    const cancel = () => {
        setMode('idle')
        setSetup(null)
        setCode('')
    }

    const startSetup = () =>
        runKeyed('totp-setup', async () => {
            const data = await setupTotp()
            setSetup(data)
            setMode('setup')
            setCode('')
        })

    // 设置流程中让开关体现"待确认"状态, 避免点击后看起来没反应
    const switchChecked = enabled ? mode !== 'disable' : mode === 'setup'

    const handleToggle = (checked: boolean) => {
        if (checked) {
            if (enabled || mode === 'setup') return
            void startSetup()
            return
        }
        if (mode === 'setup') {
            cancel()
            return
        }
        if (mode === 'disable') return
        if (enabled) {
            setMode('disable')
            setSetup(null)
            setCode('')
        }
    }

    const handleSetupCodeChange = (value: string) => {
        setCode(value)
        const trimmed = value.trim()
        if (mode === 'setup' && /^\d{6}$/.test(trimmed)) {
            void runKeyed(
                'totp-confirm',
                async () => {
                    await enableTotp(trimmed)
                    setEnabled(true)
                    cancel()
                },
                { success: '两步验证已启用' },
            ).then((ok) => {
                if (!ok) setCode('')
            })
        }
    }

    const confirmDisable = () => {
        if (!/^\d{6}$/.test(code.trim())) {
            toast.error('请输入 6 位动态验证码')
            return
        }
        void runKeyed(
            'totp-disable',
            async () => {
                await disableTotp(code.trim())
                setEnabled(false)
                cancel()
            },
            { success: '两步验证已关闭' },
        )
    }

    return (
        <div className="space-y-3 border-t border-slate-100 pt-4">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <p className="text-sm font-medium text-slate-700">两步验证(TOTP)</p>
                    <p className="text-xs text-slate-400">
                        {enabled
                            ? '已启用, 登录需输入验证器 App 中的 6 位动态码'
                            : mode === 'setup'
                              ? '待输入验证码确认, 确认后生效'
                              : '启用后登录需在密码之外输入 6 位动态码'}
                    </p>
                </div>
                <Switch checked={switchChecked} onCheckedChange={handleToggle} />
            </div>

            {mode === 'setup' && setup && (
                <div className="space-y-4 rounded-lg border border-slate-200 px-3 py-3">
                    <div>
                        <p className="text-sm font-medium text-slate-700">1. 用验证器 App 扫描二维码</p>
                        <div className="mt-3 flex flex-wrap items-start gap-4">
                            <div className="rounded-lg border border-slate-200 bg-white p-2">
                                <QRCodeSVG value={setup.uri} size={140} />
                            </div>
                            <div className="min-w-0 flex-1 space-y-2">
                                <p className="text-xs text-slate-400">无法扫码时手动输入密钥:</p>
                                <JsonBlock value={setup.secret} />
                                <p className="break-all text-[11px] text-slate-400">{setup.uri}</p>
                            </div>
                        </div>
                    </div>
                    <div>
                        <p className="text-sm font-medium text-slate-700">
                            2. 输入 App 显示的 6 位验证码确认
                        </p>
                        <div className="mt-2">
                            <OtpInput
                                value={code}
                                onValueChange={handleSetupCodeChange}
                                autoFocus
                            />
                            <p className="mt-1 text-xs text-slate-400">
                                {busy('totp-confirm')
                                    ? '正在验证...'
                                    : '输入满 6 位后自动确认; 关闭上方开关可取消'}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {mode === 'disable' && (
                <div className="space-y-3 rounded-lg border border-slate-200 px-3 py-3">
                    <p className="text-sm text-slate-700">输入当前动态验证码以关闭两步验证</p>
                    <div className="flex flex-wrap items-center gap-2">
                        <OtpInput value={code} onValueChange={setCode} />
                        <Button variant="danger" loading={busy('totp-disable')} onClick={confirmDisable}>
                            确认关闭
                        </Button>
                        <Button variant="secondary" onClick={cancel}>
                            取消
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}
