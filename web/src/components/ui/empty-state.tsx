import type { ReactNode } from 'react'

export function EmptyState({
    title,
    description,
    children,
}: {
    title: string
    description?: string
    children?: ReactNode
}) {
    return (
        <div className="flex flex-col items-center justify-center gap-2 px-6 py-14 text-center">
            <p className="text-sm font-medium text-slate-700">{title}</p>
            {description && <p className="max-w-sm text-xs text-slate-400">{description}</p>}
            {children}
        </div>
    )
}
