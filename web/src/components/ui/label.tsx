import type { ComponentProps } from 'react'
import { Field as FieldPrimitive } from '@base-ui/react/field'
import { cn } from '@/lib/utils'

function Label({ className, ...props }: ComponentProps<typeof FieldPrimitive.Label>) {
    return (
        <FieldPrimitive.Label
            data-slot="label"
            className={cn(
                'flex items-center gap-1 text-sm leading-none font-medium text-slate-700 select-none',
                className,
            )}
            {...props}
        />
    )
}

export { Label }
