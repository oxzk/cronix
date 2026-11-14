import { forwardRef, useState, type ComponentProps } from 'react'
import { Input as InputPrimitive } from '@base-ui/react/input'
import { Toggle } from '@base-ui/react/toggle'
import { Eye, EyeOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useFieldControlId } from './field'

type SecretInputProps = Omit<ComponentProps<typeof InputPrimitive>, 'type'>

/** 密码/令牌输入, Base UI Input + Toggle 控制显隐。 */
export const SecretInput = forwardRef<HTMLInputElement, SecretInputProps>(
    function SecretInput({ className, ...props }, ref) {
        const [visible, setVisible] = useState(false)
        const id = useFieldControlId()
        return (
            <div className="relative">
                <InputPrimitive
                    ref={ref}
                    {...props}
                    id={props.id ?? id}
                    type={visible ? 'text' : 'password'}
                    data-slot="secret-input"
                    className={cn(
                        'h-9 w-full rounded-md border border-slate-200 bg-white px-3 pr-9 text-sm text-slate-900',
                        'placeholder:text-slate-400 focus:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10',
                        'disabled:cursor-not-allowed disabled:opacity-50',
                        className,
                    )}
                />
                <Toggle
                    type="button"
                    tabIndex={-1}
                    pressed={visible}
                    onPressedChange={(pressed) => setVisible(pressed)}
                    aria-label={visible ? '隐藏密码' : '显示密码'}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                    {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Toggle>
            </div>
        )
    },
)
