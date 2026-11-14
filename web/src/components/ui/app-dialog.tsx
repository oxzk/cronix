import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'

export function AppDialog({
    open,
    onOpenChange,
    title,
    children,
    footer,
    wide,
}: {
    open: boolean
    onOpenChange: (open: boolean) => void
    title: string
    children: ReactNode
    footer?: ReactNode
    wide?: boolean
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent
                aria-describedby={undefined}
                className={cn('gap-0 p-0', wide ? 'max-w-2xl' : 'max-w-lg')}
            >
                <DialogHeader className="border-b border-slate-200 px-6 py-4 pr-10">
                    <DialogTitle>{title}</DialogTitle>
                </DialogHeader>
                <div className="px-6 py-4">{children}</div>
                {footer && (
                    <DialogFooter className="items-center border-t border-slate-200 px-6 py-4">
                        {footer}
                    </DialogFooter>
                )}
            </DialogContent>
        </Dialog>
    )
}
