import type { ComponentProps } from 'react'
import { Avatar as AvatarPrimitive } from '@base-ui/react/avatar'
import { cn } from '@/lib/utils'

function Avatar({ className, ...props }: ComponentProps<typeof AvatarPrimitive.Root>) {
    return (
        <AvatarPrimitive.Root
            data-slot="avatar"
            className={cn(
                'relative flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-full select-none',
                className,
            )}
            {...props}
        />
    )
}

function AvatarFallback({
    className,
    ...props
}: ComponentProps<typeof AvatarPrimitive.Fallback>) {
    return (
        <AvatarPrimitive.Fallback
            data-slot="avatar-fallback"
            className={cn(
                'flex size-full items-center justify-center rounded-full bg-slate-900 text-xs font-medium text-white',
                className,
            )}
            {...props}
        />
    )
}

export { Avatar, AvatarFallback }
