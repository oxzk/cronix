import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

function Skeleton({ className, ...props }: ComponentProps<'div'>) {
    return (
        <div
            data-slot="skeleton"
            className={cn('animate-pulse rounded-md bg-slate-200/70', className)}
            {...props}
        />
    )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-200 bg-slate-50/60 px-4 py-2.5">
                <Skeleton className="h-3 w-24" />
            </div>
            <div className="divide-y divide-slate-100">
                {Array.from({ length: rows }, (_, index) => (
                    <div key={index} className="flex items-center gap-4 px-4 py-3.5">
                        <Skeleton className="h-3 w-40" />
                        <Skeleton className="h-3 flex-1" />
                        <Skeleton className="h-3 w-16" />
                        <Skeleton className="h-3 w-24" />
                    </div>
                ))}
            </div>
        </div>
    )
}

export { Skeleton }
