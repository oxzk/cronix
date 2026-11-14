import { cn } from '@/lib/utils'

export function JsonBlock({ value, className }: { value: unknown; className?: string }) {
    const text =
        typeof value === 'string' ? value : JSON.stringify(value, null, 2) ?? String(value)
    return (
        <pre
            className={cn(
                'overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-3 font-mono text-xs whitespace-pre-wrap text-slate-700',
                className,
            )}
        >
            {text}
        </pre>
    )
}
