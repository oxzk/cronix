import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Activity, ArrowRight, Clock, FileCode2 } from 'lucide-react'
import { login as loginApi } from '@/api/auth'
import { useSession } from '@/auth/session-provider'
import { Button } from '@/components/ui/button'
import { Field, Input } from '@/components/ui/input'
import { OtpInput } from '@/components/ui/otp-input'
import { SecretInput } from '@/components/ui/secret-input'
import { useToast } from '@/components/ui/toast'
import { ApiError, getErrorMessage } from '@/lib/error'

const FEATURES = [
    { icon: Clock, title: '定时调度', text: '标准 cron 表达式精确触发, 支持脚本复用与重试' },
    { icon: Activity, title: '服务监控', text: '多类探针覆盖常用服务, 状态变化即时通知' },
    { icon: FileCode2, title: '统一视图', text: '任务、执行记录、监控与配置集中管理' },
]

export default function LoginPage() {
    const { authenticated, login } = useSession()
    const navigate = useNavigate()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [code, setCode] = useState('')
    const [totpRequired, setTotpRequired] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const toast = useToast()

    if (authenticated) return <Navigate to="/" replace />

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault()
        setSubmitting(true)
        try {
            await loginApi(username.trim(), password, totpRequired ? code.trim() : undefined)
            login()
            navigate('/', { replace: true })
        } catch (err) {
            if (err instanceof ApiError && err.code === 'totp_required') {
                setTotpRequired(true)
            } else {
                toast.error(getErrorMessage(err))
            }
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className="min-h-screen lg:grid lg:grid-cols-[1.15fr_1fr]">
            {/* 左侧品牌区 */}
            <aside className="relative hidden flex-col justify-between overflow-hidden bg-slate-950 p-10 text-white lg:flex">
                <div
                    aria-hidden
                    className="pointer-events-none absolute inset-0 opacity-[0.06]"
                    style={{
                        backgroundImage:
                            'linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)',
                        backgroundSize: '56px 56px',
                    }}
                />
                <div
                    aria-hidden
                    className="pointer-events-none absolute -top-48 left-1/2 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-emerald-500/10 blur-3xl"
                />

                <div className="relative flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/15">
                        <Clock className="h-5 w-5" />
                    </span>
                    <span className="text-lg font-semibold tracking-tight">cronix</span>
                </div>

                <div className="relative max-w-md">
                    <h1 className="text-3xl leading-tight font-semibold tracking-tight">
                        定时任务与服务的
                        <br />
                        统一控制台
                    </h1>
                    <p className="mt-3 text-sm text-slate-400">
                        从调度到观测, 在一个界面里完成日常运维操作。
                    </p>
                    <ul className="mt-9 space-y-5">
                        {FEATURES.map((feature) => (
                            <li key={feature.title} className="flex items-start gap-3.5">
                                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                                    <feature.icon className="h-4 w-4 text-slate-200" />
                                </span>
                                <div>
                                    <p className="text-sm font-medium text-slate-100">{feature.title}</p>
                                    <p className="mt-0.5 text-xs leading-relaxed text-slate-400">
                                        {feature.text}
                                    </p>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                <p className="relative text-xs text-slate-500">cronix · 自托管运维控制台</p>
            </aside>

            {/* 右侧登录表单 */}
            <main className="flex min-h-screen flex-col justify-center px-5 py-12 sm:px-10 lg:min-h-0 lg:px-14">
                <div className="mx-auto w-full max-w-sm">
                    <div className="mb-9 flex items-center gap-2.5 lg:hidden">
                        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white">
                            <Clock className="h-5 w-5" />
                        </span>
                        <span className="text-base font-semibold tracking-tight text-slate-900">
                            cronix
                        </span>
                    </div>

                    <h2 className="text-2xl font-semibold tracking-tight text-slate-900">登录</h2>
                    <p className="mt-1.5 text-sm text-slate-500">使用管理员账号继续</p>

                    <form onSubmit={handleSubmit} className="mt-8 space-y-4">
                        <Field label="用户名" required>
                            <Input
                                value={username}
                                onChange={(event) => setUsername(event.target.value)}
                                autoComplete="username"
                                autoFocus
                            />
                        </Field>
                        <Field label="密码" required>
                            <SecretInput
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="••••••••"
                                autoComplete="current-password"
                            />
                        </Field>
                        {totpRequired && (
                            <Field label="动态验证码" required>
                                <OtpInput
                                    value={code}
                                    onValueChange={setCode}
                                    autoFocus
                                    className="w-full"
                                />
                            </Field>
                        )}
                        <Button type="submit" className="mt-2 w-full" loading={submitting}>
                            {totpRequired ? '验证并登录' : '登录'}
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </form>

                    <p className="mt-10 text-center text-xs text-slate-400 lg:hidden">
                        cronix · 自托管运维控制台
                    </p>
                </div>
            </main>
        </div>
    )
}
