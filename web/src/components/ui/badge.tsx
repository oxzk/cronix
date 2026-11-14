import type { ReactNode } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
    'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium leading-5',
    {
        variants: {
            tone: {
                default: 'bg-slate-100 text-slate-600',
                success: 'bg-slate-900 text-white',
                warning: 'bg-orange-400 text-white',
                danger: 'bg-rose-600 text-white',
            },
        },
        defaultVariants: { tone: 'default' },
    },
)

export function Badge({
    tone,
    className,
    children,
}: VariantProps<typeof badgeVariants> & { className?: string; children: ReactNode }) {
    return (
        <span data-slot="badge" className={cn(badgeVariants({ tone }), className)}>
            {children}
        </span>
    )
}
