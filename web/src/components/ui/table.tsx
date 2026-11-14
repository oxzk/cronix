import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function TableCard({ className, children }: { className?: string; children: ReactNode }) {
    return (
        <div className={cn('overflow-hidden rounded-xl border border-slate-200 bg-white', className)}>
            {children}
        </div>
    )
}

export function DataTable({ className, children }: { className?: string; children: ReactNode }) {
    return (
        <div data-slot="table-container" className="relative w-full overflow-x-auto">
            <table data-slot="table" className={cn('w-full text-sm', className)}>
                {children}
            </table>
        </div>
    )
}

export function DataTableHeader({ children }: { children: ReactNode }) {
    return (
        <thead data-slot="table-header" className="border-b border-slate-200 bg-slate-50/60">
            {children}
        </thead>
    )
}

export function DataTableBody({ children }: { children: ReactNode }) {
    return (
        <tbody data-slot="table-body" className="divide-y divide-slate-100">
            {children}
        </tbody>
    )
}

export function DataTableRow({ className, children }: { className?: string; children: ReactNode }) {
    return (
        <tr
            data-slot="table-row"
            className={cn('transition-colors hover:bg-slate-50/60', className)}
        >
            {children}
        </tr>
    )
}

export function DataTableHead({ className, children }: { className?: string; children: ReactNode }) {
    return (
        <th
            data-slot="table-head"
            className={cn(
                'px-4 py-2.5 text-left text-xs font-medium tracking-wide text-slate-500 whitespace-nowrap',
                className,
            )}
        >
            {children}
        </th>
    )
}

export function DataTableCell({ className, children }: { className?: string; children: ReactNode }) {
    return (
        <td data-slot="table-cell" className={cn('px-4 py-3 align-middle', className)}>
            {children}
        </td>
    )
}
