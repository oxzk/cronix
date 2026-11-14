import * as React from 'react'
import { OTPInput, OTPInputContext, REGEXP_ONLY_DIGITS } from 'input-otp'
import { cn } from '@/lib/utils'

function OtpSlot({ index }: { index: number }) {
    const context = React.useContext(OTPInputContext)
    const { char, hasFakeCaret, isActive } = context?.slots[index] ?? {}

    return (
        <div
            data-slot="otp-slot"
            data-active={isActive}
            className={cn(
                'relative flex size-8 items-center justify-center rounded-md border border-slate-200 bg-white font-mono text-sm text-slate-900 transition-colors',
                'data-[active=true]:border-slate-400 data-[active=true]:ring-2 data-[active=true]:ring-slate-900/10',
            )}
        >
            {char}
            {hasFakeCaret && (
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                    <div className="h-4 w-px animate-caret-blink bg-slate-900" />
                </div>
            )}
        </div>
    )
}

/** 6 位动态验证码输入, shadcn Input OTP, 每个格子带边框。 */
export function OtpInput({
    value,
    onValueChange,
    disabled,
    autoFocus,
    className,
    length = 6,
}: {
    value: string
    onValueChange: (value: string) => void
    disabled?: boolean
    autoFocus?: boolean
    className?: string
    length?: number
}) {
    return (
        <OTPInput
            value={value}
            onChange={onValueChange}
            maxLength={length}
            pattern={REGEXP_ONLY_DIGITS}
            disabled={disabled}
            autoFocus={autoFocus}
            containerClassName={cn('flex items-center gap-3 has-disabled:opacity-50', className)}
            className="disabled:cursor-not-allowed"
        >
            {Array.from({ length }, (_, index) => (
                <OtpSlot key={index} index={index} />
            ))}
        </OTPInput>
    )
}
