import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'
import { Button } from './button'

function PaginationRoot({ className, ...props }: ComponentProps<'nav'>) {
    return (
        <nav
            role="navigation"
            aria-label="pagination"
            data-slot="pagination"
            className={cn('mx-auto flex w-full justify-center', className)}
            {...props}
        />
    )
}

function PaginationContent({ className, ...props }: ComponentProps<'ul'>) {
    return (
        <ul data-slot="pagination-content" className={cn('flex items-center gap-1.5', className)} {...props} />
    )
}

function PaginationItem(props: ComponentProps<'li'>) {
    return <li data-slot="pagination-item" {...props} />
}

type PaginationLinkProps = ComponentProps<typeof Button> & { isActive?: boolean }

function PaginationLink({ className, isActive, variant = 'secondary', ...props }: PaginationLinkProps) {
    return (
        <Button
            data-slot="pagination-link"
            data-active={isActive}
            variant={isActive ? 'default' : variant}
            size="sm"
            className={className}
            {...props}
        />
    )
}

export function Pagination({
    page,
    totalPages,
    pageSize,
    total,
    disabled,
    onChange,
}: {
    page: number
    totalPages: number
    pageSize: number
    total?: number
    disabled?: boolean
    onChange: (page: number) => void
}) {
    if (totalPages <= 1) return null

    return (
        <PaginationRoot className="flex-wrap justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
            <span className="text-slate-500">
                第 {page} / {totalPages} 页 · 每页 {pageSize} 条
                {total != null ? ` · 共 ${total} 条` : ''}
            </span>
            <PaginationContent>
                <PaginationItem>
                    <PaginationLink disabled={page <= 1 || disabled} onClick={() => onChange(1)}>
                        首页
                    </PaginationLink>
                </PaginationItem>
                <PaginationItem>
                    <PaginationLink disabled={page <= 1 || disabled} onClick={() => onChange(page - 1)}>
                        上一页
                    </PaginationLink>
                </PaginationItem>
                <PaginationItem>
                    <PaginationLink
                        disabled={page >= totalPages || disabled}
                        onClick={() => onChange(page + 1)}
                    >
                        下一页
                    </PaginationLink>
                </PaginationItem>
                <PaginationItem>
                    <PaginationLink
                        disabled={page >= totalPages || disabled}
                        onClick={() => onChange(totalPages)}
                    >
                        末页
                    </PaginationLink>
                </PaginationItem>
            </PaginationContent>
        </PaginationRoot>
    )
}
