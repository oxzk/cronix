import { forwardRef, type ComponentProps } from 'react'
import { Button as ButtonPrimitive } from '@base-ui/react/button'
import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
    'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/20 disabled:pointer-events-none disabled:opacity-50',
    {
        variants: {
            variant: {
                default: 'bg-slate-900 text-white hover:bg-slate-800',
                secondary: 'border border-slate-200 bg-white text-slate-900 hover:bg-slate-50',
                danger: 'bg-rose-600 text-white hover:bg-rose-500',
                ghost: 'text-slate-500 hover:bg-slate-100 hover:text-slate-900',
            },
            size: {
                default: 'h-9 px-3.5 text-sm',
                sm: 'h-8 px-3 text-sm',
                lg: 'h-10 px-4 text-sm',
                icon: 'h-8 w-8',
            },
        },
        defaultVariants: { variant: 'default', size: 'default' },
    },
)

type ButtonProps = ComponentProps<typeof ButtonPrimitive> &
    VariantProps<typeof buttonVariants> & {
        loading?: boolean
    }

const Button = forwardRef<HTMLElement, ButtonProps>(function Button(
    { className, variant, size, loading = false, disabled, children, ...props },
    ref,
) {
    return (
        <ButtonPrimitive
            ref={ref}
            data-slot="button"
            disabled={disabled || loading}
            className={cn(buttonVariants({ variant, size }), className)}
            {...props}
        >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {children}
        </ButtonPrimitive>
    )
})

export { Button }
