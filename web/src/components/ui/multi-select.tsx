import { useEffect, useRef, useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MultiSelectOption {
    value: string
    label: string
}

/** 多选下拉框(无第三方依赖, 点击外部关闭)。 */
export function MultiSelect({
    options,
    value,
    onChange,
    placeholder = '请选择',
    disabled,
}: {
    options: MultiSelectOption[]
    value: string[]
    onChange: (value: string[]) => void
    placeholder?: string
    disabled?: boolean
}) {
    const [open, setOpen] = useState(false)
    const rootRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (!open) return
        const onPointerDown = (event: MouseEvent) => {
            if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
                setOpen(false)
            }
        }
        document.addEventListener('mousedown', onPointerDown)
        return () => document.removeEventListener('mousedown', onPointerDown)
    }, [open])

    const toggle = (optionValue: string) => {
        if (value.includes(optionValue)) {
            onChange(value.filter((item) => item !== optionValue))
        } else {
            onChange([...value, optionValue])
        }
    }

    const summary = options
        .filter((option) => value.includes(option.value))
        .map((option) => option.label)

    return (
        <div className="relative" ref={rootRef}>
            <button
                type="button"
                disabled={disabled}
                onClick={() => setOpen((prev) => !prev)}
                className={cn(
                    'flex h-9 w-full items-center justify-between gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm',
                    'focus:outline-none focus:ring-2 focus:ring-slate-900/10 disabled:cursor-not-allowed disabled:opacity-50',
                )}
            >
                <span className={cn('truncate', summary.length ? 'text-slate-900' : 'text-slate-400')}>
                    {summary.length ? summary.join('、') : placeholder}
                </span>
                <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />
            </button>
            {open && (
                <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white p-1 shadow-lg">
                    {options.length === 0 ? (
                        <p className="px-2 py-1.5 text-xs text-slate-400">暂无选项</p>
                    ) : (
                        options.map((option) => {
                            const checked = value.includes(option.value)
                            return (
                                <button
                                    key={option.value}
                                    type="button"
                                    onClick={() => toggle(option.value)}
                                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-50"
                                >
                                    <span
                                        className={cn(
                                            'flex h-4 w-4 shrink-0 items-center justify-center rounded border',
                                            checked
                                                ? 'border-slate-900 bg-slate-900 text-white'
                                                : 'border-slate-300',
                                        )}
                                    >
                                        {checked && <Check className="h-3 w-3" />}
                                    </span>
                                    {option.label}
                                </button>
                            )
                        })
                    )}
                </div>
            )}
        </div>
    )
}
