import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/badge'

export function SettingCard({
    title,
    description,
    children,
    footer,
    configured,
}: {
    title: string
    description?: string
    children: ReactNode
    footer?: ReactNode
    configured?: boolean
}) {
    return (
        <div className="surface p-5">
            <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                    <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                    {description && <p className="mt-1 text-xs text-slate-400">{description}</p>}
                </div>
                {configured !== undefined && (
                    <Badge tone={configured ? 'success' : 'danger'} className="shrink-0">
                        {configured ? '已配置' : '未配置'}
                    </Badge>
                )}
            </div>
            <div className="space-y-4">{children}</div>
            {footer && <div className="mt-5 border-t border-slate-100 pt-4">{footer}</div>}
        </div>
    )
}
