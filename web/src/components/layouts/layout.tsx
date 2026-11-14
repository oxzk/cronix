import type { ComponentType } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
    Activity,
    Clock,
    FileCode2,
    History,
    LayoutDashboard,
    LogOut,
    Settings,
} from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Brand } from '@/components/Brand'
import { Button } from '@/components/ui/button'
import { useSession } from '@/auth/session-provider'
import { cn } from '@/lib/utils'

interface NavItem {
    to: string
    label: string
    icon: ComponentType<{ size?: number | string; className?: string }>
    end?: boolean
}

interface NavGroup {
    label: string
    items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
    {
        label: '调度',
        items: [
            { to: '/', label: '仪表盘', icon: LayoutDashboard, end: true },
            { to: '/tasks', label: '任务', icon: Clock },
            { to: '/runs', label: '执行记录', icon: History },
        ],
    },
    {
        label: '运维',
        items: [
            { to: '/monitors', label: '监控', icon: Activity },
            { to: '/scripts', label: '脚本', icon: FileCode2 },
        ],
    },
    {
        label: '系统',
        items: [{ to: '/settings', label: '设置', icon: Settings }],
    },
]

const ALL_ITEMS = NAV_GROUPS.flatMap((group) => group.items)

function navClass(isActive: boolean): string {
    return cn(
        'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        isActive ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
    )
}

export function AdminLayout() {
    const { username, logout } = useSession()
    const navigate = useNavigate()
    const displayName = username ?? 'admin'

    const handleLogout = async () => {
        await logout()
        navigate('/login', { replace: true })
    }

    return (
        <div className="min-h-screen">
            {/* 桌面端: 左侧固定导航 */}
            <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-slate-200/80 bg-white/90 backdrop-blur lg:flex">
                <div className="px-5 py-5">
                    <Brand />
                </div>
                <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
                    {NAV_GROUPS.map((group) => (
                        <div key={group.label}>
                            <p className="px-3 pb-1 pt-4 text-[11px] font-medium tracking-wider text-slate-400 uppercase">
                                {group.label}
                            </p>
                            {group.items.map((item) => (
                                <NavLink
                                    key={item.to}
                                    to={item.to}
                                    end={item.end}
                                    className={({ isActive }) => navClass(isActive)}
                                >
                                    <item.icon size={16} />
                                    {item.label}
                                </NavLink>
                            ))}
                        </div>
                    ))}
                </nav>
                <div className="border-t border-slate-100 px-4 py-3">
                    <div className="flex items-center gap-2.5">
                        <Avatar className="bg-slate-900">
                            <AvatarFallback>
                                {displayName.charAt(0).toUpperCase() || 'A'}
                            </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-slate-800">{displayName}</p>
                            <p className="truncate text-[11px] text-slate-400">管理员</p>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            aria-label="退出登录"
                            title="退出登录"
                            onClick={() => void handleLogout()}
                        >
                            <LogOut size={15} />
                        </Button>
                    </div>
                </div>
            </aside>

            {/* 移动端: 顶部导航 */}
            <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur lg:hidden">
                <div className="flex items-center justify-between px-4 py-3">
                    <Brand />
                    <Button variant="ghost" size="icon" aria-label="退出登录" onClick={() => void handleLogout()}>
                        <LogOut size={15} />
                    </Button>
                </div>
                <div className="flex gap-1 overflow-x-auto px-3 pb-2">
                    {ALL_ITEMS.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.end}
                            className={({ isActive }) =>
                                cn(
                                    'flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium',
                                    isActive
                                        ? 'bg-slate-900 text-white'
                                        : 'text-slate-600 hover:bg-slate-100',
                                )
                            }
                        >
                            <item.icon size={14} />
                            {item.label}
                        </NavLink>
                    ))}
                </div>
            </header>

            <main className="lg:pl-60">
                <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-9">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
