import type { ComponentProps } from 'react'
import { Dialog as DialogPrimitive } from '@base-ui/react/dialog'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

function Dialog(props: ComponentProps<typeof DialogPrimitive.Root>) {
    return <DialogPrimitive.Root data-slot="dialog" {...props} />
}

function DialogClose(props: ComponentProps<typeof DialogPrimitive.Close>) {
    return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

function DialogOverlay({ className, ...props }: ComponentProps<typeof DialogPrimitive.Backdrop>) {
    return (
        <DialogPrimitive.Backdrop
            data-slot="dialog-overlay"
            className={cn('fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-sm', className)}
            {...props}
        />
    )
}

export function DialogContent({
    className,
    children,
    showCloseButton = true,
    ...props
}: ComponentProps<typeof DialogPrimitive.Popup> & { showCloseButton?: boolean }) {
    return (
        <DialogPrimitive.Portal>
            <DialogOverlay />
            <DialogPrimitive.Popup
                data-slot="dialog-content"
                className={cn(
                    'fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-full -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl outline-none',
                    className,
                )}
                {...props}
            >
                {children}
                {showCloseButton && (
                    <DialogPrimitive.Close
                        className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
                        aria-label="关闭"
                    >
                        <X className="h-4 w-4" />
                    </DialogPrimitive.Close>
                )}
            </DialogPrimitive.Popup>
        </DialogPrimitive.Portal>
    )
}

export function DialogHeader({ className, ...props }: ComponentProps<'div'>) {
    return <div data-slot="dialog-header" className={cn('flex flex-col gap-1', className)} {...props} />
}

export function DialogFooter({ className, ...props }: ComponentProps<'div'>) {
    return <div data-slot="dialog-footer" className={cn('flex items-center justify-end gap-2', className)} {...props} />
}

export function DialogTitle({ className, ...props }: ComponentProps<typeof DialogPrimitive.Title>) {
    return (
        <DialogPrimitive.Title
            data-slot="dialog-title"
            className={cn('text-base font-semibold text-slate-900', className)}
            {...props}
        />
    )
}

export { Dialog, DialogClose }
