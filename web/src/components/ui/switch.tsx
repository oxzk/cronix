import type { ComponentProps } from 'react'
import { Switch as SwitchPrimitive } from '@base-ui/react/switch'
import { cn } from '@/lib/utils'

function Switch({ className, ...props }: ComponentProps<typeof SwitchPrimitive.Root>) {
    return (
        <SwitchPrimitive.Root
            data-slot="switch"
            className={cn(
                'inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border border-transparent transition-colors',
                'data-checked:bg-slate-900 data-unchecked:bg-slate-200',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/20 disabled:pointer-events-none disabled:opacity-50',
                className,
            )}
            {...props}
        >
            <SwitchPrimitive.Thumb
                data-slot="switch-thumb"
                className="pointer-events-none block h-4 w-4 translate-x-0.5 rounded-full bg-white shadow transition-transform data-checked:translate-x-[18px]"
            />
        </SwitchPrimitive.Root>
    )
}

export { Switch }
