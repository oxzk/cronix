import type { ReactElement } from 'react'
import { Tooltip as TooltipPrimitive } from '@base-ui/react/tooltip'
import { cn } from '@/lib/utils'

function TooltipProvider({
    delay = 0,
    ...props
}: TooltipPrimitive.Provider.Props) {
    return <TooltipPrimitive.Provider data-slot="tooltip-provider" delay={delay} {...props} />
}

function Tooltip(props: TooltipPrimitive.Root.Props) {
    return <TooltipPrimitive.Root data-slot="tooltip" {...props} />
}

function TooltipTrigger(props: TooltipPrimitive.Trigger.Props) {
    return <TooltipPrimitive.Trigger data-slot="tooltip-trigger" {...props} />
}

function TooltipContent({
    className,
    side = 'top',
    sideOffset = 6,
    children,
    ...props
}: TooltipPrimitive.Popup.Props & {
    side?: 'top' | 'bottom' | 'left' | 'right'
    sideOffset?: number
}) {
    return (
        <TooltipPrimitive.Portal>
            <TooltipPrimitive.Positioner side={side} sideOffset={sideOffset} className="isolate z-[70]">
                <TooltipPrimitive.Popup
                    data-slot="tooltip-content"
                    className={cn(
                        'inline-flex w-fit max-w-xs items-center rounded-md bg-slate-900 px-2 py-1 text-xs leading-relaxed text-white shadow',
                        className,
                    )}
                    {...props}
                >
                    {children}
                    <TooltipPrimitive.Arrow className="bg-slate-900 fill-slate-900" />
                </TooltipPrimitive.Popup>
            </TooltipPrimitive.Positioner>
        </TooltipPrimitive.Portal>
    )
}

export function TooltipTip({ content, children }: { content: string; children: ReactElement }) {
    return (
        <Tooltip>
            <TooltipTrigger render={children} />
            <TooltipContent>{content}</TooltipContent>
        </Tooltip>
    )
}

export { TooltipProvider }
