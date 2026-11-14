import { forwardRef, type ComponentProps } from 'react'
import { Input as InputPrimitive } from '@base-ui/react/input'
import { cn } from '@/lib/utils'
import { FieldFrame, useFieldControlId, type FieldFrameProps } from './field'

export function Field(props: FieldFrameProps) {
    return <FieldFrame {...props} />
}

export const Input = forwardRef<HTMLInputElement, ComponentProps<typeof InputPrimitive>>(
    function Input({ className, ...props }, ref) {
        const id = useFieldControlId()
        return (
            <InputPrimitive
                ref={ref}
                id={id ?? undefined}
                data-slot="input"
                className={cn(
                    'h-9 w-full min-w-0 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 transition-colors',
                    'placeholder:text-slate-400 focus:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10',
                    'disabled:cursor-not-allowed disabled:opacity-50',
                    className,
                )}
                {...props}
            />
        )
    },
)
