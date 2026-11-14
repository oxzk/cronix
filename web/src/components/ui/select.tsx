import * as React from 'react'
import type { ReactNode } from 'react'
import { Select as SelectPrimitive } from '@base-ui/react/select'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useFieldControlId } from './field'

type SelectProps = {
    value?: string
    onValueChange?: (value: string) => void
    placeholder?: string
    disabled?: boolean
    className?: string
    children?: ReactNode
    name?: string
}

export function Select({
    value,
    onValueChange,
    placeholder,
    disabled,
    className,
    children,
    name,
}: SelectProps) {
    const id = useFieldControlId()
    const items = React.Children.toArray(children).reduce<Record<string, ReactNode>>(
        (result, child) => {
            if (React.isValidElement(child)) {
                const props = child.props as { value?: unknown; children?: ReactNode }
                if (props.value != null) {
                    result[String(props.value)] = props.children
                }
            }
            return result
        },
        {},
    )
    return (
        <SelectPrimitive.Root
            data-slot="select"
            value={value}
            onValueChange={(next) => {
                if (typeof next === 'string') onValueChange?.(next)
            }}
            disabled={disabled}
            name={name}
        >
            <SelectPrimitive.Trigger
                id={id}
                className={cn(
                    'flex h-9 w-full items-center justify-between gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900',
                    'data-placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10',
                    'disabled:cursor-not-allowed disabled:opacity-50',
                    className,
                )}
            >
                <SelectPrimitive.Value placeholder={placeholder}>
                    {(selected) =>
                        selected == null
                            ? (placeholder ?? null)
                            : (items[String(selected)] ?? String(selected))
                    }
                </SelectPrimitive.Value>
                <SelectPrimitive.Icon
                    render={<ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />}
                />
            </SelectPrimitive.Trigger>
            <SelectPrimitive.Portal>
                <SelectPrimitive.Positioner side="bottom" align="start" sideOffset={4} className="z-50">
                    <SelectPrimitive.Popup className="max-h-(--available-height) w-(--anchor-width) min-w-36 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg">
                        <SelectPrimitive.List className="p-1">{children}</SelectPrimitive.List>
                    </SelectPrimitive.Popup>
                </SelectPrimitive.Positioner>
            </SelectPrimitive.Portal>
        </SelectPrimitive.Root>
    )
}

export function SelectItem({
    className,
    value,
    children,
}: {
    className?: string
    value: string
    children: ReactNode
}) {
    return (
        <SelectPrimitive.Item
            data-slot="select-item"
            value={value}
            className={cn(
                'relative flex cursor-pointer select-none items-center rounded-md py-1.5 pl-8 pr-3 text-sm text-slate-700 outline-none',
                'data-highlighted:bg-slate-100 data-selected:font-medium data-selected:text-slate-900',
                className,
            )}
        >
            <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
            <SelectPrimitive.ItemIndicator
                render={
                    <span className="pointer-events-none absolute left-2 flex h-4 w-4 items-center justify-center" />
                }
            >
                <Check className="h-3.5 w-3.5" />
            </SelectPrimitive.ItemIndicator>
        </SelectPrimitive.Item>
    )
}
