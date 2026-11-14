import { createContext, useContext, useId, type ComponentProps, type ReactNode } from 'react'
import { Field as FieldPrimitive } from '@base-ui/react/field'
import { cn } from '@/lib/utils'
import { Label } from './label'

const FieldControlContext = createContext<string | undefined>(undefined)

export function useFieldControlId(): string | undefined {
    return useContext(FieldControlContext)
}

function Field({ className, ...props }: ComponentProps<typeof FieldPrimitive.Root>) {
    return (
        <FieldPrimitive.Root
            data-slot="field"
            className={cn('group/field flex w-full flex-col gap-1.5', className)}
            {...props}
        />
    )
}

function FieldLabel({ className, ...props }: ComponentProps<typeof Label>) {
    return (
        <Label
            data-slot="field-label"
            className={cn('flex w-fit items-center gap-1 text-sm font-medium text-slate-700', className)}
            {...props}
        />
    )
}

function FieldDescription({
    className,
    ...props
}: ComponentProps<typeof FieldPrimitive.Description>) {
    return (
        <FieldPrimitive.Description
            data-slot="field-description"
            className={cn('text-left text-xs leading-normal text-slate-400', className)}
            {...props}
        />
    )
}

function FieldError({ className, ...props }: ComponentProps<typeof FieldPrimitive.Error>) {
    return (
        <FieldPrimitive.Error
            data-slot="field-error"
            match
            className={cn('text-xs font-normal text-rose-600', className)}
            {...props}
        />
    )
}

export interface FieldFrameProps {
    label: string
    required?: boolean
    hint?: string
    error?: string | null
    labelSuffix?: ReactNode
    className?: string
    children: ReactNode
}

/** Base UI Field 字段组合: label / 必填 / 提示 / 错误。 */
export function FieldFrame({
    label,
    required,
    hint,
    error,
    labelSuffix,
    className,
    children,
}: FieldFrameProps) {
    const id = useId()
    return (
        <FieldControlContext.Provider value={id}>
            <Field className={className} invalid={Boolean(error)}>
                <div className="flex items-center gap-1">
                    <FieldLabel htmlFor={id}>
                        {label}
                        {required && <span className="ml-0.5 text-rose-500">*</span>}
                    </FieldLabel>
                    {labelSuffix}
                </div>
                {children}
                {hint && !error && <FieldDescription>{hint}</FieldDescription>}
                {error && <FieldError>{error}</FieldError>}
            </Field>
        </FieldControlContext.Provider>
    )
}
