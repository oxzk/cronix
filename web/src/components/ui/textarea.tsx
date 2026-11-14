import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'
import { useFieldControlId } from './field'

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
    function Textarea({ className, ...props }, ref) {
        const id = useFieldControlId()
        return (
            <textarea
                ref={ref}
                id={id ?? undefined}
                data-slot="textarea"
                className={cn(
                    'flex min-h-[72px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 transition-colors',
                    'placeholder:text-slate-400 focus:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10',
                    'disabled:cursor-not-allowed disabled:opacity-50',
                    className,
                )}
                {...props}
            />
        )
    },
)
