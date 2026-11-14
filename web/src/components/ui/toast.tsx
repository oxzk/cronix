import { useMemo, type ReactNode } from 'react'
import { Toast as ToastPrimitive } from '@base-ui/react/toast'
import { CheckCircle2, Info, Loader2, X, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

const toast = ToastPrimitive.createToastManager()
const TOAST_TIMEOUT = 5000
const TOAST_LIMIT = 3

interface ToastApi {
    success: (title: string, description?: string) => void
    error: (title: string, description?: string) => void
    info: (title: string, description?: string) => void
}

function ToastIcon({ type }: { type: string | undefined }) {
    if (type === 'success') {
        return <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden />
    }
    if (type === 'error') {
        return <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" aria-hidden />
    }
    if (type === 'loading') {
        return <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-slate-500" aria-hidden />
    }
    return <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" aria-hidden />
}

function ToastList() {
    const { toasts } = ToastPrimitive.useToastManager()

    return toasts.map((item) => (
        <ToastPrimitive.Root
            key={item.id}
            toast={item}
            data-slot="toast"
            className="group pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-lg border border-slate-200 bg-white p-4 text-slate-950 shadow-lg outline-none"
        >
            <div className="absolute inset-x-0 bottom-0 h-0.5 bg-slate-100" aria-hidden>
                <div
                    className={cn(
                        'h-full origin-left animate-[toast-progress_linear_forwards]',
                        item.type === 'success'
                            ? 'bg-slate-900'
                            : item.type === 'error'
                              ? 'bg-rose-600'
                              : 'bg-slate-400',
                    )}
                    style={{ animationDuration: `${item.timeout ?? TOAST_TIMEOUT}ms` }}
                />
            </div>
            <ToastPrimitive.Content className="flex w-full items-start gap-3">
                <ToastIcon type={item.type} />
                <div className="min-w-0 flex-1">
                    <ToastPrimitive.Title className="text-sm font-semibold leading-snug tracking-tight" />
                    <ToastPrimitive.Description className="mt-1 break-words text-[13px] leading-relaxed text-slate-500" />
                </div>
                <ToastPrimitive.Close
                    aria-label="关闭"
                    className={cn(
                        'absolute right-2 top-2 rounded-md p-1 text-slate-400 opacity-0 transition',
                        'hover:bg-slate-100 hover:text-slate-700 focus:opacity-100 group-hover:opacity-100',
                    )}
                >
                    <X className="h-3.5 w-3.5" />
                </ToastPrimitive.Close>
            </ToastPrimitive.Content>
        </ToastPrimitive.Root>
    ))
}

export function ToastProvider({ children }: { children: ReactNode }) {
    return (
        <ToastPrimitive.Provider toastManager={toast} timeout={TOAST_TIMEOUT} limit={TOAST_LIMIT}>
            {children}
            <ToastPrimitive.Portal>
                <ToastPrimitive.Viewport
                    data-slot="toast-viewport"
                    className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[min(100vw-2rem,356px)] flex-col gap-2 outline-none"
                >
                    <ToastList />
                </ToastPrimitive.Viewport>
            </ToastPrimitive.Portal>
        </ToastPrimitive.Provider>
    )
}

export function useToast(): ToastApi {
    return useMemo<ToastApi>(
        () => ({
            success: (title, description) =>
                toast.add({ title, description, type: 'success' }),
            error: (title, description) => toast.add({ title, description, type: 'error' }),
            info: (title, description) => toast.add({ title, description, type: 'info' }),
        }),
        [],
    )
}
